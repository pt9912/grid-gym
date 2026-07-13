"""`BatteryDevice` — DeviceModel-Implementation (M2 Welle 2).

Implementiert das `DeviceModel`-Protocol fuer den Battery-
Geraetetyp (`GG-DEV-010`) inklusive SOC-Fortschreibung
(`GG-BESS-001/003`), Ramp-Limits (`GG-BESS-004`), Sicherheits-
grenzen-Validierung (`GG-BESS-005`) und Lifecycle-/Snapshot-
Vertrag aus ADR 0013.

Tick-Mechanik (ADR 0014 §2.4):

1. Ramp-Limit auf Power-Delta `pending - current`.
2. Energiebilanz: `power * dt_hours * efficiency` (Laden) bzw.
   `power * dt_hours / efficiency` (Entladen).
3. SOC-Hard-Clamp auf `[min_soc_kwh, max_soc_kwh]` (`GG-BESS-005`).
4. Telemetrie-Emission: `soc_pct`, `soc_kwh`, `power_kw`
   (alphabetisch sortiert nach Metrikname, deterministisch).

Decimal-Quantisierung: alle Telemetrie-Werte vor Emission auf
6 Nachkommastellen quantisiert (`GG-DATA-005`-Soll).
"""

from __future__ import annotations

from collections.abc import Mapping
from contextlib import contextmanager
from collections.abc import Iterator
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Self, cast, override

from grid_gym.hexagon.core.devices.battery.commands import (
    BatteryAlarm,
    validate_set_power_command,
)
from grid_gym.hexagon.core.devices.battery.config import (
    DC_BUS_FIELD_NAMES,
    HEALTH_FIELD_NAMES,
    REACTIVE_FIELD_NAMES,
    THERMAL_FIELD_NAMES,
    BatteryConfig,
    CellConfig,
    DcBusConfig,
    HealthConfig,
    ReactiveConfig,
    ThermalConfig,
)
from grid_gym.hexagon.core.devices.battery.snapshot import (
    SNAPSHOT_VERSION,
    BatterySnapshot,
)
from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import (
    DeviceTickContext,
    DeviceTickOutcome,
)
from grid_gym.hexagon.core.domain.quality import Quality
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.errors import (
    DeviceAlreadyInitializedError,
    DeviceNotInitializedError,
    FaultUnsupportedTypeError,
    MissingKeysError,
    WrongTypeError,
)
from grid_gym.hexagon.core.faults.types import FAULT_TYPE_CELL_FAILURE
from grid_gym.hexagon.ports.driven.random import RandomPort

_SATURATION_COMMAND_ID = "<saturation>"
"""Welle-2-Review C-2: spezieller command_id-Marker fuer
Saturation-Alarme aus dem Hard-Clamp-Pfad (ADR 0014 §2.4).
Welle 6 TickLoop kann die Alarme per String-Match filtern."""

_BATTERY_DECIMAL_PRECISION = 28
"""Default-`decimal.getcontext().prec`. Welle-2-Review M-2: das
Tick-Body wird in `with localcontext() as ctx: ctx.prec = 28;
ctx.rounding = ROUND_HALF_EVEN` eingeschlossen, damit Tests/
Adapter, die die globale Decimal-Context mutieren, den
Determinismus-Vertrag aus ADR 0014 §2.6 nicht brechen."""


@contextmanager
def _battery_decimal_context() -> Iterator[None]:
    """Decimal-Localcontext-Wrapper fuer die Tick-Berechnung
    (Welle-2-Review M-2). Pinnt `prec=28` und `rounding=ROUND_HALF_EVEN`
    fuer die Dauer der Tick-Body-Ausfuehrung."""
    with localcontext() as ctx:
        ctx.prec = _BATTERY_DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        yield


_ZERO = Decimal(0)
_ONE = Decimal(1)
_TWO = Decimal(2)
_HUNDRED = Decimal(100)
_THOUSAND = Decimal(1000)
_HALF = Decimal("0.5")
_QUANTUM = Decimal("0.000001")
"""GG-DATA-005-Soll: max. 6 Nachkommastellen in Telemetrie."""

_FAULT_STATUS_OK = "ok"
"""Slice 077 S1 (ADR 0077 §2.5): `fault_status`-String ohne aktiven Fault."""

_SUBSYSTEM = "battery"
_BATTERY_SOURCE = "battery"

_CELL_FAILURE_DERATE = Decimal("0.5")
"""M3-Welle-2 (ADR 0025): bei aktivem `cell_failure` reduziert sich
die effektive `max_discharge_kw` auf 50 % (Welle-2-Default). Welle 3+
kann den Faktor via Payload konfigurierbar machen."""
"""TelemetryPoint.source-Wert; ADR 0007 §5 Sub-Port-Konvention."""

_RUN_ID_UNSET = ""
"""Welle-3-Review M-4: Marker fuer den Pre-`set_run_id`-Zustand.
TickLoop (Welle 6) ruft `set_run_id` vor dem ersten Tick;
Test-Setup ruft direkt. Welle 2 hat keinen TickLoop, der das
automatisch macht — der Pre-`set_run_id`-Tick laeuft mit
`""` und ist absichtlich als „Welle-6-Anchor" markiert."""

# Parameter-Schluessel im ScenarioDevice.params-Mapping.
_PARAM_KEYS = (
    "capacity_kwh",
    "initial_soc_pct",
    "min_soc_pct",
    "max_soc_pct",
    "max_charge_kw",
    "max_discharge_kw",
    "charge_efficiency",
    "discharge_efficiency",
    "ramp_kw_per_s",
)


