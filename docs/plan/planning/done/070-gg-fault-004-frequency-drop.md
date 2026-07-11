# 070 — Dedizierter `frequency_drop`-Fault (Frequenzabfaelle)

**Status:** Done — 2026-07-11
**Datum:** 2026-07-11
**Quelle:** Konsolidierungs-Befund — `make doc-trace` meldet 0 Waisen, aber
[`GG-FAULT-004`](../../../../spec/lastenheft.md#gg-fault-004) „Frequenzabfaelle"
(MUSS) hatte **keinen** dedizierten Fault-Injection-Typ. `grid_fault_engine`
kannte nur `voltage_drop` ([`GG-FAULT-005`](../../../../spec/lastenheft.md#gg-fault-005)).
Owner-Entscheidung: dedizierten `frequency_drop`-Typ implementieren (Komposition
ist **nicht** akzeptabel).

---

## Kontext / Befund

[`GG-FAULT-004`](../../../../spec/lastenheft.md#gg-fault-004)-Akzeptanz: „Ein
Frequenzabfall kann mit Startzeit, Dauer, Zielnetz, Frequenzwert oder Delta und
Recovery-Verhalten definiert werden und erzeugt Grid-Telemetrie sowie einen
Alarm." Das ist der **Frequenz-Zwilling** von
[`GG-FAULT-005`](../../../../spec/lastenheft.md#gg-fault-005) (Spannungseinbrueche,
wortgleiche Akzeptanz fuer die Spannung). Der bestehende `voltage_drop`-Fault
deckt [`GG-FAULT-005`](../../../../spec/lastenheft.md#gg-fault-005) ab und wirkt auf
das `grid_connection`-Geraet (Zielnetz = Netzanschlusspunkt).

**Integrationspunkt-Analyse (aufgeloest):** Frequenz ist zwar eine
grid-MODELL-Groesse ([`GG-GRID-001`](../../../../spec/lastenheft.md#gg-grid-001):
`nominal_frequency_hz` in `grid_model/`), aber das `GridModelBilanz` ist **kein
DeviceModel** (kein `device_id`, nicht in der Device-Iteration des Fault-Engines,
Frequenz wird jeden Tick aus `imbalance_kw` **neu berechnet**). Damit ist es kein
sauberes Ziel fuer den geraete-adressierenden `ScenarioFaultEngine`. Der
`FaultPort`-Vertrag sieht das explizit vor: „Grid-Faults muessen Voltage-/
Frequency-State mutieren." Der `frequency_drop` spiegelt daher `voltage_drop` und
wirkt auf das `grid_connection`-Geraet (die `test_fault_injection.py` fuehrt schon
`frequency_drop_active` als „Welle-3-Forward-Compat"-Snapshot-Key). Das Geraet
meldet einen `frequency_hz`-Telemetriewert und hebt einen Alarm.

**Determinismus:** alle Erweiterungen sind **opt-in** — Frequenz-Telemetrie wird
nur bei aktivem Fault emittiert (Muster `reactive_power_kvar`), Snapshot-Frequenz-
Keys nur bei aktivem Fault serialisiert, `frequency_drop_active` nur bei `True` im
`fault_state`. Szenarien ohne `frequency_drop` bleiben byte-identisch (Demo-Hash-
Pins unberuehrt).

## Tranchen

- **C1 — Konstante:** `FAULT_TYPE_FREQUENCY_DROP = "frequency_drop"` als Single
  Source in `core/domain/fault.py`; Re-Export in `core/faults/types.py`.
- **C2 — Engine:** `GridFaultEngine.supported_types` um `FAULT_TYPE_FREQUENCY_DROP`
  erweitern; `_KNOWN_FAULT_TYPES` (produktiver `ScenarioFaultEngine`) +
  HTTP-Whitelist `_FAULT_TYPE_TO_DEVICE_TYPE` (`frequency_drop → grid_connection`).
- **C3 — Physik:** `GridConnectionDevice.inject_fault`/`clear_fault` fuer
  `frequency_drop` — Payload `frequency_hz` (Absolutwert) **oder** `delta_hz`
  (Abzug von Nominal 50 Hz), Default-Delta 1 Hz; `_pending_frequency_hz`-Mutation
  (KEIN Power-Mutate, GridConnection-Constraint); `tick()` committed +
  `_emit_telemetry` emittiert opt-in `frequency_hz`; Snapshot-Roundtrip.
- **C4 — Alarm:** `GridConnectionFaultAlarm` (Raw) + Mapper
  `alarm_from_grid_connection_fault_alarm` (Code `grid_fault_frequency_drop`,
  Severity `warning`) in `dispatch_alarm_mapper` registriert; `inject_fault` hebt
  den Alarm ueber die bestehende `drain_alarms`-Pipeline.
- **C5 — Tests:** Unit (Device inject/clear/telemetry/alarm/snapshot/constraint/
  unknown-type), Engine (Window/Recovery), Alarm-Mapper.
- **C6 — Traceability + Closure:** `traceability.md` §27.3-Zeile
  [`GG-FAULT-004`](../../../../spec/lastenheft.md#gg-fault-004);
  CHANGELOG `[Unreleased]`; Slice → `done/`; Roadmap-Nachzug.

## DoD

- [x] `frequency_drop` als dedizierter Fault-Typ (kein Composite); Device droppt
      Frequenz auf Payload-Wert/Delta, Recovery auf Nominal via `clear_fault`.
- [x] Grid-Telemetrie `frequency_hz` (opt-in) + Alarm (`grid_fault_frequency_drop`).
- [x] Determinismus: Szenarien ohne `frequency_drop` byte-identisch (opt-in
      Telemetrie/Snapshot/Alarm).
- [x] `make test-unit`, `make gates`, `make docs-check` gruen; `make doc-trace`
      zeigt [`GG-FAULT-004`](../../../../spec/lastenheft.md#gg-fault-004) abgedeckt.
- [x] [`GG-FAULT-004`](../../../../spec/lastenheft.md#gg-fault-004) in
      `traceability.md` §27.3; CHANGELOG `[Unreleased]`.

**Release-Entscheidung:** ja-Kandidat, aber gebuendelt unter `[Unreleased]` bis
zum naechsten Release-Schnitt (Runtime-Delta vorhanden; SemVer-Ziel Minor —
additives Feature). Kein eigener Tag in diesem Slice.

## Betroffene Kennungen

[`GG-FAULT-004`](../../../../spec/lastenheft.md#gg-fault-004) (MUSS, erfuellt),
Bezug [`GG-FAULT-005`](../../../../spec/lastenheft.md#gg-fault-005) (voltage_drop-
Spiegel), [`GG-FAULT-010`](../../../../spec/lastenheft.md#gg-fault-010)
(deterministischer Fault-Replay), [`GG-GRID-001`](../../../../spec/lastenheft.md#gg-grid-001)
(Frequenz-Groesse). Code: `core/domain/fault.py`, `core/faults/types.py`,
`core/faults/grid_fault_engine.py`, `core/devices/grid_connection/{model,commands,
snapshot,config}.py`, `core/simulation/alarm_mappers.py`,
`composition/_demo_scenario_setup.py`, `adapters/driving/http_api/_runs_action_router.py`.
ADR-Bezug: [`ADR 0022`](../../adr/0022-fault-injection-protocol.md) /
[`ADR 0025`](../../adr/0025-fault-recovery-pattern.md) (Fault-Recovery),
[`ADR 0059`](../../adr/0059-generic-scenario-fault-engine.md) (generische
Engine).

## Risiken

- **Determinismus-Regression** — ausgeschlossen durch opt-in-Emission (Telemetrie/
  Snapshot/Alarm nur bei aktivem Fault); Demo-Szenario nutzt kein `frequency_drop`.
- **Alarm-Schema-Drift** — neuer Raw-Alarm-Typ `GridConnectionFaultAlarm` mit
  eigenem Mapper (kein Missbrauch des Power-Clamp-`GridConnectionAlarm`).
- **Coverage-Gate** — neue Branches (Payload-Resolution, opt-in-Pfade) mit gezielten
  Unit-Tests abgedeckt.

---

## Closure 2026-07-11

**Integrationspunkt:** `frequency_drop` wirkt (wie `voltage_drop`) auf das
`grid_connection`-Geraet — nicht auf `GridModelBilanz` (kein DeviceModel, Frequenz
jeden Tick neu berechnet, kein Fault-Ziel des geraete-adressierenden Engines).

- **C1/C2:** [`FAULT_TYPE_FREQUENCY_DROP`](../../../../spec/lastenheft.md#gg-fault-004)
  in `core/domain/fault.py` (Single Source) + Re-Export `core/faults/types.py`.
  `GridFaultEngine.supported_types` = `{voltage_drop, frequency_drop}`; produktiver
  `ScenarioFaultEngine` (`_KNOWN_FAULT_TYPES`) + HTTP-Whitelist
  (`frequency_drop → grid_connection`) ergaenzt.
- **C3:** `GridConnectionDevice.inject_fault`/`clear_fault` mit
  `_frequency_drop_active`/`_pending_frequency_hz`/`_current_frequency_hz`;
  Payload-Resolver `_resolve_frequency_target` (`frequency_hz` > `delta_hz` >
  Default 1 Hz unter Nennwert 50 Hz); `tick()` committed + opt-in
  `frequency_hz`-Telemetrie (alphabetisch zwischen `export_kwh`/`import_kwh`);
  Snapshot opt-in (`current/pending_frequency_hz` + `fault_state.
  frequency_drop_active`) — kein Versions-Bump; `__eq__`/`__hash__` erweitert. Kein
  `_pending_power_kw`-Mutate ([`ADR 0022`](../../adr/0022-fault-injection-protocol.md) §2.4).
- **C4:** Raw `GridConnectionFaultAlarm` + Mapper
  `alarm_from_grid_connection_fault_alarm` (Code `grid_fault_frequency_drop`,
  Severity `warning`) in `dispatch_alarm_mapper`; `inject_fault` hebt den Alarm
  ueber die `drain_alarms`-Pipeline (End-to-End im TickLoop verifiziert).
- **C5:** Tests — `test_fault_injection.py` (14 neue: inject-Default/Value/Delta/
  Praezedenz, Alarm, Recovery, Idempotenz, Telemetrie opt-in/aus, Power-Constraint,
  Koexistenz mit voltage_drop, Snapshot-Roundtrip mit/ohne Fault),
  `test_grid_fault_engine.py` (Window-Aktivierung + Auto-Recovery),
  `test_tick_loop_alarm_aggregation.py` (End-to-End: emitted_alarms +
  frequency_hz-Telemetrie + Idempotenz).
- **C6:** `traceability.md` §27.3-Zeile
  [`GG-FAULT-004`](../../../../spec/lastenheft.md#gg-fault-004) = Unit Test;
  CHANGELOG `[Unreleased]` `### Added`; Roadmap-Nachzug (Header + §4); Self-Move
  nach `done/`.

**Evidence:** `make gates` gruen (2384 Unit-Tests, mypy --strict, arch-check,
ruff, coverage, noqa, spdx, dep-audit); `make docs-check` gruen; `make doc-trace`
weiterhin 0 Waisen mit [`GG-FAULT-004`](../../../../spec/lastenheft.md#gg-fault-004)
Test-covered. Determinismus: Demo-Szenario nutzt kein `frequency_drop` → opt-in-
Pfade inaktiv → byte-identisch (Abnahme-CLI-Hash-Pin unberuehrt). Runtime-Delta →
Sammlung unter `[Unreleased]` (kein Doku-only-Release).
