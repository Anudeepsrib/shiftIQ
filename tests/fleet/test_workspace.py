from datetime import datetime, timedelta, timezone

import pytest

from code_migration.fleet.config import FleetSettings
from code_migration.fleet.errors import WorkspaceBoundaryError, WorkspaceNotFoundError
from code_migration.fleet.github import normalize_github_repository, validate_ref
from code_migration.fleet.workspace import WorkspaceManager


def _manager(tmp_path):
    config = FleetSettings(_env_file=None, workspace_root=tmp_path / "fleet")
    return WorkspaceManager(config)


def test_workspace_ids_hide_paths_and_enforce_boundaries(tmp_path):
    manager = _manager(tmp_path)
    metadata = manager.create()
    workspace = manager.workspace_path(metadata.workspace_id)
    (workspace / "src").mkdir()
    (workspace / "src" / "app.py").write_text("print('data only')\n", encoding="utf-8")

    status = manager.status(metadata.workspace_id)

    assert status.file_count == 1
    assert manager.list_files(metadata.workspace_id) == ["src/app.py"]
    assert str(tmp_path) not in status.model_dump_json()
    with pytest.raises(WorkspaceBoundaryError):
        manager.workspace_path("../../outside")


def test_symlinks_are_not_exposed(tmp_path):
    manager = _manager(tmp_path)
    metadata = manager.create()
    workspace = manager.workspace_path(metadata.workspace_id)
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    try:
        (workspace / "escape.txt").symlink_to(outside)
    except OSError:
        pytest.skip("Symlink creation is not available")

    assert manager.list_files(metadata.workspace_id) == []


def test_expired_workspace_is_rejected_and_cleaned(tmp_path):
    manager = _manager(tmp_path)
    metadata = manager.create()
    metadata.expires_at = datetime.now(timezone.utc) - timedelta(seconds=1)
    manager.save(metadata)

    with pytest.raises(WorkspaceNotFoundError):
        manager.get(metadata.workspace_id)
    assert manager.sweep_expired() == 1


@pytest.mark.parametrize(
    "repository",
    [
        "http://github.com/org/repo",
        "https://example.com/org/repo",
        "file:///etc/passwd",
        "--upload-pack=evil/repo",
        "org/../repo",
        "127.0.0.1/repo",
    ],
)
def test_github_ingestion_rejects_unsafe_repository_inputs(repository):
    with pytest.raises(Exception):
        normalize_github_repository(repository)


def test_github_ingestion_normalizes_supported_input():
    assert normalize_github_repository("https://github.com/langchain-ai/langchain.git") == "langchain-ai/langchain"
    assert validate_ref("feature/migration-1") == "feature/migration-1"
    with pytest.raises(Exception):
        validate_ref("--upload-pack=evil")
