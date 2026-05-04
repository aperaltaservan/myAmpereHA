# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What is this

Integración personalizada de Home Assistant (custom component) para inversores **Ampere Energy** (Torre, Tower Pro, Square, Hybrid). Se conecta **localmente** a la smart-box **Ampere.IO** mediante **Modbus TCP** usando sockets asyncio crudos (no requiere librerías externas). No hay nube ni API externa.

Se distribuye via HACS como repositorio personalizado (categoría: integration).

## Instalación y desarrollo

No hay sistema de build, bundler ni test runner propios. El desarrollo es directo sobre los fichełos Python.

**Para probar la integración:**
1. Copiar `custom_components/ampere_energy/` en el directorio `config/custom_components/` de Home Assistant.
2. Reiniciar Home Assistant.
3. Añadir la integración desde UI: Ajustes → Dispositivos y servicios → + Añadir integración → "Ampere Energy".

**Versión mínima de HA:** 2024.1.0 (ver `hacs.json`).

## Arquitectura

El flujo de datos es: `ConfigFlow` → `__init__.py` → `AmpereModbusClient` → `AmpereCoordinator` → `AmpereEnergySensor`.

### Ficheros clave

| Fichero | Responsabilidad |
|---|---|
| `const.py` | Todas las constantes: tipos de dato, claves de sensor, `PREDEFINED_SENSORS` |
| `modbus_client.py` | `AmpereModbusClient` — conexión TCP, lectura en bulk, decodificación de tipos |
| `coordinator.py` | `AmpereCoordinator` — polling con `DataUpdateCoordinator`, construye `dict[register: value]` |
| `sensor.py` | `AmpereEnergySensor` — entidad HA, consume datos del coordinator por dirección de registro |
| `config_flow.py` | `AmpereEnergyConfigFlow` (inicial) + `AmpereOptionsFlow` (gestión de sensores) |
| `translations/` | Strings UI en `es.json` y `en.json` |

### Conceptos importantes

- **Sensor definitions** (`list[dict]`): cada sensor es un dict con claves definidas en `const.py` (`SENSOR_KEY_*`). Se guardan en `entry.options[CONF_SENSORS]`.
- **Predefined vs custom**: los sensores predefinidos tienen `predefined: True`; no se pueden borrar, solo deshabilitar (`enabled: False`).
- **Bulk read**: el coordinator pide cada registro **individualmente** (no en rangos) porque el Ampere.IO rechaza rangos con huecos. Ver `modbus_client.py:read_bulk`.
- **Sentinel value**: `65535` (`NO_VALUE_SENTINEL`) indica "sin dato" para tipos uint16/int16.
- **Tipos 32-bit**: consumen 2 registros consecutivos. El coordinator calcula automáticamente los registros adicionales necesarios.
- **Reload automático**: al guardar cambios en el options flow, `_async_update_listener` en `__init__.py` recarga el entry completo.
- **Unique ID**: `{DOMAIN}_{entry_id}_reg{register_address}` — si se añaden dos sensores con el mismo registro, habrá colisión de unique_id.

### Options Flow (pantallas)

```
init → lista sensores + acciones
     → sensor  (editar sensor existente)
     → add     (añadir sensor nuevo)
     delete:N  (inline, sin pantalla extra)
```
