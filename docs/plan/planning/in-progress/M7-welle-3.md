# Welle 3 — M7 Safety-Closure: `GG-SAFE-003/004` (Trigger 034 + 035)

**Status:** In Progress — eroeffnet mit Welle-3-C0 (`9e266d2`;
NEU Gruppenplan + Sub-Slicing-Beschluss + NEU
[`M7-welle-3a.md`](../done/M7-welle-3a.md)). **Gruppenplan** fuer die
letzte offene M7-Substanz vor der M7-Closure: die SOLLTE-/Audit-IDs
`GG-SAFE-004` ([Trigger 034](../done/034-safe-004-max-age-stale-quality.md))
+ `GG-SAFE-003` ([Trigger 035](../open/035-safe-003-comm-failure-missing-quality.md)),
beide per M7-Welle-0-C2-Triage `Active in M7-Welle-3`.
**Sub-Slicing-Beschluss (Welle-3-D-1 = A):** Welle **3a**
(`max_age`-`STALE`-Stage, Trigger 034) + Welle **3b**
(Adapter-Comm-Failure → `MISSING` + Alarm, Trigger 035 — Slice-Doc
via 3b-C0). Pattern analog Welle-1-Sub-Slicing (1a/1b).
**Welle 3a Done 2026-06-11** ([`M7-welle-3a.md`](../done/M7-welle-3a.md);
C0 `9e266d2` + C1 `744e31e` ADR 0052 + C2 `23c614a` +
Review-Folge `5a9960a` + C3 — **`GG-SAFE-004` ✓ produktiv**,
Trigger 034 Closed, Move `done/` in der 3a-C4-Sequenz).
**Aktiver Slice: Welle 3b** (3b-C0 als naechster Schritt;
F4-Erbschaft aus dem 3a-Review: Severity-Override-Helper-Lift
nach `quality.py` in 3b-C0 mitentscheiden).
**Datum:** 2026-06-11 (Welle-3-C0 · 3a Done 2026-06-11).
**Quelle:** [`M7-mvp-completion.md §3`](M7-mvp-completion.md) +
Trigger 034/035 (M6-Welle-5a-Audit) +
[`roadmap.md §M7`](roadmap.md).

---

## 1. Context

Mit M7-Welle-2-Closure (2026-06-10) sind **alle vier
`GG-MVP-*`-Punkte produktiv**. Vor der M7-Closure verbleiben die
zwei Safety-Audit-Lücken aus dem M6-Welle-5a-Quality-Pipeline-Audit
([`docs/user/safe-001-004-quality-pipeline.md`](../../../user/safe-001-004-quality-pipeline.md)):

| ID | Lücke (Welle-5a-Audit) | Trigger | Status heute |
| --- | --- | --- | --- |
| `GG-SAFE-004` | `max_age`-`STALE`-Markierung — **Substanz fehlt komplett** (`Quality.STALE`-Enum existiert, `quality.py:24`; grep `max_age` ueber `src/grid_gym/` = null Treffer) | [034](../done/034-safe-004-max-age-stale-quality.md) | ✗ Lücke |
| `GG-SAFE-003` | Adapter-Kommunikationsausfall → `MISSING`/`STALE` + Alarm — **partial** (SmartMeter-pre-attach-`MISSING` `smart_meter/model.py:202` + Adapter-String-Read-`INVALID`; mid-flight-Verbindungsverlust-Quality + Alarm fehlen) | [035](../open/035-safe-003-comm-failure-missing-quality.md) | ⚠ partial Lücke |

**M7-Erfolgskriterium** (`M7-mvp-completion.md §2`): beide IDs
„geschlossen **oder als bewusste Carveout-Notiz verankert**" —
der Carveout-Fallback ist fuer 3b relevant (siehe §3 D-4 + R2).

### 1.1 Ist-Zustand (Code-verifiziert, Welle-3-C0-Audit)

**Trigger-034-Seite (Core):**

- `Quality.STALE` existiert (`hexagon/core/domain/quality.py:24`,
  Severity 3 in `QUALITY_SEVERITY`), hat **keinen Emitter**.
- `TelemetryPoint` traegt `simulation_time: int` (ms ab Lauf-Start)
  + `quality: Quality` (`hexagon/core/domain/telemetry.py:38-47`)
  — der Sim-Zeit-Vergleich braucht **kein** neues Domain-Feld.
