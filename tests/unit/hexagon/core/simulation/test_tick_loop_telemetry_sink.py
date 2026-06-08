"""Unit-Tests fuer das `TelemetrySinkPort`-Wiring im `TickLoop`
(M7 Welle 1a, ADR 0047 §2.3).

Pinnt: ein gesetzter `telemetry_sink` bekommt pro Tick exakt die
`TickResult.emitted_telemetry`-Sequenz append-only persistiert
(Insertion-Reihenfolge); `telemetry_sink=None` ist ein sauberer
No-op-Skip (Backward-Compat). Die Sink-Daten-Pfad-Substanz selbst
ist in `tests/unit/adapters/driven/persistence_inmemory/
test_telemetry_sink.py` (in-memory) + im Postgres-Integration-Smoke
gepinnt.
"""

from __future__ import annotations

from grid_gym.adapters.driven.persistence_inmemory import InMemoryTelemetrySink
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom

_RUN_ID = "welle-1a-sink-test"


def _make_loop(*, telemetry_sink: InMemoryTelemetrySink | None) -> TickLoop:
    return TickLoop(
        run_id=_RUN_ID,
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        telemetry_sink=telemetry_sink,
    )


def test_tick_persists_emitted_telemetry_to_sink() -> None:
    """Wiring-Vertrag: nach `tick()` haelt der Sink exakt die
    `TickResult.emitted_telemetry` des Laufs in Insertion-
    Reihenfolge (deviceloser Loop → leere, aber identische
    Sequenz; der Persist-Branch wird ausgefuehrt)."""
    sink = InMemoryTelemetrySink()
    loop = _make_loop(telemetry_sink=sink)
    result = loop.tick()
    assert sink.read_ordered(_RUN_ID) == result.emitted_telemetry


def test_none_sink_is_noop_skip() -> None:
    """Backward-Compat: ohne `telemetry_sink` laeuft `tick()`
    unveraendert (kein Persist-Pfad)."""
    loop = _make_loop(telemetry_sink=None)
    result = loop.tick()
    assert result.emitted_telemetry == ()
