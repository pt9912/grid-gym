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
from grid_gym.hexagon.core.errors import (
    DeviceAlreadyInitializedError,
    DeviceNotInitializedError,
    VersionError,
)
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
    zurueckgeben (kein bool/None/str). Post-Welle-1-Review C-2:
    `initialize()` ist Vorbedingung."""
    device = NullDevice()
    device.initialize(_make_scenario_device(), FixedSeedRandom(seed=0))
    result = device.apply_command(_make_command())
    assert isinstance(result, CommandResult)


def test_tick_returns_device_tick_outcome() -> None:
    """`tick(context)` liefert `DeviceTickOutcome` mit Telemetrie-
    Tuple. NullDevice gibt leeres Tuple zurueck (keine Telemetrie),
    aber der Typ-Vertrag steht. Post-Welle-1-Review C-2:
    `initialize()` ist Vorbedingung."""
    device = NullDevice()
    device.initialize(_make_scenario_device(), FixedSeedRandom(seed=0))
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
    pruefbar.

    Welle-1-Review L-3: die `bool`-vs-`int`-Pruefung dupliziert
    den Check aus `SnapshotEnvelope.__post_init__` (siehe
    `hexagon/core/domain/snapshot.py:71-72`). Bewusste Doppel-
    Absicherung — ein Refactor an einer Stelle traegt das
    Test-Gegenstueck mit."""
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


def test_decimal_with_excess_precision_passes_envelope_but_fails_encoder() -> None:
    """Welle-1-Review M-2: `GG-DATA-005` schreibt 6 Nachkommastellen
    vor. Der `SnapshotEnvelope`-Payload-Canonical-Walk prueft
    typmaessig (Decimal ist erlaubt), nicht praezisionsmaessig.
    Ein 7-Nachkommastellen-Decimal kommt am Envelope durch, faellt
    aber am `canonical_json`-Encoder mit Tail-Nullen-Erhaltung
    nicht durch — der Encoder akzeptiert beliebige finite Decimals.
    Dieser Test pinnt das Verhalten, damit Welle-2-Battery-Implementierer
    nicht ueberrascht werden: Praezisions-Quantisierung ist
    Aufgabe der Geraete-Ingress-Boundary, nicht des Envelopes."""
    from grid_gym.hexagon.core.serialization.canonical import canonical_json

    # 7 Nachkommastellen — uebersteigt GG-DATA-005-Soll-Praezision.
    snapshot = {"version": 1, "soc_pct": Decimal("50.0123456")}
    envelope = SnapshotEnvelope(
        version=1,
        run_id="r",
        simulation_time=0,
        sub_snapshots={"devices.battery-1": snapshot},
    )
    # Envelope laesst es durch.
    assert envelope.sub_snapshots["devices.battery-1"]["soc_pct"] == Decimal("50.0123456")
    # canonical_json emittiert den Wert wie er ist (Fixed-Point, alle
    # Nachkommastellen) — Quantisierung ist Aufgabe der Ingress-Logik
    # der konkreten Welle-2-Geraete.
    output = canonical_json(snapshot)
    assert b"50.0123456" in output


# ---------------------------------------------------------------------------
# Welle-1-Review M-1: Wrong-Signature- und Missing-Method-Negativ-Pfade
# ---------------------------------------------------------------------------


def test_class_missing_one_method_fails_protocol() -> None:
    """`@runtime_checkable typing.Protocol` prueft Methoden-Namen.
    Eine Klasse mit 4 von 5 Methoden + Property faellt durch
    isinstance. Welle-2-Implementierer trippen sonst auf "ich habe
    alle Methoden ausser einer und das funktioniert irgendwie noch"."""

    class MissingFromSnapshot:
        @property
        def device_id(self) -> str:
            return ""

        def initialize(self, scenario_device, random) -> None:  # type: ignore[no-untyped-def]
            pass

        def apply_command(self, command):  # type: ignore[no-untyped-def]
            return CommandResult.IGNORED

        def tick(self, context):  # type: ignore[no-untyped-def]
            return DeviceTickOutcome(telemetry=())

        def snapshot(self):  # type: ignore[no-untyped-def]
            return {"version": 1}

        def telemetry(self) -> tuple[object, ...]:
            return ()

    # `from_snapshot` fehlt — Protocol verwirft.
    assert not isinstance(MissingFromSnapshot(), DeviceModel)