- `TickLoop.tick()` sammelt `emitted_telemetry` und baut daraus
  das `TickResult` (`tick_loop.py:1172`), danach
  `_persist_emitted_telemetry` (`tick_loop.py:1197`) — die
  natuerliche Stage-Naht liegt **vor** dem `TickResult`-Bau
  (eine Stelle, wirkt auf Stream + Persistenz + Replay identisch).
- Kein `max_age`-Konfigurationsfeld in `ScenarioSimulation`
  (`tick_ms`/`duration_s`/`seed`, `scenario.py:52-54`) oder
  `ScenarioDevice`.

**Trigger-035-Seite (Adapter):**

- Alle fuenf Protocol-Adapter (`protocol_mqtt`/`_modbus`/`_opcua`/
  `_dnp3`/`_iec61850`) implementieren `DeviceProtocolPort`
  (`hexagon/ports/driven/device_protocol.py:43`; `start`/`stop`/
  `read`/`write`) mit typisierter Error-Hierarchie
  (`DeviceProtocolPortError`-Wurzel, `device_protocol.py:149`).
- **Kein Adapter emittiert `MISSING`/`STALE`** bei
  Verbindungsverlust — Read-Fehler werfen typisierte Exceptions
  (z. B. `Iec61850PortReadConnectionLostError` fuer mid-flight-
  Session-Drop, `protocol_iec61850/_port.py:265` — die
  **Erkennungs**-Substanz existiert dort bereits, die
  **Quality-/Alarm-Folge** fehlt).
- **Kein produktiver `read()`-Pfad:** der `TickLoop` haelt
  `protocol_ports` nur fuer `start_protocol_ports()`/
  `stop_protocol_ports()` (Lifecycle, `tick_loop.py:900/954`);
  `read()` wird ausschliesslich von Test-Siblings aufgerufen.
  Das Demo-Wiring uebergibt keine `protocol_ports`
  (`_demo_setup.py:152-159`).
- **Alarm-Emission laeuft heute ausschliesslich Device-seitig:**
  `TickResult.emitted_alarms` → `DemoTickLoopDriver.
  _publish_emitted_alarms()` (`_tick_loop_driver.py:269-290`) →
  `AlarmStreamPort.publish()` (ADR 0040). Es gibt **keinen**
  Adapter-seitigen Alarm-Pfad; Alarm-Codes heute:
  `power_clamp_limited`/`command_rejected`/`smart_meter_rejected`
  (`alarm_mappers.py`).
- Composition-Wrapper-Praezedenz: `OtelSpanWrappedDeviceProtocolPort`
  (`adapters/driven/_protocol_otel_wrap.py:145`) wrappt alle fuenf
  Adapter einheitlich — Vorbild fuer einen Comm-Failure-Wrapper.

**Skipped Smokes** (M6-Welle-5a, `tests/integration/test_m6_welle_
5a_safe_001_004_smoke.py`): `test_safe_004_stale_data_quality_
after_max_age` (Trigger 034) + `test_safe_003_comm_failure_emits_
missing_or_stale` (Trigger 035) — werden in 3a-C2 bzw. 3b-C2
reaktiviert.

---

## 2. Lieferziel (Gruppen-Ebene)

1. **Welle 3a** (Trigger 034): NEU `max_age`-Konfiguration +
   Core-`STALE`-Stage im `TickLoop` + Smoke-Reaktivierung +
   Audit-Doku-Flip `GG-SAFE-004` ✗ → ✓. Slice-Doc
   [`M7-welle-3a.md`](../done/M7-welle-3a.md) (dieser Commit).
2. **Welle 3b** (Trigger 035): Adapter-Comm-Failure-Quality
   (`MISSING`) + Alarm-Emission (`adapter_communication_lost`) +
   Smoke-Reaktivierung + Audit-Doku-Flip `GG-SAFE-003` ⚠ → ✓
   (oder bewusste Carveout-Notiz, siehe D-4/R2). Slice-Doc via
   3b-C0.
3. **Welle-3-Closure**: beide Trigger → `done/`; danach ist
   M7-Welle-X (M7-Closure) der letzte Slice.

