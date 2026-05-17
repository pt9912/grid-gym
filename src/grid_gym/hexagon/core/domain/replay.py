"""Replay-Domain-Modelle (`GG-REPLAY-001..007`).

`ReplaySample` ist ein historischer Mess-Eintrag aus einer
externen Zeitreihe (CSV oder JSON-Lines, `GG-REPLAY-001`). Der
`mapper` in `hexagon/core/replay/mapper.py` konvertiert raw lines
in `ReplaySample`-Tupel und mappt Original-Timestamps auf
Simulationszeit (`GG-REPLAY-002`).

`ReplayDelta` ist das Diff-Ergebnis aus `diff_replay`
(`GG-REPLAY-007`) — pro Abweichung ein Eintrag mit Pfad,
erwartetem/tatsaechlichem Wert und Klassifikation
(fachlich vs. volatil).

Beide Klassen sind Frozen-Dataclasses (AC-DOMAIN-FROZEN).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from enum import StrEnum


class ReplayDeltaClassification(StrEnum):
    """Klassifikation einer Replay-Abweichung (`GG-REPLAY-007`)."""

    FACHLICH = "fachlich"
    VOLATIL = "volatil"


@dataclass(frozen=True, slots=True)
class ReplaySample:
    """Ein einzelner Replay-Mess-Eintrag (`GG-REPLAY-001`).

    Felder gemaess Akzeptanz: Zeitstempel, Geraete-ID, Metrikname,
    Wert, Einheit. Zusaetzlich tragen wir `simulation_time` als
    abgebildete Sim-Zeit (`GG-REPLAY-002`) und `import_sequence`
    als stabilen Einfuege-Counter (`GG-REPLAY-003`-Tie-Breaking).

    `timestamp` ist die Originalzeit als String (ISO-8601 oder
    rohes Quellen-Format) und bleibt unveraendert
    (`GG-REPLAY-002` Akzeptanz: „Originalzeitstempel werden
    unveraendert gespeichert").
    """

    timestamp: str
    simulation_time: int
    device_id: str
    metric: str
    value: Decimal
    unit: str
    import_sequence: int


@dataclass(frozen=True, slots=True)
class ReplayDelta:
    """Eine Abweichung im Replay-Diff (`GG-REPLAY-007`).

    Felder gemaess Akzeptanz: Pfad, erwarteter Wert, tatsaechlicher
    Wert, Tick, Geraete-ID, Klassifikation.
    """

    path: str
    expected: str
    actual: str
    tick: int
    device_id: str
    classification: ReplayDeltaClassification
