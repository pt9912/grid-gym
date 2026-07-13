"""Register-Map + `float32`-Encode fuer den Modbus-Server-Adapter
(ADR 0075 §2.2; Encode-Oracle: `spec/protocol_profiles.md` „Server-Profile").

Reiner, **pymodbus-freier** Kern (ohne Server testbar): rechnet die Modbus-
Register on-demand aus der geteilten Current-Value-Projektion — kein
materialisierter Datastore im Kern, keine Duplikat-Haltung.

- **Holding-Register (FC03)**: jedes `(device_id, metric)` → `float32` (2 Register,
  Big-Endian, High-Word zuerst) via `struct.pack('>f', float(value))` — die
  deterministische `float32`-Quantisierung (Encode-**Oracle**; der C2-E2E
  vergleicht gegen genau diese Bytes, **nicht** gegen `Decimal == decoded`).
  Fehlender Wert (Projektion leer fuer das Paar) → `0`.
- **Discrete-Input (FC02)**: Quality-Flag pro Mapping (ordinaler Index in
  `register_map`) — `VALID → 1`, sonst `0`; fehlender Wert → `0`. Exponiert den
  ADR-0074-Quality-Marker im Feldbus-Frame.

**Tick-frame-Atomizitaet (Review-Fund C2)**: ein `float32` belegt **zwei**
Register und muss aus **einem** Projektions-Snapshot gerechnet werden — sonst
koennte ein nebenlaeufiger Tick-Update zwischen High- und Low-Word-Read einen
fabrizierten Wert erzeugen (halb alt, halb neu). Der Refresh-Pfad `refresh_frame()`
(und die vollflaechige Sicht `render()`) nimmt darum **genau einen** `snapshot()`
und rechnet den ganzen Frame daraus. Der Snapshot ist tick-frame-atomar
(Referenz-Swap in `CurrentValueProjection`, lock-frei). `refresh_frame()` pusht
dabei **nur** die Read-Fenster (Review-Fund Slice 075: write_map-Sollwert-Register
bleiben unangetastet, sonst wuerde ein Master-Write genullt).

**Determinismus (ADR 0075 §2.5)**: reine Funktion der emittierten Telemetrie;
kein Server-State.
"""

from __future__ import annotations

import math
import struct
from collections.abc import Mapping
from decimal import Decimal
from typing import Final

from grid_gym.adapters.driving._field_current_value import CurrentValueProjection
from grid_gym.adapters.driving.device_server_modbus._config import (
    ModbusServerConfig,
    RegisterMapping,
)
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint

_REGISTER_ZERO: Final[int] = 0
_WORD_HIGH: Final[int] = 0

_Frame = Mapping[tuple[str, str], TelemetryPoint]


def encode_float32(value: Decimal) -> tuple[int, int]:
    """Kodiert `value` als `float32` in zwei Big-Endian-`uint16`-Register.

    Encode-**Oracle** (C0/Slice 074): `struct.pack('>f', float(value))` — die
    deterministische `float32`-Quantisierung; Rueckgabe `(high_word, low_word)`
    (Big-Endian, kein Word-Swap). **Total** (wirft nie), damit ein einzelner
    pathologischer Wert weder den Refresh-Task noch den Start toetet
    (Review-Fund C2):

    - Betrags-Overflow jenseits der `float32`-Reichweite (`|value| > ~3.4e38`,
      wo `struct.pack('>f', ...)` sonst `OverflowError` wirft) → saettigend auf
      `±inf` (IEEE-754-Rundung eines zu grossen Endlichen).
    - Nicht in `float` konvertierbare `Decimal` (`sNaN` → `ValueError`) → `NaN`.

    `nan_injection` ([`GG-FAULT-003`]) selbst liefert **keinen** numerischen NaN
    in die Projektion (es emittiert die endliche Sentinel `Decimal("0")` mit
    `quality=nan`); dieser Zweig ist reine Robustheit gegen beliebige Werte."""
    try:
        as_float = float(value)
    except (ValueError, OverflowError):
        as_float = math.nan
    try:
        packed = struct.pack(">f", as_float)
    except OverflowError:
        packed = struct.pack(">f", math.copysign(math.inf, as_float))
    high, low = struct.unpack(">HH", packed)
    return high, low


