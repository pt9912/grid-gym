"""`GridModelBilanz` — Netzbilanzmodell (M2 Welle 5a,
`GG-GRID-001` + `GG-GRID-002`).

Welle-5a-Minimum (ADR 0019): proportionales Modell ohne
Tragheit/Daempfung/Power-Flow. Single-Bus-Approximation,
`model_kind = "simplified-proportional"`.

Imbalance-Definition (ADR 0019 §2.2):

```
imbalance_kw = generation_kw - load_kw - storage_kw + grid_connection_kw
```

Sign-Konvention spiegelt ADR 0016 §2.2 und ADR 0017 §2.2:
positiver Imbalance = Erzeugungs-/Importueberschuss →
Frequenz/Spannung steigen.

Frequenz/Spannungs-Formeln (ADR 0019 §2.3 / §2.4):

```
frequency_hz = nominal_frequency_hz + k_f * imbalance_kw
voltage_v    = nominal_voltage_v    + k_v * imbalance_kw
```

Mit Safety-Clamps (ADR 0019 §2.3): jedes Zuschnappen
inkrementiert `clamp_event_count`. Counting-Semantik:
Frequenz UND Spannung clampen = `+= 2`; einzeln = `+= 1`;
keine = `+= 0`; keine Deduplizierung.

`GridModelBilanz` ist **kein** DeviceModel (ADR 0019 §1):
- Single-Instance pro Simulation.
- Keine `device_id`, kein `apply_command`, kein
  `DeviceModel`-Protocol.
- Snapshot-Sub-Key in `SnapshotEnvelope.sub_snapshots` ist
  `grid_model`, nicht `devices.<id>`.
- Welle 6 verdrahtet `update(...)` in den TickLoop.
"""

from __future__ import annotations

from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from decimal import ROUND_HALF_EVEN, Decimal, localcontext
from typing import Self, override

from grid_gym.hexagon.core.domain.event import (
    CONSTRAINT_TRANSFORMER_HOT_SPOT,
    GridConstraintViolationEvent,
)
from grid_gym.hexagon.core.grid_model.config import (
    GridModelConfig,
    GridModelTransformerWiringError,
    TransformerLimitConfig,
)
from grid_gym.hexagon.core.grid_model.loads import LoadEvent, LoadProfile
from grid_gym.hexagon.core.grid_model.snapshot import (
    MODEL_KIND_SIMPLIFIED_PROPORTIONAL,
    SNAPSHOT_VERSION,
    GridModelSnapshot,
)

_ZERO = Decimal(0)
_THOUSAND = Decimal(1000)
_GRID_MODEL_DECIMAL_PRECISION = 28
# M8-Welle-3b (ADR 0061 §2.2): Quantisierungs-Schritt fuer die akkumulierte
# Top-Oil-Temperatur — haelt die Stellenzahl gebunden + den Snapshot lesbar
# (deterministisch im ROUND_HALF_EVEN-Context).
_THETA_QUANTUM = Decimal("0.000001")


@contextmanager
def _grid_model_decimal_context() -> Iterator[None]:
    """Decimal-Localcontext-Wrapper (Welle-2-Review-M-2-Spiegel)."""
    with localcontext() as ctx:
        ctx.prec = _GRID_MODEL_DECIMAL_PRECISION
        ctx.rounding = ROUND_HALF_EVEN
        yield


