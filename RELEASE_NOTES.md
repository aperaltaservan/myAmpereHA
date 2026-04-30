# Release notes - v0.2.1

Fecha: 30 de abril de 2026

## Resumen

myAmpere v0.2.1 mejora la identificacion del equipo Ampere.IO y corrige sensores predefinidos del modelo TW6.

## Cambios

- Lee los registros ASCII `1000-1010` como modelo/equipo y los registra en Home Assistant como `model`.
- Lee los registros ASCII `1016-1018` como version de firmware y los registra como `sw_version`.
- Anade entidades de diagnostico `Equipo` y `Version` para consultar esos valores desde Home Assistant.
- Elimina el sensor predefinido `Consumo hogar 2` porque el registro `25` no esta identificado correctamente.
- Aplica una calibracion por tramos al SOC de bateria TW6 basada en los puntos observados:
  - lectura 18% -> SOC app 9%
  - lectura 65% -> SOC app 65%
  - lectura 95% -> SOC app 100%
- Optimiza la lectura Modbus por grupos cercanos para evitar leer todo el rango hasta los registros `1000+`.

# Release notes - v0.2.0

Fecha: 30 de abril de 2026

## Resumen

myAmpere v0.2.0 incorpora sensores nuevos orientados a Home Assistant Energy. La integracion ahora expone potencia de bateria y sensores de energia acumulada en kWh calculados a partir de las potencias instantaneas leidas por Modbus.

## Novedades

- Nuevo sensor predefinido `Potencia bateria` sobre el registro Modbus `13`, con unidad `W`, clase `power` e icono de bateria.
- Nuevos sensores derivados de energia acumulada en `kWh`:
  - `Energia produccion solar`
  - `Energia consumo hogar`
  - `Energia importada de red`
  - `Energia exportada a red`
  - `Energia descargada bateria`
  - `Energia cargada bateria`
- Los sensores derivados usan `device_class: energy` y `state_class: total_increasing`, por lo que pueden utilizarse directamente en el panel Energy de Home Assistant.
- La energia acumulada se calcula mediante integracion trapezoidal de la potencia en W.
- Los acumulados se restauran tras reiniciar Home Assistant mediante `RestoreEntity`.
- Las potencias con signo se separan automaticamente en contadores de importacion/exportacion o carga/descarga segun el sentido del flujo.

## Mejoras

- Los sensores predefinidos nuevos se incorporan automaticamente a configuraciones existentes sin reemplazar los sensores que ya tuviera el usuario.
- La informacion del dispositivo se centraliza para que todos los sensores queden agrupados bajo el mismo dispositivo Ampere Energy.
- Se actualiza la version del componente en `manifest.json` a `0.2.0`.

## Compatibilidad y actualizacion

- Version anterior: `v0.1.3`
- Version nueva: `v0.2.0`
- No se requieren cambios manuales de configuracion.
- Tras actualizar, reinicia Home Assistant o recarga la integracion para crear las nuevas entidades.
- Los sensores de energia derivados solo se crean si el registro de potencia fuente esta habilitado.

## Notas tecnicas

- Los sensores de energia evitan integrar intervalos mayores de 1 hora para reducir saltos anormales tras pausas o reinicios.
- Los acumulados empiezan en `0.000 kWh` si no existe estado previo restaurable.
- El calculo local depende del intervalo de escaneo configurado y de la disponibilidad de lecturas Modbus validas.
