"""Constantes para la integracion Ampere Energy."""

DOMAIN = "ampere_energy"

# Claves de configuracion
CONF_SLAVE = "slave"
CONF_FUNCTION = "function"
CONF_SCAN_INTERVAL = "scan_interval"
CONF_SENSORS = "sensors"

# Funciones Modbus disponibles
FUNCTION_HOLDING = "holding"   # FC03
FUNCTION_INPUT = "input"       # FC04
FUNCTION_OPTIONS = [FUNCTION_HOLDING, FUNCTION_INPUT]

# Tipos de dato soportados
DTYPE_UINT16 = "uint16"
DTYPE_INT16 = "int16"
DTYPE_UINT32_BE = "uint32_be"
DTYPE_INT32_BE = "int32_be"
DTYPE_UINT32_LE = "uint32_le"
DTYPE_INT32_LE = "int32_le"
DTYPE_FLOAT32_BE = "float32_be"
DTYPE_FLOAT32_LE = "float32_le"

DTYPE_OPTIONS = [
    DTYPE_UINT16,
    DTYPE_INT16,
    DTYPE_UINT32_BE,
    DTYPE_INT32_BE,
    DTYPE_UINT32_LE,
    DTYPE_INT32_LE,
    DTYPE_FLOAT32_BE,
    DTYPE_FLOAT32_LE,
]

DTYPE_LABELS = {
    DTYPE_UINT16: "uint16 - Entero sin signo 16 bits (mas comun)",
    DTYPE_INT16: "int16 - Entero con signo 16 bits",
    DTYPE_UINT32_BE: "uint32 Big-Endian - 32 bits, high primero",
    DTYPE_INT32_BE: "int32 Big-Endian - 32 bits con signo, high primero",
    DTYPE_UINT32_LE: "uint32 Little-Endian - 32 bits, low primero",
    DTYPE_INT32_LE: "int32 Little-Endian - 32 bits con signo, low primero",
    DTYPE_FLOAT32_BE: "float32 Big-Endian - IEEE 754, high primero",
    DTYPE_FLOAT32_LE: "float32 Little-Endian - IEEE 754, low primero",
}

# Claves de cada definicion de sensor
SENSOR_KEY_NAME = "name"
SENSOR_KEY_REGISTER = "register"
SENSOR_KEY_DTYPE = "dtype"
SENSOR_KEY_SCALE = "scale"
SENSOR_KEY_PRECISION = "precision"
SENSOR_KEY_UNIT = "unit"
SENSOR_KEY_DEVICE_CLASS = "device_class"
SENSOR_KEY_STATE_CLASS = "state_class"
SENSOR_KEY_ICON = "icon"
SENSOR_KEY_ENABLED = "enabled"
SENSOR_KEY_IS_PREDEFINED = "predefined"   # True = viene del componente
SENSOR_KEY_VALUE_MAP = "value_map"

# Calibraciones conocidas para sensores predefinidos.
VALUE_MAP_SOC_TW6 = "soc_tw6"

# Registros ASCII de identificacion del equipo.
DEVICE_MODEL_REGISTERS = list(range(1000, 1011))
DEVICE_VERSION_REGISTERS = list(range(1016, 1019))

# Claves para sensores derivados de energia (integracion de W a kWh)
ENERGY_KEY_ID = "id"
ENERGY_KEY_NAME = "name"
ENERGY_KEY_SOURCE_REGISTER = "source_register"
ENERGY_KEY_MODE = "mode"
ENERGY_MODE_POSITIVE = "positive"
ENERGY_MODE_NEGATIVE = "negative"

# Valores por defecto
DEFAULT_PORT = 502
DEFAULT_SLAVE = 1
DEFAULT_FUNCTION = FUNCTION_INPUT
DEFAULT_SCAN_INTERVAL = 30
DEFAULT_DTYPE = DTYPE_UINT16
DEFAULT_SCALE = 1.0
DEFAULT_PRECISION = 0

# Valor Modbus que significa "sin dato"
NO_VALUE_SENTINEL = 65535

