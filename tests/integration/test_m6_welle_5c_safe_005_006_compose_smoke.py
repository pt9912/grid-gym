"""Integration-Smoke fuer `GG-SAFE-005` + `GG-SAFE-006` + Demo-
Compose-Hardening (M6 Welle 5c; SOLLTE-Items + IP/Netz-Beschraenkung).

Sechs Smoke-Tests:

- SAFE-005 (x4): Geraete-Fallback-Verhalten an den vier
  Lastenheft-Z. 2291-Geraeten (Battery / Load / GridConnection /
  PV). Jeder Smoke fuehrt einen ueberschiessenden bzw. Sign-
  Verletzenden Command durch den jeweiligen
  `validate_set_power_command`-Validator und pinnt:
  - REJECTED/LIMITED-Outcome,
  - Alarm-Emission mit `limit_unit="kW"` (bzw. `"pct"` fuer
    Battery-SOC-Alarms),
  - Power-Clamp auf Sicherheits-Wertebereich
    (`pending_power_kw`).

- SAFE-006 (x1): Core-Diff-Algorithm-Substanz. Ein bewusst
  konstruierter `expected`/`actual`-Mismatch belegt alle vier
  Lastenheft-Akzeptanz-Komponenten in einem Aufruf
  (Replay-Diff + volatile Felder + Tick + Klassifikation).

- SAFE-006-Integration (x1): vormals `pytest.skip` (Trigger 036).
  Mit M7-Welle-1b-b (ADR 0049) sind `replay_diff_status`-Metrik +
  ReplaySource-Integration produktiv; der Audit-Trail-Pin belegt
  die Code-Verankerung (Verhalten end-to-end in
  `test_mvp_002_replay_lifecycle_smoke.py`).

- Demo-Compose-Hardening (x1): Quell-Datei-Inspektion von
  `deploy/compose.yml`. Pinnt:
  - Default-Bind auf `127.0.0.1` (`carveouts.md §2.7`-Auflage).
  - ENV-Override-Anker `GRID_GYM_DEMO_HOST_BIND` vorhanden.

Audit-Trail: `docs/user/safe-005-006-fallback-determinism.md` +
`docs/user/demo-compose-hardening.md`.
"""

from __future__ import annotations

from decimal import Decimal
from pathlib import Path

from grid_gym.hexagon.core.devices.battery.commands import (
    COMMAND_TYPE_SET_POWER_KW as BATTERY_CMD,
    validate_set_power_command as battery_validate,
)
from grid_gym.hexagon.core.devices.battery.config import BatteryConfig
from grid_gym.hexagon.core.devices.grid_connection.commands import (
    validate_set_power_command as grid_validate,
)
from grid_gym.hexagon.core.devices.grid_connection.config import (
    GridConnectionConfig,
)
from grid_gym.hexagon.core.devices.load.commands import (
    validate_set_power_command as load_validate,
)
from grid_gym.hexagon.core.devices.load.config import LoadConfig
from grid_gym.hexagon.core.devices.pv.commands import (
    validate_set_power_command as pv_validate,
)
from grid_gym.hexagon.core.devices.pv.config import PvConfig
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.replay import (
    ReplayDeltaClassification,
    ReplaySample,
)
from grid_gym.hexagon.core.replay.diff import diff_replay

_REPO_ROOT = Path(__file__).resolve().parents[2]
_COMPOSE_PATH = _REPO_ROOT / "deploy" / "compose.yml"


