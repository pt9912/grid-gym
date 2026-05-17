"""ClockPort — zentrale Simulationszeit-Quelle (`GG-ARCH-007`).

Driven-Port-Vertrag fuer `GG-AR-PORT-DRN-001` (Lastenheft
`GG-ARCH-007`): Fachlogik in `hexagon/core/**` darf Simulationszeit
nur ueber `ClockPort.now()` lesen und nie ueber `time.time()`,
`time.monotonic()`, `datetime.now()` etc. (`AC-NO-TIME`,
`ADR 0002 §A-1`).

Welle 2 liefert das Protocol und einen `FakeClock`-Test-Helper unter
`tests/`. Eine produktive `SimulationClock`-Implementation (vom
Tick-Loop getrieben) folgt in Welle 4 mit `core/simulation/`.
"""

from __future__ import annotations

from typing import Protocol

# Simulationszeit in Millisekunden ab Lauf-Start (Konvention aus
# `GG-DATA-005` / `TelemetryPoint.simulation_time`). Kein NewType-
# Wrapper, weil mypy --strict mit `type ...` schon eine nominale
# Verwechslungs-Sicherheit ueber Funktionssignaturen liefert
# (Wand-Plattformen + canonical_json-Vertrag erwarten reines int).
type SimulationTime = int


class ClockPort(Protocol):
    """Zentrale Simulationszeit-Quelle.

    Implementierungen MUESSEN deterministisch sein — `now()` ist
    eine reine Funktion ueber den intern getragenen Zaehlerstand,
    keine Wall-Clock-Quelle. `AC-NO-TIME` erlaubt unter `hexagon/
    core/**` keine andere Zeitquelle.
    """

    def now(self) -> SimulationTime:
        """Liefert den aktuellen Stand der Simulationszeit (ms ab
        Lauf-Start)."""
        ...  # pragma: no cover — Protocol-Stub

    def advance(self, delta_ms: int) -> None:
        """Schiebt die Simulationszeit um `delta_ms` Millisekunden
        nach vorn.

        `delta_ms` MUSS positiv sein (`> 0`). Tick-Loop-Implementationen
        rufen `advance(tick_ms)` einmal pro Tick auf — `tick_ms`
        kommt aus `RunMetadata.tick_ms` (`GG-SIM-002`).
        """
        ...  # pragma: no cover — Protocol-Stub