def test_class_missing_device_id_property_fails_protocol() -> None:
    """`device_id` ist Pflicht-Property (ADR 0013 §2.7).
    Implementation ohne sie faellt durch."""

    class MissingDeviceId:
        def initialize(self, scenario_device, random) -> None:  # type: ignore[no-untyped-def]
            pass

        def apply_command(self, command):  # type: ignore[no-untyped-def]
            return CommandResult.IGNORED

        def tick(self, context):  # type: ignore[no-untyped-def]
            return DeviceTickOutcome(telemetry=())

        def snapshot(self):  # type: ignore[no-untyped-def]
            return {"version": 1}

        def telemetry(self) -> tuple[object, ...]:
            return ()

        @classmethod
        def from_snapshot(cls, state):  # type: ignore[no-untyped-def]
            _ = state  # Test-Stub mit Protocol-Surface; Payload ignoriert.
            return cls()

    assert not isinstance(MissingDeviceId(), DeviceModel)


def test_wrong_signature_still_passes_isinstance() -> None:
    """`@runtime_checkable` prueft nur Namen, NICHT Signaturen.
    Dieser Test dokumentiert die Einschraenkung: eine `tick(self)`-
    Methode ohne `context`-Parameter passt das isinstance ist
    immer noch True. Welle-2-Implementierer muessen daher
    type-checking via mypy strict + Unit-Tests pro Geraet
    machen, nicht isinstance allein."""

    class WrongSignatureTick:
        @property
        def device_id(self) -> str:
            return ""

        def initialize(self, scenario_device, random) -> None:  # type: ignore[no-untyped-def]
            pass

        def apply_command(self, command):  # type: ignore[no-untyped-def]
            return CommandResult.IGNORED

        def tick(self):  # type: ignore[no-untyped-def]  # FALSCH: kein context
            return DeviceTickOutcome(telemetry=())

        def snapshot(self):  # type: ignore[no-untyped-def]
            return {"version": 1}

        def telemetry(self) -> tuple[object, ...]:
            return ()

        @classmethod
        def from_snapshot(cls, state):  # type: ignore[no-untyped-def]
            _ = state  # Test-Stub mit Protocol-Surface; Payload ignoriert.
            return cls()

        def set_run_id(self, run_id: str) -> None:  # type: ignore[no-untyped-def]
            # Welle-6a-Protocol-Erweiterung (C-1-Fix); _run_id wird
            # nicht persistiert, weil das Test-Double nichts emittiert.
            _ = run_id

    # @runtime_checkable findet `tick` als Attribut — passt durch.
    # Das ist eine bekannte typing.Protocol-Beschraenkung; siehe
    # Protocol-Docstring im `_protocol.py`.
    assert isinstance(WrongSignatureTick(), DeviceModel)


# ---------------------------------------------------------------------------
# Welle-1-Review C-2: Lifecycle-Pre-init-Raises
# ---------------------------------------------------------------------------


def test_device_id_pre_init_raises() -> None:
    """`device_id` pre-init wirft `DeviceNotInitializedError`
    (ADR 0013 §2.7)."""
    device = NullDevice()
    with pytest.raises(DeviceNotInitializedError):
        _ = device.device_id


def test_tick_pre_init_raises() -> None:
    """`tick()` pre-init wirft `DeviceNotInitializedError`
    (ADR 0013 §2.6)."""
    device = NullDevice()
    with pytest.raises(DeviceNotInitializedError):
        device.tick(_make_context(tick=0))


