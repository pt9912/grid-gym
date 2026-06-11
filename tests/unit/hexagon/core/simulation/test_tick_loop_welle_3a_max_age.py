"""Unit-Tests fuer die `max_age`-`STALE`-Stage im `TickLoop`
(M7 Welle 3a, ADR 0052; `GG-SAFE-004`).

Pinnt:

- Boundary: strikt `>` markiert (`==` ist nicht „ueberschritten",
  frische Punkte bleiben unmarkiert) — ADR 0052 §2.5.
- Severity-Override: `STALE` ersetzt nur Qualities mit niedrigerer
  `QUALITY_SEVERITY` (VALID/ESTIMATED/LIMITED); schwerere Befunde
  (FAULT_INJECTED/INVALID/NAN/MISSING) dominieren — ADR 0052 §2.3.
- `max_age_ms=None` (Default) ist byte-identischer no-op-Pfad.
- `max_age_ms <= 0` → typisierter `TickLoopInvalidMaxAgeMsError`.
- Determinismus: zwei identisch konfigurierte Laeufe markieren
  identische Punkte (nur Sim-Zeit, AC-NO-TIME) — ADR 0052 §2.4.
- `build_tick_loop`-Symmetrie: `TickLoopWiring.max_age_ms` wird
  an den Konstruktor durchgereicht — ADR 0052 §2.1.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.errors import TickLoopInvalidMaxAgeMsError
from grid_gym.hexagon.core.scenario.loader import TickLoopWiring, build_tick_loop, load_scenario
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.core.simulation._fakes import LaggingEmitterDevice
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom

_RUN_ID = "welle-3a-max-age-test"


def _make_loop(
    devices: tuple[LaggingEmitterDevice, ...],
    *,
    max_age_ms: int | None,
) -> TickLoop:
    return TickLoop(
        run_id=_RUN_ID,
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=devices,
        max_age_ms=max_age_ms,
    )


def test_stale_boundary_strictly_greater_than_max_age() -> None:
    """ADR 0052 §2.5: `(now - simulation_time) > max_age_ms`
    markiert; Gleichheit und frische Punkte bleiben unmarkiert."""
    loop = _make_loop(
        (
            LaggingEmitterDevice("over", lag_ms=1001, quality=Quality.VALID),
            LaggingEmitterDevice("exact", lag_ms=1000, quality=Quality.VALID),
            LaggingEmitterDevice("fresh", lag_ms=0, quality=Quality.VALID),
        ),
        max_age_ms=1000,
    )
    result = loop.tick()
    quality_by_id = {p.device_id: p.quality for p in result.emitted_telemetry}
    assert quality_by_id["over"] is Quality.STALE, "Alter 1001 > 1000 muss STALE markieren"
    assert quality_by_id["exact"] is Quality.VALID, "Alter == max_age ist nicht ueberschritten"
    assert quality_by_id["fresh"] is Quality.VALID, "frischer Punkt bleibt unmarkiert"


def test_stale_marking_preserves_all_other_point_fields() -> None:
    """ADR 0052 §2.2: `dataclasses.replace` tauscht nur `quality`;
    `sequence`/`source`/`value`/`simulation_time` bleiben identisch
    (Scheduler-Tie-Breaking unberuehrt)."""
    loop = _make_loop(
        (LaggingEmitterDevice("over", lag_ms=5000, quality=Quality.VALID),),
        max_age_ms=1000,
    )
    point = loop.tick().emitted_telemetry[0]
    assert point.quality is Quality.STALE
    assert point.device_id == "over"
    assert point.simulation_time == 1000 - 5000
    assert point.value == Decimal("1")
    assert point.source == "test_lagging_emitter"
    assert point.sequence == 1


def test_severity_override_upgrades_only_lower_severities() -> None:
    """ADR 0052 §2.3: STALE (Severity 3) ersetzt VALID/ESTIMATED/
    LIMITED (0..2); FAULT_INJECTED/INVALID/NAN/MISSING (4..7)
    dominieren und bleiben unangetastet."""
    upgraded = (Quality.VALID, Quality.ESTIMATED, Quality.LIMITED)
    dominant = (Quality.FAULT_INJECTED, Quality.INVALID, Quality.NAN, Quality.MISSING)
    devices = tuple(
        LaggingEmitterDevice(f"dev-{quality.value}", lag_ms=2000, quality=quality)
        for quality in upgraded + dominant
    )
    loop = _make_loop(devices, max_age_ms=1000)
    quality_by_id = {p.device_id: p.quality for p in loop.tick().emitted_telemetry}
    for quality in upgraded:
        assert quality_by_id[f"dev-{quality.value}"] is Quality.STALE, (
            f"{quality} (niedrigere Severity) muss zu STALE upgraden"
        )
    for quality in dominant:
        assert quality_by_id[f"dev-{quality.value}"] is quality, (
            f"{quality} (hoehere Severity) muss dominieren"
        )


def test_none_default_keeps_stage_off() -> None:
    """ADR 0052 §2.1: `max_age_ms=None` (Default) laesst auch stark
    nachlaufende Punkte unmarkiert (byte-identischer Bestands-Pfad)."""
    loop = _make_loop(
        (LaggingEmitterDevice("over", lag_ms=100_000, quality=Quality.VALID),),
        max_age_ms=None,
    )
    assert loop.tick().emitted_telemetry[0].quality is Quality.VALID


@pytest.mark.parametrize("invalid_value", [0, -1, -1000])
def test_non_positive_max_age_is_rejected_at_constructor(invalid_value: int) -> None:
    """ADR 0052 §2.1: `max_age_ms <= 0` → typisierter
    `TickLoopInvalidMaxAgeMsError` (kein stiller Unsinn)."""
    with pytest.raises(TickLoopInvalidMaxAgeMsError):
        _make_loop((), max_age_ms=invalid_value)


def test_two_identical_runs_mark_identical_points() -> None:
    """ADR 0052 §2.4: die Stage misst nur Sim-Zeit (AC-NO-TIME) —
    zwei identisch konfigurierte Laeufe emittieren ueber mehrere
    Ticks identische (inkl. STALE-markierter) Streams."""

    def _run() -> tuple[TelemetryPoint, ...]:
        loop = _make_loop(
            (
                LaggingEmitterDevice("over", lag_ms=1500, quality=Quality.VALID),
                LaggingEmitterDevice("fresh", lag_ms=0, quality=Quality.VALID),
            ),
            max_age_ms=1000,
        )
        stream: list[TelemetryPoint] = []
        for _ in range(3):
            stream.extend(loop.tick().emitted_telemetry)
        return tuple(stream)

    first = _run()
    second = _run()
    assert first == second
    assert any(p.quality is Quality.STALE for p in first), (
        "der nachlaufende Emitter muss in jedem Tick STALE markiert sein"
    )


def test_build_tick_loop_passes_max_age_through_wiring() -> None:
    """ADR 0052 §2.1: `TickLoopWiring.max_age_ms` erreicht den
    Konstruktor (Builder-Symmetrie; Praezedenz `replay_snapshot`-
    Kwargs aus ADR 0049 §2.2)."""
    scenario = load_scenario(
        {
            "schema_version": "grid-gym.scenario.v1",
            "metadata": {"id": "welle-3a", "name": "max_age-wiring"},
            "simulation": {"tick_ms": 1000, "duration_s": 60, "seed": 42},
            "devices": [
                {
                    "id": "grid-1",
                    "type": "grid_connection",
                    "params": {
                        "max_import_kw": Decimal("1000"),
                        "max_export_kw": Decimal("1000"),
                        "nominal_voltage_v": Decimal("400"),
                    },
                },
            ],
        }
    ).scenario
    loop = build_tick_loop(
        scenario,
        run_id=_RUN_ID,
        clock=FakeClock(),
        random_root=FixedSeedRandom(seed=42),
        wiring=TickLoopWiring(max_age_ms=1234),
    )
    # Wiring-Pin ueber den privaten Slot: ein Verhaltens-Surrogat
    # braeuchte ein nachlaufendes Scenario-Device, das es produktiv
    # bewusst nicht gibt (ADR 0052 §6 „bewusste Grenze").
    assert loop._max_age_ms == 1234


def test_from_snapshot_reinjects_max_age() -> None:
    """C2-Review-Folge F1: `from_snapshot` nimmt `max_age_ms` als
    Resume-Kwarg (Symmetrie zum Konstruktor, ADR 0052 §2.1) — ein
    resumed Lauf mit re-injizierter Schwelle markiert weiter STALE
    statt die Stage still abzuschalten."""
    original = TickLoop(
        run_id=_RUN_ID,
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        max_age_ms=1000,
    )
    original.tick()
    snap = original.snapshot()

    resumed_clock = FakeClock()
    resumed_clock.advance(1000)
    resumed = TickLoop.from_snapshot(
        snap,
        clock=resumed_clock,
        random=FixedSeedRandom(seed=42),
        devices=(LaggingEmitterDevice("over", lag_ms=5000),),
        max_age_ms=1000,
    )
    point = resumed.tick().emitted_telemetry[0]
    assert point.quality is Quality.STALE, (
        "re-injizierte max_age_ms-Schwelle muss nach Resume weiter markieren"
    )
