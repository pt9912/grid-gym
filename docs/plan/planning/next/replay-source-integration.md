# GG-MVP-002 Closure — Zeitreihen-Persistenz + Replay-Source-Integration + `replay_diff_status`-Metrik

**Status:** Next — getriaged auf **M7-Welle-1** (per
M7-Welle-0-C2-Triage 2026-06-08; siehe
[`M7-mvp-completion.md §3`](../in-progress/M7-mvp-completion.md)).
Aktivierung (`git mv next/ → in-progress/`) +
Decision-Finalisierung in M7-Welle-1-C0.
**Datum:** 2026-06-07 (Scope-Skizze) · **Re-Sharpened
2026-06-08** (gegen M7-Stand: ADR-Nummer 0047 statt 0046,
M7-Welle-1-Positionierung, M6-Welle-6-`/ready`-Erbschaft).
**Quelle:** [`roadmap.md §M7 + GG-MVP-002-Zeile`](../in-progress/roadmap.md)
+ [`open/036-safe-006-replay-diff-status-replay-source-integration.md`](../open/036-safe-006-replay-diff-status-replay-source-integration.md)
(Welle-5c-Audit, Trigger-Watch).

---

## 1. Context

`GG-MVP-002` ist der einzige `GG-MVP-*`-Punkt im **partial**-
Stand. Die anderen MVP-Punkte: 001 ✓ produktiv; **003
Abnahme-CLI ist M7-Welle-2** (M6-Welle-6 hat es NICHT als
Scope-Erweiterung aufgenommen — eigener Plan
[`abnahme-cli.md`](abnahme-cli.md), getriaged auf M7-Welle-2);
004 eigener Tracking-Pfad.

**Lastenheft-Akzeptanz (Z. 130-135, GG-MVP-002):**

> Der MVP MUSS mindestens ein End-to-End-Szenario mit
> Netzanschlusspunkt, PV, Lastprofil, Smart Meter und
> Batteriespeicher enthalten. Akzeptanz: Das Szenario
> startet ueber API, erzeugt Live-Telemetrie, persistiert
> Zeitreihen und **laesst sich deterministisch replayen**.

**Stand der vier Akzeptanz-Komponenten:**

| Komponente | Substanz | Status |
| --- | --- | --- |
| Szenario startet ueber API | `POST /runs` + Demo-Szenario `deploy/scenarios/gg-demo.yaml` (5 Entitaeten per Lastenheft-Pflicht: GridConnection + PV + Last + Smart Meter + Batteriespeicher) | ✓ produktiv |
| Live-Telemetrie | WebSocket-Streams `/runs/{id}/telemetry` + `/runs/{id}/alarms-stream` | ✓ produktiv |
| Persistiert Zeitreihen | `PostgresRunRepository` persistiert Laufmetadaten ✓; produktive `TelemetrySinkPort`-/Zeitreihen-Persistenz fuer Telemetriepunkte fehlt noch (`GG-PERSIST-001` listet Telemetrie-/Alarm-Schema weiter als M3-offen) | ⚠ **partial** |
| **Laesst sich deterministisch replayen** | Core-Diff `diff_replay()` ✓ produktiv (Welle-5c-Audit); **End-to-End-Verkabelung fehlt** | ⚠ **partial** |

Die offenen Akzeptanzteile sind damit zwei gekoppelte
Luecken:

1. Telemetrie-Zeitreihen muessen produktiv append-only und
   deterministisch sortierbar persistiert werden. `RunRepositoryPort`
   reicht dafuer nicht, weil er nur Laufmetadaten/Status haelt.
2. Ein persistierter Lauf muss ohne manuelle Diff-Sequenzen-
   Konstruktion gegen einen Re-Run verglichen werden koennen, und
   der Vergleich muss maschinenlesbar (`replay_diff_status`)
   emittieren. Heute gibt es weder einen produktiven
   `ReplaySourcePort`-Adapter noch einen Lauf-Lifecycle-Hook, der
   `diff_replay()` automatisch aufruft.