def test_apply_command_pre_init_raises() -> None:
    """`apply_command()` pre-init wirft `DeviceNotInitializedError`
    (ADR 0013 §2.6)."""
    device = NullDevice()
    with pytest.raises(DeviceNotInitializedError):
        device.apply_command(_make_command())


def test_snapshot_pre_init_returns_minimal_mapping() -> None:
    """`snapshot()` pre-init ist zulaessig und liefert minimal
    `{"version": SNAPSHOT_VERSION}` (ADR 0013 §2.6)."""
    device = NullDevice()
    state = device.snapshot()
    assert state == {"version": NullDevice.SNAPSHOT_VERSION}


def test_telemetry_pre_init_returns_empty_tuple() -> None:
    """`telemetry()` pre-init liefert `()` (ADR 0013 §2.5/2.6)."""
    device = NullDevice()
    assert device.telemetry() == ()


# ---------------------------------------------------------------------------
# Welle-1-Review L-1: Double-Initialize
# ---------------------------------------------------------------------------


def test_double_initialize_raises() -> None:
    """Zweiter `initialize()`-Aufruf wirft
    `DeviceAlreadyInitializedError` — Devices sind nicht
    resettable (ADR 0013 §2.6)."""
    device = NullDevice()
    device.initialize(_make_scenario_device(), FixedSeedRandom(seed=0))
    with pytest.raises(DeviceAlreadyInitializedError):
        device.initialize(_make_scenario_device(), FixedSeedRandom(seed=1))


# ---------------------------------------------------------------------------
# Welle-1-Review C-1: telemetry-vs-tick-Equality
# ---------------------------------------------------------------------------


def test_telemetry_equals_last_tick_outcome() -> None:
    """`telemetry()` nach `tick(ctx_n)` ist ==-identisch zum
    Telemetrie-Tupel aus `DeviceTickOutcome` (ADR 0013 §2.5).
    NullDevice liefert leere Telemetrie — die Equality bleibt
    trivial true, der Vertrag ist aber strukturell gesetzt."""
    device = NullDevice()
    device.initialize(_make_scenario_device(), FixedSeedRandom(seed=0))
    outcome = device.tick(_make_context(tick=0))
    assert device.telemetry() == outcome.telemetry


# ---------------------------------------------------------------------------
# Welle-1-Review C-3: from_snapshot-Roundtrip
# ---------------------------------------------------------------------------


def test_from_snapshot_roundtrip_is_byte_stable() -> None:
    """`from_snapshot(snapshot()) == device` (ADR 0013 §2.4 +
    Welle-1-Konvention fuer Welle 2..5). NullDevice ist State-arm,
    aber der Vertrag ist hier strukturell gesetzt."""
    device = NullDevice()
    state = device.snapshot()
    restored = NullDevice.from_snapshot(state)
    assert restored == device


def test_from_snapshot_version_mismatch_raises_version_error() -> None:
    """Wrong-version-state wirft typisiert
    `VersionError(subsystem="<device>", expected=N, found=...)`
    aus dem Welle-0a-Generic-Codec (ADR 0013 §2.4)."""
    bogus_state = {"version": 99}
    with pytest.raises(VersionError) as exc_info:
        NullDevice.from_snapshot(bogus_state)
    assert exc_info.value.subsystem == "null_device"


def test_from_snapshot_is_classmethod_not_staticmethod() -> None:
    """Sanity-Check: `from_snapshot` ist als Classmethod gebunden,
    nicht als Staticmethod. `NullDevice.from_snapshot` und
    `NullDevice().from_snapshot` liefern identische Resultate."""
    state = NullDevice().snapshot()
    via_class = NullDevice.from_snapshot(state)
    via_instance = NullDevice().from_snapshot(state)
    assert type(via_class) is NullDevice
    assert type(via_instance) is NullDevice
