# Slice-Plan — M1 Tick-Loop-Spine

**Status:** In Progress — Welle 0..4 abgeschlossen
(2026-05-15 / 2026-05-17 ×4). ADR 0007/0010 sind `Accepted`;
Domain-Modelle, Ports, `Scheduler` und `TickLoop` (`GG-SIM-001/
002/005`) liegen mit Determinismus- und Snapshot-Resume-Property-
Tests. Trigger 003 + 012 sind `done`. Welle 5 (Scenario + Replay)
ist der naechste Schritt.
**Datum:** 2026-05-15 (geoeffnet als `Next`);
Move `next/` → `in-progress/`: 2026-05-15 nach Welle 0.
**Bezug:**
[`ADR 0002`](../../adr/0002-language-and-build-stack.md)
(`Accepted` 2026-05-15),
[`ADR 0005`](../../adr/0005-type-check-gate.md)
(`Accepted` 2026-05-15),
[`ADR 0007`](../../adr/0007-random-port.md) (`Provisional`,
Acceptance synchron mit Welle 2),
[`done/spike-0.md`](../done/spike-0.md) §0 (Spike-0-Closure mit
„M1 — Tick-Loop-Spine"-Verweis),
[`roadmap.md`](roadmap.md) §3 M1.

---

## 1. Zweck

M1 liefert die **invariante Spine** der Simulation: einen
deterministischen Tick-Loop ohne Geraete, der `ClockPort` und
`RandomPort` als externe Eingaben nutzt, Events stabil sortiert
verarbeitet, Domain-Objekte (Telemetry/Command/Event/Quality)
kanonisch serialisiert und Snapshots persistierbar macht.

**Geraetemodelle** (Battery, PV, Load, Smart Meter, Grid Connection)
sind explizit Out-of-Scope und folgen in M2+. Die M1-Spine muss
aber so designed sein, dass M2-Geraete sich ohne Aenderung am Kern
einklinken koennen — Driving-Port-/Driven-Port-Modulgrenzen aus
`ADR 0002 §A-1` bleiben strikt.

## 2. Erfolgskriterien

M1 ist erfolgreich, wenn:

1. **`make fullbuild` gruen** auf `main` (Spike-0-M1-Abnahme-
   bedingung aus `done/spike-0.md §0`). Erfordert:
   - `tests/integration/compose.yml` (Trigger 009) liefert PostgreSQL
     fuer testcontainers-Tests.
   - `deploy/compose.yml` (Trigger 010) startet api+sim (UI bleibt
     M2-Slice).
   - Minimal-`adapters/driving/http_api.py` mit `app` (FastAPI), das
     `openapi-validate`-Stage importieren kann.
   - `runtime`-Image mit `/health`-HEALTHCHECK aus dem Dockerfile.
2. **`make gates` ohne `CRITICAL_COV_TARGETS`-Override gruen**:
   - `src/grid_gym/hexagon/core/simulation/` (Scheduler, Tick-Loop,
     Snapshot) ≥ 90 % Line + Branch.
   - `src/grid_gym/hexagon/core/devices/battery/` — **bewusst leer**
     in M1; Path-Guard kommt mit M2. Pragmatisch: M1-Abschluss
     erlaubt entweder ein leer-quittiertes `battery/`-Modul oder
     ein bewusstes Skipping im Path-Guard (entschieden in Welle 4).
   - `src/grid_gym/hexagon/core/scenario/` mit YAML-Schema-Validator
     (`GG-SCN-001`/`008`).
   - `src/grid_gym/hexagon/core/replay/` mit Diff-Klassifikation
     (`GG-REPLAY-007`).
3. **Determinismus-Property nachgewiesen**:
   - Zwei `RunMetadata`-identische Laeufe (gleicher Seed, gleiches
     Szenario) erzeugen byte-identische Snapshot-Exports.
   - Tie-Breaking `(time, priority, source, sequence, event_id)`
     per `hypothesis`-Property-Test verifiziert.
4. **Trigger-Abarbeitung**:
   - `001-code-review-doc.md` (`docs/user/code-review.md` +
     PR-Template) geliefert — spaetestens vor der ersten
     Adapter-PR.
   - `003-random-port-adr.md` (RandomPort-ADR) geschrieben und
     `Accepted`.
   - `009`/`010` operativ via Compose-Files.
5. **Folge-ADRs gepflegt**: jede Aenderung an `pyproject.toml`
   `[tool.*]`-Sektionen, die `ADR 0002 §A-1`- oder
   `ADR 0005 §5.1`-Vertraege beruehrt, traegt eine Folge-ADR-
   Referenz (per Trigger 001 Code-Review-Doc enforced).

## 3. Liefer-Reihenfolge (Wellen)

Wellen sind atomar; jede Welle endet mit einem gruenen Lauf der
bis dahin aktiven Gates (`make gates CRITICAL_COV_TARGETS=...`).

### Welle 0 — Vorbereitung (1/2 Tag)

- **Trigger 003** (`RandomPort`-ADR) als `ADR 0007` schreiben:
  Seeding-Kette pro Lauf, deterministischer PRNG-Vertrag (z. B.
  `random.Random`-basiert mit Sub-Seeds), Snapshot-/Resume-Vertrag.
  Status `Provisional`, dann `Accepted` synchron mit M1-Slice-1.
- **Trigger 001** (`docs/user/code-review.md` + PR-Template)
  starten — kann parallel laufen.
- **Lock-Refresh-Pruefung**: `make lock-refresh`; wenn `uv.lock`
  sich aendert, separater `chore(deps)`-Commit vor M1-Start.

### Welle 1 — Domain-Modelle (Tag 1)

- `src/grid_gym/hexagon/core/domain/`:
  - `quality.py` — `Quality`-Enum (valid/stale/estimated/limited/
    invalid/nan/missing/fault_injected) gemaess `GG-DATA-003`.
  - `command_result.py` — `CommandResult`-Enum (accepted/rejected/
    limited/expired/failed/ignored) gemaess `GG-DATA-004`.
  - `run.py` — `RunMetadata` als `@dataclass(frozen=True, slots=True)`
    (run_id, scenario_hash, schema_version, seed, tick_ms,
    started_at, ended_at, tool_version) gemaess `GG-DATA-001` /
    `GG-SIM-003`.
  - `telemetry.py` — `TelemetryPoint` als FrozenDataclass (run_id,
    tick, simulation_time, device_id, metric, value, unit, quality,
    source, sequence) gemaess `GG-DATA-001`/`002`.
  - `command.py` — `Command` als FrozenDataclass (command_id,
    simulation_time, target_device_id, type, payload,
    validation_status, result) gemaess `GG-DATA-004`.
  - `event.py` — `Event` als FrozenDataclass (event_id,
    simulation_time, source, target, type, payload, priority,
    sequence) gemaess `GG-ARCH-005`.
- `tests/unit/hexagon/core/domain/test_*.py`:
  - `hypothesis`-Property-Tests: Roundtrip via `canonical_json`
    byte-stabil, Frozen-Garantie geprueft (`pytest.raises` bei
    Attribut-Set).
- **Snapshot-Schema-Vorbereitung** (Pflicht fuer Welle 4):
  `Snapshot`-Skelett (oder ein Mini-`SnapshotEnvelope`-Wrapper)
  traegt einen `version: int`-Discriminator. Begruendung: ADR 0007
  §5.1 schreibt `version: int` fuer `RandomPort.snapshot()` fest;
  damit M1-Welle-4 nicht zwei inkompatible Versionierungs-Schemata
  nebeneinander stellt, fixiert Welle 1 die Konvention „jedes
  Sub-Snapshot-Dokument im Snapshot-Envelope hat einen
  `version: int`-Schluessel als erstes Feld". `canonical_json`-
  Sortierung garantiert keine Feld-Reihenfolge, daher kein
  konkretes JSON-Ordering — nur Anwesenheits-Pflicht.
- **Gate-Status nach Welle 1**: `make lint`/`format-check`/
  `typecheck`/`arch-check` (AC-DOMAIN-FROZEN faengt jetzt echte
  Domain-Klassen), `make test-unit`, `make coverage-gate-critical
  CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/domain`.

### Welle 2 — Ports (ClockPort + RandomPort) (Tag 2)

- `src/grid_gym/hexagon/ports/driven/`:
  - `clock.py` — `ClockPort` als `typing.Protocol` mit
    `now() -> SimulationTime`, `advance(delta_ms: int) -> None`.
  - `random.py` — `RandomPort` als `Protocol` mit
    `next_int(low, high) -> int`, `next_float() -> Decimal`,
    `sub_port(name: str) -> RandomPort` (Sub-Seeding aus ADR 0007).
- `tests/unit/hexagon/ports/driven/test_*.py`:
  - In-Memory-Test-Implementationen fuer Tests (`FakeClock`,
    `FixedSeedRandom`).
  - Determinismus-Property: gleicher Seed → gleiche Sequenz
    (via `hypothesis`-`@given`).
- **Gate-Status nach Welle 2**: alle aus Welle 1 plus
  `make coverage-gate-critical CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/domain src/grid_gym/hexagon/ports/driven`.
- **Abgeschlossen 2026-05-17:** ADR 0007 `Accepted` (Validierungs-
  Spike §4a AC1-AC6 gruen), Trigger 003 nach `done/`,
  `MersenneTwisterRandomPort` in `adapters/driven/random_mt/`
  ausgeliefert. §5.1 bei Acceptance geschaerft: `from_snapshot`
  ist `classmethod` am Adapter (statt Modul-Funktion im Port),
  weil `AC-PORTS-NO-OUT` `ports → adapters`-Importe verbietet.
  **Test-Ablage-Konvention:** Tests spiegeln das getestete Modul,
  nicht das Protocol-Modul. Konkret:
  `tests/unit/hexagon/ports/driven/_fakes.py` haelt die Test-
  Doubles (`FakeClock`, `FixedSeedRandom`-Alias) und
  `tests/unit/hexagon/ports/driven/test_clock.py` testet
  `FakeClock`-Verhalten; die deterministischen RandomPort-Tests
  (`§4a` AC1-AC6) liegen in
  `tests/unit/adapters/driven/random_mt/test_mersenne_twister.py`,
  weil sie die konkrete Adapter-Implementation pruefen — Slice-
  Plan-Wortlaut „tests/unit/hexagon/ports/driven/test_*.py"
  oben ist als Sammelbegriff fuer Port-Verhaltens-Tests zu
  lesen, nicht als Adapter-Test-Ablage.
  Erweiterter Critical-Override:
  `CRITICAL_COV_TARGETS="src/grid_gym/hexagon/core/domain
  src/grid_gym/hexagon/ports/driven
  src/grid_gym/adapters/driven/random_mt"`.

### Welle 3 — Scheduler mit Tie-Breaking (Tag 3)

- `src/grid_gym/hexagon/core/simulation/scheduler.py`:
  - Event-Queue mit `heapq` (intern), Tie-Breaking-Reihenfolge
    `(time, priority, source, sequence, event_id)` gemaess
    `GG-ARCH-006`.
  - `Scheduler.add(event: Event)`, `Scheduler.pop_due(time) -> list[Event]`,
    `Scheduler.snapshot() -> SchedulerState`.
- `tests/unit/hexagon/core/simulation/test_scheduler.py`:
  - Tie-Breaking-Test: 5 Events mit gleichem `time`, in
    randomisierter Eingabereihenfolge → identische Ausgabereihenfolge.
  - `hypothesis`-Property: Permutation der Eingabe-Events erzeugt
    identische `pop_due`-Reihenfolge.
- **Gate-Status nach Welle 3**: alle aus Welle 2 plus Coverage
  auf `simulation/scheduler`.
- **Abgeschlossen 2026-05-17:** `Scheduler` in
  `hexagon/core/simulation/scheduler.py` mit heap-basierter Queue
  (Sort-Keys-Only, Events neben dem Heap im `dict`-Index, damit
  `heapq` nie unordbare `Event`-Instanzen vergleicht).
  `Scheduler.add`, `pop_due(time <= ...)`, `snapshot()` (Mapping
  mit `version: int` + `pending_events` in Pop-Reihenfolge) und
  `from_snapshot()` als classmethod. Typisierte
  `SchedulerSnapshotFormatError`-Hierarchie in `core/errors.py`.
  `SchedulerDuplicateEventIdError` schuetzt Sort-Key-Eindeutigkeit.
  Erweiterter Critical-Override:
  `CRITICAL_COV_TARGETS="src/grid_gym/hexagon/core/domain
  src/grid_gym/hexagon/ports/driven
  src/grid_gym/adapters/driven/random_mt
  src/grid_gym/hexagon/core/simulation"`. TODO(M1-Welle-4):
  Snapshot-Composition mit `RandomPort.snapshot()` (heute
  `bytes`-canonical vs. `Mapping[str, object]`) im
  `SnapshotEnvelope` vereinheitlichen — ggf. Folge-ADR.

### Welle 4 — Tick-Loop + Snapshot (Tag 4)

- `src/grid_gym/hexagon/core/simulation/tick_loop.py`:
  - `TickLoop` mit `ClockPort`/`RandomPort`-Injektion,
    `Scheduler`-Verarbeitung, Commit-Reihenfolge stabil.
  - `tick(self) -> TickResult`: ClockPort → Scheduler.pop_due →
    Events verarbeiten → Telemetry sammeln → Commit.
  - Snapshot-Pfad (`GG-SIM-005`): einfacher in-memory Snapshot
    (Pickle-frei, via `canonical_json`).
- `tests/unit/hexagon/core/simulation/test_tick_loop.py`:
  - Determinismus-Property: zwei TickLoop-Instanzen mit gleichem
    Seed/Setup → byte-identische Telemetry-Exports.
  - Snapshot-Resume: nach Snapshot fortgesetzt → ab Snapshot
    gleiche Werte wie ein ununterbrochener Lauf (`GG-SIM-005`).
- **Gate-Status nach Welle 4**: `make gates` jetzt mit
  `CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/simulation src/grid_gym/hexagon/core/domain src/grid_gym/hexagon/ports/driven`.
  Default `CRITICAL_COV_TARGETS` ist immer noch rot, weil
  `devices/battery`/`scenario`/`replay` noch nicht implementiert.
  Loesung: M1-`gates` mit explizitem Override; volle Default-
  `gates` erst nach Welle 5/6.
- **Abgeschlossen 2026-05-17:** TickLoop (`tick_loop.py`) und
  TickResult (`domain/tick_result.py`) ausgeliefert.
  Snapshot-Composition ueber `RandomPort.snapshot_as_mapping`
  (`ADR 0010`) — Trigger 012 geschlossen. TickLoop.snapshot()
  baut SnapshotEnvelope-konformes Mapping mit
  sub_snapshots={scheduler, random_root}. from_snapshot prueft
  Clock-/Random-Konsistenz typisiert. Erweiterter Critical-
  Override unveraendert (gleiche vier Targets wie Welle 3 — der
  TickLoop liegt in `core/simulation`, ist also schon abgedeckt).
  Trigger-012-§2/§3/§4-Restpunkte (generischer Snapshot-Codec,
  Payload-Canonical-Validierung als Free-Function) bleiben bis
  Welle 5 offen (Folge-Trigger 013 oeffnet sich dort).

### Welle 5 — Scenario + Replay (Tag 5)

- `src/grid_gym/hexagon/core/scenario/`:
  - `validator.py` — YAML-Schema-Validator (`GG-SCN-001`/`008`)
    plus Reference-/Event-/Replay-/Fault-Validatoren (kann
    leere Stub-Funktionen sein, solange Fault-Logik in M3+
    bleibt).
  - `loader.py` — YAML laden, Schema-Version pruefen, kanonisches
    Szenarioobjekt + Hash zurueckgeben (`GG-SCN-003`/`004`).
- `src/grid_gym/hexagon/core/replay/`:
  - `mapper.py` — CSV/JSON-Lines-Import, Originalzeit → Simulationszeit
    (`GG-REPLAY-001`/`002`).
  - `diff.py` — fachliche vs. volatile Felder klassifizieren
    (`GG-REPLAY-007`).
- Tests entsprechend.
- **Gate-Status nach Welle 5**: Default `CRITICAL_COV_TARGETS`
  funktioniert fuer `scenario` und `replay`; `devices/battery`
  bleibt offen (M2).

### Welle 6 — Integration + `make fullbuild` (Tag 6)

- **Trigger 009** abarbeiten: `tests/integration/compose.yml` mit
  Postgres-Service, testcontainers-Test-Runner. Mindestens ein
  Integration-Test, der den Tick-Loop gegen Postgres-Persistenz
  laufen laesst.
- **Trigger 010** abarbeiten: `deploy/compose.yml` mit `api`-
  Service (FastAPI) + Postgres + `simulation`-Service.
  `make runtime` startet das, pollt `/health`.
- `src/grid_gym/adapters/driving/http_api.py`:
  - Minimal-FastAPI-`app` mit `/health`, `/openapi.json`,
    `POST /runs` (Stub fuer M1).
  - `openapi-validate`-Stage wird damit gruen (`GG-API-003`).
- `src/grid_gym/adapters/driven/persistence_postgres/`:
  - Minimaler `RunRepositoryPort`-Driver mit `alembic`-Migration
    fuer `runs`-Tabelle.
- **Gate-Status nach Welle 6**: `make fullbuild` gruen
  (CI + Runtime-Image-Build + Compose-Smoke). M1-Abschluss-Gate
  erreicht.

### Welle 7 — Closure (1/2 Tag)

- ADR 0007 (`RandomPort`) `Accepted` setzen (synchron mit Welle 2
  Spike-0-Pattern).
- `done/M1-tick-loop-spine.md` Closure-Notiz mit Welle-1..7-
  Tabelle, Verweis auf `done/M1-tick-loop-results.md` (analog
  spike-0-results).
- `roadmap.md §3 M2`-Vorbelegung skizzieren (Geraetemodelle).
- Triggers `005`/`006` aus `open/` pruefen, ob durch M1-Code
  aktivierungsreif geworden.

## 4. Out-of-Scope (bleibt fuer M2+ oder eigene Triggers)

- **Geraetemodelle** (Battery, PV, Load, Smart Meter, Grid
  Connection) — `GG-DEV-010..014`, `GG-BESS-001..008`,
  `GG-GRID-001..007`. M2.
- **Fault Injection** — `GG-FAULT-001..010`. M3 oder eigener Slice.
- **Multi-Agent-Subsystem** — `GG-AGENT-001..008`. SOLLTE,
  Folgewellen.
- **UI** — `GG-UI-001..009`. M4 oder eigener Slice (`ui/`-Modul).
- **OpenTelemetry-Tracing** — `GG-OTEL-001/004`. SOLLTE,
  M3-koppelbar.
- **Protokolladapter** (MQTT/Modbus/OPC-UA/DNP3/IEC-61850) — alle
  `SOLLTE`, Folgewellen mit eigenen Slices.
- **Performance-Benchmarks** (`GG-RT-004/005`) — M3 oder eigener
  Slice; M1 zeigt nur Determinismus-Funktionalitaet, nicht
  Performance.

## 5. Risiken und Fallback

- **`RandomPort`-ADR (Trigger 003) zieht sich**: M1-Welle 2 wartet
  ohne ADR. Fallback: vorlaeufiger PRNG-Vertrag in der Domain
  direkt, ohne ADR — explizit als „interim" markiert; ADR wird
  rueckwirkend formalisiert. Risiko: Drift bei spaeterer
  Acceptance.
- **`make gates`-Default-Schwellen passen nicht zum M1-Stand**:
  `devices/battery` bleibt leer bis M2 — `Default
  CRITICAL_COV_TARGETS` schlaegt Path-Guard fail-fast. Fallback:
  M1-Closure dokumentiert „M1-Acceptance-Override" analog zum
  Spike-0-Pattern (`make gates CRITICAL_COV_TARGETS=...` mit
  M1-spezifischer Liste).
- **`tests/integration/compose.yml` Postgres-Setup auf
  CI-Maschine**: Docker-in-Docker oder Docker-Socket-Mount
  Risiko. Fallback: in M1 nur lokal verifizieren, GitHub-Actions-
  Workflow kommt mit Trigger zur CI-Matrix-Aktivierung.
- **FastAPI-`app`-Import-Pfad**: `openapi-validate`-Stage
  importiert `grid_gym.adapters.driving.http_api`. Wenn das
  Module-Path ungeschickt liegt, kollidiert es mit
  AC-ADAPTER-PURE. Vor-Pruefung: Welle 6 startet mit
  Skelett-Test, dass `make arch-check` mit dem leeren `http_api.py`
  gruen bleibt.

## 6. Wandert nach

- `in-progress/M1-tick-loop-spine.md`, sobald Welle 0 oder 1
  startet.
- `done/M1-tick-loop-spine.md` mit Closure-Notiz nach Welle 7.
- `archive/`, falls M1 grundlegend umgeplant wird (unwahrscheinlich
  — Tick-Loop-Spine ist die `ADR 0002 §6.2`-fixierte Spine-
  Definition).

## 7. Verifikationspfad

| Erfolg                                           | Verifikation (Dockerfile-Stage via `make <target>`)                                                                                        |
| ------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------ |
| Domain-Modelle frozen + canonical-roundtrip      | `make test-unit` mit `hypothesis`-Property-Tests fuer Telemetry/Command/Event                                                              |
| ClockPort + RandomPort deterministisch           | `make test-unit` mit Seed-Property-Tests (gleicher Seed → identische Sequenz)                                                              |
| Scheduler Tie-Breaking stabil                    | `make test-unit` mit Permutations-Property                                                                                                 |
| Tick-Loop byte-stabil ueber Snapshots            | `make test-unit` Determinismus-Property (zwei Laeufe → identische `canonical_json`-Ausgabe)                                                |
| Scenario-Validator weist Schema-Fehler ab        | `make test-unit` mit Negativ-Tests (Schema-Fehler vor erstem Tick)                                                                         |
| Replay-Diff klassifiziert fachlich vs. volatil   | `make test-unit` Replay-Diff-Tests                                                                                                         |
| M1-Slice ohne `CRITICAL_COV_TARGETS`-Override    | `make gates` (Default-`CRITICAL_COV_TARGETS` aus `devices/battery` weiterhin out-of-scope; M1-Closure dokumentiert M1-spezifischen Override) |
| `openapi-validate` gruen                         | `make ci` (oder `make openapi-validate` einzeln)                                                                                           |
| `make fullbuild` gruen — **M1-Abschluss-Gate**   | `make fullbuild` (CI + Runtime-Image + Compose-Smoke); erfordert Trigger 009 + 010 abgearbeitet                                              |
| Trigger 001 abgearbeitet                         | `docs/user/code-review.md` + `.github/PULL_REQUEST_TEMPLATE.md` (oder Gitea-Aequivalent) im Repo                                            |
| Trigger 003 abgearbeitet                         | `ADR 0007 RandomPort` `Accepted`; `RandomPort`-Implementierung in `hexagon/ports/driven/random.py` + Tests                                  |
