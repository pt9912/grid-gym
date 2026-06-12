# Welle 3a — M7 Safety-Closure: `max_age`-basierte `STALE`-Quality-Stage (`GG-SAFE-004`)

**Status:** Done — C0 `9e266d2` (Gruppenplan + Slice-Doc +
Decision-Liste 3a-D-1..D-5) + C1 `744e31e` (NEU ADR 0052
`Provisional`) + C2 `23c614a` (Code: `max_age_ms`-Kwarg +
`_apply_max_age_stage` + `TickLoopInvalidMaxAgeMsError` +
`build_tick_loop`-Symmetrie + 7 Unit-Tests + Smoke-Reaktivierung
+ Doku-Flip) + C2-Review-Folge `5a9960a` (F1 `from_snapshot`-
Resume-Symmetrie + F2 ADR-Bilanz-Note + F3 Shared-Fake; F4
zurueckgestellt → 3b-C0) + C3 (DoD §9 abgehakt, **`GG-SAFE-004`
✓ produktiv**, Trigger 034 → Closed; dieser Commit). **Offen:
C4a/C4b** (Self-Close-Move `M7-welle-3a.md` + Trigger 034 →
`done/` + Refs-Sync). Code + Gates (`gates`/`test-integration`
138 passed / 5 skipped/`fullbuild` inkl. `accept-pin-check`/
`docs-check`) cache-frei gruen 2026-06-11.

Erstes Sub-Slice von **M7-Welle-3** (Safety-Closure;
Gruppenplan [`M7-welle-3.md`](M7-welle-3.md)): schliesst die
`GG-SAFE-004`-Lücke
([Trigger 034](034-safe-004-max-age-stale-quality.md),
M6-Welle-5a-Audit ✗). **Monolithisch** (ein Code-Commit C2): die
Teile (Kwarg + Stage + Tests + Doku-Flip) sind klein und eng
gekoppelt. **Datum:** 2026-06-11 (Welle-3-C0 · Done 2026-06-11 C3).
**Quelle:** [Trigger 034](034-safe-004-max-age-stale-quality.md)
+ Lastenheft §20 Z. 1373-1378 +
[`M7-welle-3.md`](M7-welle-3.md).

Liefer-Reihenfolge C0 → C1 (NEU ADR 0052 `Provisional`) → C2
(Code) → C3 (Status/DoD-Sync + Flip) → C4a/C4b (Self-Close-Move).

---

## 1. Context

**Lastenheft-Akzeptanz (Z. 1373-1378, `GG-SAFE-004` MUSS):**

> Veraltete Daten MUESSEN markiert werden.
>
> Akzeptanz: Werte, deren Simulationszeitstempel die
> konfigurierte `max_age` ueberschreiten, erhalten
> deterministisch den Qualitaetsstatus `stale`.

### 1.1 Ist-Zustand (Code-verifiziert, Welle-3-C0-Audit)

- **`Quality.STALE` existiert ohne Emitter**
  (`hexagon/core/domain/quality.py:24`; Severity 3 im
  `QUALITY_SEVERITY`-Ranking `quality.py:33-42`).
- **`TelemetryPoint` traegt bereits beide Vergleichsgroessen:**
  `simulation_time: int` (ms ab Lauf-Start) + `quality: Quality`
  (`hexagon/core/domain/telemetry.py:38-47`, frozen + slots).
  Kein neues Domain-Feld noetig; Quality-Austausch via
  `dataclasses.replace`.
- **Stage-Naht:** `TickLoop.tick()` sammelt `emitted` ueber die
  Device-Iterationen und baut daraus das `TickResult`
  (`tick_loop.py:1168-1175`, `emitted_telemetry=tuple(emitted)`);
  direkt danach `_persist_emitted_telemetry(result)`
  (`tick_loop.py:1176`). Eine Pruefung **vor** dem
  `TickResult`-Bau wirkt damit identisch auf Live-Stream,
  Persistenz (`TelemetrySinkPort`) und Replay-Pfad
  (`ReplaySnapshotPort` rekonstruiert aus `telemetry_points`) —
  genau eine Stelle, kein Drift.
- **Keine `max_age`-Konfiguration:** `ScenarioSimulation` kennt
  `tick_ms`/`duration_s`/`seed` (`scenario.py:52-54`);
  `ScenarioDevice.params` ist devicetyp-spezifisch; grep
  `max_age` ueber `src/grid_gym/` = null Treffer.
