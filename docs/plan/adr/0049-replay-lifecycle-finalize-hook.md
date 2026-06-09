# ADR 0049 — Replay-Lifecycle: Terminal-Hook + `replay_diff_status` + GG-TERM-Preflight (M7 Welle 1b-b)

**Status:** Provisional — direkter `Proposed → Provisional`-
Sprung (dieser Commit, M7-Welle-1b-b-C1).
**Datum:** 2026-06-09
**Status geaendert am:** 2026-06-09 — `Proposed → Provisional`.
**Bezug:**

- [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
  — Lifecycle-/Status-Pfad.
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) — Schaerfung-
  ohne-Supersedes-Pattern (Form-Anker; ADR 0049 schaerft den
  TickLoop-Spine + Observability-Pfad additiv).
- [`ADR 0024`](0024-observability-port-trio.md) — `MetricsPort`-/
  `LogPort`-Vertrag (`replay_diff_status`-Gauge + SAFE-006-
  Detail-Log nutzen die bestehenden Surface-Methoden).
- [`ADR 0039`](0039-run-control-and-status-tracking.md) —
  `RunRepositoryPort` + `control_state`/`request(...)`-Lifecycle;
  ADR 0049 ergaenzt eine Terminal-Naht (`finalize()`), ohne die
  Transition-Matrix zu aendern.
- [`ADR 0047`](0047-telemetry-sink-timeseries-persistence.md) —
  Zeitreihen-Persistenz (1a); liefert die persistierten Laeufe.
- [`ADR 0048`](0048-replay-snapshot-port-reconstruction.md) —
  `ReplaySnapshotPort` (1b-a); liefert `expected`/`actual`-
  `ReplaySample`-Sequenzen.
- [`M7-welle-1b-b.md`](../planning/in-progress/M7-welle-1b-b.md)
  — Slice-Doc (Decisions 1b-b-D-0..D-9); ADR 0049 fixiert
  D-1..D-6.
- [`M7-welle-1.md`](../planning/in-progress/M7-welle-1.md) —
  GG-MVP-002-Gruppenplan (D-2/D-3).
- [Trigger 036](../planning/open/036-safe-006-replay-diff-status-replay-source-integration.md)
  — wird mit 1b-b-C3 aufgeloest (`done/`).
- [Trigger 038](../planning/open/038-gg-term-002-003-full-equality-matrix.md)
  — volle GG-TERM-Matrix (Carveout).
- [Trigger 039](../planning/open/039-api-replay-trigger-surface.md)
  — oeffentliche API-Replay-Bedienung (Carveout).

---

## 1. Kontext

`GG-MVP-002` (E2E-Szenario + deterministisches Replay) ist im
**partial**-Stand. Welle **1a** ([ADR 0047](0047-telemetry-sink-timeseries-persistence.md))
lieferte die Zeitreihen-Persistenz, Welle **1b-a**
([ADR 0048](0048-replay-snapshot-port-reconstruction.md)) den
`ReplaySnapshotPort`, der `ReplaySample`-Sequenzen rekonstruiert.
ADR 0049 (Welle 1b-b) schliesst die **Lauf-Lifecycle-
Verkabelung** + flippt `GG-MVP-002`.

**Code-Ist-Stand (verifiziert):**

- **Kein Core-Terminal-Seam.** `TickLoop` setzt `"completed"`
  nie automatisch; Terminierung ist externes `request("stop")` →
  `"stopped"` (`_CONTROL_ACTION_TRANSITIONS` kennt nur
  `pause`/`resume`/`stop`). `tick()` wirft bei terminalem State.
  Kein `finalize()`/End-of-Run-Hook.
- **Run-End-Naht im Driver:** `DemoTickLoopDriver._tick_forever()`
  verlaesst den Loop genau einmal bei terminalem `control_state`.
- **`diff_replay(expected, actual, *, tick_ms=1000,
  volatile_fields=None) -> tuple[ReplayDelta, ...]`** (Pure-
  Function; `volatile_fields`-Default `{"import_sequence"}`).
- **`ReplayDelta`** traegt alle vier `GG-SAFE-006`-Detailfelder
  (`path`/`expected`/`actual`, `tick`, `device_id`,
  `classification`).
- **`MetricsPort.gauge(name, value, *, attributes)`** +
  **`LogPort`** produktiv (ADR 0024); `TickLoop._obs_gauge`
  emittiert bereits mit `attributes={"run_id": …}`.