class GridModelBilanz:
    """Netzbilanzmodell — Single-Instance, kein DeviceModel."""

    def __init__(
        self,
        config: GridModelConfig,
        active_load_events: tuple[LoadEvent, ...] = (),
        active_load_profiles: tuple[LoadProfile, ...] = (),
    ) -> None:
        self._config: GridModelConfig = config
        # ADR 0019 §2.6: nach __init__ ist Equilibrium-Zustand
        # (imbalance == 0; Frequenz/Spannung auf Nennwert).
        self._current_frequency_hz: Decimal = config.nominal_frequency_hz
        self._current_voltage_v: Decimal = config.nominal_voltage_v
        self._last_imbalance_kw: Decimal = _ZERO
        self._clamp_event_count: int = 0
        self._model_kind: str = MODEL_KIND_SIMPLIFIED_PROPORTIONAL
        # Welle 5b (ADR 0020 §2.5): passive State, der vom
        # TickLoop in Welle 6 in LoadDevice.apply_command-Aufrufe
        # uebersetzt wird. update() konsumiert ihn nicht.
        self._active_load_events: tuple[LoadEvent, ...] = active_load_events
        self._active_load_profiles: tuple[LoadProfile, ...] = active_load_profiles
        # M8-Welle-3b (ADR 0061 §2.2): akkumulierte Top-Oil-Temperatur des
        # Transformer-Constraint-Layers — `None`, wenn kein Layer
        # konfiguriert (bit-genau heutiges Verhalten); sonst auf
        # Umgebungstemperatur initialisiert.
        self._top_oil_temp_c: Decimal | None = (
            config.transformer_limit.ambient_temp_c
            if config.transformer_limit is not None
            else None
        )
        # Transientes Tick-Output (ADR 0061 §2.3): die im letzten update()
        # erkannten Verletzungen. KEIN Snapshot-State, NICHT in __eq__.
        self._last_constraint_violations: tuple[GridConstraintViolationEvent, ...] = ()

    @property
    def config(self) -> GridModelConfig:
        return self._config

    @property
    def frequency_hz(self) -> Decimal:
        return self._current_frequency_hz

    @property
    def voltage_v(self) -> Decimal:
        return self._current_voltage_v

    @property
    def last_imbalance_kw(self) -> Decimal:
        return self._last_imbalance_kw

    @property
    def clamp_event_count(self) -> int:
        return self._clamp_event_count

    @property
    def model_kind(self) -> str:
        return self._model_kind

    @property
    def active_load_events(self) -> tuple[LoadEvent, ...]:
        return self._active_load_events

    @property
    def active_load_profiles(self) -> tuple[LoadProfile, ...]:
        return self._active_load_profiles

    @property
    def top_oil_temp_c(self) -> Decimal | None:
        """M8-Welle-3b (ADR 0061 §2.2): akkumulierte Top-Oil-Temperatur
        des Transformer-Constraint-Layers; `None` ohne Layer."""
        return self._top_oil_temp_c

    @property
    def last_constraint_violations(self) -> tuple[GridConstraintViolationEvent, ...]:
        """M8-Welle-3b (ADR 0061 §2.4): die im letzten `update(...)`
        erkannten Netz-Constraint-Verletzungen (leer, wenn keine). Der
        TickLoop drainst sie in `TickResult.emitted_grid_events`."""
        return self._last_constraint_violations

    def update(
        self,
        generation_kw: Decimal,
        load_kw: Decimal,
        storage_kw: Decimal,
        grid_connection_kw: Decimal,
        tick_ms: int | None = None,
        simulation_time: int | None = None,
    ) -> None:
        """Schreitet das Modell um genau einen Tick fort
        (ADR 0019 §2.6).

        Inputs sind die aggregierten `power_kw`-Werte aus den
        Geraete-Telemetrien (vor TickLoop-Verdrahtung in
        Welle 6 sind das Test-Helper-Aggregationen).
        Sign-Konvention spiegelt ADR 0016 §2.2 / ADR 0017
        §2.2:

        - `generation_kw`: positive Summe der PV-Erzeugung.
        - `load_kw`: positive Summe des Verbrauchs.
        - `storage_kw`: Battery-Bilanz (positiv = laden,
          negativ = entladen; ADR 0014 §2.2 wird hier
          subtrahiert, weil Laden Verbrauch ist).
        - `grid_connection_kw`: positiv = Import ins lokale
          System; negativ = Export (ADR 0017 §2.2).

        Schreibt `frequency_hz`, `voltage_v`,
        `last_imbalance_kw` und `clamp_event_count` fort.
        Kein Rueckgabewert — Welle 6 liest die Properties.

        M8-Welle-3b (ADR 0061 §2.4): mit aktivem `transformer_limit` sind
        `tick_ms` (für `dt_s`) und `simulation_time` (für das Event)
        Pflicht; der TickLoop reicht sie durch. Ohne Layer werden sie
        ignoriert (Bestands-Aufrufer + Inaktiv-Pfad byte-identisch).
        Die erkannten Verletzungen liegen danach in
        `last_constraint_violations`.
        """
        with _grid_model_decimal_context():
            self._update_in_context(
                generation_kw=generation_kw,
                load_kw=load_kw,
                storage_kw=storage_kw,
                grid_connection_kw=grid_connection_kw,
                tick_ms=tick_ms,
                simulation_time=simulation_time,
            )

    def _update_in_context(
        self,
        *,
        generation_kw: Decimal,
        load_kw: Decimal,
        storage_kw: Decimal,
        grid_connection_kw: Decimal,
        tick_ms: int | None,
        simulation_time: int | None,
    ) -> None:
        imbalance_kw = generation_kw - load_kw - storage_kw + grid_connection_kw
        self._last_imbalance_kw = imbalance_kw

        raw_freq = (
            self._config.nominal_frequency_hz
            + self._config.frequency_sensitivity_hz_per_kw * imbalance_kw
        )
        raw_volt = (
            self._config.nominal_voltage_v
            + self._config.voltage_sensitivity_v_per_kw * imbalance_kw
        )

        clamp_increment = 0
        clamped_freq, freq_was_clamped = _clamp(
            raw_freq,
            self._config.frequency_clamp_min_hz,
            self._config.frequency_clamp_max_hz,
        )
        if freq_was_clamped:
            clamp_increment += 1
        clamped_volt, volt_was_clamped = _clamp(
            raw_volt,
            self._config.voltage_clamp_min_v,
            self._config.voltage_clamp_max_v,
        )
        if volt_was_clamped:
            clamp_increment += 1

        self._current_frequency_hz = clamped_freq
        self._current_voltage_v = clamped_volt
        self._clamp_event_count += clamp_increment

        # M8-Welle-3b (ADR 0061 §2.2/§2.4): Transformer-Constraint-Layer.
        self._apply_transformer_constraint(
            grid_connection_kw=grid_connection_kw,
            tick_ms=tick_ms,
            simulation_time=simulation_time,
        )

    def _apply_transformer_constraint(
        self,
        *,
        grid_connection_kw: Decimal,
        tick_ms: int | None,
        simulation_time: int | None,
    ) -> None:
        """ADR 0061 §2.2: vereinfachtes Single-Zonen-Thermomodell als
        Zeit-Strom-Mechanismus. No-op ohne `transformer_limit` (Inaktiv-
        Pfad byte-identisch). `last_constraint_violations` wird je Tick neu
        gesetzt (transientes Output)."""
        limit = self._config.transformer_limit
        if limit is None:
            self._last_constraint_violations = ()
            return
        if tick_ms is None or simulation_time is None:
            raise GridModelTransformerWiringError
        # __init__ setzt top_oil bei aktivem Layer auf ambient; der Fallback
        # ist nur das mypy-Narrowing (kein assert — S101).
        top_oil = self._top_oil_temp_c if self._top_oil_temp_c is not None else limit.ambient_temp_c
        dt_s = Decimal(tick_ms) / _THOUSAND
        apparent_power_kva = abs(grid_connection_kw)
        load_pu = apparent_power_kva / limit.max_apparent_power_kva
        load_pu_sq = load_pu * load_pu
        theta_oil_ss = limit.ambient_temp_c + limit.top_oil_rise_rated_c * load_pu_sq
        theta_oil = top_oil + (theta_oil_ss - top_oil) * (dt_s / limit.top_oil_time_constant_s)
        theta_oil = theta_oil.quantize(_THETA_QUANTUM)
        self._top_oil_temp_c = theta_oil
        theta_hs = (theta_oil + limit.hot_spot_rise_rated_c * load_pu_sq).quantize(_THETA_QUANTUM)
        if theta_hs > limit.hot_spot_limit_c:
            self._last_constraint_violations = (
                GridConstraintViolationEvent(
                    constraint=CONSTRAINT_TRANSFORMER_HOT_SPOT,
                    simulation_time=simulation_time,
                    apparent_power_kva=apparent_power_kva,
                    limit_kva=limit.max_apparent_power_kva,
                    top_oil_temp_c=theta_oil,
                    hot_spot_temp_c=theta_hs,
                    hot_spot_limit_c=limit.hot_spot_limit_c,
                ),
            )
        else:
            self._last_constraint_violations = ()

    def snapshot(self) -> Mapping[str, object]:
        """Liefert den Bilanz-Zustand als `Mapping[str, object]`
        mit `version` als Erst-Feld (ADR 0013 §2.4 Konvention)."""
        snap = GridModelSnapshot(
            version=SNAPSHOT_VERSION,
            config=self._config,
            model_kind=self._model_kind,
            current_frequency_hz=self._current_frequency_hz,
            current_voltage_v=self._current_voltage_v,
            last_imbalance_kw=self._last_imbalance_kw,
            clamp_event_count=self._clamp_event_count,
            active_load_events=self._active_load_events,
            active_load_profiles=self._active_load_profiles,
            top_oil_temp_c=self._top_oil_temp_c,
        )
        return snap.to_dict()

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        """Rekonstruiert eine `GridModelBilanz` aus einem
        Snapshot (ADR 0019 §2.5/§2.6 self-sufficient)."""
        snap = GridModelSnapshot.from_dict(state)
        bilanz = cls(
            config=snap.config,
            active_load_events=snap.active_load_events,
            active_load_profiles=snap.active_load_profiles,
        )
        bilanz._current_frequency_hz = snap.current_frequency_hz
        bilanz._current_voltage_v = snap.current_voltage_v
        bilanz._last_imbalance_kw = snap.last_imbalance_kw
        bilanz._clamp_event_count = snap.clamp_event_count
        bilanz._model_kind = snap.model_kind
        # M8-Welle-3b (ADR 0061 §2.5): Thermo-State aus dem opt-in-Snapshot.
        # `__init__` hat ihn bereits auf ambient (bei aktivem Layer) bzw.
        # None gesetzt; der Snapshot-Wert ueberschreibt fuer den Resume.
        bilanz._top_oil_temp_c = snap.top_oil_temp_c
        return bilanz

    @override
    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GridModelBilanz):
            return NotImplemented
        return (
            self._config == other._config
            and self._current_frequency_hz == other._current_frequency_hz
            and self._current_voltage_v == other._current_voltage_v
            and self._last_imbalance_kw == other._last_imbalance_kw
            and self._clamp_event_count == other._clamp_event_count
            and self._model_kind == other._model_kind
            and self._active_load_events == other._active_load_events
            and self._active_load_profiles == other._active_load_profiles
            and self._top_oil_temp_c == other._top_oil_temp_c
        )

    @override
    def __hash__(self) -> int:
        return hash(
            (
                self._config,
                self._current_frequency_hz,
                self._current_voltage_v,
                self._last_imbalance_kw,
                self._clamp_event_count,
                self._model_kind,
                self._active_load_events,
                self._active_load_profiles,
                self._top_oil_temp_c,
            )
        )


def _clamp(value: Decimal, lo: Decimal, hi: Decimal) -> tuple[Decimal, bool]:
    """Clamp `value` auf `[lo, hi]`. Gibt `(geclamped, hat_geclampt)`
    zurueck — `hat_geclampt` ist `True`, wenn der Originalwert
    ausserhalb des Intervalls lag."""
    if value < lo:
        return lo, True
    if value > hi:
        return hi, True
    return value, False


__all__ = [
    "GridModelBilanz",
]
