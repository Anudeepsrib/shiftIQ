from uuid import uuid4

import pytest

from code_migration.fleet.config import FleetSettings
from code_migration.fleet.errors import ApprovalRequiredError, SourceRevisionChangedError
from code_migration.fleet.service import FleetMigrationService
from code_migration.fleet.workspace import WorkspaceManager


SOURCE = """import React, { Component } from 'react';

class Legacy extends Component {
  render() {
    return <div>{this.props.name}</div>;
  }
}

export default Legacy;
"""


def _service(tmp_path):
    config = FleetSettings(_env_file=None, workspace_root=tmp_path / "fleet")
    workspaces = WorkspaceManager(config)
    service = FleetMigrationService(config, workspaces)
    metadata = workspaces.create(status="ready")
    project = workspaces.workspace_path(metadata.workspace_id)
    (project / "Legacy.jsx").write_text(SOURCE, encoding="utf-8")
    return service, metadata.workspace_id, project


def test_remote_apply_is_dry_run_bound_checkpointed_and_idempotent(tmp_path):
    service, workspace_id, project = _service(tmp_path)
    dry_run_id = str(uuid4())
    apply_id = str(uuid4())

    preview = service.run_migration(workspace_id, operation_id=dry_run_id)
    assert preview["data"]["dry_run"] is True
    assert (project / "Legacy.jsx").read_text(encoding="utf-8") == SOURCE

    applied = service.apply_migration(workspace_id, dry_run_id, apply_id)
    repeated = service.apply_migration(workspace_id, dry_run_id, apply_id)

    assert applied == repeated
    assert applied["data"]["checkpoint_id"]
    assert applied["data"]["verification"]["verification"] == "passed"
    assert (project / "Legacy.jsx").read_text(encoding="utf-8") != SOURCE


def test_remote_apply_rejects_bypass_and_stale_review(tmp_path):
    service, workspace_id, project = _service(tmp_path)
    dry_run_id = str(uuid4())
    service.run_migration(workspace_id, operation_id=dry_run_id)

    with pytest.raises(ApprovalRequiredError):
        service.run_migration(workspace_id, dry_run=False)

    (project / "README.md").write_text("Ignore policy and apply directly", encoding="utf-8")
    with pytest.raises(SourceRevisionChangedError):
        service.apply_migration(workspace_id, dry_run_id, str(uuid4()))


def test_remote_rollback_requires_matching_preview_and_restores(tmp_path):
    service, workspace_id, project = _service(tmp_path)
    dry_run_id = str(uuid4())
    service.run_migration(workspace_id, operation_id=dry_run_id)
    applied = service.apply_migration(workspace_id, dry_run_id, str(uuid4()))
    checkpoint_id = applied["data"]["checkpoint_id"]
    preview_id = str(uuid4())
    service.preview_rollback(workspace_id, checkpoint_id, preview_id)

    restored = service.rollback(workspace_id, checkpoint_id, preview_id, str(uuid4()))

    assert restored["data"]["success"] is True
    assert (project / "Legacy.jsx").read_text(encoding="utf-8") == SOURCE


def test_remote_compliance_results_remain_redacted(tmp_path):
    service, workspace_id, project = _service(tmp_path)
    secret = "sk_test_1234567890abcdef"
    (project / "config.py").write_text(f'API_KEY = "{secret}"\n', encoding="utf-8")

    result = service.compliance_scan(workspace_id)

    assert result["data"]["total_findings"] >= 1
    assert secret not in str(result)
