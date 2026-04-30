"""Cliente Modbus TCP asíncrono para myAmpere.

Usa sockets TCP crudos (asyncio.open_connection) replicando exactamente
el protocolo del mapeador. Cada lectura abre conexión, envía petición,
recibe respuesta y cierra.
"""

from __future__ import annotations

import asyncio
import struct
import logging
import time

from .const import (
    FUNCTION_HOLDING,
    FUNCTION_INPUT,
    DTYPE_UINT16,
    DTYPE_INT16,
    DTYPE_UINT32_BE,
    DTYPE_INT32_BE,
    DTYPE_UINT32_LE,
    DTYPE_INT32_LE,
    DTYPE_FLOAT32_BE,
    DTYPE_FLOAT32_LE,
    NO_VALUE_SENTINEL,
)

_LOGGER = logging.getLogger(__name__)

CHUNK_SIZE = 60  # Registros por petición


class AmpereModbusClient:
    """Gestiona la comunicación Modbus TCP con la smart-box Ampere.IO."""

    def __init__(
        self,
        host: str,
        port: int,
        slave: int,
        function: str,
        timeout: float = 5.0,
    ) -> None:
        self._host = host
        self._port = port
        self._slave = slave
        self._function = function
        self._timeout = timeout

    # ------------------------------------------------------------------
    # Lectura cruda por socket (igual que el mapeador)
    # ------------------------------------------------------------------

    async def _raw_read(self, start: int, count: int) -> list[int] | None:
        """
        Lee 'count' registros Modbus a partir de 'start'.
        Abre conexión TCP, envía petición, recibe respuesta y cierra.
        Protocolo idéntico al mapeador (modbus_read_registers).
        """
        func_code = 4 if self._function == FUNCTION_INPUT else 3
        tid = int(time.time() * 1000) & 0xFFFF

        pdu = struct.pack(">BHH", func_code, start, count)
        mbap = struct.pack(">HHHB", tid, 0, len(pdu) + 1, self._slave)
        request = mbap + pdu

        writer = None
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_connection(self._host, self._port),
                timeout=self._timeout,
            )

            writer.write(request)
            await writer.drain()

            # Leer cabecera MBAP (7 bytes)
            header = await asyncio.wait_for(
                reader.readexactly(7), timeout=self._timeout,
            )
            _tid, _pid, length, _unit = struct.unpack(">HHHB", header)

            # Leer cuerpo
            body = await asyncio.wait_for(
                reader.readexactly(length - 1), timeout=self._timeout,
            )

            # Comprobar excepción Modbus
            if body[0] == (func_code | 0x80):
                exc_code = body[1] if len(body) > 1 else "?"
                _LOGGER.warning(
                    "Excepcion Modbus FC%s reg %s+%s: codigo %s",
                    func_code, start, count, exc_code,
                )
                return None

            if body[0] != func_code:
                _LOGGER.warning(
                    "Funcion inesperada: esperaba %s, recibido %s",
                    func_code, body[0],
                )
                return None

            byte_count = body[1]
            data = body[2 : 2 + byte_count]
            return [
                struct.unpack(">H", data[i : i + 2])[0]
                for i in range(0, len(data), 2)
            ]

        except asyncio.TimeoutError:
            _LOGGER.warning(
                "Timeout conectando/leyendo %s:%s (reg %s+%s)",
                self._host, self._port, start, count,
            )
            return None
        except ConnectionRefusedError:
            _LOGGER.warning(
                "Conexion rechazada %s:%s", self._host, self._port,
            )
            return None
        except OSError as exc:
            _LOGGER.warning(
                "Error de red %s:%s: %s", self._host, self._port, exc,
            )
            return None
        except Exception as exc:
            _LOGGER.warning(
                "Error inesperado _raw_read: %s: %s",
                type(exc).__name__, exc,
            )
            return None
        finally:
            if writer:
                writer.close()
                try:
                    await writer.wait_closed()
                except Exception:
                    pass

    # ------------------------------------------------------------------
    # Lectura en bulk (rango completo como el mapeador)
    # ------------------------------------------------------------------

    async def read_bulk(self, addresses: list[int]) -> dict[int, int]:
        """
        Lee todos los registros necesarios en bloques de rango contiguos.
        Cada bloque abre su propia conexión TCP (como el mapeador).
        Devuelve dict {address: raw_value}.
        """
        if not addresses:
            return {}

        sorted_addrs = sorted(set(addresses))
        addr_set = set(sorted_addrs)
        start = sorted_addrs[0]
        end = sorted_addrs[-1]
        result: dict[int, int] = {}

        pos = start
        while pos <= end:
            count = min(CHUNK_SIZE, end - pos + 1)
            raw = await self._raw_read(pos, count)
            if raw is not None:
                for i, val in enumerate(raw):
                    if (pos + i) in addr_set:
                        result[pos + i] = val
            pos += count

        return result

    # ------------------------------------------------------------------
    # Test de conectividad
    # ------------------------------------------------------------------

    async def test_connection(self) -> bool:
        """Verifica conectividad: abre TCP, lee registro 0, cierra."""
        result = await self._raw_read(0, 1)
        return result is not None

    # ------------------------------------------------------------------
    # Interpretación de tipos de dato
    # ------------------------------------------------------------------

    @staticmethod
    def decode_value(
        raw_registers: list[int],
        dtype: str,
        scale: float = 1.0,
    ) -> float | None:
        """
        Interpreta raw_registers según dtype y aplica escala.
        raw_registers: lista con 1 elemento (16-bit) o 2 (32-bit).
        Devuelve None si el valor es el sentinel 65535 (no value).
        """
        if not raw_registers:
            return None

        r0 = raw_registers[0]

        # Tipos de 16 bits
        if dtype == DTYPE_UINT16:
            if r0 == NO_VALUE_SENTINEL:
                return None
            return round(r0 * scale, 6)

        if dtype == DTYPE_INT16:
            val = r0 - 65536 if r0 > 32767 else r0
            if val == -1 and r0 == NO_VALUE_SENTINEL:
                return None
            return round(val * scale, 6)

        # Tipos de 32 bits — necesitan dos registros
        if len(raw_registers) < 2:
            return None

        r1 = raw_registers[1]

        if dtype == DTYPE_UINT32_BE:
            val = (r0 << 16) | r1
        elif dtype == DTYPE_INT32_BE:
            u = (r0 << 16) | r1
            val = u - (1 << 32) if u >= (1 << 31) else u
        elif dtype == DTYPE_UINT32_LE:
            val = (r1 << 16) | r0
        elif dtype == DTYPE_INT32_LE:
            u = (r1 << 16) | r0
            val = u - (1 << 32) if u >= (1 << 31) else u
        elif dtype == DTYPE_FLOAT32_BE:
            try:
                u = (r0 << 16) | r1
                val = struct.unpack(">f", struct.pack(">I", u))[0]
            except struct.error:
                return None
        elif dtype == DTYPE_FLOAT32_LE:
            try:
                u = (r1 << 16) | r0
                val = struct.unpack(">f", struct.pack(">I", u))[0]
            except struct.error:
                return None
        else:
            _LOGGER.error("Tipo de dato desconocido: %s", dtype)
            return None

        return round(val * scale, 6)

    @staticmethod
    def registers_needed(dtype: str) -> int:
        """Cuántos registros de 16 bits necesita este tipo de dato."""
        return 2 if "32" in dtype else 1
