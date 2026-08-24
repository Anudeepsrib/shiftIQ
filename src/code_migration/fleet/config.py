"""Cloud-optional configuration for Fleet-facing components."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import AliasChoices, Field, SecretStr, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class FleetSettings(BaseSettings):
    fleet_enabled: bool = False
    langsmith_tracing: bool = False
    remote_mcp_enabled: bool = False
    remote_mcp_host: str = "127.0.0.1"
    remote_mcp_port: int = Field(default=8001, ge=1, le=65535)
    remote_mcp_path: str = "/mcp"
    remote_mcp_auth_enabled: bool = True
    mcp_api_key: Optional[SecretStr] = None
    workspace_root: Path = Path(".shiftiq-workspaces")
    workspace_ttl_seconds: int = Field(default=86_400, ge=60, le=2_592_000)
    workspace_max_mb: int = Field(default=512, ge=1, le=102_400)
    workspace_max_count: int = Field(default=100, ge=1, le=10_000)
    request_timeout_seconds: int = Field(default=300, ge=1, le=3600)
    remote_rate_limit_per_minute: int = Field(default=60, ge=1, le=10_000)
    static_verification: bool = True
    execution_verification: bool = False
    github_token: Optional[SecretStr] = None
    github_clone_timeout_seconds: int = Field(default=180, ge=1, le=3600)

    langsmith_api_key: Optional[SecretStr] = Field(
        default=None,
        validation_alias=AliasChoices("LANGGRAPH_API_KEY", "LANGSMITH_API_KEY"),
    )
    langsmith_workspace_id: Optional[str] = Field(default=None, validation_alias="LANGSMITH_WORKSPACE_ID")
    langsmith_project: str = Field(default="shiftiq", validation_alias="LANGSMITH_PROJECT")
    fleet_agent_id: Optional[str] = Field(default=None, validation_alias="LANGSMITH_FLEET_AGENT_ID")
    fleet_api_url: Optional[str] = Field(default=None, validation_alias="LANGSMITH_FLEET_API_URL")

    model_config = SettingsConfigDict(
        env_prefix="SHIFTIQ_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("remote_mcp_path")
    @classmethod
    def validate_mcp_path(cls, value: str) -> str:
        if not value.startswith("/") or ".." in value:
            raise ValueError("SHIFTIQ_REMOTE_MCP_PATH must be an absolute URL path")
        return value.rstrip("/") or "/mcp"

    @property
    def mcp_api_key_value(self) -> Optional[str]:
        return self.mcp_api_key.get_secret_value().strip() if self.mcp_api_key else None

    @property
    def langsmith_api_key_value(self) -> Optional[str]:
        return self.langsmith_api_key.get_secret_value().strip() if self.langsmith_api_key else None

    @property
    def github_token_value(self) -> Optional[str]:
        return self.github_token.get_secret_value().strip() if self.github_token else None

    @property
    def resolved_workspace_root(self) -> Path:
        return self.workspace_root.expanduser().resolve()


@lru_cache(maxsize=1)
def get_fleet_settings() -> FleetSettings:
    return FleetSettings()
