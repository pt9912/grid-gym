"""Integration-Smoke fuer `GG-SAFE-001..004` (M6 Welle 5a;
Quality-Pipeline-Audit).

Sieben Smoke-Tests:

- SAFE-001 (x2): Schema-Validierung wird im Scenario-Loader
  produktiv durchgesetzt (Welle-5a-Audit ✓ produktiv); Schwester-
  Akzeptanz fuer wrong-type-Pflichtwert.
- SAFE-002 (x2): NaN/Infinity-Werte werden von `canonical_json`
  rejected (Welle-5a-Audit ✓ produktiv).
- SAFE-003 (x2): SmartMeter-pre-attach-`MISSING` (Teil-Substanz)
  + Adapter-Verbindungsverlust → `MISSING` + Alarm end-to-end
  via `CommFailureGuardedDeviceProtocolPort` (M7-Welle-3b,
  ADR 0053 — reaktiviert aus dem Trigger-035-Skip; Welle-5a-Audit
  war ⚠ partial).
- SAFE-004 (x1): `max_age`-`STALE`-Stage end-to-end (M7-Welle-3a,
  ADR 0052 — reaktiviert aus dem Trigger-034-Skip; Welle-5a-Audit
  war ✗ Lücke).

Audit-Trail: `docs/user/safe-001-004-quality-pipeline.md`.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

import pytest

from grid_gym.adapters.driven._protocol_comm_failure_wrap import (
    CommFailureGuardedDeviceProtocolPort,
)
from grid_gym.adapters.driven.protocol_iec61850 import (
    Iec61850PortReadConnectionLostError,
)
from grid_gym.hexagon.core.devices.smart_meter.model import SmartMeterDevice
from grid_gym.hexagon.core.domain.alarm import Alarm
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.device import DeviceTickContext
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.errors import ScenarioError
from grid_gym.hexagon.core.scenario.loader import load_scenario
from grid_gym.hexagon.core.serialization.canonical import (
    NonFiniteDecimalError,
    canonical_json,
)
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from tests.unit.hexagon.core.simulation._fakes import LaggingEmitterDevice
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


def test_safe_001_invalid_scenario_schema_rejected() -> None:
    """`GG-SAFE-001`: Scenario mit Schema-Fehler wird vom Loader
    mit typisiertem `ScenarioError` rejected — kein stilles
    Verschlucken.

    Audit-Trail: `docs/user/safe-001-004-quality-pipeline.md`
    Sektion `GG-SAFE-001`.
    """

    invalid_scenario: Mapping[str, object] = {
        "garbage_key": 42,
    }

    with pytest.raises(ScenarioError):
        load_scenario(invalid_scenario)


def test_safe_001_invalid_scenario_wrong_type_rejected() -> None:
    """`GG-SAFE-001`-Schwester-Akzeptanz: Scenario mit korrekten
    Pflicht-Keys aber wrong-type-Wert (`tick_ms` als String statt
    Int) wird vom Loader ebenfalls rejected — Schema-Fehler-Pfad
    deckt nicht nur fehlende Keys, sondern auch Typ-Verletzungen.
    """

    wrong_type_scenario: Mapping[str, object] = {
        "schema_version": "grid-gym.scenario.v1",
        "metadata": {"name": "smoke", "description": "safe-001-schwester"},
        "simulation": {"tick_ms": "100", "duration_s": 60, "seed": 42},
        "devices": [],
    }

    with pytest.raises(ScenarioError):
        load_scenario(wrong_type_scenario)


def test_safe_002_nan_value_rejected_at_serialization() -> None:
    """`GG-SAFE-002`: NaN-Werte werden von der canonical_json-
    Pipeline mit `NonFiniteDecimalError` rejected — typisierter
    Fehler statt stiller Verarbeitung.

    Audit-Trail: `docs/user/safe-001-004-quality-pipeline.md`
    Sektion `GG-SAFE-002`.
    """

    payload: dict[str, object] = {"value": Decimal("NaN")}

    with pytest.raises(NonFiniteDecimalError):
        canonical_json(payload)


def test_safe_002_infinity_value_rejected_at_serialization() -> None:
    """`GG-SAFE-002`-Schwester-Akzeptanz: Infinity-Werte ebenfalls
    rejected (canonical_json behandelt NaN + Inf einheitlich)."""

    payload: dict[str, object] = {"value": Decimal("Infinity")}

    with pytest.raises(NonFiniteDecimalError):
        canonical_json(payload)


def test_safe_003_smart_meter_pre_attach_emits_missing() -> None:
    """`GG-SAFE-003` Teil-Substanz: `SmartMeterDevice` emittiert
    `Quality.MISSING` wenn Source-Devices nicht via
    `attach_sources(...)` attached sind (ADR 0018 §2.3).

    **Audit-Hinweis** (Welle-5a-Audit): das ist
    Konfigurations-Pre-Attach-Zustand, NICHT Real-
    Kommunikationsausfall. Voller `GG-SAFE-003`-Akzeptanz-Umfang
    (Adapter-Verbindungs-Verlust + Alarm) ist Lücke; siehe
    [Trigger 035](../plan/planning/open/035-safe-003-comm-failure-missing-quality.md).

    Dieser Smoke-Test deckt nur die Teil-Substanz (existierende
    `Quality.MISSING`-Emission im SmartMeter-Pre-Attach-Zustand).
    """

    device = SmartMeterDevice()
    device.initialize(
        ScenarioDevice(
            id="meter-001",
            type="smart_meter",
            params={
                "aggregate_device_ids": ("source-001",),
                "aggregate_metric_name": "power_kw",
            },
        ),
        FixedSeedRandom(seed=42),
    )
    device.set_run_id("run-safe-003-smoke")
    # Kein `attach_sources(...)` aufgerufen → Pre-Attach-Pfad.
    outcome = device.tick(DeviceTickContext(tick=0, simulation_time=0, tick_ms=100))

    assert outcome.telemetry, "SmartMeter emittiert TelemetryPoint pro Tick"
    assert outcome.telemetry[0].quality is Quality.MISSING, (
        "SmartMeter-pre-attach muss Quality.MISSING emittieren (ADR 0018 §2.3)"
    )


class _ConnectionDroppingAdapter:
    """Test-Double fuer den SAFE-003-Smoke: liefert einen
    erfolgreichen Read, danach kollabiert die Session mid-flight
    (`Iec61850PortReadConnectionLostError` — die praeziseste
    Verbindungsverlust-Erkennung des Bestands,
    `protocol_iec61850/_port.py`)."""

    def __init__(self) -> None:
        self._reads = 0

    def start(self) -> None:
        return None

    def stop(self) -> None:
        return None

    def read(self, target: str) -> TelemetryPoint | None:
        self._reads += 1
        if self._reads == 1:
            return TelemetryPoint(
                run_id="",
                tick=0,
                simulation_time=0,
                device_id=target,
                metric="power_kw",
                value=Decimal("42"),
                unit="kW",
                quality=Quality.VALID,
                source=f"protocol_test.{target}",
                sequence=0,
            )
        raise Iec61850PortReadConnectionLostError(target, "IED1/LD0/MMXU1.TotW", "MX")

    def write(self, target: str, command: Command) -> None:
        _ = target
        _ = command


def test_safe_003_comm_failure_emits_missing_or_stale() -> None:
    """`GG-SAFE-003` voller Umfang: Adapter-Verbindungs-Verlust →
    `Quality.MISSING` + Alarm mit Ziel/Startzeit/Ursache
    (M7-Welle-3b, ADR 0053; reaktiviert aus dem Trigger-035-Skip).

    End-to-End ueber den `CommFailureGuardedDeviceProtocolPort`-
    Wrapper + einen Adapter, der nach erfolgreichem Read die
    Verbindung verliert: der erste Read geht unveraendert durch,
    der Verbindungsverlust liefert den `MISSING`-Point + den
    `adapter_communication_lost`-Alarm (per-Familie-Detail-Pins
    in `tests/unit/adapters/driven/test_protocol_comm_failure_
    wrap.py`).

    Audit-Trail: `docs/user/safe-001-004-quality-pipeline.md`
    Sektion `GG-SAFE-003`.
    """

    alarms: list[Alarm] = []
    clock = FakeClock()
    clock.advance(3000)
    wrapper = CommFailureGuardedDeviceProtocolPort(
        _ConnectionDroppingAdapter(),
        run_id="run-safe-003-smoke",
        clock=clock,
        on_alarm=alarms.append,
    )

    first = wrapper.read("meter-1")
    assert first is not None and first.quality is Quality.VALID, (
        "intakte Verbindung: Original-Point geht unveraendert durch"
    )
    assert alarms == []

    dropped = wrapper.read("meter-1")
    assert dropped is not None and dropped.quality is Quality.MISSING, (
        "Verbindungsverlust muss Quality.MISSING markieren (GG-SAFE-003, ADR 0053 §2.3)"
    )
    assert len(alarms) == 1, "genau ein Alarm pro Kommunikationsausfall"
    alarm = alarms[0]
    assert alarm.code == "adapter_communication_lost"
    assert alarm.target == "meter-1", "Akzeptanz-Pflichtfeld Ziel"
    assert alarm.simulation_time_ms == 3000, "Akzeptanz-Pflichtfeld Startzeit (Sim-Zeit)"
    assert "Iec61850PortReadConnectionLostError" in alarm.message, (
        "Akzeptanz-Pflichtfeld Ursache (dokumentierter Fehlerstatus)"
    )


def test_safe_004_stale_data_quality_after_max_age() -> None:
    """`GG-SAFE-004`: Werte deren Sim-Zeitstempel die konfigurierte
    `max_age` ueberschreiten erhalten deterministisch
    `Quality.STALE` (M7-Welle-3a, ADR 0052; reaktiviert aus dem
    Trigger-034-Skip).

    End-to-End ueber einen `TickLoop` mit `max_age_ms` + einem
    nachlaufenden Emitter: der ueber-alte Punkt flippt auf STALE,
    ein frischer Lauf ohne Schwelle bleibt unmarkiert
    (Boundary-/Override-Detail-Pins in `tests/unit/hexagon/core/
    simulation/test_tick_loop_welle_3a_max_age.py`).

    Audit-Trail: `docs/user/safe-001-004-quality-pipeline.md`
    Sektion `GG-SAFE-004`.
    """

    loop = TickLoop(
        run_id="run-safe-004-smoke",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=(LaggingEmitterDevice(lag_ms=5000),),
        max_age_ms=1000,
    )
    result = loop.tick()

    assert result.emitted_telemetry, "Emitter liefert einen Punkt pro Tick"
    assert result.emitted_telemetry[0].quality is Quality.STALE, (
        "Alter 5000 ms > max_age 1000 ms muss deterministisch "
        "Quality.STALE markieren (GG-SAFE-004, ADR 0052 §2.2/§2.5)"
    )

    stage_off = TickLoop(
        run_id="run-safe-004-smoke-off",
        tick_ms=1000,
        clock=FakeClock(),
        random=FixedSeedRandom(seed=42),
        scheduler=Scheduler(),
        devices=(LaggingEmitterDevice(lag_ms=5000),),
    )
    assert stage_off.tick().emitted_telemetry[0].quality is Quality.VALID, (
        "max_age_ms=None (Default) laesst die Stage aus — Bestands-Pfad unveraendert"
    )
