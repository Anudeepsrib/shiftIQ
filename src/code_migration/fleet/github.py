"""Restricted GitHub ingestion for managed ShiftIQ workspaces."""

from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlparse

from code_migration.fleet.config import FleetSettings, get_fleet_settings
from code_migration.fleet.errors import RemoteMCPError, WorkspaceQuotaError
from code_migration.fleet.models import WorkspaceMetadata
from code_migration.fleet.workspace import WorkspaceManager


OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]{1,100}$")
REF_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._/-]{0,254}$")


def normalize_github_repository(repository: str) -> str:
    value = repository.strip().removesuffix(".git")
    if "://" in value:
        parsed = urlparse(value)
        if parsed.scheme != "https" or parsed.hostname not in {"github.com", "www.github.com"}:
            raise RemoteMCPError("Only HTTPS GitHub repositories are supported")
        value = parsed.path.strip("/")
    parts = value.split("/")
    if (
        len(parts) != 2
        or not OWNER_RE.fullmatch(parts[0])
        or not REPOSITORY_RE.fullmatch(parts[1])
        or parts[1].startswith(("-", "."))
    ):
        raise RemoteMCPError("Repository must be a valid GitHub owner/name slug")
    return value


def validate_ref(ref: str) -> str:
    value = ref.strip()
    if not REF_RE.fullmatch(value) or ".." in value or "@{" in value or value.endswith((".", "/")):
        raise RemoteMCPError("Invalid Git ref")
    return value


def prepare_github_workspace(
    repository: str,
    *,
    ref: str = "main",
    manager: WorkspaceManager | None = None,
    config: FleetSettings | None = None,
) -> WorkspaceMetadata:
    cfg = config or get_fleet_settings()
    workspaces = manager or WorkspaceManager(cfg)
    slug = normalize_github_repository(repository)
    safe_ref = validate_ref(ref)
    metadata = workspaces.create(source_repository=slug, source_ref=safe_ref, status="preparing")
    destination = workspaces.workspace_path(metadata.workspace_id)
    url = f"https://github.com/{slug}.git"

    env = os.environ.copy()
    env.update({"GIT_TERMINAL_PROMPT": "0", "GIT_LFS_SKIP_SMUDGE": "1"})
    token = cfg.github_token_value
    if token:
        env.update(
            {
                "GIT_CONFIG_COUNT": "1",
                "GIT_CONFIG_KEY_0": "http.https://github.com/.extraHeader",
                "GIT_CONFIG_VALUE_0": f"Authorization: Bearer {token}",
            }
        )

    hooks_path = "NUL" if os.name == "nt" else "/dev/null"
    command = [
        "git",
        "-c",
        "protocol.file.allow=never",
        "-c",
        "protocol.ext.allow=never",
        "-c",
        f"core.hooksPath={hooks_path}",
        "clone",
        "--depth=1",
        "--filter=blob:none",
        "--no-tags",
        "--single-branch",
        "--branch",
        safe_ref,
        "--",
        url,
        str(destination),
    ]
    try:
        completed = subprocess.run(
            command,
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=cfg.github_clone_timeout_seconds,
            check=False,
        )
        if completed.returncode != 0:
            raise RemoteMCPError("GitHub repository could not be prepared")
        sha = subprocess.run(
            ["git", "-C", str(destination), "rev-parse", "HEAD"],
            env=env,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=30,
            check=True,
        ).stdout.strip()
        if not re.fullmatch(r"[0-9a-f]{40,64}", sha):
            raise RemoteMCPError("GitHub repository returned an invalid commit SHA")
        metadata.source_sha = sha
        metadata.status = "ready"
        workspaces.save(metadata)
        return workspaces.status(metadata.workspace_id)
    except (OSError, subprocess.SubprocessError, WorkspaceQuotaError):
        workspaces.delete(metadata.workspace_id)
        raise RemoteMCPError("GitHub repository could not be prepared") from None
