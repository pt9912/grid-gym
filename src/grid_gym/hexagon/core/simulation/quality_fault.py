"""Spine-interner, metrik-adressierter Quality-Fault-Runtime
(ADR 0074 §2.2; Slice 071 / GG-FAULT-003 + Slice 072 / GG-FAULT-002).

Der `ScenarioFaultEngine` (ADR 0059) bleibt fuer **device-adressierte
Physik-Faults** zustaendig (`device.inject_fault(...)`). Metrik-
adressierte Quality-Faults (`nan_injection`, `stale_data`) manipulieren
dagegen den **Qualitaetsstatus emittierter Telemetrie** — eine zentrale
Prozessor-Aufgabe ([`GG-AR-P-003`], eine Pruefstelle fuer Stream/
Persistenz/Replay), die der device-adressierte Pfad strukturell nicht
ausdruecken kann (Devices emittieren unbedingt `quality=VALID`).

Der `QualityFaultRuntime` wird **pro Lauf** aus `scenario.faults`
konstruiert (opt-in via `build_quality_fault_runtime` → `None`, wenn
das Szenario keinen Quality-Fault deklariert) und vom TickLoop-Spine
in `_apply_quality_fault_stage` — Geschwister der `max_age`-STALE-Stage
([`ADR 0052`] §2.2) — auf der gesammelten `emitted`-Liste **unmittelbar
vor** dem `TickResult`-Bau aufgerufen.

Aktive-Fenster-Semantik identisch zum Physik-Engine ([`ADR 0025`]):
`start_simulation_time ≤ now < start_simulation_time + duration_ms`.

Slice A (GG-FAULT-003, ADR 0074 §2.4): NaN-Verhalten **ohne** Last-
Value-Cache. Aktiver `nan_injection`-Fault → matchende Punkte tragen
den endlichen Sentinel `Decimal("0")` + `quality=Quality.NAN` (kein
numerischer NaN — `serialization/canonical.py`/`NonFiniteDecimalError`
bleibt unangetastet); einmaliger Raw-Alarm beim inactive→active-
Uebergang (ADR 0074 §2.5).

Slice B (GG-FAULT-002, ADR 0074 §2.3): `stale_data`-Verhalten **mit**
per-`(device_id, metric)`-Last-Valid-Value-Cache. Aktiver `stale_data`-
Fault → der emittierte Wert wird durch den zuletzt gecachten gueltigen
Wert **ersetzt** (weitergeliefert); solange `(now - cached_sim_time) ≤
max_age_ms` bleibt die Quality unveraendert, sobald `>` (strikt, ADR
0052 §2.5-Grenzsemantik) → `quality=Quality.STALE`. **Kein** Alarm (ADR
0074 §2.5; Alarm-bei-STALE ist GG-SAFE-003-Scope). Der Cache ueberlebt
den TickLoop-Snapshot **opt-in** (ADR 0074 §2.3/§2.7), damit Resume
mitten im Stale-Fenster den letzten gueltigen Wert nicht verliert.

Der Alarm-Transitions-State (`_active`) ist **runtime-only** und wird —
exakt wie `ScenarioFaultEngine._active_faults` — **nicht** im Snapshot
serialisiert; der Runtime wird auf Resume neu konstruiert (Praezedenz
device-adressierter `fault_port`). Der Last-Value-Cache (`_last_valid`)
ist dagegen der **einzige** opt-in serialisierte State — ohne ihn
verlaeße ein Resume mitten im Stale-Fenster den Vorwert. Ohne
Quality-Fault ist der Runtime `None` → die Stage no-op → byte-identisch
(ADR 0074 §2.7).
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Final

from grid_gym.hexagon.core.domain.fault import (
    FAULT_TYPE_NAN_INJECTION,
    FAULT_TYPE_STALE_DATA,
)
from grid_gym.hexagon.core.domain.quality import QUALITY_SEVERITY, Quality
from grid_gym.hexagon.core.domain.scenario import ScenarioFault
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.errors import VersionError, WrongTypeError
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_decimal,
    assert_int,
    assert_mapping,
    assert_required_keys,
    assert_str,
)

_NAN_SENTINEL: Final[Decimal] = Decimal("0")
"""ADR 0074 §2.4: endlicher Sentinel-Wert (Praezedenz [`ADR 0053`] §2.6
`MISSING`-Point) fuer NaN-markierte Punkte — **kein** numerischer NaN
betritt die Domaene."""

_CACHE_SUBSYSTEM: Final[str] = "quality_fault"
"""snapshot_codec-Subsystem-Tag fuer typisierte Format-Fehler beim
Last-Value-Cache-Restore (ADR 0074 §2.3)."""

_CACHE_SNAPSHOT_VERSION: Final[int] = 1
"""Schema-Version des opt-in Last-Value-Cache-Sub-Snapshots (ADR 0074
§2.7). Erhoehung → Folge-ADR (analog `_SNAPSHOT_VERSION` im TickLoop)."""

_CACHE_KEYS: Final[frozenset[str]] = frozenset({"version", "entries"})
_CACHE_ENTRY_KEYS: Final[frozenset[str]] = frozenset(
    {"device_id", "metric", "value", "simulation_time"}
)


@dataclass(frozen=True, slots=True)
class QualityFaultNanInjectionAlarm:
    """Raw-Alarm fuer einen aktiven `nan_injection`-Quality-Fault
    (ADR 0074 §2.5).

    Analog `GridConnectionFaultAlarm` (Slice 070), aber spine-erzeugt
    statt device-erzeugt: die Quality-Fault-Stage hebt ihn genau **einmal
    beim inactive→active-Uebergang** (nicht pro Tick) in den Spine-Alarm-
    Kanal; der Mapper `alarm_from_quality_fault_nan_injection_alarm`
    (`alarm_mappers.py`) bildet ihn auf den Unified `Alarm` mit
    Run-Kontext ab (Code `quality_fault_nan_injection`, Severity
    `warning`).

    Felder:
    - `target_device_id` — Zielgeraet (= `ScenarioFault.target`).
    - `metric` — die betroffene Metrik (aus `payload["metric"]`).
    """

    target_device_id: str
    metric: str


class QualityFaultRuntime:
    """Spine-interner Runtime fuer metrik-adressierte Quality-Faults
    (ADR 0074 §2.2).

    Konstruktor-Injection von `scenario.faults`; filtert auf die
    `nan_injection`-Faults mit gueltiger `payload["metric"]: str` (Slice
    A) und die `stale_data`-Faults mit gueltiger `payload["metric"]: str`
    **und** `payload["max_age_ms"]: int` (Slice B) und belegt sie mit
    deterministischer ID (`fault-{i}`, Original-Scenario-Index — stabil
    ueber Fault-Typ-Hinzufuegungen, Konvention [`ScenarioFaultEngine`]).
    Alle uebrigen Fault-Typen (Physik-Faults) werden ignoriert.
    """

    def __init__(self, faults: Sequence[ScenarioFault]) -> None:
        # (fault_id, fault, metric) — Metrik einmal beim Bau extrahiert.
        # Der Scenario-Validator (ADR 0074 §2.1) garantiert fuer
        # `nan_injection` ein `payload["metric"]: str`; der isinstance-
        # Guard ist defensive Tiefen-Sicherung (nie-Zweig fuer validierte
        # Szenarien), damit ein fehltypisierter Payload keinen
        # Laufzeit-Crash im Spine ausloest.
        self._nan_faults: list[tuple[str, ScenarioFault, str]] = []
        # (fault_id, fault, metric, max_age_ms) — Slice B. Der Validator
        # (ADR 0074 §2.1) garantiert `metric: str` + `max_age_ms: int > 0`;
        # die isinstance-Guards sind dieselbe defensive Tiefe.
        self._stale_faults: list[tuple[str, ScenarioFault, str, int]] = []
        for index, fault in enumerate(faults):
            fault_id = f"fault-{index}"
            if fault.type == FAULT_TYPE_NAN_INJECTION:
                metric = fault.payload.get("metric")
                if isinstance(metric, str):
                    self._nan_faults.append((fault_id, fault, metric))
            elif fault.type == FAULT_TYPE_STALE_DATA:
                metric = fault.payload.get("metric")
                max_age_ms = fault.payload.get("max_age_ms")
                # `bool` ist `int`-Subklasse — Alter-Fenster ist eine
                # echte Ganzzahl (spiegelt `_assert_int` im Validator).
                # Inline-isinstance verengt fuer mypy --strict beide Werte.
                if (
                    isinstance(metric, str)
                    and isinstance(max_age_ms, int)
                    and not isinstance(max_age_ms, bool)
                ):
                    self._stale_faults.append((fault_id, fault, metric, max_age_ms))
        # ADR 0074 §2.5: Alarm-Transitions-State (True = aktiv). Runtime-
        # only, NICHT im Snapshot serialisiert (Praezedenz
        # `ScenarioFaultEngine._active_faults`). Key: fault_id. Nur
        # `nan_injection` hebt Alarme (`stale_data` ist alarmlos).
        self._active: dict[str, bool] = {}
        # ADR 0074 §2.7 (Snapshot-minimal): die genau adressierten
        # `stale_data`-Ziel-`(device_id, metric)`-Paare (fenster-unabhaengig).
        # Der Cache wird NUR fuer diese Paare gefuehrt — nicht fuer jeden
        # VALID-Punkt eines Szenarios, das irgendeinen `stale_data`-Fault
        # deklariert. Haelt den opt-in Snapshot bei O(stale-Ziele) statt
        # O(alle (device, metric)) und treu zur §2.7-Minimal-Intent
        # (nur der weiterzuliefernde Vorwert wird persistiert).
        self._stale_targets: frozenset[tuple[str, str]] = frozenset(
            (fault.target, metric) for _fault_id, fault, metric, _max_age_ms in self._stale_faults
        )
        # ADR 0074 §2.3: per-(device_id, metric)-Last-Valid-Value-Cache
        # `(value, simulation_time)`. Anders als `_active` ueberlebt er
        # den Snapshot **opt-in** (`cache_snapshot`/`restore_cache`).
        self._last_valid: dict[tuple[str, str], tuple[Decimal, int]] = {}

    @property
    def has_faults(self) -> bool:
        """True, wenn der Runtime mindestens einen metrik-adressierten
        Quality-Fault (`nan_injection` oder `stale_data`) haelt.
        `build_quality_fault_runtime` liefert sonst `None` (Stage
        vollstaendig aus → byte-identisch, ADR 0074 §2.7)."""
        return bool(self._nan_faults or self._stale_faults)

    def apply_stage(
        self,
        emitted: list[TelemetryPoint],
        now: int,
    ) -> tuple[list[TelemetryPoint], list[QualityFaultNanInjectionAlarm]]:
        """ADR 0074 §2.2/§2.3/§2.4/§2.5/§2.6: rewritet die matchenden
        Punkte aktiver Quality-Faults und liefert die Transitions-Alarms.

        Aktives Fenster: `start ≤ now < start + duration` ([`ADR 0025`]).
        Match: `point.device_id == fault.target` **und**
        `point.metric == payload["metric"]`. Rewrite via
        `dataclasses.replace` (frozen+slots gewahrt; `source`/`sequence`/
        `simulation_time` unberuehrt → Scheduler-Tie-Breaking
        unangetastet).

        Reihenfolge (ADR 0074 §2.3 Cache-Timing-Risiko): **zuerst** der
        Cache-Update-Pass (der letzte gueltige Wert wird gecacht, BEVOR
        ein Rewrite ihn einfrieren koennte), **dann** der Rewrite-Pass
        (`nan_injection` vor `stale_data`; beide severity-monoton, ADR
        0074 §2.6). Nur Sim-Zeit (`AC-NO-TIME`); deterministische
        Fault-Iteration (Szenario-Reihenfolge)."""
        active_nan, alarms = self._collect_active_nan(now)
        active_stale = self._collect_active_stale(now)
        self._update_last_valid_cache(emitted, active_stale)
        if not active_nan and not active_stale:
            return emitted, alarms
        rewritten = [self._rewrite_point(point, now, active_nan, active_stale) for point in emitted]
        return rewritten, alarms

    def _collect_active_nan(
        self, now: int
    ) -> tuple[set[tuple[str, str]], list[QualityFaultNanInjectionAlarm]]:
        """ADR 0074 §2.4/§2.5: aktive `nan_injection`-`(target, metric)`-
        Menge + Transitions-Alarms (genau **einer** je Fault beim
        inactive→active-Uebergang, nicht pro Tick)."""
        active_targets: set[tuple[str, str]] = set()
        alarms: list[QualityFaultNanInjectionAlarm] = []
        for fault_id, fault, metric in self._nan_faults:
            window_end = fault.start_simulation_time + fault.duration_ms
            in_window = fault.start_simulation_time <= now < window_end
            was_active = self._active.get(fault_id, False)
            if in_window:
                active_targets.add((fault.target, metric))
                if not was_active:
                    alarms.append(
                        QualityFaultNanInjectionAlarm(
                            target_device_id=fault.target,
                            metric=metric,
                        )
                    )
                    self._active[fault_id] = True
            elif was_active:
                self._active[fault_id] = False
        return active_targets, alarms

    def _collect_active_stale(self, now: int) -> dict[tuple[str, str], int]:
        """ADR 0074 §2.3: aktive `stale_data`-`(target, metric)` →
        `max_age_ms`. Kein Alarm-/Transitions-State (`stale_data` ist
        alarmlos, ADR 0074 §2.5)."""
        active_stale: dict[tuple[str, str], int] = {}
        for _fault_id, fault, metric, max_age_ms in self._stale_faults:
            window_end = fault.start_simulation_time + fault.duration_ms
            if fault.start_simulation_time <= now < window_end:
                # Bei ueberlappenden Faults auf demselben (target, metric)
                # gewinnt deterministisch der letzte in Szenario-
                # Reihenfolge (dict-Overwrite); ein additiver Faecher ist
                # ADR 0074 §7-Folgearbeit.
                active_stale[fault.target, metric] = max_age_ms
        return active_stale

    def _update_last_valid_cache(
        self,
        emitted: Sequence[TelemetryPoint],
        active_stale: Mapping[tuple[str, str], int],
    ) -> None:
        """ADR 0074 §2.3 Cache-Update-Regel: ist `(device_id, metric)` ein
        `stale_data`-Ziel, liegt dort **kein** aktiver `stale_data`-Fault an
        und ist der Punkt `Quality.VALID`, wird `(value, simulation_time)`
        gecacht (der letzte gueltige Wert). Laeuft **vor** dem Rewrite auf
        dem *echten* Vorwert (Cache-Timing-Risiko: nicht auf den bereits
        eingefrorenen Wert cachen). Der `_stale_targets`-Filter haelt den
        Cache — und damit den opt-in Snapshot (§2.7) — auf die tatsaechlich
        adressierten Ziele beschraenkt (kein Bloat durch fremde
        `(device, metric)`-Paare). No-op, wenn kein `stale_data`-Fault
        konfiguriert ist (Slice-A-only-Szenarien bleiben byte-identisch —
        kein Cache-Aufbau, kein opt-in Snapshot-Anteil)."""
        if not self._stale_faults:
            return
        for point in emitted:
            key = (point.device_id, point.metric)
            if (
                key in self._stale_targets
                and key not in active_stale
                and point.quality is Quality.VALID
            ):
                self._last_valid[key] = (point.value, point.simulation_time)

    def _rewrite_point(
        self,
        point: TelemetryPoint,
        now: int,
        active_nan: set[tuple[str, str]],
        active_stale: Mapping[tuple[str, str], int],
    ) -> TelemetryPoint:
        """Rewrite eines einzelnen Punkts: `nan_injection` (Severity 6)
        vor `stale_data` (Severity 3), beide nur auf Punkte mit
        **niedrigerer** `QUALITY_SEVERITY` (ADR 0074 §2.6 — schwerere
        Befunde wie `MISSING` (7) dominieren, kein Informationsverlust).

        Der Severity-Gate loest zugleich die §2.3/§2.6-Spannung fuer
        `stale_data`: die Wert-Weiterlieferung ist an denselben Gate
        gebunden — ein Live-Punkt mit **schlechterer** Quality (INVALID/
        NAN/MISSING/FAULT_INJECTED) wird **nicht** wert-ersetzt (der
        schwerere Befund darf nicht durch einen eingefrorenen
        „gueltig aussehenden" Vorwert maskiert werden). Nur VALID/
        ESTIMATED/LIMITED (Severity < STALE) werden weitergeliefert."""
        key = (point.device_id, point.metric)
        point_severity = QUALITY_SEVERITY[point.quality]
        if key in active_nan and point_severity < QUALITY_SEVERITY[Quality.NAN]:
            return replace(point, value=_NAN_SENTINEL, quality=Quality.NAN)
        if key in active_stale and point_severity < QUALITY_SEVERITY[Quality.STALE]:
            return self._apply_stale(point, now, active_stale[key])
        return point

    def _apply_stale(
        self,
        point: TelemetryPoint,
        now: int,
        max_age_ms: int,
    ) -> TelemetryPoint:
        """ADR 0074 §2.3 STALE-Verhalten fuer einen matchenden Punkt.

        - **Cache-Eintrag vorhanden:** der emittierte Wert wird durch den
          gecachten Last-Valid-Wert **ersetzt** (weitergeliefert); solange
          `(now - cached_sim_time) ≤ max_age_ms` bleibt die Quality
          unveraendert, sobald `>` (strikt) → `Quality.STALE`.
        - **Kein Cache-Eintrag** (Fault ab Tick 0, nie ein gueltiger
          Vorwert): der Wert wird **nicht** ersetzt (nichts
          weiterzuliefern); STALE nur, wenn der Punkt selbst zu alt ist
          (Referenz = eigene Sim-Zeit — die ehrliche Grenze degeneriert
          zur `max_age`-Stage-Semantik, ADR 0052 §2.5)."""
        cached = self._last_valid.get((point.device_id, point.metric))
        if cached is None:
            if (now - point.simulation_time) > max_age_ms:
                return replace(point, quality=Quality.STALE)
            return point
        value, cached_simulation_time = cached
        quality = Quality.STALE if (now - cached_simulation_time) > max_age_ms else point.quality
        return replace(point, value=value, quality=quality)

    def cache_snapshot(self) -> Mapping[str, object] | None:
        """ADR 0074 §2.3/§2.7: opt-in Snapshot-Anteil des Last-Value-
        Cache. `None` bei leerem Cache → der TickLoop haengt **keinen**
        Sub-Snapshot-Key ein (byte-identisch, solange kein `stale_data`-
        Vorwert gecacht wurde). Eintraege deterministisch nach
        `(device_id, metric)` sortiert; `value` als roher `Decimal`
        (canonical_json-faehig, wie die Geraete-Snapshots)."""
        if not self._last_valid:
            return None
        entries = tuple(
            {
                "device_id": device_id,
                "metric": metric,
                "value": value,
                "simulation_time": simulation_time,
            }
            for (device_id, metric), (value, simulation_time) in sorted(self._last_valid.items())
        )
        return {"version": _CACHE_SNAPSHOT_VERSION, "entries": entries}

    def restore_cache(self, raw: object) -> None:
        """ADR 0074 §2.3: rekonstruiert den Last-Value-Cache aus dem
        opt-in Sub-Snapshot, damit ein Resume mitten im Stale-Fenster den
        letzten gueltigen Wert nicht verliert. `None` (Cache war leer /
        Snapshot ohne den Key) → no-op. Typisierte Format-Fehler via
        snapshot_codec-Helper (`subsystem="quality_fault"`)."""
        if raw is None:
            return
        state = assert_mapping(raw, "cache", _CACHE_SUBSYSTEM)
        assert_required_keys(state, _CACHE_KEYS, _CACHE_SUBSYSTEM)
        version = assert_int(state["version"], "version", _CACHE_SUBSYSTEM)
        if version != _CACHE_SNAPSHOT_VERSION:
            raise VersionError(_CACHE_SUBSYSTEM, expected=_CACHE_SNAPSHOT_VERSION, found=version)
        raw_entries = state["entries"]
        if not isinstance(raw_entries, list | tuple):
            raise WrongTypeError(_CACHE_SUBSYSTEM, "entries", "list", type(raw_entries).__name__)
        restored: dict[tuple[str, str], tuple[Decimal, int]] = {}
        for index, raw_entry in enumerate(raw_entries):
            entry = assert_mapping(raw_entry, f"entries[{index}]", _CACHE_SUBSYSTEM)
            assert_required_keys(entry, _CACHE_ENTRY_KEYS, _CACHE_SUBSYSTEM)
            path = f"entries[{index}]"
            device_id = assert_str(entry["device_id"], f"{path}.device_id", _CACHE_SUBSYSTEM)
            metric = assert_str(entry["metric"], f"{path}.metric", _CACHE_SUBSYSTEM)
            value = assert_decimal(entry["value"], f"{path}.value", _CACHE_SUBSYSTEM)
            simulation_time = assert_int(
                entry["simulation_time"], f"{path}.simulation_time", _CACHE_SUBSYSTEM
            )
            restored[device_id, metric] = (value, simulation_time)
        self._last_valid = restored


def build_quality_fault_runtime(
    faults: Sequence[ScenarioFault],
) -> QualityFaultRuntime | None:
    """ADR 0074 §2.2/§2.7: baut den spine-internen `QualityFaultRuntime`
    aus `scenario.faults` oder `None`, wenn kein Quality-Fault deklariert
    ist.

    `None` (Default-Fall) skippt die Spine-Stage vollstaendig — exakt das
    opt-in-Muster des `max_age_ms`-/`command_engine`-Pfads: Szenarien ohne
    `nan_injection`/`stale_data` bleiben byte-identisch (Demo-Hash-Pins
    unberuehrt)."""
    runtime = QualityFaultRuntime(faults)
    return runtime if runtime.has_faults else None
