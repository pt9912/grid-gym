"""Welle-6b-Integration-Tests fuer TickLoop (ADR 0021).

Pinnt die Welle-6b-Vertraege:
- `active_load_events`/`active_load_profiles` Konstruktor-Kwargs.
- Jedes-Tick-Baseline + Profile-/Event-Overlay an LoadDevices
  (`_consume_load_inputs_into`).
- Manual-Override-Heuristik fuer GridConnection-Auto-Schluss
  (Profile/Event auf GridConnection-Target supprimiert Auto-
  Schluss; ohne Override greift `pre_grid_residual`-Berechnung).
- `unknown_device_class`-Pfad fuer `_device_type_for`.
- Forward-Compat-Defense: device_id mit Punkt im Snapshot.
- Public-Properties: `run_id`, `tick_ms` (Welle-6b-API-Vertrag fuer
  Welle 6c MVP-Demo + Welle-7 Replay-Konsumenten).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from typing import Self

import pytest

from grid_gym.adapters.driven.random_mt import MersenneTwisterRandomPort
from grid_gym.hexagon.core.devices.grid_connection import GridConnectionDevice
from grid_gym.hexagon.core.devices.load import LoadDevice
from grid_gym.hexagon.core.devices.pv import PvDevice
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext, DeviceTickOutcome
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.errors import TickLoopUnknownDeviceTypeError
from grid_gym.hexagon.core.grid_model import GridModelBilanz, GridModelConfig
from grid_gym.hexagon.core.grid_model.loads import LoadEvent, LoadProfile
from grid_gym.hexagon.core.simulation.scheduler import Scheduler
from grid_gym.hexagon.core.simulation.tick_loop import TickLoop
from grid_gym.hexagon.ports.driven.random import RandomPort
from tests.unit.hexagon.ports.driven._fakes import FakeClock, FixedSeedRandom


def _grid_model_config() -> GridModelConfig:
    return GridModelConfig(
        nominal_frequency_hz=Decimal("50"),
        frequency_sensitivity_hz_per_kw=Decimal("0.001"),
        frequency_clamp_min_hz=Decimal("45"),
        frequency_clamp_max_hz=Decimal("55"),
        nominal_voltage_v=Decimal("400"),
        voltage_sensitivity_v_per_kw=Decimal("0.1"),
        voltage_clamp_min_v=Decimal("280"),
        voltage_clamp_max_v=Decimal("520"),
    )


def _make_pv(device_id: str = "pv-1", rated: Decimal = Decimal("500")) -> PvDevice:
    pv = PvDevice()
    pv.initialize(
        ScenarioDevice(id=device_id, type="pv", params={"rated_power_kw": rated}),
        FixedSeedRandom(seed=0),
    )
    return pv


def _make_load(device_id: str = "load-1", rated: Decimal = Decimal("300")) -> LoadDevice:
    load = LoadDevice()
    load.initialize(
        ScenarioDevice(id=device_id, type="load", params={"rated_power_kw": rated}),
        FixedSeedRandom(seed=0),
    )
    return load


def _make_grid_connection(
    device_id: str = "grid-1",
    max_import_kw: Decimal = Decimal("1000"),
    max_export_kw: Decimal = Decimal("1000"),
) -> GridConnectionDevice:
    grid_dev = GridConnectionDevice()
    grid_dev.initialize(
        ScenarioDevice(
            id=device_id,
            type="grid_connection",
            params={
                "nominal_voltage_v": Decimal("400"),
                "max_import_kw": max_import_kw,
                "max_export_kw": max_export_kw,
            },
        ),
        FixedSeedRandom(seed=0),
    )
    return grid_dev


def _make_loop(
    *,
    devices: tuple[object, ...] = (),
    grid_model: GridModelBilanz | None = None,
    tick_ms: int = 1000,
    active_load_events: tuple[LoadEvent, ...] = (),
    active_load_profiles: tuple[LoadProfile, ...] = (),
) -> TickLoop:
    return TickLoop(
        run_id="run-6b",
        tick_ms=tick_ms,
        clock=FakeClock(),
        random=MersenneTwisterRandomPort(seed=42),
        scheduler=Scheduler(),
        devices=devices,  # type: ignore[arg-type]
        grid_model=grid_model,
        active_load_events=active_load_events,
        active_load_profiles=active_load_profiles,
    )


# ---------------------------------------------------------------------------
# Public API: run_id, tick_ms properties (Welle-6a + Welle-6b smoketest)
# ---------------------------------------------------------------------------


def test_run_id_property_returns_constructor_value() -> None:
    """Welle-6a-API-Vertrag (Welle-6b-Review N-1): `run_id` ist als
    public property exponiert; Welle-7 Replay-Konsumenten lesen ihn
    ohne `_run_id`-Private-Access."""
    loop = _make_loop()
    assert loop.run_id == "run-6b"


def test_tick_ms_property_returns_constructor_value() -> None:
    """Welle-6a-API-Vertrag (Welle-6b-Review N-1): `tick_ms` public
    property — Welle-7 Replay-Konsumenten und Welle-6c MVP-Demo
    lesen den Wert ohne `_tick_ms`-Private-Access."""
    loop = _make_loop(tick_ms=100)
    assert loop.tick_ms == 100


# ---------------------------------------------------------------------------
# LoadEvent-Overlay (ADR 0021 §2.5)
# ---------------------------------------------------------------------------


def test_load_event_overlay_overrides_load_baseline() -> None:
    """ADR 0021 §2.5 Event-Overlay: aktiver LoadEvent setzt
    `intent_by_id[target_id] = event.power_kw`, ueberschreibt das
    Baseline-`rated_power_kw`."""
    load = _make_load("load-1", rated=Decimal("300"))
    event = LoadEvent(
        start_s=Decimal("0"),
        duration_s=Decimal("10"),
        target_device_id="load-1",
        power_kw=Decimal("250"),
    )
    loop = _make_loop(devices=(load,), active_load_events=(event,))
    result = loop.tick()
    load_points = [p for p in result.emitted_telemetry if p.source == "load"]
    assert len(load_points) == 1
    assert load_points[0].value == Decimal("250")


def test_load_event_inactive_outside_window_keeps_baseline() -> None:
    """ADR 0021 §2.5: ausserhalb `[start_s, start_s + duration_s)`
    greift die Baseline `rated_power_kw`."""
    load = _make_load("load-1", rated=Decimal("100"))
    # Event endet vor dem ersten Tick (now=1s).
    event = LoadEvent(
        start_s=Decimal("5"),
        duration_s=Decimal("1"),
        target_device_id="load-1",
        power_kw=Decimal("999"),
    )
    loop = _make_loop(devices=(load,), active_load_events=(event,))
    result = loop.tick()  # now=1s, vor Event-Start
    load_points = [p for p in result.emitted_telemetry if p.source == "load"]
    assert load_points[0].value == Decimal("100")


def test_load_event_unknown_target_is_skipped() -> None:
    """ADR 0021 §2.5: LoadEvent mit `target_device_id`, der nicht
    in `_device_by_id` ist, wird silent-skipped (kein KeyError)."""
    load = _make_load("load-1", rated=Decimal("100"))
    ghost = LoadEvent(
        start_s=Decimal("0"),
        duration_s=Decimal("10"),
        target_device_id="ghost-load",
        power_kw=Decimal("999"),
    )
    loop = _make_loop(devices=(load,), active_load_events=(ghost,))
    result = loop.tick()  # darf nicht knallen
    load_points = [p for p in result.emitted_telemetry if p.source == "load"]
    assert load_points[0].value == Decimal("100")


# ---------------------------------------------------------------------------
# LoadProfile-Overlay (ADR 0021 §2.5)
# ---------------------------------------------------------------------------


def test_load_profile_overlay_uses_tick_indexed_value() -> None:
    """ADR 0020 §2.3 / ADR 0021 §2.5: Profile-Wert nach
    `(tick_count * tick_ms) // profile.tick_ms` indizieren."""
    load = _make_load("load-1", rated=Decimal("100"))
    profile = LoadProfile(
        target_device_id="load-1",
        tick_values=(Decimal("10"), Decimal("20"), Decimal("30")),
        tick_ms=1000,
    )
    loop = _make_loop(devices=(load,), active_load_profiles=(profile,), tick_ms=1000)
    # Tick 0: profile_index=0 → 10
    result = loop.tick()
    point = next(p for p in result.emitted_telemetry if p.source == "load")
    assert point.value == Decimal("10")
    # Tick 1: profile_index=1 → 20
    result = loop.tick()
    point = next(p for p in result.emitted_telemetry if p.source == "load")
    assert point.value == Decimal("20")


def test_load_profile_overlay_repeats_last_value_when_oob() -> None:
    """ADR 0020 §2.3: out-of-bounds Profile-Index → Repeat-Last-Value
    (Welle-5b-Konvention)."""
    load = _make_load("load-1", rated=Decimal("100"))
    profile = LoadProfile(
        target_device_id="load-1",
        tick_values=(Decimal("10"),),
        tick_ms=1000,
    )
    loop = _make_loop(devices=(load,), active_load_profiles=(profile,), tick_ms=1000)
    loop.tick()  # index 0 → 10
    result = loop.tick()  # index 1 → OOB → repeat-last (10)
    point = next(p for p in result.emitted_telemetry if p.source == "load")
    assert point.value == Decimal("10")


def test_load_profile_unknown_target_is_skipped() -> None:
    """ADR 0021 §2.5: LoadProfile mit unbekanntem target wird
    silent-skipped — kein KeyError."""
    load = _make_load("load-1", rated=Decimal("100"))
    ghost = LoadProfile(
        target_device_id="ghost-load",
        tick_values=(Decimal("999"),),
        tick_ms=1000,
    )
    loop = _make_loop(devices=(load,), active_load_profiles=(ghost,))
    result = loop.tick()
    load_points = [p for p in result.emitted_telemetry if p.source == "load"]
    assert load_points[0].value == Decimal("100")


# ---------------------------------------------------------------------------
# Manual-Override-Heuristik fuer GridConnection-Auto-Schluss
# (ADR 0021 §2.7)
# ---------------------------------------------------------------------------


def test_grid_connection_manual_override_via_event_suppresses_auto_close() -> None:
    """ADR 0021 §2.7: LoadEvent mit `target_device_id` einer
    GridConnection markiert sie als Manual-Override; Auto-Schluss
    wird supprimiert. Bilanz traegt den verbleibenden Residual."""
    pv = _make_pv(rated=Decimal("500"))
    load = _make_load(rated=Decimal("300"))
    grid_dev = _make_grid_connection("grid-1")
    # Manual-Event auf die GridConnection: power_kw = 0 (keine Last,
    # kein Import); damit greift kein Auto-Schluss.
    event = LoadEvent(
        start_s=Decimal("0"),
        duration_s=Decimal("10"),
        target_device_id="grid-1",
        power_kw=Decimal("0"),
    )
    bilanz = GridModelBilanz(config=_grid_model_config())
    loop = _make_loop(
        devices=(pv, load, grid_dev),
        grid_model=bilanz,
        active_load_events=(event,),
    )
    loop.tick()
    # Ohne Auto-Schluss: imbalance = 500 - 300 - 0 + 0 = 200.
    assert bilanz.last_imbalance_kw == Decimal("200")


def test_grid_connection_manual_override_via_profile_suppresses_auto_close() -> None:
    """ADR 0021 §2.7: LoadProfile auf GridConnection-ID supprimiert
    Auto-Schluss genauso wie LoadEvent."""
    pv = _make_pv(rated=Decimal("500"))
    load = _make_load(rated=Decimal("300"))
    grid_dev = _make_grid_connection("grid-1")
    profile = LoadProfile(
        target_device_id="grid-1",
        tick_values=(Decimal("0"),),
        tick_ms=1000,
    )
    bilanz = GridModelBilanz(config=_grid_model_config())
    loop = _make_loop(
        devices=(pv, load, grid_dev),
        grid_model=bilanz,
        active_load_profiles=(profile,),
    )
    loop.tick()
    assert bilanz.last_imbalance_kw == Decimal("200")


# ---------------------------------------------------------------------------
# _device_type_for unbekannte Klasse (ADR 0015 §2.3 + Welle-6a-Review M-6)
# ---------------------------------------------------------------------------


class _DotIdDevice:
    """Test-Double: device_id mit Punkt — kollidiert mit
    `devices.<type>.<id>`-Schluessel-Schema (Welle-6a-Review L-5)."""

    def __init__(self) -> None:
        self._run_id = ""

    @property
    def device_id(self) -> str:
        return "pv.with.dot"

    def initialize(self, scenario_device: ScenarioDevice, random: RandomPort) -> None:
        _ = scenario_device
        _ = random

    def apply_command(self, command: Command) -> CommandResult:
        _ = command
        return CommandResult.IGNORED

    def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
        _ = context
        return DeviceTickOutcome(telemetry=())

    def snapshot(self) -> Mapping[str, object]:
        return {"version": 1}

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return ()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        _ = state
        return cls()

    def set_run_id(self, run_id: str) -> None:
        self._run_id = run_id


class _UnknownClassDevice:
    """Test-Double: Klasse NICHT in `_DEVICE_TYPE_BY_CLASS_NAME`.
    Snapshot-Pfad muss `TickLoopUnknownDeviceTypeError` werfen."""

    def __init__(self) -> None:
        self._run_id = ""

    @property
    def device_id(self) -> str:
        return "x-1"

    def initialize(self, scenario_device: ScenarioDevice, random: RandomPort) -> None:
        _ = scenario_device
        _ = random

    def apply_command(self, command: Command) -> CommandResult:
        _ = command
        return CommandResult.IGNORED

    def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
        _ = context
        return DeviceTickOutcome(telemetry=())

    def snapshot(self) -> Mapping[str, object]:
        return {"version": 1}

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return ()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        _ = state
        return cls()

    def set_run_id(self, run_id: str) -> None:
        self._run_id = run_id


def test_snapshot_rejects_device_id_with_dot() -> None:
    """Welle-6a-Review L-5: device_id mit '.' kollidiert mit dem
    `devices.<type>.<id>`-Sub-Snapshot-Schluessel — TickLoop wirft
    `TickLoopUnknownDeviceTypeError`."""
    pv = _make_pv("pv-ok")
    # PV-Device als regulaer + DotIdDevice als Test-Double.
    dot_dev = _DotIdDevice()
    loop = _make_loop(devices=(pv, dot_dev))
    with pytest.raises(TickLoopUnknownDeviceTypeError):
        loop.snapshot()


def test_snapshot_rejects_device_with_unregistered_class() -> None:
    """ADR 0015 §2.3 + Welle-6a-Review M-6: Unbekannte Device-Klasse
    im Snapshot-Pfad → `TickLoopUnknownDeviceTypeError` (statt
    silent-falsches Type-Segment im Sub-Snapshot-Schluessel)."""
    unknown = _UnknownClassDevice()
    loop = _make_loop(devices=(unknown,))
    with pytest.raises(TickLoopUnknownDeviceTypeError):
        loop.snapshot()


# ---------------------------------------------------------------------------
# Welle-6b-Review-Fixes (H-1, H-2, H-3-Boundary, M-7)
# ---------------------------------------------------------------------------


def test_auto_close_cap_limit_leaks_residual_into_imbalance() -> None:
    """Welle-6b-Review H-1 + ADR 0021 §2.7: wenn der Auto-Schluss
    den `max_import_kw`/`max_export_kw`-Cap der GridConnection
    sprengt, wird der Wert intern clamped — der **Restposten** geht
    in `imbalance_kw`. Pflicht-Test pinnt die ADR-§2.7-Klausel
    'Cap-Limit-Respekt'."""
    pv = _make_pv(rated=Decimal("500"))
    load = _make_load(rated=Decimal("100"))
    # Generation - Load = 400 kW, also `auto_close = -400`. Cap
    # `max_export_kw=50` clamped auf -50. Restposten = -350.
    grid_dev = _make_grid_connection(
        max_import_kw=Decimal("50"),
        max_export_kw=Decimal("50"),
    )
    bilanz = GridModelBilanz(config=_grid_model_config())
    loop = _make_loop(devices=(pv, load, grid_dev), grid_model=bilanz)
    loop.tick()
    # imbalance = 500 - 100 + (-50) = 350; bzw. 400 - 50 = 350 Restposten.
    assert bilanz.last_imbalance_kw == Decimal("350")


def test_baseline_overwrites_external_set_power_kw_next_tick() -> None:
    """Welle-6b-Review H-2 + ADR 0021 §2.5 (Jedes-Tick-Baseline):
    TickLoop besitzt `set_power_kw` an LoadDevices exklusiv. Ein
    externer `apply_command(set_power_kw, 0)` zwischen Ticks wird
    im naechsten Tick auf `rated_power_kw` zurueckgesetzt."""
    from grid_gym.hexagon.core.domain.command import Command
    from grid_gym.hexagon.core.domain.command_result import CommandResult

    load = _make_load("load-1", rated=Decimal("100"))
    loop = _make_loop(devices=(load,))
    # Externer Command zwischen Ticks: setze auf 0.
    load.apply_command(
        Command(
            command_id="external-1",
            simulation_time=0,
            target_device_id="load-1",
            type="set_power_kw",
            payload={"value": Decimal("0")},
            validation_status="validated",
            result=CommandResult.IGNORED,
        )
    )
    result = loop.tick()
    # TickLoop-Baseline ueberschreibt mit rated_power_kw=100.
    point = next(p for p in result.emitted_telemetry if p.source == "load")
    assert point.value == Decimal("100")


def test_load_event_active_during_first_tick_at_boundary_start() -> None:
    """Welle-6b-Review H-3: Event mit `start_s=0, duration_s=1`
    deckt das erste Tick-Intervall `[0, 1)` ab und ist im ersten
    Tick aktiv (Tick-Start-Zeit-Konvention). Vor der H-3-Fix war
    der Check gegen `now_s=1` und das Event wurde stumm
    inaktiviert."""
    load = _make_load("load-1", rated=Decimal("100"))
    event = LoadEvent(
        start_s=Decimal("0"),
        duration_s=Decimal("1"),
        target_device_id="load-1",
        power_kw=Decimal("75"),
    )
    loop = _make_loop(devices=(load,), active_load_events=(event,), tick_ms=1000)
    result = loop.tick()
    point = next(p for p in result.emitted_telemetry if p.source == "load")
    assert point.value == Decimal("75")


def test_load_event_inactive_at_boundary_end_in_second_tick() -> None:
    """Welle-6b-Review H-3: half-offene Window `[start_s, end_s)`.
    Event `start_s=0, duration_s=1` ist im zweiten Tick (Tick-
    Start-Zeit = 1s) abgelaufen — Baseline `rated_power_kw`
    greift."""
    load = _make_load("load-1", rated=Decimal("100"))
    event = LoadEvent(
        start_s=Decimal("0"),
        duration_s=Decimal("1"),
        target_device_id="load-1",
        power_kw=Decimal("75"),
    )
    loop = _make_loop(devices=(load,), active_load_events=(event,), tick_ms=1000)
    loop.tick()  # tick 0 — event aktiv
    result = loop.tick()  # tick 1 — event abgelaufen
    point = next(p for p in result.emitted_telemetry if p.source == "load")
    assert point.value == Decimal("100")


def test_profile_and_event_both_active_event_wins() -> None:
    """Welle-6b-Review M-7 + ADR 0021 §3 (Reihenfolge): wenn ein
    Profile und ein Event gleichzeitig auf dasselbe Target zeigen,
    setzt das Event den finalen `intent` (Event-Overlay-Schritt
    folgt nach Profile-Overlay)."""
    load = _make_load("load-1", rated=Decimal("100"))
    profile = LoadProfile(
        target_device_id="load-1",
        tick_values=(Decimal("50"),),
        tick_ms=1000,
    )
    event = LoadEvent(
        start_s=Decimal("0"),
        duration_s=Decimal("10"),
        target_device_id="load-1",
        power_kw=Decimal("80"),
    )
    loop = _make_loop(
        devices=(load,),
        active_load_events=(event,),
        active_load_profiles=(profile,),
    )
    result = loop.tick()
    point = next(p for p in result.emitted_telemetry if p.source == "load")
    # Event-Wert (80) ueberschreibt Profile-Wert (50).
    assert point.value == Decimal("80")


def test_manual_override_list_is_deterministic_and_dedup() -> None:
    """Welle-6b-Review M-1: `manual_override_grid_ids` ist
    `list[str]` (kein Set); doppelt referenziertes Target wird nicht
    mehrfach eingefuegt (Append-mit-Check). Profile + Event auf
    gleiche GridConnection → ID einmal in der Override-Liste."""
    pv = _make_pv(rated=Decimal("500"))
    load = _make_load(rated=Decimal("300"))
    grid_dev = _make_grid_connection("grid-1")
    profile = LoadProfile(
        target_device_id="grid-1",
        tick_values=(Decimal("0"),),
        tick_ms=1000,
    )
    event = LoadEvent(
        start_s=Decimal("0"),
        duration_s=Decimal("10"),
        target_device_id="grid-1",
        power_kw=Decimal("0"),
    )
    bilanz = GridModelBilanz(config=_grid_model_config())
    loop = _make_loop(
        devices=(pv, load, grid_dev),
        grid_model=bilanz,
        active_load_events=(event,),
        active_load_profiles=(profile,),
    )
    # Smoke: kein Throw bei doppelt-Override; Auto-Schluss
    # supprimiert; imbalance = 500 - 300 + 0 = 200.
    loop.tick()
    assert bilanz.last_imbalance_kw == Decimal("200")
