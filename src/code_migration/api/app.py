from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from code_migration.config import settings
from code_migration.api.deps import get_registry
from code_migration.api.errors import (
    APIError,
    api_error_handler,
    global_exception_handler,
    http_exception_handler,
    SecurityError,
    security_error_handler,
)
from code_migration.api.auth import verify_api_key
from code_migration.api.v1.router import router as v1_router


def _docs_url(path: str) -> str | None:
    if settings.server.docs_enabled and not settings.is_production:
        return path
    if settings.server.docs_enabled and settings.is_production:
        return path
    return None


def create_app() -> FastAPI:
    """Create the FastAPI application."""
    allow_credentials = "*" not in settings.server.cors_origins

    app = FastAPI(
        title="ShiftIQ API",
        version="0.1.0",
        description="Local-first code migration assistant API",
        docs_url=_docs_url("/docs"),
        redoc_url=_docs_url("/redoc"),
        openapi_url=_docs_url("/openapi.json"),
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.server.cors_origins,
        allow_credentials=allow_credentials,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.add_exception_handler(APIError, api_error_handler)
    app.add_exception_handler(SecurityError, security_error_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, global_exception_handler)

    app.include_router(
        v1_router,
        prefix="/api/v1",
        tags=["API v1"],
        dependencies=[Depends(verify_api_key)],
    )

    @app.get("/healthz", tags=["System"])
    async def healthz(registry=Depends(get_registry)):
        """Health check without secrets, paths, or environment dumps."""
        return {
            "status": "ok",
            "service": "shiftiq",
            "migrator_count": len(registry.names()),
        }

    @app.get("/api/healthz", include_in_schema=False)
    async def api_healthz():
        return JSONResponse({"status": "ok"})

    repo_root = Path(__file__).resolve().parents[3]
    static_dir = repo_root / "ui" / "dist"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=str(static_dir), html=True), name="static")
    else:
        @app.get("/")
        async def index():
            return HTMLResponse(
                """
                <!doctype html>
                <html lang="en">
                  <head>
                    <meta charset="utf-8" />
                    <meta name="viewport" content="width=device-width, initial-scale=1" />
                    <title>ShiftIQ API</title>
                  </head>
                  <body>
                    <main>
                      <h1>ShiftIQ API is running</h1>
                      <p>The React UI has not been built yet. Run <code>cd ui && npm install && npm run build</code>.</p>
                    </main>
                  </body>
                </html>
                """,
                status_code=200,
            )

    return app


app = create_app()
