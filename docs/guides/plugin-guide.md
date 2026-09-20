# Developing Plugins for ShiftIQ

The platform uses Python `entry_points` to dynamically discover and inject external packages as native migrators.

This means you can build proprietary migrations for your internal enterprise software without needing to fork the `shiftIQ` core.

## The `BaseMigrator` Interface

Every migrator must subclass `BaseMigrator` from `code_migration.migrators.base_migrator`. 

```python
from pathlib import Path
from code_migration.migrators.base_migrator import BaseMigrator

class MyInternalFrameworkMigrator(BaseMigrator):
    @property
    def name(self) -> str:
        return "my-internal-migrator"
        
    @property
    def description(self) -> str:
        return "Migrates v1 internal UI schema to v2 UI schema"

    @property
    def version(self) -> str:
        return "1.0.0"

    @property
    def supported_extensions(self) -> list[str]:
        return [".js", ".jsx", ".ts", ".tsx"]

    @property
    def tags(self) -> list[str]:
        return ["internal", "frontend"]
        
    def can_migrate(self, file_path: Path) -> bool:
        # Check if file needs migration (e.g. contains specific legacy imports)
        return True

    def migrate(self, content: str, file_path: Path) -> str:
        # Perform your migrations here (RegEx, AST modifications, etc)
        # Return the modified content
        return content
```

## Registering Plugins

The core application scans for standard Python entry points in the `code_migration.migrators` group.

### Using `pyproject.toml`
If your new migrator is in its own python package `my-custom-migrator`, update your `pyproject.toml`:

```toml
[project.entry-points."code_migration.migrators"]
my_internal_framework = "my_custom_migrator.module:MyInternalFrameworkMigrator"
```

Once a user `pip install`'s your package alongside the parent `shiftIQ`, it will automatically appear in the UI, `/api/v1/migrators`, and the Typer CLI as a usable system!

## Best Practices
1. **Respect Boundaries**: Stick to AST or RegEx scanning in your `migrate` functions. Avoid any type of system modifications inside plugins.
2. **Metadata**: Always define `supported_extensions` so the engine can skip un-allocatable files before calling your plugin.
3. **Logs**: Use `from code_migration.utils.logger import get_logger`. The structlog bindings will automatically pick up your namespace and ingest your plugin telemetry correctly.
