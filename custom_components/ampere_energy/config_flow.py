"""Config flow y Options flow para Ampere Energy."""

from __future__ import annotations

import copy
import logging
from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_SLAVE,
    CONF_FUNCTION,
    CONF_SCAN_INTERVAL,
    CONF_SENSORS,
    FUNCTION_OPTIONS,
    DTYPE_OPTIONS,
    DTYPE_LABELS,
    PREDEFINED_SENSORS,
    DEFAULT_PORT,
    DEFAULT_SLAVE,
    DEFAULT_FUNCTION,
    DEFAULT_SCAN_INTERVAL,
    DEFAULT_DTYPE,
    DEFAULT_SCALE,
    DEFAULT_PRECISION,
    SENSOR_KEY_NAME,
    SENSOR_KEY_REGISTER,
    SENSOR_KEY_DTYPE,
    SENSOR_KEY_SCALE,
    SENSOR_KEY_PRECISION,
    SENSOR_KEY_UNIT,
    SENSOR_KEY_DEVICE_CLASS,
    SENSOR_KEY_STATE_CLASS,
    SENSOR_KEY_ICON,
    SENSOR_KEY_ENABLED,
    SENSOR_KEY_IS_PREDEFINED,
)
from .modbus_client import AmpereModbusClient

_LOGGER = logging.getLogger(__name__)

# Clases de dispositivo HA más comunes para inversores
DEVICE_CLASS_OPTIONS = [
    "", "power", "energy", "battery", "voltage", "current",
    "temperature", "frequency", "apparent_power", "reactive_power",
]

STATE_CLASS_OPTIONS = ["", "measurement", "total_increasing", "total"]


def _initial_sensors() -> list[dict]:
    """Devuelve una copia de los sensores predefinidos para un entry nuevo."""
    return copy.deepcopy(PREDEFINED_SENSORS)


class AmpereEnergyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Config flow inicial: recoge IP, puerto, slave, función e intervalo."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            slave = user_input[CONF_SLAVE]
            function = user_input[CONF_FUNCTION]

            # Probar conexión antes de crear el entry
            client = AmpereModbusClient(host, port, slave, function)
            can_connect = await client.test_connection()

            if can_connect:
                await self.async_set_unique_id(f"{host}:{port}:{slave}")
                self._abort_if_unique_id_configured()

                return self.async_create_entry(
                    title=f"myAmpere ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_SLAVE: slave,
                        CONF_FUNCTION: function,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    },
                    options={
                        CONF_SENSORS: _initial_sensors(),
                    },
                )
            else:
                errors["base"] = "cannot_connect"

        schema = vol.Schema({
            vol.Required(CONF_HOST, default="192.168.1.50"): str,
            vol.Required(CONF_PORT, default=DEFAULT_PORT): vol.All(int, vol.Range(1, 65535)),
            vol.Required(CONF_SLAVE, default=DEFAULT_SLAVE): vol.All(int, vol.Range(1, 247)),
            vol.Required(CONF_FUNCTION, default=DEFAULT_FUNCTION): vol.In(FUNCTION_OPTIONS),
            vol.Required(CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL): vol.All(
                int, vol.Range(5, 300)
            ),
        })

        return self.async_show_form(
            step_id="user",
            data_schema=schema,
            errors=errors,
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> "AmpereOptionsFlow":
        return AmpereOptionsFlow(config_entry)


class AmpereOptionsFlow(OptionsFlow):
    """
    Options flow: gestiona la lista de sensores desde la UI.
    
    Pantallas:
      init      → menú principal (lista sensores, añadir, ajustes conexión)
      sensor    → editar un sensor existente (predefinido o custom)
      add       → añadir un sensor nuevo
      confirm_delete → confirmar borrado de un sensor
    """

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._entry = config_entry
        # Copia mutable de los sensores actuales
        self._sensors: list[dict] = copy.deepcopy(
            config_entry.options.get(CONF_SENSORS, _initial_sensors())
        )
        self._editing_index: int | None = None
        self._connection_changed: bool = False

    # ------------------------------------------------------------------
    # Menú principal
    # ------------------------------------------------------------------

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Menú principal: lista de sensores + opciones."""
        if user_input is not None:
            action = user_input.get("action", "")

            if action == "add":
                return await self.async_step_add()

            if action == "connection":
                return await self.async_step_connection()

            if action == "save":
                return self.async_create_entry(
                    title="",
                    data={CONF_SENSORS: self._sensors},
                )

            # El usuario seleccionó un sensor para editar (formato "edit:N")
            if action.startswith("edit:"):
                idx = int(action.split(":")[1])
                self._editing_index = idx
                return await self.async_step_sensor()

            # Eliminar sensor (formato "delete:N")
            if action.startswith("delete:"):
                idx = int(action.split(":")[1])
                sensor = self._sensors[idx]
                if sensor.get(SENSOR_KEY_IS_PREDEFINED):
                    # Los predefinidos no se borran, solo se deshabilitan
                    self._sensors[idx][SENSOR_KEY_ENABLED] = False
                else:
                    self._sensors.pop(idx)
                # Volvemos al menú
                return await self.async_step_init()

        # Construir lista de opciones del selector
        sensor_choices: dict[str, str] = {}
        for i, s in enumerate(self._sensors):
            enabled = s.get(SENSOR_KEY_ENABLED, True)
            predefined = s.get(SENSOR_KEY_IS_PREDEFINED, False)
            tag = ""
            if not enabled:
                tag = " 🔴"
            elif predefined:
                tag = " ⭐"
            label = f"{s[SENSOR_KEY_NAME]} (reg {s[SENSOR_KEY_REGISTER]}){tag}"
            sensor_choices[f"edit:{i}"] = label
            # Añadir opción de borrar/deshabilitar al final
            delete_label = (
                f"🔕 Deshabilitar: {s[SENSOR_KEY_NAME]}"
                if predefined
                else f"🗑️ Eliminar: {s[SENSOR_KEY_NAME]}"
            )
            sensor_choices[f"delete:{i}"] = delete_label

        sensor_choices["add"] = "➕ Añadir sensor nuevo"
        sensor_choices["connection"] = "🔌 Ajustes de conexión (IP, puerto, refresco)"
        sensor_choices["save"] = "💾 Guardar y cerrar"

        schema = vol.Schema({
            vol.Required("action", default="save"): vol.In(sensor_choices),
        })

        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            description_placeholders={
                "total": str(len(self._sensors)),
                "active": str(sum(1 for s in self._sensors if s.get(SENSOR_KEY_ENABLED, True))),
            },
        )

    # ------------------------------------------------------------------
    # Editar sensor existente
    # ------------------------------------------------------------------

    async def async_step_sensor(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Editar un sensor (predefinido o custom)."""
        idx = self._editing_index
        assert idx is not None
        current = self._sensors[idx]

        if user_input is not None:
            # Actualizar los datos del sensor
            self._sensors[idx] = {
                **current,
                SENSOR_KEY_NAME: user_input[SENSOR_KEY_NAME].strip(),
                SENSOR_KEY_REGISTER: user_input[SENSOR_KEY_REGISTER],
                SENSOR_KEY_DTYPE: user_input[SENSOR_KEY_DTYPE],
                SENSOR_KEY_SCALE: user_input[SENSOR_KEY_SCALE],
                SENSOR_KEY_PRECISION: user_input[SENSOR_KEY_PRECISION],
                SENSOR_KEY_UNIT: user_input.get(SENSOR_KEY_UNIT, ""),
                SENSOR_KEY_DEVICE_CLASS: user_input.get(SENSOR_KEY_DEVICE_CLASS, ""),
                SENSOR_KEY_STATE_CLASS: user_input.get(SENSOR_KEY_STATE_CLASS, ""),
                SENSOR_KEY_ICON: user_input.get(SENSOR_KEY_ICON, ""),
                SENSOR_KEY_ENABLED: user_input.get(SENSOR_KEY_ENABLED, True),
            }
            self._editing_index = None
            return await self.async_step_init()

        schema = vol.Schema({
            vol.Required(SENSOR_KEY_NAME, default=current[SENSOR_KEY_NAME]): str,
            vol.Required(SENSOR_KEY_REGISTER, default=current[SENSOR_KEY_REGISTER]): vol.All(
                int, vol.Range(0, 65535)
            ),
            vol.Required(SENSOR_KEY_DTYPE, default=current.get(SENSOR_KEY_DTYPE, DEFAULT_DTYPE)): vol.In(
                {k: v for k, v in DTYPE_LABELS.items()}
            ),
            vol.Required(SENSOR_KEY_SCALE, default=current.get(SENSOR_KEY_SCALE, DEFAULT_SCALE)): vol.All(
                float, vol.Range(min=-1e6, max=1e6)
            ),
            vol.Required(SENSOR_KEY_PRECISION, default=current.get(SENSOR_KEY_PRECISION, DEFAULT_PRECISION)): vol.All(
                int, vol.Range(0, 6)
            ),
            vol.Optional(SENSOR_KEY_UNIT, default=current.get(SENSOR_KEY_UNIT, "")): str,
            vol.Optional(SENSOR_KEY_DEVICE_CLASS, default=current.get(SENSOR_KEY_DEVICE_CLASS, "")): vol.In(
                DEVICE_CLASS_OPTIONS
            ),
            vol.Optional(SENSOR_KEY_STATE_CLASS, default=current.get(SENSOR_KEY_STATE_CLASS, "")): vol.In(
                STATE_CLASS_OPTIONS
            ),
            vol.Optional(SENSOR_KEY_ICON, default=current.get(SENSOR_KEY_ICON, "")): str,
            vol.Required(SENSOR_KEY_ENABLED, default=current.get(SENSOR_KEY_ENABLED, True)): bool,
        })

        return self.async_show_form(
            step_id="sensor",
            data_schema=schema,
            description_placeholders={"sensor_name": current[SENSOR_KEY_NAME]},
        )

    # ------------------------------------------------------------------
    # Ajustes de conexión
    # ------------------------------------------------------------------

    async def async_step_connection(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Editar IP, puerto, slave, función e intervalo de refresco."""
        errors: dict[str, str] = {}
        current_data = self._entry.data

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            port = user_input[CONF_PORT]
            slave = user_input[CONF_SLAVE]
            function = user_input[CONF_FUNCTION]

            # Probar conexión con los nuevos datos
            client = AmpereModbusClient(host, port, slave, function)
            can_connect = await client.test_connection()

            if can_connect:
                # Actualizar entry.data con los nuevos valores
                self.hass.config_entries.async_update_entry(
                    self._entry,
                    title=f"myAmpere ({host})",
                    data={
                        CONF_HOST: host,
                        CONF_PORT: port,
                        CONF_SLAVE: slave,
                        CONF_FUNCTION: function,
                        CONF_SCAN_INTERVAL: user_input[CONF_SCAN_INTERVAL],
                    },
                )
                return await self.async_step_init()
            else:
                errors["base"] = "cannot_connect"

        schema = vol.Schema({
            vol.Required(CONF_HOST, default=current_data.get(CONF_HOST, "192.168.1.50")): str,
            vol.Required(CONF_PORT, default=current_data.get(CONF_PORT, DEFAULT_PORT)): vol.All(
                int, vol.Range(1, 65535)
            ),
            vol.Required(CONF_SLAVE, default=current_data.get(CONF_SLAVE, DEFAULT_SLAVE)): vol.All(
                int, vol.Range(1, 247)
            ),
            vol.Required(CONF_FUNCTION, default=current_data.get(CONF_FUNCTION, DEFAULT_FUNCTION)): vol.In(
                FUNCTION_OPTIONS
            ),
            vol.Required(CONF_SCAN_INTERVAL, default=current_data.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL)): vol.All(
                int, vol.Range(5, 300)
            ),
        })

        return self.async_show_form(
            step_id="connection",
            data_schema=schema,
            errors=errors,
        )

    # ------------------------------------------------------------------
    # Añadir sensor nuevo
    # ------------------------------------------------------------------

    async def async_step_add(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Formulario para añadir un sensor custom nuevo."""
        if user_input is not None:
            new_sensor = {
                SENSOR_KEY_NAME: user_input[SENSOR_KEY_NAME].strip(),
                SENSOR_KEY_REGISTER: user_input[SENSOR_KEY_REGISTER],
                SENSOR_KEY_DTYPE: user_input[SENSOR_KEY_DTYPE],
                SENSOR_KEY_SCALE: user_input[SENSOR_KEY_SCALE],
                SENSOR_KEY_PRECISION: user_input[SENSOR_KEY_PRECISION],
                SENSOR_KEY_UNIT: user_input.get(SENSOR_KEY_UNIT, ""),
                SENSOR_KEY_DEVICE_CLASS: user_input.get(SENSOR_KEY_DEVICE_CLASS, ""),
                SENSOR_KEY_STATE_CLASS: user_input.get(SENSOR_KEY_STATE_CLASS, ""),
                SENSOR_KEY_ICON: user_input.get(SENSOR_KEY_ICON, ""),
                SENSOR_KEY_ENABLED: True,
                SENSOR_KEY_IS_PREDEFINED: False,
            }
            self._sensors.append(new_sensor)
            return await self.async_step_init()

        schema = vol.Schema({
            vol.Required(SENSOR_KEY_NAME): str,
            vol.Required(SENSOR_KEY_REGISTER): vol.All(int, vol.Range(0, 65535)),
            vol.Required(SENSOR_KEY_DTYPE, default=DEFAULT_DTYPE): vol.In(
                {k: v for k, v in DTYPE_LABELS.items()}
            ),
            vol.Required(SENSOR_KEY_SCALE, default=1.0): vol.All(
                float, vol.Range(min=-1e6, max=1e6)
            ),
            vol.Required(SENSOR_KEY_PRECISION, default=0): vol.All(int, vol.Range(0, 6)),
            vol.Optional(SENSOR_KEY_UNIT, default=""): str,
            vol.Optional(SENSOR_KEY_DEVICE_CLASS, default=""): vol.In(DEVICE_CLASS_OPTIONS),
            vol.Optional(SENSOR_KEY_STATE_CLASS, default=""): vol.In(STATE_CLASS_OPTIONS),
            vol.Optional(SENSOR_KEY_ICON, default=""): str,
        })

        return self.async_show_form(
            step_id="add",
            data_schema=schema,
        )
