# AGENTS.md

## Quick facts

- **Type:** Home Assistant custom component (local integration)
- **Distribution:** HACS (custom repository)  
- **HA min version:** 2024.1.0
- **Python:** 3.11+
- **NO external dependencies** — uses raw asyncio sockets, NOT pymodbus library

## Key commands

```bash
# Run tests
pytest tests/

# Lint
ruff check custom_components/ampere_energy/

# Type check (if available)
ruff check custom_components/ampere_energy/
```

## Architecture

```
ConfigFlow → __init__.py → AmpereModbusClient → AmpereCoordinator → Sensor entities
                                 ↓
                          binary_sensor.py
```

**Entry points:**
- `__init__.py:async_setup_entry` — setup flow
- `config_flow.py` — user config UI
- `sensor.py` + `binary_sensor.py` — HA entities

## Critical concepts

- **Bulk read:** Each register requested individually (Ampere.IO rejects ranges with gaps)
- **Sentinel:** `65535` = "no value" for uint16/int16
- **32-bit types:** Use 2 consecutive registers
- **Predefined sensors:** Cannot delete, only disable (`enabled: False`)
- **Retry logic:** `_with_retry()` in modbus_client.py handles reconnection

## Common traps

- Do NOT assume registers are contiguous — always use `read_bulk()`
- Do NOT use pymodbus library — raw sockets implemented in modbus_client.py
- Check `const.py` for all constant definitions (sensor keys, dtypes, defaults)
- Binary sensors depend on power sensors being enabled

## Useful constants in const.py

- `PREDEFINED_SENSORS` — 6 default power sensors
- `DERIVED_ENERGY_SENSORS` — energy kWh (for HA Energy)
- `PREDEFINED_BINARY_SENSORS` — state binary sensors
- `DTYPE_OPTIONS`, `FUNCTION_OPTIONS` — UI dropdowns

## File purposes

| File | Purpose |
|------|---------|
| `const.py` | All constants, sensor definitions |
| `modbus_client.py` | TCP connection, retry, decode |
| `coordinator.py` | Polling, data aggregation |
| `sensor.py` | Power + energy sensors |
| `binary_sensor.py` | State sensors |
| `config_flow.py` | Config + options UI |
| `translations/` | UI strings (es/en) |