"""Typed settings for ShiftIQ.

Configuration is loaded from safe defaults, an optional YAML file, ``.env``,
and ``MIGRATION_*`` environment variables. Environment variables always win.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Literal, Optional

import yaml
from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


DEMO_API_KEYS = {
    "dev-enterprise-key-123",
    "change-me",
    "changeme",
    "demo",
    "test",
    "secret",
    "password",
}


def _parse_csv_or_json(value: object) -> object:
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        if stripped.startswith("["):
            return json.loads(stripped)
        return [item.strip() for item in stripped.split(",") if item.strip()]
    return value


class SecuritySettings(BaseSettings):
    level: Literal["low", "medium", "high"] = Field(default="high")
    audit_logging: bool = Field(default=True)
    max_file_size_kb: int = Field(default=5000, ge=1, le=100_000)
    rate_limit_per_minute: int = Field(default=60, ge=1, le=10_000)
    allowed_roots: List[str] = Field(default_factory=lambda: ["."])
    max_files: int = Field(default=5000, ge=1, le=1_000_000)
    expose_raw_findings: bool = Field(default=False)

    @field_validator("allowed_roots", mode="before")
    @classmethod
    def parse_allowed_roots(cls, value: object) -> object:
        return _parse_csv_or_json(value)


class AnalysisSettings(BaseSettings):
    confidence_weights: Dict[str, float] = Field(
        default_factory=lambda: {
            "test_coverage": 0.25,
            "complexity": 0.20,
            "dependencies": 0.15,
            "code_quality": 0.15,
            "breaking_changes": 0.15,
            "team_experience": 0.10,
        }
    )
    cost_rate_per_hour: float = Field(default=100.0, ge=0)
    max_workers: int = Field(default=4, ge=1, le=64)
    timeout_seconds: int = Field(default=300, ge=1, le=86_400)


class ServerSettings(BaseSettings):
    environment: Literal["development", "test", "production"] = Field(default="development")
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000, ge=1, le=65535)
    cors_origins: List[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    docs_enabled: bool = Field(default=True)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def parse_cors_origins(cls, value: object) -> object:
        return _parse_csv_or_json(value)


class ObservabilitySettings(BaseSettings):
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(default="INFO")
    log_format: Literal["text", "json"] = Field(default="text")

    @field_validator("log_level", mode="before")
    @classmethod
    def normalize_log_level(cls, value: object) -> object:
        return value.upper() if isinstance(value, str) else value


def _load_yaml_config(file_path: Optional[str]) -> dict:
    """Load configuration from YAML without treating missing files as errors."""
    candidate = file_path
    if not candidate:
        repo_root = Path(__file__).resolve().parents[2]
        for loc in (repo_root / "config.defaults.yaml", Path("config.defaults.yaml")):
            if loc.exists():
                candidate = str(loc)
                break

    if not candidate or not Path(candidate).exists():
        return {}

    try:
        with open(candidate, "r", encoding="utf-8") as handle:
            return yaml.safe_load(handle) or {}
    except Exception as exc:
        print(f"Warning: failed to load config file {candidate}: {exc}", file=sys.stderr)
        return {}


class MigrationSettings(BaseSettings):
    """Application settings with production safety validation."""

    api_key: Optional[SecretStr] = Field(default=None)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    analysis: AnalysisSettings = Field(default_factory=AnalysisSettings)
    server: ServerSettings = Field(default_factory=ServerSettings)
    observability: ObservabilitySettings = Field(default_factory=ObservabilitySettings)

    model_config = SettingsConfigDict(
        env_prefix="MIGRATION_",
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        return self.server.environment == "production"

    @property
    def api_key_value(self) -> Optional[str]:
        if self.api_key is None:
            return None
        value = self.api_key.get_secret_value().strip()
        return value or None

    @model_validator(mode="after")
    def validate_runtime_safety(self) -> "MigrationSettings":
        if self.is_production:
            self._validate_production_api_key()
            self._validate_production_cors()
        return self

    def _validate_production_api_key(self) -> None:
        api_key = self.api_key_value
        if not api_key:
            raise ValueError("MIGRATION_API_KEY is required in production")
        lowered = api_key.lower()
        if api_key in DEMO_API_KEYS or lowered.startswith(("dev-", "demo-", "test-")):
            raise ValueError("MIGRATION_API_KEY must not use a demo/default value in production")
        if len(api_key) < 32:
            raise ValueError("MIGRATION_API_KEY must be at least 32 characters in production")

    def _validate_production_cors(self) -> None:
        origins = self.server.cors_origins
        if not origins or "*" in origins:
            raise ValueError("MIGRATION_SERVER__CORS_ORIGINS must be explicit in production")

    def resolved_allowed_roots(self) -> List[Path]:
        roots: List[Path] = []
        for root in self.security.allowed_roots:
            path = Path(root).expanduser()
            if not path.is_absolute():
                path = Path.cwd() / path
            roots.append(path.resolve())
        return roots

    @classmethod
    def load(cls) -> "MigrationSettings":
        config_file = os.environ.get("MIGRATION_CONFIG_FILE")
        yaml_data = _load_yaml_config(config_file)
        return cls(**yaml_data)


settings = MigrationSettings.load()
