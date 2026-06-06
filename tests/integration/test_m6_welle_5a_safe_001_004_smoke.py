"""Integration-Smoke fuer `GG-SAFE-001..004` (M6 Welle 5a;
Quality-Pipeline-Audit).

Vier Smoke-Tests, einer pro Lastenheft-ID:

- SAFE-001: Schema-Validierung wird im Scenario-Loader
  produktiv durchgesetzt (Welle-5a-Audit ✓ produktiv).
- SAFE-002: NaN-Werte werden von `canonical_json` rejected
  (Welle-5a-Audit ✓ produktiv).
- SAFE-003: SmartMeter emittiert `Quality.MISSING` bei pre-
  attach (Welle-5a-Audit ⚠ partial Lücke; voller
  Kommunikationsausfall-Smoke ist `pytest.skip` mit Pointer
  auf Trigger 035).
- SAFE-004: max_age-Substanz fehlt komplett im Repository
  (Welle-5a-Audit ✗ Lücke); Smoke ist `pytest.skip` mit
  Pointer auf Trigger 034.

Audit-Trail: `docs/user/safe-001-004-quality-pipeline.md`.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal

import pytest

from grid_gym.hexagon.core.errors import ScenarioError
from grid_gym.hexagon.core.scenario.loader import load_scenario
from grid_gym.hexagon.core.serialization.canonical import (
    NonFiniteDecimalError,
    canonical_json,
)


def test_safe_001_invalid_scenario_schema_rejected() -> None:
    """`GG-SAFE-001`: Scenario mit Schema-Fehler wird vom Loader
    mit typisiertem `ScenarioError` rejected — kein stilles
    Verschlucken.

    Audit-Trail: `docs/user/safe-001-004-quality-pipeline.md`
    Sektion `GG-SAFE-001`.
    """

    invalid_scenario: Mapping[str, object] = {
        # Pflicht-Top-Level-Keys fehlen: `schema_version`,
        # `tick_ms`, `devices`, etc.
        "garbage_key": 42,
    }

    with pytest.raises(ScenarioError):
        load_scenario(invalid_scenario)


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

    from grid_gym.hexagon.core.domain.device import DeviceTickContext
    from grid_gym.hexagon.core.domain.quality import Quality
    from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
    from grid_gym.hexagon.core.devices.smart_meter.model import SmartMeterDevice
    from tests.unit.hexagon.ports.driven._fakes import FixedSeedRandom

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


@pytest.mark.skip(
    reason=(
        "GG-SAFE-003 voller Akzeptanz-Umfang (Adapter-Kommunikationsausfall + "
        "Alarm-Emission) ist Lücke per Welle-5a-Audit. Siehe Trigger 035 "
        "(docs/plan/planning/open/035-safe-003-comm-failure-missing-quality.md)."
    )
)
def test_safe_003_comm_failure_emits_missing_or_stale() -> None:
    """`GG-SAFE-003` voller Umfang: Adapter-Verbindungs-Verlust →
    Quality.MISSING/STALE + Alarm. **Lücke per Welle-5a-Audit.**

    Aktivierung: Trigger 035 verankert die erwartete Lieferung.
    """

    pytest.fail("Erwartete Substanz fehlt; siehe Trigger 035 fuer den Folge-Pfad.")


@pytest.mark.skip(
    reason=(
        "GG-SAFE-004 max_age-Substanz fehlt komplett im Repository "
        "(Welle-5a-Audit). Siehe Trigger 034 "
        "(docs/plan/planning/open/034-safe-004-max-age-stale-quality.md)."
    )
)
def test_safe_004_stale_data_quality_after_max_age() -> None:
    """`GG-SAFE-004`: Werte deren Sim-Zeitstempel `max_age`
    ueberschreiten erhalten `Quality.STALE`. **Lücke per
    Welle-5a-Audit.**

    Aktivierung: Trigger 034 verankert die erwartete Lieferung
    (`max_age`-Konfigurationsfeld + Quality-Pipeline-Stage).
    """

    pytest.fail("Erwartete Substanz fehlt; siehe Trigger 034 fuer den Folge-Pfad.")
