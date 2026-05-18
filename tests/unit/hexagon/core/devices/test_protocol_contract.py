"""Protocol-Adherence-Tests fuer `DeviceModel` (M2 Welle 1).

Pruefen:

- `NullDevice` satisfies das `DeviceModel`-Protocol via
  `isinstance(...)` (`@runtime_checkable`).
- Alle fuenf Protocol-Methoden liefern den erwarteten Rueckgabetyp.
- `snapshot()` enthaelt `version` als **Erst-Feld** (Konvention aus
  M1 Welle 1 / M2 Welle 0a Trigger 014).
- `SnapshotEnvelope.__post_init__` akzeptiert den Geraete-Snapshot
  ohne Verstoss (End-to-End-Verifikation der Konvention gegen den
  Envelope-Composition-Pfad).

**Konvention fuer Folge-Wellen (Welle 2..5):** jede konkrete
Geraete-Implementation wiederholt die Adherence-Pruefung mit ihrer
eigenen Klasse als Parameter und prueft zusaetzlich den Snapshot-
Roundtrip (`from_snapshot(snapshot()) == device` byte-stabil).
Siehe ADR 0013 §5 + M2-Slice-Plan §3 Welle 1.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import FrozenInstanceError
from decimal import Decimal

import pytest

from grid_gym.hexagon.core.devices import DeviceModel
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import (
    DeviceTickContext,
    DeviceTickOutcome,
)
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.snapshot import SnapshotEnvelope
from tests.unit.hexagon.core.devices._fakes import NullDevice
from tests.unit.hexagon.ports.driven._fakes import FixedSeedRandom


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _make_scenario_device(device_id: str = "null-1") -> ScenarioDevice:
    return ScenarioDevice(id=device_id, type="null", params={})


def _make_command(target: str = "null-1") -> Command:
    return Command(
        command_id="cmd-1",
        simulation_time=0,
        target_device_id=target,
        type="ping",
        payload={},
        validation_status="validated",
        result=CommandResult.IGNORED,
    )


def _make_context(tick: int = 0) -> DeviceTickContext:
    return DeviceTickContext(
        tick=tick,
        simulation_time=tick * 1000,
        tick_ms=1000,
    )


# ---------------------------------------------------------------------------
# Protocol-Adherence via isinstance
# ---------------------------------------------------------------------------


def test_null_device_satisfies_device_model_protocol() -> None:
    """`@runtime_checkable` Protocol prueft Vorhandensein der
    Methoden-Namen (nicht Signaturen). NullDevice hat alle fuenf
    Pflicht-Methoden → isinstance-True."""
    device = NullDevice()
    assert isinstance(device, DeviceModel)


def test_plain_object_does_not_satisfy_protocol() -> None:
    """Sanity-Check: ein Plain-Objekt ohne die fuenf Methoden
    matched das Protocol nicht."""

    class NotADevice:
        pass

    assert not isinstance(NotADevice(), DeviceModel)


# ---------------------------------------------------------------------------
# Methoden-Surface
# ---------------------------------------------------------------------------


def test_initialize_stores_scenario_device_and_random() -> None:
    """`initialize(...)` haelt beide Argumente fuer spaeteren
    Zugriff aus `tick()`/`apply_command()` bereit."""
    device = NullDevice()
    scenario_device = _make_scenario_device("battery-1")
    random = FixedSeedRandom(seed=42)
    device.initialize(scenario_device, random)
    assert device.scenario_device is scenario_device
    assert device.random is random


def test_apply_command_returns_command_result_enum() -> None:
    """`apply_command(cmd)` MUSS einen `CommandResult`-Enum-Wert
    zurueckgeben (kein bool/None/str)."""
    device = NullDevice()
    result = device.apply_command(_make_command())
    assert isinstance(result, CommandResult)


def test_tick_returns_device_tick_outcome() -> None:
    """`tick(context)` liefert `DeviceTickOutcome` mit Telemetrie-
    Tuple. NullDevice gibt leeres Tuple zurueck (keine Telemetrie),
    aber der Typ-Vertrag steht."""
    device = NullDevice()
    outcome = device.tick(_make_context(tick=5))
    assert isinstance(outcome, DeviceTickOutcome)
    assert outcome.telemetry == ()


def test_telemetry_returns_tuple() -> None:
    """`telemetry()` liefert ein Tuple (kein list/None)."""
    device = NullDevice()
    assert isinstance(device.telemetry(), tuple)


# ---------------------------------------------------------------------------
# Snapshot-Vertrag (M1 Welle 1 Konvention, M2 Welle 0a Trigger 014)
# ---------------------------------------------------------------------------


def test_snapshot_is_mapping() -> None:
    """`snapshot()` MUSS `Mapping[str, object]` liefern."""
    device = NullDevice()
    state = device.snapshot()
    assert isinstance(state, Mapping)


def test_snapshot_has_version_as_first_field() -> None:
    """Erstfeld-Pflicht (ADR 0013 §2.4): das erste Iterations-Key
    der Snapshot-Map ist `version` und der Wert ist `int`.
    Python-dict-Insertion-Order-Garantie ab 3.7 macht das
    pruefbar."""
    device = NullDevice()
    state = device.snapshot()
    first_key = next(iter(state))
    assert first_key == "version"
    version = state["version"]
    assert isinstance(version, int)
    assert not isinstance(version, bool)


def test_snapshot_envelope_accepts_device_snapshot() -> None:
    """End-to-End-Verifikation: ein NullDevice-Snapshot in
    `SnapshotEnvelope.sub_snapshots` durchlaeuft den Welle-0a-
    `__post_init__`-Check (`version: int`-Erstfeld + Payload-
    Canonical-Walk) ohne Verstoss."""
    device = NullDevice()
    envelope = SnapshotEnvelope(
        version=1,
        run_id="r",
        simulation_time=0,
        sub_snapshots={"devices.null-1": device.snapshot()},
    )
    assert "devices.null-1" in envelope.sub_snapshots


# ---------------------------------------------------------------------------
# Context-/Outcome-Dataclasses sind Frozen
# ---------------------------------------------------------------------------


def test_device_tick_context_is_frozen() -> None:
    """`DeviceTickContext` ist `@dataclass(frozen=True)` —
    AC-DOMAIN-FROZEN."""
    ctx = _make_context(tick=1)
    with pytest.raises(FrozenInstanceError):
        ctx.tick = 2  # type: ignore[misc]


def test_device_tick_outcome_is_frozen() -> None:
    """`DeviceTickOutcome` ebenfalls frozen."""
    outcome = DeviceTickOutcome(telemetry=())
    with pytest.raises(FrozenInstanceError):
        outcome.telemetry = ()  # type: ignore[misc]


def test_device_tick_context_carries_only_sim_time_fields() -> None:
    """Welle-1-Bewusste-Auslassung: kein `random_sub_port`-Feld,
    kein `pending_commands`-Feld (siehe ADR 0013 §2.2/§2.3)."""
    ctx = _make_context(tick=3)
    assert ctx.tick == 3
    assert ctx.simulation_time == 3000
    assert ctx.tick_ms == 1000
    # Es soll KEIN Random-Port- oder Pending-Commands-Feld geben.
    field_names = {f for f in ctx.__dataclass_fields__}
    assert field_names == {"tick", "simulation_time", "tick_ms"}


# ---------------------------------------------------------------------------
# Decimal-Sanitaet (Decimal-Werte sind canonical-zulaessig)
# ---------------------------------------------------------------------------


def test_decimal_payload_is_canonical_compatible_in_envelope() -> None:
    """Sicherheits-Check: ein Geraete-Snapshot mit `Decimal`-Wert
    laeuft durch den `SnapshotEnvelope`-Payload-Canonical-Walk
    (Welle 0a Item 5). Concretete M2-Geraete (Battery) verwenden
    `Decimal` fuer SOC/Leistung."""
    snapshot = {"version": 1, "soc_pct": Decimal("50.000000")}
    envelope = SnapshotEnvelope(
        version=1,
        run_id="r",
        simulation_time=0,
        sub_snapshots={"devices.battery-1": snapshot},
    )
    assert envelope.sub_snapshots["devices.battery-1"]["soc_pct"] == Decimal("50.000000")
