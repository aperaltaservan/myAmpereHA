"""Coordinator de polling para myAmpere."""

from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    SENSOR_KEY_REGISTER,
    SENSOR_KEY_DTYPE,
    SENSOR_KEY_SCALE,
    SENSOR_KEY_ENABLED,
)
from .modbus_client import AmpereModbusClient

_LOGGER = logging.getLogger(__name__)


class AmpereCoordinator(DataUpdateCoordinator[dict[int, float | None]]):
    """
    Coordina la lectura periódica de todos los registros Modbus.

    Los datos que entrega son un dict {register_address: valor_final}.
    Los sensores los consumen directamente por su dirección.
    """

    def __init__(
        self,
        hass: HomeAssistant,
        client: AmpereModbusClient,
        sensor_defs: list[dict],
        scan_interval: int,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self._client = client
        self._sensor_defs = sensor_defs

    def update_sensor_defs(self, sensor_defs: list[dict]) -> None:
        """Actualiza la lista de sensores activos (llamado al reconfigurar)."""
        self._sensor_defs = sensor_defs

    async def _async_update_data(self) -> dict[int, float | None]:
        """
        Lectura principal: coge las direcciones de todos los sensores activos,
        las pide al cliente en bulk (mínimas peticiones Modbus) y devuelve
        el dict de valores decodificados.
        """
        active = [s for s in self._sensor_defs if s.get(SENSOR_KEY_ENABLED, True)]

        if not active:
            return {}

        # Calcular qué registros necesitamos (contando registros extra para tipos 32-bit)
        needed_addresses: set[int] = set()
        for sensor in active:
            addr = sensor[SENSOR_KEY_REGISTER]
            dtype = sensor.get(SENSOR_KEY_DTYPE, "uint16")
            needed_addresses.add(addr)
            if "32" in dtype:
                needed_addresses.add(addr + 1)

        # Leer todos los registros necesarios en bulk
        # (read_bulk gestiona su propia conexión: conecta, lee, desconecta)
        raw_map: dict[int, int] = await self._client.read_bulk(
            list(needed_addresses)
        )

        if not raw_map:
            raise UpdateFailed("Sin respuesta Modbus — comprueba IP y slave ID")

        # Decodificar cada sensor
        result: dict[int, float | None] = {}
        for sensor in active:
            addr = sensor[SENSOR_KEY_REGISTER]
            dtype = sensor.get(SENSOR_KEY_DTYPE, "uint16")
            scale = sensor.get(SENSOR_KEY_SCALE, 1.0)

            # Recoger los registros necesarios para este sensor
            regs_needed = AmpereModbusClient.registers_needed(dtype)
            raw_regs: list[int] = []
            valid = True
            for i in range(regs_needed):
                if addr + i in raw_map:
                    raw_regs.append(raw_map[addr + i])
                else:
                    valid = False
                    break

            if valid and raw_regs:
                result[addr] = AmpereModbusClient.decode_value(raw_regs, dtype, scale)
            else:
                result[addr] = None

        return result
