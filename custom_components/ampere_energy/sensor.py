"""Sensores de Ampere Energy."""

from __future__ import annotations

import logging
from datetime import UTC, datetime

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntityDescription,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, UnitOfEnergy
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo, EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    CONF_SENSORS,
    DERIVED_ENERGY_SENSORS,
    DOMAIN,
    ENERGY_KEY_ID,
    ENERGY_KEY_MODE,
    ENERGY_KEY_NAME,
    ENERGY_KEY_SOURCE_REGISTER,
    ENERGY_MODE_NEGATIVE,
    SENSOR_KEY_DEVICE_CLASS,
    SENSOR_KEY_DTYPE,
    SENSOR_KEY_ENABLED,
    SENSOR_KEY_ICON,
    SENSOR_KEY_NAME,
    SENSOR_KEY_PRECISION,
    SENSOR_KEY_REGISTER,
    SENSOR_KEY_STATE_CLASS,
    SENSOR_KEY_UNIT,
    SENSOR_KEY_VALUE_MAP,
    VALUE_MAP_SOC_TW6,
    merge_predefined_sensors,
)
from .coordinator import AmpereCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Crea los sensores a partir de la configuracion del entry."""
    coordinator: AmpereCoordinator = hass.data[DOMAIN][entry.entry_id]
    sensors_defs = merge_predefined_sensors(entry.options.get(CONF_SENSORS, []))

    entities: list[SensorEntity] = [
        AmpereEnergySensor(coordinator, entry, sensor_def)
        for sensor_def in sensors_defs
        if sensor_def.get(SENSOR_KEY_ENABLED, True)
    ]

    active_registers = {
        sensor_def[SENSOR_KEY_REGISTER]
        for sensor_def in sensors_defs
        if sensor_def.get(SENSOR_KEY_ENABLED, True)
    }
    entities.extend(
        AmpereEnergyIntegratedSensor(coordinator, entry, energy_def)
        for energy_def in DERIVED_ENERGY_SENSORS
        if energy_def[ENERGY_KEY_SOURCE_REGISTER] in active_registers
    )
    entities.extend(
        [
            AmpereDiagnosticSensor(
                coordinator,
                entry,
                SensorEntityDescription(
                    key="device_model",
                    name="Equipo",
                    icon="mdi:devices",
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
            AmpereDiagnosticSensor(
                coordinator,
                entry,
                SensorEntityDescription(
                    key="device_version",
                    name="Version",
                    icon="mdi:package-variant",
                    entity_category=EntityCategory.DIAGNOSTIC,
                ),
            ),
        ]
    )

    async_add_entities(entities)


def _device_info(entry: ConfigEntry, coordinator: AmpereCoordinator) -> DeviceInfo:
    """Agrupa todos los sensores bajo el mismo dispositivo."""
    host = entry.data.get(CONF_HOST, "unknown")
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name="Ampere Energy",
        manufacturer="Ampere Energy SL",
        model=coordinator.device_model or "Ampere.IO Smart-box",
        sw_version=coordinator.device_version,
        configuration_url=f"http://{host}",
    )


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
        self._register = sensor_def[SENSOR_KEY_REGISTER]
        self._precision = sensor_def.get(SENSOR_KEY_PRECISION, 0)
        self._value_map = sensor_def.get(SENSOR_KEY_VALUE_MAP)

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_reg{self._register}"
        self._attr_name = sensor_def[SENSOR_KEY_NAME]

        unit = sensor_def.get(SENSOR_KEY_UNIT, "")
        self._attr_native_unit_of_measurement = unit if unit else None

        dc = sensor_def.get(SENSOR_KEY_DEVICE_CLASS, "")
        self._attr_device_class = dc if dc else None

        sc = sensor_def.get(SENSOR_KEY_STATE_CLASS, "")
        self._attr_state_class = sc if sc else None

        icon = sensor_def.get(SENSOR_KEY_ICON, "")
        self._attr_icon = icon if icon else None

        self._attr_extra_state_attributes = {
            "registro": self._register,
            "tipo": sensor_def.get(SENSOR_KEY_DTYPE, "uint16"),
        }

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self._entry, self.coordinator)

    @callback
    def _handle_coordinator_update(self) -> None:
        """El coordinator ha actualizado los datos."""
        self._attr_native_value = self._get_value()
        self.async_write_ha_state()

    def _get_value(self) -> float | int | None:
        """Obtiene el valor del dict del coordinator y aplica precision."""
        if self.coordinator.data is None:
            return None
        raw = self.coordinator.data.get(self._register)
        if raw is None:
            return None
        raw = self._map_value(raw)
        if self._precision == 0:
            return int(round(raw))
        return round(raw, self._precision)

    def _map_value(self, value: float) -> float:
        """Aplica calibraciones conocidas a sensores predefinidos."""
        if self._value_map != VALUE_MAP_SOC_TW6:
            return value
        if value <= 65:
            mapped = 9 + ((value - 18) * (65 - 9) / (65 - 18))
        else:
            mapped = 65 + ((value - 65) * (100 - 65) / (95 - 65))
        return min(100.0, max(0.0, mapped))

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


class AmpereEnergyIntegratedSensor(
    CoordinatorEntity[AmpereCoordinator], SensorEntity, RestoreEntity
):
    """Sensor de energia acumulada a partir de una potencia instantanea."""

    def __init__(
        self,
        coordinator: AmpereCoordinator,
        entry: ConfigEntry,
        energy_def: dict,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._source_register = energy_def[ENERGY_KEY_SOURCE_REGISTER]
        self._mode = energy_def[ENERGY_KEY_MODE]
        self._energy_kwh = 0.0
        self._last_power_w: float | None = None
        self._last_update: datetime | None = None

        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{energy_def[ENERGY_KEY_ID]}"
        self._attr_name = energy_def[ENERGY_KEY_NAME]
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_icon = energy_def.get(SENSOR_KEY_ICON)
        self._attr_suggested_display_precision = 3
        self._attr_extra_state_attributes = {
            "source_register": self._source_register,
            "integration": "trapezoidal",
            "source_unit": "W",
        }

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self._entry, self.coordinator)

    async def async_added_to_hass(self) -> None:
        """Restaura el acumulado tras reiniciar Home Assistant."""
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is None:
            return
        try:
            self._energy_kwh = max(0.0, float(last_state.state))
        except (TypeError, ValueError):
            _LOGGER.debug("No se pudo restaurar energia de %s", self.entity_id)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Integra la potencia nueva y publica el acumulado."""
        now = datetime.now(UTC)
        power_w = self._current_power_w()

        if power_w is not None and self._last_power_w is not None and self._last_update:
            elapsed_hours = (now - self._last_update).total_seconds() / 3600
            if 0 < elapsed_hours <= 1:
                avg_power_w = (self._last_power_w + power_w) / 2
                self._energy_kwh += (avg_power_w * elapsed_hours) / 1000

        self._last_power_w = power_w
        self._last_update = now
        self._attr_native_value = self.native_value
        self.async_write_ha_state()

    def _current_power_w(self) -> float | None:
        """Devuelve potencia positiva para el flujo configurado."""
        if self.coordinator.data is None:
            return None
        raw = self.coordinator.data.get(self._source_register)
        if raw is None:
            return None
        value = float(raw)
        if self._mode == ENERGY_MODE_NEGATIVE:
            return max(0.0, -value)
        return max(0.0, value)

    @property
    def native_value(self) -> float:
        return round(self._energy_kwh, 3)

    @property
    def available(self) -> bool:
        """Disponible si el registro fuente tiene dato."""
        return (
            self.coordinator.last_update_success
            and self.coordinator.data is not None
            and self.coordinator.data.get(self._source_register) is not None
        )


class AmpereDiagnosticSensor(CoordinatorEntity[AmpereCoordinator], SensorEntity):
    """Sensor de diagnostico con datos identificativos del equipo."""

    entity_description: SensorEntityDescription

    def __init__(
        self,
        coordinator: AmpereCoordinator,
        entry: ConfigEntry,
        description: SensorEntityDescription,
    ) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self.entity_description = description
        self._attr_unique_id = f"{DOMAIN}_{entry.entry_id}_{description.key}"
        self._attr_name = description.name
        self._attr_icon = description.icon
        self._attr_entity_category = description.entity_category

    @property
    def device_info(self) -> DeviceInfo:
        return _device_info(self._entry, self.coordinator)

    @property
    def native_value(self) -> str | None:
        if self.entity_description.key == "device_model":
            return self.coordinator.device_model
        if self.entity_description.key == "device_version":
            return self.coordinator.device_version
        return None

    @callback
    def _handle_coordinator_update(self) -> None:
        self._attr_native_value = self.native_value
        self.async_write_ha_state()

    @property
    def available(self) -> bool:
        return self.coordinator.last_update_success and self.native_value is not None
