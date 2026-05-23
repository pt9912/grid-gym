# Welle 4b — RuleBasedAgent + Scenario-Schema + End-to-End-Demo

**Status:** Done — M3-Welle-4b-Closure am 2026-05-22
(`8802dc0..ac7b47f`, 9 Welle-4b-Kern-Commits inkl. Review-
Folgen + diesem C3-Status-Sync). Welle 4b liefert die
produktive Konkretisierung des Multi-Agent-Subsystems
oberhalb der Welle-4a-Foundation-Plumbing-Schicht
(`a24f733..da18c6d` + Welle-4a-Review-Folge `38272f6`).

**DoD-Verifikation (Welle-Schluss):**

- `make fullbuild` cache-frei gruen **ohne** Override (volle
  CI-Linie `lint + format-check + typecheck + arch-check +
  test-unit + coverage-gate + coverage-gate-critical +
  dep-audit + test-integration + openapi-validate +
  image-audit` plus `runtime`-Build + Compose-Smoke). Das
  ist das **Welle-4-Abnahme-Kriterium** aus ADR 0027 §2.5.
- `make test-unit`: **992 Tests gruen** (Welle-4a-Endstand 923
  → +65 Welle-4b-C2 + 4 Welle-4b-C2-Review-Folge = +69
  Welle-4b-Tests).
- `make test-integration`: **19 Tests gruen** (Welle-4a-
  Endstand 14 → +4 Welle-4b-E2E + 1 SoC-Pinning = +5
  Welle-4b-Integration-Tests).
- `make gates` A-1 gruen ohne Override: lint, format-check,
  mypy `--strict` (90 source files), arch-check 7/7 contracts
  kept, arch-check-imports 7/7 kept 0/7 broken, coverage
  94.51% line / 90.47% critical-branch, dep-audit gruen
  (starlette `1.0.0 → 1.0.1` Upgrade `ac7b47f`).
- ADR 0027: `Proposed → Provisional` (Schwester-ADR zu
  ADR 0026; Pattern-Pendant zu ADR 0025 fuer Welle-2-
  Konkretisierung).
- AC-PORTS-NO-OUT bleibt KEPT.
- Welle-4-Gate `make fullbuild` als Top-Level-Closure ohne
  Override-Mitigation; Compose-Smoke + Trivy-Image-Audit
  laufen produktiv durch.

Welle 4b schliesst zugleich die M3-Welle 4 ab (Foundation 4a +
Konkretisierung 4b), spiegelt damit eins-zu-eins das M3-Welle-1
(Fault-Foundation) → M3-Welle-2 (Fault-Konkretisierung)-Pattern.
Nach Welle-4b-Closure ist das Multi-Agent-Subsystem auf produktivem
Welle-4-Vertragstand und kann Welle 5 (Observability) zur Seite
liefern.

