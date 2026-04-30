# Herramienta de mapeo Modbus

Script web para descubrir y documentar los registros Modbus de tu smart-box Ampere.IO.

## Requisitos

- Python 3.8+
- Acceso por red a la smart-box (mismo segmento LAN)

No necesita dependencias externas (solo stdlib de Python).

## Uso

```bash
python modbus_scanner.py --host 172.16.0.220
```

Se abre un servidor web en `http://localhost:8787` con una interfaz para:

- Leer registros en tiempo real (auto-refresco configurable)
- Ver valores en múltiples formatos: uint16, int16, /10, /100, hex, ASCII
- Ver pares de registros como 32-bit (u32, s32, float32, big/little endian)
- Asignar nombres/alias a los registros descubiertos
- Exportar los alias como JSON

## Parámetros

| Parámetro | Default | Descripción |
|---|---|---|
| `--host` | `172.16.0.220` | IP de la smart-box |
| `--port` | `502` | Puerto Modbus TCP |
| `--unit` | `1` | Slave/Unit ID |
| `--func` | `4` | Función Modbus (3=Holding, 4=Input) |
| `--start` | `0` | Registro inicial |
| `--count` | `50` | Cantidad de registros a leer |
| `--web-port` | `8787` | Puerto del servidor web |
| `--refresh` | `3` | Intervalo de refresco en segundos |
| `--names-file` | `~/.openclaw/.../modbus_register_names.json` | Fichero de alias |

## Ejemplo

```bash
# Leer registros 0-99 de un equipo en 192.168.1.50
python modbus_scanner.py --host 192.168.1.50 --start 0 --count 100

# Usar Holding Registers (FC03) en vez de Input (FC04)
python modbus_scanner.py --host 192.168.1.50 --func 3
```

## Registros conocidos (Ampere.IO TW6, FC04, slave 1)

| Reg | Dato | Tipo | Escala | Unidad |
|---|---|---|---|---|
| 1 | Red electrica (+ importa, - exporta) | int16 | x1 | W |
| 5 | Bateria/Casa | int16 | x1 | W |
| 9 | Produccion solar | uint16 | x1 | W |
| 15 | SOC bateria | uint16 | x0.1 | % |
| 25 | Consumo hogar (variante 2) | uint16 | x1 | W |
| 43 | Consumo hogar | uint16 | x1 | W |

> El mapa puede variar segun modelo y firmware. Usa esta herramienta para verificar los tuyos.