- **Kwarg-Praezedenz:** `TickLoop` nimmt optionale keyword-only
  Ports/Konfiguration (`telemetry_sink`, `protocol_ports`,
  `replay_snapshot`/`replay_reference_run_id` aus 1b-b) mit
  `None`-Default = Feature aus; `build_tick_loop`
  (`loader.py:402`) reicht sie symmetrisch durch.
- **Skipped Smoke:** `test_safe_004_stale_data_quality_after_
  max_age` (`tests/integration/test_m6_welle_5a_safe_001_004_
  smoke.py:155-170`, `pytest.skip` mit Trigger-034-Pointer) —
  wird in 3a-C2 reaktiviert.
- **Hash-Pin-Kopplung (Welle-2-Erbschaft):** `scenario_hash` =
  `sha256(canonical_json(asdict(scenario)))` — **jedes** neue
  `Scenario`-Dataclass-Feld flippt den Hash aller Szenarien und
  damit `EXPECTED_DEMO_SCENARIO_HASH` +
  `EXPECTED_DEMO_TELEMETRY_STREAM_HASH`
  (`tools/check_demo_scenario_pin.py`, `make ci`-Gate).

---

## 2. Lieferziel (Welle-3a-C2)

1. **NEU keyword-only `TickLoop`-Konstruktor-Kwarg
   `max_age_ms: int | None = None`** (`None` → Stage aus,
   no-op; 3a-D-1). Validierung: `max_age_ms <= 0` →
   typisierter Fehler beim Konstruktor (kein stiller Unsinn).
2. **NEU Core-`STALE`-Stage in `tick()`**: unmittelbar vor dem
   `TickResult`-Bau prueft die Stage jeden gesammelten
   `TelemetryPoint`: `(now - point.simulation_time) >
   max_age_ms` → Point wird via `dataclasses.replace(point,
   quality=Quality.STALE)` ersetzt (3a-D-2). Nur Sim-Zeit
   (`now` = aktuelle `simulation_time` des Ticks), **kein
   Wall-Clock** — `AC-NO-TIME` bleibt gewahrt (3a-D-4).
   Grenzwert: `== max_age_ms` ist **nicht** ueberschritten →
   bleibt unmarkiert (3a-D-5).
3. **Severity-Override-Regel:** `STALE` ersetzt nur Qualities
   mit **niedrigerer** Severity (`VALID`=0/`ESTIMATED`=1/
   `LIMITED`=2); Qualities mit hoeherer Severity
   (`FAULT_INJECTED`=4/`INVALID`=5/`NAN`=6/`MISSING`=7)
   bleiben unangetastet (3a-D-3 — kein Informationsverlust
   ueber schwerere Befunde).
4. **`build_tick_loop`-Symmetrie** (`loader.py:402`): NEU
   keyword-only `max_age_ms: int | None = None` durchgereicht
   (Praezedenz `replay_snapshot`-Kwargs aus 1b-b).
5. **NEU Unit-Tests** (`tests/unit/hexagon/core/simulation/
   test_tick_loop_welle_3a_max_age.py`, Namens-Konvention der
   Siblings): Boundary (`> max_age` stale / `== max_age` nicht /
   frische Punkte nicht), Severity-Override (niedrig → ersetzt,
   hoch → unangetastet), `None`-Default = no-op,
   `max_age_ms <= 0`-Reject, Determinismus (zwei identische
   Laeufe mit `max_age_ms` → identische Streams).
6. **Smoke-Reaktivierung:** `test_safe_004_stale_data_quality_
   after_max_age` (Skip-Marker raus): End-to-End ueber einen
   `TickLoop` mit `max_age_ms` + einem Test-Device, das einen
   Point mit nachlaufendem `simulation_time` emittiert →
   `Quality.STALE` im `TickResult.emitted_telemetry`.
7. **Doku-Flip** `docs/user/safe-001-004-quality-pipeline.md`:
   `GG-SAFE-004`-Zeile ✗ Lücke → ✓ produktiv (Substanz- +
   Test-Pfad-Spalten aktualisiert; Detail-Sektion + Quality-
   Enum-Referenz nachgezogen).
8. **NEU ADR 0052 `Provisional`** (C1): Konfigurations-Surface
   (Kwarg statt Scenario-Schema), Stage-Naht, Severity-Override,
   Grenzwert-Semantik, `AC-NO-TIME`-Garantie.
9. **C3:** Trigger 034 → Closed (Move `done/` in C4a);
   carveouts-Zeile; roadmap-/Gruppenplan-Sync; DoD §9.

