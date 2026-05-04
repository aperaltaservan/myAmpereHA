"""Test fixtures for Ampere Energy integration."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_ampere_modbus_client():
    """Mock of AmpereModbusClient for testing."""
    from custom_components.ampere_energy.modbus_client import AmpereModbusClient

    with patch("custom_components.ampere_energy.modbus_client.AmpereModbusClient") as MockClient:
        client = MagicMock(spec=AmpereModbusClient)
        client.test_connection = AsyncMock(return_value=True)
        client.read_bulk = AsyncMock(return_value={1: 100, 5: 200, 9: 300})
        client.is_alive = True
        client.connection_errors = 0
        client.reset_error_count = MagicMock()
        yield client


@pytest.fixture
def mock_coordinator():
    """Mock of AmpereCoordinator for testing."""
    from custom_components.ampere_energy.coordinator import AmpereCoordinator

    with patch("custom_components.ampere_energy.coordinator.AmpereCoordinator") as MockCoord:
        coordinator = MagicMock(spec=AmpereCoordinator)
        coordinator.data = {1: 100, 5: 200, 9: 300, 13: -50, 15: 85}
        coordinator.last_update_success = True
        coordinator.device_model = "Ampere.IO TW6"
        coordinator.device_version = "v1.2.3"
        yield coordinator


@pytest.fixture
def sample_sensor_defs():
    """Sample sensor definitions for testing."""
    return [
        {
            "name": "Produccion solar",
            "register": 9,
            "dtype": "uint16",
            "scale": 1.0,
            "precision": 0,
            "unit": "W",
            "device_class": "power",
            "state_class": "measurement",
            "icon": "mdi:solar-panel",
            "enabled": True,
            "predefined": True,
        },
        {
            "name": "SOC bateria",
            "register": 15,
            "dtype": "uint16",
            "scale": 0.1,
            "precision": 1,
            "unit": "%",
            "device_class": "battery",
            "state_class": "measurement",
            "icon": "mdi:battery",
            "enabled": True,
            "predefined": True,
        },
    ]


@pytest.fixture
def mock_config_entry():
    """Mock ConfigEntry for testing."""
    from homeassistant.config_entries import ConfigEntry

    entry = MagicMock(spec=ConfigEntry)
    entry.entry_id = "test_entry_123"
    entry.data = {
        "host": "192.168.1.50",
        "port": 502,
        "slave": 1,
        "function": "input",
        "scan_interval": 30,
    }
    entry.options = {"sensors": []}
    yield entry