"""`BatteryConfig` mit Initial-Validierung (`GG-BESS-008`).

Vor Simulationsstart validiert: Kapazitaet positiv, SOC-Grenzen
konsistent, Initial-SOC in [min, max]-Bereich, Leistungsgrenzen
positiv, Wirkungsgrade in (0, 1], Ramp-Limit positiv. Verstoesse
werfen `BatteryConfigError`-Subklassen — keine stillen Akzeptanzen.

Decimal-Praezision: Werte werden im Konstruktor NICHT quantisiert
— Eingangs-Quantisierung ist Adapter-Verantwortung. `BatteryDevice`
selbst arbeitet mit der vollen Decimal-Praezision; Telemetrie-
Output quantisiert auf 6 Nachkommastellen (`GG-DATA-005`).
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import ROUND_HALF_EVEN, Decimal, localcontext

from grid_gym.hexagon.core.errors import GridGymError

_ZERO = Decimal(0)
_HUNDRED = Decimal(100)
_ONE = Decimal(1)
_TWO = Decimal(2)
_QFACTOR_PRECISION = 28
"""Decimal-`prec` fuer die `q_factor`-Berechnung (`sqrt`), kontext-unabhaengig +
deterministisch — konsistent mit `_BATTERY_DECIMAL_PRECISION` im Model."""


class BatteryConfigError(GridGymError):
    """Wurzel der `BatteryConfig`-Validierungs-Fehler (`GG-BESS-008`)."""


class BatteryConfigInvalidValueError(BatteryConfigError):
    """Ein einzelner Konfigurationswert ist ausserhalb des
    erlaubten Wertebereichs.

    `value` ist `object` (nicht `Decimal`), damit auch No-float-/
    Typ-Verstoesse des opt-in Thermo-Blocks (M8-Welle-4a, ADR 0065 §2.1)
    typisiert gemeldet werden koennen — analog `PvConfigInvalidValueError`.
    """

    def __init__(self, field: str, value: object, constraint: str) -> None:
        super().__init__(f"BatteryConfig.{field}={value} violates constraint {constraint!r}")


class BatteryConfigInconsistentRangeError(BatteryConfigError):
    """SOC-Grenzen sind nicht konsistent (z. B. `min_soc_pct >=
    max_soc_pct` oder `initial_soc_pct` ausserhalb des Intervalls).

    Wird mit drei Decimals + Kontext-String konstruiert; die Message-
    Bildung passiert hier (statt am Aufruferort) — `TRY003` zufrieden.
    """

    def __init__(self, field: str, value: Decimal, range_description: str) -> None:
        super().__init__(f"BatteryConfig.{field}={value} inconsistent with {range_description}")


# M8-Welle-4a (ADR 0065 §2.1): Pflicht-Decimal-Felder des opt-in
# Thermo-Blocks (Single-Source fuer no-float + Snapshot-Serialisierung).
THERMAL_FIELD_NAMES: tuple[str, ...] = (
    "ambient_temp_c",
    "thermal_rise_c_at_full_load",
    "thermal_time_constant_s",
)


@dataclass(frozen=True, slots=True)
class ThermalConfig:
    """Single-Zonen-Thermomodell eines Battery-Packs (M8-Welle-4a,
    `GG-BESS-006`, ADR 0065 §2.1).

    Stateful Euler-Modell, analog dem Top-Oil-Thermomodell aus
    [`ADR 0061`](../../../../../../docs/plan/adr/0061-transformer-limit-bilanz-pattern.md)
    §2.2:

        load_pu   = abs(power_kw) / max(max_charge_kw, max_discharge_kw)
        theta_ss  = ambient_temp_c + thermal_rise_c_at_full_load * load_pu**2
        theta    += (theta_ss - theta) * (dt_s / thermal_time_constant_s)

    `theta` ist akkumulierter Geraete-State (`temperature_celsius`), bei
    aktivem Block auf `ambient_temp_c` kaltgestartet (ADR 0065 §2.4 — kein
    separater Initialwert).

    Invarianten (Verstoss -> `BatteryConfigInvalidValueError`):

    - `thermal_rise_c_at_full_load` — Temperaturanstieg bei Volllast, > 0.
    - `thermal_time_constant_s` — thermische Traegheit (Tau), > 0.
    - `ambient_temp_c` — Umgebungstemperatur, beliebiges `Decimal` (auch
      negativ: Tiefsttemperatur-Umgebung).

    Die No-float-Typpruefung (`GG-DATA-005`) liegt — wie im Bestands-
    Battery-Pattern — in den Parsern (`_thermal_from_params` /
    Snapshot-`assert_decimal`), nicht im Konstruktor.
    """

    ambient_temp_c: Decimal
    thermal_rise_c_at_full_load: Decimal
    thermal_time_constant_s: Decimal

    def __post_init__(self) -> None:
        positive: tuple[tuple[str, Decimal], ...] = (
            ("thermal_rise_c_at_full_load", self.thermal_rise_c_at_full_load),
            ("thermal_time_constant_s", self.thermal_time_constant_s),
        )
        for field, value in positive:
            if value <= _ZERO:
                raise BatteryConfigInvalidValueError(f"thermal.{field}", value, "> 0")


# M8-Welle-4b (ADR 0066 §2.1): Pflicht-Felder des opt-in Zell-Blocks
# (n_cells ist `int`, die uebrigen `Decimal`).
CELL_FIELD_NAMES: tuple[str, ...] = (
    "nominal_pack_voltage_v",
    "n_cells",
    "noise_amplitude_v",
)


@dataclass(frozen=True, slots=True)
class CellConfig:
    """Zellspannungs-Modell eines Battery-Packs (M8-Welle-4b, `GG-BESS-007`,
    ADR 0066 §2.1).

    Das Pack wird in `n_cells` Zellen aufgeloest, jede mit Basisspannung
    `nominal_pack_voltage_v / n_cells`. Bei `noise_amplitude_v > 0`
    ueberlagert pro Zelle ein seeded, deterministisches Rauschen aus dem
    `RandomPort` (per-Zelle + per-Tick unabhaengig); bei `0` sind alle Zellen
    identisch (kein `RandomPort`-Zug).

    Invarianten (Verstoss -> `BatteryConfigInvalidValueError`):

    - `nominal_pack_voltage_v` — Pack-Nennspannung, > 0.
    - `n_cells` — Zellzahl, >= 1 (`int`).
    - `noise_amplitude_v` — Rausch-Amplitude (+/- um die Basisspannung), >= 0.

    Die No-float-/Typpruefung (`GG-DATA-005`) liegt — wie im Bestands-
    Battery-Pattern — in den Parsern (`_cell_from_params` /
    Snapshot-`assert_*`), nicht im Konstruktor.
    """

    nominal_pack_voltage_v: Decimal
    n_cells: int
    noise_amplitude_v: Decimal = _ZERO

    def __post_init__(self) -> None:
        if self.nominal_pack_voltage_v <= _ZERO:
            raise BatteryConfigInvalidValueError(
                "cell.nominal_pack_voltage_v", self.nominal_pack_voltage_v, "> 0"
            )
        if self.n_cells < 1:
            raise BatteryConfigInvalidValueError("cell.n_cells", self.n_cells, ">= 1")
        if self.noise_amplitude_v < _ZERO:
            raise BatteryConfigInvalidValueError(
                "cell.noise_amplitude_v", self.noise_amplitude_v, ">= 0"
            )

    @property
    def base_cell_voltage_v(self) -> Decimal:
        """Basisspannung je Zelle (`nominal_pack_voltage_v / n_cells`)."""
        return self.nominal_pack_voltage_v / Decimal(self.n_cells)


# Slice 077 S1 (ADR 0077 §2.2): Pflicht-Felder des opt-in Health-Blocks.
HEALTH_FIELD_NAMES: tuple[str, ...] = (
    "initial_soh_pct",
    "degradation_pct_per_full_cycle",
)


@dataclass(frozen=True, slots=True)
class HealthConfig:
    """State-of-Health-Modell des Battery-Packs (Slice 077 S1, ADR 0077 §2.2).

    `soh_percent` als Geraete-State: kaltgestartet auf `initial_soh_pct`, pro Tick
    linear degradierend mit dem Equivalent-Full-Cycle-Durchsatz
    (`soh = initial_soh_pct - degradation_pct_per_full_cycle·efc`, geklemmt `≥ 0`).
    Bei `degradation_pct_per_full_cycle=0` (Default) ist SOH ueber den Lauf konstant
    — physikalisch ehrlich (reale Degradation ist ueber Sim-Laufzeiten
    vernachlaessigbar).

    Invarianten (Verstoss → `BatteryConfigInvalidValueError`):

    - `initial_soh_pct` — Start-SOH in Prozent, `(0, 100]`.
    - `degradation_pct_per_full_cycle` — Degradation je Vollzyklus, `≥ 0`.
    """

    initial_soh_pct: Decimal
    degradation_pct_per_full_cycle: Decimal = _ZERO

    def __post_init__(self) -> None:
        if not (_ZERO < self.initial_soh_pct <= _HUNDRED):
            raise BatteryConfigInvalidValueError(
                "health.initial_soh_pct", self.initial_soh_pct, "in (0, 100]"
            )
        if self.degradation_pct_per_full_cycle < _ZERO:
            raise BatteryConfigInvalidValueError(
                "health.degradation_pct_per_full_cycle",
                self.degradation_pct_per_full_cycle,
                ">= 0",
            )


# Slice 077 S1 (ADR 0077 §2.3): Pflicht-Felder des opt-in DC-Bus-Blocks.
DC_BUS_FIELD_NAMES: tuple[str, ...] = (
    "nominal_voltage_v",
    "ocv_soc_slope_v",
    "internal_resistance_ohm",
)


@dataclass(frozen=True, slots=True)
class DcBusConfig:
    """DC-Bus-/Pack-Klemmenspannungs-Modell (Slice 077 S1, ADR 0077 §2.3).

    Zustandsloses Modell (reine Funktion aus `power_kw`/`soc`):

        ocv        = nominal_voltage_v + ocv_soc_slope_v·(soc_frac - 0.5)
        i_dc       = power_kw·1000 / ocv          # grid-gym-Vorzeichen: Laden = +
        dc_voltage = ocv + i_dc·internal_resistance_ohm

    IR-Drop-Vorzeichen: die Klemmenspannung liegt beim **Laden** (`i_dc > 0`)
    **ueber** OCV, beim Entladen darunter — daher `+ i_dc·R`. Bei
    `ocv_soc_slope_v=0` **und** `internal_resistance_ohm=0` (Default) ist
    `dc_voltage = nominal_voltage_v` konstant.

    **Versoehnung mit** `CellConfig.nominal_pack_voltage_v` ([`ADR 0066`]): sind
    beide Bloecke aktiv, muessen die Nennspannungen uebereinstimmen (Validierung in
    `BatteryConfig.__post_init__`) — eine Nennspannung, zwei Sichten.

    Invarianten (Verstoss → `BatteryConfigInvalidValueError`):

    - `nominal_voltage_v` — Pack-Nennspannung, `> 0`.
    - `ocv_soc_slope_v` — SOC-Spannungs-Steigung, beliebiges `Decimal`.
    - `internal_resistance_ohm` — Innenwiderstand, `≥ 0`.
    """

    nominal_voltage_v: Decimal
    ocv_soc_slope_v: Decimal = _ZERO
    internal_resistance_ohm: Decimal = _ZERO

    def __post_init__(self) -> None:
        if self.nominal_voltage_v <= _ZERO:
            raise BatteryConfigInvalidValueError(
                "dc_bus.nominal_voltage_v", self.nominal_voltage_v, "> 0"
            )
        if self.internal_resistance_ohm < _ZERO:
            raise BatteryConfigInvalidValueError(
                "dc_bus.internal_resistance_ohm", self.internal_resistance_ohm, ">= 0"
            )
        # Review-Fund: der OCV-Slope-Term ist `slope·(soc_frac - 0.5)` mit
        # `soc_frac ∈ [0, 1]` → `ocv ∈ [nominal - |slope|/2, nominal + |slope|/2]`.
        # `|slope| < 2·nominal` haelt `ocv > 0` ueber den ganzen SOC-Bereich — sonst
        # koennte `ocv` auf/unter 0 fallen (Div-durch-~0 / vorzeichen-gedrehter
        # i_dc → sinnloses dc_voltage). Fail-fast statt stiller Garbage.
        if abs(self.ocv_soc_slope_v) >= _TWO * self.nominal_voltage_v:
            raise BatteryConfigInvalidValueError(
                "dc_bus.ocv_soc_slope_v",
                self.ocv_soc_slope_v,
                f"|slope| < 2*nominal_voltage_v={_TWO * self.nominal_voltage_v} (haelt ocv > 0)",
            )


# Slice 077 S1 (ADR 0077 §2.4): Pflicht-Felder des opt-in Reactive-Blocks.
REACTIVE_FIELD_NAMES: tuple[str, ...] = ("power_factor",)


@dataclass(frozen=True, slots=True)
class ReactiveConfig:
    """Blindleistungs-Modell ueber einen konstanten Leistungsfaktor (Slice 077 S1,
    ADR 0077 §2.4).

    `reactive_power_kvar = |power_kw| · q_factor` mit
    `q_factor = sqrt(1 - pf²)/pf` (identisch `tan(acos(pf))`, aber **rein in
    `Decimal`** — `GG-DATA-005`-konform, kein `float`/libm). Bei `power_factor=1`
    (Default) ist `q_factor=0` → `Q=0`.

    Invariante (Verstoss → `BatteryConfigInvalidValueError`):

    - `power_factor` — Leistungsfaktor, `(0, 1]`.
    """

    power_factor: Decimal = _ONE

    def __post_init__(self) -> None:
        if not (_ZERO < self.power_factor <= _ONE):
            raise BatteryConfigInvalidValueError(
                "reactive.power_factor", self.power_factor, "in (0, 1]"
            )

    @property
    def q_factor(self) -> Decimal:
        """`sqrt(1 - pf²)/pf` — der Blindleistungs-Faktor, kontext-unabhaengig
        deterministisch gerechnet (eigener `localcontext`, `prec=28`)."""
        with localcontext() as ctx:
            ctx.prec = _QFACTOR_PRECISION
            ctx.rounding = ROUND_HALF_EVEN
            return (_ONE - self.power_factor * self.power_factor).sqrt() / self.power_factor


@dataclass(frozen=True, slots=True)
class BatteryConfig:
    """Statische Battery-Parameter (`GG-BESS-001..005, 008`).

    Felder mit Wertebereich-Vertrag (Pruefung in `__post_init__`):

    - `capacity_kwh` — Nennkapazitaet, > 0.
    - `initial_soc_pct` — Start-SOC in Prozent, [min_soc_pct,
      max_soc_pct].
    - `min_soc_pct` / `max_soc_pct` — SOC-Grenzen in Prozent, je
      [0, 100]; `min_soc_pct < max_soc_pct`.
    - `max_charge_kw` / `max_discharge_kw` — Leistungsgrenzen,
      beide > 0.
    - `charge_efficiency` / `discharge_efficiency` — Wirkungsgrade,
      jeweils (0, 1].
    - `ramp_kw_per_s` — Leistungsaenderung pro Sekunde, > 0.

    Verstoesse werfen typisierte `BatteryConfigError`-Subklassen
    (`BatteryConfigInvalidValueError`/`BatteryConfigInconsistentRangeError`).
    """

    capacity_kwh: Decimal
    initial_soc_pct: Decimal
    min_soc_pct: Decimal
    max_soc_pct: Decimal
    max_charge_kw: Decimal
    max_discharge_kw: Decimal
    charge_efficiency: Decimal
    discharge_efficiency: Decimal
    ramp_kw_per_s: Decimal
    # M8-Welle-4a (ADR 0065 §2.1): opt-in Single-Zonen-Thermomodell.
    # `None` (Default) = keine Temperatur-Telemetrie (kein
    # `temperature_celsius`-Punkt, bit-genau heutiges Verhalten).
    thermal: ThermalConfig | None = None
    # M8-Welle-4b (ADR 0066 §2.1): opt-in Zellspannungs-Modell.
    # `None` (Default) = keine Zell-Telemetrie (kein `cell_voltage_delta_v`-
    # Punkt, kein `cell_voltages_v`-State, bit-genau heutiges Verhalten).
    cell: CellConfig | None = None
    # Slice 077 S1 (ADR 0077): opt-in Field-Envelope-Bloecke (soh/dc_voltage/
    # reactive). `None` (Default) = kein zusaetzlicher Punkt, bit-genau heutiges
    # Verhalten (pin-neutral).
    health: HealthConfig | None = None
    dc_bus: DcBusConfig | None = None
    reactive: ReactiveConfig | None = None

    def __post_init__(self) -> None:
        # Reduziert C901-Komplexitaet, indem die Pruefungen tabellarisch
        # gefuehrt werden. Reihenfolge ist load-bearing: Wertebereich-
        # Checks vor Konsistenz-Checks, damit Inkonsistenz-Fehler immer
        # auf bereits gueltige Einzelwerte aufbauen.
        positive: tuple[tuple[str, Decimal], ...] = (
            ("capacity_kwh", self.capacity_kwh),
            ("max_charge_kw", self.max_charge_kw),
            ("max_discharge_kw", self.max_discharge_kw),
            ("ramp_kw_per_s", self.ramp_kw_per_s),
        )
        for field, value in positive:
            if value <= _ZERO:
                raise BatteryConfigInvalidValueError(field, value, "> 0")

        pct_in_zero_hundred: tuple[tuple[str, Decimal], ...] = (
            ("min_soc_pct", self.min_soc_pct),
            ("max_soc_pct", self.max_soc_pct),
        )
        for field, value in pct_in_zero_hundred:
            if not (_ZERO <= value <= _HUNDRED):
                raise BatteryConfigInvalidValueError(field, value, "in [0, 100]")

        efficiencies: tuple[tuple[str, Decimal], ...] = (
            ("charge_efficiency", self.charge_efficiency),
            ("discharge_efficiency", self.discharge_efficiency),
        )
        for field, value in efficiencies:
            if not (_ZERO < value <= _ONE):
                raise BatteryConfigInvalidValueError(field, value, "in (0, 1]")

        self._validate_consistency()

        # M8-Welle-4a (ADR 0065 §2.1): opt-in Thermo-Block — defensiver
        # Typ-Guard (analog `PvConfig.volt_var`). `None` = inaktiv.
        if self.thermal is not None and not isinstance(self.thermal, ThermalConfig):
            raise BatteryConfigInvalidValueError(
                "thermal",
                self.thermal,
                f"None or ThermalConfig (got {type(self.thermal).__name__})",
            )

        # M8-Welle-4b (ADR 0066 §2.1): opt-in Zell-Block — defensiver
        # Typ-Guard. `None` = inaktiv.
        if self.cell is not None and not isinstance(self.cell, CellConfig):
            raise BatteryConfigInvalidValueError(
                "cell",
                self.cell,
                f"None or CellConfig (got {type(self.cell).__name__})",
            )

        # Slice 077 S1 (ADR 0077): opt-in Field-Envelope-Bloecke — defensive
        # Typ-Guards (`None` = inaktiv) + die dc_bus↔cell-Nennspannungs-Versoehnung.
        self._validate_field_envelope_blocks()

    def _validate_field_envelope_blocks(self) -> None:
        typed: tuple[tuple[str, object, type, str], ...] = (
            ("health", self.health, HealthConfig, "HealthConfig"),
            ("dc_bus", self.dc_bus, DcBusConfig, "DcBusConfig"),
            ("reactive", self.reactive, ReactiveConfig, "ReactiveConfig"),
        )
        for name, value, expected, label in typed:
            if value is not None and not isinstance(value, expected):
                raise BatteryConfigInvalidValueError(
                    name, value, f"None or {label} (got {type(value).__name__})"
                )
        # ADR 0077 §2.3: `dc_voltage` und `cell_voltage_delta_v` teilen die eine
        # Pack-Nennspannung — sind beide Bloecke aktiv, muessen sie uebereinstimmen.
        if (
            self.dc_bus is not None
            and self.cell is not None
            and self.dc_bus.nominal_voltage_v != self.cell.nominal_pack_voltage_v
        ):
            raise BatteryConfigInconsistentRangeError(
                "dc_bus.nominal_voltage_v",
                self.dc_bus.nominal_voltage_v,
                f"cell.nominal_pack_voltage_v={self.cell.nominal_pack_voltage_v} "
                "(eine Pack-Nennspannung, zwei Sichten)",
            )

    def _validate_consistency(self) -> None:
        if self.min_soc_pct >= self.max_soc_pct:
            raise BatteryConfigInconsistentRangeError(
                "min_soc_pct",
                self.min_soc_pct,
                f"max_soc_pct={self.max_soc_pct} (min must be < max)",
            )
        if not (self.min_soc_pct <= self.initial_soc_pct <= self.max_soc_pct):
            raise BatteryConfigInconsistentRangeError(
                "initial_soc_pct",
                self.initial_soc_pct,
                f"[min_soc_pct={self.min_soc_pct}, max_soc_pct={self.max_soc_pct}]",
            )

    @property
    def min_soc_kwh(self) -> Decimal:
        """SOC-Untergrenze in kWh — `min_soc_pct/100 * capacity_kwh`."""
        return self.min_soc_pct * self.capacity_kwh / _HUNDRED

    @property
    def max_soc_kwh(self) -> Decimal:
        """SOC-Obergrenze in kWh."""
        return self.max_soc_pct * self.capacity_kwh / _HUNDRED

    @property
    def initial_soc_kwh(self) -> Decimal:
        """Initialer Energieinhalt in kWh."""
        return self.initial_soc_pct * self.capacity_kwh / _HUNDRED
