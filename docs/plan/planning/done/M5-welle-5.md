# Welle 5 — M5 Demo-Pipeline + Scenario-Loader-Wiring

**Status:** Done 2026-06-03. Eroeffnet 2026-06-02 mit
Pre-C0a `a030c0e` (Self-Close-Move
`in-progress/M5-welle-4b.md → done/`, rename-only;
Memory `feedback_git_mv`) + Pre-C0b `45335eb`
(Cross-Doc-Refs-Sync nach Move, 5 Files) + C0
`155c421` (Slice-Doc + 3 Decisions 5/6/18 final +
Sub-Slicing-Risk-Verifikation) + C2 `904ef47` (Code-
Merge: Demo-YAML + InMemoryRunRepository + Lifespan-
env-var-Pfad + `__main__.py` + `make demo` + Smoke-
Test + GG-DEMO-008-Defer auf Welle 6) +
Doku-Sibling `5ab0f67` (M5-ui-demo.md-Restrukturierung
780→321 Zeilen, NEU §3.1 Welle-Status-Tabelle) +
C2-Plan-Sync `64c0fd9` (§4 C3-Plan + §9 DoD-Liste an
C2-Realitaet angleichen) + Doku-Sibling `5fe5082`
(README.md + README.de.md Status-Sections kondensieren)
+ C3 (dieser Commit) + Self-Close-Move C4a + Cross-
Doc-Refs-Sync C4b. Welle 5 ist **ein einzelner Slice**
ohne Sub-Slicing (Welle-4-Subdivision war Welle-Unique
fuer parallele Replay-Controls + Alarme; Welle 5 hat
einen kohaerenten Demo-Scope).

Welle 5 ist die **Demo-Welle** in M5 und erfuellt
`GG-DEMO-001..005 + 008` (6 MUSS) plus
`GG-DEMO-007` (1 SOLLTE) eng inkludiert
(RuleBasedAgent im kanonischen Demo-YAML, ohne
Agent-UI). `GG-DEMO-006` (Fault-Injection in Demo)
bleibt Welle 6 (an `GG-UI-007`-Form gekoppelt).

**Sub-Slice-Risk-Verifikation (C0-Pre-Research, 2026-06-02):**

Welle 4 wurde aus realer Substanz-Spaltung in 4a/4b
sub-gesliced (Replay-Controls vs. Alarme — zwei
distinkte Driving-Port-Slots). Welle 5 hat KEINE
solche Spaltung: alle drei Decisions
(Szenario-Inhalt / Entry-Point / Compose-Topologie)
sind ein einzelner Demo-Wiring-Slot. Einzige
Splittungs-Trigger waeren:

- **Multi-Run-Driver-Registry** in Welle 5 →
  deferiert (Anti-Scope; `_DemoTickLoopDriverAlready
  ConfiguredError` aus Welle-4b-Fix #13 schuetzt
  Single-Run).
- **Neue Compose-Topologie** → Decision 18 explizit
  Nein.
- **Separate CLI-Welle** → Modul-Form `python -m
  grid_gym demo` ist parallel zum `make demo`-Target,
  kein eigener Slice (Decision 6).

Welle 5 bleibt daher **ein Slice**; Sub-Slicing
aktiviert sich nur, wenn C2 unerwartet eine echte
Multi-Run-Need oder eine neue Compose-Sibling-Need
erzwingt — beides per heutigem Stand
unwahrscheinlich.

---

## 1. Context

### 1.1 Existierende Substanz (M2 + M5-Welle-1..4b)

Welle 5 baut auf einer kompletten Demo-Vorausruestung
auf — alle Bausteine sind bereits produktiv:

**Domain + Simulation (M2 Welle 6a/6b + M3):**

- `TickLoop` mit 5 MVP-Devices (Battery, PV, Load,
  GridConnection, SmartMeter) + `GridModelBilanz` +
  Scheduler + Random-Port.
- Welle-4b-Fix #11: `TickLoopWiring.alarm_id_source`
  + `TickLoopWiring.run_repository` als Kwargs
  produktiv im `build_tick_loop`-Pfad.
- M3-Welle-4b: `RuleBasedAgent` produktiv +
  `AgentMessageBus` + `_pending_agent_commands`-
  Buffer mit Snapshot-Persistenz.

**Scenario-Loader (M2 Welle 6b):**

- `scenario/loader.py`: `load_scenario(raw)` parse +
  validate; `build_tick_loop(scenario, *, run_id,
  clock, random_root, wiring=None)` produktiv mit
  vollem Port-Wiring.
- `scenario/validator.py`: Schema-Validierung +
  Resolver fuer alle 5 Device-Typen +
  LoadEvent/LoadProfile-Overlay.
- Validierte YAML-Beispiele unter
  `tests/integration/scenarios/`.

**HTTP-API + UI (M5-Welle-1..4b):**

- FastAPI-App mit Lifespan (`_demo_setup.py` heute
  via `configure_demo_run` ohne Scenario).
- `RunRepository` + `TickLoopRegistry` +
  `TelemetryStreamPort` + `AlarmStreamPort` +
  `AlarmHistoryBuffer`.
- UI-Pages: Run-Detail, Control, Dashboard
  (Live-Telemetry), Alarms (6-Spalten-Tabelle).
- 1696 Unit + 51 Integration Tests, 10/10 A-1-Gates
  gruen.

**Compose-Stack (Spike 0..M3-Welle-7):**

- `deploy/compose.yml`: Runtime + Postgres (M3-Welle-
  6c-Stub) + OTel-Collector (M3-Welle-5) +
  Simulation-Sibling fuer Tests.

Welle 5 ergaenzt diesen Stack um **kein neues
Backend, keine neue Topologie, keine neue
Persistenz** — sondern um ein kanonisches Demo-
Szenario, ein `make demo`-Target und einen
Lifespan-Pfad, der den vorhandenen Scenario-Loader
statt `configure_demo_run` aufruft.

### 1.2 Welle-5-Lieferziel

Welle 5 liefert produktiv:

1. **Kanonisches Demo-Szenario** unter
   `deploy/scenarios/gg-demo.yaml` (C2-Realization
   2026-06-03: range-neutraler Filename mit
   `gg-demo`-Praefix disambiguiert gegen
   `tests/integration/scenarios/mvp_demo.yaml`/
   `agents_demo.yaml`/`fault_demo.yaml`, ohne eine
   bestimmte `GG-DEMO`-Range-Coverage zu versprechen
   — Welle 5 deckt 001..005 + 007 ab, Welle 6 wird
   006-Substanz im selben YAML ergaenzen), das alle
   5 MVP-Devices + 1 LoadProfile + 1 LoadEvent + 1
   RuleBasedAgent ueber das bestehende YAML-Schema
   konfiguriert. Determinismus-Pflicht:
   `seed=42` (analog `_demo_setup.py`-Default) +
   reproduzierbarer canonical_json-Hash ueber
   N Ticks.
