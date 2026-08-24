"""Optional LangSmith spans without a mandatory cloud dependency."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from code_migration.fleet.config import FleetSettings


@contextmanager
def trace_operation(name: str, metadata: dict, config: FleetSettings) -> Iterator[None]:
    if not config.langsmith_tracing:
        yield
        return
    try:
        from langsmith.run_helpers import trace
    except ImportError:
        yield
        return
    with trace(name, run_type="tool", project_name=config.langsmith_project, metadata=metadata):
        yield
