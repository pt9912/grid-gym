# ADR 0048 — ReplaySnapshotPort Replay-Snapshot-Rekonstruktion (M7 Welle 1b-a)

**Status:** Accepted — gezogen 2026-06-12 mit M7-Welle-X-C1
(M7-Closure-Welle). Provisional-Schritt 2026-06-09 (direkter
`Proposed → Provisional`-Sprung mit M7-Welle-1b-a-C1).
**Datum:** 2026-06-09
**Status geaendert am:** 2026-06-09 — `Proposed → Provisional`;
2026-06-12 — `Provisional → Accepted` (M7-Welle-X-Closure).
**Bezug:**

- [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
  — Lifecycle-/Status-Pfad.
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) — Schaerfung-
  ohne-Supersedes-Pattern (Form-Anker; ADR 0048 schaerft das
  Driven-Port-/Postgres-Lese-Pattern additiv).
- [`ADR 0047`](0047-telemetry-sink-timeseries-persistence.md) —
  `TelemetrySinkPort`-Zeitreihen-Persistenz (Welle 1a); liefert
  die `telemetry_points`-Tabelle + den byte-stabilen `TEXT`-
  `value`-Vertrag, aus dem ADR 0048 liest.
- [`ADR 0039`](0039-run-control-and-status-tracking.md) —
  `RunRepositoryPort` als Driven-Port (Form-Vorbild fuer den
  Driven-Lese-Port + `connection_factory`-Adapter-Pattern).