Kanonische Slice-Spezifikation:
[`M3-faults-agents-observability.md §3 Welle 4`](../in-progress/M3-faults-agents-observability.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht als Ersatz.

**Commit-Sequenz (geliefert):**

- Pre-C0 `8802dc0` — `chore(welle-4b): git mv welle-4a.md → done/welle-4a.md` (rename-only).
- Post-Pre-C0 `c055be9` — `docs(plan): fix welle-4a.md relative ref nach Pre-C0-Move`.
- C0 `581e09b` + `d1a6683` (Spot-Check-Folge) — `docs(plan):
  welle-4b Slice-Doc + Out-of-Scope-Schaerfung Trigger 011 /
  GG-AGENT-005`.
- C1 `5995152` + `42b47da` (C1-Review-Folge) —
  `docs(adr): ADR 0027 Proposed + F-1/F-2 + 4 Nits`.
- C2 `95979e5` + `11b2ca9` (C2-Review-Folge) —
  `feat(welle-4b): RuleBasedAgent + Scenario-Agents-Block +
  Property-Tests + End-to-End-Demo` + C2-Review-Folge-Fix
  (build_tick_loop-Sentinel + Plugin-Restore-Welle-4c-
  Verschiebung + SoC-Pinning).
- Dep-Audit-Fix `ac7b47f` — `chore(deps): bump starlette
  1.0.0 → 1.0.1 (PYSEC-2026-161)`.
- C3 (dieser Commit) — `docs(plan): Welle-4b Status/DoD-Sync`
  (ADR 0027 → Provisional, ADR-Index + M3-Plan §3 Welle-4b-
  Done-Tag, welle-4b.md → Done, Welle-4-Gate `make fullbuild`-
  Beleg, Welle 5 (Observability) als naechster Schritt
  vermerkt).

## 1. Context

M3-Welle-4a (`a24f733..da18c6d` + Welle-4a-Review-Folge
`38272f6`) hat die Foundation-Plumbing-Schicht produktiv
abgeschlossen: ADR 0026 `Provisional`, TickLoop-`agents`-
Konstruktor-Kwarg + Auto-Bus + `AgentDuplicateIdError`-Fail-
Fast, Schritt A0v/A0a-Drain mit Atomizitaets-Vertrag,
`_attach_agents()`-Lifecycle mit Sub-Random-Stream-Konvention,
`AgentMessageBus.consume_for(receiver)` Direct-Inbox-Drain,
Agent-Foundation-State-Sub-Snapshots (`agent_bus` +
`pending_agent_commands`), Resume-Match-Checks. 923 Unit-Tests
+ 14 Integration-Tests; `make gates` A-1 ohne Override gruen.

Welle-4a-Foundation hat **keine** konkreten Agent-Implementer
und **keinen** `agents`-Top-Level-Block im Scenario-Schema —
Welle-4a-Tests pinnen alle Pflicht-Pfade via `_NullAgent` und
`_OrderRecordingAgent`-Stubs. Welle 4b setzt darauf auf und
liefert die produktiv konsumierbaren Bausteine.

ADR 0023 §6 + ADR 0026 §7 Anti-Scope listen die Welle-4b-
Pflicht-Themen auf (siehe §2 In-Scope).

## 2. Scope

**In Scope (Welle 4b):**

- **`RuleBasedAgent`-Implementer** (`hexagon/core/agents/
  rule_based.py`): konkreter `Agent`-Implementer mit
  deterministischer Decision-Logik. Surface-Auswahl ist
  Welle-4b-C1-Material (z. B. Regel-Map `device_id →
  TelemetryThreshold → Command-Template`). Implementer
  erfuellt `Agent`-Protocol (Welle-3) und optional
  `_RandomAttachableAgent`-Sub-Protocol (Welle-4a).
- **`agents`-Top-Level-Block im Scenario-Schema** + Validator-
  Hardening + `ScenarioAgent`-Domain-Klasse (analog
  `ScenarioDevice` / `ScenarioFault`). Schema-Validierung:
  Pflicht-Felder (`id`, `type`, `params`), Eindeutigkeit
  von `agent_id`, Unknown-Type-Reject (analog
  `ScenarioUnknownDeviceTypeError`-Pattern,
  `ScenarioUnknownAgentTypeError`).
- **`build_agents(...)` Factory + `build_tick_loop(agents=)`-
  Verdrahtung im Loader** (analog `build_devices` aus
  Welle 6b). Pro `ScenarioAgent`: Factory-Dispatch nach
  `ScenarioAgent.type`, `agent.set_run_id(...)` + optional
  `attach_random(...)` laufen ueber den TickLoop-Konstruktor-
  Lifecycle (Welle-4a-`_attach_agents()`).
- **Konkrete Agent-Instanz-Snapshots** `agents.<agent_type>.
  <agent_id>` in `TickLoop.snapshot()` /
  `from_snapshot(...)` (ADR 0015 §2.3-additiv, kein Schema-
  Bump). Roundtrip-Vertrag analog Device-Snapshot-Pattern
  (ADR 0013 §2.4): `from_snapshot(snapshot())` ist
  byte-stabil.
- **Property-Determinismus-Tests** pro Agent-Implementer
  (`GG-AGENT-003`): gleicher Seed + gleicher Eingabeverlauf
  → identische Command-Sequenz. Property-Tests laufen mit
  `hypothesis` analog Welle-2-Fault-Property-Tests.
- **End-to-End-Demo-Szenario** unter
  `scenarios/agents-demo.yaml` o. ae.: minimales PV + Load
  + Battery + GridConnection-Setup mit einem
  `RuleBasedAgent`, das Battery-SoC-Threshold steuert.
  Demo laeuft 60 s ohne Crash, emittiert Telemetry, Snapshot/
  Restore-Roundtrip ist byte-stabil.
- **Welle-4-Abschluss-Gate** `make fullbuild` ohne Override:
  alle A-1-Gates + Compose-Smoke + Demo-Szenario-Lauf gruen
  ohne `OVERRIDE=…`. Damit ist M3-Welle 4 (Foundation +
  Konkretisierung) abnahmefaehig.

**Out of Scope (Welle 4c oder spaeter — explizit dokumentierte
Forward-Pointer aus ADR 0023 §6 + ADR 0026 §7 + ADR 0027 §7):**

- **Konkrete `AgentPlugin`-Implementer** (`LearnedPolicy`,
  `MPCController` o. ae.) — ADR 0027 §2.3 + §4 + §7: Welle
  4b liefert nur die `AgentPlugin`-Sub-Protocol-Surface +
  `_AGENT_PLUGIN_FACTORIES`-Registry (leer). Konkrete
  Plugins sind Welle 4c+ Material.
- `GG-AGENT-007` Deadlines (Agent-Tick-Budget).
- `GG-AGENT-008` Async (vollstaendiger Async-Vertrag —
  Welle-4-Stand bleibt synchron-deterministisch).
- `LogPort`/`MetricsPort`/`TracePort`-Injektion in Agents
  (ADR 0024-Material, Welle 5/6).
- Multi-Receiver-Broadcast-Watermark (`evict_before(...)`
  o. ae., ADR 0026 §2.4 Forward-Pointer).
- RL-Adapter (`GG-FUTURE-001/002`, ADR 0023 §7) —
  RL-Trainings-Loop bleibt extern; `Agent`-Protocol ist
  RL-faehig, aber kein Welle-4-Material.
- **Trigger 011** (Sub-Seed-Wortbreite) — ADR 0023 §7
  verlangt Welle-4-Konkretisierungs-Pruefung des
  Aktivierungs-Kriteriums (`> 10⁶ Sub-Ports`). Welle-4b-
  Stand: ein konkreter `RuleBasedAgent`-Implementer im
  Demo-Szenario erreicht das Kriterium nicht (< 100
  Agents × ein Per-Agent-Sub-Random-Stream); Trigger 011
  bleibt in `open/`. Naechste Aktivierungs-Pruefung mit
  M3-Welle-7-Closure oder bei produktivem Multi-Strategien-
  Pattern (siehe `GG-AGENT-005`-Forward-Pointer unten).
- In-Tick-Wirksamkeit der Agent-Commands (GG-AGENT-008
  Commit-Reihenfolge bleibt: Commands wirken im Folge-Tick
  via A0v/A0a).
- Mehrere konkurrierende Agent-Implementer mit
  Priorisierungs-Resolution (`GG-AGENT-005`) — ADR 0023 §7
  („Welle 4 oder Welle-4-Folge") raeumt explizit
  Wahlfreiheit ein; Welle 4b nutzt sie, liefert einen
  Implementer-Typ und schiebt Multi-Strategien-
  Priorisierung in Welle 4c+ (kein neues
  Priorisierungs-Konstrukt am TickLoop in Welle 4b).

## 3. Architektur-Entscheidungen (C1-Triage 2026-05-22)

**ADR-Status (Welle-4b-Stand 2026-05-22):**

- [`ADR 0027`](../../adr/0027-rule-based-agent-scenario-pattern.md)
  `Proposed` (2026-05-22 mit Welle-4b-C1). Schwester-ADR zu
  ADR 0026 (Welle-4a-Foundation); Pattern-Pendant zu
  ADR 0025 (Welle-2-Konkretisierung). `Provisional` mit
  Welle-4b-C2-Merge; `Accepted` mit M3-Welle-7-Closure.
- ADR 0023 / ADR 0026 bleiben unveraendert in `Provisional`;
  Welle-4b-Code lebt im durch sie definierten Vertrag.

**Entscheidungen (C1-Triage 2026-05-22, in ADR 0027 fixiert):**

- **D-1 — ADR 0027 statt Decision-Memo** (ADR 0027 §1, §3.3):
  Welle 4b trifft drei substantielle neue Architektur-
  Decisions (Schema-Form, Decision-Surface, Sub-Snapshot-
  Layout) → eigenstaendiges ADR pro Pattern-Konsistenz zu
  ADR 0025 / ADR 0026.
- **D-2 — RuleBasedAgent Hybrid Rules + Plugin-Hook**
  (ADR 0027 §2.3, §3.2): Default-Pfad Threshold-Rules-Liste
  (first-match-wins, geordnete Tuple, snapshot-bar,
  scenario-spezifizierbar); Erweiterungs-Pfad optionaler
  Plugin-Hook mit `_AGENT_PLUGIN_FACTORIES` (Welle 4b leer,
  konkrete Plugins sind Welle 4c+). **Mutual Exclusivity:**
  Rules ODER Plugin, nicht beides — vermeidet Reihenfolge-
  Drift. Neues `AgentPlugin`-Sub-Protocol mit eigenem
  Snapshot-Vertrag.
- **D-3 — `agents`-Schema nested Mapping** (ADR 0027 §2.1,
  §3.1): `agents: {<agent_id>: {type, params}}` (Schema-
  eindeutige IDs, fachliche Map-Semantik). Konsistenz-Bruch
  zu flachen `devices`/`faults`/`events`/`load_events`/
  `load_profiles` als bewusste fachliche Entscheidung
  dokumentiert. Loader iteriert `sorted(agents.keys())` fuer
  Determinismus.
- **D-4 — Demo-Szenario `tests/integration/scenarios/agents_demo.yaml`**
  (ADR 0027 §2.6): Konsistenz zu existing `mvp_demo.yaml`
  und `fault_demo.yaml`; kein neues Top-Level-`scenarios/`-
  Verzeichnis.

## 4. Liefer-Reihenfolge

### Pre-C0 — `chore`: git mv welle-4a.md → done/ (rename-only, `8802dc0`)

Reiner Rename-Commit nach Welle-4a-C3-Closure + Welle-4a-
Review-Folge + Welle-4b-Vorbereitung-Sync. 0 Insertions /
0 Deletions; `git log --follow done/welle-4a.md` bleibt
traceable.

### Post-Pre-C0 — `docs(plan)`: fix welle-4a.md relative ref nach Move (`c055be9`)

Fix der einen broken Reference in `done/welle-4a.md` (Zeile
53: `M3-faults-agents-observability.md` →
`../in-progress/M3-faults-agents-observability.md`). Separater
Commit per `feedback_git_mv`-Konvention.

### C0 — `docs(plan)`: welle-4b Slice-Doc (dieses Dokument)

Eroeffnet Welle 4b mit Scope-Skizze, geplanter Liefer-
Reihenfolge, Risiken und Anti-Scope. Plus `in-progress/
README.md`-Sync: `welle-4a.md`-Eintrag entfernt (jetzt in
`done/`), neuer `welle-4b.md`-Eintrag im Bestand.

### C1 — `docs(adr)`: ADR 0027 Proposed + welle-4b.md §3-Triage-Resultate

[`ADR 0027`](../../adr/0027-rule-based-agent-scenario-pattern.md)
Proposed (2026-05-22): RuleBasedAgent + Scenario-Agents-Block-
Pattern. Fixiert fuenf substantielle Architektur-
Entscheidungen — §2.1 nested-Schema, §2.2 ScenarioAgent +
`_assert_agent_list`-Validator + `build_agents(...)`-Factory,
§2.3 Hybrid Rules + Plugin-Hook (`AgentPlugin`-Sub-Protocol
neu), §2.4 `agents.<type>.<id>`-Sub-Snapshot-Layout
(bidirektionaler Resume-Match), §2.5 Welle-4-Abschluss-Gate
(`make fullbuild` mit Mitigation-Fallback), §2.6 Demo-Pfad.
Plus `welle-4b.md §3`-Update: vier offene Punkte aus C0 in
Entscheidungen D-1..D-4 konsolidiert, ADR 0027 verlinkt.
Plus `docs/plan/adr/README.md`-Eintrag fuer ADR 0027.

### C2 — `feat(welle-4b)`: RuleBasedAgent + Scenario-Schema + Demo + Tests

Produktive Implementation:

- `hexagon/core/agents/rule_based.py` — `RuleBasedAgent`-
  Klasse mit deterministischer Decision-Logik + Snapshot/
  Roundtrip.
- `hexagon/core/scenario/validator.py` + `loader.py` —
  `agents`-Top-Level-Block Validator + `ScenarioAgent`-Domain
  + `build_agents(...)` Factory + `build_tick_loop(agents=)`-
  Verdrahtung.
- `hexagon/core/simulation/tick_loop.py` — Agent-Instanz-
  Sub-Snapshots (`agents.<type>.<id>`) in `snapshot()` /
  `from_snapshot(...)`.
- `tests/unit/hexagon/core/agents/test_rule_based.py` —
  Decision-Logik-Pinning + Snapshot-Roundtrip.
- `tests/unit/hexagon/core/scenario/test_*` —
  `agents`-Schema-Validator + Loader-Forwarding.
- `tests/unit/hexagon/core/simulation/test_tick_loop_welle_
  4b_*.py` — Agent-Instanz-Snapshot + Resume-Match.
- `tests/property/test_rule_based_determinism.py` — Property-
  Test (Seed → Sequenz).
- `tests/integration/test_agents_demo_e2e.py` — End-to-End-
  Demo-Run (60 s, Telemetry, Snapshot/Restore).
- `scenarios/agents-demo.yaml` (oder `tests/fixtures/...`) —
  Demo-Szenario.

### C3 — `docs(plan)`: Welle-4b Status/DoD-Sync

ADR 0027 (oder ADR 0023/0026) Status-Uebergang. M3-Slice-Plan
§3 Welle-4b-Done-Tag. `welle-4b.md` Status `In Progress →
Done`. Welle-4-Gate-Beleg (`make fullbuild` cache-frei gruen
ohne Override). Welle 5 als naechster Schritt im
`in-progress/README.md` vermerkt.

## 5. Critical Files

Files, die zwingend Aenderungen im C2-Commit haben:

- `src/grid_gym/hexagon/core/agents/rule_based.py` — **NEU**
  (RuleBasedAgent-Implementer).
- `src/grid_gym/hexagon/core/agents/__init__.py` —
  Re-Export `RuleBasedAgent`.
- `src/grid_gym/hexagon/core/scenario/validator.py` —
  `agents`-Block-Validierung.
- `src/grid_gym/hexagon/core/scenario/loader.py` —
  `build_agents(...)` + `build_tick_loop(agents=)`-
  Verdrahtung.
- `src/grid_gym/hexagon/core/domain/scenario.py` —
  `ScenarioAgent`-Domain-Klasse + Aufnahme in `Scenario`-
  Tupel.
- `src/grid_gym/hexagon/core/simulation/tick_loop.py` —
  Agent-Instanz-Sub-Snapshot-Schreibe-/Lese-Pfad.
- `src/grid_gym/hexagon/core/errors.py` —
  `ScenarioUnknownAgentTypeError` + ggf.
  `ScenarioDuplicateAgentIdError`.
- `tests/...` — Tests pro Vertrag (siehe C2-Block).
- `scenarios/agents-demo.yaml` oder
  `tests/fixtures/scenarios/agents-demo.yaml` — Demo.

## 6. Verifikationspfad

Welle-4b-Endstand erreicht, wenn alle Punkte gruen:

1. `make test-unit` — Welle-4b-Tests gruen; Welle-4a-Stand
   923 → erwartet ≥ 950 (RuleBasedAgent + Schema + Snapshot
   + Property + Resume bringt ~25-30 neue Tests).
2. `make test-integration` — End-to-End-Demo-Test gruen.
3. `make gates` A-1 cache-frei gruen ohne Override
   (lint, format-check, mypy `--strict`, arch-check,
   coverage ≥ 94 % line + ≥ 90 % branch, critical-coverage
   `core/agents`, dep-audit).
4. `make fullbuild` ohne Override gruen — **Welle-4-
   Abschluss-Gate**: Compose-Smoke + Demo-Szenario-Lauf +
   Trivy-Image-Audit (falls in fullbuild eingeschlossen).
5. ADR-Status-Uebergang (`Proposed → Provisional` oder
   bestehende ADRs unveraendert mit Welle-4b-Hash als
   Provisional-Stand).
6. `make docs-check` gruen (alle Markdown-Refs aufloesbar).
7. AC-PORTS-NO-OUT bleibt KEPT.
8. `grep -rn` keine Welle-4a-Forward-Pointer mit Welle-4b-
   Adresse offen (alle `RuleBasedAgent`/`agents`-Top-Level-
   Forward-Pointer aus Welle-4a-Docs sind aufgeloest).

## 7. Risiken

- **R-1: Determinismus-Drift in `RuleBasedAgent`-Decision-
  Logik.** Wenn die Decision-Surface implizit auf
  Set/Dict-Iteration baut, bricht das Property-Test-
  Determinismus-Pinning (`GG-AGENT-003`). Mitigation:
  Decision-Map als sortiertes Tupel oder explizite
  `sorted(...)`-Aufrufe pro Iteration; Property-Test mit
  Permutations-Input.
- **R-2: Scenario-Schema-Migration.** Wenn `agents`-Block
  in einem Scenario-Schema-Bump (`v1 → v2`) landet, brechen
  alle existierenden Demo-Szenarien. Mitigation:
  optionaler Top-Level-Block (`agents:` darf fehlen,
  default `()`), gleiches Pattern wie `faults:` /
  `load_events:` /  `grid_model:` aus Welle 6b.
- **R-3: Snapshot-Backward-Compat.** Alte Welle-4a-Snapshots
  (ohne `agents.<type>.<id>`-Sub-Snapshots) muessen mit
  Welle-4b-Restore-Pfad ohne Crash lesbar bleiben.
  Mitigation: Welle-4a-Pattern beibehalten (Snapshot-Slot
  optional, Default-leer); Welle-4a-Resume-Match-Check
  bidirektional (`38272f6`) bleibt Pflicht.
- **R-4: `make fullbuild`-Compose-Smoke-Pflichten.**
  Demo-Szenario muss in compose-up + Tick-Loop ohne Crash
  laufen. Wenn der `RuleBasedAgent` z. B. `Decimal`-
  Operationen ausserhalb des localcontext-Vertrags
  durchfuehrt, bricht `make fullbuild`. Mitigation: alle
  Decimal-Operationen im Agent unter
  `_tick_loop_decimal_context`-Schutz (analog Device-
  Implementer-Pattern aus Welle 6).
- **R-5: Welle-4-Gate-Reife.** `make fullbuild` ist in M3
  evtl. noch nicht produktiv (Compose-Smoke-Stage existiert
  vielleicht nicht voll). Mitigation: vor C2-Start Status
  von `make fullbuild` checken; falls Stage fehlt, in C1
  als M3-Welle-5-Vorbereitung markieren und Welle-4b-Gate
  pragmatisch auf `make gates` A-1 + Demo-Szenario-Unit-
  Test reduzieren.
- **R-6: ADR-Scope.** Welle 4b koennte ohne eigenstaendige
  ADR auskommen, wenn alle Decisions in ADR 0023/0026
  bereits gefasst sind. Mitigation: C1-Triage entscheidet;
  internes Decision-Memo in §3 dieses Slice-Docs als
  Fallback dokumentiert.

## 8. Wandert nach

- `done/welle-4b.md` mit M3-Welle-5-Start als Pre-C0 reiner-
  Rename-Commit (Memory-Konvention `feedback_git_mv` strikt,
  Pattern aus Welle-4a-Pre-C0 `a24f733` + Welle-4b-Pre-C0
  `8802dc0`).
- Welle 5 folgt direkt — M3-Slice-Plan §3 sieht Observability
  (LogPort/MetricsPort/TracePort + ADR 0024) als naechsten
  Sub-Bereich nach abgeschlossener Welle 4.