**Trigger-036-Vorbelegung** (Welle-5c-C2): die Replay-
Substanz-Skizze ist in [Trigger 036](../open/036-safe-006-replay-diff-status-replay-source-integration.md)
verankert (`replay_diff_status`-Metrik, Driven-Adapter,
Lifecycle-Hook im Core-Spine, `GG-TERM-002`-Equality-
Vorbedingung). Dieser `next/`-Plan erweitert die Trigger-
Notiz um die fuer `GG-MVP-002` noch fehlende produktive
Zeitreihen-Persistenz; falls Welle-X-C0 diese Arbeit
separat schneidet, bleibt `GG-MVP-002` bis zur zweiten Welle
partial.

## 2. Lieferziel

Ein eigenstaendiger Slice — **M7-Welle-1** (per
M7-Welle-0-C2-Triage; siehe §5) — liefert:

1. **Produktive Zeitreihen-Persistenz fuer Telemetriepunkte**
   (`GG-PERSIST-001`, Architektur `TelemetrySinkPort`): NEU
   `TelemetrySinkPort`-Protocol, Postgres-Adapter und Alembic-
   Schema, falls diese Surface bei Aktivierung weiterhin fehlt.
   - Persistierte Records muessen alle `TelemetryPoint`-/
     `GG-PERSIST-001`-Pflichtfelder strukturiert tragen:
     `run_id`, `tick`, `simulation_time`, `device_id`, `metric`,
     `value`, `unit`, `quality`, `source` und `sequence`. C0
     gleicht die exakten Felder gegen das Core-Domain-
     `TelemetryPoint` (`src/grid_gym/hexagon/core/domain/telemetry.py`,
     `GG-DATA-001` — **nicht** das gleichnamige Driving-Stream-
     DTO in `ports/driving/telemetry_stream.py`), `GG-DATA-*`
     und `GG-PERSIST-001` ab.
   - Der Pfad ist **nicht** `RunRepositoryPort`; dieser bleibt
     Laufmetadaten/Status.
   - Live-Telemetrie kann weiter ueber die bestehende Stream-
     Surface laufen, aber der Slice muss belegen, dass derselbe
     Demo-/API-Lauf Zeitreihen persistiert.
   - Der Persistenz-Smoke muss nicht nur Existenz pruefen:
     deterministische Sortierung bei gleicher Simulationszeit,
     append-only-Verhalten ohne doppelte Records beim erneuten
     Lesen, alle `GG-PERSIST-001`-/`TelemetryPoint`-Felder
     inklusive `unit`, `source` und `sequence` sowie stabile
     kanonische Ausgabe sind Boundary-Pins.

2. **Driven-Adapter `SnapshotReplaySource` fuer
   `ReplaySourcePort`-Surface** (Architektur §4.2 Z. 248 +
   §8 Z. 544): produktive Implementation, die
   `ReplaySample`-Sequenzen aus einem persistierten
   Lauf-Snapshot liefert.
   - Persistenz-Quelle ist **nicht** `RunRepositoryPort`
     (haelt nur Lauf-Metadaten/Status).
   - Welle-X-C0 entscheidet, ob der Sample-Strom aus dem
     bestehenden `SnapshotPort` (= `GG-AR-PORT-DRV-005`,
     Driving — eine Persistenz-Quelle aus einer Driving-
     Surface zu ziehen ist ein Schichten-Twist; siehe §3 D-1)
     oder einem NEU `ReplaySnapshotPort` (Driven, Persistenz-
     Schicht) kommt.

3. **`replay_diff_status`-Metrik-Emission** (Architektur §15
   Z. 820 + 823): nach jedem `diff_replay()`-Aufruf ein
   maschinenlesbarer Statuswert pro Lauf auf `MetricsPort`.
   - **Semantische Wertedomaene und numerische
     `MetricsPort`-Kodierung** werden in C1-ADR fixiert
     (Welle-X-D-2; siehe §3). Der bestehende `MetricsPort`
     akzeptiert numerische Werte; String-Statuswerte duerfen
     hoechstens als Attribute/Labels auftauchen.
   - Der Statuswert ersetzt NICHT den `GG-SAFE-006`-Detailvertrag:
     die integrierte Replay-Erkennung muss Replay-Diff, volatile
     Felder, betroffene Ticks und Abweichungsklassifikation
     maschinenlesbar bereitstellen oder `GG-SAFE-006` bleibt
     in der Audit-Doku `partial`.