class BatteryDevice:
    """`DeviceModel`-Implementation fuer den Battery-Geraetetyp.

    Lifecycle, Snapshot-Vertrag und Determinismus sind in
    ADR 0013/0014 fixiert; siehe Modul-Docstring oben fuer die
    Tick-Mechanik.

    Welle 2 nutzt den injizierten `RandomPort` nicht (keine
    stochastischen Anteile); Welle 3+ Fault-Injection wird ihn
    via `sub_port`-Konvention konsumieren.
    """

    def __init__(self) -> None:
        self._scenario_device: ScenarioDevice | None = None
        self._random: RandomPort | None = None
        self._config: BatteryConfig | None = None
        self._soc_kwh: Decimal = _ZERO
        self._current_power_kw: Decimal = _ZERO
        self._pending_power_kw: Decimal = _ZERO
        self._last_telemetry: tuple[TelemetryPoint, ...] = ()
        self._alarms: list[BatteryAlarm] = []
        self._run_id: str = _RUN_ID_UNSET
        # `_sequence` zaehlt monoton ueber alle emittierten
        # `TelemetryPoint.sequence`-Felder — pro Tick werden drei
        # Werte ausgegeben (`power_kw`, `soc_kwh`, `soc_pct`); ohne
        # eigenen Counter wuerden mehrere Battery-Devices im selben
        # Tick kollidieren. ADR 0007 §5 `RandomPort.sub_port` ist
        # nicht der richtige Hebel, weil `sequence` keine Zufalls-
        # Quelle ist.
        self._sequence: int = 0
        # M3-Welle-2 (ADR 0025 §2.2): Fault-State-Flag.
        # Device haelt nur Physik-Flag; Adapter
        # (BatteryFaultEngine) haelt Scheduling-State
        # (`remaining_ticks`).
        self._cell_failure_active: bool = False
        # M8-Welle-4a (ADR 0065 §2.2): akkumulierte Pack-Temperatur des
        # opt-in Thermomodells. `None`, solange kein `thermal`-Block
        # konfiguriert ist (bit-genau heutiges Verhalten); `initialize`/
        # `from_snapshot` setzen ihn bei aktivem Block auf `ambient_temp_c`.
        self._temperature_celsius: Decimal | None = None
        # M8-Welle-4b (ADR 0066 §2.2): letzte Zellspannungen des opt-in Zell-
        # Modells. Leeres Tuple ohne `cell`-Block bzw. vor dem ersten Tick
        # (bit-genau heutiges Verhalten); pro Tick aus Basis + seeded Rauschen
        # neu berechnet (derived, nicht akkumuliert).
        self._cell_voltages: tuple[Decimal, ...] = ()
        # Slice 077 S1 (ADR 0077 §2.2): akkumulierter Equivalent-Full-Cycle-
        # Zaehler des opt-in Health-Modells. `_ZERO` ohne `health`-Block (nie
        # akkumuliert, nicht gesnapshottet → bit-genau heutiges Verhalten);
        # `soh_percent` ist eine reine Funktion aus `_efc` + Config (kein zweiter
        # State-Slot). `dc_voltage`/`reactive_power_kvar` sind zustandslos.
        self._efc: Decimal = _ZERO

    # ------------------------------------------------------------------
    # Pflicht-Property (ADR 0013 §2.7)
    # ------------------------------------------------------------------

    @property
    def device_id(self) -> str:
        if self._scenario_device is None:
            raise DeviceNotInitializedError("device_id")
        return self._scenario_device.id

    @property
    def alarms(self) -> tuple[BatteryAlarm, ...]:
        """Bisher emittierte Alarme als Tupel-Snapshot
        (ADR 0014 §2.5). Unveraenderlich; Welle 6 TickLoop kann
        die Liste konsumieren, ohne Mutation zu riskieren.
        Verwende `drain_alarms()` fuer destruktives Auslesen.
        """
        return tuple(self._alarms)

    def drain_alarms(self) -> tuple[BatteryAlarm, ...]:
        """Liefert alle bisher emittierten Alarme und leert die
        interne Liste (Welle-2-Review M-3: AlarmSinkPort kommt mit
        M3; bis dahin braucht der Aufrufer eine Drain-Semantik,
        damit lange Laeufe nicht unbeschraenkt Speicher binden)."""
        drained = tuple(self._alarms)
        self._alarms = []
        return drained

    def set_run_id(self, run_id: str) -> None:
        """Setzt `TelemetryPoint.run_id` fuer alle nachfolgenden
        Tick-Emissions (Welle-2-Review H-2). TickLoop ruft das
        beim Lauf-Start; Welle 2 hat keinen TickLoop, der das
        macht — Test-Setup ruft direkt."""
        self._run_id = run_id

    def attach_random(self, random: RandomPort) -> None:
        """Re-Attach des `RandomPort` (Welle-3-Review M-6).

        `from_snapshot(...)` rekonstruiert State, kann aber keinen
        `RandomPort` aus dem Snapshot rekonstruieren — Welle 6
        TickLoop ruft `attach_random` nach `from_snapshot`, sobald
        Welle 3+ Geraete tatsaechlich stochastische Anteile haben.
        Welle 2 Battery konsumiert `_random` nicht; die Methode ist
        symmetrisch zu PV/Load vorgehalten, damit Welle 6 alle drei
        Geraete-Typen uniform behandelt."""
        self._random = random

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    def initialize(
        self,
        scenario_device: ScenarioDevice,
        random: RandomPort,
    ) -> None:
        if self._scenario_device is not None:
            raise DeviceAlreadyInitializedError
        config = _config_from_params(scenario_device.params)
        self._scenario_device = scenario_device
        self._random = random
        self._config = config
        self._soc_kwh = config.initial_soc_kwh
        self._current_power_kw = _ZERO
        self._pending_power_kw = _ZERO
        # M8-Welle-4a (ADR 0065 §2.4): Kaltstart auf Umgebungstemperatur bei
        # aktivem Thermo-Block; sonst `None` (kein Temperatur-State/-Punkt).
        self._temperature_celsius = (
            config.thermal.ambient_temp_c if config.thermal is not None else None
        )
        # Slice 077 S1 (ADR 0077 §2.2): EFC-Zaehler kaltgestartet (SOH = initial).
        self._efc = _ZERO

    def apply_command(self, command: Command) -> CommandResult:
        if self._scenario_device is None or self._config is None:
            raise DeviceNotInitializedError("apply_command")
        outcome = validate_set_power_command(
            config=self._config,
            soc_kwh=self._soc_kwh,
            command=command,
            device_id=self._scenario_device.id,
        )
        if outcome.pending_power_kw is not None:
            self._pending_power_kw = outcome.pending_power_kw
        if outcome.alarm is not None:
            self._alarms.append(outcome.alarm)
        return outcome.result

    def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
        if self._scenario_device is None or self._config is None:
            raise DeviceNotInitializedError("tick")
        with _battery_decimal_context():
            return self._tick_in_context(context)

    # ------------------------------------------------------------------
    # Fault-Injection (M3 Welle 2, ADR 0022 §2.1 + ADR 0025)
    # ------------------------------------------------------------------

    def inject_fault(
        self,
        fault_type: str,
        payload: Mapping[str, object],
    ) -> None:
        """Wendet einen Fault auf das Device an
        (`FaultInjectableDevice`-Vertrag aus ADR 0022 §2.1).

        Welle-2-Closed-Set (ADR 0025 §2.1): unterstuetzt
        ausschliesslich `fault_type=FAULT_TYPE_CELL_FAILURE`
        (`"cell_failure"`). Andere Typen werfen typisiert
        `FaultUnsupportedTypeError`.

        Effekt: setzt `_cell_failure_active = True`. Die naechste
        `tick()` reduziert die effektive `max_discharge_kw` um
        den Faktor `_CELL_FAILURE_DERATE` (Welle-2-Default 50 %)
        als **Hard-Clamp** in der jeweiligen Tick — Ramp-Limit
        (`ramp_kw_per_s`) wird vom Derate-Clamp ueberschrieben
        (ADR 0025 §2.1: Safety-Constraint schlaegt Comfort-Ramp).

        **Welle-2-Payload-Vertrag** (Review-Folge M-5): `payload`
        wird vollstaendig **ignoriert** (keine Schema-Validierung,
        keine `derate_factor`-Konfiguration). Welle-3+ kann das
        Payload-Schema schaerfen (z. B. optionaler
        `payload["derate_factor"]: Decimal`-Override mit Range
        `0 < factor <= 1`); aktuell uebergebene Payload-Werte
        werden ohne Warnung verworfen.
        """
        _ = payload  # Welle 2 ignoriert Payload (siehe Docstring + ADR 0025 §2.1).
        if fault_type == FAULT_TYPE_CELL_FAILURE:
            self._cell_failure_active = True
            return
        raise FaultUnsupportedTypeError("battery", fault_type)

    def clear_fault(self, fault_type: str) -> None:
        """Recovery-Surface (Welle-2-Review-Folge H-2,
        ADR 0025 §2.2): setzt den `_<fault_type>_active`-Flag
        zurueck. Symmetrisch zu `inject_fault`.

        Welle-2-Closed-Set: nur `cell_failure`. Unbekannter
        `fault_type` wirft `FaultUnsupportedTypeError`.
        Idempotenz-Vertrag (ADR 0025 §2.4): wiederholte Aufrufe
        sind No-Op (`_cell_failure_active = False` bleibt False).
        """
        if fault_type == FAULT_TYPE_CELL_FAILURE:
            self._cell_failure_active = False
            return
        raise FaultUnsupportedTypeError("battery", fault_type)

    def _tick_in_context(self, context: DeviceTickContext) -> DeviceTickOutcome:
        # Welle-2-Review L-5: `dt_hours = dt_seconds / 3600` explizit
        # (statt zwei unabhaengiger Quotienten aus `context.tick_ms`).
        # Welle 3+ Geraete kopieren das Muster; eine einzige
        # Definitionsquelle vermeidet Drift.
        config = cast(BatteryConfig, self._config)
        dt_seconds = Decimal(context.tick_ms) / Decimal(1000)
        dt_hours = dt_seconds / Decimal(3600)

        # Ramp-Limit (GG-BESS-004)
        max_delta = config.ramp_kw_per_s * dt_seconds
        delta = self._pending_power_kw - self._current_power_kw
        if delta > max_delta:
            new_power_kw = self._current_power_kw + max_delta
        elif delta < -max_delta:
            new_power_kw = self._current_power_kw - max_delta
        else:
            new_power_kw = self._pending_power_kw

        # Energiebilanz (GG-BESS-001/003)
        if new_power_kw > _ZERO:
            energy_delta_kwh = new_power_kw * dt_hours * config.charge_efficiency
        elif new_power_kw < _ZERO:
            energy_delta_kwh = new_power_kw * dt_hours / config.discharge_efficiency
        else:
            energy_delta_kwh = _ZERO

        # M3-Welle-2 (ADR 0025 §2.1): bei aktivem `cell_failure`
        # wird die effektive `max_discharge_kw` halbiert; ueber-
        # schreitende Discharge-Power wird hart geclampt. Ramp
        # kann den Wert in folgenden Ticks gradually erreichen,
        # aber die Tick selbst clampt instant.
        if self._cell_failure_active:
            effective_max_discharge = config.max_discharge_kw * _CELL_FAILURE_DERATE
            if new_power_kw < -effective_max_discharge:
                new_power_kw = -effective_max_discharge
                # Energie-Bilanz nochmal mit reduzierter Power
                # rechnen, sonst persistiert die Original-
                # Discharge-Rate im SOC.
                energy_delta_kwh = new_power_kw * dt_hours / config.discharge_efficiency

        # SOC-Hard-Clamp + Saturation-Power-Reset (GG-BESS-005,
        # Welle-2-Review C-2).
        new_soc_kwh, new_power_kw = self._apply_soc_clamp(
            self._soc_kwh + energy_delta_kwh, new_power_kw, config
        )

        # Slice 077 S1 (ADR 0077 §2.2): EFC-Akkumulation auf dem **tatsaechlich**
        # geflossenen Energie-Durchsatz (`new_soc - old_soc`, post-Clamp) — VOR der
        # SOC-Zuweisung, damit `self._soc_kwh` noch der Vorwert ist (kein Extra-
        # Statement). Review-Fund: bei SOC-Saturation ist die tatsaechliche Energie
        # kleiner als das intendierte `energy_delta_kwh`; konsistent mit dem
        # post-Clamp-Thermomodell (kein Ghost-Cycling). No-op ohne `health`-Block.
        self._update_soh(new_soc_kwh - self._soc_kwh, config)

        self._soc_kwh = new_soc_kwh
        self._current_power_kw = new_power_kw

        # M8-Welle-4a (ADR 0065 §2.2): Thermo-Euler-Schritt auf der
        # tatsaechlich gefahrenen Power dieses Ticks (post-Ramp/-Clamp).
        # No-op ohne `thermal`-Block (Inaktiv-Pfad bit-identisch).
        self._update_temperature(new_power_kw, dt_seconds, config)

        # M8-Welle-4b (ADR 0066 §2.2): Zellspannungen neu berechnen.
        # No-op ohne `cell`-Block (Inaktiv-Pfad bit-identisch).
        self._update_cell_voltages(context, config)

        telemetry = self._emit_telemetry(context, new_soc_kwh, new_power_kw)
        self._last_telemetry = telemetry
        return DeviceTickOutcome(telemetry=telemetry)

    def _update_temperature(
        self,
        power_kw: Decimal,
        dt_seconds: Decimal,
        config: BatteryConfig,
    ) -> None:
        """ADR 0065 §2.2: stateful Single-Zonen-Euler-Schritt (analog dem
        Top-Oil-Thermomodell aus ADR 0061 §2.2). No-op ohne `thermal`-Block
        — `_temperature_celsius` bleibt `None` (kein State, kein Punkt,
        bit-identisch zum heutigen Battery-Pfad).

            load_pu   = abs(power_kw) / max(max_charge_kw, max_discharge_kw)
            theta_ss  = ambient + thermal_rise_c_at_full_load * load_pu**2
            theta    += (theta_ss - theta) * (dt_s / thermal_time_constant_s)

        Laeuft im `_battery_decimal_context` (prec=28, ROUND_HALF_EVEN);
        `theta` wird auf `_QUANTUM` (6 Nachkommastellen) quantisiert —
        gebundene Stellenzahl, kein Float-Drift im Snapshot/Telemetrie."""
        thermal = config.thermal
        if thermal is None:
            return
        # __init__/initialize/from_snapshot setzen den State bei aktivem Block;
        # der ambient-Fallback ist nur mypy-Narrowing (kein assert — S101).
        current = (
            self._temperature_celsius
            if self._temperature_celsius is not None
            else thermal.ambient_temp_c
        )
        rated_kw = max(config.max_charge_kw, config.max_discharge_kw)
        load_pu = abs(power_kw) / rated_kw
        theta_ss = thermal.ambient_temp_c + thermal.thermal_rise_c_at_full_load * load_pu * load_pu
        theta = current + (theta_ss - current) * (dt_seconds / thermal.thermal_time_constant_s)
        self._temperature_celsius = theta.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)

    def _update_cell_voltages(self, context: DeviceTickContext, config: BatteryConfig) -> None:
        """ADR 0066 §2.2: berechnet die `n_cells` Zellspannungen neu. No-op
        ohne `cell`-Block (`_cell_voltages` bleibt leer — kein State, kein
        Punkt, bit-identisch zum heutigen Battery-Pfad).

        Basis je Zelle: `nominal_pack_voltage_v / n_cells`. Bei
        `noise_amplitude_v == 0` sind alle Zellen identisch (kein
        `RandomPort`-Zug). Bei `> 0` ueberlagert pro Zelle ein
        deterministisches Rauschen in `[-amp, +amp)` aus
        `random.sub_port("cell-<idx>").sub_port("tick-<tick>")` — per-Zelle
        unabhaengig, per-Tick variierend und **tick-gekeyt** (Resume liefert
        fuer denselben Tick byte-identisch denselben Wert). Ohne attach-ten
        `RandomPort` (z. B. nach `from_snapshot`) wirft der Tick fail-loud."""
        cell = config.cell
        if cell is None:
            return
        base = cell.base_cell_voltage_v
        if cell.noise_amplitude_v == _ZERO:
            voltage = base.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)
            self._cell_voltages = tuple(voltage for _ in range(cell.n_cells))
            return
        if self._random is None:
            # Resume-Vertrag (ADR 0066 §2.6): aktives Zell-Rauschen braucht
            # nach `from_snapshot` ein `attach_random` vor dem ersten Tick.
            raise DeviceNotInitializedError("tick")
        voltages: list[Decimal] = []
        for index in range(cell.n_cells):
            draw = (
                self._random.sub_port(f"cell-{index}").sub_port(f"tick-{context.tick}").next_float()
            )
            noise = (draw * _TWO - _ONE) * cell.noise_amplitude_v
            voltages.append((base + noise).quantize(_QUANTUM, rounding=ROUND_HALF_EVEN))
        self._cell_voltages = tuple(voltages)

    def _update_soh(self, soc_delta_kwh: Decimal, config: BatteryConfig) -> None:
        """ADR 0077 §2.2: akkumuliert den Equivalent-Full-Cycle-Zaehler aus dem
        **tatsaechlich geflossenen** Energie-Durchsatz dieses Ticks (`new_soc -
        old_soc`, post-Clamp). No-op ohne `health`-Block (`_efc` bleibt `_ZERO` —
        kein State, kein Punkt, bit-identisch).

            efc += |soc_delta_kwh| / (2·capacity_kwh)

        `soh_percent` selbst ist eine reine Funktion aus `_efc` + Config und wird
        erst in `_emit_telemetry` gerechnet (kein zweiter State-Slot)."""
        if config.health is None:
            return
        self._efc += abs(soc_delta_kwh) / (_TWO * config.capacity_kwh)

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return self._last_telemetry

    # ------------------------------------------------------------------
    # Fault-Status-Surface (Slice 077 S1, ADR 0077 §2.5)
    # ------------------------------------------------------------------

    @property
    def fault_status(self) -> str:
        """ADR 0077 §2.5: aktiver device-Fault-Typ-String, sonst `"ok"`. Projektion
        der `_<fault>_active`-Flags (kein Telemetrie-Punkt). Heute nur
        `cell_failure`; neue device-Fault-Typen tragen sich additiv mit fixer
        Prioritaets-Reihenfolge ein."""
        if self._cell_failure_active:
            return FAULT_TYPE_CELL_FAILURE
        return _FAULT_STATUS_OK

    @property
    def available(self) -> bool:
        """ADR 0077 §2.5: `False` gdw. ein Fault aus dem `available`-Closed-Set
        aktiv ist (heute `cell_failure`); sonst `True`.

        **Bewusste Grenze (Review-Fund):** `cell_failure` deratet physikalisch nur
        die `max_discharge` um 50 % (das Geraet laeuft weiter), meldet hier aber
        `available=False`. Das ist Absicht: der Feldvertrag (ADR 0078 §2.6)
        braucht einen fahrbaren `available=False`/`fault`-Pfad fuer den
        EMS-Safe-Stop-E2E; die derate↔unavailable-Spannung ist akzeptiert (Closed-
        Set, verfeinerbar, wenn ein device-Fault mit anderer Betriebs-Semantik
        dazukommt)."""
        return not self._cell_failure_active

    # ------------------------------------------------------------------
    # Snapshot
    # ------------------------------------------------------------------

    def snapshot(self) -> Mapping[str, object]:
        config = self._config
        if config is None or self._scenario_device is None:
            # Pre-init: nur `version`-Felder (ADR 0013 §2.6).
            return {"version": SNAPSHOT_VERSION}
        snap = BatterySnapshot(
            version=SNAPSHOT_VERSION,
            device_id=self._scenario_device.id,
            run_id=self._run_id,
            sequence=self._sequence,
            config=config,
            soc_kwh=self._soc_kwh,
            current_power_kw=self._current_power_kw,
            pending_power_kw=self._pending_power_kw,
            cell_failure_active=self._cell_failure_active,
            temperature_celsius=self._temperature_celsius,
            cell_voltages_v=self._cell_voltages,
            efc=self._efc,
        )
        return snap.to_dict()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        # Welle-2-Review C-1: from_snapshot ist self-sufficient
        # (ADR 0014 §2.2). Wir synthesizen ein minimales
        # ScenarioDevice aus device_id + embedded config, damit
        # die Lifecycle-Pre-init-Raises sofort aufgeloest sind.
        # `_random` bleibt None — Welle 2 Battery konsumiert es
        # nicht; Welle 3+ Geraete brauchen separate Loesung.
        snap = BatterySnapshot.from_dict(state)
        device = cls()
        device._scenario_device = ScenarioDevice(
            id=snap.device_id,
            type="battery",
            params=_config_to_params(snap.config),
        )
        device._config = snap.config
        device._soc_kwh = snap.soc_kwh
        device._current_power_kw = snap.current_power_kw
        device._pending_power_kw = snap.pending_power_kw
        device._run_id = snap.run_id
        device._sequence = snap.sequence
        device._cell_failure_active = snap.cell_failure_active
        # M8-Welle-4a (ADR 0065 §2.5): Thermo-State aus dem opt-in-Snapshot
        # (None ohne Block; `__init__` hat ihn bereits konsistent gesetzt,
        # der Snapshot-Wert ueberschreibt fuer den Resume).
        device._temperature_celsius = snap.temperature_celsius
        # M8-Welle-4b (ADR 0066 §2.5): letzte Zellspannungen aus dem opt-in-
        # Snapshot. `_random` bleibt None — aktives Zell-Rauschen braucht ein
        # `attach_random` vor dem ersten Tick (sonst fail-loud).
        device._cell_voltages = snap.cell_voltages_v
        # Slice 077 S1 (ADR 0077 §2.6): EFC-Zaehler aus dem opt-in-Snapshot
        # (`_ZERO` ohne Health-Block; SOH re-derived in `_emit_telemetry`).
        device._efc = snap.efc
        return device

    # ------------------------------------------------------------------
    # Equality (fuer Roundtrip-Vergleich von_snapshot(snapshot()) == device)
    # ------------------------------------------------------------------

    @override
    def __eq__(self, other: object) -> bool:
        # Welle-2-Review M-1: Equality vergleicht persistierten
        # State (alles, was im Snapshot landet). Run-Segment-lokale
        # Felder wie `_alarms` und `_last_telemetry`/`_random` sind
        # bewusst ausgeschlossen — sie sind Effekt der bisherigen
        # Iteration, nicht des Zustands.
        if not isinstance(other, BatteryDevice):
            return NotImplemented
        return (
            self._config == other._config
            and self._soc_kwh == other._soc_kwh
            and self._current_power_kw == other._current_power_kw
            and self._pending_power_kw == other._pending_power_kw
            and self._device_id_or_none() == other._device_id_or_none()
            and self._run_id == other._run_id
            and self._sequence == other._sequence
            and self._cell_failure_active == other._cell_failure_active
            and self._temperature_celsius == other._temperature_celsius
            and self._cell_voltages == other._cell_voltages
            and self._efc == other._efc
        )

    @override
    def __hash__(self) -> int:
        return hash(
            (
                self._config,
                self._soc_kwh,
                self._current_power_kw,
                self._pending_power_kw,
                self._device_id_or_none(),
                self._run_id,
                self._sequence,
                self._cell_failure_active,
                self._temperature_celsius,
                self._cell_voltages,
                self._efc,
            )
        )

    def _device_id_or_none(self) -> str | None:
        return None if self._scenario_device is None else self._scenario_device.id

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _apply_soc_clamp(
        self,
        target_soc_kwh: Decimal,
        current_power_kw: Decimal,
        config: BatteryConfig,
    ) -> tuple[Decimal, Decimal]:
        """SOC-Hard-Clamp (GG-BESS-005) + Saturation-Power-Reset
        (Welle-2-Review C-2). Liefert das Tupel
        `(new_soc_kwh, new_power_kw)` zurueck.

        Bei Saturation:
        - `new_soc_kwh = clamp(target_soc_kwh, min/max_soc_kwh)`,
        - `new_power_kw = 0` (kein Ghost-Discharge),
        - `_pending_power_kw = 0` (kein „auto-resume",
          `GG-BESS-005`-Akzeptanz),
        - Saturation-Alarm via `command_id="<saturation>"` in
          `_alarms` angefuegt.
        """
        if target_soc_kwh < config.min_soc_kwh:
            new_soc_kwh = config.min_soc_kwh
            saturation_limit_pct: Decimal = config.min_soc_pct
        elif target_soc_kwh > config.max_soc_kwh:
            new_soc_kwh = config.max_soc_kwh
            saturation_limit_pct = config.max_soc_pct
        else:
            return target_soc_kwh, current_power_kw

        if current_power_kw == _ZERO:
            # SOC kommt zwar aus den Grenzen heraus, aber das war
            # nicht durch eigene Power getrieben (z. B. anfaengliche
            # Konfiguration genau am Limit) — kein Alarm.
            return new_soc_kwh, current_power_kw

        # Power+Pending zero + Alarm
        self._pending_power_kw = _ZERO
        device_id = cast(ScenarioDevice, self._scenario_device).id
        self._alarms.append(
            BatteryAlarm(
                target_device_id=device_id,
                limit=saturation_limit_pct,
                limit_unit="pct",
                result=CommandResult.LIMITED,
                command_id=_SATURATION_COMMAND_ID,
            )
        )
        return new_soc_kwh, _ZERO

    def _dc_voltage(
        self,
        dc: DcBusConfig,
        capacity_kwh: Decimal,
        new_soc_kwh: Decimal,
        power_kw: Decimal,
    ) -> Decimal:
        """ADR 0077 §2.3: `dc_voltage = ocv + i_dc·R` (zustandslos). `power_kw` ist
        der gefahrene (quantisierte) Wert; Laden = **+** → `i_dc > 0` → Spannung
        ueber OCV. `ocv == 0` (pathologischer Slope) → `i_dc = 0` (kein Div-by-Zero;
        Default-Slope=0 haelt `ocv = nominal_voltage_v > 0`)."""
        soc_frac = new_soc_kwh / capacity_kwh
        ocv = dc.nominal_voltage_v + dc.ocv_soc_slope_v * (soc_frac - _HALF)
        # `DcBusConfig` validiert `|slope| < 2*nominal` → `ocv > 0`; der `> _ZERO`-
        # Guard ist Defense-in-Depth gegen Div-by-Zero (nie ein negativer i_dc).
        i_dc = power_kw * _THOUSAND / ocv if ocv > _ZERO else _ZERO
        return (ocv + i_dc * dc.internal_resistance_ohm).quantize(
            _QUANTUM, rounding=ROUND_HALF_EVEN
        )

    def _emit_telemetry(
        self,
        context: DeviceTickContext,
        new_soc_kwh: Decimal,
        new_power_kw: Decimal,
    ) -> tuple[TelemetryPoint, ...]:
        config = cast(BatteryConfig, self._config)
        device_id = cast(ScenarioDevice, self._scenario_device).id

        soc_pct = (new_soc_kwh / config.capacity_kwh * _HUNDRED).quantize(
            _QUANTUM, rounding=ROUND_HALF_EVEN
        )
        soc_kwh = new_soc_kwh.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)
        power_kw = new_power_kw.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN)

        # Drei Bestands-Metriken; die opt-in Metriken werden additiv ergaenzt
        # und das Ergebnis am Ende alphabetisch nach Metrikname sortiert
        # (deterministische Reihenfolge, ADR 0014 §2.4). Ohne opt-in Metriken
        # bleibt die Reihenfolge `power_kw`/`soc_kwh`/`soc_pct` byte-identisch.
        emissions = [
            ("power_kw", power_kw, "kW"),
            ("soc_kwh", soc_kwh, "kWh"),
            ("soc_pct", soc_pct, "pct"),
        ]
        # M8-Welle-4a (ADR 0065 §2.2): opt-in `temperature_celsius`-Punkt
        # **nur bei aktivem Thermomodell** (inaktiv -> kein Punkt, nicht `0`).
        if self._temperature_celsius is not None:
            emissions.append(
                (
                    "temperature_celsius",
                    self._temperature_celsius.quantize(_QUANTUM, rounding=ROUND_HALF_EVEN),
                    "degC",
                )
            )
        # M8-Welle-4b (ADR 0066 §2.3): opt-in aggregierte
        # `cell_voltage_delta_v`-Metrik (`max - min`) **nur bei aktivem
        # Zell-Modell** (inaktiv -> kein Punkt). Bounded auf einen Punkt
        # statt N per-Zelle-Punkte.
        if self._cell_voltages:
            delta = (max(self._cell_voltages) - min(self._cell_voltages)).quantize(
                _QUANTUM, rounding=ROUND_HALF_EVEN
            )
            emissions.append(("cell_voltage_delta_v", delta, "V"))
        # Slice 077 S1 (ADR 0077 §2.2): opt-in `soh_percent` (nur bei aktivem
        # Health-Block). SOH = initial - degradation·efc, geklemmt `≥ 0`.
        if config.health is not None:
            soh = (
                config.health.initial_soh_pct
                - config.health.degradation_pct_per_full_cycle * self._efc
            )
            emissions.append(
                (
                    "soh_percent",
                    max(soh, _ZERO).quantize(_QUANTUM, rounding=ROUND_HALF_EVEN),
                    "pct",
                )
            )
        # Slice 077 S1 (ADR 0077 §2.3): opt-in `dc_voltage` (zustandslos).
        if config.dc_bus is not None:
            emissions.append(
                (
                    "dc_voltage",
                    self._dc_voltage(config.dc_bus, config.capacity_kwh, new_soc_kwh, power_kw),
                    "V",
                )
            )
        # Slice 077 S1 (ADR 0077 §2.4): opt-in `reactive_power_kvar` (zustandslos).
        if config.reactive is not None:
            reactive = (abs(power_kw) * config.reactive.q_factor).quantize(
                _QUANTUM, rounding=ROUND_HALF_EVEN
            )
            emissions.append(("reactive_power_kvar", reactive, "kvar"))
        emissions.sort(key=lambda emission: emission[0])
        points = []
        for metric, value, unit in emissions:
            self._sequence += 1
            points.append(
                TelemetryPoint(
                    run_id=self._run_id,
                    tick=context.tick,
                    simulation_time=context.simulation_time,
                    device_id=device_id,
                    metric=metric,
                    value=value,
                    unit=unit,
                    quality=Quality.VALID,
                    source=_BATTERY_SOURCE,
                    sequence=self._sequence,
                )
            )
        return tuple(points)