def _set_power_command(value: Decimal, *, target_device_id: str) -> Command:
    """Welle-5c-Smoke-Helper: konstruiert einen kanonischen
    `set_power_kw`-Command. Geteilt zwischen allen vier Geraete-
    Smokes, damit die Sicherheitsgrenzen-Auswertung am Validator
    nicht durch divergente Command-Konstruktion verzerrt wird.
    """
    return Command(
        command_id="cmd-welle-5c",
        simulation_time=0,
        target_device_id=target_device_id,
        type=BATTERY_CMD,
        payload={"value": value},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


# ---------------------------------------------------------------------------
# GG-SAFE-005 — Geraete-Fallback-Verhalten (Lastenheft Z. 1380-1385 + Z. 2291)
# ---------------------------------------------------------------------------


def test_safe_005_battery_fallback_canonical() -> None:
    """`GG-SAFE-005` Battery: Power-Ueberschuss wird auf
    `max_charge_kw` geclampt; Alarm-Emission mit `limit_unit="kW"`
    (Lastenheft Z. 2291 Anker `BatteryDevice.apply_command` /
    Sicherheitsgrenzen-Validierung)."""
    config = BatteryConfig(
        capacity_kwh=Decimal("1000"),
        initial_soc_pct=Decimal("50"),
        min_soc_pct=Decimal("10"),
        max_soc_pct=Decimal("90"),
        max_charge_kw=Decimal("500"),
        max_discharge_kw=Decimal("500"),
        charge_efficiency=Decimal("0.95"),
        discharge_efficiency=Decimal("0.95"),
        ramp_kw_per_s=Decimal("50"),
    )
    outcome = battery_validate(
        config=config,
        soc_kwh=Decimal("500"),
        command=_set_power_command(Decimal("9999"), target_device_id="battery-1"),
        device_id="battery-1",
    )
    assert outcome.result is CommandResult.LIMITED
    assert outcome.pending_power_kw == Decimal("500")
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("500")
    assert outcome.alarm.limit_unit == "kW"


def test_safe_005_load_fallback_canonical() -> None:
    """`GG-SAFE-005` Load: Sign-verletzender Command (negativ)
    wird REJECTED — Last bezieht Energie, kein Reverse-Power."""
    config = LoadConfig(rated_power_kw=Decimal("200"))
    outcome = load_validate(
        config=config,
        command=_set_power_command(Decimal("-100"), target_device_id="load-1"),
        device_id="load-1",
    )
    assert outcome.result is CommandResult.REJECTED
    assert outcome.pending_power_kw is None
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("0")
    assert outcome.alarm.limit_unit == "kW"


def test_safe_005_grid_connection_fallback_canonical() -> None:
    """`GG-SAFE-005` GridConnection: Import ueber `max_import_kw`
    wird auf den Cap geclampt; LIMITED + Alarm mit
    `limit_unit="kW"`."""
    config = GridConnectionConfig(
        nominal_voltage_v=Decimal("400"),
        max_import_kw=Decimal("400"),
        max_export_kw=Decimal("300"),
    )
    outcome = grid_validate(
        config=config,
        command=_set_power_command(Decimal("9999"), target_device_id="grid-1"),
        device_id="grid-1",
    )
    assert outcome.result is CommandResult.LIMITED
    assert outcome.pending_power_kw == Decimal("400")
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("400")
    assert outcome.alarm.limit_unit == "kW"


def test_safe_005_pv_fallback_canonical() -> None:
    """`GG-SAFE-005` PV: Sign-verletzender Command (negativ —
    Erzeugungs-Geraet) wird REJECTED; positiver
    ueberschuessiger Command waere LIMITED."""
    config = PvConfig(rated_power_kw=Decimal("250"))
    outcome = pv_validate(
        config=config,
        command=_set_power_command(Decimal("-100"), target_device_id="pv-1"),
        device_id="pv-1",
    )
    assert outcome.result is CommandResult.REJECTED
    assert outcome.pending_power_kw is None
    assert outcome.alarm is not None
    assert outcome.alarm.limit == Decimal("0")
    assert outcome.alarm.limit_unit == "kW"


# ---------------------------------------------------------------------------
# GG-SAFE-006 — Replay-Diff Core-Algorithm (Lastenheft Z. 1387-1393)
# ---------------------------------------------------------------------------


def test_safe_006_diff_replay_core_algorithm_canonical() -> None:
    """`GG-SAFE-006` Core-Diff: zwei `ReplaySample`-Sequenzen mit
    einer fachlichen + einer volatilen Abweichung. Belegt alle
    vier Lastenheft-Akzeptanz-Komponenten in einem Aufruf:
    Replay-Diff (`tuple[ReplayDelta, ...]`), volatile Felder
    (`import_sequence` ist Default-volatile), betroffene Ticks
    (`simulation_time // tick_ms`) und Abweichungsklassifikation
    (`FACHLICH` vs `VOLATIL`).
    """
    expected = ReplaySample(
        timestamp="2026-06-07T00:00:00Z",
        simulation_time=1000,
        device_id="dev-1",
        metric="power_kw",
        value=Decimal("100"),
        unit="kW",
        import_sequence=1,
    )
    actual = ReplaySample(
        timestamp="2026-06-07T00:00:00Z",
        simulation_time=1000,
        device_id="dev-1",
        metric="power_kw",
        value=Decimal("150"),  # fachliche Abweichung
        unit="kW",
        import_sequence=42,  # volatile Abweichung
    )

    deltas = diff_replay([expected], [actual], tick_ms=1000)

    classifications = {d.classification for d in deltas}
    assert ReplayDeltaClassification.FACHLICH in classifications
    assert ReplayDeltaClassification.VOLATIL in classifications

    # Replay-Diff-Komponente: Tupel mit ReplayDelta-Instanzen.
    assert len(deltas) == 2

    # Volatile-Feld-Komponente: import_sequence ist VOLATIL.
    import_seq_delta = next(d for d in deltas if d.path.endswith(".import_sequence"))
    assert import_seq_delta.classification is ReplayDeltaClassification.VOLATIL

    # Tick-Komponente: simulation_time // tick_ms = 1000 // 1000 = 1.
    assert all(d.tick == 1 for d in deltas)

    # Klassifikations-Komponente: value-Delta ist FACHLICH.
    value_delta = next(d for d in deltas if d.path.endswith(".value"))
    assert value_delta.classification is ReplayDeltaClassification.FACHLICH


def test_safe_006_diff_replay_status_integrated_welle_1b_b() -> None:
    """`GG-SAFE-006` (vormals partial via Trigger 036): der Per-Lauf-
    Status-Marker `replay_diff_status` (Architektur §8.2 Z. 820 + 823)
    + die ReplaySource-Integration (Lastenheft Z. 2292) sind mit
    M7-Welle-1b-b (ADR 0049) produktiv. Das Verhalten ist end-to-end
    in `test_mvp_002_replay_lifecycle_smoke.py` gepinnt; dieser
    Audit-Trail-Pin belegt die Code-Verankerung im Core-Spine
    (frueher: grep ueber `src/grid_gym/` nach `replay_diff_status`
    lieferte null Treffer)."""
    tick_loop_src = (
        _REPO_ROOT / "src" / "grid_gym" / "hexagon" / "core" / "simulation" / "tick_loop.py"
    ).read_text(encoding="utf-8")
    assert "replay_diff_status" in tick_loop_src, (
        "GG-SAFE-006: `replay_diff_status`-Emission muss im TickLoop-Spine verankert sein."
    )
    assert "def finalize(" in tick_loop_src, (
        "GG-SAFE-006: Run-Terminal-`finalize()`-Hook muss im TickLoop existieren."
    )


# ---------------------------------------------------------------------------
# Demo-Compose-Hardening (carveouts.md §2.7-Auflage)
# ---------------------------------------------------------------------------


def test_demo_compose_host_bind_defaults_to_loopback() -> None:
    """`carveouts.md §2.7`-Auflage: `deploy/compose.yml` `api`-
    `ports`-Klausel bindet per Default auf `127.0.0.1` und
    bietet ENV-Override ueber `GRID_GYM_DEMO_HOST_BIND`. Quell-
    Datei-Inspektion (keine echte Container-Start-Verkabelung
    noetig — der String-Vertrag genuegt fuer die Auflage).
    """
    text = _COMPOSE_PATH.read_text(encoding="utf-8")
    # Locate the api-service `ports:`-Block via marker line.
    assert "8000:8080" in text, (
        "compose.yml muss den Host-Port-8000-Mapping behalten (make demo Abnahme-URL)."
    )
    assert "127.0.0.1" in text, "Default-Bind muss auf 127.0.0.1 stehen (carveouts.md §2.7)."
    assert "GRID_GYM_DEMO_HOST_BIND" in text, (
        "ENV-Override-Anker muss vorhanden sein, damit Lab-/Remote-"
        "Demo ohne Compose-Edit moeglich ist."
    )
