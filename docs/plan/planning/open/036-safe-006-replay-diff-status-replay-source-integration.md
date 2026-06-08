# 036 — `GG-SAFE-006` Per-Lauf-Status-Marker + ReplaySource-Integration (partial Lücke)

**Status:** Open — partial Substanz-Lücke aus M6-Welle-5c-Audit
**Datum:** 2026-06-07
**Quelle:** M6-Welle-5c-C2 (SOLLTE-Items + IP/Netz-Beschraenkung;
siehe `docs/user/safe-005-006-fallback-determinism.md`).

---

## Lastenheft-Akzeptanz

`GG-SAFE-006` SOLLTE (Lastenheft Z. 1387-1393):

> Nichtdeterministische Simulationslaeufe SOLLTEN erkannt
> werden.
>
> Akzeptanz: Wenn Erkennung nichtdeterministischer Laeufe
> implementiert ist, meldet die Plattform Replay-Diff,
> volatile Felder, betroffene Ticks und Abweichungsklassifikation
> maschinenlesbar.

**Lastenheft-Traceability** (Z. 2292): „Replay-Diff-Status-
Markierung — **M3 mit Replay-Source-Integration**" (Status
`🔲 M3`).

**Architektur-Anforderung** (`spec/architecture.md §15`,
Z. 820 + 823):

- Z. 820: Observability-Metrik-Liste enthaelt
  `replay_diff_status`.
- Z. 823: „Replay-Diff-Status | maschinenlesbarer Statuswert
  pro Lauf | `GG-REPLAY-007`, `GG-SAFE-006`".

## Substanz-Stand (Welle-5c-Audit 2026-06-07)

- ✓ **Core-Diff-Algorithm produktiv** in
  `src/grid_gym/hexagon/core/replay/diff.py::diff_replay()`
  mit allen vier Lastenheft-Akzeptanz-Komponenten:
  - Replay-Diff → `tuple[ReplayDelta, ...]`.
  - Volatile Felder → `volatile_fields`-Parameter mit
    Default `_VOLATILE_FIELDS_DEFAULT =
    frozenset({"import_sequence"})`.
  - Betroffene Ticks → `ReplayDelta.tick`
    (`simulation_time // tick_ms`).
  - Abweichungsklassifikation → `ReplayDelta.classification`
    (`ReplayDeltaClassification` StrEnum mit
    `FACHLICH` / `VOLATIL`).
  - Test-Coverage: `tests/unit/hexagon/core/replay/
    test_diff.py` pinnt alle vier Komponenten.