def _config_from_params(params: Mapping[str, object]) -> BatteryConfig:
    """Parst eine `ScenarioDevice.params`-Map zu `BatteryConfig`.

    Welle 2: erwartet alle Pflicht-Felder als `Decimal` im Params-
    Mapping. YAML-Adapter-Schicht (M3/Welle-5-Scenario-YAML) ist
    fuer die Decimal-Konversion verantwortlich; hier wird strukturell
    geprueft. Mismatches werfen `WrongTypeError("battery", key,
    "Decimal", actual)`.
    """
    missing = [key for key in _PARAM_KEYS if key not in params]
    if missing:
        raise MissingKeysError(_SUBSYSTEM, missing)
    fields: dict[str, Decimal] = {}
    for key in _PARAM_KEYS:
        value = params[key]
        if not isinstance(value, Decimal):
            raise WrongTypeError(_SUBSYSTEM, f"params.{key}", "Decimal", type(value).__name__)
        fields[key] = value
    return BatteryConfig(
        **fields,
        thermal=_thermal_from_params(params),
        cell=_cell_from_params(params),
        health=_health_from_params(params),
        dc_bus=_dc_bus_from_params(params),
        reactive=_reactive_from_params(params),
    )


def _decimal_block_from_params(
    params: Mapping[str, object], block_name: str, field_names: tuple[str, ...]
) -> dict[str, Decimal] | None:
    """Slice 077 S1: liest einen opt-in Decimal-Block aus den Scenario-Params
    (fehlt → `None`). Alle `field_names` sind Pflicht + `Decimal` (No-float,
    `GG-DATA-005`); Muster `_thermal_from_params`. Der jeweilige Config-Konstruktor
    erzwingt die Wertebereiche."""
    if block_name not in params:
        return None
    block = params[block_name]
    if not isinstance(block, Mapping):
        raise WrongTypeError(_SUBSYSTEM, f"params.{block_name}", "Mapping", type(block).__name__)
    fields: dict[str, Decimal] = {}
    for key in field_names:
        if key not in block:
            raise MissingKeysError(_SUBSYSTEM, [f"{block_name}.{key}"])
        value = block[key]
        if not isinstance(value, Decimal):
            raise WrongTypeError(
                _SUBSYSTEM, f"params.{block_name}.{key}", "Decimal", type(value).__name__
            )
        fields[key] = value
    return fields