- **`RunMetadata`** (frozen) traegt strukturiert `scenario_hash`,
  `schema_version`, `seed`, `tick_ms`, `tool_version`
  (+ `started_at`/`ended_at` heute leer/ungenutzt).
- **Keine Referenz-Lauf-Verknuepfung** existiert (kein
  `ReplaySource`/`reference_run_id`/Replay-Feld).

---

## 2. Entscheidung

ADR 0049 fixiert sechs Punkte fuer den Welle-1b-b-Replay-
Lifecycle.

### §2.1 Core-`TickLoop.finalize()`-Terminal-Naht (1b-b-D-1)

NEU **idempotente** Core-Methode `TickLoop.finalize()`. Der
`DemoTickLoopDriver` (und der Lifespan-`stop()`-Pfad) ruft sie am
Loop-Ende; der **Driver traegt KEINE Diff-Logik** — `diff_replay()`,
die `replay_diff_status`-Emission und die `GG-SAFE-006`-Detail-
Evidence sitzen **im Core-Spine**.

- **Idempotenz:** ein `_finalized`-Flag stellt sicher, dass
  Mehrfachaufruf (Driver-Loop-Exit **und** Lifespan-`stop()`) genau
  **eine** Emission erzeugt.
- **`control_state` bleibt unveraendert:** `finalize()` setzt
  `"completed"` **nicht** — `"completed"` bleibt semantisch
  vorhanden, aber ohne Core-Auto-Transition (ein Auto-`completed`
  braeuchte ein Tick-Budget/Szenario-Ende, das es nicht gibt —
  out-of-scope). `finalize()` laeuft **nach** dem terminalen
  `control_state` (der Lauf ist gestoppt).
- **Begruendung (GG-AR-P-003/GG-AR-P-007):** Live + Replay teilen
  denselben Tick-Prozessor; die Replay-Diff-Orchestrierung gehoert
  in den Spine, nicht in einen Driving-Adapter — sonst diffte ein
  headless-Runner (Abnahme-CLI `GG-MVP-003`) ohne den Driver
  nicht. Der Adapter **triggert**, der Core **entscheidet**.

### §2.2 Referenzlauf-Bindung (1b-b-D-2)

NEU keyword-only Core-Kwargs `replay_snapshot:
ReplaySnapshotPort | None = None` + `replay_reference_run_id:
str | None = None` (beide `None` → `finalize()` no-op; konsistent
mit `run_repository`/`telemetry_sink`-Pattern). Bei gesetzter
Bindung:

```text
expected = replay_snapshot.read_samples(replay_reference_run_id)
actual   = replay_snapshot.read_samples(run_id)
```

- **KEIN Self-Replay gegen dieselbe `run_id`** als Determinismus-
  Beleg (tautologisch leer — nur Read-/Idempotenz-Test). Der
  Beleg braucht **zwei getrennte Laeufe**.
