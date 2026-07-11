# 071 — Metrik-adressierter `nan_injection`-Quality-Fault (NaN-Injection)

**Status:** Done — 2026-07-11
**Datum:** 2026-07-11
**Quelle:** GG-FAULT-Konsolidierungs-Investigation — `make doc-trace` meldet
0 Waisen, aber [`GG-FAULT-003`](../../../../spec/lastenheft.md#gg-fault-003)
„NaN-Injection" (MUSS) hatte **keinen** dedizierten Fault-Typ. Die
Architektur-Entscheidung [`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md)
fixiert den metrik-adressierten Quality-Fault-Pfad und teilt die Lieferung in
zwei Slices; **Slice A = dieses Slice** liefert die Foundation + das
NaN-Verhalten (ohne Last-Value-Cache — der ist Slice B).

---

## Kontext / Befund

[`GG-FAULT-003`](../../../../spec/lastenheft.md#gg-fault-003)-Akzeptanz: „Ein
NaN-Fault kann fuer ein Ziel und eine Metrik einen nicht numerischen
Eingangswert erzeugen. Der Wert wird nicht ungeprueft in den Geraetezustand
uebernommen, sondern mit Qualitaetsstatus `nan` und Alarm protokolliert."

Das ist — anders als
[`GG-FAULT-004`](../../../../spec/lastenheft.md#gg-fault-004)/[`GG-FAULT-005`](../../../../spec/lastenheft.md#gg-fault-005)
(`frequency_drop`/`voltage_drop`, Geraete-Physik) — ein **(Ziel, Metrik)**-
adressierter Effekt auf den **Qualitaetsstatus emittierter Telemetrie**. Der
device-adressierte [`ADR 0022`](../../adr/0022-fault-injection-protocol.md)/[`ADR 0059`](../../adr/0059-generic-scenario-fault-engine.md)-Pfad
kann das strukturell nicht ausdruecken (Devices emittieren unbedingt
`quality=VALID`). [`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md)
§2.2 legt daher einen **parallelen, spine-internen** Quality-Fault-Pfad an —
Geschwister der [`ADR 0052`](../../adr/0052-max-age-stale-quality-stage.md)-`max_age`-STALE-Stage.

**Integrationspunkt-Analyse (aufgeloest):** Quality-Manipulation ist eine
zentrale Prozessor-Aufgabe ([`GG-AR-P-003`](../../../../spec/architecture.md#2-architekturprinzipien) —
eine Pruefstelle fuer Stream/Persistenz/Replay), **nicht** `device.inject_fault`
(Impedanz-Mismatch). Die Metrik reist im `payload` (`{"metric": <str>}`) statt
als `ScenarioFault.metric`-Schema-Feld — ein Schema-Feld wuerde den
`asdict`-basierten `scenario_hash` **aller** Szenarien flippen (Pin-Bruch),
exakt die [`ADR 0052`](../../adr/0052-max-age-stale-quality-stage.md) §2.1-Linie.
Der NaN-Wert wird mit dem endlichen Sentinel `Decimal("0")` + `quality=nan`
versoehnt (Praezedenz [`ADR 0053`](../../adr/0053-comm-failure-wrapper-missing-quality-alarm.md)
§2.6): **kein** numerischer NaN betritt die Domaene, der
`serialization/canonical.py`-Reject (`NonFiniteDecimalError`) bleibt
unangetastet; `quality = "nan"` ist die von
[`GG-DATA-003`](../../../../spec/lastenheft.md#gg-data-003) reservierte
Darstellung.

**Determinismus:** alles opt-in — ohne `nan_injection`-Fault ist der
`QualityFaultRuntime` `None` → die Spine-Stage no-op → Szenarien byte-identisch
(Demo-Hash-Pins + `scenario_hash` unberuehrt). **Kein** Last-Value-Cache in
Slice A → **keine** Snapshot-Aenderung. Der Alarm-Transitions-State ist
runtime-only (Praezedenz `ScenarioFaultEngine._active_faults` — auch nicht im
Snapshot serialisiert); der Runtime wird auf Resume re-injiziert (wie der
device-adressierte `fault_port`), nicht rekonstruiert.

## Tranchen

- **C1 — Konstante + Validator:** `FAULT_TYPE_NAN_INJECTION = "nan_injection"`
  als Single Source in `core/domain/fault.py`; Re-Export in `core/faults/types.py`.
  Validator-Schaerfung ([`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md)
  §2.1): fuer `type == "nan_injection"` MUSS `payload["metric"]: str` (fehlend →
  `ScenarioMissingKeysError`, fehltypisiert → `ScenarioWrongTypeError`).
- **C2 — Spine-Runtime + Stage:** NEU `core/simulation/quality_fault.py`
  (`QualityFaultRuntime` + `build_quality_fault_runtime` + Raw-Alarm
  `QualityFaultNanInjectionAlarm`); NEU `_apply_quality_fault_stage` +
  `_build_tick_result` im TickLoop-Spine; Konstruktor-Kwarg
  `quality_fault_runtime` + `from_snapshot`-Symmetrie; Verdrahtung in
  `build_tick_loop` (aus `scenario.faults`).
- **C3 — Alarm:** Raw `QualityFaultNanInjectionAlarm` → Mapper
  `alarm_from_quality_fault_nan_injection_alarm` (Code
  `quality_fault_nan_injection`, Severity `warning`) in `dispatch_alarm_mapper`
  registriert; Emission ueber `TickResult.emitted_alarms` einmal beim
  inactive→active-Uebergang.
- **C4 — Whitelists:** `_KNOWN_FAULT_TYPES`-Entkopplung im Demo-Setup
  (`nan_injection` gilt als **bekannt**, ist aber NICHT in den `supported_types`
  der device-adressierten `ScenarioFaultEngine`); HTTP-Whitelist
  `_FAULT_TYPE_TO_DEVICE_TYPE`-Ergaenzung um ein metrik-adressiertes Set (Ziel
  darf jedes Geraet sein → device-Typ-Match uebersprungen, Target-Existenz
  bleibt).
- **C5 — Tests:** Unit (Rewrite/Match/Fenster/Alarm-Transition/Severity-
  Override/NaN-vs-STALE/None-no-op/Builder+Resume-Symmetrie/Determinismus),
  Validator (metric-Pflicht), Alarm-Mapper (direkt + Dispatch), Demo-Compose-
  Entkopplung, HTTP-metric-addressed-Accept.
- **C6 — Doku + Closure:** [`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md)
  Status `Accepted`; ADR-Index-Zeile + Folge-ADR-Cross-Refs (0052/0053);
  `traceability.md` §27.3-Zeile
  [`GG-FAULT-003`](../../../../spec/lastenheft.md#gg-fault-003); CHANGELOG
  `[Unreleased]`; Roadmap-Nachzug; Self-Move nach `done/`.

## DoD

- [x] `nan_injection` als metrik-adressierter Quality-Fault (Spine-Stage, kein
      `device.inject_fault`); aktiver Fault → matchende Punkte tragen Sentinel
      `Decimal("0")` + `quality=nan`, Geraet unberuehrt.
- [x] Einmaliger `quality_fault_nan_injection`-Alarm (`warning`) beim
      inactive→active-Uebergang ueber `TickResult.emitted_alarms`.
- [x] Kein numerischer NaN (`canonical.py`/`NonFiniteDecimalError` unberuehrt);
      Severity-Override ueber `QUALITY_SEVERITY` (`nan` (6) ersetzt nur
      niedrigere, `missing` (7) dominiert).
- [x] Validator: `payload["metric"]: str` Pflicht fuer `nan_injection`.
- [x] Determinismus: Szenarien ohne `nan_injection` byte-identisch (Runtime
      opt-in `None`, keine Snapshot-Aenderung).
- [x] `make gates`, `make docs-check`, `make doc-trace`, `make test-determinism`,
      `make test-fault` gruen; `make doc-trace` zeigt
      [`GG-FAULT-003`](../../../../spec/lastenheft.md#gg-fault-003) abgedeckt.
- [x] [`GG-FAULT-003`](../../../../spec/lastenheft.md#gg-fault-003) in
      `traceability.md` §27.3; CHANGELOG `[Unreleased]`;
      [`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md)
      `Accepted`.

**Release-Entscheidung:** ja-Kandidat, aber gebuendelt unter `[Unreleased]` bis
zum naechsten Release-Schnitt (Runtime-Delta vorhanden; SemVer-Ziel Minor —
additives Feature). Kein eigener Tag in diesem Slice.

## Betroffene Kennungen

[`GG-FAULT-003`](../../../../spec/lastenheft.md#gg-fault-003) (MUSS, erfuellt),
Bezug [`GG-FAULT-002`](../../../../spec/lastenheft.md#gg-fault-002) (Stale Data,
Slice B), [`GG-DATA-003`](../../../../spec/lastenheft.md#gg-data-003)
(`Quality.NAN`-Darstellung),
[`GG-SAFE-004`](../../../../spec/lastenheft.md#gg-safe-004) (`max_age`-STALE-
Stage, Geschwister). Code: `core/domain/fault.py`, `core/faults/types.py`,
`core/simulation/quality_fault.py` (NEU), `core/simulation/tick_loop.py`,
`core/simulation/alarm_mappers.py`, `core/scenario/validator.py`,
`core/scenario/loader.py`, `composition/_demo_scenario_setup.py`,
`adapters/driving/http_api/_runs_action_router.py`. ADR-Bezug:
[`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md) (verbindlich),
[`ADR 0052`](../../adr/0052-max-age-stale-quality-stage.md) (Geschwister-Stage),
[`ADR 0053`](../../adr/0053-comm-failure-wrapper-missing-quality-alarm.md)
(Sentinel-/Alarm-Vertrag),
[`ADR 0025`](../../adr/0025-fault-recovery-pattern.md) (Fenster-Semantik),
[`ADR 0040`](../../adr/0040-alarm-aggregation-and-stream-port.md) (Alarm-Domain),
[`ADR 0011`](../../adr/0011-schaerfung-ohne-abloesung.md) (Schaerfung ohne
Ablösung).

## Risiken

- **Determinismus-Regression** — ausgeschlossen durch opt-in: ohne
  `nan_injection`-Fault ist der `QualityFaultRuntime` `None` → Stage no-op →
  keine Snapshot-Aenderung, Demo-Hash-Pins unberuehrt.
- **Whitelist-Kopplung** — `_KNOWN_FAULT_TYPES` doppelt genutzt (Demo-„bekannt"-
  Check + `ScenarioFaultEngine.supported_types`); Entkopplung via
  `_QUALITY_FAULT_TYPES`, damit die Engine nie ein `device.inject_fault(
  "nan_injection", …)` versucht (`FaultUnsupportedTypeError`).
- **NaN-Reject-Policy** — kein numerischer NaN in die Domaene (Sentinel `0` +
  `quality=nan`); `canonical.py` bleibt unangetastet.

---

## Closure 2026-07-11

**Integrationspunkt:** die metrik-adressierte Quality-Fault-Stage
(`_apply_quality_fault_stage`) laeuft im TickLoop-Spine auf der gesammelten
`emitted`-Liste **unmittelbar vor** dem `TickResult`-Bau — Geschwister der
[`ADR 0052`](../../adr/0052-max-age-stale-quality-stage.md)-`max_age`-STALE-Stage.
Der `TickResult`-Bau ist in `_build_tick_result` gebuendelt (Reihenfolge:
Quality-Fault-Stage → `max_age`-Stage; severity-monoton, `nan` (6) > `stale`
(3), also verhaltensneutral). **Nicht** `device.inject_fault` — das Geraet bleibt
unberuehrt.

- **C1:** [`FAULT_TYPE_NAN_INJECTION`](../../../../spec/lastenheft.md#gg-fault-003)
  in `core/domain/fault.py` (Single Source) + Re-Export `core/faults/types.py`.
  Validator: NEU `_assert_nan_injection_payload` in `_assert_fault_list`.
- **C2:** NEU `core/simulation/quality_fault.py` — `QualityFaultRuntime` haelt
  die gefilterten `nan_injection`-Faults (`fault-{i}`-IDs) + den Alarm-
  Transitions-State (`_active`, runtime-only); `apply_stage` rewritet matchende
  Punkte (`(device_id, metric)`, Fenster `[start, start+duration)`) via
  `dataclasses.replace` und liefert die Transitions-Alarms.
  `build_quality_fault_runtime` → `None` ohne `nan_injection`-Fault.
  TickLoop-Konstruktor-Kwarg `quality_fault_runtime` (via `_attach_quality_stages`
  neben `max_age_ms`) + `from_snapshot`-Symmetrie; Verdrahtung in
  `build_tick_loop`.
- **C3:** Raw `QualityFaultNanInjectionAlarm` + Mapper in
  `dispatch_alarm_mapper` (Code `quality_fault_nan_injection`, Severity
  `warning`, Message `"nan injection on metric <metric>"`); gemappt mit
  Run-Kontext (`run_id`/`simulation_time_ms`/`alarm_id_source`) im Spine.
- **C4:** `_demo_scenario_setup.py` — NEU `_QUALITY_FAULT_TYPES` +
  `_ALL_KNOWN_FAULT_TYPES` (Union fuer den „bekannt"-Check); die
  `ScenarioFaultEngine`-`supported_types` bleiben `_KNOWN_FAULT_TYPES`
  (Physik-only). HTTP-Handler: NEU `_METRIC_ADDRESSED_FAULT_TYPES` +
  Short-Circuit — der device-Typ-Match wird uebersprungen (Ziel darf jedes
  existierende Geraet sein), Target-Existenz bleibt der einzige harte Check.
- **C5:** Tests — `test_tick_loop_quality_fault_nan.py` (15),
  `test_validator_nan_injection_payload.py` (3), `test_alarm.py` (+2 Mapper),
  `test_fault_port_composition.py` (+1 Entkopplung),
  `test_runs_action_router.py` (+2 HTTP metric-addressed).
- **C6:** `traceability.md` §27.3-Zeile
  [`GG-FAULT-003`](../../../../spec/lastenheft.md#gg-fault-003) = Unit Test;
  CHANGELOG `[Unreleased]` `### Added`;
  [`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md) `Proposed
  → Accepted`; ADR-Index-Zeile + Folge-ADR-Cross-Refs (0052/0053); Roadmap-
  Nachzug (Header + §4); Self-Move nach `done/`.

**Evidence:** `make gates` gruen (2407 Unit-Tests, mypy --strict, arch-check,
ruff lint/format, coverage-gate + coverage-gate-critical, noqa, spdx,
dep-audit); `make docs-check` gruen; `make doc-trace` weiterhin 0 Waisen mit
[`GG-FAULT-003`](../../../../spec/lastenheft.md#gg-fault-003) Test-covered;
`make test-determinism` + `make test-fault` gruen. Determinismus: Demo-Szenario
nutzt kein `nan_injection` → `QualityFaultRuntime` `None` → Stage inaktiv →
byte-identisch (Abnahme-CLI-Hash-Pin unberuehrt). Runtime-Delta → Sammlung
unter `[Unreleased]` (kein Doku-only-Release).

**Review (statisch, adversarial) 2026-07-11:** Verdikt „committen" — keine
CRITICAL/HIGH/MEDIUM-Defekte. Verifiziert:
[`ADR 0074`](../../adr/0074-metric-quality-fault-stage-stale-nan.md)-Konformitaet
(§2.1–§2.7), Determinismus (`None`-Runtime returnt frueh ohne
`alarm_id_source`-Konsum → Demo-Pins byte-identisch), Whitelist-Routing
(`nan_injection` wird vom `ScenarioFaultEngine` gefiltert → nie
`device.inject_fault`, Target-Existenz bleibt harter Check), Stage-Ordering
severity-monoton. **LOW-1** (Alarm-ID-Allokation ≠ Tupel-Position bei Ticks mit
Device- **und** Quality-Alarm) vor Commit adressiert: Device-Alarms werden jetzt
zuerst gemappt, ID-Allokation folgt der Tupel-Position; fuer Szenarien ohne
Quality-Fault ID-neutral (keine ID-Konsumption → kein Pin-Impact, kein
Bestandstest beruehrt). Bewusst belassen (kein Defekt): Resume-Re-Alarm
(praezedenz-treu zu `ScenarioFaultEngine._active_faults`, produktiv unerreichbar
— kein `from_snapshot`-Aufrufer in `src/`), `duration_ms=0`/leere-Metrik
(systemisch fuer alle Fault-Typen bzw. spec-konform `str`).