def _health_from_params(params: Mapping[str, object]) -> HealthConfig | None:
    """Slice 077 S1 (ADR 0077 §2.2): opt-in `health`-Block."""
    fields = _decimal_block_from_params(params, "health", HEALTH_FIELD_NAMES)
    return None if fields is None else HealthConfig(**fields)


def _dc_bus_from_params(params: Mapping[str, object]) -> DcBusConfig | None:
    """Slice 077 S1 (ADR 0077 §2.3): opt-in `dc_bus`-Block."""
    fields = _decimal_block_from_params(params, "dc_bus", DC_BUS_FIELD_NAMES)
    return None if fields is None else DcBusConfig(**fields)


def _reactive_from_params(params: Mapping[str, object]) -> ReactiveConfig | None:
    """Slice 077 S1 (ADR 0077 §2.4): opt-in `reactive`-Block."""
    fields = _decimal_block_from_params(params, "reactive", REACTIVE_FIELD_NAMES)
    return None if fields is None else ReactiveConfig(**fields)


def _thermal_from_params(params: Mapping[str, object]) -> ThermalConfig | None:
    """M8-Welle-4a (ADR 0065 §2.1): liest den optionalen `thermal`-Block aus
    den Scenario-Params (opt-in — fehlt → `None` → kein Thermomodell).
    Spiegelt `_volt_var_from_params` aus dem PV-Geraet; die No-float-Pruefung
    (`GG-DATA-005`) liegt hier (nicht im `ThermalConfig`-Konstruktor)."""
    if "thermal" not in params:
        return None
    block = params["thermal"]
    if not isinstance(block, Mapping):
        raise WrongTypeError(_SUBSYSTEM, "params.thermal", "Mapping", type(block).__name__)
    fields: dict[str, Decimal] = {}
    for key in THERMAL_FIELD_NAMES:
        if key not in block:
            raise MissingKeysError(_SUBSYSTEM, [f"thermal.{key}"])
        value = block[key]
        if not isinstance(value, Decimal):
            raise WrongTypeError(
                _SUBSYSTEM, f"params.thermal.{key}", "Decimal", type(value).__name__
            )
        fields[key] = value
    return ThermalConfig(**fields)


