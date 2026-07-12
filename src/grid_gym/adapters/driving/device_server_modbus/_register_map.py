"""Register-Map + `float32`-Encode fuer den Modbus-Server-Adapter
(ADR 0075 §2.2; Encode-Oracle: `spec/protocol_profiles.md` „Server-Profile").

Reiner, **pymodbus-freier** Kern (ohne Server testbar): rechnet die Modbus-
Register **on-demand** aus der geteilten Current-Value-Projektion — kein
materialisierter Datastore, keil kein Refresh-Task, keine Staleness. Ein Poll
zu beliebiger Zeit sieht den letzten emittierten Wert pro `(device_id, metric)`.

- **Holding-Register (FC03)**: jedes `(device_id, metric)` → `float32` (2 Register,
  Big-Endian, High-Word zuerst) via `struct.pack('>f', float(value))` — die
  deterministische `float32`-Quantisierung (Encode-**Oracle**; der C2-E2E
  vergleicht gegen genau diese Bytes, **nicht** gegen `Decimal == decoded`).
  Fehlender Wert (Projektion leer fuer das Paar) → `0`.
- **Discrete-Input (FC02)**: Quality-Flag pro Mapping (ordinaler Index in
  `register_map`) — `VALID → 1`, sonst `0`; fehlender Wert → `0`. Exponiert den
  ADR-0074-Quality-Marker im Feldbus-Frame.

**Nebenlaeufigkeit (ADR 0075 §2.2)**: `RegisterMap` haelt eine **Referenz** auf
die Projektion (keine Kopie) und liest pro Poll via `latest()` — der Read greift
die aktuelle, tick-frame-atomar getauschte Frame-Referenz ab (lock-frei,
CPython-GIL). Der Poll kommt aus dem Server-Loop-Thread, der Tick-Update aus dem
Driver-Thread.
"""

from __future__ import annotations

import struct
from decimal import Decimal
from typing import Final

from grid_gym.adapters.driving._field_current_value import CurrentValueProjection
from grid_gym.adapters.driving.device_server_modbus._config import (
    ModbusServerConfig,
    RegisterMapping,
)
from grid_gym.hexagon.core.domain.quality import Quality

_REGISTER_ZERO: Final[int] = 0
_WORD_HIGH: Final[int] = 0


def encode_float32(value: Decimal) -> tuple[int, int]:
    """Kodiert `value` als `float32` in zwei Big-Endian-`uint16`-Register.

    Encode-**Oracle** (C0/Slice 074): `struct.pack('>f', float(value))` — die
    deterministische `float32`-Quantisierung; Rueckgabe `(high_word, low_word)`
    (Big-Endian, kein Word-Swap). Nicht-endliche Werte (`NaN`/`Inf` aus dem
    nan_injection-Fault, [`GG-FAULT-003`]) fliessen als das jeweilige
    IEEE-754-Bitmuster durch — konsistent zum Oracle."""
    high, low = struct.unpack(">HH", struct.pack(">f", float(value)))
    return high, low


class RegisterMap:
    """On-demand-Berechnung der Modbus-Register aus der Projektion (ADR 0075 §2.2).

    Baut bei Konstruktion die statische Adress-Topologie (Holding-Register-
    Adresse → `(mapping, word)`, Discrete-Input-Index → `mapping`); die **Werte**
    werden pro Poll frisch aus der Projektion gerechnet.
    """

    def __init__(self, config: ModbusServerConfig, projection: CurrentValueProjection) -> None:
        self._projection: CurrentValueProjection = projection
        self._holding: dict[int, tuple[RegisterMapping, int]] = {}
        self._discrete: dict[int, RegisterMapping] = {}
        for index, mapping in enumerate(config.register_map):
            self._holding[mapping.address] = (mapping, 0)
            self._holding[mapping.address + 1] = (mapping, 1)
            self._discrete[index] = mapping

    def holding_register(self, address: int) -> int:
        """Ein Holding-Register (`uint16`) an `address`; `0` fuer eine nicht
        gemappte Adresse oder ein `(device_id, metric)` ohne emittierten Wert."""
        entry = self._holding.get(address)
        if entry is None:
            return _REGISTER_ZERO
        mapping, word = entry
        point = self._projection.latest(mapping.device_id, mapping.metric)
        if point is None:
            return _REGISTER_ZERO
        high, low = encode_float32(point.value)
        return high if word == _WORD_HIGH else low

    def holding_registers(self, address: int, count: int) -> list[int]:
        """`count` Holding-Register ab `address` (FC03-Read-Serving)."""
        return [self.holding_register(address + offset) for offset in range(count)]

    def discrete_input(self, address: int) -> bool:
        """Quality-Flag an Discrete-Input-`address` (ordinaler Mapping-Index);
        `True` gdw. ein Wert emittiert wurde **und** `quality is VALID`."""
        mapping = self._discrete.get(address)
        if mapping is None:
            return False
        point = self._projection.latest(mapping.device_id, mapping.metric)
        return point is not None and point.quality is Quality.VALID

    def discrete_inputs(self, address: int, count: int) -> list[bool]:
        """`count` Discrete-Inputs ab `address` (FC02-Read-Serving)."""
        return [self.discrete_input(address + offset) for offset in range(count)]