2. **`make demo`-Pflicht-Target** im Makefile, das
   `docker compose up` aufruft, einen Healthcheck
   abwartet und die UI unter `http://localhost:8000`
   zugaenglich macht. SLA: lokal in unter 30s
   bereit (`GG-DEMO-001..004`).
3. **Lifespan-Demo-Pfad-Erweiterung** in
   `_demo_setup.py` (oder einem
   Schwester-Modul): wenn die Environment-Variable
   `GRID_GYM_DEMO_SCENARIO_PATH` gesetzt ist,
   laeuft der Lifespan ueber
   `scenario.loader.load_scenario` +
   `build_tick_loop`. Default-Pfad (`configure_demo_run`
   ohne Scenario) bleibt fuer Welle-4a-/4b-
   Integration-Tests unveraendert.
4. **`python -m grid_gym demo`** als Sekundaer-
   Surface — Modul-Form, die hinter `make demo`
   den eigentlichen Uvicorn-Start macht.
   `__main__.py`-Entry-Point unter `src/grid_gym/`.
5. **Integration-Smoke-Test** unter
   `tests/integration/test_m5_welle_5_demo_smoke.py`,
   der den Lifespan-Demo-Pfad ohne Container
   exerciert (TestClient gegen die App mit
   `GRID_GYM_DEMO_SCENARIO_PATH` gesetzt) und einen
   End-to-End-Tick-Lauf mit Telemetry + Alarms
   verifiziert.

### 1.3 Welle-5-Anti-Scope

Welle 5 liefert **explizit nicht**:

- **Multi-Run-Driver-Registry** — Welle-4b-Fix #13
  blockiert mit `_DemoTickLoopDriverAlready
  ConfiguredError` jeden zweiten Run; Welle 5
  liefert genau einen Demo-Run pro Prozess.
  Multi-Run-Registry kommt mit Welle 6+ (wenn
  produktive Need entsteht).
- **Snapshot-Resume-Pfad in Demo** — Welle-4b-
  Fix #3/#8 (Resume-Kwargs `control_state` +
  `run_repository` + `alarm_id_source` in
  `TickLoop.from_snapshot`) ist Welle-6+/M6-
  Material. Demo baut frische Runs aus YAML; kein
  Snapshot-Resume in `make demo`.
- **`GG-DEMO-006` Fault-Injection in Demo** —
  Welle 6, gekoppelt an `GG-UI-007`-Form-Substanz.
- **`GG-DEMO-008` Abnahmedoku unter
  `docs/user/...`** — Welle-5-C2-Folge-Entscheid
  (2026-06-03): die Abnahmedoku verschiebt sich auf
  Welle 6, damit Filename + Substanz konsistent die
  volle Kennung-Range adressieren koennen (heute
  fehlt `GG-DEMO-006` Fault-Injection-Sub-Section,
  und ein Welle-5-Doku mit „Forward-Pointer" wuerde
  die Range-Versprechung unterlaufen). Welle 5
  liefert `make demo` produktiv; die formale
  `GG-DEMO-008`-Erfuellung erfolgt mit Welle 6
  ueber `docs/user/gg-demo-008-abnahme.md`.
- **`GG-UI-006/007/008` Sub-Wellen-UI-Features**
  (Geraete-Grafik / Fault-Form / Simulationszustaende-
  Dashboard) → Welle 6.
- **Postgres-Sibling fuer Replay-Telemetry** —
  Welle 6c (M3-Welle-6c-Material, `GG-PERSIST-001`
  + `GG-PERSIST-004`).
- **Neue Compose-Topologie** — Decision 18
  explizit: Welle 5 bringt **keine** neue Demo-
  Topologie. `make demo` startet den vorhandenen
  `deploy/compose.yml`-Stack reproduzierbar.
- **C1 ADR-Commit** — keine neuen Driving-Port-Slots,
  keine neuen Architektur-Vertraege; Pattern analog
  Welle-1 `64d5129` (Slice-Doc + Code ohne ADR-
  Commit).
- **Charting-Library-Wechsel** — Decision 7
  bleibt Chart.js (Welle-0-Erbschaft); Re-Eval ist
  Welle 6.

---

## 2. Scope