# Sensores predefinidos que vienen con el componente.
# El usuario los puede editar o deshabilitar desde la UI.
# Estan basados en los registros descubiertos en el Ampere.IO TW6.
PREDEFINED_SENSORS: list[dict] = [
    {
        SENSOR_KEY_NAME: "Produccion solar",
        SENSOR_KEY_REGISTER: 9,
        SENSOR_KEY_DTYPE: DTYPE_UINT16,
        SENSOR_KEY_SCALE: 1.0,
        SENSOR_KEY_PRECISION: 0,
        SENSOR_KEY_UNIT: "W",
        SENSOR_KEY_DEVICE_CLASS: "power",
        SENSOR_KEY_STATE_CLASS: "measurement",
        SENSOR_KEY_ICON: "mdi:solar-panel",
        SENSOR_KEY_ENABLED: True,
        SENSOR_KEY_IS_PREDEFINED: True,
    },
    {
        SENSOR_KEY_NAME: "SOC bateria",
        SENSOR_KEY_REGISTER: 15,
        SENSOR_KEY_DTYPE: DTYPE_UINT16,
        SENSOR_KEY_SCALE: 0.1,
        SENSOR_KEY_PRECISION: 1,
        SENSOR_KEY_UNIT: "%",
        SENSOR_KEY_DEVICE_CLASS: "battery",
        SENSOR_KEY_STATE_CLASS: "measurement",
        SENSOR_KEY_ICON: "mdi:battery",
        SENSOR_KEY_ENABLED: True,
        SENSOR_KEY_IS_PREDEFINED: True,
        SENSOR_KEY_VALUE_MAP: VALUE_MAP_SOC_TW6,
    },
    {
        SENSOR_KEY_NAME: "Red electrica",
        SENSOR_KEY_REGISTER: 1,
        SENSOR_KEY_DTYPE: DTYPE_INT16,
        SENSOR_KEY_SCALE: 1.0,
        SENSOR_KEY_PRECISION: 0,
        SENSOR_KEY_UNIT: "W",
        SENSOR_KEY_DEVICE_CLASS: "power",
        SENSOR_KEY_STATE_CLASS: "measurement",
        SENSOR_KEY_ICON: "mdi:transmission-tower",
        SENSOR_KEY_ENABLED: True,
        SENSOR_KEY_IS_PREDEFINED: True,
    },
    {
        SENSOR_KEY_NAME: "Bateria / Casa",
        SENSOR_KEY_REGISTER: 5,
        SENSOR_KEY_DTYPE: DTYPE_INT16,
        SENSOR_KEY_SCALE: 1.0,
        SENSOR_KEY_PRECISION: 0,
        SENSOR_KEY_UNIT: "W",
        SENSOR_KEY_DEVICE_CLASS: "power",
        SENSOR_KEY_STATE_CLASS: "measurement",
        SENSOR_KEY_ICON: "mdi:home-battery",
        SENSOR_KEY_ENABLED: True,
        SENSOR_KEY_IS_PREDEFINED: True,
    },
    {
        SENSOR_KEY_NAME: "Potencia bateria",
        SENSOR_KEY_REGISTER: 13,
        SENSOR_KEY_DTYPE: DTYPE_INT16,
        SENSOR_KEY_SCALE: 1.0,
        SENSOR_KEY_PRECISION: 0,
        SENSOR_KEY_UNIT: "W",
        SENSOR_KEY_DEVICE_CLASS: "power",
        SENSOR_KEY_STATE_CLASS: "measurement",
        SENSOR_KEY_ICON: "mdi:battery-charging",
        SENSOR_KEY_ENABLED: True,
        SENSOR_KEY_IS_PREDEFINED: True,
    },
    {
        SENSOR_KEY_NAME: "Consumo hogar",
        SENSOR_KEY_REGISTER: 43,
        SENSOR_KEY_DTYPE: DTYPE_UINT16,
        SENSOR_KEY_SCALE: 1.0,
        SENSOR_KEY_PRECISION: 0,
        SENSOR_KEY_UNIT: "W",
        SENSOR_KEY_DEVICE_CLASS: "power",
        SENSOR_KEY_STATE_CLASS: "measurement",
        SENSOR_KEY_ICON: "mdi:home-lightning-bolt",
        SENSOR_KEY_ENABLED: True,
        SENSOR_KEY_IS_PREDEFINED: True,
    },
]

