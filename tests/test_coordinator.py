"""Tests for coordinator."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from datetime import timedelta


class TestAmpereCoordinator:
    """Test cases for AmpereCoordinator."""

    @pytest.fixture
    def mock_hass(self):
        """Mock HomeAssistant."""
        hass = MagicMock()
        hass.data = {}
        return hass

    @pytest.fixture
    def mock_client(self):
        """Mock Modbus client."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        client = MagicMock(spec=AmpereModbusClient)
        client.read_bulk = AsyncMock(
            return_value={
                0: 0,
                1: 100,
                5: 200,
                9: 300,
                13: -50,
                15: 850,
                1000: ord("T") << 8 | ord("W"),
                1001: ord("6") << 8 | ord(" "),
                1016: ord("1") << 8 | ord("."),
                1017: ord("2") << 8 | ord("."),
                1018: ord("3") << 8 | ord("\0"),
            }
        )
        client.test_connection = AsyncMock(return_value=True)
        return client

    def test_coordinator_initialization(
        self, mock_hass, mock_client, sample_sensor_defs
    ):
        """Test coordinator initialization."""
        from custom_components.ampere_energy.coordinator import AmpereCoordinator

        coordinator = AmpereCoordinator(
            mock_hass, mock_client, sample_sensor_defs, 30
        )

        assert coordinator._client is mock_client
        assert coordinator._sensor_defs == sample_sensor_defs
        assert coordinator.name == "ampere_energy"
        assert coordinator.update_interval == timedelta(seconds=30)

    def test_coordinator_update_sensor_defs(
        self, mock_hass, mock_client, sample_sensor_defs
    ):
        """Test update_sensor_defs method."""
        from custom_components.ampere_energy.coordinator import AmpereCoordinator

        coordinator = AmpereCoordinator(
            mock_hass, mock_client, sample_sensor_defs, 30
        )

        new_defs = [
            {
                "name": "Test",
                "register": 100,
                "enabled": True,
            }
        ]
        coordinator.update_sensor_defs(new_defs)

        assert coordinator._sensor_defs == new_defs

    @pytest.mark.asyncio
    async def test_async_update_data(
        self, mock_hass, mock_client, sample_sensor_defs
    ):
        """Test async_update_data method."""
        from custom_components.ampere_energy.coordinator import AmpereCoordinator

        coordinator = AmpereCoordinator(
            mock_hass, mock_client, sample_sensor_defs, 30
        )

        result = await coordinator._async_update_data()

        assert isinstance(result, dict)
        assert 9 in result
        assert 15 in result

    @pytest.mark.asyncio
    async def test_async_update_data_empty_sensors(
        self, mock_hass, mock_client
    ):
        """Test async_update_data with no sensors."""
        from custom_components.ampere_energy.coordinator import AmpereCoordinator

        coordinator = AmpereCoordinator(mock_hass, mock_client, [], 30)

        result = await coordinator._async_update_data()

        assert result == {}

    @pytest.mark.asyncio
    async def test_async_update_data_read_errors(
        self, mock_hass, mock_client, sample_sensor_defs
    ):
        """Test async_update_data handles read errors."""
        from custom_components.ampere_energy.coordinator import AmpereCoordinator

        mock_client.read_bulk = AsyncMock(return_value={})

        coordinator = AmpereCoordinator(
            mock_hass, mock_client, sample_sensor_defs, 30
        )

        with pytest.raises(Exception):
            await coordinator._async_update_data()

    def test_decode_ascii(self, mock_hass, mock_client):
        """Test ASCII decoding."""
        from custom_components.ampere_energy.coordinator import AmpereCoordinator

        raw_map = {
            1000: ord("T") << 8 | ord("W"),
            1001: ord("6") << 8 | ord(" "),
            1002: ord("F") << 8 | ord(" "),
            1003: ord("X") << 8 | ord(" "),
            1004: 0,
        }

        result = AmpereCoordinator._decode_ascii(raw_map, [1000, 1001, 1002, 1003])

        assert "TW" in result

    def test_decode_ascii_empty(self, mock_hass, mock_client):
        """Test ASCII decoding with missing registers."""
        from custom_components.ampere_energy.coordinator import AmpereCoordinator

        raw_map = {}

        result = AmpereCoordinator._decode_ascii(raw_map, [1000, 1001])

        assert result is None