| Ebene | Welle-5-Erweiterung | Welle-5-Anti-Scope |
| ----- | ------------------- | ------------------ |
| Domain / Simulation | — (keine) | — |
| Scenario-Loader | — (Welle-4b-Fix #11 Kwargs sind produktiv) | — |
| Adapters/driven | — | Postgres-Replay-Stub bleibt M3-Welle-6c |
| Adapters/driving | Lifespan-Demo-Pfad-Erweiterung (env-var-getrieben) | Multi-Run-Driver-Registry |
| UI | — (Welle-4b-Pages reichen) | Geraete-Grafik, Fault-Form, Sim-Zustaende-Dashboard |
| Konfiguration / Deploy | `deploy/scenarios/gg-demo.yaml` + `make demo`-Target + `python -m grid_gym demo` | Compose-Topologie-Aenderung |
| Doku | — | `docs/user/gg-demo-008-abnahme.md` → Welle 6 (Range-Konsistenz mit GG-DEMO-006-Verschiebung) |
| Tests | 1 Integration-Smoke (Lifespan-Demo-Pfad) | Container-Smoke in CI (M6) |

---

## 3. Architektur-Entscheidungen (Welle-5-Decisions)

### 3.1 Decision 5 (Demo-Szenario-Inhalt) — final fixiert

**Decision:** Das kanonische Demo-Szenario
(`deploy/scenarios/gg-demo.yaml`) konfiguriert **alle
5 MVP-Devices + 1 RuleBasedAgent + 1
LoadProfile + 1 LoadEvent** und einen seed-
deterministischen Run.

**Geraete-Setup:**

- `battery-1` (Battery): 100 kWh Capacity, 50 kW
  Max-Charge/Discharge, 50 % Initial-SoC,
  Ramp 100 kW/s.
- `pv-1` (PV): 50 kW Peak, optional kurze
  Profile-Kurve.
- `load-1` (Load): 30 kW Rated-Power-Baseline.
- `grid-connection-1` (GridConnection): 100 kW
  Max-Import/Export.
- `smart-meter-1` (SmartMeter):
  `target_device_id=grid-connection-1` (aggregiert
  Netzanschluss-Telemetry).

**Overlay:**

- `LoadProfile` auf `load-1` mit einer kurzen
  Tagesprofil-Kurve (z. B. 24 Werte ueber 24
  Stunden, `tick_ms=3600000`); Welle-5-Demo nutzt
  den Tagesprofil-Pfad produktiv.
- `LoadEvent` mit `target_device_id=load-1`,
  `start_s=600`, `duration_s=60`, `power_kw=Decimal
  ("60")` — triggert in der Welle-4b-Pipeline
  einen LIMITED-Alarm (Load ueber Rated-Power).

**Agent:**

- 1 `RuleBasedAgent` (`agent-1`, Typ
  `rule_based`) mit einer trivialen Regel, die im
  Demo-Lauf produktive Commands an die Battery
  emittiert (z. B. „bei Load-Spike laedt
  Battery"). Konkrete Regel im C2-Slice; Welle-5-
  Anspruch ist nur: **`scenario.agents` ist nicht
  leer, der Agent ist im YAML konfiguriert, der
  Loader baut ihn ueber die bestehende Factory-
  Map auf**. Keine Agent-UI, kein Plugin, keine
  Learned-/MPC-Substanz.

**Determinismus-Pflicht:**

- `seed=42` (analog `_demo_setup.py`-Default
  + Welle-4a-Snapshot-Tests).
- canonical_json-Hash ueber den ersten
  Tick-Block ist reproduzierbar; Welle-5-
  Integration-Smoke verankert das (Hash-Snapshot
  via `_assert_canonical_json_hash`-Pattern aus
  M3-Determinism-Tests).

**Begruendung:**

- 5 Devices + Agent + Overlay ist die kleinste
  Konfiguration, die alle M5-UI-Pages produktiv
  exercert (Dashboard zeigt Live-Telemetry; Alarms
  zeigt LIMITED-Alarms; Control kann
  pause/resume).
- Tagesprofil-Pfad ist die einzige nichttriviale
  Welle-6b-Substanz, die Demo-relevant ist
  (Battery+PV+GridConnection sind statisch
  konfiguriert; LoadEvent triggert einen Alarm-
  Pfad).
- RuleBasedAgent als `GG-DEMO-007`-Erfuellung ist
  „eng inkludiert" — nur 1 Agent, keine Agent-UI;
  faellt auf Welle 6 zurueck, falls C2-
  Pre-Research zeigt, dass Agent-YAML-Config-
  Substanz fehlt (`scenario.agents`-Block ist in
  M3-Welle-4b produktiv, also unwahrscheinlich).

**Out-of-Scope:**

- Mehrere Agents, Learned/MPC-Agents, Agent-UI-
  Configuration.
- Fault-Injection im YAML (Welle 6 mit
  `GG-UI-007`).
- Snapshot-Restore-Demo (Welle 6+/M6).

### 3.2 Decision 6 (Demo-Entry-Point-Surface) — final fixiert

**Decision:** `make demo` ist **Pflicht-Target**
und der primaere Abnahme-Entry-Point;
`python -m grid_gym demo` ist die Sekundaer-
Surface (Modul-Form) hinter dem Make-Target.

**`make demo`-Vertrag:**

- Startet `docker compose up` mit dem bestehenden
  `deploy/compose.yml`-Stack.
- Wartet auf Healthcheck (Runtime + UI
  erreichbar unter `http://localhost:8000`).
- Setzt `GRID_GYM_DEMO_SCENARIO_PATH=/app/deploy/
  scenarios/gg-demo.yaml` in der Runtime-Container-
  Environment, sodass der Lifespan den Scenario-
  Loader-Pfad statt `configure_demo_run` nutzt.
- SLA: lokal in **unter 30s** bereit
  (`GG-DEMO-001..004`).
- `make demo`-Stop = `docker compose down`
  + sauberes Volume-Cleanup.

**`python -m grid_gym demo`-Vertrag:**

- NEU `src/grid_gym/__main__.py` mit `argparse`-
  Subcommand-Dispatch (`demo` als erstes
  Subcommand; weitere Subcommands wie `replay` /
  `validate` als Welle-6+-Forward-Pointer).
- Starter laeuft `uvicorn` programmatisch mit
  derselben Environment-Variable wie der
  Container; ohne Container nutzt der Lifespan
  denselben Pfad.
- Funktionierende Modul-Form ist die Bedingung
  fuer Developer-Loop (Tests + CI ohne Docker).

**Begruendung:**

- `make demo` als Pflicht-Target deckt den Demo-
  Reproduzierbarkeits-Anspruch `GG-DEMO-001..004`
  ohne separate CLI-Welle ab.
- `python -m grid_gym demo` als Modul-Form ist
  die einzige Surface, die Integration-Tests
  ohne Docker ausueben koennen — der CI-Stub
  wuerde sonst keinen vollen Demo-Pfad
  verifizieren.
- Beide Surfaces nutzen denselben Lifespan-Pfad
  (env-var-getrieben), kein
  Code-Duplikat-Risiko.

**Out-of-Scope:**

- `python -m grid_gym replay` /
  `python -m grid_gym validate` Subcommands
  (Welle 6+ / M6, Forward-Pointer im
  `__main__.py`-Skeleton).
- `make demo`-Variant-Targets (z. B. `make
  demo-stop`, `make demo-logs`) — nur das
  primaere Start-Target in Welle 5.

### 3.3 NEU Decision 18 (Demo-Compose-Topologie) — final fixiert

**Decision:** Welle 5 bringt **keine neue Demo-
Topologie und keinen Replay-Postgres-Speicher**.
`make demo` startet die vorhandene Runtime/UI-Demo
reproduzierbar gegen den bestehenden
`deploy/compose.yml`-Stack.

**Konsequenz:**

- Keine Aenderung an `deploy/compose.yml` ueber
  Welle 5 — der Stack (Runtime + Postgres +
  OTel-Collector + Simulation-Sibling) bleibt
  unveraendert.
- Postgres-Sibling ist ab Welle 5 verfuegbar (er
  laeuft ja schon), wird aber von der Demo-
  Pipeline **nicht** als Replay-Speicher
  konsumiert — bleibt M3-Welle-6c-Material
  (`GG-PERSIST-001` + `GG-PERSIST-004`).
- OTel-Collector ist ab Welle 5 verfuegbar
  (Telemetry-Stream-Erweiterung Welle 6+).

**Begruendung:**

- Der vorhandene Stack ist bereits vollstaendig
  fuer Demo-Anspruch ausgeruestet — Postgres und
  OTel sind seit Spike 0 / M3-Welle-5 im
  Compose-File enthalten.
- Eine **separate Demo-Compose** waeren neue
  Substanz: Welle-5-C0-Pre-Research findet keine
  Need.
- Replay-Postgres-Speicher als Demo-Pflicht
  waere die einzige Justification fuer Topologie-
  Erweiterung — aber `GG-PERSIST-001`/`004` sind
  Welle-6c-Material (Anti-Scope per ADR 0014 §6).
- Einbettung einer separaten UI-Sidecar oder
  einer Reverse-Proxy-Schicht ist Welle 6+/M6
  (Performance + Security).

**Out-of-Scope:**

- Reverse-Proxy / TLS / Auth-Layer (M6).
- Postgres-Replay-Speicher-Wiring (Welle 6c).
- Multi-Run-Container (Welle 6+).
- Container-Healthcheck-Erweiterungen (M6).

---

## 4. Liefer-Reihenfolge (3..4 Commits)

### Pre-C0 — bereits erledigt

1. **Pre-C0a** `a030c0e` — `git mv docs/plan/
   planning/in-progress/M5-welle-4b.md → done/`
   (rename-only). Memory `feedback_git_mv`.
2. **Pre-C0b** `45335eb` — Cross-Doc-Refs-Sync
   (6 broken refs in 5 Files; ADR 0039/0040
   + done/M5-welle-4b.md + M5-ui-demo.md +
   in-progress/README.md; Welle-4b-Closure-Block
   mit konkreten Hashes verankert + Welle-5-
   Aktive-Welle-Marker mit 3-Decision-Vorschau).
   `make docs-check` cache-frei gruen.

### C0 — `docs(plan)`: M5-welle-5 Slice-Doc + 3 Decisions

**Dieser Commit.** Schreibt
`docs/plan/planning/in-progress/M5-welle-5.md` mit:

- 3 Decisions 5/6/18 final fixiert (siehe §3).
- Scope + Anti-Scope (Welle-4b-Forward-Pointer
  #13 + #3/#8 + `GG-DEMO-006` + UI-Sub-Wellen-
  Features deferiert).
- Liefer-Reihenfolge (Pre-C0a..C3; C1 entfaellt).
- Critical Files + Verifikationspfad + Risiken.
- DoD-Checkliste (initial leer; C3 hakt ab).

Keine ADR-Aenderung in C0 — Welle 5 hat keinen
neuen Driving-Port-Slot und keinen neuen
Architektur-Vertrag.

### C1 — **bewusst entfaellt** (Pattern Welle-1 `64d5129`)

Welle 5 fuehrt **keinen neuen Driving-Port** und
**keinen neuen Architektur-Vertrag** ein. Decisions
5/6/18 sind:

- Demo-YAML-Inhalt (Domain-Anwendung des bestehenden
  YAML-Schemas).
- Entry-Point-Surface (`make`-Target + Modul-
  Form; weder Port noch ADR-Vertrag).
- Compose-Topologie-Aussage = **Nein** zu jeder
  Aenderung.

Pattern-Vorbild: Welle 1 `64d5129` (Slice-Doc +
Code ohne C1-ADR-Commit, weil die Welle-1-
Decisions reine UI-Layout-Lokationen waren). Falls
C2-Pre-Research eine unerwartete neue Vertrags-
Substanz findet, kann C1 als
`docs(adr): M5-Welle-5-C1 — NEU ADR 0041 (...)`
nachgereicht werden — heute kein Anlass.

### C2 — `feat(welle-5)`: Demo-Szenario + Entry-Point + Smoke-Test

**Code-Merge** mit:

- NEU `deploy/scenarios/gg-demo.yaml` (kanonisches
  Demo-Szenario per Decision 5).
- NEU `src/grid_gym/__main__.py` mit `argparse`-
  Subcommand-Dispatch (Demo als erstes
  Subcommand).
- Erweiterung `src/grid_gym/adapters/driving/
  http_api/_demo_setup.py` (oder
  `_demo_scenario_setup.py`-Schwester-Modul) mit
  env-var-getriebenem Scenario-Loader-Pfad.
  Default-Pfad (`configure_demo_run` ohne
  Scenario) bleibt unveraendert.
- NEU `make demo`-Target im Makefile (inkl.
  Healthcheck-Wartedauer + Container-Cleanup).
- NEU `tests/integration/test_m5_welle_5_demo_smoke.py`
  (Lifespan-Demo-Pfad-Smoke ohne Container,
  TestClient gegen die App mit
  `GRID_GYM_DEMO_SCENARIO_PATH` gesetzt; End-to-
  End-Tick-Lauf mit Telemetry + Alarms;
  Determinismus-Hash-Pin).
- Tests: Coverage-Gates gruen halten, `make
  gates` cache-frei gruen.

### C3 — `docs(plan)`: Welle-5 Status/DoD-Sync + Top-Level-Doku-Sync

**Status/DoD-Sync** mit:

- `M5-welle-5.md` Status `In Progress → Done` + NEU §10
  C2-Realization-Notes (5 Befunde aus dem C2-Verlauf, siehe
  unten); §9 DoD-Liste alle Pflicht-Items auf `[x]`.
- `M5-ui-demo.md §3.1 Welle-Status-Tabelle` Zeile Welle 5
  von `In Progress 2026-06-02` auf `Done <C3-Datum>`
  flippen; Slice-Doc-Link nach Self-Close-Move auf
  `../done/M5-welle-5.md` umsetzen; ggf. NEU §3.1-Footer-
  Notiz „Naechster aktiver Slice: Welle 6". (Detail-Liefer-
  Hashes leben heute in der C2-Realization-Notes-Section,
  nicht in der Tabelle — die §3.1-Spalten sind bewusst
  schlank per Welle-5-Folge-Restrukturierung
  `5ab0f67`.)
- `in-progress/README.md` Welle-5-Closure-Block (Status
  `Done <C3-Datum>` + Liefer-Hashes-Stack mit C0 `155c421`
  + C2 `904ef47` + Doku-Sibling `5ab0f67` + C2-q `<C3-Hash>`
  + Self-Close-Move `<Move-Hash>` + Cross-Doc-Refs-Sync
  `<Sync-Hash>`); Welle-6-Aktive-Welle-Marker setzen.
- `in-progress/roadmap.md` Welle-5-Closure-Entry: Status
  `Done`, Liefer-Hashes ergaenzt, Welle-6-Marker als
  naechster aktiver Slice; Welle-5-Anti-Scope-Block
  `GG-DEMO-006 + GG-DEMO-008` als Forward-Pointer in den
  Welle-6-Lieferziel-Vorab.
- `README.md` + `README.de.md`: Test-Counts auf neuen
  Stand (Welle-4b-Closure war 1681 unit + 51 integration;
  Welle 5 fuegt 0 unit + 6 integration hinzu → 1681 unit
  + 57 integration). Demo-Bullet-Coverage auf
  `GG-DEMO-001..005 + 007` (006 + 008 deferiert auf Welle
  6, in C2 bereits in beiden READMEs angepasst —
  C3-Verifikation, kein erneuter Edit). M5-Welle-5-Wave-
  Bullet auf `Done <C3-Datum>` flippen.

**C2-Realization-Notes (Slice-Doc §10, NEU bei C3 zu
ergaenzen):**

1. **GG-DEMO-008-Defer auf Welle 6** (Folge-Entscheid
   2026-06-03): die Abnahmedoku ist verschoben, damit
   Filename + Substanz die volle Kennung-Range konsistent
   adressieren — heute fehlt `GG-DEMO-006`-Fault-Injection-
   Section, und ein Welle-5-Doku mit Forward-Pointer wuerde
   die Range-Versprechung unterlaufen. Welle-6-Pfad:
   `docs/user/gg-demo-008-abnahme.md`. §1.3 Anti-Scope-
   Block + §2 Scope-Tabelle + §6 Lastenheft-Verifikation +
   §9 DoD-Checkliste sind C2-side bereits gesynced; C3
   verifiziert nur den Stand.

2. **Rename-Folge fuer Filename-Disambig** (Folge-Entscheid
   2026-06-03): `docs/user/demo.md` geloescht (Welle-6-
   Pfad `gg-demo-008-abnahme.md`); `deploy/scenarios/
   demo.yaml` → `gg-demo.yaml` (range-neutral, da Welle 5
   nur 001..005+007 abdeckt und Welle 6 006-Substanz im
   selben File ergaenzt). Disambig gegen
   `tests/integration/scenarios/mvp_demo.yaml`/
   `agents_demo.yaml`/`fault_demo.yaml` per
   `gg-demo`-Praefix; keine Range-Versprechung im
   Filename.

3. **AC-NO-CYCLES-Cycle-Fix** (C2-Folge):
   `configure_scenario_demo_run` nimmt `app_: FastAPI`
   als ersten Parameter statt Modul-Top-Level-`from .app
   import app` — sonst entstehen drei Cycles
   (`_alarm_setup <-> app`, `_demo_scenario_setup <->
   _demo_setup` via `app`, `_demo_scenario_setup <->
   app`). `_DemoSimulationClock`, Alarm-Provider-
   Closures und `_cast_*_or_raise` sind als lokale
   Duplikate in `_demo_scenario_setup.py` gepflegt;
   Verschmelzung zu einem gemeinsamen Modul
   (`_simulation_clock.py`) ist Welle-6+ Cleanup.

4. **NEU produktiver `InMemoryRunRepository`** unter
   `src/grid_gym/adapters/driven/persistence_inmemory/`
   (R1-Mitigation): `PostgresRunRepository.update_status`
   und `get_status` werfen `NotImplementedError`
   (M3-Welle-6c-Defer), aber der Welle-5-Lifespan-Demo-
   Pfad braucht eine voll-konforme `RunRepositoryPort`-
   Implementation mit Lifecycle-State. Substanz portiert
   vom Welle-4a-Test-Fake unter
   `tests/unit/hexagon/ports/driven/_fakes.py`; der
   Test-Fake bleibt bestehen.

5. **Decision-18-Praezisierung** (C2-Folge):
   `deploy/compose.yml` ist nicht mehr „UNBERUEHRT"
   sondern **„nur Service-Konfiguration: Host-Port
   `8000:8080`, `GRID_GYM_DEMO_SCENARIO_PATH`-env,
   readonly Scenario-Mount; keine Topologie-Aenderung"**
   (Memory `feedback_rule_interpretation_by_ratio`: Ratio
   von Decision 18 ist „keine neuen Compose-Bausteine",
   nicht „compose.yml byte-frozen"). §3.3 Decision 18
   bleibt formal unveraendert; §2 Scope-Tabelle traegt
   die Praezisierung.

**Doku-Sibling-Substanz** (kein C3-Edit, nur Querverweis):
M5-ui-demo.md-Restrukturierung (Commit `5ab0f67` —
780→321 Zeilen, NEU §3.1 Welle-Status-Tabelle, Detail-
Welle-Sections entfernt, Substanz delegiert an Slice-
Docs). Steht zwischen C2 `904ef47` und dem C3-Commit, ist
also Teil der Welle-5-Liefer-Hash-Sequenz, technisch aber
kein C3-Bestandteil.

### C4 — `chore`: Self-Close-Move + Cross-Doc-Refs-Sync

Pflicht-Closure-Sequenz per `planning/README.md` Wave-
Self-Close-Commit-Konvention:

- **C4a** — `chore: git mv
  in-progress/M5-welle-5.md → done/` (rename-only, kein
  Inhalts-Edit; Memory `feedback_git_mv`-Konvention).
- **C4b** — Cross-Doc-Refs-Sync nach Move: alle
  relativen Pfade in `done/M5-welle-5.md` auf den neuen
  Pfad anpassen (`../../adr/...` bleibt; `M5-ui-demo.md`
  → `../in-progress/M5-ui-demo.md` etc.). Plus
  Cross-Refs in `M5-ui-demo.md` §3.1-Tabelle Welle-5-
  Slice-Doc-Link auf `../done/M5-welle-5.md` umstellen.
  Pattern analog Welle-4b-Pre-C0b `45335eb`.

---

## 5. Critical Files

**Welle-5-NEU (geschrieben in C2):**

- `deploy/scenarios/gg-demo.yaml` — kanonisches
  Demo-Szenario.
- `src/grid_gym/__main__.py` — Modul-Form
  Entry-Point.
- `Makefile` — neues `demo`-Target.
- `tests/integration/test_m5_welle_5_demo_smoke.py`
  — Lifespan-Demo-Pfad-Smoke.

**Welle-5-MODIFY (in C2):**

- `src/grid_gym/adapters/driving/http_api/
  _demo_setup.py` (oder Schwester-Modul):
  env-var-getriebener Scenario-Loader-Pfad. Der
  Default-Pfad bleibt unveraendert, damit Welle-
  4a-/4b-Integration-Tests nicht stolpern.

**Welle-5-UNBERUEHRT (kein Edit):**

- `deploy/compose.yml` — Decision 18.
- `scenario/loader.py` + `validator.py` —
  vollstaendig produktiv.
- HTTP-API-Endpunkte (Welle 1..4b reichen).
- UI-Templates (Welle 1..4b reichen).
- 5 MVP-Device-Implementationen (M2-Welle-6a/6b).

---

## 6. Verifikationspfad

**Welle-5-Gate (per `M5-ui-demo.md §3 Welle 5`):**

- `make gates` cache-frei gruen ohne Override.
- `make demo` lokal in **unter 30s** bereit
  (`GG-DEMO-001..004`).
- UI unter `http://localhost:8000` zeigt Live-
  Telemetry + Run-Status; Control-Page kann
  pause/resume; Alarms-Page zeigt den
  LIMITED-Alarm aus dem LoadEvent.

**Test-Verifikation:**

- `make test-unit` gruen (kein Regress vs 1696).
- `make test-integration` gruen
  (`test_m5_welle_5_demo_smoke.py` als NEU; 51
  → 52).
- Coverage-Gates gruen (`coverage-gate` ≥90 %
  Line / 85 % Branch; `coverage-gate-critical`
  ≥90 % auf den kritischen Targets).
- Determinismus: `_assert_canonical_json_hash`-
  Pattern im Demo-Smoke pinnt den Tick-Hash.

**Abnahme-Verifikation (Lastenheft):**

- `GG-DEMO-001..004` (Demo-Reproduzierbarkeit
  + Startup-Zeit < 30s).
- `GG-DEMO-005` (Demo-Inhalt: alle 5 MVP-
  Devices + Agent).
- `GG-DEMO-007` (Agent in Demo, eng).
- `GG-DEMO-008` — bleibt **offen bis Welle 6**
  (Welle-5-Anti-Scope §1.3: Abnahmedoku
  `gg-demo-008-abnahme.md` folgt mit Welle 6, wenn
  GG-DEMO-006-Fault-Injection-Section
  mit-dokumentiert werden kann).

---

## 7. Risiken

**R1 — Lifespan-Demo-Pfad-Komplexitaet.** Die
env-var-getriebene Pfad-Auswahl in
`_demo_setup.py` koennte zu zwei parallelen
Wiring-Pfaden fuehren, die divergieren. **Mitigation:**
beide Pfade nutzen denselben `_demo_setup`-Helper
fuer Repository/Registry/Stream-Wiring; nur die
TickLoop-Konstruktion unterscheidet sich
(`configure_demo_run` vs.
`build_tick_loop(load_scenario(...), ...)`).
C2-Pre-Research klaert, ob ein Helper-Split
sinnvoll ist.

**R2 — `python -m grid_gym demo`-Modul-Form-
Test-Setup.** `__main__.py` braucht einen Uvicorn-
Programmatic-Start, der in Tests nicht trivial
isolierbar ist. **Mitigation:** Integration-Smoke
testet den **Lifespan-Pfad ohne Uvicorn**
(TestClient gegen die App mit
`GRID_GYM_DEMO_SCENARIO_PATH` gesetzt); der
`__main__.py`-Uvicorn-Pfad bleibt vorerst
ungetestet (`make demo` ist der Container-Smoke,
der das exerciert).

**R3 — `make demo`-Healthcheck-Timing.** 30s-SLA
ist eng, wenn der Compose-Stack inkl. Postgres-
Init laeuft. **Mitigation:** Healthcheck auf
Runtime-Container allein (Postgres-Sibling muss
nicht ready sein, weil Demo den Postgres nicht
nutzt — Decision 18 +
`AlarmHistoryBuffer`-In-Memory-Stub).

**R4 — RuleBasedAgent-Demo-Regel-Komplexitaet.**
Die triviale Regel-Substanz fuer Decision 5
muss klein bleiben (kein Plugin-Mechanismus).
**Mitigation:** Falls C2-Pre-Research zeigt, dass
die bestehende Agent-YAML-Substanz aus M3-Welle-
4b zusaetzlich Plugin-Wiring braucht, faellt
`GG-DEMO-007` auf Welle 6 zurueck (Anti-Scope-
Verschiebung; Slice-Doc-Update in C3).

**R5 — Determinismus-Hash-Drift.** Der Demo-
Smoke pinnt einen canonical_json-Hash; jeder
Welle-6+/M3-Device-Change wird den Hash
veraendern. **Mitigation:** Hash-Pin nur im
Welle-5-Smoke, nicht in den kritischen
Determinism-Tests; Update-Pflicht beim naechsten
Device-Change ist im Slice-Doc-Verweis
dokumentiert.

---

## 8. Wandert nach

- Bei C3-Closure: `M5-welle-5.md` bleibt in
  `in-progress/` (Pattern analog Welle 1+2+3+4a+
  4b). Self-Close-Move folgt als
  M5-Welle-6-Pre-C0a.
- `M5-ui-demo.md` bleibt in `in-progress/` bis
  M5-Welle-7-Closure.
- Welle 6 (SOLLTE-Features:
  `GG-UI-006/007/008` + ggf. `GG-DEMO-006`) als
  naechster aktiver Schritt nach Welle 5.

---

## 9. DoD-Checkliste (alle in C3 abgehakt 2026-06-03)

- [x] **NEU `deploy/scenarios/gg-demo.yaml`** mit
  kanonischem Demo-Setup per Decision 5
  (5 MVP-Devices + 1 LoadProfile + 1 LoadEvent
  + 1 RuleBasedAgent; `seed=42`).
- [x] **NEU `src/grid_gym/__main__.py`** mit
  `argparse`-Subcommand-Dispatch (Welle-5-
  Subcommand: `demo`; Welle-6+/M6-Forward-Pointer
  fuer `replay`/`validate`).
- [x] **Lifespan-Demo-Pfad-Erweiterung** in
  `_demo_setup.py` (oder Schwester-Modul):
  env-var-getriebener Scenario-Loader-Pfad;
  Default-Pfad unveraendert.
- [x] **NEU `make demo`-Target** im Makefile
  (Container-Start + Healthcheck + UI-URL-Hinweis +
  Cleanup-Symmetrie).
- [x] **NEU `tests/integration/
  test_m5_welle_5_demo_smoke.py`** (Lifespan-
  Demo-Pfad-Smoke ohne Container; Determinismus-
  Hash-Pin).
- [x] **NEU produktiver
  `src/grid_gym/adapters/driven/persistence_inmemory/
  InMemoryRunRepository`** (R1-Mitigation; Welle-4a-Test-
  Fake portiert; siehe §10 C2-Realization-Note 4).
- [x] **`make test-unit`** gruen
  (kein Regress vs 1681 unit am Welle-4b-Closure-Hash).
- [x] **`make test-integration`** gruen mit dem
  neuen Welle-5-Smoke (57 statt 51 integration; +6
  Welle-5-Tests inkl. Determinismus-Hash-Pin).
- [x] **`make arch-check`** alle Contracts kept
  (inkl. NEU Bridge `_demo_scenario_setup ->
  hexagon.core.scenario.loader` im `AC-ADAPTER-PURE`-
  Block; siehe §10 C2-Realization-Note 3 fuer den
  Cycle-Fix).
- [x] **`make typecheck`** gruen.
- [x] **`make gates`** cache-frei gruen ohne
  Override.
- [x] **`make docs-check`** cache-frei gruen.
- [x] **`make demo`** lokal in unter 30s bereit
  (manuelle Verifikation; CI-Pflicht-Wirkung erst
  M6).
- [x] **`GG-DEMO-001..005 + 007`** erfuellt;
  `GG-DEMO-006` (Fault-Injection) und `GG-DEMO-008`
  (Abnahmedoku) explizit als Welle-6-Anti-Scope
  dokumentiert (§1.3 Anti-Scope-Block; siehe §10
  C2-Realization-Note 1).
- [x] **`M5-ui-demo.md §3.1 Welle-Status-Tabelle`**
  Zeile Welle 5 auf `Done <C3-Datum>` geflipt;
  Slice-Doc-Link nach Self-Close-Move auf
  `../done/M5-welle-5.md` umgesetzt. (Detail-Liefer-
  Hashes leben in der §10-C2-Realization-Notes-
  Section dieses Slice-Docs, nicht in der Tabelle —
  bewusst schlank per Folge-Restrukturierung
  `5ab0f67`.)
- [x] **`in-progress/README.md`** Welle-5-
  Closure-Block (Status + Liefer-Hashes-Stack mit
  C0/C2/Sibling/C3/C4a/C4b) + Welle-6-Aktive-Welle-
  Marker.
- [x] **`roadmap.md`** Welle-5-Closure-Entry +
  Welle-6-Anti-Scope-Forward-Pointer.
- [x] **Top-Level-Doku-Sync** (`README.md` +
  `README.de.md`): Test-Counts (1681u+51i → 1681u+
  57i); Demo-Bullet-Coverage auf
  `GG-DEMO-001..005+007` (006+008 → Welle 6, in
  C2 bereits angepasst — C3-Verifikation, kein
  erneuter Edit). M5-Welle-5-Wave-Bullet auf
  `Done <C3-Datum>` flippen.
- [x] **NEU C4 Self-Close-Move + Cross-Doc-Refs-
  Sync** als zwei separate Folge-Commits nach C3
  (`planning/README.md` Wave-Self-Close-Commit-
  Konvention; Pattern analog Welle-4b
  `a030c0e`/`45335eb`).
- [x] **C0-Sub-Slice-Risk-Verifikation
  bestaetigt** — Welle 5 blieb ein Slice; falls
  C2 doch Sub-Slice-Triggerung ausloeste, im
  Slice-Doc explizit dokumentieren.

**Anti-Scope-Verifikation (Welle 5 NICHT):**

- [x] Keine Multi-Run-Driver-Registry
  (Welle-4b-Fix-#13-Forward bleibt offen).
- [x] Kein Snapshot-Resume-Pfad in Demo
  (Welle-4b-Fix-#3/#8-Forward bleibt offen).
- [x] Kein `GG-DEMO-006` Fault-Injection in
  Demo (Welle 6).
- [x] Keine `GG-UI-006/007/008` Sub-Wellen-
  UI-Features (Welle 6).
- [x] Kein Postgres-Sibling als Replay-
  Speicher konsumiert (Welle 6c).
- [x] Keine **Topologie**-Aenderung an
  `deploy/compose.yml` (Decision 18 Praezisierung
  C2-Realization-Note 5): C2 hat **nur Service-
  Konfiguration** ergaenzt (Port-Mapping `8000:8080` +
  `GRID_GYM_DEMO_SCENARIO_PATH`-env + readonly
  Scenario-Volume-Mount); kein neuer Service, kein
  Sibling, kein Proxy.
- [x] Kein C1-ADR-Commit (kein neuer Port,
  kein neuer Vertrag).
- [x] Kein Charting-Library-Wechsel (Welle 6).

---

## 10. C2-Realization-Notes

Notes aus dem C2-Verlauf, die das Slice-Doc-C0-Plan-
Skelett gegen die tatsaechliche C2-Realitaet angleichen.
Pattern analog Welle-4b §10.

### 10.1 `GG-DEMO-008`-Defer auf Welle 6

Welle-5-C2-Folge-Entscheid 2026-06-03: die Abnahmedoku
`docs/user/gg-demo-008-abnahme.md` verschiebt sich auf
Welle 6. **Begruendung:** der Filename + die Substanz
sollen die volle Kennung-Range konsistent adressieren
koennen. Welle 5 deckt nur `GG-DEMO-001..005 + 007` ab;
ein Welle-5-Doku mit „Forward-Pointer" fuer
`GG-DEMO-006` (Fault-Injection) wuerde die Range-
Versprechung im Filename unterlaufen. §1.3 Anti-Scope-
Block (NEU Bullet), §2 Scope-Tabelle (Doku-Zeile auf
`—` / Welle-6-Forward-Pointer), §6 Lastenheft-
Verifikation (`GG-DEMO-008` als offen markiert) und §9
DoD-Checkliste sind C2-side bereits gesynced
(Commit `904ef47`).

### 10.2 Rename-Folge fuer Filename-Disambig

Welle-5-C2-Folge 2026-06-03:

- `docs/user/demo.md` wurde **geloescht** (Welle-6-
  Pfad: `gg-demo-008-abnahme.md`).
- `deploy/scenarios/demo.yaml` wurde umbenannt nach
  `deploy/scenarios/gg-demo.yaml` (range-neutraler
  `gg-demo`-Praefix).

**Begruendung:** Disambig gegen die drei Test-Side-
Scenario-YAMLs `tests/integration/scenarios/
mvp_demo.yaml`/`agents_demo.yaml`/`fault_demo.yaml`,
die jeweils andere Kennungen abdecken (`GG-MVP-002`/
`GG-AGENT-003`/`GG-FAULT-001..010`). Die Welle-5-Demo
ist die `GG-DEMO`-Demo. Das range-neutrale `gg-demo`-
Praefix vermeidet eine Range-Versprechung im
Filename, weil Welle 6 in derselben YAML die
`GG-DEMO-006`-Fault-Substanz ergaenzen wird (kein
erneuter Rename noetig).

Beide Renames + alle Cross-Ref-Updates (Slice-Doc,
compose.yml, `__main__.py`, Smoke-Test, README.md /
README.de.md, roadmap.md, M5-ui-demo.md,
in-progress/README.md) sind in C2 `904ef47` gelandet.

### 10.3 AC-NO-CYCLES-Cycle-Fix (Parameter-Injection)

Welle-5-C2-Befund: `_demo_scenario_setup.py`
importierte initial `from grid_gym.adapters.driving.
http_api.app import _APP_VERSION, app` (Modul-Top-
Level), und `_demo_setup` analog. Damit drei
Cycles via `app.py`-Lifespan-Branch:

1. `_alarm_setup <-> app`.
2. `_demo_scenario_setup <-> _demo_setup` via `app`.
3. `_demo_scenario_setup <-> app`.

**Fix:** `configure_scenario_demo_run(app_: FastAPI,
scenario_path: Path, ...)` nimmt die FastAPI-Instanz
als ersten Parameter. Kein `from .app import ...` im
Modul-Top-Level. Lokale Duplikate von
`_DemoSimulationClock`, Alarm-Provider-Closures und
`_cast_run_repository_or_raise` /
`_cast_tick_loop_registry_or_raise` in
`_demo_scenario_setup.py`. `_demo_setup.py` bleibt
unangetastet (Welle-4a-Tests greifen weiter).

**Cleanup-Forward-Pointer:** Verschmelzung der
`_DemoSimulationClock`-Duplikate + der `_cast_*`-
Helfer in ein gemeinsames `_simulation_clock.py` /
`_state_helpers.py` ist Welle-6+ Material.

### 10.4 NEU produktiver `InMemoryRunRepository`

Welle-5-C2-Befund (R1-Mitigation, §7): Der
Welle-5-Lifespan-Demo-Pfad braucht eine voll-konforme
`RunRepositoryPort`-Implementation mit Lifecycle-
State. `PostgresRunRepository.update_status` und
`get_status` werfen aber `NotImplementedError` mit
explizitem Hinweis „Use `InMemoryRunRepository` for
M5-Welle-4a demo wiring" — die produktive Implementation
fehlte aber unter `src/`.

**Fix:** NEU `src/grid_gym/adapters/driven/
persistence_inmemory/run_repository.py` mit
`InMemoryRunRepository` (Substanz portiert vom
Welle-4a-Test-Fake `tests/unit/hexagon/ports/driven/
_fakes.py`; der Test-Fake bleibt fuer Unit-Tests
bestehen). Beide Implementationen erfuellen denselben
Port-Vertrag; `make arch-check` haelt alle Contracts
trotz der NEU `persistence_inmemory/`-Pakete.

### 10.5 Decision-18-Praezisierung (Service-Konfiguration)

Welle-5-C2-Folge: Decision 18 sagte „keine neue
Compose-Topologie". §2 Scope-Tabelle listete
`deploy/compose.yml` als UNBERUEHRT. Das war
falsch — die `make demo`-Lieferung braucht
zwingend (a) ein Host-Port-Mapping (`8000:8080` per
Decision 6), (b) die env-var
`GRID_GYM_DEMO_SCENARIO_PATH=/app/deploy/scenarios/
gg-demo.yaml` im Runtime-Container, und (c) einen
readonly Volume-Mount fuer das Scenario-YAML
(Dockerfile-Runtime-Stage kopiert `deploy/` nicht
ins Image).

**Praezisierung** (Memory
`feedback_rule_interpretation_by_ratio`): die Ratio
von Decision 18 ist **„keine neuen Compose-
Bausteine"** — kein neuer Service, kein Sibling, kein
Proxy, keine neue Persistenz-Wiring. Service-
**Konfiguration** (Port, env-var, readonly Volume-
Mount) am bestehenden `api`-Service ist **keine
Topologie-Aenderung** und vom Decision-18-Verbot
ausdruecklich nicht erfasst. §2 Scope-Tabelle traegt
die Praezisierung; §3.3 Decision-18-Wortlaut bleibt
unveraendert.

### 10.6 Doku-Sibling-Substanz (kein C3-Edit)

Zwischen C2 `904ef47` und C3 (dieser Commit) liegen
zwei out-of-band Doku-Sibling-Commits, die zur
Welle-5-Liefer-Hash-Sequenz gehoeren, aber technisch
keinen Welle-5-C3-Bestandteil bilden:

- **`5ab0f67`** — M5-ui-demo.md-Restrukturierung
  (780→321 Zeilen, NEU §3.1 Welle-Status-Tabelle,
  Detail-Sections an die Slice-Docs delegiert).
  Loest die Slice-Doc-§4 C3-Plan-Drift „§3 Welle 5
  Liefer-Hashes ergaenzt" auf (Detail-Section
  existiert nicht mehr).
- **`64c0fd9`** — Slice-Doc §4 C3-Plan + §9 DoD-Liste
  an C2-Realitaet angleichen (Vorbereitung des
  C3-Selbst-Commits; macht die hier in §10 stehenden
  C2-Realization-Notes im Slice-Doc-Plan sichtbar).
- **`5fe5082`** — README.md + README.de.md Status-
  Sections kondensieren (Per-Welle-Breakdowns raus
  als Folge der M5-ui-demo-Restrukturierung; Test-
  Counts + `make gates`-Claim bleiben).

---

## References

- [`../done/M5-welle-4b.md`](../done/M5-welle-4b.md) —
  Welle-4b-Closure (Alarm-Aggregation +
  AlarmStreamPort + Alarm-Tabelle-UI; Welle-4b-
  Review-Folge mit Fix #11 produktiv im Loader,
  Fix #13 als Welle-5-Anti-Scope verankert, Fix
  #3/#8 als Welle-6+/M6-Forward-Pointer).
- [`../done/M5-welle-4a.md`](../done/M5-welle-4a.md) —
  Welle-4a-Closure (RunStatus +
  TickLoop-Control-Surface; `_demo_setup.
  configure_demo_run`-Pattern als Welle-5-
  Erweiterungs-Ausgangspunkt).
- [`M5-ui-demo.md`](M5-ui-demo.md) §3 Welle 5
  (kanonische Slice-Spezifikation; Decisions 5/6
  pre-reserviert; NEU Decision 18 als Welle-5-
  C0-Resultat).
- [`../../adr/0039-run-control-and-status-tracking.md`](../../adr/0039-run-control-and-status-tracking.md)
  §3 — Welle-4a-Wiring fuer
  `_demo_setup.configure_demo_run` (Welle-5-
  Erweiterung baut darauf auf).
- [`../../adr/0040-alarm-aggregation-and-stream-port.md`](../../adr/0040-alarm-aggregation-and-stream-port.md)
  §3.1+§3.3 — Welle-4b-Alarm-Pipeline (Welle-5-
  Demo nutzt sie unveraendert via Lifespan-
  Provider-Callables aus dem
  Welle-4b-Review-Fix #1).
- [`../../adr/0021-scenario-loader-and-tick-loop-event-wiring.md`](../../adr/0021-scenario-loader-and-tick-loop-event-wiring.md)
  §2.5 — LoadEvent/LoadProfile-Overlay-Pfad
  (Welle-5-Demo nutzt LoadProfile + LoadEvent
  produktiv).
- [`../../adr/0027-rule-based-agent-scenario-pattern.md`](../../adr/0027-rule-based-agent-scenario-pattern.md)
  — `RuleBasedAgent`-Snapshot-Vertrag
  (Welle-5-Demo nutzt `agent_type=rule_based`
  ueber die bestehende Factory-Map).
- [`../../../../spec/lastenheft.md §24`](../../../../spec/lastenheft.md)
  `GG-DEMO-001..008` (Demo-Anspruch).
- [`../../../../spec/architecture.md §Scenario`](../../../../spec/architecture.md)
  (kanonisches YAML-Schema; Welle-5-Demo nutzt
  produktiv).
- Pattern-Vorbild **Welle-1-ohne-C1**:
  [`../done/M5-welle-1.md`](../done/M5-welle-1.md)
  + Commit `64d5129` (Slice-Doc + Code-Merge
  ohne C1-ADR-Commit; Pattern-Praezedenz fuer
  Welle 5).
- Pattern-Vorbild **Sub-Wellen-Verzicht**:
  Welle 5 ist nicht sub-gesliced, weil die 3
  Decisions kohaerent in einem Demo-Wiring-Slot
  zusammenfallen (vs. Welle-4-Subdivision in 4a
  Replay-Controls + 4b Alarme).