- [`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md)
  §2.9 — kanonische `Decimal`-/Byte-Stabilitaets-Konvention.
- [`M7-welle-1b-a.md`](../planning/done/M7-welle-1b-a.md)
  — Slice-Doc (Decisions 1b-a-D-0..D-6); ADR 0048 fixiert
  D-2/D-3/D-4.
- [`M7-welle-1.md`](../planning/done/M7-welle-1.md) —
  GG-MVP-002-Gruppenplan (D-1/D-1.1).
- [Trigger 036](../planning/done/036-safe-006-replay-diff-status-replay-source-integration.md)
  — Replay-Lifecycle (Welle 1b-b, ADR 0049) konsumiert den hier
  rekonstruierten `ReplaySample`-Strom.

---

## 1. Kontext

`GG-MVP-002` (E2E-Szenario + deterministisches Replay) ist im
**partial**-Stand. Welle **1a** ([ADR 0047](0047-telemetry-sink-timeseries-persistence.md))
hat die erste Lücke geschlossen — produktive Telemetrie-Zeitreihen-
Persistenz (`telemetry_points`, byte-stabiler `TEXT`-`value`).
Offen bleibt die **End-to-End-Replay-Verkabelung**:
`diff_replay()` ist produktiv (Welle-5c-Audit), aber es fehlt
(a) eine Persistenz-Quelle, die `ReplaySample`-Sequenzen aus dem
persistierten Lauf liefert, und (b) der Lauf-Lifecycle-Hook, der
`diff_replay()` aufruft + `replay_diff_status` emittiert.

Die [`M7-welle-1.md`](../planning/done/M7-welle-1.md)-Sub-
Slicing-Entscheidung (D-4 = B) schneidet Welle **1b** in **1b-a**
(dieser ADR — Persistenz-Lese-Substanz) + **1b-b** (Lifecycle-
Hook + `replay_diff_status` + `GG-TERM-002/003`-Preflight,
ADR 0049; 1b-a-D-1). ADR 0048 deckt ausschliesslich die
`ReplaySnapshotPort`-Lese-/Rekonstruktions-Seite ab —
**kein Core-Change** (reiner Driven-Adapter).

**Code-Ist-Stand (verifiziert):**

- `ReplaySample`-Domain (`hexagon/core/domain/replay.py:31-52`,
  `GG-REPLAY-001/002/003`): Frozen-Dataclass, Felder `timestamp`
  (`str`), `simulation_time` (`int`), `device_id`, `metric`,
  `value` (`Decimal`), `unit`, `import_sequence` (`int`).
- `diff_replay()` (`hexagon/core/replay/diff.py:63`): konsumiert
  `Iterable[ReplaySample]` `expected`/`actual`, keyword-only
  `tick_ms: int = 1000`, `volatile_fields` (Default
  `frozenset({"import_sequence"})`); liefert
  `tuple[ReplayDelta, ...]`.
- `telemetry_points` (1a): Spalten `id` (Surrogat-PK, aufsteigend
  = Insertion-Order), `run_id`, `tick`, `simulation_time`,
  `device_id`, `metric`, `value` (`TEXT`, `str(Decimal)`),
  `unit`, `quality`, `source`, `sequence`. `TelemetrySinkPort.
  read_ordered` liest `WHERE run_id = %s ORDER BY id`.
- **`TelemetryPoint` fuehrt KEINEN Original-`timestamp`-String**
  (nur `tick` + `simulation_time`) — das ist die D-1.1-Lücke,
  die ADR 0048 §2.2 final aufloest.
- **Kein** `ReplaySourcePort`/`ReplaySnapshotPort` (grep);
  nur Forward-Pointer-Docstring in ADR 0047 §2.1.

---

## 2. Entscheidung

ADR 0048 fixiert drei Punkte fuer die Welle-1b-a-Replay-Snapshot-
Rekonstruktion.

### §2.1 `ReplaySnapshotPort` (Driven-Protocol)

NEU `hexagon/ports/driven/replay_snapshot.py` mit einem
read-only-Driven-Vertrag:

```python
class ReplaySnapshotPort(Protocol):
    def read_samples(self, run_id: str) -> tuple[ReplaySample, ...]: ...
```

- **`read_samples`** rekonstruiert die `ReplaySample`-Sequenz
  eines Laufs in **deterministischer Reihenfolge** (Insertion-
  Order, §2.2) — die Form, die `diff_replay()` als
  `expected`/`actual` konsumiert.
- Der Port nutzt den **Core-Domain**-`ReplaySample`
  (`core.domain.replay`), nicht einen Adapter-Typ — AC-PORTS-NO-
  OUT-konform (Praezedenz `TelemetrySinkPort.read_ordered →
  core.domain.telemetry`).
- **Getrennt von `TelemetrySinkPort`** (kein Methoden-Anbau):
  der Sink persistiert `TelemetryPoint`s; der Snapshot-Port
  rekonstruiert `ReplaySample`s — unterschiedliche Domain-Typen,
  unterschiedliche Konsumenten (1b-a-D-2). **NICHT** `SnapshotPort`
  (`GG-AR-PORT-DRV-005`, **Driving**, ADR 0015) wiederverwenden:
  eine Persistenz-Quelle aus einer Driving-Surface zu ziehen
  waere ein Schichten-Twist (Gruppenplan D-1).

### §2.2 Snapshot→`ReplaySample`-Rekonstruktion + Timestamp-Vertrag

Der `PostgresReplaySnapshotAdapter`
(`adapters/driven/persistence_postgres/
replay_snapshot_repository.py`) liest `telemetry_points`
(`WHERE run_id = %s ORDER BY id`, gleiche Insertion-Order-Basis
wie `read_ordered`) und mappt **pro Zeile**
`TelemetryPoint`-Substanz → `ReplaySample`:

| `ReplaySample` | Quelle | Hinweis |
| -------------- | ------ | ------- |
| `simulation_time` | `telemetry_points.simulation_time` | direkt. |
| `device_id` | `device_id` | direkt. |
| `metric` | `metric` | direkt. |
| `unit` | `unit` | direkt. |
| `value` | `Decimal(value)` aus `TEXT` | verlustfreier Round-Trip (1a §2.4). |
| `import_sequence` | **0-basierte Enumeration ueber die `id`-Order** | deterministischer Tie-Break (`GG-REPLAY-003`). |
| `timestamp` | **`str(simulation_time)`** | Derivations-Vertrag, siehe unten. |

**Timestamp-Derivations-Vertrag (die D-1.1-Lücke):**
`ReplaySample.timestamp` wird **deterministisch aus
`simulation_time` abgeleitet** (`timestamp =
str(simulation_time)`) — **NICHT** aus `RunMetadata.started_at`
(Wall-Clock) oder einem anderen lauf-variablen Wert.

- **Begruendung:** `GG-REPLAY-002` definiert `timestamp` als
  „unveraendert gespeicherten" Original-Zeitstempel. Fuer einen
  **simulations-erzeugten** (nicht extern aufgezeichneten) Lauf
  gibt es keinen externen Original-Stempel — der kanonische
  `simulation_time`-String **ist** der stabile Original-Wert.
- **Determinismus-Konsequenz:** Zwei Laeufe desselben Szenarios
  (gleicher Seed/`tick_ms`/Szenario) erzeugen identische
  `simulation_time`-Folgen → identische `timestamp`-Werte →
  leeren Replay-Diff (`GG-MVP-002`-Akzeptanz „byte-identische
  kanonische Ergebnisdateien oder leerer Replay-Diff"). Eine
  Wall-Clock-Ableitung wuerde den Self-Replay byte-instabil
  machen und den Determinismus-Beleg brechen.
- **`import_sequence` ist diff-volatil** (`diff_replay`-Default
  `volatile_fields = {"import_sequence"}`): es dient nur dem
  Tie-Break/der Ordnung, nicht dem fachlichen Vergleich. Die
  0-basierte `id`-Order-Enumeration ist trotzdem **deterministisch**
  identisch ueber zwei Laeufe.

### §2.3 Keine neue Tabelle / keine neue Migration

ADR 0048 fuegt **keine** Alembic-Migration hinzu. Der
`ReplaySnapshotPort`-Adapter liest die bestehende 1a-Tabelle
`telemetry_points`; alle `ReplaySample`-Substanzen liegen dort
(`timestamp` **abgeleitet**, nicht gespeichert; §2.2). Der
Alembic-Head bleibt `0002_create_telemetry_points`.

**Begruendung:** Gruppenplan-D-1-Option-A nannte „eigene Tabelle";
die R1-Mitigation hielt explizit fest: „Falls `ReplaySample`-
Sequenzen schon in der Snapshot-Envelope-Sektion liegen,
entfaellt die zweite Migration." Da 1a's `telemetry_points`-
Schema die Substanz traegt und der Timestamp deterministisch
ableitbar ist, ist eine separate Replay-Snapshot-Tabelle
unnoetig. Das haelt 1b-a schmal und vermeidet eine zweite
Migrations-Kette.

**Hexagonal-Reinheit:** Der Core importiert nur das
`ReplaySnapshotPort`-Protocol; der `PostgresReplaySnapshot
Adapter` traegt die `psycopg`-Abhaengigkeit (AC-NO-FW gewahrt,
Praezedenz `telemetry_sink_repository`). Die Verdrahtung in einen
Lauf-Lifecycle ist **Welle 1b-b** (ADR 0049) — 1b-a liefert nur
Port + Adapter + Smoke, **kein** `TickLoop`-Kwarg. `make
arch-check` (AC-PORTS-NO-OUT + AC-NO-FW) verifiziert in C2, dass
`hexagon/core/**` unveraendert bleibt.

---

## 3. Begruendung

- **Zweite `GG-MVP-002`-Lücke vorbereiten.** Ohne eine Persistenz-
  Quelle fuer `ReplaySample`-Sequenzen kann der 1b-b-Lifecycle-
  Hook `diff_replay()` nicht mit `expected`-Samples speisen.
- **Driven-Lese-Port-Konsistenz.** Der Snapshot-Port spiegelt das
  `TelemetrySinkPort.read_ordered`-Lese-Pattern (Driven-Protocol +
  Postgres-Adapter via `connection_factory` + Core-Domain-Typ).
  Kein neues Architektur-Konzept.
- **Timestamp-Determinismus ist Vertrags-kritisch.** Die
  `simulation_time`-Ableitung (statt Wall-Clock) ist die
  Voraussetzung fuer den byte-stabilen Self-Replay — die
  zentrale `GG-MVP-002`-Akzeptanz.
- **Scope-Disziplin via No-New-Table.** Die telemetry_points-
  Wiederverwendung haelt 1b-a frei von Core-Change + zweiter
  Migration; der harte Teil (TickLoop-Terminal-Naht) bleibt
  isoliert in 1b-b.

---

## 4. Reichweite

- NEU `hexagon/ports/driven/replay_snapshot.py` +
  `adapters/driven/persistence_postgres/
  replay_snapshot_repository.py` (C2).
- NEU `tests/integration/test_mvp_002_replay_snapshot_smoke.py`
  (C2): rekonstruiert `ReplaySample` aus einem persistierten
  Demo-Lauf; pinnt Sortierung, Timestamp-Derivation,
  `import_sequence`-Tie-Break, `value`-Round-Trip + Zwei-Lauf-
  Determinismus (`diff_replay()` leer modulo `run_id`).
- ADR-Index Aktive-ADRs-Tabelle NEU ADR-0048-Zeile +
  Drift-Sync der ADR-0047-Bezüge (0048 → 0049 fuer die
  Lifecycle-Substanz; ADR 0047 ist `Provisional`).
- **Unberuehrt:** `telemetry_points`-Schema (1a, read-only),
  `diff_replay()`-Core, `TickLoop` (Wiring ist 1b-b),
  `TelemetrySinkPort`, `RunRepositoryPort`/`RunMetadata`
  (keine Migration). Keine `ReplaySample`-Domain-Aenderung.

---

## 5. Lieferung

Lieferplan, Commit-Hashes + Verifikations-Gates leben in der
Slice-Doc [`M7-welle-1b-a.md`](../planning/done/M7-welle-1b-a.md)
(C2: Code-Substanz; C2-Verifikation inkl. `make test-integration`-
Rekonstruktions-Smoke). Status-Pfad (`Proposed → Provisional →
Accepted`): siehe Status-Header; `Accepted` gezogen 2026-06-12
mit M7-Welle-X-C1 (gebuendelt mit ADR 0047 + ADR 0049).

---

## 6. Konsequenzen

- **Positiv:** liefert die deterministische `ReplaySample`-Lese-
  Surface, auf die der 1b-b-Lifecycle-Hook `diff_replay()`
  aufsetzt — ohne Core-Change in 1b-a.
- **Positiv:** keine zweite Migration; Alembic-Head bleibt
  `0002`. Schmaler Slice.
- **Neutral (Timestamp-Semantik):** `timestamp = str(simulation_
  time)` ist fuer simulations-erzeugte Laeufe der kanonische
  Original-Wert. Falls eine spaetere Welle **externe** Replay-
  Quellen mit echtem aufgezeichnetem Original-Stempel braucht,
  ist das eine additive ADR-0011-Schaerfung (Zusatzspalte in
  `telemetry_points` oder eigene Tabelle), **kein** Bruch dieses
  Vertrags.
- **Neutral (Lese-Last):** `read_samples` liest den vollstaendigen
  Lauf in den Speicher (wie `read_ordered`). Fuer Demo-/Abnahme-
  Skala unkritisch; ein Streaming-/Paginierungs-Lese-Pfad waere
  eine additive Schaerfung bei Last-Druck.
- **Neutral (Adapter-Kopplung):** der Snapshot-Adapter liest
  dieselbe `telemetry_points`-Tabelle wie der Sink-Adapter,
  bleibt aber ein eigener Driven-Port (Vertrags-Trennung §2.1).
  Die geteilte Sortier-Invariante (`ORDER BY id`) ist die
  einzige Kopplung und in beiden Adaptern identisch verankert.

---

## 7. Nicht Gegenstand dieser ADR

- **Core-Spine-Lifecycle-Hook + `diff_replay()`-Aufruf +
  `replay_diff_status`-Metrik** — Welle 1b-b, **ADR 0049**.
- **`GG-TERM-002/003`-MVP-E2E-Replay-Preflight** (5 vorhandene
  `RunMetadata`-Felder) — Welle 1b-b, ADR 0049.
- **Volle `GG-TERM-002/003`-Equality-Matrix** (`platform_arch`,
  `enabled_adapters`, `sim_start_time`, `config_hash`) —
  Carveout [Trigger 038](../planning/open/038-gg-term-002-003-full-equality-matrix.md)
  (1b-a-D-6).
- **`ReplaySnapshotPort`-Wiring in den Lauf-Lifecycle** — Welle
  1b-b (1b-a liefert nur Port + Adapter + Smoke).
- **Externe Replay-Quellen mit echtem Original-`timestamp`** —
  spaetere additive ADR-0011-Schaerfung.
- **Query-/Export-/Streaming-Lese-API** ueber `read_samples`
  (Smoke-Bedarf) hinaus — eigener spaeterer Scope.