- **KEINE implizite Auto-Auswahl** („letzter passender Lauf") —
  mehrdeutig + schlecht auditierbar.
- Die Bindung ist in 1b-b **Runtime/Test/Demo-intern** (Core-
  Kwarg); die **oeffentliche API-Replay-Bedienung** (POST /runs
  `replay_of` + `RunMetadata`-Spalte + Migration) ist
  [Trigger 039](../planning/open/039-api-replay-trigger-surface.md)
  (§7).

### §2.3 `GG-TERM-002/003`-MVP-Preflight (1b-b-D-3)

Vor `diff_replay()` prueft `finalize()` die Gleichheit der **5
bereits strukturierten** `RunMetadata`-Felder von Referenz- und
aktuellem Lauf (via `run_repository.get_by_id(...)`):
`scenario_hash`, `schema_version`, `seed`, `tick_ms`,
`tool_version`.

- **Bei Ungleichheit eines Felds → Reject vor dem Diff:** **kein**
  `replay_diff_status` (kein valider Vergleich), stattdessen ein
  strukturierter `log_port`-Record mit dem/den abweichenden
  Feld(ern).
- **Begruendung:** ein Replay-Diff zwischen ungleich-
  konfigurierten Laeufen ist fachlich bedeutungslos; die binaere
  Metrik bleibt nur fuer **valide** Vergleiche definiert (§2.4).
- **C2-Pin:** **per-Feld**-Boundary-Tests (ein generischer
  Mismatch reicht nicht).
- Die **volle** `GG-TERM-002/003`-Matrix (`platform_arch`,
  `enabled_adapters`, `sim_start_time`, `config_hash`) ist
  **NICHT** Gegenstand — Carveout
  [Trigger 038](../planning/open/038-gg-term-002-003-full-equality-matrix.md)
  (1b-a-D-6). Das ist eine bewusste Teil-Operationalisierung von
  `GG-TERM-002/003`, nicht der volle Vertrag.

### §2.4 `replay_diff_status`-Kodierung (1b-b-D-4)

Bei preflight-validem Vergleich emittiert `finalize()`:

```python
metrics_port.gauge(
    "replay_diff_status",
    1.0 if not fachlich_deltas else 0.0,
    attributes={
        "run_id": run_id,
        "reference_run_id": replay_reference_run_id,
        "status": "clean" if not fachlich_deltas else "diverged",
    },
)
```

- **Binaer:** `1.0` = clean (kein **fachlicher** Delta) / `0.0` =
  diverged (≥1 fachlicher Delta). Volatile Deltas
  (`import_sequence`) zaehlen **nicht** als Divergenz.
- **Nur bei preflight-validem Vergleich** emittiert — die Metrik
  bedeutet stets „ein valider Replay-Vergleich lief und war
  clean/diverged".
- **Keine neue `MetricsPort`-Methode** (ADR-0024-Vertrag gewahrt);
  Severity-Stufen waeren additive ADR-0011-Schaerfung.

### §2.5 `GG-SAFE-006`-Detail-Evidence (1b-b-D-5)

`finalize()` emittiert die `ReplayDelta`-Details maschinenlesbar
via `log_port` — alle vier `GG-SAFE-006`-Akzeptanzfelder:
`path`/`expected`/`actual` (Replay-Diff), `tick` (betroffene
Ticks), `device_id`, `classification` (`fachlich`/`volatil`). Die
Felder liegen **bereits** in `ReplayDelta`; ADR 0049 liefert den
**integrierten Lifecycle-Pfad**, der sie emittiert. Der Divergenz-
Smoke pinnt alle vier Felder → `docs/user/safe-005-006-fallback-
determinism.md` flippt `GG-SAFE-006` ⚠ → ✓ produktiv +
Trigger 036 → `done/`.

### §2.6 Ausfuehrungsmodell (1b-b-D-6)

`finalize()` laeuft **synchron**. Der Diff ist durch die Lauf-
Laenge beschraenkt; fuer Demo-/Abnahme-Skala unkritisch. Eine
asynchrone Entkopplung (mit explizitem Lifecycle-/Drain-Vertrag,
**kein** Fire-and-forget) ist eine additive ADR-0011-Schaerfung
bei Last-Druck. Die Lauf-Status-Transition blockiert nicht auf
unbounded Diff-Arbeit, weil `finalize()` nach dem terminalen
`control_state` laeuft.

### §2.7 Hexagonal-Reinheit

Der Core haelt nur Driven-Port-**Protokolle** als keyword-only-
Kwargs (`replay_snapshot`, `metrics_port`, `log_port`,
`run_repository`) — Praezedenz exakt wie `telemetry_sink`
(ADR 0047 §2.3). Keine Adapter-/Library-Importe im Core; die
`ReplaySnapshotPort.read_samples`-Rueckgabe ist Core-Domain
(`ReplaySample`, AC-PORTS-NO-OUT). `make arch-check`
(AC-HEXAGON-PURE + AC-NO-FW + AC-PORTS-NO-OUT) verifiziert in C2.

---

## 3. Begruendung

- **`GG-MVP-002` schliessen.** Der integrierte Replay-Lifecycle
  ist die zweite (letzte) `GG-MVP-002`-Lücke; mit ihm flippt die
  Lastenheft-Akzeptanz „laesst sich deterministisch replayen".
- **Spine statt Adapter (GG-AR-P-003/007).** Die Diff-/Metrik-/
  Evidence-Orchestrierung im Core haelt Live + Replay + headless
  konsistent.
- **Determinismus-Vorbedingung respektieren.** Der Preflight
  verhindert bedeutungslose Diffs ungleich-konfigurierter Laeufe;
  die byte-stabile Persistenz (ADR 0047 §2.4) + deterministische
  Rekonstruktion (ADR 0048 §2.2) garantieren, dass zwei gleich-
  konfigurierte Laeufe einen leeren Diff erzeugen.
- **Schaerfung ohne Supersedes (ADR 0011).** ADR 0039
  (`control_state`/`request`) + ADR 0024 (`MetricsPort`/`LogPort`)
  bleiben textlich unveraendert; ADR 0049 ergaenzt eine Terminal-
  Naht + einen Metrik-/Log-Emissions-Pfad additiv.

---

## 4. Reichweite

- NEU `TickLoop.finalize()` + Kwargs `replay_snapshot` +
  `replay_reference_run_id` (`hexagon/core/simulation/
  tick_loop.py`); `build_tick_loop`-Symmetrie (`scenario/
  loader.py`) (C2).
- Driver triggert `finalize()` am Loop-Exit (`_tick_loop_
  driver.py`); Demo-Wiring (`_demo_scenario_setup.py`) (C2).
- NEU `InMemoryReplaySnapshot` (`persistence_inmemory/`) (C2).
- NEU `docs/user/replay-determinism-e2e.md` +
  Flip `docs/user/safe-005-006-fallback-determinism.md` +
  Reaktivierung des Trigger-036-Skip-Smokes (C2).
- ADR-Index NEU ADR-0049-Zeile (C1).
- **Unberuehrt:** `diff_replay()`-Algorithm (nur aufgerufen),
  `ReplaySample`/`ReplayDelta`-Domain, `control_state`-Transition-
  Matrix (ADR 0039), `ReplaySnapshotPort`/`telemetry_points`
  (ADR 0047/0048).

---

## 5. Lieferung

Lieferplan, Commit-Hashes + Verifikations-Gates leben in der
Slice-Doc [`M7-welle-1b-b.md`](../planning/in-progress/M7-welle-1b-b.md)
(C2: Code-Substanz; C2-Verifikation inkl. `make test-integration`-
Zwei-Lauf-Replay-Lifecycle-Smoke). Status-Pfad (`Proposed →
Provisional → Accepted`): `Accepted` mit M7-Welle-X-Closure
(gebuendelt mit ADR 0047 + ADR 0048).

---

## 6. Konsequenzen

- **Positiv:** `GG-MVP-002` flippt produktiv; `GG-SAFE-006`
  flippt ⚠ → ✓; Trigger 036 schliesst.
- **Positiv:** der Core-Spine-Hook gilt fuer **jeden** `TickLoop`-
  Lauf (Live, Demo, headless) — kein Driver-Coupling.
- **Neutral:** der Core haelt zwei weitere optionale Driven-/
  Runtime-Kwargs (`replay_snapshot`, `replay_reference_run_id`);
  `None`-default haelt bestehende Pfade no-op.
- **Neutral (Observability):** preflight-Reject emittiert **kein**
  `replay_diff_status` (nur valide Vergleiche) — ein Beobachter
  unterscheidet „kein Replay konfiguriert" nicht von „Preflight
  rejected" ohne den `log_port`-Record (1b-b-R3; Smoke pinnt den
  Reject-Log).