4. **Core-Spine-Lifecycle-Hook**: ein NEU zu schaerfender
   Core-seitiger Lauf-Lifecycle-Hook ruft
   `diff_replay()` mit den `ReplaySourcePort`-Sequenzen
   auf + emittiert die Metrik.
   - Driving-Adapter (HTTP-Action-Router, WebSocket, UI,
     CLI) duerfen den Hook NICHT tragen (`GG-AR-P-003`-
     Verletzung — Simulationslogik kennt keine
     Kommunikationsadapter, Abhaengigkeiten zeigen nach innen;
     `GG-AR-P-007` stuetzt: Live + Replay teilen denselben
     Tick-Prozessor, der Hook gehoert in diesen Spine, nicht in
     einen Adapter; siehe Trigger 036 D-3).

5. **`GG-TERM-002`-/`GG-TERM-003`-Equality-Vorbedingung im
   Live-Mode**: Replay-Vergleich nur unter vollstaendig
   operationalisierter Reproduzierbarkeits-Gleichheit:
   Tool-/Schema-Version, Plattformarchitektur, Eingabedaten bzw.
   Szenario-Datei/-Hash, kanonischer Konfigurations-Hash,
   Startzeit im Simulationszeitmodell, aktivierte Adapter/
   Adapterprofile, Seed und `tick_ms`.
   `GG-TERM-002`/`GG-TERM-003` sind dabei normative
   Begriffsdefinitionen (Lastenheft §27.1.1 / Z. 2203:
   „n/a — normative Begriffsdefinition", **nicht** in der
   Implementations-Matrix); sie liefern die Feldliste, der
   *testbare* Determinismus-Vertrag traced auf `GG-AR-P-008`
   (`GG-SIM-001/002/003`, `GG-RT-002`) plus die GG-TERM-002-
   Akzeptanz (byte-identische kanonische Ergebnisdateien oder
   leerer Replay-Diff).
   C0/C1 legt fest, ob diese Daten in `RunMetadata` oder einem
   eigenen `ReplayComparisonMetadata`-Envelope liegen. Fehlende
   oder abweichende Pflichtfelder rejecten vor Diff-
   Klassifikation; Boundary-Tests pinnen die kritischen Felder
   einzeln, nicht nur einen generischen Mismatch.

6. **NEU Integration-/Replay-Smoke-Familie**:
   - Zeitreihen-Persistenz-Smoke: API-/Demo-Lauf erzeugt
     persistierte Telemetrie-Zeitreihen fuer die MVP-Geraete;
     Boundary-Pin prueft stabile Sortierung bei Ties,
     append-only-Wiederholungslesen und alle strukturierten
     `GG-PERSIST-001`-/`TelemetryPoint`-Felder.
   - Clean-Replay-Smoke: persistierter Lauf + gleicher Re-Run
     liefern leeren Diff und emittieren den `clean`-Statuswert.
   - Divergence-Smoke: bewusst eingefuehrte Tick-Differenz
     zwischen zwei Sample-Quellen wird als Divergenz-
     Statuswert emittiert und stellt die `GG-SAFE-006`-
     Detailfelder maschinenlesbar bereit: Replay-Diff,
     volatile Felder, betroffene Ticks und
     Abweichungsklassifikation.
   - Boundary-Test-Familie: Metadata-Mismatches nach
     `GG-TERM-002`/`GG-TERM-003` rejecten vor Diff-
     Klassifikation; mindestens Version, Konfiguration,
     Startzeit im Simulationszeitmodell, aktivierte Adapter,
     Seed und `tick_ms` werden einzeln gepinnt.
   - Wiederholungs-/Idempotenz-Pin: derselbe persistierte Lauf
     kann erneut gelesen und verglichen werden, ohne Status- oder
     Sample-Duplikation zu erzeugen.

