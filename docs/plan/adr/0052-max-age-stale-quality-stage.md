# ADR 0052 — `max_age`-basierte `STALE`-Quality-Stage im TickLoop-Spine (M7 Welle 3a)

**Status:** Accepted — gezogen 2026-06-12 mit M7-Welle-X-C1
(M7-Closure-Welle). Provisional-Schritt 2026-06-11 (direkter
`Proposed → Provisional`-Sprung mit M7-Welle-3a-C1).
**Datum:** 2026-06-11
**Status geaendert am:** 2026-06-11 — `Proposed → Provisional`;
2026-06-12 — `Provisional → Accepted` (M7-Welle-X-Closure).
**Bezug:**

- [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
  — Lifecycle-/Status-Pfad.
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) — Schaerfung-
  ohne-Supersedes-Pattern (Form-Anker; ADR 0052 schaerft den
  TickLoop-Spine additiv, kein bestehender Vertrag wird
  abgeloest).
- [`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md)
  — `build_tick_loop`-Vertrag (erhaelt das Symmetrie-Kwarg
  `max_age_ms`, additiv wie die 1b-b-Replay-Kwargs).
- [`ADR 0049`](0049-replay-lifecycle-finalize-hook.md) §2.7 —
  Praezedenz fuer optionale keyword-only Core-Kwargs mit
  `None`-Default = Feature aus.
- [`M7-welle-3a.md`](../planning/done-archive/M7-welle-3a.md) —
  Slice-Doc (Decisions 3a-D-1..D-5); ADR 0052 fixiert D-1..D-5.
- [`M7-welle-3.md`](../planning/done-archive/M7-welle-3.md) —
  Welle-3-Gruppenplan (Sub-Slicing D-1, ADR-Numbering D-3).
- [Trigger 034](../planning/done-archive/034-safe-004-max-age-stale-quality.md)
  — [`GG-SAFE-004`](../../../spec/lastenheft.md#gg-safe-004)-Lücken-Verankerung; wird mit 3a-C3 aufgeloest
  (`done/`).
- [`../../user/safe-001-004-quality-pipeline.md`](../../user/safe-001-004-quality-pipeline.md)
  — Quality-Pipeline-Audit (Flip-Ziel ✗ → ✓).

---

## 1. Kontext

[`GG-SAFE-004`](../../../spec/lastenheft.md#gg-safe-004) (Lastenheft §20 Z. 1373-1378, MUSS) verlangt:
Werte, deren Simulationszeitstempel die konfigurierte `max_age`
ueberschreiten, erhalten **deterministisch** den Qualitaetsstatus
`stale`. Das M6-Welle-5a-Audit stufte die ID als ✗ Lücke ein.

**Code-Ist-Stand (verifiziert, Welle-3-C0-Audit):**

- `Quality.STALE` existiert ohne Emitter
  (`hexagon/core/domain/quality.py:24`; Severity 3 im
  `QUALITY_SEVERITY`-Ranking).
- `TelemetryPoint` traegt `simulation_time: int` (ms ab
  Lauf-Start) + `quality: Quality` — beide Vergleichsgroessen
  sind vorhanden, kein neues Domain-Feld noetig.
- `TickLoop.tick()` sammelt die Device-Emissionen in `emitted`
  und baut daraus das `TickResult`
  (`emitted_telemetry=tuple(emitted)`); unmittelbar danach
  laeuft `_persist_emitted_telemetry(result)`. Live-Stream,
  Persistenz (`TelemetrySinkPort`, ADR 0047) und Replay
  (`ReplaySnapshotPort`, ADR 0048) konsumieren alle dieselbe
  `TickResult`-Projektion.
- Keine `max_age`-Konfiguration existiert (grep ueber
  `src/grid_gym/` = null Treffer); `ScenarioSimulation` kennt
  nur `tick_ms`/`duration_s`/`seed`.
- **Hash-Pin-Kopplung (Welle-2-Erbschaft):** `scenario_hash` =
  `sha256(canonical_json(asdict(scenario)))` — jedes neue
  `Scenario`-Dataclass-Feld flippt den Hash **aller** Szenarien
  und damit `EXPECTED_DEMO_SCENARIO_HASH` +
  `EXPECTED_DEMO_TELEMETRY_STREAM_HASH`
  (`tools/check_demo_scenario_pin.py`, `make ci`-Gate).

---

## 2. Entscheidung

ADR 0052 fixiert fuenf Punkte fuer die Welle-3a-`STALE`-Stage.

### §2.1 Konfigurations-Surface: `TickLoop`-Kwarg (3a-D-1)

NEU keyword-only `TickLoop`-Konstruktor-Kwarg
`max_age_ms: int | None = None` + `build_tick_loop`-Symmetrie
(`scenario/loader.py`).

- **`None` (Default) → Stage aus** (no-op) — exakt das Pattern
  der optionalen Core-Kwargs `telemetry_sink` (ADR 0047 §2.3) +
  `replay_snapshot`/`replay_reference_run_id` (ADR 0049 §2.2/
  §2.7). Bestehende Pfade bleiben byte-identisch.
- **Validierung:** `max_age_ms <= 0` → typisierter
  Konstruktor-Fehler (kein stiller Unsinn; eine Schwelle von 0
  oder negativ wuerde jeden Punkt bzw. nichts deterministisch
  Sinnvolles markieren).
- **BEWUSST KEIN Scenario-Schema-Feld:** ein Feld in
  `ScenarioSimulation`/`ScenarioDevice` wuerde den
  `asdict`-basierten `scenario_hash` aller Szenarien flippen
  (Pin-Bruch, §1) und ein Schema-Touch fuer eine SOLLTE-Schwelle
  ohne existierende Stakeholder-Anforderung waere
  unverhaeltnismaessig. „Konfigurierte `max_age`" der Akzeptanz
  bindet an Konfigurierbarkeit, nicht an einen
  Szenario-Datei-Standort. **Folgeoption:** ein optionales
  Scenario-Feld ist eine additive ADR-0011-Schaerfung, sobald
  eine konkrete Schwelle gefordert wird — dann mit bewusstem
  Pin-Update im selben PR (der Drift-Lint erzwingt das).
- **KEINE per-Geraet-/per-Metric-Granularitaet** (Trigger-034-
  Option): Over-Engineering ohne Anforderung; jederzeit additiv
  nachruestbar.

### §2.2 Stage-Naht: in `tick()` vor dem `TickResult`-Bau (3a-D-2)

Die Stage laeuft in `TickLoop.tick()` auf der gesammelten
`emitted`-Liste, **unmittelbar vor** dem `TickResult`-Bau:

```python
if self._max_age_ms is not None:
    emitted = [
        replace(point, quality=Quality.STALE)
        if (now - point.simulation_time) > self._max_age_ms
        and QUALITY_SEVERITY[point.quality] < QUALITY_SEVERITY[Quality.STALE]
        else point
        for point in emitted
    ]
```

- **Eine Stelle, drei Konsumenten:** Stream + Persistenz +
  Replay sehen identisch markierte Punkte — keine zweite
  Pruefstelle, kein Drift-Risiko.
- **NICHT Device-seitig** (N Pruefstellen, jedes Device muesste
  die Schwelle kennen) und **NICHT Sink-/Adapter-seitig**
  (Replay-/Stream-Pfad bliebe unmarkiert; Core-Semantik gehoert
  in den Spine, [`GG-AR-P-003`](../../../spec/architecture.md#2-architekturprinzipien)).
- Quality-Austausch via `dataclasses.replace` (frozen + slots
  bleiben gewahrt; alle uebrigen Felder unveraendert —
  insbesondere `sequence`/`source`, das Scheduler-Tie-Breaking
  ist unberuehrt).
- **Bilanz-Abgrenzung (C2-Review-Folge F2):** die
  Netzbilanz-Aggregation (`bucket_sums` →
  `GridModelBilanz.update`, Schritt B/D/E) laeuft **vor** der
  Stage und ist im Bestand **quality-agnostisch** (sie filtert
  nur nach Metrik, nie nach Quality — auch `INVALID`-/`MISSING`-
  Punkte gingen schon immer mit Rohwert ein). Ein als `STALE`
  markierter Punkt ist also mit seinem Rohwert in der Bilanz
  verrechnet — **Markierung ≠ Filterung**; [`GG-SAFE-004`](../../../spec/lastenheft.md#gg-safe-004)
  verlangt nur die Markierung, und die Stage aendert die
  Simulations-Physik bewusst nicht. Eine quality-gewichtete
  Bilanz waere eine eigene, additive Schaerfung mit eigenem
  Fach-Vertrag (nicht 3a, nicht 3b).

### §2.3 Severity-Override-Regel (3a-D-3)

`STALE` (Severity 3) ersetzt nur Qualities mit **niedrigerer**
Severity: `VALID` (0) / `ESTIMATED` (1) / `LIMITED` (2).
Qualities mit hoeherer Severity — `FAULT_INJECTED` (4) /
`INVALID` (5) / `NAN` (6) / `MISSING` (7) — bleiben unangetastet.

- Nutzt das **existierende** `QUALITY_SEVERITY`-Ranking
  (`quality.py:33-42`) — deterministisch, keine neue Ordnung.
- **Begruendung:** kein Informationsverlust ueber schwerere
  Befunde — ein als `INVALID` erkannter Wert bleibt `INVALID`,
  auch wenn er zusaetzlich alt ist; der schwerere Befund
  dominiert.

### §2.4 Determinismus-Garantie: nur Sim-Zeit (3a-D-4)

Die Alterspruefung vergleicht ausschliesslich
**Simulationszeit** gegen Simulationszeit: `now` (die
`simulation_time` des laufenden Ticks) minus
`point.simulation_time`. **Kein Wall-Clock-Zugriff** —
`AC-NO-TIME` bleibt im Core gewahrt; zwei gleich-konfigurierte
Laeufe markieren identische Punkte (Replay-stabil,
[`GG-SAFE-004`](../../../spec/lastenheft.md#gg-safe-004)-„deterministisch").

**Demo-Wiring bleibt `max_age_ms=None`** (Stage im Demo-Pfad
aus): es existiert keine konkrete Stakeholder-Schwelle
(Trigger-034-Aktivierung erfolgte per Maintainer-Entscheidung,
nicht per Compliance-Druck mit Wert); eine erfundene
Demo-Schwelle waere Schein-Konfiguration, die nie feuert (alle
Demo-Devices emittieren frische Punkte, Alter 0). Der
Akzeptanz-Beleg ist der reaktivierte Welle-5a-Smoke +
Unit-Boundary-Tests; Demo-Aktivierung ist ein Einzeiler bei
Bedarf. Folge: **kein** Verhaltens- oder Stream-Hash-Delta im
produktiven Demo-/Abnahme-Pfad (`make accept`-Pins unberuehrt).

### §2.5 Grenzwert-Semantik: strikt `>` (3a-D-5)

`(now - point.simulation_time) > max_age_ms` markiert;
Gleichheit (`== max_age_ms`) ist nicht „ueberschritten"
(Lastenheft-Wortlaut) und bleibt unmarkiert. C2 pinnt die
Grenze beidseitig per Unit-Test (`>` stale / `==` nicht /
frisch nicht).

---

## 3. Begruendung

- **[`GG-SAFE-004`](../../../spec/lastenheft.md#gg-safe-004) schliessen.** Die Stage ist die fehlende
  Emissions-Substanz fuer den seit M5-Welle-6b existierenden
  `Quality.STALE`-Enum-Wert; mit ihr flippt die letzte
  ✗-Lücken-Zeile des Welle-5a-Audits.
- **Spine statt Device/Adapter ([`GG-AR-P-003`](../../../spec/architecture.md#2-architekturprinzipien)).** Eine zentrale
  Stage im Tick-Prozessor wirkt auf jeden Lauf (Live, Demo,
  headless) und jeden Konsumenten (Stream, Persistenz, Replay)
  identisch — genau eine Pruefstelle.
- **Minimaler Eingriff.** Kwarg-Surface + Listen-Pass vor dem
  `TickResult`-Bau; kein Schema-Touch, kein Pin-Bruch, kein
  neuer Port, keine neue Domain-Form.
- **Schaerfung ohne Supersedes (ADR 0011).** ADR 0021
  (`build_tick_loop`) erhaelt ein additives Kwarg; kein
  bestehender Vertrag aendert sich.

---

## 4. Reichweite

- NEU `TickLoop`-Kwarg `max_age_ms` (+ Validierung) + Stage in
  `tick()` (`hexagon/core/simulation/tick_loop.py`) (C2).
- `build_tick_loop`-Symmetrie (`hexagon/core/scenario/loader.py`)
  (C2).
- NEU Unit-Tests `tests/unit/hexagon/core/simulation/
  test_tick_loop_welle_3a_max_age.py` + Reaktivierung
  `test_safe_004_stale_data_quality_after_max_age`
  (`tests/integration/test_m6_welle_5a_safe_001_004_smoke.py`)
  (C2).
- Flip `docs/user/safe-001-004-quality-pipeline.md`
  [`GG-SAFE-004`](../../../spec/lastenheft.md#gg-safe-004) ✗ → ✓ (C2).
- ADR-Index NEU ADR-0052-Zeile (C1).
- **Unberuehrt:** `Quality`-Enum + `QUALITY_SEVERITY` (nur
  konsumiert), `TelemetryPoint`-Domain, Scenario-Schema +
  `scenario_hash`-Pfad, Demo-Wiring (`None`),
  `tools/accept.py`-Pins, Protocol-Adapter (Welle 3b),
  Scheduler-Tie-Breaking.

---

## 5. Lieferung

Lieferplan, Commit-Hashes + Verifikations-Gates leben in der
Slice-Doc [`M7-welle-3a.md`](../planning/done-archive/M7-welle-3a.md)
(C2: Code-Substanz; Verifikation inkl. `make accept` Exit 0 als
Demo-Unveraendert-Beleg). Status-Pfad (`Proposed → Provisional →
Accepted`): `Accepted` gezogen 2026-06-12 mit M7-Welle-X-C1
(gebuendelt mit ADR 0047..0049).

---

## 6. Konsequenzen

- **Positiv:** [`GG-SAFE-004`](../../../spec/lastenheft.md#gg-safe-004) flippt ✗ → ✓ produktiv;
  Trigger 034 schliesst; der Welle-5a-Skip-Smoke wird
  reaktiviert.
- **Positiv:** die Stage gilt fuer jeden `TickLoop`-Lauf —
  kuenftige Quellen nachlaufender Zeitstempel (z. B. ein
  produktiver Protocol-Adapter-`read()`-Pfad mit Queue-Latenz,
  Welle-3b+-Material) sind automatisch abgedeckt.
- **Neutral:** der Core haelt ein weiteres optionales Kwarg;
  `None`-Default haelt bestehende Pfade byte-identisch
  (Demo-/Abnahme-Pins unberuehrt, §2.4).
- **Neutral (Replay alt/neu):** Laeufe mit gesetztem
  `max_age_ms` erzeugen gegenueber Vor-3a-Referenzlaeufen
  andere Quality-Werte — kein realer Bruch: der
  `GG-TERM`-Preflight (ADR 0049 §2.3) vergleicht ohnehin nur
  konfigurationsgleiche Laeufe, und der Demo-Pfad bleibt aus.
- **Bewusste Grenze:** heutige produktive Devices emittieren
  `simulation_time = now` (Alter 0) — die Stage feuert im
  Bestand nie; der Beleg lebt in Tests mit nachlaufenden
  Zeitstempeln. Das ist die ehrliche Operationalisierung der
  Akzeptanz, solange keine nachlaufende Quelle produktiv ist.

---

## 7. Nicht Gegenstand dieser ADR

- **Scenario-Schema-Feld fuer `max_age`** — additive
  ADR-0011-Schaerfung bei konkreter Stakeholder-Schwelle
  (mit bewusstem Pin-Update, §2.1).
- **Per-Geraet-/per-Metric-Schwellen** — additive Schaerfung
  bei Bedarf.
- **Demo-Schwellen-Aktivierung** — Einzeiler bei konkreter
  Anforderung (§2.4).
- **Alarm-Emission bei `STALE`** — [`GG-SAFE-004`](../../../spec/lastenheft.md#gg-safe-004) verlangt nur
  die Markierung; Alarm-Substanz ist [`GG-SAFE-003`](../../../spec/lastenheft.md#gg-safe-003)-Material
  (Welle 3b, Trigger 035).
- **Comm-Failure-Quality (`MISSING`) + Adapter-Lifecycle** —
  Welle 3b ([Trigger 035](../planning/done-archive/035-safe-003-comm-failure-missing-quality.md);
  ADR-Nummer 0053 reserviert).
- **`Quality.NAN`-/`ESTIMATED`-Emitter** — eigene Scopes
  (NAN bleibt per M2-Trigger-014-Entscheidung
  Serialisierungs-Reject statt Quality-Emission).
