from pathlib import Path

from code_migration.operations import rollback_checkpoint, run_migration


def test_apply_creates_checkpoint_and_rollback_restores(tmp_path, monkeypatch):
    project = tmp_path / "project"
    src = project / "src"
    src.mkdir(parents=True)
    target = src / "Legacy.jsx"
    original = """import React, { Component } from 'react';

class Legacy extends Component {
  render() {
    return <div>{this.props.name}</div>;
  }
}

export default Legacy;
"""
    target.write_text(original, encoding="utf-8")
    monkeypatch.setattr("code_migration.config.settings.security.allowed_roots", [str(tmp_path)])

    result = run_migration(str(project), migration_type="react-hooks", dry_run=False)

    assert result["checkpoint_id"]
    assert result["results"][0]["applied"] is True
    assert target.read_text(encoding="utf-8") != original

    rollback = rollback_checkpoint(str(project), result["checkpoint_id"])

    assert rollback["success"] is True
    assert target.read_text(encoding="utf-8") == original


def test_dry_run_has_diff_but_does_not_write(tmp_path, monkeypatch):
    project = tmp_path / "project"
    project.mkdir()
    target = project / "Legacy.jsx"
    original = """import React, { Component } from 'react';

class Legacy extends Component {
  render() {
    return <div>{this.props.name}</div>;
  }
}

export default Legacy;
"""
    target.write_text(original, encoding="utf-8")
    monkeypatch.setattr("code_migration.config.settings.security.allowed_roots", [str(tmp_path)])

    result = run_migration(str(project), migration_type="react-hooks", dry_run=True)

    assert result["results"][0]["changed"] is True
    assert result["results"][0]["applied"] is False
    assert "--- Legacy.jsx" in result["results"][0]["diff"]
    assert target.read_text(encoding="utf-8") == original