**Anti-Scope (3a NICHT):** `max_age`-Feld im Scenario-Schema
(3a-D-1-Folgeoption, siehe unten); per-Device-/per-Metric-
Granularitaet; Demo-Wiring-Aktivierung mit konkreter Schwelle
(3a-D-4); Alarm-Emission bei `STALE` (Lastenheft verlangt fuer
SAFE-004 nur die Markierung; Alarm ist SAFE-003-Substanz →
Welle 3b); Comm-Failure-Pfade (Trigger 035 → 3b).

---

## 3. Architektur-Entscheidungen (Welle-3a)

### 3a-D-1 — Konfigurations-Standort

**Frage:** Wo lebt die `max_age`-Schwelle? (Trigger 034 nennt
`ScenarioDevice.params` ODER `TickLoop`-Konstruktor-Argument
ODER per-Geraet/per-Metric.)

**Final: B — NEU keyword-only `TickLoop`-Konstruktor-Kwarg
`max_age_ms: int | None = None`** + `build_tick_loop`-Symmetrie.

- **A — `ScenarioSimulation`/`ScenarioDevice`-Feld:** flippt
  `scenario_hash` fuer **alle** Szenarien (`asdict`-Hash) →
  bricht `EXPECTED_DEMO_SCENARIO_HASH` +
  `EXPECTED_DEMO_TELEMETRY_STREAM_HASH` + erzwingt
  Pin-Updates + beruehrt den `GG-TERM`-Preflight-Vergleich
  alt-persistierter Laeufe. Schema-Touch fuer eine SOLLTE-
  Schwelle ohne existierende Stakeholder-Anforderung ist
  unverhaeltnismaessig.
- **B — `TickLoop`-Kwarg:** minimaler Eingriff; exakte
  Praezedenz der 1b-b-Replay-Kwargs (`None` = Feature aus);
  kein Schema-/Hash-Touch; „konfigurierte `max_age`" der
  Akzeptanz ist erfuellt (Konstruktor-Konfiguration ist
  Konfiguration — das Lastenheft verlangt keinen
  Szenario-Datei-Standort).
- **C — per-Geraet/per-Metric:** Over-Engineering ohne
  Anforderung; jederzeit additive Schaerfung.

**Folgeoption (dokumentiert, kein Trigger):** sobald eine
konkrete Stakeholder-Schwelle existiert, ist ein optionales
Scenario-Schema-Feld eine additive ADR-0011-Schaerfung — dann
mit bewusstem Pin-Update im selben PR (Lint erzwingt das).

### 3a-D-2 — Stage-Naht

**Final: in `tick()` unmittelbar vor dem `TickResult`-Bau**
(`tick_loop.py:1168`), auf der gesammelten `emitted`-Liste.

- Wirkt **einmal** und identisch auf Stream + Persistenz +
  Replay (beide konsumieren `TickResult.emitted_telemetry` bzw.
  dessen Persistenz-Projektion) — keine zweite Pruefstelle,
  kein Drift-Risiko.
- **NICHT** Device-seitig (jedes Device muesste die Schwelle
  kennen — N Pruefstellen) und **NICHT** Sink-/Adapter-seitig
  (Replay-/Stream-Pfad bliebe unmarkiert; Core-Semantik
  gehoert in den Spine, GG-AR-P-003).

### 3a-D-3 — Severity-Override-Regel

**Final: `STALE` ersetzt nur niedrigere Severities** (`VALID`/
`ESTIMATED`/`LIMITED`, Severity 0..2); `FAULT_INJECTED`/
`INVALID`/`NAN`/`MISSING` (Severity 4..7) bleiben. Nutzt das
existierende `QUALITY_SEVERITY`-Ranking (`quality.py:33-42`) —
deterministisch, kein Informationsverlust: ein als `INVALID`
erkannter Wert bleibt `INVALID`, auch wenn er zusaetzlich alt
ist (der schwerere Befund dominiert).

### 3a-D-4 — Demo-Wiring

**Final: Demo bleibt `max_age_ms=None`** (Stage im Demo-Pfad
aus). Begruendung: es existiert **keine** konkrete Stakeholder-
Schwelle (Trigger-034-Aktivierung erfolgte per Maintainer-
Entscheidung, nicht per Compliance-Druck mit Wert); eine
erfundene Demo-Schwelle waere Schein-Konfiguration, die nie
feuert (alle Demo-Devices emittieren frische Punkte, Alter 0).
Der Akzeptanz-Beleg ist der reaktivierte Smoke + Unit-Boundary-
Tests. Demo-Aktivierung ist ein Einzeiler, sobald eine Schwelle
gefordert wird. Zugleich garantiert das: **kein** Verhaltens-
oder Stream-Hash-Delta im produktiven Demo-/Abnahme-Pfad
(`make accept`-Pins unberuehrt).

