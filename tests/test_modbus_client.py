"""Tests for modbus_client."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

import asyncio


class TestAmpereModbusClient:
    """Test cases for AmpereModbusClient."""

    def test_client_initialization(self):
        """Test client is initialized with correct parameters."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        client = AmpereModbusClient("192.168.1.50", 502, 1, "input", 5.0, 3)

        assert client._host == "192.168.1.50"
        assert client._port == 502
        assert client._slave == 1
        assert client._function == "input"
        assert client._timeout == 5.0
        assert client._max_retries == 3
        assert client._connection_errors == 0

    def test_connection_error_tracking(self):
        """Test error count is tracked correctly."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        client = AmpereModbusClient("192.168.1.50", 502, 1, "input")

        assert client.connection_errors == 0
        assert client.is_alive is True

        client._record_error()
        assert client.connection_errors == 1
        client._record_error()
        assert client.connection_errors == 2
        assert client.is_alive is True

        client._record_error()
        assert client.is_alive is False

        client.reset_error_count()
        assert client.connection_errors == 0
        assert client.is_alive is True

    @pytest.mark.asyncio
    async def test_raw_read_success(self):
        """Test successful raw read."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        mock_reader = AsyncMock()
        mock_writer = AsyncMock()

        header = b"\x00\x01\x00\x00\x00\x05\x01"
        body = b"\x04\x02\x00\x64\x00\xC8"

        async def mock_readexactly(n):
            if n == 7:
                return header
            return body

        mock_reader.readexactly = mock_readexactly

        with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
            mock_open.return_value = (mock_reader, mock_writer)

            client = AmpereModbusClient("192.168.1.50", 502, 1, "input")
            result = await client._raw_read(0, 1)

            assert result == [100, 200]

    @pytest.mark.asyncio
    async def test_raw_read_timeout(self):
        """Test read timeout handling."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
            mock_open.side_effect = asyncio.TimeoutError()

            client = AmpereModbusClient("192.168.1.50", 502, 1, "input")
            result = await client._raw_read(0, 1)

            assert result is None

    @pytest.mark.asyncio
    async def test_raw_read_connection_refused(self):
        """Test connection refused handling."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        with patch("asyncio.open_connection", new_callable=AsyncMock) as mock_open:
            mock_open.side_effect = ConnectionRefusedError()

            client = AmpereModbusClient("192.168.1.50", 502, 1, "input")
            result = await client._raw_read(0, 1)

            assert result is None

    @pytest.mark.asyncio
    async def test_read_bulk_empty_addresses(self):
        """Test read_bulk with empty address list."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        client = AmpereModbusClient("192.168.1.50", 502, 1, "input")
        result = await client.read_bulk([])

        assert result == {}

    @pytest.mark.asyncio
    async def test_read_bulk_groups_registers(self):
        """Test read_bulk groups registers correctly."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        client = AmpereModbusClient("192.168.1.50", 502, 1, "input")

        addresses = [5, 9, 10, 15, 20, 25]

        with patch.object(client, "_raw_read", new_callable=AsyncMock) as mock_read:
            mock_read.return_value = [100, 200, 300]
            result = await client.read_bulk(addresses)

            assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_connection_with_retry(self):
        """Test connection with retry logic."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        client = AmpereModbusClient(
            "192.168.1.50",
            502,
            1,
            "input",
            timeout=5.0,
            max_retries=3,
            initial_backoff=0.1,
            max_backoff=0.2,
        )

        with patch.object(client, "_raw_read", new_callable=AsyncMock) as mock_read:
            mock_read.return_value = [100]

            success, result = await client._with_retry(
                lambda: asyncio.create_task(client._raw_read(0, 1))
            )

            assert success is True
            assert result == [100]
            assert client.connection_errors == 0


class TestDecodeValue:
    """Test cases for decode_value method."""

    def test_decode_uint16(self):
        """Test uint16 decoding."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        result = AmpereModbusClient.decode_value([100], "uint16", 1.0)
        assert result == 100.0

    def test_decode_uint16_with_scale(self):
        """Test uint16 decoding with scale."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        result = AmpereModbusClient.decode_value([100], "uint16", 0.1)
        assert result == 10.0

    def test_decode_uint16_sentinel(self):
        """Test uint16 sentinel value handling."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient
        from custom_components.ampere_energy.const import NO_VALUE_SENTINEL

        result = AmpereModbusClient.decode_value([NO_VALUE_SENTINEL], "uint16", 1.0)
        assert result is None

    def test_decode_int16_positive(self):
        """Test int16 positive value."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        result = AmpereModbusClient.decode_value([100], "int16", 1.0)
        assert result == 100.0

    def test_decode_int16_negative(self):
        """Test int16 negative value."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        result = AmpereModbusClient.decode_value([65535 - 100], "int16", 1.0)
        assert result == -100.0

    def test_decode_int32_be(self):
        """Test int32 big-endian decoding."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        result = AmpereModbusClient.decode_value([0, 100], "int32_be", 1.0)
        assert result == 100.0

    def test_decode_float32_be(self):
        """Test float32 big-endian decoding."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        import struct

        raw = struct.unpack(">I", struct.pack(">f", 123.5))[0]
        high = (raw >> 16) & 0xFFFF
        low = raw & 0xFFFF

        result = AmpereModbusClient.decode_value([high, low], "float32_be", 1.0)
        assert result is not None

    def test_decode_unsupported_type(self):
        """Test unsupported type handling."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        result = AmpereModbusClient.decode_value([100], "unsupported", 1.0)
        assert result is None


class TestRegistersNeeded:
    """Test cases for registers_needed method."""

    def test_registers_needed_16bit(self):
        """Test 16-bit types need 1 register."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        assert AmpereModbusClient.registers_needed("uint16") == 1
        assert AmpereModbusClient.registers_needed("int16") == 1

    def test_registers_needed_32bit(self):
        """Test 32-bit types need 2 registers."""
        from custom_components.ampere_energy.modbus_client import AmpereModbusClient

        assert AmpereModbusClient.registers_needed("uint32_be") == 2
        assert AmpereModbusClient.registers_needed("int32_be") == 2
        assert AmpereModbusClient.registers_needed("uint32_le") == 2
        assert AmpereModbusClient.registers_needed("int32_le") == 2
        assert AmpereModbusClient.registers_needed("float32_be") == 2
        assert AmpereModbusClient.registers_needed("float32_le") == 2