def _cell_from_params(params: Mapping[str, object]) -> CellConfig | None:
    """M8-Welle-4b (ADR 0066 §2.1): liest den optionalen `cell`-Block aus den
    Scenario-Params (opt-in — fehlt → `None`). `n_cells` ist `int`, die
    uebrigen `Decimal`; die No-float-/Typpruefung liegt hier."""
    if "cell" not in params:
        return None
    block = params["cell"]
    if not isinstance(block, Mapping):
        raise WrongTypeError(_SUBSYSTEM, "params.cell", "Mapping", type(block).__name__)
    for key in ("nominal_pack_voltage_v", "n_cells", "noise_amplitude_v"):
        if key not in block:
            raise MissingKeysError(_SUBSYSTEM, [f"cell.{key}"])
    n_cells = block["n_cells"]
    # `bool` ist `int`-Subklasse — Zellzahl ist aber Ganzzahl, kein Flag.
    if not isinstance(n_cells, int) or isinstance(n_cells, bool):
        raise WrongTypeError(_SUBSYSTEM, "params.cell.n_cells", "int", type(n_cells).__name__)
    decimals: dict[str, Decimal] = {}
    for key in ("nominal_pack_voltage_v", "noise_amplitude_v"):
        value = block[key]
        if not isinstance(value, Decimal):
            raise WrongTypeError(_SUBSYSTEM, f"params.cell.{key}", "Decimal", type(value).__name__)
        decimals[key] = value
    return CellConfig(
        nominal_pack_voltage_v=decimals["nominal_pack_voltage_v"],
        n_cells=n_cells,
        noise_amplitude_v=decimals["noise_amplitude_v"],
    )


