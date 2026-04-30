# Ampere Energy — Integración local para Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

Integración para Home Assistant que conecta **localmente** con la smart-box **Ampere.IO** de los inversores **Ampere Energy** (Torre, Tower Pro, Square) mediante **Modbus TCP**, sin depender de la nube ni de la app MyAmpere.

## ✅ Características

- **100% local** — Sin nube, sin API externa, sin cuenta.
- **Configurable desde la UI de HA** — Sin editar ficheros YAML.
- **Sensores predefinidos** — SOC batería, producción FV, potencia red, consumo hogar.
- **Sensores personalizados** — Añade cualquier registro Modbus desde la interfaz.
- **Todos los tipos de dato** — uint16, int16, uint32, int32, float32, big/little endian.
- **Factor de escala y precisión** configurables por sensor.
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

## 🗺️ Mapa de registros

Los registros conocidos para el modelo **TW6** (función **Input / FC04**, slave **1**):

| Registro | Dato | Tipo | Escala | Unidad |
|---|---|---|---|---|
| 1 | Red eléctrica (+ importa, - exporta) | int16 | ×1 | W |
| 5 | Batería/Casa | int16 | ×1 | W |
| 9 | Producción solar | uint16 | ×1 | W |
| 15 | SOC batería | uint16 | ×0.1 | % |
| 25 | Consumo hogar (variante 2) | uint16 | ×1 | W |
| 27 | Consumo hogar | uint16 | ×1 | W |
| 43 | Consumo hogar probable | uint16 | ×1 | W |

> ⚠️ El mapa de registros puede variar según modelo y versión de firmware.
> Usa la [herramienta de mapeo](tools/README.md) incluida para verificar los tuyos.

## 🔧 Herramienta de mapeo (para desarrolladores)

En la carpeta `tools/` encontrarás el script `modbus_scanner.py` para descubrir registros desconocidos. Consulta `tools/README.md` para instrucciones de uso.

## 🤝 Contribuir

Si tienes un modelo Ampere diferente y has descubierto nuevos registros, ¡abre un Issue o Pull Request! Tu aportación ayuda a toda la comunidad.

## 📄 Licencia

MIT — Libre para uso personal y comercial. Ver `LICENSE`.
