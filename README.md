# myAmpere — Integración local para Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![versión](https://img.shields.io/github/v/release/aperaltaservan/myAmpereHA)](https://github.com/aperaltaservan/myAmpereHA/releases)

Integración para Home Assistant que conecta **localmente** con la smart-box **Ampere.IO** de los inversores **Ampere Energy** (Torre, Tower Pro, Square, Hybrid) mediante **Modbus TCP**, sin depender de la nube ni de la app myAmpere.

## ✅ Características

- **100% local** — Sin nube, sin API externa, sin cuenta.
- **Configurable desde la UI de HA** — Sin editar fichełos YAML.
- **6 sensores predefinidos** — Potencia solar, SOC batería, red, batería, consumo.
- **Sensores de energía integrada** — kWh acumulados para HA Energy.
- **Binary sensors** — Estados (cargando, descargando, produciendo, importando/exportando).
- **Sensores personalizados** — Añade cualquier registro Modbus desde la interfaz.
- **Todos los tipos de dato** — uint16, int16, uint32, int32, float32, big/little endian.
- **Factor de escala y precisión** configurables por sensor.
- **Retry automático** — Reconexión con backoff exponencial ante fallos.
- **Recarga automática** al guardar cambios.

## 📋 Requisitos

- Home Assistant 2024.1.0 o superior.
- HACS instalado.
- Smart-box Ampere.IO accesible por la LAN (misma red que el host de HA).
- Puerto **502 abierto** en la smart-box (Modbus TCP).

## 🚀 Instalación

### Desde HACS (recomendado)

1. HACS → Integraciones → Menú ⋮ → **Repositorios personalizados**.
2. URL: `https://github.com/aperaltaservan/myAmpereHA` — Categoría: **Integración**.
3. Busca "Ampere Energy" y pulsa **Instalar**.
4. Reinicia Home Assistant.

### Manual

1. Copia la carpeta `custom_components/ampere_energy` en `config/custom_components/`.
2. Reinicia Home Assistant.

## ⚙️ Configuración

1. **Ajustes → Dispositivos y servicios → + Añadir integración** → busca "Ampere Energy".
2. Introduce la IP de tu smart-box, el puerto (502), el Slave ID (1) y la función Modbus (normalmente **Input / FC04**).
3. Pulsa **Conectar**.
4. La integración crea automáticamente los sensores predefinidos.

### Añadir o editar sensores

1. **Ajustes → Dispositivos y servicios → Ampere Energy → Configurar**.
2. Selecciona un sensor para editarlo, o elige **➕ Añadir sensor nuevo**.
3. Pulsa **💾 Guardar y cerrar**.
4. La integración se recarga automáticamente.

### Ajustes de conexión

Desde configurar puedes modificar:
- **Dirección IP** de la smart-box.
- **Puerto Modbus TCP** (por defecto 502).
- **Slave ID** (por defecto 1).
- **Función Modbus** (Input/FC04 o Holding/FC03).
- **Intervalo de lectura** (por defecto 30 segundos).
- **Timeout** (por defecto 5 segundos).
- **Reintentos** (por defecto 3).

## 📊 Sensores predefinidos

### Sensores de potencia (W)

| Sensor | Registro | Tipo | Escala | Unidad |
|--------|----------|------|--------|--------|
| Red eléctrica | 1 | int16 | ×1 | W |
| Batería → Casa | 5 | int16 | ×1 | W |
| Producción solar | 9 | uint16 | ×1 | W |
| Potencia batería | 13 | int16 | ×1 | W |
| SOC batería | 15 | uint16 | ×0.1 | % |
| Consumo hogar | 43 | uint16 | ×1 | W |

### Sensores de energía (kWh)

Para usar en **Energy** de Home Assistant:

| Sensor | Registro | Dirección |
|--------|----------|-----------|
| Energía producción solar | 9 | positivo |
| Energía consumo hogar | 43 | positivo |
| Energía importada de red | 1 | positivo |
| Energía exportada a red | 1 | negativo |
| Energía descargada batería | 13 | positivo |
| Energía cargada batería | 13 | negativo |

### Binary sensors (estados)

| Sensor | Registro base | Condición |
|--------|---------------|-----------|
| Cargando batería | 13 | potencia > 0 |
| Descargando batería | 13 | potencia < 0 |
| Produciendo solar | 9 | producción > 0 |
| Importando red | 1 | potencia > 0 |
| Exportando red | 1 | potencia < 0 |

## 🗺️ Mapa de registros

Los registros conocidos para el modelo **TW6** (función **Input / FC04**, slave **1**):

| Registro | Dato | Tipo | Escala | Unidad |
|---|---|---|---|---|
| 1 | Red eléctrica (+ importa, - exporta) | int16 | ×1 | W |
| 5 | Batería/Casa | int16 | ×1 | W |
| 9 | Producción solar | uint16 | ×1 | W |
| 13 | Potencia batería | int16 | ×1 | W |
| 15 | SOC batería | uint16 | ×0.1 | % |
| 43 | Consumo hogar | uint16 | ×1 | W |
| 1000-1010 | Modelo equipo (ASCII) | uint16 | - | - |
| 1016-1019 | Versión firmware (ASCII) | uint16 | - | - |

> ⚠️ El mapa de registros puede variar según modelo y versión de firmware.
> Usa la [herramienta de mapeo](tools/README.md) incluida para verificar los tuyos.

## 🧪 Desarrollo

### Tests unitarios

```bash
pip install pytest pytest-asyncio
pytest tests/
```

### Herramienta de mapeo

En la carpeta `tools/` encontrarás el script `modbus_scanner.py` para descubrir registros desconocidos. Consulta `tools/README.md` para instrucciones de uso.

## 🤝 Contribuir

Si tienes un modelo Ampere diferente y has descubierto nuevos registros, ¡abre un Issue o Pull Request! Tu aportación ayuda a toda la comunidad.

## 📄 Licencia

MIT — Libre para uso personal y comercial. Ver `LICENSE`.