- **Neutral (Demo):** der Demo-Lauf hat keine Referenz →
  `finalize()` no-op; der Determinismus-Beleg lebt im Zwei-Lauf-
  E2E-Smoke (1b-b-R1: falls API-getriggertes Replay fuer den Flip
  gefordert wird, Trigger 039 vorziehen).

---

## 7. Nicht Gegenstand dieser ADR

- **Oeffentliche API-Replay-Bedienung** (POST /runs `replay_of` +
  `RunMetadata`-Spalte + Migration + `RunCreateRequest`-Strict-
  Schaerfung) — [Trigger 039](../planning/open/039-api-replay-trigger-surface.md)
  (1b-b-D-7).
- **Volle `GG-TERM-002/003`-Matrix** (`platform_arch`,
  `enabled_adapters`, `sim_start_time`, `config_hash`) —
  [Trigger 038](../planning/open/038-gg-term-002-003-full-equality-matrix.md).
- **`started_at`/`ended_at`-Timestamp-Setzen** + `RunMetadata`-
  Mutations-Pfad — eigener spaeterer Scope.
- **Auto-`completed`-Transition** im Core (Tick-Budget/Szenario-
  Ende) — eigener spaeterer Scope.
- **Severity-Stufen** des `replay_diff_status` (ordinal/`yellow`/
  `red`) — additive ADR-0011-Schaerfung bei Bedarf.
- **Asynchroner/entkoppelter Diff** — additive Schaerfung bei
  Last-Druck.
- **`GG-REPLAY-004..006`** (beschleunigtes Replay / Replay-Pause-
  Resume / Delta-Analysen-API; SOLLTE) — eigener Scope.
