"""Sensores de Ampere Energy."""

from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    CONF_SENSORS,
    SENSOR_KEY_NAME,
    SENSOR_KEY_REGISTER,
    SENSOR_KEY_DTYPE,
    SENSOR_KEY_PRECISION,
    SENSOR_KEY_UNIT,
    SENSOR_KEY_DEVICE_CLASS,
    SENSOR_KEY_STATE_CLASS,
    SENSOR_KEY_ICON,
    SENSOR_KEY_ENABLED,
)
from .coordinator import AmpereCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crea los sensores a partir de la configuración del entry."""
    coordinator: AmpereCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensors_defs = entry.options.get(CONF_SENSORS, [])

    entities = [
        AmpereEnergySensor(coordinator, entry, sensor_def)
        for sensor_def in sensors_defs
        if sensor_def.get(SENSOR_KEY_ENABLED, True)
    ]
    async_add_entities(entities)


class AmpereEnergySensor(CoordinatorEntity[AmpereCoordinator], SensorEntity):
    """Sensor que representa un registro Modbus del inversor Ampere."""

    def __init__(
        self,
        coordinator: AmpereCoordinator,
        entry: ConfigEntry,
        sensor_def: dict,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._def = sensor_def
        self._register = sensor_def[SENSOR_KEY_REGISTER]
        self._precision = sensor_def.get(SENSOR_KEY_PRECISION, 0)

        # Identificador único: dominio + entry_id + dirección de registro
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_reg{self._register}"

        # Nombre visible
        self._attr_name = sensor_def[SENSOR_KEY_NAME]

        # Unidad
        unit = sensor_def.get(SENSOR_KEY_UNIT, "")
        self._attr_native_unit_of_measurement = unit if unit else None

        # Device class
        dc = sensor_def.get(SENSOR_KEY_DEVICE_CLASS, "")
        self._attr_device_class = dc if dc else None

        # State class
        sc = sensor_def.get(SENSOR_KEY_STATE_CLASS, "")
        self._attr_state_class = sc if sc else None

        # Icono
        icon = sensor_def.get(SENSOR_KEY_ICON, "")
        self._attr_icon = icon if icon else None

        # Atributos extra para diagnóstico
        self._attr_extra_state_attributes = {
            "registro": self._register,
            "tipo": sensor_def.get(SENSOR_KEY_DTYPE, "uint16"),
        }

    @property
    def device_info(self) -> DeviceInfo:
        """Agrupa todos los sensores bajo el mismo dispositivo."""
        from homeassistant.const import CONF_HOST
        host = self._entry.data.get(CONF_HOST, "unknown")
        return DeviceInfo(
            identifiers={(DOMAIN, self._entry.entry_id)},
            name="Ampere Energy",
            manufacturer="Ampere Energy SL",
            model="Ampere.IO Smart-box",
            configuration_url=f"http://{host}",
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """El coordinator ha actualizado los datos — refrescar estado."""
        self._attr_native_value = self._get_value()
        self.async_write_ha_state()

    def _get_value(self) -> float | str | None:
        """Obtiene el valor del dict del coordinator y aplica precisión."""
        if self.coordinator.data is None:
            return None
        raw = self.coordinator.data.get(self._register)
        if raw is None:
            return None
        if self._precision == 0:
            return int(round(raw))
        return round(raw, self._precision)

    @property
    def native_value(self) -> float | int | None:
        return self._get_value()

    @property
    def available(self) -> bool:
        """Disponible si el coordinator tiene datos y el valor no es None."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.get(self._register) is not None
        )
