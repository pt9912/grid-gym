"""Spine-interner, metrik-adressierter Quality-Fault-Runtime
(ADR 0074 §2.2; Slice 071 / GG-FAULT-003).

Der `ScenarioFaultEngine` (ADR 0059) bleibt fuer **device-adressierte
Physik-Faults** zustaendig (`device.inject_fault(...)`). Metrik-
adressierte Quality-Faults (`nan_injection`; Slice B ergaenzt
`stale_data`) manipulieren dagegen den **Qualitaetsstatus emittierter
Telemetrie** — eine zentrale Prozessor-Aufgabe ([`GG-AR-P-003`], eine
Pruefstelle fuer Stream/Persistenz/Replay), die der device-adressierte
Pfad strukturell nicht ausdruecken kann (Devices emittieren unbedingt
`quality=VALID`).

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
Uebergang (ADR 0074 §2.5). Der Last-Value-Cache + `stale_data` (ADR
0074 §2.3, GG-FAULT-002) sind Slice B.

Der Alarm-Transitions-State (`_active`) ist **runtime-only** und wird —
exakt wie `ScenarioFaultEngine._active_faults` — **nicht** im Snapshot
serialisiert; der Runtime wird auf Resume neu konstruiert (Praezedenz
device-adressierter `fault_port`). Ohne Quality-Fault ist der Runtime
`None` → die Stage no-op → byte-identisch (ADR 0074 §2.7).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, replace
from decimal import Decimal
from typing import Final

from grid_gym.hexagon.core.domain.fault import FAULT_TYPE_NAN_INJECTION
from grid_gym.hexagon.core.domain.quality import QUALITY_SEVERITY, Quality
from grid_gym.hexagon.core.domain.scenario import ScenarioFault
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint

_NAN_SENTINEL: Final[Decimal] = Decimal("0")
"""ADR 0074 §2.4: endlicher Sentinel-Wert (Praezedenz [`ADR 0053`] §2.6
`MISSING`-Point) fuer NaN-markierte Punkte — **kein** numerischer NaN
betritt die Domaene."""


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
    `nan_injection`-Faults mit gueltiger `payload["metric"]: str` und
    belegt sie mit deterministischer ID (`fault-{i}`, Original-Scenario-
    Index — stabil ueber Fault-Typ-Hinzufuegungen, Konvention
    [`ScenarioFaultEngine`]). Alle uebrigen Fault-Typen (Physik-Faults,
    Slice-B-`stale_data`) werden ignoriert.
    """

    def __init__(self, faults: Sequence[ScenarioFault]) -> None:
        # (fault_id, fault, metric) — Metrik einmal beim Bau extrahiert.
        # Der Scenario-Validator (ADR 0074 §2.1) garantiert fuer
        # `nan_injection` ein `payload["metric"]: str`; der isinstance-
        # Guard ist defensive Tiefen-Sicherung (nie-Zweig fuer validierte
        # Szenarien), damit ein fehltypisierter Payload keinen
        # Laufzeit-Crash im Spine ausloest.
        self._nan_faults: list[tuple[str, ScenarioFault, str]] = []
        for index, fault in enumerate(faults):
            if fault.type != FAULT_TYPE_NAN_INJECTION:
                continue
            metric = fault.payload.get("metric")
            if isinstance(metric, str):
                self._nan_faults.append((f"fault-{index}", fault, metric))
        # ADR 0074 §2.5: Alarm-Transitions-State (True = aktiv). Runtime-
        # only, NICHT im Snapshot serialisiert (Praezedenz
        # `ScenarioFaultEngine._active_faults`). Key: fault_id.
        self._active: dict[str, bool] = {}

    @property
    def has_faults(self) -> bool:
        """True, wenn der Runtime mindestens einen `nan_injection`-Fault
        haelt. `build_quality_fault_runtime` liefert sonst `None` (Stage
        vollstaendig aus → byte-identisch, ADR 0074 §2.7)."""
        return bool(self._nan_faults)

    def apply_stage(
        self,
        emitted: list[TelemetryPoint],
        now: int,
    ) -> tuple[list[TelemetryPoint], list[QualityFaultNanInjectionAlarm]]:
        """ADR 0074 §2.2/§2.4/§2.5: rewritet die matchenden Punkte
        aktiver `nan_injection`-Faults und liefert die Transitions-Alarms.

        Aktives Fenster: `start ≤ now < start + duration` ([`ADR 0025`]).
        Match: `point.device_id == fault.target` **und**
        `point.metric == payload["metric"]`. Rewrite via
        `dataclasses.replace` (frozen+slots gewahrt; `source`/`sequence`
        unberuehrt → Scheduler-Tie-Breaking unangetastet): Wert →
        `Decimal("0")`-Sentinel, Quality → `NAN`. Severity-Override (ADR
        0074 §2.6): `NAN` (6) ersetzt nur Punkte mit **niedrigerer**
        `QUALITY_SEVERITY` — `MISSING` (7) dominiert. Nur Sim-Zeit
        (`AC-NO-TIME`). Alarm genau **einmal** je Fault beim
        inactive→active-Uebergang; deterministische Fault-Iteration
        (Szenario-Reihenfolge)."""
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
        if not active_targets:
            return emitted, alarms
        nan_severity = QUALITY_SEVERITY[Quality.NAN]
        rewritten = [
            replace(point, value=_NAN_SENTINEL, quality=Quality.NAN)
            if (point.device_id, point.metric) in active_targets
            and QUALITY_SEVERITY[point.quality] < nan_severity
            else point
            for point in emitted
        ]
        return rewritten, alarms


def build_quality_fault_runtime(
    faults: Sequence[ScenarioFault],
) -> QualityFaultRuntime | None:
    """ADR 0074 §2.2/§2.7: baut den spine-internen `QualityFaultRuntime`
    aus `scenario.faults` oder `None`, wenn kein Quality-Fault deklariert
    ist.

    `None` (Default-Fall) skippt die Spine-Stage vollstaendig — exakt das
    opt-in-Muster des `max_age_ms`-/`command_engine`-Pfads: Szenarien ohne
    `nan_injection` bleiben byte-identisch (Demo-Hash-Pins unberuehrt)."""
    runtime = QualityFaultRuntime(faults)
    return runtime if runtime.has_faults else None