### 3a-D-5 — Grenzwert-Semantik

**Final: strikt `>`** — `(now - point.simulation_time) >
max_age_ms` markiert; Gleichheit (`== max_age_ms`) ist nicht
„ueberschritten" (Lastenheft-Wortlaut) und bleibt unmarkiert.
Unit-Test pinnt die Grenze beidseitig.

---

## 4. Liefer-Reihenfolge

- **C0** (dieser Commit) — Gruppenplan
  [`M7-welle-3.md`](M7-welle-3.md) + dieses Slice-Doc +
  Decision-Liste 3a-D-1..D-5 + Refs-Sync.
- **C1** — NEU ADR 0052 `Provisional` (max_age-`STALE`-Stage).
- **C2** — Code: Kwarg + Stage + `build_tick_loop`-Symmetrie +
  Unit-Tests + Smoke-Reaktivierung + Doku-Flip.
- **C3** — Status/DoD-Sync + `GG-SAFE-004`-Flip + Trigger 034 →
  Closed.
- **C4a/C4b** — Self-Close-Move `M7-welle-3a.md → done/` +
  Trigger 034 → `done/` + Refs-Sync. Gruppenplan bleibt in
  `in-progress/` (3b offen).

---

## 5. Critical Files

**NEU (C0/C1/C2):** `M7-welle-3.md` + `M7-welle-3a.md` (C0);
`docs/plan/adr/0052-max-age-stale-quality-stage.md` (C1);
`tests/unit/hexagon/core/simulation/test_tick_loop_welle_3a_max_age.py`
(C2).
**MODIFY (C2):** `src/grid_gym/hexagon/core/simulation/tick_loop.py`
(Kwarg + Stage); `src/grid_gym/hexagon/core/scenario/loader.py`
(`build_tick_loop`-Symmetrie);
`tests/integration/test_m6_welle_5a_safe_001_004_smoke.py`
(Skip-Reaktivierung `test_safe_004_*`);
`docs/user/safe-001-004-quality-pipeline.md` (Flip ✗ → ✓);
`docs/plan/adr/README.md` (C1).
**MODIFY (C3):** `M7-welle-3.md` (3a → Done) +
`M7-mvp-completion.md` + `roadmap.md` + `carveouts.md` +
`open/README.md` + `open/034-…` (→ `done/` in C4a).
**UNBERUEHRT:** `Quality`-Enum + `QUALITY_SEVERITY` (nur
konsumiert), `TelemetryPoint`-Domain, Scenario-Schema +
`scenario_hash`-Pfad, `tools/accept.py`-Pins, Protocol-Adapter
(Welle 3b).

---

## 6. Verifikationspfad

- `make gates` cache-frei gruen (inkl. `arch-check`: Stage ist
  Core-interner Code, kein neuer Port).
- `make test-integration` gruen inkl. reaktiviertem
  `test_safe_004_stale_data_quality_after_max_age`.
- `make accept` weiter Exit 0 (Demo-Pfad unveraendert,
  3a-D-4-Beleg) + `make fullbuild` + `make docs-check`
  cache-frei gruen.

---

## 7. Risiken

- **R1 Stream-Hash-Drift.** Falls die Stage versehentlich
  Demo-Punkte markiert (Bug in der Alters-Arithmetik), flippt
  `EXPECTED_DEMO_TELEMETRY_STREAM_HASH`. Mitigation: 3a-D-4
  (Demo `None` = Stage aus) + `make accept`/Pin-Lint als
  Regression-Beleg im DoD.
- **R2 Smoke braucht nachlaufende Punkte.** Produktive Devices
  emittieren `simulation_time = now` (Alter 0) — der Smoke
  braucht ein Test-Device mit nachlaufendem Zeitstempel.
  Mitigation: Fake-Device im Test (Praezedenz: Test-Sibling-
  Fakes der TickLoop-Unit-Suite); kein produktiver Code-Touch.
