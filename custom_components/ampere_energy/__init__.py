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
    DEFAULT_SCAN_INTERVAL,
)
from .modbus_client import AmpereModbusClient
from .coordinator import AmpereCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = [Platform.SENSOR]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Arranca la integración cuando se carga el config entry."""
    host = entry.data[CONF_HOST]
    port = entry.data[CONF_PORT]
    slave = entry.data[CONF_SLAVE]
    function = entry.data[CONF_FUNCTION]
    scan_interval = entry.data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)
    sensor_defs = entry.options.get(CONF_SENSORS, [])

    # Crear cliente Modbus y verificar conectividad
    client = AmpereModbusClient(host, port, slave, function)
    if not await client.test_connection():
        raise ConfigEntryNotReady(
            f"No se puede conectar a la smart-box Ampere.IO en {host}:{port}"
        )

    # Crear coordinator
    coordinator = AmpereCoordinator(hass, client, sensor_defs, scan_interval)

    # Primera lectura para verificar que hay datos
    await coordinator.async_config_entry_first_refresh()

    # Guardar en hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Registrar el listener para cambios en opciones (reload automático)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    # Registrar las plataformas
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Se llama cuando el usuario guarda cambios en el options flow."""
    _LOGGER.debug("Opciones actualizadas, recargando la integración")
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Detiene la integración limpiamente."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