class RegisterMap:
    """On-demand-Berechnung der Modbus-Register aus der Projektion (ADR 0075 §2.2).

    Baut bei Konstruktion die statische Adress-Topologie (Holding-Register-
    Adresse → `(mapping, word)`, Discrete-Input-Index → `mapping`); die **Werte**
    werden aus einem Projektions-Snapshot gerechnet.
    """

    def __init__(self, config: ModbusServerConfig, projection: CurrentValueProjection) -> None:
        self._projection: CurrentValueProjection = projection
        self._read_mappings: tuple[RegisterMapping, ...] = tuple(config.register_map)
        self._holding: dict[int, tuple[RegisterMapping, int]] = {}
        self._discrete: dict[int, RegisterMapping] = {}
        for index, mapping in enumerate(config.register_map):
            self._holding[mapping.address] = (mapping, 0)
            self._holding[mapping.address + 1] = (mapping, 1)
            self._discrete[index] = mapping

    def _holding_at(self, frame: _Frame, address: int) -> int:
        entry = self._holding.get(address)
        if entry is None:
            return _REGISTER_ZERO
        mapping, word = entry
        point = frame.get((mapping.device_id, mapping.metric))
        if point is None:
            return _REGISTER_ZERO
        high, low = encode_float32(point.value)
        return high if word == _WORD_HIGH else low

    def _discrete_at(self, frame: _Frame, address: int) -> bool:
        mapping = self._discrete.get(address)
        if mapping is None:
            return False
        point = frame.get((mapping.device_id, mapping.metric))
        return point is not None and point.quality is Quality.VALID

    def holding_register(self, address: int) -> int:
        """Ein Holding-Register (`uint16`) an `address`; `0` fuer eine nicht
        gemappte Adresse oder ein `(device_id, metric)` ohne emittierten Wert."""
        return self._holding_at(self._projection.snapshot(), address)

    def holding_registers(self, address: int, count: int) -> list[int]:
        """`count` Holding-Register ab `address` aus **einem** Snapshot (FC03)."""
        frame = self._projection.snapshot()
        return [self._holding_at(frame, address + offset) for offset in range(count)]

    def discrete_input(self, address: int) -> bool:
        """Quality-Flag an Discrete-Input-`address` (ordinaler Mapping-Index);
        `True` gdw. ein Wert emittiert wurde **und** `quality is VALID`."""
        return self._discrete_at(self._projection.snapshot(), address)

    def discrete_inputs(self, address: int, count: int) -> list[bool]:
        """`count` Discrete-Inputs ab `address` aus **einem** Snapshot (FC02)."""
        frame = self._projection.snapshot()
        return [self._discrete_at(frame, address + offset) for offset in range(count)]

    def render(self, holding_count: int, discrete_count: int) -> tuple[list[int], list[bool]]:
        """Ein **konsistenter Frame** — `(holding_values, discrete_values)` aus
        genau **einem** Projektions-Snapshot. Kein Tearing zwischen den zwei
        Registern eines `float32` und keine Wert/Quality-Divergenz zwischen den
        Bloecken (Review-Fund C2).

        Vollflaechig ueber `[0, holding_count)` — der **Refresh-Task** nutzt statt
        dieser Methode `refresh_frame(...)` (nur Read-Fenster, laesst write_map-
        Register unangetastet, Review-Fund Slice 075). `render` bleibt als
        vollflaechige Snapshot-Sicht (Encode-Oracle-Pin, `test_register_map`)."""
        frame = self._projection.snapshot()
        holding = [self._holding_at(frame, address) for address in range(holding_count)]
        discrete = [self._discrete_at(frame, index) for index in range(discrete_count)]
        return holding, discrete

    def _window_words(self, frame: _Frame, mapping: RegisterMapping) -> list[int]:
        """`[high, low]` eines Read-Mappings aus `frame`; `[0, 0]` ohne Wert."""
        point = frame.get((mapping.device_id, mapping.metric))
        if point is None:
            return [_REGISTER_ZERO, _REGISTER_ZERO]
        high, low = encode_float32(point.value)
        return [high, low]

    def refresh_frame(
        self, discrete_count: int
    ) -> tuple[tuple[tuple[int, list[int]], ...], list[bool]]:
        """Refresh-Push-Frame aus genau **einem** Snapshot (ADR 0075 §2.2):
        je Read-Mapping ein `(address, [high, low])`-`float32`-Fenster + die
        Discrete-Inputs.

        Deckt **nur** die `register_map`-Read-Fenster — die `write_map`-Sollwert-
        Register werden bewusst **nicht** angefasst, damit ein Master-geschriebener
        Sollwert im Datastore erhalten bleibt (Review-Fund Slice 075; siehe
        `_adapter._push`). Ein Snapshot fuer den ganzen Frame → kein Tearing."""
        frame = self._projection.snapshot()
        windows = tuple(
            (mapping.address, self._window_words(frame, mapping)) for mapping in self._read_mappings
        )
        discrete = [self._discrete_at(frame, index) for index in range(discrete_count)]
        return windows, discrete