- ✗ **Per-Lauf-Status-Marker `replay_diff_status` fehlt**:
  Architektur §15 (Z. 820 + 823) listet `replay_diff_status`
  als Pflicht-Metrik („maschinenlesbarer Statuswert pro
  Lauf"). Grep ueber `src/grid_gym/` nach
  `replay_diff_status` liefert null Treffer; die Metrik wird
  weder im Lauf-Lifecycle gesetzt noch ueber `MetricsPort`
  emittiert.

- ✗ **`ReplaySourcePort`-Verkabelung fehlt**: Lastenheft
  Z. 2292 nennt explizit „Replay-Diff-Status-Markierung —
  M3 mit Replay-Source-Integration". Die Driven-Port-
  Surface `ReplaySourcePort` ist in
  `spec/architecture.md §4.2 (GG-AR-PORT-DRN-006, Z. 248)`
  registriert und in `§8 Schnittstellen` (Z. 544)
  detailliert; ein produktiver Adapter und eine
  Lauf-Lifecycle-Verkabelung dieser Surface mit
  `diff_replay()` existieren heute noch nicht. Der
  `diff_replay()`-Algorithm ist eine standalone Pure-
  Function ohne Anbindung an den Lauf-Snapshot-Pfad.

Welle-5c-C2-Smoke-Test (`tests/integration/test_m6_welle_5c_
safe_005_006_compose_smoke.py::test_safe_006_diff_replay_
status_deferred_via_trigger_036`) ist deshalb `pytest.skip`
mit Pointer auf diesen Trigger.

## Erwartete Lieferung

Eigener Slice (M6-Welle-5c-Folge oder spaeter, z. B. M6-Welle-6
Deploy-Hardening-Beifang, oder M7+):

1. **`ReplaySourcePort`-Adapter + Lauf-Lifecycle-Verkabelung**:
   die Driven-Port-Surface `ReplaySourcePort` (architektur-
   seitig bereits definiert, siehe `GG-AR-PORT-DRN-006`)
   bekommt einen produktiven Adapter, der `ReplaySample`-
   Sequenzen vom persistierten Lauf-Snapshot als `expected`
   und vom Live-Lauf als `actual` liefert. Persistenz-Quelle
   ist **nicht** der `RunRepositoryPort` (dieser haelt heute
   ausschliesslich Lauf-Metadaten/Status, keine
   `ReplaySample`-/Snapshot-Daten); welcher Persistenz-Pfad
   (`SnapshotPort` oder ein neuer Snapshot-Adapter) den
   Sample-Strom liefert, entscheidet der Folge-Slice-C0.

2. **`replay_diff_status`-Metrik-Emission**: nach jedem
   `diff_replay()`-Aufruf ein maschinenlesbarer Statuswert
   pro Lauf auf den `MetricsPort`. Die Architektur §15
   (Z. 820 + 823) fordert ausschliesslich „maschinenlesbarer
   Statuswert pro Lauf"; **die konkrete Wertedomaene
   (z. B. binaer `clean`/`diverged`, ordinal mit Severity-
   Stufen, oder klassifikationsweise pro
   `ReplayDeltaClassification`) ist nicht spec-fixiert und
   gehoert in einen Schaerfungs-ADR im Folge-Slice-C0**
   (ADR-0011-Schaerfungs-Pattern; danach existiert ein
   Telemetrievertrag, an dem ein Smoke pinnen kann).
   Solange dieser ADR fehlt, definiert der Folge-Slice
   keinen Telemetrievertrag.

3. **Lauf-Lifecycle-Hook im Core-Spine**: die invariante
   Lauf-Spine (TickLoop-Abschluss bzw. ein Core-seitiger
   Lauf-Lifecycle-Hook) ruft `diff_replay()` mit den
   `ReplaySourcePort`-Sequenzen auf und emittiert die
   Metrik. Driving-Adapter (HTTP-Action-Router, WebSocket-
   Handler, UI-Routes, CLI) duerfen den Hook **nicht**
   tragen — andernfalls umgehen Nicht-HTTP-Pfade (Replay-
   Mode-CLI, Multi-Agent-Bus) den Per-Lauf-Status, und
   fachliche Replay-Status-Logik wandert in den Adapter
   (`GG-AR-P-003`-Verletzung — Simulationslogik kennt keine
   Kommunikationsadapter, Abhaengigkeiten zeigen nach innen;
   `GG-AR-P-007` stuetzt: Live + Replay teilen denselben Tick-
   Prozessor, der Hook gehoert in diesen Spine). Aktivierungs-
   Pfad:
   - Replay-Mode: `expected = persisted snapshot`, `actual =
     re-run`.
   - Live-Mode: `expected = previous run`, `actual = current
     run` — **nur** vergleichbar unter Wahrung der
     `GG-TERM-002`-Gleichheitsbedingungen (gleiche Version,
     gleiche Plattformarchitektur, gleiche Eingabedaten,
     gleicher `scenario_hash`, gleiche Konfiguration,
     gleicher Seed, gleiche `tick_ms`). Der Folge-Slice
     verankert die Metadata-Equality-Checks als Vorbedingung;
     wer ohne Equality vergleicht, klassifiziert legitime
     Lauf-Unterschiede faelschlich als nichtdeterministisch
     (Boundary-Test-Pflicht im Folge-Slice).

4. **NEU Integration-Smoke**: belegt End-to-End, dass eine
   bewusst eingefuehrte Tick-Differenz zwischen zwei
   Sample-Quellen ueber `ReplaySourcePort` (also dem im
   Folge-Slice-C0 festgelegten Snapshot-Persistenz-Pfad,
   **nicht** ueber `RunRepositoryPort` — der haelt nur
   Lauf-Metadaten/Status) als Divergenz-Statuswert auf
   `MetricsPort` emittiert wird. Der konkrete
   Statuswert-Vergleich richtet sich nach dem in
   Liefer-Punkt 2 verankerten Schaerfungs-ADR.

5. **Audit-Doku-Update**: nach Implementation wandert die
   `GG-SAFE-006`-Zeile in `safe-005-006-fallback-determinism.md`
   von ⚠ partial auf ✓ produktiv; Trigger 036 wandert nach
   `done/` mit dem aufloesenden Slice.

## Aktivierungs-Bedingung

- **Compliance-Druck oder Stakeholder-Bedarf**: heute keine
  konkrete Aktivierung; `GG-SAFE-006` ist `SOLLTE` und der
  Core-Diff-Algorithm reicht fuer Reviewer-getriebene
  Replay-Vergleiche.
- **CI-Bench-Determinismus-Drift**: falls die Welle-4b-a-
  Bench-Suite oder ein anderer CI-Sensor `FACHLICH`-Deltas
  zwischen zwei Laeufen produziert, ist die Aktivierung
  unmittelbar (Drift-Diagnose-Werkzeug).
- **`GG-REPLAY-004..006`-Aktivierung** (Replay-Diff-Status
  / Telemetrie-Replay-Monitoring, Status `🔲 M3` per
  Lastenheft-Traceability Z. 2269): die offene M3-Familie
  `GG-REPLAY-004..006` adressiert den gleichen
  Lauf-Lifecycle-Monitoring-Pfad und kann den Folge-Slice
  als Mitziehe-Substanz buendeln. `GG-REPLAY-007` ist
  bereits `✓ M1+M2` (Lastenheft-Traceability Z. 2270 ueber
  `diff_replay` + Trigger-013-Closure) und nicht der
  Aktivierungs-Anker.

## Anti-Scope

- **Keine `diff_replay`-Algorithm-Erweiterung**: die vier
  Akzeptanz-Komponenten sind im Core-Algorithm ✓ vollstaendig
  (siehe Welle-5c-Audit). Trigger 036 deckt **ausschliesslich**
  die Lauf-Lifecycle-Verankerung + Metrik-Emission.
- **Keine NEU Klassifikations-Kategorie**: `FACHLICH` /
  `VOLATIL` reicht; eine differenziertere Klassifikation
  (z. B. `time-ordering` vs `random-seed-drift`) ist nicht
  von der Lastenheft-Akzeptanz gefordert und wuerde Scope-
  Inflation einbringen.
- **Kein Replay-Roundtrip-Tool** (z. B. `make replay-diff`-
  Target): Trigger 036 zielt auf die Substanz-Verankerung
  im Hexagon-Kern; ein User-facing Tool waere `GG-REPLAY-007`-
  Substanz, nicht `GG-SAFE-006`.

## Bezug

- [`docs/user/safe-005-006-fallback-determinism.md`](../../../user/safe-005-006-fallback-determinism.md)
  — Audit-Doku mit Status-Verlinkung auf diesen Trigger.
- M6-Welle-5c-Slice-Doc (anlegende Welle) — lebt unter
  `in-progress/` bis zur Self-Close-Folge, dann unter
  `done/M6-welle-5c.md` (Pfad nicht hart gelinkt, damit
  `make docs-check` den Trigger nicht an die Move-Reihenfolge
  bindet).
- [`../../adr/0041-performance-bench-pattern.md`](../../adr/0041-performance-bench-pattern.md)
  §2.2 — Doppel-Akzeptanz fuer `GG-RT-004` mit Replay-Diff;
  liefert den Pattern-Vorbild fuer den binaeren Diff-Vergleich
  (auch ein Aufrufer von `diff_replay`).
- `tests/unit/hexagon/core/replay/test_diff.py` — Test-
  Coverage des Core-Algorithm; bleibt als Basis-Sensor
  bestehen.
- `spec/architecture.md §15` (Z. 820 + 823) — Architektur-
  Vorgabe fuer `replay_diff_status`-Metrik und
  maschinenlesbaren Statuswert pro Lauf.
