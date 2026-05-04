"""Binary sensors for Ampere Energy."""

from __future__ import annotations

import logging

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    BINARY_SENSOR_KEY_INVERT,
    BINARY_SENSOR_KEY_NAME,
    BINARY_SENSOR_KEY_REGISTERS,
    BINARY_SENSOR_KEY_THRESHOLD,
    CONF_SENSORS,
    DOMAIN,
    PREDEFINED_BINARY_SENSORS,
    SENSOR_KEY_ENABLED,
    SENSOR_KEY_REGISTER,
    merge_predefined_sensors,
)
from .coordinator import AmpereCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["binary_sensor"]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crea los binary sensors a partir de la configuración del entry."""
    coordinator: AmpereCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensor_defs = merge_predefined_sensors(entry.options.get(CONF_SENSORS, []))

    active_registers = {
        sensor_def[SENSOR_KEY_REGISTER]
        for sensor_def in sensor_defs
        if sensor_def.get(SENSOR_KEY_ENABLED, True)
    }

    entities: list[BinarySensorEntity] = []

    for binary_def in PREDEFINED_BINARY_SENSORS:
        registers = binary_def[BINARY_SENSOR_KEY_REGISTERS]
        if any(reg in active_registers for reg in registers):
            entities.append(
                AmpereBinarySensor(
                    coordinator,
                    entry,
                    binary_def,
                )
            )

    async_add_entities(entities)


def _device_info(entry: ConfigEntry, coordinator: AmpereCoordinator) -> DeviceInfo:
    """Agrupa todos los sensores bajo el mismo dispositivo."""
    host = entry.data.get(CONF_HOST, "unknown")
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Ampere Energy",
        manufacturer="Ampere Power Energy, S.L.",
        model=coordinator.device_model or "Ampere.IO Smart-box",
        sw_version=coordinator.device_version,
        configuration_url=f"http://{host}",
    )


class AmpereBinarySensor(
    BinarySensorEntity,
):
    """Binary sensor que indica estados derivedos de registros Modbus."""

    def __init__(
        self,
        coordinator: AmpereCoordinator,
        entry: ConfigEntry,
        binary_def: dict,
    ) -> None:
        self._entry = entry
        self._coordinator = coordinator
        self._name = binary_def[BINARY_SENSOR_KEY_NAME]
        self._registers = binary_def[BINARY_SENSOR_KEY_REGISTERS]
        self._threshold = binary_def.get(BINARY_SENSOR_KEY_THRESHOLD, 0)
        self._invert = binary_def.get(BINARY_SENSOR_KEY_INVERT, False)

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_binary_{self._name}"
        self._attr_name = self._name
        self._attr_device_class = BinarySensorDeviceClass.POWER
        self._attr_entity_category = EntityCategory.DIAGNOSTIC
        self._attr_extra_state_attributes = {
            "source_registers": self._registers,
            "threshold": self._threshold,
            "inverted": self._invert,
        }

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self._entry, self._coordinator)

    @callback
    def _handle_coordinator_update(self) -> None:
        """El coordinator ha actualizado los datos."""
        self._attr_is_on = self._compute_state()
        self.async_write_ha_state()

    def _compute_state(self) -> bool | None:
        """Calcula el estado del binary sensor."""
        if self._coordinator.data is None:
            return None

        values = []
        for reg in self._registers:
            value = self._coordinator.data.get(reg)
            if value is None:
                return None
            values.append(value)

        avg_value = sum(values) / len(values) if values else 0

        if self._invert:
            return avg_value < self._threshold

        return avg_value > self._threshold

    @property
    def is_on(self) -> bool | None:
        return self._compute_state()

    @property
    def available(self) -> bool:
        """Disponible si el coordinator tiene datos."""
        return (
            self._coordinator.last_update_success
            and self._coordinator.data is not None
        )