**Anti-Scope (Welle 3 NICHT):** SOLLTE-Geraete-Trigger 016..024;
`GG-DEPLOY-007..010` (Trigger 037); OTel-CVE-Watch (Trigger 033);
produktive Protocol-Adapter-Demo-Aktivierung (es gibt keinen
produktiven `read()`-Pfad — siehe §1.1; dessen Etablierung ist
eigener Scope ausserhalb der SAFE-003-Akzeptanz).

---

## 3. Architektur-Entscheidungen (Welle-3)

### Welle-3-D-1 — Sub-Slicing-Beschluss

**Final: A — Sub-Wellen 3a + 3b** (Pattern Welle-1 → 1a/1b).

- **A**: 3a (Trigger 034, Core-Quality-Stage) + 3b (Trigger 035,
  Adapter-Familie + Alarm-Vertrag) mit eigenen Slice-Docs +
  eigenen C0..C4-Sequenzen.
- **B**: Monolithische Welle 3 mit C2a/C2b.

**Begruendung:** die zwei Trigger beruehren **disjunkte
Code-Regionen** (Core-`TickLoop`-Spine vs. fuenf Protocol-Adapter
+ Alarm-Vertrag), haben **getrennte Flips** (je eigener
Doku-/Trigger-Close) und ungleiches Risiko: 3a ist klein + voll
schliessbar, 3b traegt den Scope-/Carveout-Entscheid (D-4). Die
Sub-Slicing-Schwelle (`M7-mvp-completion.md §1`: > 2 unabhaengige
Sub-Bereiche ODER > 300 Zeilen Slice-Doc) wuerde mit einem
Monolith-Doc (zwei volle Decision-Saetze) gerissen.

### Welle-3-D-2 — Reihenfolge

**Final: 3a zuerst.** 3a ist Core-only, ohne offene
Scope-Fragen, ~1-1.5 Tage; 3b braucht den D-4-Scope-Entscheid in
3b-C0. Keine Daten-Abhaengigkeit zwischen 3a und 3b.

### Welle-3-D-3 — ADR-Bedarf (Vorbelegung)

- **3a → NEU ADR 0052 `Provisional`** (max_age-`STALE`-Stage:
  Konfigurations-Surface + Stage-Naht + Severity-Override-Regel) —
  Core-Quality-Pipeline-Semantik ist Architektur-Vertrag
  (Praezedenz: ADR 0047..0049, je ein ADR pro Welle-1-Sub-Slice).
  Finalisiert in 3a-C1.
- **3b → ADR-Nummer 0053 reserviert** (Comm-Failure-Wrapper +
  Adapter-Alarm-Vertrag); Bedarf final in 3b-C0.

### Welle-3-D-4 — 3b-Akzeptanz-Lesart (Scope-Schalter; final in 3b-C0)

