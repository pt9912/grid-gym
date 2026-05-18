"""Replay-Diff-Klassifikation (`GG-REPLAY-007`).

Vergleicht zwei `ReplaySample`-Sequenzen (`expected` vs.
`actual`) und liefert `ReplayDelta`-Tupel mit Klassifikation
„fachlich" vs. „volatil".

Klassifikations-Regeln:
- **Volatile Felder** sind Vergleichs-irrelevant fuer fachliche
  Korrektheit (z. B. `import_sequence` — interner Mapper-
  Counter). Welle 5 fuehrt eine konfigurierbare
  `volatile_fields`-Liste; der Default ist
  `frozenset({"import_sequence"})` (`_VOLATILE_FIELDS_DEFAULT`).
- **Fachliche Felder** sind alle anderen, inkl. `timestamp`
  (Welle-5-Review SC-1: `GG-REPLAY-002` verlangt
  „Originalzeitstempel werden unveraendert gespeichert" —
  eine Aenderung ist Drift-Indikator, nicht Rauschen).
  Aufrufer koennen `timestamp` per `volatile_fields`-Override
  explizit aufweichen, wenn zwei Quellen unterschiedliche
  ISO-8601-Schreibweisen tragen.

Vergleichs-Pfade (`path`-Feld in `ReplayDelta`):
- `"sample[i].field"` fuer Werte-Mismatches.
- `"sample[i]"` mit `expected="<sample>"` / `actual="<missing>"`
  fuer Laengen-Mismatches (oder umgekehrt).

`tick`-Feld in `ReplayDelta` ist `simulation_time // tick_ms`
— Aufrufer-Pflicht-Parameter ab M2 Welle 2 (Trigger 013
Closure). Default `tick_ms=1000` bewahrt Welle-5-Kompatibilitaet
ohne Backward-Compat-Bruch.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import fields
from typing import Final

from grid_gym.hexagon.core.domain.replay import (
    ReplayDelta,
    ReplayDeltaClassification,
    ReplaySample,
)
from grid_gym.hexagon.core.errors import ReplayInvalidTickMsError

_VOLATILE_FIELDS_DEFAULT: Final[frozenset[str]] = frozenset({"import_sequence"})
"""Default-volatile Felder.

`import_sequence` ist ein interner Mapper-Counter, der zwischen
zwei Laeufen variieren kann, ohne dass das Replay fachlich
abweicht.

`timestamp` ist bewusst NICHT im Default (Welle-5-Review SC-1):
`GG-REPLAY-002` verlangt „Originalzeitstempel werden unveraendert
gespeichert" — eine Aenderung des Roh-Strings ist damit ein
Drift-Indikator, nicht ein Rauschen. Aufrufer, die zwei Quellen
mit unterschiedlichen ISO-8601-Schreibweisen
(`...Z` vs. `...+00:00`) vergleichen wollen, koennen das per
`volatile_fields=frozenset({"import_sequence", "timestamp"})`
explizit aufweichen.
"""


def diff_replay(
    expected: Iterable[ReplaySample],
    actual: Iterable[ReplaySample],
    *,
    tick_ms: int = 1000,
    volatile_fields: frozenset[str] | None = None,
) -> tuple[ReplayDelta, ...]:
    """Vergleicht zwei `ReplaySample`-Sequenzen feldweise und liefert
    klassifizierte `ReplayDelta`-Tupel.

    `tick_ms` (M2 Welle 2, Trigger 013 Closure): definiert die
    Tick-Skala fuer das `tick`-Feld im erzeugten `ReplayDelta`.
    Default `1000` (Welle-5-Kompatibilitaet, keine Backward-Compat-
    Aenderung); muss `> 0` sein, sonst `ReplayInvalidTickMsError`.

    Wenn `volatile_fields=None`, gilt der Default aus
    `_VOLATILE_FIELDS_DEFAULT`. Per Aufrufer-Override kann die
    Liste je Use-Case verschaerft oder gelockert werden.
    """
    if tick_ms <= 0:
        raise ReplayInvalidTickMsError(tick_ms)
    volatile = volatile_fields if volatile_fields is not None else _VOLATILE_FIELDS_DEFAULT
    expected_list = list(expected)
    actual_list = list(actual)
    deltas: list[ReplayDelta] = []
    pair_count = min(len(expected_list), len(actual_list))
    for index in range(pair_count):
        deltas.extend(
            _compare_sample(index, expected_list[index], actual_list[index], volatile, tick_ms)
        )
    if len(actual_list) > pair_count:
        for index in range(pair_count, len(actual_list)):
            sample = actual_list[index]
            deltas.append(
                ReplayDelta(
                    path=f"sample[{index}]",
                    expected="<missing>",
                    actual="<sample>",
                    tick=sample.simulation_time // tick_ms,
                    device_id=sample.device_id,
                    classification=ReplayDeltaClassification.FACHLICH,
                )
            )
    elif len(expected_list) > pair_count:
        for index in range(pair_count, len(expected_list)):
            sample = expected_list[index]
            deltas.append(
                ReplayDelta(
                    path=f"sample[{index}]",
                    expected="<sample>",
                    actual="<missing>",
                    tick=sample.simulation_time // tick_ms,
                    device_id=sample.device_id,
                    classification=ReplayDeltaClassification.FACHLICH,
                )
            )
    return tuple(deltas)


def _compare_sample(
    index: int,
    expected: ReplaySample,
    actual: ReplaySample,
    volatile: frozenset[str],
    tick_ms: int,
) -> list[ReplayDelta]:
    """Feld-fuer-Feld-Vergleich; sammelt Deltas pro abweichendem Feld."""
    deltas: list[ReplayDelta] = []
    for field in fields(ReplaySample):
        name = field.name
        expected_value = getattr(expected, name)
        actual_value = getattr(actual, name)
        if expected_value == actual_value:
            continue
        classification = (
            ReplayDeltaClassification.VOLATIL
            if name in volatile
            else ReplayDeltaClassification.FACHLICH
        )
        deltas.append(
            ReplayDelta(
                path=f"sample[{index}].{name}",
                expected=str(expected_value),
                actual=str(actual_value),
                tick=expected.simulation_time // tick_ms,
                device_id=expected.device_id,
                classification=classification,
            )
        )
    return deltas
