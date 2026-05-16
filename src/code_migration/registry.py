"""
Plugin registry for Code Migration Assistant.

Provides auto-discovery and manual registration of migrators, analyzers,
and compliance scanners. Third-party plugins register via Python
entry_points (group: ``code_migration.migrators``).

Usage::

    from code_migration.registry import MigratorRegistry

    # Auto-discover all installed plugins
    registry = MigratorRegistry()
    registry.discover()

    # Use a migrator
    migrator = registry.get("react-hooks")
"""

from __future__ import annotations

import importlib.metadata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Type

from code_migration.migrators.base_migrator import BaseMigrator
from code_migration.utils.logger import get_logger

logger = get_logger(__name__)

# ---------------------------------------------------------------------------
# Plugin metadata
# ---------------------------------------------------------------------------

@dataclass
class PluginInfo:
    """Metadata about a registered plugin."""
    name: str
    description: str
    version: str
    supported_extensions: List[str]
    tags: List[str] = field(default_factory=list)
    source: str = "builtin"  # builtin | entry_point | manual


# ---------------------------------------------------------------------------
# Migrator Registry
# ---------------------------------------------------------------------------

class MigratorRegistry:
    """
    Central registry for migration plugins.

    Supports two registration paths:

    1. **Entry-points discovery** — any installed package can declare
       migrators under the ``code_migration.migrators`` group in its
       ``pyproject.toml``.
    2. **Manual registration** — call :meth:`register` programmatically.
    """

    ENTRY_POINT_GROUP = "code_migration.migrators"

    def __init__(self) -> None:
        self._migrators: Dict[str, BaseMigrator] = {}
        self._info: Dict[str, PluginInfo] = {}

    # -- Discovery -----------------------------------------------------------

    def discover(self) -> "MigratorRegistry":
        """
        Discover and load migrators from installed entry_points.

        Returns self for chaining.
        """
        try:
            eps = importlib.metadata.entry_points()
            # Python 3.9+ returns a SelectableGroups / dict
            if isinstance(eps, dict):
                group = eps.get(self.ENTRY_POINT_GROUP, [])
            else:
                group = eps.select(group=self.ENTRY_POINT_GROUP)

            for ep in group:
                try:
                    if ep.name in self._migrators:
                        continue
                    migrator_cls = ep.load()
                    migrator = migrator_cls() if isinstance(migrator_cls, type) else migrator_cls
                    self.register(
                        migrator,
                        source="entry_point",
                    )
                    logger.info("Discovered migrator '%s' via entry_point", migrator.name)
                except Exception:
                    logger.warning(
                        "Failed to load entry_point '%s'", ep.name, exc_info=True
                    )
        except Exception:
            logger.debug("Entry-point discovery unavailable", exc_info=True)

        return self

    def discover_builtins(self) -> "MigratorRegistry":
        """
        Register the built-in migrators shipped with this package.

        Called separately so that entry-points don't double-register
        builtins when the package is installed in editable mode.
        """
        from code_migration.migrators.react_hooks import ReactHooksMigrator

        builtin_migrators = [
            ReactHooksMigrator(),
        ]

        for m in builtin_migrators:
            if m.name not in self._migrators:
                self.register(m, source="builtin")

        return self

    # -- Registration --------------------------------------------------------

    def register(
        self,
        migrator: BaseMigrator,
        *,
        source: str = "manual",
    ) -> None:
        """Register a migrator instance under its ``name``."""
        name = migrator.name
        self._migrators[name] = migrator
        self._info[name] = PluginInfo(
            name=name,
            description=getattr(migrator, "description", ""),
            version=getattr(migrator, "version", "0.1.0"),
            supported_extensions=getattr(
                migrator, "supported_extensions",
                self._infer_extensions(migrator),
            ),
            tags=getattr(migrator, "tags", []),
            source=source,
        )

    @staticmethod
    def _infer_extensions(migrator: BaseMigrator) -> List[str]:
        """Best-effort extension inference from ``can_migrate``."""
        common = [".py", ".js", ".jsx", ".ts", ".tsx", ".vue"]
        return [ext for ext in common if migrator.can_migrate(Path(f"test{ext}"))]

    # -- Lookup --------------------------------------------------------------

    def get(self, name: str) -> Optional[BaseMigrator]:
        """Return a migrator by name, or ``None``."""
        return self._migrators.get(name)

    def __contains__(self, name: str) -> bool:
        return name in self._migrators

    def __getitem__(self, name: str) -> BaseMigrator:
        return self._migrators[name]

    def list_all(self) -> List[PluginInfo]:
        """Return metadata for all registered migrators."""
        return list(self._info.values())

    def names(self) -> List[str]:
        """Return all registered migrator names."""
        return list(self._migrators.keys())

    def as_dict(self) -> Dict[str, BaseMigrator]:
        """Return the full migrator dict (CLI compatibility)."""
        return dict(self._migrators)


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

def create_registry() -> MigratorRegistry:
    """Create a fully-populated registry (builtins + entry_points)."""
    registry = MigratorRegistry()
    registry.discover_builtins()
    registry.discover()
    return registry
