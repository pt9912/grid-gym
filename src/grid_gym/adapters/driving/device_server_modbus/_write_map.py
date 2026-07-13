"""Inbound-Write-Decoder fuer den Modbus-Server-Adapter (ADR 0076 §2.1).

Gegenrichtung zu [`_register_map`](./_register_map.py): ein Master-Write auf ein
`write_map`-Fenster (`float32`, 2 Holding-Register) wird zu `(target_device_id,
command_type, Decimal)` dekodiert — der Rohstoff fuer einen `Command`
(`payload={"value": Decimal}`, ADR 0076 §2.1).

Reiner, **pymodbus-freier** Kern (ohne Server testbar): kennt nur die statische
`write_map`-Topologie + das `float32`-Decode-Oracle. Die pymodbus-`SimAction`-Naht
(Funktions-Code-Filter, Enqueue) sitzt im Adapter.

**`float32`-Decode-Oracle**: `struct.unpack('>f', struct.pack('>HH', high, low))`
— die exakte Umkehr von [`encode_float32`](./_register_map.py). Der dekodierte
`float` wird ueber `Decimal(str(...))` in einen `Decimal` gehoben (die
Kanonisierungs-/Command-Payload-Waehrung, `GG-DATA-004`).

**Total gegen pathologische Bitmuster (Review-Haerte)**: ein `float32`-Wort-Paar
kann `NaN`/`±inf` kodieren (z. B. ein Master schreibt ein nicht-endliches
Bitmuster). Ein nicht-endlicher Wert wird **verworfen** (`None`) statt einen
`Decimal('NaN')` in einen `Command` zu tragen — das braeche sowohl die
`canonical_json`-Serialisierung (Materialisierung/`scenario_hash`) als auch
`Decimal`-Vergleiche im Geraete-Command-Vertrag.
"""

from __future__ import annotations

import math
import struct
from dataclasses import dataclass
from decimal import Decimal
from typing import Final

from grid_gym.adapters.driving.device_server_modbus._config import (
    ModbusServerConfig,
    WritableRegisterMapping,
)

_FLOAT32_REGISTERS: Final[int] = 2
_UINT16_MASK: Final[int] = 0xFFFF


def decode_float32(high: int, low: int) -> Decimal | None:
    """Dekodiert zwei Big-Endian-`uint16`-Register als `float32` → `Decimal`.

    Umkehr des Encode-Oracles (`encode_float32`): `struct.unpack('>f', ...)`.
    Liefert `None` fuer ein **nicht-endliches** Ergebnis (`NaN`/`±inf`) — ein
    solches Bitmuster darf nicht in einen `Command` wandern (siehe Modul-Docstring).
    """
    packed = struct.pack(">HH", high & _UINT16_MASK, low & _UINT16_MASK)
    as_float: float = struct.unpack(">f", packed)[0]
    if not math.isfinite(as_float):
        return None
    return Decimal(str(as_float))


@dataclass(frozen=True, slots=True)
class DecodedInboundWrite:
    """Ein dekodierter Inbound-Write (Rohstoff fuer `Command`, ADR 0076 §2.1)."""

    target_device_id: str
    command_type: str
    value: Decimal


class InboundWriteDecoder:
    """Uebersetzt ein Modbus-Write-Fenster in dekodierte Inbound-Writes.

    Baut bei Konstruktion die statische `write_map`-Adress-Topologie
    (`address → WritableRegisterMapping`); `decode(...)` extrahiert je vollstaendig
    ueberdecktem `float32`-Fenster einen `DecodedInboundWrite`.
    """

    def __init__(self, config: ModbusServerConfig) -> None:
        # Nach Adresse sortiert → deterministische Reihenfolge, wenn **ein** Write
        # mehrere Sollwert-Fenster ueberdeckt (Same-Request-Multiplizitaet).
        self._writable: tuple[WritableRegisterMapping, ...] = tuple(
            sorted(config.write_map, key=lambda mapping: mapping.address)
        )

    @property
    def has_writable(self) -> bool:
        """`True` gdw. mindestens ein beschreibbares Fenster konfiguriert ist."""
        return bool(self._writable)

    def decode(self, address: int, values: list[int]) -> tuple[DecodedInboundWrite, ...]:
        """Dekodiert ein Holding-Write `[address, address+len(values))`.

        Fuer jedes `write_map`-Fenster, dessen **beide** Register vollstaendig im
        geschriebenen Bereich liegen, wird der `float32` dekodiert. Ein Teil-Write
        (nur ein halbes Fenster, z. B. FC06 auf ein 2-Register-Sollwert) wird
        **uebersprungen** — er kann keinen vollstaendigen `float32` bilden. Ein
        nicht-endliches Bitmuster wird ebenfalls uebersprungen (`decode_float32`
        liefert `None`).
        """
        end = address + len(values)
        decoded: list[DecodedInboundWrite] = []
        for mapping in self._writable:
            if mapping.address < address or mapping.address + _FLOAT32_REGISTERS > end:
                continue
            offset = mapping.address - address
            value = decode_float32(values[offset], values[offset + 1])
            if value is None:
                continue
            decoded.append(
                DecodedInboundWrite(mapping.target_device_id, mapping.command_type, value)
            )
        return tuple(decoded)
