"""Optional programmatic client for a configured Fleet agent."""

from __future__ import annotations

import asyncio
from typing import Any

import requests

from code_migration.fleet.config import FleetSettings, get_fleet_settings
from code_migration.fleet.errors import FleetConfigurationError, RemoteMCPError


class ShiftIQFleetClient:
    def __init__(self, config: FleetSettings | None = None) -> None:
        self.config = config or get_fleet_settings()
        if not self.config.fleet_api_url or not self.config.fleet_agent_id:
            raise FleetConfigurationError("Fleet API URL and agent ID are required")
        if not self.config.langsmith_api_key_value:
            raise FleetConfigurationError("LANGGRAPH_API_KEY or LANGSMITH_API_KEY is required")

    async def invoke(self, message: str) -> dict[str, Any]:
        """Invoke a stateless Fleet run through the documented Agent Server endpoint."""
        return await asyncio.to_thread(self._invoke_sync, message)

    def _invoke_sync(self, message: str) -> dict[str, Any]:
        url = f"{self.config.fleet_api_url.rstrip('/')}/runs/wait"
        headers = {
            "Content-Type": "application/json",
            "X-Api-Key": self.config.langsmith_api_key_value or "",
            "X-Auth-Scheme": "langsmith-api-key",
        }
        payload = {
            "assistant_id": self.config.fleet_agent_id,
            "input": {"messages": [{"role": "user", "content": message}]},
        }
        try:
            response = requests.post(
                url,
                headers=headers,
                json=payload,
                timeout=self.config.request_timeout_seconds,
            )
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError) as exc:
            raise RemoteMCPError("Fleet invocation failed") from exc

    async def analyze_repository(
        self,
        repository: str,
        migration_type: str = "react-hooks",
    ) -> dict[str, Any]:
        return await self.invoke(
            f"Analyze GitHub repository {repository} for migration type {migration_type}. "
            "Do not modify files. Return the ShiftIQ operation IDs and source commit."
        )
