"""Constantes para la integración Ampere Energy."""

DOMAIN = "ampere_energy"

# Claves de configuración
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
    DTYPE_UINT16:     "uint16 — Entero sin signo 16 bits (más común)",
    DTYPE_INT16:      "int16  — Entero con signo 16 bits",
    DTYPE_UINT32_BE:  "uint32 Big-Endian — 32 bits, high primero",
    DTYPE_INT32_BE:   "int32  Big-Endian — 32 bits con signo, high primero",
    DTYPE_UINT32_LE:  "uint32 Little-Endian — 32 bits, low primero",
    DTYPE_INT32_LE:   "int32  Little-Endian — 32 bits con signo, low primero",
    DTYPE_FLOAT32_BE: "float32 Big-Endian — IEEE 754, high primero",
    DTYPE_FLOAT32_LE: "float32 Little-Endian — IEEE 754, low primero",
}

# Claves de cada definición de sensor
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
# Están basados en los registros descubiertos en el Ampere.IO TW6.
PREDEFINED_SENSORS: list[dict] = [
    {
        SENSOR_KEY_NAME: "Producción solar",
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
        SENSOR_KEY_NAME: "SOC batería",
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
    },
    {
        SENSOR_KEY_NAME: "Red eléctrica",
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
        SENSOR_KEY_NAME: "Batería / Casa",
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
    {
        SENSOR_KEY_NAME: "Consumo hogar 2",
        SENSOR_KEY_REGISTER: 25,
        SENSOR_KEY_DTYPE: DTYPE_UINT16,
        SENSOR_KEY_SCALE: 1.0,
        SENSOR_KEY_PRECISION: 0,
        SENSOR_KEY_UNIT: "W",
        SENSOR_KEY_DEVICE_CLASS: "power",
        SENSOR_KEY_STATE_CLASS: "measurement",
        SENSOR_KEY_ICON: "mdi:home-lightning-bolt-outline",
        SENSOR_KEY_ENABLED: True,
        SENSOR_KEY_IS_PREDEFINED: True,
    },
]