- **R3 Replay-Vergleich alt/neu.** Punkte, die die Stage
  markiert, aendern den persistierten Stream gegenueber
  Vor-3a-Referenzlaeufen. Kein realer Bruch: Demo-Pfad bleibt
  aus (D-4), und der `GG-TERM`-Preflight vergleicht ohnehin nur
  konfigurationsgleiche Laeufe; dokumentiert als Hinweis in
  ADR 0052.

---

## 8. Wandert nach

Self-Close-Move `M7-welle-3a.md → done/` (C4a) + Refs-Sync (C4b)
nach 3a-C3. Der Gruppenplan [`M7-welle-3.md`](M7-welle-3.md)
bleibt bis zur 3b-Closure in `in-progress/`; danach aktiver
Slice → **Welle 3b** (3b-C0).

---

## 9. DoD-Checkliste (mit C3 abgehakt)

- [x] C0 — Gruppenplan + Slice-Doc §1..§9 + Decision-Liste
      3a-D-1..D-5 + Refs-Sync. (`9e266d2`)
- [x] C1 — NEU ADR 0052 `Provisional` (Kwarg-Surface + Stage-Naht
      + Severity-Override + Grenzwert + `AC-NO-TIME`). (`744e31e`)
- [x] C2 — `max_age_ms`-Kwarg (+ Validierung `<= 0`) + Stage vor
      `TickResult`-Bau + `build_tick_loop`-Symmetrie; Review-Folge
      F1 ergaenzt `from_snapshot`-Resume-Symmetrie. (`23c614a` +
      `5a9960a`)
- [x] C2 — Unit-Tests: Boundary (`>`/`==`/frisch) +
      Severity-Override + `None`-no-op + Reject + Determinismus
      (+ F1-Resume-Test; Shared-Fake per F3).
- [x] C2 — Smoke `test_safe_004_stale_data_quality_after_max_age`
      reaktiviert + gruen (End-to-End `Quality.STALE`;
      `test-integration` 138 passed / 5 skipped).
- [x] C2 — Doku-Flip `safe-001-004-quality-pipeline.md`
      `GG-SAFE-004` ✗ → ✓.
- [x] `make gates` + `make test-integration` + `make fullbuild` +
      `make docs-check` cache-frei gruen. **Demo-Pfad-Beleg:** der
      `accept-pin-check` in `make ci`/`fullbuild` recomputed beide
      `GG-MVP-003`-Demo-Pins headless (Scenario- + Stream-Hash
      unveraendert) — der 3a-D-4-Beleg, dass der Demo-/Abnahme-
      Pfad byte-identisch bleibt. Ein Live-`make accept` (braucht
      `make demo`-Stack + Host-uv-Venv) bleibt optionaler
      Operator-Schritt; das Pin-Aequivalent ist der CI-Beleg.
- [x] C3 — 3a `Done`; **`GG-SAFE-004` ✓ produktiv**; Trigger 034
      → Closed (Move `done/` in C4a); Gruppenplan-/roadmap-/
      carveouts-Sync; aktiver Slice → 3b.

**Anti-Scope (3a NICHT):** Scenario-Schema-Feld, per-Device-/
per-Metric-Schwellen, Demo-Schwellen-Aktivierung, `STALE`-Alarm,
Comm-Failure (3b), Alarm-Vertrag (3b).

---

## References

- [`M7-welle-3.md`](M7-welle-3.md) — Welle-3-Gruppenplan
  (Sub-Slicing-Beschluss D-1, ADR-Numbering D-3).
- [Trigger 034](034-safe-004-max-age-stale-quality.md) —
  Lücken-Verankerung + erwartete Lieferung (M6-Welle-5a-Audit).
- [`../../../user/safe-001-004-quality-pipeline.md`](../../../user/safe-001-004-quality-pipeline.md)
  — Audit-Tabelle (Flip-Ziel) + Quality-Enum-Referenz.
- [`M7-mvp-completion.md`](../in-progress/M7-mvp-completion.md) — M7-Slice-Plan
  (§2 Erfolgskriterien).
- [`../done/M7-welle-1b-b.md`](M7-welle-1b-b.md) —
  Kwarg-Praezedenz (`replay_snapshot`/`replay_reference_run_id`)
  + Slice-Doc-Pattern.
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md)
  — Schaerfungs-Pattern (Scenario-Schema-Folgeoption).
- [`../../adr/0021-scenario-loader-and-tick-loop-event-wiring.md`](../../adr/0021-scenario-loader-and-tick-loop-event-wiring.md)
  — `build_tick_loop`-Vertrag.
- [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md)
  §20 `GG-SAFE-004` (Z. 1373-1378).