OBSOLETE_PREDEFINED_REGISTERS = {25}

# Sensores kWh acumulados para usar directamente en HA Energy.
# Los registros con signo se dividen en dos contadores monotonicamente crecientes.
DERIVED_ENERGY_SENSORS: list[dict] = [
    {
        ENERGY_KEY_ID: "solar_production_energy",
        ENERGY_KEY_NAME: "Energia produccion solar",
        ENERGY_KEY_SOURCE_REGISTER: 9,
        ENERGY_KEY_MODE: ENERGY_MODE_POSITIVE,
        SENSOR_KEY_ICON: "mdi:solar-power-variant",
    },
    {
        ENERGY_KEY_ID: "home_consumption_energy",
        ENERGY_KEY_NAME: "Energia consumo hogar",
        ENERGY_KEY_SOURCE_REGISTER: 43,
        ENERGY_KEY_MODE: ENERGY_MODE_POSITIVE,
        SENSOR_KEY_ICON: "mdi:home-lightning-bolt",
    },
    {
        ENERGY_KEY_ID: "grid_import_energy",
        ENERGY_KEY_NAME: "Energia importada de red",
        ENERGY_KEY_SOURCE_REGISTER: 1,
        ENERGY_KEY_MODE: ENERGY_MODE_POSITIVE,
        SENSOR_KEY_ICON: "mdi:transmission-tower-import",
    },
    {
        ENERGY_KEY_ID: "grid_export_energy",
        ENERGY_KEY_NAME: "Energia exportada a red",
        ENERGY_KEY_SOURCE_REGISTER: 1,
        ENERGY_KEY_MODE: ENERGY_MODE_NEGATIVE,
        SENSOR_KEY_ICON: "mdi:transmission-tower-export",
    },
    {
        ENERGY_KEY_ID: "battery_discharge_energy",
        ENERGY_KEY_NAME: "Energia descargada bateria",
        ENERGY_KEY_SOURCE_REGISTER: 13,
        ENERGY_KEY_MODE: ENERGY_MODE_POSITIVE,
        SENSOR_KEY_ICON: "mdi:battery-arrow-down",
    },
    {
        ENERGY_KEY_ID: "battery_charge_energy",
        ENERGY_KEY_NAME: "Energia cargada bateria",
        ENERGY_KEY_SOURCE_REGISTER: 13,
        ENERGY_KEY_MODE: ENERGY_MODE_NEGATIVE,
        SENSOR_KEY_ICON: "mdi:battery-arrow-up",
    },
]


def merge_predefined_sensors(sensor_defs: list[dict]) -> list[dict]:
    """Devuelve sensores existentes mas predefinidos nuevos que falten."""
    merged = [
        dict(sensor)
        for sensor in sensor_defs
        if not (
            sensor.get(SENSOR_KEY_IS_PREDEFINED)
            and sensor.get(SENSOR_KEY_REGISTER) in OBSOLETE_PREDEFINED_REGISTERS
        )
    ]
    existing_registers = {sensor.get(SENSOR_KEY_REGISTER) for sensor in merged}
    predefined_by_register = {
        sensor[SENSOR_KEY_REGISTER]: sensor for sensor in PREDEFINED_SENSORS
    }
    for sensor in merged:
        predefined = predefined_by_register.get(sensor.get(SENSOR_KEY_REGISTER))
        if predefined and sensor.get(SENSOR_KEY_IS_PREDEFINED):
            for key, value in predefined.items():
                sensor.setdefault(key, value)
    for predefined in PREDEFINED_SENSORS:
        if predefined[SENSOR_KEY_REGISTER] not in existing_registers:
            merged.append(dict(predefined))
            existing_registers.add(predefined[SENSOR_KEY_REGISTER])
    return merged