7. **`docs/user/replay-determinism-e2e.md`** Audit-Doku
   (Pattern analog Welle-5*-Audit-Docs): markiert
   `GG-MVP-002` erst dann als ✓ produktiv, wenn Zeitreihen-
   Persistenz und Replay-E2E beide belegt sind. Die
   `GG-SAFE-006`-Audit-Doku
   (`docs/user/safe-005-006-fallback-determinism.md`) flippt
   nur dann von ⚠ partial auf ✓ produktiv, wenn der integrierte
   Pfad neben `replay_diff_status` auch die vier
   Safety-Detailfelder aus `GG-SAFE-006` maschinenlesbar pinnt;
   sonst bleibt `GG-SAFE-006` partial und Trigger 036 wandert
   noch nicht nach `done/`.

## 3. Architektur-Entscheidungs-Skizze (Welle-X-Decisions; nicht final)

Die folgenden Entscheidungen werden im Welle-X-C0-Slice-Doc
final festgelegt. Hier nur die Optionen-Skizze.

### D-0 — Zeitreihen-Persistenz-Surface

- **A**: NEU `TelemetrySinkPort` (Driven) + Postgres-
  Adapter + `telemetry_points`-Schema. Schmaler Vertrag fuer
  append-only Telemetrie-Zeitreihen; Query-/Export-Surfaces
  bleiben eigener Scope, ausser C0 braucht sie fuer den Smoke.
- **B**: Bestehende Live-Stream-Surface um Persistenz erweitern.
  Wiederverwendet Demo-Wiring, mischt aber Stream-/Persistenz-
  Verantwortung und braucht besondere Adapter-Purity-Pruefung.
- **C**: `RunRepositoryPort` als ausreichend behandeln. Verworfen:
  der Port haelt nur Laufmetadaten/Status und keine Zeitreihen.

Vorschlag: A. Welle-X-C0 verifiziert gegen `TelemetryPoint`,
`GG-PERSIST-001` und die vorhandene Live-Telemetry-Surface.

### D-1 — Persistenz-Quelle fuer `expected`-Samples

- **A**: NEU `ReplaySnapshotPort` (Driven) mit Postgres-
  Adapter, der `ReplaySample`-Sequenzen aus dem persistierten
  Lauf-Snapshot extrahiert. Eigener Vertrag, eigene Tabelle.
- **B**: `SnapshotPort` (`GG-AR-PORT-DRV-005`, Driving) plus
  Sample-Extraktor — wiederverwendet bestehende Persistenz-
  Surface; aber Driving-Port als Persistenz-Quelle ist
  Schichten-Twist (Driving + Driven gemischt).
- **C**: Telemetrie-Schicht (`TelemetrySinkPort`) als Sample-
  Quelle, falls D-0 sie liefert; aber `TelemetryPoint` fuehrt
  keinen Original-`timestamp`-String (nur `tick` +
  `simulation_time`), den `ReplaySample` per `GG-REPLAY-002`
  zwingend traegt — Option C braucht also ein Zusatzfeld oder
  eine Mapping-Konvention (siehe D-1.1).

Vorschlag: A (NEU `ReplaySnapshotPort` Driven). Welle-X-C0
verifiziert.