`GG-SAFE-003` verlangt Quality-Markierung + Alarm bei
Kommunikationsausfall. **Befund §1.1:** es gibt keinen produktiven
Adapter-`read()`-Pfad — die Akzeptanz kann nur an der
**Adapter-Substanz** (Wrapper/Lifecycle-Hook + Test-Sibling-E2E)
belegt werden, nicht an einem Demo-Lauf. **Vorbelegung:**
Composition-Wrapper analog `_protocol_otel_wrap.py` (ein Wrapper
fuer alle fuenf Adapter; mappt `DeviceProtocolPortReadError`-
Subklassen → `Quality.MISSING`-Point + `Alarm(code="adapter_
communication_lost", target=<device_id>, simulation_time_ms=
<Startzeit>, message=<Ursache>)`). Falls 3b-C0 den vollen Umfang
als nicht-ehrlich-belegbar einstuft, greift der M7-
Erfolgskriteriums-Fallback („bewusste Carveout-Notiz") mit
explizitem Rest-Trigger.

---

## 4. Sub-Scope (Wellen-Vorbelegung)

- **3a** — **Done 2026-06-11** ([`M7-welle-3a.md`](../done/M7-welle-3a.md)):
  NEU `TickLoop`-Kwarg `max_age_ms` (+ `from_snapshot`-Resume-
  Symmetrie per Review-Folge F1) + Core-Stage + ADR 0052 +
  Unit-Boundary-Tests + Smoke-Reaktivierung + Doku-Flip;
  `GG-SAFE-004` ✓ produktiv; Trigger 034 Closed (→ `done/` in
  3a-C4a).
- **3b** — Slice-Doc via 3b-C0 (~2-3 Tage): Comm-Failure-Wrapper
  + Alarm-Vertrag + per-Adapter-Familie-Smokes +
  Smoke-Reaktivierung + Doku-Flip + Trigger 035 → `done/`
  (oder D-4-Carveout-Pfad). 3b-C0-Erbschaft: F4-Entscheid
  (Severity-Override-Helper-Lift nach `quality.py`, falls 3b
  die Regel braucht).

---

## 5. Risiken

- **R1 (3a) Hash-Pin-Kopplung.** Ein `max_age`-Feld in
  `ScenarioSimulation` wuerde `scenario_hash` fuer **alle**
  Szenarien flippen (`asdict(scenario)`-Hash, `loader.py`) und
  damit `EXPECTED_DEMO_SCENARIO_HASH` + Welle-2-Pins brechen.
  Mitigation: 3a-D-1 waehlt den `TickLoop`-Kwarg-Standort —
  kein Scenario-Schema-Touch, keine Pin-Drift
  (`tools/check_demo_scenario_pin.py` belegt das im CI).
- **R2 (3b) Scope-Ehrlichkeit.** Ohne produktiven `read()`-Pfad
  koennte ein Reviewer den `GG-SAFE-003`-Flip als zu schwach
  lesen. Mitigation: D-4-Lesart explizit in 3b-C0/ADR
  dokumentieren; Fallback Carveout-Notiz ist per M7-
  Erfolgskriterium legitim.
- **R3 (3b) Alarm-Kontext im Driven-Ring.** `Alarm` braucht
  `run_id` + `simulation_time_ms`; Adapter haben heute keinen
  Lauf-Kontext. Mitigation: Kontext-Provider im Wrapper
  (3b-C0-Decision); Praezedenz: Late-Binding-Provider des
  Alarm-Publishing-Pfads (`_demo_setup.py:176`).

---

## 6. Wandert nach

`M7-welle-3.md` bleibt in `in-progress/` bis zur 3b-Closure
(analog `M7-welle-1.md`-Gruppenplan); dann Self-Close-Move →
`done/` in der 3b-C4-Sequenz, zusammen mit dem letzten
Sub-Slice-Doc.

---

## 7. Verifikationspfad

- Pro Sub-Welle: `make gates` + `make fullbuild` +
  `make docs-check` cache-frei gruen; Smoke-Reaktivierung
  (3a: `test_safe_004_*`; 3b: `test_safe_003_comm_failure_*`).
- Welle-3-Closure: beide Zeilen in
  `docs/user/safe-001-004-quality-pipeline.md` auf ✓ (oder
  dokumentierter Carveout-Rest), Trigger 034/035 → `done/`.

---

## References

- [`M7-mvp-completion.md`](M7-mvp-completion.md) — M7-Meilenstein-
  Slice-Plan (§2 Erfolgskriterien, §3 Welle-Tabelle).
- [`M7-welle-3a.md`](../done/M7-welle-3a.md) — Sub-Slice 3a (Trigger 034).
- [Trigger 034](../done/034-safe-004-max-age-stale-quality.md) +
  [Trigger 035](../open/035-safe-003-comm-failure-missing-quality.md)
  — Lücken-Verankerung (M6-Welle-5a-Audit).
- [`../../../user/safe-001-004-quality-pipeline.md`](../../../user/safe-001-004-quality-pipeline.md)
  — Audit-Tabelle (Flip-Ziel).
- [`../done/M6-welle-5a.md`](../done/M6-welle-5a.md) — Quality-
  Pipeline-Audit-Quelle.
- [`../../adr/0024-observability-port-trio.md`](../../adr/0024-observability-port-trio.md)
  + [`../../adr/0040-alarm-aggregation-and-stream-port.md`](../../adr/0040-alarm-aggregation-and-stream-port.md)
  — Alarm-/Observability-Vertraege (3b-Vorbild).
- [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md)
  §20 (`GG-SAFE-003` Z. 1365-1371 + `GG-SAFE-004` Z. 1373-1378).