def _config_to_params(config: BatteryConfig) -> Mapping[str, object]:
    """Inverse von `_config_from_params`: serialisiert
    `BatteryConfig` zurueck in das Params-Mapping-Form fuer das
    synthesizte `ScenarioDevice` post-`from_snapshot`
    (Welle-2-Review C-1). M8-Welle-4a/4b: die opt-in `thermal`-/`cell`-Bloecke
    werden als nested Mapping nur bei aktivem Modell wiedergegeben."""
    params: dict[str, object] = {key: getattr(config, key) for key in _PARAM_KEYS}
    if config.thermal is not None:
        params["thermal"] = {key: getattr(config.thermal, key) for key in THERMAL_FIELD_NAMES}
    if config.cell is not None:
        params["cell"] = {
            "nominal_pack_voltage_v": config.cell.nominal_pack_voltage_v,
            "n_cells": config.cell.n_cells,
            "noise_amplitude_v": config.cell.noise_amplitude_v,
        }
    # Slice 077 S1 (ADR 0077): opt-in Field-Envelope-Bloecke (nur bei aktivem Modell).
    if config.health is not None:
        params["health"] = {key: getattr(config.health, key) for key in HEALTH_FIELD_NAMES}
    if config.dc_bus is not None:
        params["dc_bus"] = {key: getattr(config.dc_bus, key) for key in DC_BUS_FIELD_NAMES}
    if config.reactive is not None:
        params["reactive"] = {key: getattr(config.reactive, key) for key in REACTIVE_FIELD_NAMES}
    return params