**Sub-Decision D-1.1 — Snapshot→`ReplaySample`-Rekonstruktion**:
`ReplaySample` ist **bereits** als Frozen-Dataclass im Domain-
Modell verankert (`src/grid_gym/hexagon/core/domain/replay.py`,
`GG-REPLAY-001/002/003`) und wird von `diff_replay()`
(`hexagon/core/replay/diff.py`) konsumiert. Die Felder sind
`timestamp` (Original-Zeitstempel als String, `GG-REPLAY-002`
„unveraendert gespeichert"), `simulation_time`, `device_id`,
`metric`, `value`, `unit` und `import_sequence` (Tie-Breaking-
Counter, `GG-REPLAY-003`). Die `ReplaySample`-Form ist also
**nicht** offen; offen ist die Persistenz→`ReplaySample`-
Rekonstruktion aus dem Snapshot. Kritisch dabei: der Original-
`timestamp` ist ein `ReplaySample`-Pflichtfeld, das
`TelemetryPoint` (`core/domain/telemetry.py`, nur `tick` +
`simulation_time`) **nicht** fuehrt. Welle-X-C0 legt das
Snapshot-Mapping gegen die bestehende `ReplaySample`-Signatur
fest; genau diese Timestamp-Luecke ist der Grund, warum D-1
Option C (Telemetrie als Sample-Quelle) nicht ohne Zusatzfeld
oder Mapping-Konvention gegen A/B abgrenzbar ist.

### D-2 — Semantik + `MetricsPort`-Kodierung des `replay_diff_status`

- **A**: Binaer semantisch (`clean`/`diverged`), numerisch als
  `MetricsPort.gauge("replay_diff_status", 0.0|1.0,
  attributes={"run_id": ..., "status": ...})`.
- **B**: Ordinal mit drei Stufen (`green`/`yellow`/`red`)
  + Klassifikations-Regel, numerisch z. B. `0.0/1.0/2.0`.
- **C**: Per-`ReplayDeltaClassification`-Mapping
  (`fachlich`/`volatil`-Counter; Aggregat-Status auf Basis
  von `fachlich`-Count > 0), numerisch per Gauge/Counter-
  Familie ohne neue `MetricsPort`-Methode.

Vorschlag: A (binaer; einfachstes maschinenlesbares Modell,
keine Severity-Drift-Diskussion, kompatibel mit ADR-0024-
`MetricsPort`). Welle-X-C0-ADR verifiziert. Der binaere Status
ist nur der Per-Lauf-Marker; die `GG-SAFE-006`-Details
(`ReplayDelta`-Diff, volatile Felder, Ticks, Klassifikation)
bleiben ein separater maschinenlesbarer Evidence-Vertrag —
konsistent damit, dass `spec/architecture.md §15` Z. 823 die
Status-Zeile bereits an `GG-REPLAY-007` **und** `GG-SAFE-006`
koppelt.

### D-3 — Lifecycle-Hook-Position

- **A**: NEU TickLoop-Terminal-Hook im Core-Spine, geschaerft
  gegen den heutigen `control_state`-/`request(...)`-Pfad.
- **B**: NEU Core-Service `RunReplayValidator` mit
  Application-Service-Form (Driving-Port-Aufruf vom Adapter).

Vorschlag: A (Terminal-Transition im TickLoop ist der
natuerliche Spine-Punkt; eigener `RunReplayValidator`-Core-
Service ist YAGNI fuer eine einzige Metrik-Emission). Welle-X-C0
auditiert dafuer explizit den Ist-Zustand: es gibt heute keinen
`TickLoop.finalize()`-Hook, sondern `control_state`,
`request(...)`, `tick()`-Terminal-Guards und den externen
`DemoTickLoopDriver`-Loop. Falls Welle-X-C0 Option B waehlt,
muss der C2-Sub-Scope den Service explizit aufnehmen; Option A
liefert keinen separaten Service.

### D-4 — Sub-Slicing-Beschluss

- **A**: Monolithischer Slice (Zeitreihen-Persistenz +
  Replay-Adapter + Metrik + Lifecycle + Audit-Doku in einer
  Welle).
- **B**: Sub-Slicing — eigener Slice fuer Zeitreihen-
  Persistenz und ggf. `SnapshotPort`-/`ReplaySnapshotPort`-
  Re-Modellierung, plus Folge-Slice fuer Lifecycle + Metrik.

Vorschlag: B falls D-0 eine neue Postgres-Zeitreihen-Migration
plus D-1 eine eigene Replay-Snapshot-Migration braucht; A nur,
wenn C0 beide Schemata klein und reviewbar schneiden kann.

### D-5 — ADR-Bedarf

- **NEU ADR(s) (`Provisional`)** — ein oder zwei ADRs,
  abhaengig vom D-4-Beschluss:
  - **Monolithisch (D-4 Option A)**: ein ADR
    `GG-MVP-002-Replay-Source-Integration` verankert alle
    fuenf Substanz-Entscheidungen (Zeitreihen-Persistenz,
    Replay-Source-Adapter-Form, numerischer
    `replay_diff_status`-Vertrag, separater
    `GG-SAFE-006`-Detailvertrag, vollstaendige
    `GG-TERM-002`-/`GG-TERM-003`-Equality-Matrix +
    Lifecycle-Hook-Pflicht im Core-Spine nach
    `GG-AR-P-003`/`GG-AR-P-007`).
  - **Sub-sliced (D-4 Option B)**: zwei ADRs — ein
    Persistenz-ADR (`TelemetrySinkPort`-Zeitreihen-
    Persistenz + ggf. `ReplaySnapshotPort`-Adapter-Form)
    und ein Replay-Lifecycle-ADR (numerischer
    `replay_diff_status`-Vertrag, separater
    `GG-SAFE-006`-Detailvertrag, vollstaendige
    `GG-TERM-002`-/`GG-TERM-003`-Equality-Matrix +
    Lifecycle-Hook-Pflicht im Core-Spine nach
    `GG-AR-P-003`/`GG-AR-P-007`).
  Welle-X-C0 trifft die Aufteilungs-Entscheidung gegen D-4.
- Naechste freie ADR-Nummer ist **0047** (letzte vergebene:
  `0046-multi-python-test-stage-pattern.md`, M6-Welle-6); bei
  Sub-Slicing 0047 + 0048.

## 4. Sub-Scope (Welle-Vorbelegung)

Falls D-4 Option A (monolithisch):

- **Welle-X-C0** Slice-Doc + Decision-Liste D-0..D-5 final.
- **Welle-X-C1** NEU ADR (Provisional).
- **Welle-X-C2** Code-Substanz:
  - NEU `TelemetrySinkPort` (Driven-Protocol) falls bei
    Aktivierung noch nicht vorhanden.
  - NEU `PostgresTelemetrySinkAdapter` + Alembic-Zeitreihen-
    Schema.
  - NEU `ReplaySnapshotPort` (Driven-Protocol).
  - NEU `PostgresReplaySnapshotAdapter` (Driven-Adapter).
  - NEU TickLoop-Terminal-Hook / Core-Lifecycle-Surface.
  - `replay_diff_status`-Metrik-Emission auf `MetricsPort`
    mit numerischer Kodierung.
  - NEU `docs/user/replay-determinism-e2e.md`.
  - NEU `tests/integration/test_mvp_002_timeseries_replay_smoke.py`
    mit Zeitreihen-Sortier-/Append-only-, vollstaendiger
    `GG-PERSIST-001`-Feld-, Clean-Replay-, Divergence-Detail-,
    Equality-Feld- und Idempotenz-Pins.
  - `docs/user/safe-005-006-fallback-determinism.md` Status-
    Sync auf ✓ produktiv nur bei belegtem `GG-SAFE-006`-
    Detailvertrag; andernfalls bleibt die partial-Markierung.
  - Trigger 036 wandert erst nach `done/`, wenn Status-Metrik,
    ReplaySource-Integration und `GG-SAFE-006`-Details belegt
    sind.
- **Welle-X-C3** Status/DoD-Sync.
- **Self-Close-Folge C4a/C4b**.

Falls D-4 Option B (sub-sliced):
- Welle-X = Zeitreihen-Persistenz + ggf. `ReplaySnapshotPort`-
  Substanz-Welle.
- Welle-Y = Lifecycle-Hook + Metrik + Replay-E2E-Audit-Doku.
  `GG-MVP-002` flippt erst nach Welle-Y, wenn Welle-X-Evidence
  gruen vorliegt.

## 5. Vorbedingungen + Aktivierungs-Bedingungen

**Erfuellte Vorbedingungen:**

- ✓ Core-Diff `diff_replay()` produktiv (Welle-5c-Audit).
- ✓ `RunRepositoryPort` + Lauf-Metadaten produktiv (M1-
  Welle-6c).
- ✓ `MetricsPort` produktiv (M3-Welle-5/6-OTel-Adapter +
  M6-Welle-3-CI).
- ✓ TickLoop-Run-Lifecycle-Basis existiert (`control_state`,
  `request(...)`, terminale `stopped`/`completed`-Guards);
  ein dedizierter Terminal-Hook existiert **noch nicht** und
  ist Lieferumfang dieses Slice.

**Noch nicht erfuellt / Lieferumfang:**

- ⚠ Produktive Telemetrie-Zeitreihen-Persistenz fehlt; diese
  Luecke blockiert `GG-MVP-002` genauso wie Replay-E2E.
- ⚠ `ReplaySourcePort`-Adapter + Lifecycle-Verkabelung fehlen.

**Aktivierungs-Beschluss (erfolgt 2026-06-08):** Per
M7-Welle-0-C2-Triage ist dieser Plan **`Active in
M7-Welle-1`** ([`M7-mvp-completion.md §3`](../in-progress/M7-mvp-completion.md))
— M7 (MVP-Abschluss) ist der eroeffnete aktive Meilenstein,
`GG-MVP-002` ist seine erste (groesste) Substanz-Welle.
M7-Welle-1-C0 aktiviert diesen Plan (`git mv next/ →
in-progress/`), finalisiert D-0..D-5 und entscheidet das
Sub-Slicing (D-4) gegen die dann gemessene Migrations-Groesse.

**Bundling-Pruefung in Welle-1-C0:**

- **`GG-REPLAY-004..006`** (Status `🔲 M3` per Lastenheft
  Z. 2269) teilt den gleichen Lauf-Lifecycle-Hook —
  Welle-1-C0 prueft Mit-Buendelung.
- **CI-Bench-Determinismus-Drift** (Welle-4b-a-Bench-Suite
  ODER anderer CI-Sensor mit `FACHLICH`-Deltas): waere ein
  vorgezogener Aktivierungs-Grund gewesen; jetzt ohnehin
  aktiv — der Replay-Status-Marker dient zugleich als
  Drift-Diagnose.
- **Compliance-Druck** auf maschinenlesbaren Replay-Status
  pro Lauf: durch die M7-Welle-1-Lieferung abgedeckt.

## 6. Risiken

**R1 — Doppeltes Persistenz-Schema.** D-0 kann ein
`telemetry_points`-Schema brauchen, D-1 zusaetzlich ein
`run_snapshots`-/Replay-Sample-Schema.
**Mitigation:** Welle-X-C0 trennt Zeitreihen-Records von
Replay-Samples und entscheidet Sub-Slicing nach Migrations-
Groesse. Falls `ReplaySample`-Sequenzen schon in der
Snapshot-Envelope-Sektion liegen, entfaellt die zweite
Migration.

**R2 — Lifecycle-Hook-Timing.** Wenn der neue Terminal-Hook
synchron `diff_replay()` aufruft, koennte er die Lauf-Closure
verzoegern (bei grossen Sample-Sequenzen).
**Mitigation:** Welle-X-C0 entscheidet das Ausfuehrungsmodell
(synchron vs. asynchron). Welle-X-C2 pinnt, dass die Lauf-
Status-Transition nicht auf unbounded Diff-Arbeit blockiert;
falls asynchrone Entkopplung noetig ist, braucht sie einen
expliziten Lifecycle-/Drain-Vertrag statt eines impliziten
Fire-and-forget-Tasks.

**R3 — `replay_diff_status`-Wertedomaene fixiert sich
zu frueh oder passt nicht zum `MetricsPort`.** ADR-0011-
Pattern erlaubt nachtraegliche Schaerfung; wenn D-2 binaer
ist und spaeter Severity gewollt ist, ist das ein additiver
Welle-Y-Schritt. Die C1-ADR muss aber von Anfang an eine
numerische `MetricsPort`-Kodierung gegen die bestehenden
Surface-Methoden (`increment` / `gauge` / `observe`)
festlegen, ohne eine neue Port-Methode einzufuehren, damit
der Accepted-ADR-0024-Vertrag nicht aufgeweicht wird.

**R4 — `GG-TERM-002`-/`GG-TERM-003`-Equality-Check ist
subtil**: Version, Plattformarchitektur, Konfiguration,
Startzeit im Simulationszeitmodell, aktivierte Adapter und
Eingabedaten sind heute nicht alle strukturiert in `RunMetadata`
verankert.
**Mitigation:** Welle-X-C0 erstellt eine vollstaendige
Equality-Matrix gegen `GG-TERM-002` und `GG-TERM-003` und
entscheidet den Speicherort (`RunMetadata`-Erweiterung oder
NEU `ReplayComparisonMetadata`). C1/ADR fixiert Pflichtfelder,
Hash-/Canonicalization-Regeln und Reject-Semantik fuer fehlende
oder abweichende Werte. C2 liefert parametrisierte Boundary-
Tests fuer mindestens Version, Konfiguration, Startzeit im
Simulationszeitmodell, aktivierte Adapter, Seed und `tick_ms`;
ein generischer Mismatch-Test reicht nicht. Die Tests tracen
auf den Determinismus-Invariant `GG-AR-P-008`
(`GG-SIM-001/002/003`, `GG-RT-002`); `GG-TERM-002`/`GG-TERM-003`
liefern nur die normative Feld-/Akzeptanz-Definition (n/a in der
Impl-Matrix, Lastenheft Z. 2203).

## 7. Cost-Estimate

Grobe Schaetzung (analog Welle 5c — Audit-Welle 2-3 Tage,
diese Substanz-Welle laenger):

- C0 (Slice-Doc): 0.5 Tag.
- C1 (NEU ADR Provisional): 0.5 Tag.
- C2 (Code-Substanz + Tests + Audit-Doku): 4-5 Tage.
  - NEU Zeitreihen-Driven-Port + Postgres-Adapter: 1-1.5 Tage.
  - NEU Replay-Driven-Port + Adapter: 1 Tag.
  - Core-Lifecycle-Surface + Terminal-Hook: 0.5 Tag.
  - Metrik-Emission + Schema: 0.5 Tag.
  - Integration-/Replay-Smoke-Familie inkl. Clean/Diverged/
    Equality/Idempotenz: 1 Tag.
  - Audit-Doku + Trigger-Move: 0.5 Tag.
- C3 + C4a/C4b: 0.5 Tag.

Summe: 6-7 Tage. Falls D-4 Option B (sub-sliced) ueber zwei
Wellen verteilt: gleicher Aufwand, zwei separate Closures und
kein `GG-MVP-002`-Statusflip vor der zweiten Closure.

## 8. References

- [`../open/036-safe-006-replay-diff-status-replay-source-integration.md`](../open/036-safe-006-replay-diff-status-replay-source-integration.md)
  — Trigger 036 Substanz-Skizze; wandert erst nach `done/`,
  wenn Status-Metrik, ReplaySource-Integration und
  `GG-SAFE-006`-Details belegt sind.
- [`../../../user/safe-005-006-fallback-determinism.md`](../../../user/safe-005-006-fallback-determinism.md)
  — Welle-5c-Audit; markiert die ⚠ partial Lücke fuer
  `GG-SAFE-006`; flippt erst bei belegtem integrierten
  `GG-SAFE-006`-Detailvertrag auf ✓ produktiv.
- [`../in-progress/roadmap.md §3 GG-MVP-002`](../in-progress/roadmap.md)
  — MVP-Abnahmescope-Tabelle; wird erst nach Zeitreihen-
  Persistenz- und Replay-E2E-Evidence auf ✓ produktiv geflippt.
- [`../../../../spec/lastenheft.md §3 GG-MVP-002`](../../../../spec/lastenheft.md)
  — Akzeptanz-Quelle (Z. 130-135).
- [`../../../../spec/architecture.md §4.2 + §8 + §15`](../../../../spec/architecture.md)
  — `TelemetrySinkPort` (§4.2 Z. 244 + §8 Z. 542);
  `ReplaySourcePort` (§4.2 Z. 248 + §8 Z. 544);
  `replay_diff_status`-Metrik (§15 Z. 820 + 823).
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md)
  — Schaerfungs-Pattern fuer NEU ADR (D-5).
- [`../done/M6-welle-5c.md`](../done/M6-welle-5c.md)
  Welle-5c — bringt `GG-SAFE-006`-Audit-Substanz mit
  Trigger-036-Anlage; Vor-Erbe fuer diesen Slice.
