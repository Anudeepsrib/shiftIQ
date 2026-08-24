"""Remote request authentication, correlation, rate limiting, and context."""

from __future__ import annotations

import asyncio
import secrets
import time
from collections import defaultdict, deque
from contextvars import ContextVar
from uuid import uuid4

from starlette.datastructures import Headers

from code_migration.fleet.config import FleetSettings
from code_migration.utils.logger import get_logger


logger = get_logger(__name__)


request_id_var: ContextVar[str | None] = ContextVar("shiftiq_request_id", default=None)
fleet_trace_id_var: ContextVar[str | None] = ContextVar("shiftiq_fleet_trace_id", default=None)
actor_var: ContextVar[str | None] = ContextVar("shiftiq_actor", default=None)


def _json_response(status: int, code: str, message: str) -> tuple[int, list[tuple[bytes, bytes]], bytes]:
    import json

    body = json.dumps({"error": {"code": code, "message": message}}).encode("utf-8")
    headers = [(b"content-type", b"application/json"), (b"content-length", str(len(body)).encode("ascii"))]
    return status, headers, body


class RemoteSecurityMiddleware:
    """Small ASGI middleware so MCP auth is independent of tool arguments."""

    def __init__(self, app, *, config: FleetSettings) -> None:
        self.app = app
        self.config = config
        # ponytail: per-process limiter; move to the gateway/Redis before horizontal scaling.
        self.requests: dict[str, deque[float]] = defaultdict(deque)

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = Headers(scope=scope)
        started_at = time.monotonic()
        status_code = 500
        request_id = headers.get("x-request-id") or str(uuid4())
        request_id = request_id[:128]
        tokens = (
            request_id_var.set(request_id),
            fleet_trace_id_var.set((headers.get("x-fleet-trace-id") or "")[:128] or None),
            actor_var.set((headers.get("x-fleet-actor") or "")[:128] or None),
        )

        async def correlated_send(message) -> None:
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
                message.setdefault("headers", []).append((b"x-request-id", request_id.encode("ascii", "ignore")))
            await send(message)

        try:
            path = scope.get("path", "")
            if path not in {"/healthz", "/readyz"}:
                rejection = self._authorize(headers, scope)
                if rejection:
                    status, response_headers, body = rejection
                    await correlated_send({"type": "http.response.start", "status": status, "headers": response_headers})
                    await correlated_send({"type": "http.response.body", "body": body})
                    return
            await asyncio.wait_for(
                self.app(scope, receive, correlated_send),
                timeout=self.config.request_timeout_seconds,
            )
        except TimeoutError:
            status, response_headers, body = _json_response(504, "request_timeout", "Request timed out")
            await correlated_send({"type": "http.response.start", "status": status, "headers": response_headers})
            await correlated_send({"type": "http.response.body", "body": body})
        finally:
            logger.info(
                "remote_mcp_request",
                request_id=request_id,
                method=scope.get("method"),
                path=scope.get("path"),
                status_code=status_code,
                duration_ms=round((time.monotonic() - started_at) * 1000, 2),
            )
            request_id_var.reset(tokens[0])
            fleet_trace_id_var.reset(tokens[1])
            actor_var.reset(tokens[2])

    def _authorize(self, headers: Headers, scope) -> tuple[int, list[tuple[bytes, bytes]], bytes] | None:
        client = scope.get("client")
        client_key = client[0] if client else "unknown"
        now = time.monotonic()
        window = self.requests[client_key]
        while window and window[0] <= now - 60:
            window.popleft()
        if len(window) >= self.config.remote_rate_limit_per_minute:
            return _json_response(429, "rate_limit", "Rate limit exceeded")
        window.append(now)

        if not self.config.remote_mcp_auth_enabled:
            return None
        expected = self.config.mcp_api_key_value
        if not expected:
            return _json_response(503, "authentication_unconfigured", "Remote MCP authentication is not configured")
        provided = headers.get("x-api-key")
        authorization = headers.get("authorization", "")
        if not provided and authorization.lower().startswith("bearer "):
            provided = authorization[7:].strip()
        if not provided or not secrets.compare_digest(provided, expected):
            return _json_response(401, "authentication_error", "Invalid or missing API key")
        return None
