import pytest

from code_migration.fleet.client import ShiftIQFleetClient
from code_migration.fleet.config import FleetSettings
from code_migration.fleet.errors import FleetConfigurationError
from code_migration.fleet.tracing import trace_operation


def test_tracing_disabled_needs_no_langsmith_configuration():
    config = FleetSettings(_env_file=None, langsmith_tracing=False)
    with trace_operation("test", {"source": "redacted"}, config):
        pass


def test_fleet_client_requires_explicit_cloud_configuration():
    config = FleetSettings(_env_file=None, fleet_api_url=None, fleet_agent_id=None)
    with pytest.raises(FleetConfigurationError):
        ShiftIQFleetClient(config)
