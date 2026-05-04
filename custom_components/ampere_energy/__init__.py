"""Integración myAmpere para Home Assistant."""

from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady

from .const import (
    DOMAIN,
    CONF_SLAVE,
    CONF_FUNCTION,
    CONF_SCAN_INTERVAL,
    CONF_SENSORS,
    CONF_TIMEOUT,
    CONF_MAX_RETRIES,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_TIMEOUT,
    DEFAULT_MAX_RETRIES,
    merge_predefined_sensors,
)
from .modbus_client import AmpereModbusClient
from .coordinator import AmpereCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR, Platform.BINARY_SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Arranca la integración cuando se carga el config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    slave = entry.data[CONF_SLAVE]
    function = entry.data[CONF_FUNCTION]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    timeout = entry.data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT)
    max_retries = entry.data.get(CONF_MAX_RETRIES, DEFAULT_MAX_RETRIES)
    sensor_defs = merge_predefined_sensors(entry.options.get(CONF_SENSORS, []))

    client = AmpereModbusClient(host, port, slave, function, timeout, max_retries)
    can_connect = await client.test_connection()
    if not can_connect:
        raise ConfigEntryNotReady(
            f"No se puede conectar a la smart-box Ampere.IO en {host}:{port}. "
            f"Verifica la IP, el puerto y que el dispositivo esté conectado."
        )

    coordinator = AmpereCoordinator(hass, client, sensor_defs, scan_interval)

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Se llama cuando el usuario guarda cambios en el options flow."""
    _LOGGER.info("Opciones actualizadas, recargando la integración")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Detiene la integración limpiamente."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
