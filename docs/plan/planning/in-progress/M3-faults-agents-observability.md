# Slice-Plan — M3 Faults + Multi-Agent + Observability — In Progress

**Status:** In Progress — eroeffnet 2026-05-20. Welle 0/1/2/3/4a/4b/5/6
sind abgeschlossen (alle drei Sub-Bereiche inhaltlich fertig:
Faults `Done` 2026-05-20, Multi-Agent `Done` 2026-05-22, Observability
Foundation `Done` 2026-05-23, OTLP-Adapter `Done` 2026-05-25);
**Welle 7 (Closure)** ist der naechste aktive Slice (eroeffnet
2026-05-25 via `M3-welle-7.md`). Drei Sub-Bereiche (Faults,
Multi-Agent, Observability) ueber Welle 0..7 verteilt; M3-Slice-Plan
wandert nach `done/` mit Welle-7-Closure.

**Wellen-Historie:**

- **Welle 0 — Vorabraeumung + Slice-Eroeffnung** — eroeffnet
  2026-05-20, `cfb7a72`/`4bd2673`/`f5de006`/`3e6170d`.

- **Welle 1 — Fault-Foundation** — `Done` 2026-05-20,
  `712d73b`/`7e0a497`/`823eda7`/`79bb50a`.
  - ADR 0022 `Proposed → Provisional`.
  - `FaultInjectableDevice` Sub-Protocol + `FaultPort` Driven-Port +
    Validator-Target-Haertung + TickLoop-Hook.
  - 773 Unit-Tests (+11).

- **Welle 2 — Battery-/Grid-Fault-Konkretisierung** — `Done`
  2026-05-20, `1debd5e..91d44e2` (8 Commits) + C3-Status-Sync.
  - ADR 0025 `Proposed → Provisional` (Fault-Recovery-Pattern,
    Schaerfung-ohne-Supersede zu ADR 0022 §2.4).
  - Battery `cell_failure` + Grid `voltage_drop` +
    `auto-recover-after-N-ticks` + `manual-via-command` produktiv.
  - Adapter-Module unter `hexagon/core/faults/` (architektur-korrekt;
    **nicht** unter `adapters/driven/`, weil Fault-Adapter
    Domain-Orchestrierung sind).
  - 840 Unit-Tests + 14 Integration-Tests (+67 / +3 ggue. Welle 1).
  - Property-Tests (Hypothesis-half-open + Determinismus +
    Seed-Independence); Fault-Demo-Szenario + Postgres-Roundtrip.

- **Welle 3 — Multi-Agent-Foundation** — `Done` 2026-05-21,
  `3dbe6af..d6f66fc` (5 Kern-Commits + 8 Wording-Polish + C3-Sync).
  - ADR 0023 `Proposed → Provisional` (Multi-Agent-Bus +
    Agent-Protocol).
  - **Pattern-Drift gegen ADR 0022:** `AgentMessageBus` als
    Core-Klasse, kein Driven-Port — Architektur §14 schreibt eigenes
    Kernmodul vor; Bus hat keine externe Adapter-Boundary.
  - `Agent`-Sub-Protocol (eigenstaendig, **nicht** DeviceModel-
    erbend) + `AgentMessageBus` mit Snapshot-Surface +
    `AgentMessage`-frozen-dataclass mit `GG-AGENT-004`-Pflicht-
    Feldern + TickLoop-Schritt-D2-Hook (Architektur §6 Schritt 7) +
    `agent_bus`-Builder-Symmetrie + `AgentBusError`-Family.
  - 889 Unit-Tests + 14 Integration-Tests (+49 / 0 ggue. Welle 2).
    Foundation ohne konkrete Agent-Implementer (Welle 4).
  - Code-Review-Folge `d6f66fc` adressiert 9 Findings (1H + 4M + 4L)
    als Schaerfungen-ohne-Supersede (ADR 0011-Pattern).

- **Welle 4a — Multi-Agent-Foundation-Plumbing** — `Done`
  2026-05-21, `a24f733..da18c6d`.
  - ADR 0026 `Proposed → Provisional` (Agent-Drain + Registry +
    Snapshot + Lifecycle-Pattern; Schwester-ADR zu ADR 0023,
    Pattern-Pendant zu ADR 0025).
  - TickLoop-`agents`-Kwarg + Auto-Bus + Duplicate-ID-Fail-Fast +
    `_attach_agents()`-Lifecycle (`set_run_id` + optional
    `_RandomAttachableAgent.attach_random`).
  - **Schritt A0v** (Pre-Clock-Target-Validierung) + **Schritt A0a**
    (Apply nach Clock, vor Schritt A) mit Atomizitaets-Vertrag bei
    `AgentInvalidCommandTargetError`.
  - `AgentMessageBus.consume_for(receiver)` Direct-Inbox-destruktiv
    (Broadcasts bleiben nicht-destruktiv).
  - `agent_bus`/`pending_agent_commands` Sub-Snapshots +
    Resume-Match-Checks fuer Devices/GridModel/LoadOverlays.
  - Sechs neue Error-Klassen in drei Roots: `AgentRegistryError`,
    `AgentCommandDrainError(TickLoopError)`,
    `TickLoopAgentSnapshot*Error`.
  - Welle-3-`_set_agents_for_testing(...)`-Helper entfernt;
    `build_tick_loop(agents=)`-Symmetrie + GridModelBilanz-Overlay-
    Verdrahtung.
  - 921 Unit-Tests + 14 Integration-Tests (+32 / 0 ggue. Welle 3);
    `make gates` A-1 ohne Override gruen.

- **Welle 4b — Multi-Agent-Konkretisierung** — `Done` 2026-05-22,
  `8802dc0..ac7b47f`.
  - ADR 0027 `Proposed → Provisional` (RuleBasedAgent +
    Scenario-Agents-Block-Pattern; Schwester-ADR zu ADR 0026,
    Pattern-Pendant zu ADR 0025).
  - `RuleBasedAgent`-Implementer mit Hybrid Rules + Plugin-Hook
    (Welle-4b-Metric-Whitelist `tick`/`simulation_time`,
    first-match-wins, snapshot-bar).
  - `ScenarioAgent`-Domain + `_assert_agent_list(...)`-Validator +
    `_build_agents(...)`-Factory + `_AGENT_PLUGIN_FACTORIES`-Hook
    (leer; Welle 4c+).
  - `agents.<agent_type>.<agent_id>`-Sub-Snapshot mit bidirektionalem
    Resume-Match-Check; `AgentPlugin`-Sub-Protocol (`@runtime_checkable`).
  - Sieben neue Error-Klassen: `ScenarioUnknownAgentTypeError`,
    `ScenarioUnknownAgentTargetError`,
    `ScenarioInvalidRuleMetricError`,
    `ScenarioInvalidRuleComparatorError`,
    `ScenarioInvalidAgentParamsError`,
    `ScenarioUnknownAgentPluginError`,
    `TickLoopAgentInstanceSnapshotMismatchError`.
  - `build_tick_loop(agents=None)`-Sentinel-Pattern (expliziter
    `()`-Override wird respektiert).
  - Demo-Szenario `tests/integration/scenarios/agents_demo.yaml` mit
    drei zeitgesteuerten Phasen (Idle/Charge/Discharge).
  - 992 Unit-Tests + 19 Integration-Tests (+69 / +5 ggue. Welle 4a).
  - **`make fullbuild` cache-frei gruen ohne Override** (volle CI +
    Runtime-Image + Compose-Smoke + Trivy-Image-Audit) — Welle-4-
    Abnahme-Kriterium aus ADR 0027 §2.5 erfuellt.
  - Begleit-Fix `ac7b47f`: `dep-audit` starlette `1.0.0 → 1.0.1`
    (PYSEC-2026-161).

- **Welle 5 — Observability-Foundation** — `Done` 2026-05-23,
  `7427daf..a690c02` (6 Welle-5-Kern-Commits inkl. C0/C1/C2/
  Hygiene-Folge/coverage-report-Target + C3-Sync).
  - ADR 0024 `Proposed → Provisional` (Observability-Port-Trio
    `LogPort`/`MetricsPort`/`TracePort` als Driven-Ports unter
    `hexagon/ports/driven/observability.py`).
  - 3 Protocols (`@runtime_checkable`, stateless, **keine** OTLP/
    SDK-Typen im Port-Layer — Core bleibt OTLP-frei) +
    `SpanContext`-frozen-dataclass (`trace_id`/`span_id`/
    `parent_span_id` String-basiert) mit `start_span`/`end_span`/
    `record_event`-Surface; `None`-No-Op-Fallback im TracePort
    fuer Adapter-Robustheit.
  - 3 Null-Adapter (`adapters/driven/observability_null/`) mit
    Default-`call_count`+`last_call`-Surface und opt-in
    `record_calls=True` fuer `call_records`+`clear_calls()`.
    NullTraceAdapter manufakturiert deterministische
    `SpanContext`-Instanzen.
  - Additive TickLoop-Hooks (`log_port`/`metrics_port`/
    `trace_port`-Kwargs, Default `None` skippt): `tick.cycle`-
    Span umfasst die Tick-Arbeit; `tick_begin`/`tick_end` Logs;
    `gauge('event_queue_len', ...)` nach `scheduler.pop_due`;
    `increment('tick_count')` am Tick-Ende; `fault.inject`-Span
    um Schritt A2 (ADR 0022 §2.4); `agent.tick`-Span pro
    Agent-Tick in Schritt D2 (ADR 0023 §2.4 + ADR 0026 §2.1).
    Schritt-/Atomizitaets-Vertraege aus ADR 0022/0023/0026
    bleiben unangetastet.
  - Loest ADR 0023 §2.6 Observability-Vorgriff-Verbot auf
    (Welle-3-Klausel).
  - `tick_duration_ms` **nicht** aus TickLoop emittiert —
    `AC-NO-TIME` verbietet Wall-Clock-Zugriff im Core; Welle 6
    OTLP-Adapter instrumentiert das extern.
  - Trigger 006 (`--strict-bytes`) explizit deferred auf Welle 6
    (kein Bytes-Pfad in Welle 5).
  - **Hygiene-Folge** `9ae2376`: ADR 0029 `Accepted` (Schaerfung-
    ohne-Supersede von ADR 0002 §A-1 per ADR 0011-Pattern); 11.
    `tools/arch_check.py`-Contract `AC-NO-COVERAGE-PRAGMA`
    verbietet `# pragma: no cover`/`no branch`/`exclude file`
    in `src/grid_gym/**`. Erstanwendung: 32 Pragma-Vorkommen
    entfernt (29 Protocol-Stubs ueber `^\s*\.\.\.\s*$`-Regex in
    `[tool.coverage.report] exclude_lines` abgedeckt, 4 Dead-Code-
    Stellen geloescht).
  - Make-Target `coverage-report` (Commit `a690c02`):
    `docker build --no-cache-filter coverage-gate` liefert die
    aktuelle Total-Coverage ohne `--no-cache`-Volllauf.
  - 1023 Unit-Tests + 19 Integration-Tests (+31 Unit / 0
    Integration ggue. Welle 4b). Coverage **95.55%** total
    (+1.04 ggue. Welle-4b-94.51% durch Dead-Code-Loeschung).
  - **`make fullbuild` cache-frei gruen ohne Override** —
    Welle-5-Abnahme-Kriterium aus ADR 0024 §4.1 erfuellt.

- **Welle 6 — OTLP-Adapter** — `Done` 2026-05-25,
  `c98ce1a..46dbd6e` (C1 inkl. drei Review-Folgen
  `8eba9ff`/`c99680c`/`54657dc`/`3f887b5`/`c19c69d`/`5493831`,
  C2 `c61ab0d`, C3-Hauptcommit `47a46b0`, C3-Closure-Docs
  `11eb670`, End-of-Wave-Move `245add8`, Pfad-Folge `ac70eda`,
  Trigger-029-Schaerfung `24dfb2e`, Trigger-029-Move `1f8f69a`,
  Trigger-029-Closure `7fbafbb`, Code-Review-Folge `46dbd6e`).
  - Produktiver `adapters/driven/telemetry_otlp/`-Adapter:
    `OtlpLogAdapter`/`OtlpMetricsAdapter`/`OtlpTraceAdapter` (gRPC)
    + `build_otlp_adapters`-Factory + `flush_and_shutdown`-Helper.
  - ADR 0024 §4.5-Schaerfung mit 8 normativen Decisions
    (Compose-Smoke-Determinismus-Pattern, gRPC-Pinning,
    Trace-ID-Determinismus, etc.) per ADR-0011-Pattern ohne
    Supersede.
  - `deploy/compose.yml`-Erweiterung um `otel-collector`-Sibling
    + `deploy/otel-collector-config.yaml` + Trivy-Audit fuer
    den gepinnten Collector-Tag.
  - `tools/wait_otel_collector.py` als externer Liveness-Poll
    (distroless-Image hat keinen in-container Healthcheck).
  - Integration-Smoke `tests/integration/test_otlp_compose_smoke.py`
    mit Tripel-Assert (>= 1 Span `tick.cycle` + >= 1 Metric
    `tick_count` + >= 1 Log `tick_begin`/`tick_end`), gefiltert
    auf per-Lauf eindeutige `service.instance.id`.
  - Trigger 029 (`done/029-otlp-span-grpc-export-edge-case.md`)
    als Fehlbefund geschlossen — vermuteter OTLP-Span-Export-Bug
    war ein Span-Regex-Bug im Smoke-Test (`^Name` ohne Leading-
    Whitespace vs. Debug-Exporter-Padding `    Name           :
    tick.cycle`).
  - `tools/diagnose_otlp_span_export.py` als Matrix-Diagnose-
    Pattern + Internal-Counter-Scrape im Repo erhalten (Operations-
    Affordance).
  - Runbook `docs/user/observability.md` mit Padding-Format-
    Hinweisen + Internal-Counter-Diagnose + Failure-Mode-Pfaden.
  - Neuer 12. arch_check-Contract `AC-OTLP-ADAPTER-NO-TIME`
    (ADR 0024 §4.5.5 D-4): kein `time`/`datetime`-Import in
    `adapters/driven/telemetry_otlp/**`.
  - Code-Review-Folge (`46dbd6e`): H-1 (Sampler-Pin) + 4
    M-Findings + 4 L-Findings + 2 N-Findings als Code-Fixes;
    Sentinel-Test gegen Format-Drift.
  - 1023+ Unit-Tests + 21 Integration-Tests (+0 Unit / +2
    Integration ggue. Welle 5; neu: Compose-Smoke + Format-
    Drift-Sentinel). Coverage-Endstand unveraendert ggue. Welle 5
    (Welle 6 fuegt nur produktiven Adapter-Code hinzu, der ueber
    `CRITICAL_COV_TARGETS` abgedeckt ist).
  - **`make fullbuild` cache-frei gruen ohne Override mit
    OTLP-Collector-Sibling** — Welle-6-Abnahme-Kriterium aus
    ADR 0024 §4.5.7 + M3-Slice-Plan §3 Welle 6 erfuellt.
  - ADR 0024 bleibt `Provisional` — Promotion auf `Accepted` ist
    M3-Welle-7-Material.

**Naechster Schritt:** **Welle 7** (M3-Closure —
ADR 0022/0023/0024 → `Accepted`, Trigger-006-Decision,
`done/M3-results.md`, `roadmap.md` M3 auf `Done`, S-1..S-6-Sweep,
End-of-Wave-Move M3-Slice-Plan → `done/`).

**Datum:** 2026-05-20 (in `in-progress/` direkt eroeffnet,
kein `next/`-Zwischenschritt — M2-Welle-7-Closure hatte M3
bereits als „naechsten aktiven Slice" ausgewiesen); Welle 3
abgeschlossen 2026-05-21; Welle 4a abgeschlossen 2026-05-21;
Welle 4b abgeschlossen 2026-05-22; Welle 5 abgeschlossen
2026-05-23; Welle 6 abgeschlossen 2026-05-25.

**Bezug:**

- [`roadmap.md`](roadmap.md) §3 M3 (Lieferziel, DoD-
  Checkliste, Architekturartefakte).
- M2-Closure-Notiz
  [`done/M2-devices.md`](../done/M2-devices.md) +
  [`done/M2-devices-results.md`](../done/M2-devices-results.md)
  §5 Welle-7-Erbschaft fuer M3+.
- M2-Welle-7-Open-Trigger
  [`open/011`](../open/011-mlrandomport-subseed-width.md)
  (`MLRandomPort`-Sub-Seed-Wortbreite — M3-Multi-Agent-
  Aktivierung) sowie
  [`open/016..024`](../open/) (SOLLTE-Trigger fuer Geraete/
  Netz/Battery — explizit out-of-scope fuer M3, eigene Slices
  nach M3).
- M1-Welle-7-End-to-End-Sweep-Pattern
  [`done/M1-tick-loop-results.md`](../done/M1-tick-loop-results.md)
  §7 (S-1..S-6-Pattern), gespiegelt durch M2 in
  [`done/M2-devices-results.md`](../done/M2-devices-results.md)
  §4.
- Lastenheft §14 Fault Injection (`GG-FAULT-001..010`),
  §15 Multi-Agent-System (`GG-AGENT-001..008`),
  §19 Telemetrie (`GG-OTEL-001..004`),
  §20 Sicherheitsanforderungen (`GG-SAFE-001..006`).
- Architektur §5 Komponentensicht (`GG-AR-COMP-FAULTS`,
  `GG-AR-COMP-AGENTS`, `GG-AR-COMP-OBS`),
  §13 Fault-Injection-Architektur,
  §14 Multi-Agent-Subsystem,
  §15 Beobachtbarkeit;
  §4.2 Driven-Ports-Tabelle mit `GG-AR-PORT-DRN-008`
  (`LogPort`/`MetricsPort`/`TracePort`).
- [`ADR 0007`](../../adr/0007-random-port.md) §5/§6
  (`RandomPort.sub_port` als Fault-Stream-Vehikel; Drift-
  Trigger 011 fuer Multi-Agent).
- [`ADR 0013`](../../adr/0013-device-model-protocol.md) §4
  (`DeviceModel`-Protocol als Hook-Punkt fuer Fault-Injection
  ueber Geraete).

---

## 1. Zweck

M3 liefert drei produktive Subsysteme als Erweiterung des
M2-Geraete-Pfads:

- **Fault-Injection** (`GG-FAULT-001..010`, `GG-SAFE-001..006`):
  Scenario-Schema-Erweiterung fuer `faults`-Block; FaultPort
  + TickLoop-Trigger; mindestens ein konkreter Fault-Typ pro
  Battery- und Grid-Achse (`voltage_drop`, `cell_failure`);
  Recovery-Verhalten dokumentiert + getestet; Determinismus-
  Property-Test pro Fault-Typ.
- **Multi-Agent-Subsystem** (`GG-AGENT-001..008`,
  `GG-AR-COMP-AGENTS`): Agent-Bus + Agent-Protocol;
  Sub-Random-Streams pro Agent; Decision-Loop integriert sich
  in TickLoop; RL-Adapter sind separater Folge-Slice nach M3.
- **Observability** (`GG-OTEL-001..004`, `GG-AR-COMP-OBS`,
  `GG-AR-PORT-DRN-008`): `LogPort`, `MetricsPort`, `TracePort`
  als Driven-Ports; produktiver OTLP-Adapter unter
  `adapters/driven/telemetry-*/` (Architektur §5 Z. 314 fixiert
  diesen Pfad — `*` steht fuer den konkreten Backend-Slug, z. B.
  `telemetry-otlp`); Telemetry-Stream geht ueber `MetricsPort`
  an einen OTLP-Collector; Tick-/Welle-Spans liegen ueber
  `TracePort` an.

M3 schliesst die DoD-Restposten fuer M3 in `roadmap.md §3 M3`
(6 Checkboxen). Welle 7 schliesst M3 in `done/M3-…md` ab.

---

## 2. Erfolgskriterien

1. **Fault-Definitions validiert + ausgeloest**:
   `GG-FAULT-001..010` — Scenario-Validator pruft `faults`-
   Block, TickLoop konsumiert + ruft FaultPort an den
   richtigen Tick-Punkten auf. Pre-Tick-Validation faengt
   Schema-Fehler ab.
2. **Mindestens ein konkreter Fault-Typ pro Battery + Grid**:
   `voltage_drop` (Grid) und `cell_failure` (Battery) als
   Pflicht-Beispiele aus `roadmap.md §3 M3 DoD`. Plus mind.
   1 weiterer Fault-Typ aus `GG-FAULT-001..010` zur
   Robustheits-Demonstration.
3. **Recovery-Verhalten dokumentiert + getestet**: jeder
   Fault hat ein Recovery-Modell (z. B. `auto-recover-after-N-
   ticks`, `manual-via-command`, `permanent`); Recovery-
   Pfade haben Unit-/Property-Tests.
4. **Multi-Agent-Bus implementiert**: `GG-AGENT-001..008` —
   Agent-Registry + Bus + Decision-Loop in TickLoop; RL-
   Adapter werden NICHT in M3 geliefert, aber das Port-
   Interface ist RL-faehig (analog `RandomPort.sub_port`-
   Konvention).
5. **`LogPort`/`MetricsPort`/`TracePort` mit OTLP-Adapter**:
   `GG-AR-PORT-DRN-008` — Driven-Port-Trio mit produktivem
   OTLP-Adapter (`adapters/driven/observability_otlp/`);
   `make fullbuild`-Compose-Smoke laeuft mit OTLP-Collector
   sibling-container und ueberprueft, dass mindestens ein
   Span + ein Metric exportiert wird.
6. **Property-Tests fuer Fault-Determinismus**: gleicher Seed
   + gleiche Fault-Sequenz → gleicher Telemetry-Export +
   gleicher Snapshot-Hash (Welle-3-Scheduler-Permutations-
   Pattern gespiegelt).
7. **Default-`make gates` ohne `CRITICAL_COV_TARGETS`-
   Override gruen**: Default-Liste wird in Welle 1+/3+/5+
   schrittweise um `core/faults`, `core/agents`,
   `ports/driven/observability` erweitert (vor Closure).
8. **`make fullbuild` gruen ohne Override**:
   M3-Abschluss-Gate (analog M2-Welle-6c-Gate). Compose-Smoke
   mit OTLP-Collector als Sibling-Container.
9. **End-to-End-Sweep S-1..S-6 (analog M1-Welle-7 §7,
   M2-Welle-7 §4)** mit M3-spezifischen S-Items (siehe §3
   Welle 0 unten).

**Anti-Erfolgskriterien** (bewusst NICHT in M3):

- Keine RL-Adapter (`GG-FUTURE-001/002`) — Folge-Slice.
- Keine Performance-Benchmarks (`GG-RT-004/005`) — M6.
- Keine SOLLTE-Geraete (`GG-DEV-015..018`) /
  -Netz (`GG-GRID-005..007`) / -Battery (`GG-BESS-006..007`)
  — eigene Slices nach M3 ueber
  [`open/016..024`](../open/).
- Keine M4-Protokolladapter (MQTT/Modbus/OPC-UA/DNP3/IEC) —
  M4.

---

## 3. Liefer-Reihenfolge (Wellen)

**Sub-Slicing-Schwelle** (analog M2 §3, aus M1-Welle-7-Sweep
S-2): Eine Welle wird **vor** dem Start in 2 oder mehr Sub-
Wellen geteilt, wenn

- die Welle zwei oder mehr distinkte Adapter-Module
  gleichzeitig liefert (z. B. Faults-Core + OTLP-Adapter in
  einer Welle wuerden ungeplant zerfallen),
- die DoD-Checkliste der Welle > 6 Items hat, von denen
  mindestens 2 echte Architektur-Entscheidungen sind,
- oder die Welle zwei `*Error`-Subsysteme gleichzeitig
  beruehrt (z. B. FaultError + AgentError gleichzeitig).

Default: Welle-Bezeichnung `Welle Na/Nb/...` mit Eintrag in
den Closure-Ergebnissen.

Wellen sind atomar; jede Welle endet mit einem gruenen
`make fullbuild`-Lauf oder einem dokumentierten Welle-lokalen
`CRITICAL_COV_TARGETS`-Override. Default-Gate-Sprung erfolgt
in den jeweiligen Sub-Bereichs-Wellen (Welle 1/3/5).

### Welle 0 — Vorabraeumung + Slice-Plan-Eroeffnung (in progress)

- Slice-Begleit-Doc [`welle-0.md`](../done/welle-0.md) (C0
  `cfb7a72`).
- M3-Slice-Plan (dieses Dokument, C1).
- M3-Welle-0-Trigger-Triage (C2):
  - Open-Trigger 005 (`pyright`-vs-`mypy`) — M3-Drift-
    Pruefung: M3 nutzt RL-Faehige Multi-Agent-Protocols,
    die generische Protocols stressen. **Aktivierung**:
    pruefen mit M3-Welle-3 (Multi-Agent-Bus).
  - Open-Trigger 006 (`--strict-bytes`) — M3-Drift-Pruefung:
    OTLP-Export laeuft ueber Protobuf-Bytes. **Aktivierung**:
    pruefen mit M3-Welle-5 (Observability-Foundation).
  - Open-Trigger 007 (`pyright` als Pre-Commit-Hook) — Dev-
    Experience-Trigger, M3-nicht-blockend. **Aktivierung**:
    nach M3-Welle-7 oder eigener Dev-Tooling-Slice.
  - Open-Trigger 011 (`MLRandomPort`-Sub-Seed-Wortbreite) —
    explizit M3-Multi-Agent-getriggert. **Aktivierung**:
    M3-Welle-3 (Multi-Agent-Bus) muss entscheiden, ob die
    64-bit-Wortbreite reicht.
  - Open-Trigger 016..024 (M2-SOLLTE-Items) — Drift-Check:
    alle 9 bleiben **out-of-scope** fuer M3. Eigene Slices
    nach M3-Closure.

**Welle-0-Gate-Erwartung:** kein Default-Gate-Sprung; die
Triage-Notiz erweitert nur den Slice-Plan + die welle-0.md.
`make gates` cache-frei gruen ohne Code-Pfad-Aenderung
(Sanity-Check in C2).

### Welle 1 — Fault-Foundation (FaultPort + Scenario-Schema) (`Done` 2026-05-20, Commits `712d73b`/`7e0a497`/`823eda7`/`79bb50a` + C3-Sync)

- ADR-Folge (geplant **ADR 0022**, `Provisional` mit Welle-1-
  Merge, `Accepted` mit Welle-7-Closure) als Erweiterung zu
  [`ADR 0013`](../../adr/0013-device-model-protocol.md) §4:
  Fault-Injection-Protocol + Scenario-Schema-Erweiterung
  fuer `faults`-Block.
- Scenario-Validator-Erweiterung fuer `faults[*]`:
  `start_simulation_time`, `duration_ms`, `target`, `type`,
  `payload`, `recovery` (Strukturvertrag steht in M1 Welle
  5 schon — Welle 1 macht ihn produktiv).
- FaultPort als Driven-Port (`ports/driven/fault.py`); pro
  Geraet-Typ ein FaultPort-Adapter (z. B.
  `BatteryFaultAdapter`).
- TickLoop-Hook: vor `device.tick(...)` ruft TickLoop
  `fault_port.maybe_inject(...)` an.

**Welle-1-Gate:** `make test-unit` gruen mit FaultPort-
Protocol-Test + Scenario-Validator-Tests (Negativ-Pfade).
Default-`CRITICAL_COV_TARGETS` um `core/faults` erweitert.

### Welle 2 — Battery- und Grid-Fault-Konkretisierung (`Done` 2026-05-20, Commits `1debd5e..91d44e2` + C3-Sync)

- `BatteryFault` mit `cell_failure` produktiv:
  `BatteryFaultAdapter` unter `hexagon/core/faults/` (Architektur-
  Korrektur ggue. Welle-1-Plan: Fault-Adapter sind Domain-
  Orchestrierung, **nicht** externe Adapter unter
  `adapters/driven/`); `_cell_failure_active`-Flag auf
  `BatteryDevice`; `_CELL_FAILURE_DERATE = 0.5` halbiert
  `max_discharge_kw` als Hard-Clamp (Safety vor Comfort-Ramp).
- `GridFault` mit `voltage_drop` produktiv:
  `GridFaultAdapter` strukturell symmetrisch zu Battery;
  `_voltage_drop_active` + `_pending_voltage_v` +
  `_current_voltage_v` auf `GridConnectionDevice`; viertes
  Telemetry-Metric `voltage_v` (alphabetisch zwischen `power_kw`
  und `voltage_v`). Fault mutiert **nicht** `power_kw`
  (ADR 0022 §2.4 GridConnection-Voltage/Frequency-Only-
  Constraint).
- Recovery-Verhalten produktiv:
  `auto-recover-after-N-ticks` (Default; half-open
  `[start, end)`-Window analog ADR 0021 §2.5 LoadEvent) +
  `manual-via-command` (`manual-recover-fault`-Command mit
  Pflicht-Payload `fault_id` + `target_device_id`, optional
  `correlation_id`); `permanent` verschoben auf Welle 3+/M6.
- `FaultInjectableDevice(DeviceModel, Protocol)` um symmetrische
  `clear_fault(fault_type)`-Methode erweitert (Welle-2a-Review
  H-2): eliminiert das `cast() + type: ignore`-Pattern fuer
  Protocol-Surface-Asymmetrie.
- Snapshot-Persistierung additiv (kein v2→v3-Bump):
  Battery- + GridConnection-Sub-Snapshots erweitert um
  `fault_state`-Block (ADR 0015 §2.3 erlaubt additive Sub-
  Snapshot-Erweiterung; ADR 0014/0017 bleiben `Accepted`).
- Property-Tests (Hypothesis): Half-open-`[start, end)`-Window
  pro Adapter (Battery + Grid; `assume(duration_ms >= 2000)`
  garantiert distinkte Mid-Window-Probe — Items-7-10-Review
  H-2/L-1) + Per-Seed-Determinismus + Welle-2-Seed-Independence
  (cross-seed-Vergleich pinnt, dass Welle-2-Battery den
  RandomPort tatsaechlich ignoriert — Forward-Pointer auf
  Welle-3-Stochastic-Recovery).
- Fault-Demo-Szenario unter
  `tests/integration/scenarios/fault_demo.yaml` (5 MVP-Devices
  + 2 nicht-ueberlappende Faults: Battery `cell_failure`
  `[5000ms, 15000ms)` + Grid `voltage_drop`
  `[20000ms, 25000ms)`) mit 5 Integration-Tests
  (Determinismus-Byte-Identitaet, Battery-Smoke,
  Voltage-Drop-Window, Postgres-Roundtrip,
  Composite-Order-Invariant).
- `_CompositeFaultPort` Test-Helper unter
  `tests/integration/_fault_composite.py` (Welle-3-Promote-TODO:
  produktiver Composite-Adapter ist Welle-3-Material).
- Symmetrie-Notiz: ADR 0021 §2.4 + ADR 0022 §2.5 dokumentieren
  die `build_tick_loop(fault_port=)`-Signatur-Erweiterung
  (Items-7-10-Review N-1).
- ADR 0025 `Proposed → Provisional` (Fault-Recovery-Pattern,
  Schaerfung-ohne-Supersede zu ADR 0022 §2.4 — ADR 0011-Pattern).

**Welle-2-Gate:** `make test-integration` gruen
(14 Tests inkl. `tests/integration/test_fault_demo_scenario.py`
mit 5 Tests; +3 vs. Welle 1) + `make test-unit`
(840 Tests, +67 vs. Welle 1) + `make gates` (A-1 ohne Override).

### Welle 3 — Multi-Agent-Foundation (AgentBus + Agent-Protocol) (`Done` 2026-05-21, Commits `3dbe6af..d6f66fc` + C3-Sync)

- ADR 0023 `Proposed → Provisional` (Multi-Agent-Bus +
  Agent-Protocol; Pattern-Drift gegen ADR 0022:
  AgentMessageBus als **Core-Klasse**, kein Driven-Port).
- `Agent`-Sub-Protocol unter `hexagon/core/agents/_protocol.py`
  (eigenstaendig, **nicht** DeviceModel-erbend — Agents
  produzieren `Sequence[Command]`, keine TelemetryPoints; ADR
  0013 §2.8-konform).
- `AgentMessageBus`-Core-Klasse unter
  `hexagon/core/agents/bus.py` mit deterministisch sortiertem
  Buffer (Sortier-Vertrag `(simulation_time, sender, sequence)`),
  nicht-destruktiver `drain_for`-Semantik, Snapshot-Roundtrip-
  Surface; `publish(sequence < -1)` und `drain_for("*")`
  werden typisiert abgelehnt (Welle-3-Review-Folge L-2/L-3).
- `AgentMessage`-frozen-dataclass unter
  `hexagon/core/domain/agent_message.py` mit `GG-AGENT-004`-
  Pflicht-Feldern (`simulation_time`, `sender`, `receiver`,
  `message_type`, `payload`, `sequence`). Konsistenz-Pflicht:
  kein `MappingProxyType`-Wrap auf `payload` (Welle-3-Review-
  Folge H-1 — Domain-Layer-Pattern analog ScenarioFault/
  Command/Event).
- TickLoop-Schritt-D2-Hook zwischen Schritt D (zweite Device-
  Iteration) und Schritt E (`grid_model.update`) per
  Architektur §6 Schritt 7; `agent_bus: AgentMessageBus |
  None = None`-Kwarg + `_set_agents_for_testing(...)`-Helper
  (Welle-3-Review-Folge L-1 — Welle 4 erzwingt die produktive
  Registry-API).
- `build_tick_loop`-Builder-Symmetrie (`agent_bus`-Kwarg
  analog Welle-2-`fault_port`); ADR 0021 §2.4-Pattern
  fortgefuehrt.
- `AgentBusError`-Family unter `core/errors.py`:
  Snapshot-Format-Klassen
  (`AgentBusSnapshotNotAMappingError`,
  `AgentBusSnapshotMissingKeysError`,
  `AgentBusSnapshotWrongTypeError`,
  `AgentBusSnapshotVersionError`) plus
  Defensive-Validation-Klassen (`AgentBusInvalidSequenceError`,
  `AgentBusInvalidReceiverError`).
- `CRITICAL_COV_TARGETS`-Default um `core/agents` erweitert
  (10. Ziel-Modul); `agent_message.py` wird via Import-Pfad
  mitabgedeckt — kein separater File-Eintrag noetig
  (Welle-3-Review-Folge M-1).
- Trigger 011 (`MLRandomPort`-Sub-Seed-Wortbreite) bleibt in
  `open/` — Welle-3-Skala (< 100 Sub-Streams) erreicht
  Aktivierungs-Schwelle (10⁶ Sub-Ports) nicht; ADR-Folge zu
  ADR 0007 §5.2 wird in Welle 4 erneut geprueft.
- Welle-4-Folge-Specs (Welle-3-Review-Folge M-3/M-4 + N-2):
  Sub-Random-Stream-Konvention `RandomPort.sub_port(f"agent-
  {agent_id}")` wandert nach Welle 4; Bus-Buffer-Eviction
  (`consume_for(receiver)` oder `evict_before(...)`) ist
  Welle-4-Pflicht; `_attach_agents()`-Lifecycle analog
  `_attach_devices()` mit `set_run_id`-Aufruf ist Welle-4-
  Material.

**Welle-3-Gate:** `make test-unit` gruen (889 Tests, +49 vs.
Welle 2) + `make test-integration` (14 Tests, unveraendert) +
`make gates` (A-1 ohne Override; AC-PORTS-NO-OUT KEPT mit
16 Contracts; `CRITICAL_COV_TARGETS`-Default-Erweiterung um
`core/agents` greift cache-frei).

### Welle 4 — Multi-Agent-Subsystem konkret

Welle 4 wird per M3-Slice-Plan-Sub-Slicing-Schwelle in zwei
Teilwellen geliefert, weil die Scope-Liste 6+ Items und mehrere
echte Architektur-Entscheidungen enthaelt.

#### Welle 4a — Foundation-Plumbing (`In Progress` 2026-05-21)

- ADR 0026 `Proposed → Provisional`: Agent-Drain + Registry +
  Snapshot + Lifecycle-Pattern (Schaerfung zu ADR 0023 ohne
  Supersede).
- TickLoop erhaelt `agents: tuple[Agent, ...] = ()`, Duplicate-
  ID-Fail-Fast, Auto-Bus-Regel bei `agents != () and
  agent_bus is None` und `_attach_agents()` mit `set_run_id` +
  optionalem `attach_random(random_root.sub_port(f"agent-
  {agent_id}"))`.
- Schritt A0 drainet `_pending_agent_commands` in der Folgetick
  per `apply_command(...)`: Target-Validierung vor Clock-/
  Scheduler-Mutation, Apply vor Step-A-Baseline/Profile/Event.
  Die bestehende LoadDevice-Baseline gewinnt auf LoadDevices;
  GridConnection-Agent-Commands zaehlen als manueller Auto-
  Close-Override. Der No-Side-Effect-Fail-Fast gilt fuer
  ungueltige Targets; unerwartete `apply_command(...)`-
  Exceptions propagieren ohne Rollback-Versprechen.
- `AgentMessageBus.consume_for(receiver)` konsumiert nur direkt
  adressierte private Inbox-Nachrichten destruktiv; Broadcasts
  bleiben bis zu registry-aware Fan-out/Watermark
  nicht-destruktiv.
- TickLoop-Snapshot haengt generischen Agent-Foundation-State ein:
  `agent_bus` plus `pending_agent_commands`. Konkrete
  `agents.<agent_type>.<agent_id>`-Snapshots bleiben Welle 4b.
- `build_tick_loop(..., agents=...)`-Symmetrie; der Builder
  spiegelt `scenario.load_events`/`scenario.load_profiles` in
  `GridModelBilanz`, wenn `grid_model_config` vorhanden ist,
  damit GridModel-v2-Overlay-Snapshots die Welle-4a-Resume-
  Match-Checks tragen. Overlay-only-Szenarien ohne GridModel
  bleiben gueltig, bekommen aber keinen snapshot-gestuetzten
  Overlay-Match-Check.

**Welle-4a-Gate:** `make test-unit`, `make test-integration`,
`make gates` und `make fullbuild` gruen ohne Override; kein
konkreter Agent-Implementer und kein Welle-4-End-to-End-Demo-
Szenario in dieser Teilwelle.

#### Welle 4b — RuleBasedAgent + Scenario-Schema

- Mind. ein konkreter Agent-Typ als Beispiel (z. B.
  `RuleBasedAgent` mit fester Regel-Tabelle).
- Agent-Decision-Loop deterministisch + property-tested
  (gleicher Seed + gleicher Welt-Zustand → gleiche
  Entscheidungs-Sequenz).
- `agents`-Top-Level-Block im Scenario-Schema +
  `_assert_agent_list`-Validator + Agent-Factory-Map analog
  `_DEVICE_FACTORIES`.
- Konkrete Agent-Instanz-Snapshots
  `agents.<agent_type>.<agent_id>` additiv zum Welle-4a-
  Foundation-State.

**Welle-4-Gate:** Welle 4b schliesst den zweiten Sub-Bereich ab:
Default-`CRITICAL_COV_TARGETS` enthaelt `core/agents`; `make
fullbuild` gruen ohne Override mit End-to-End-Demo-Szenario.

### Welle 5 — Observability-Foundation (LogPort/MetricsPort/TracePort) (`Done` 2026-05-23, Commits `7427daf..a690c02` + C3-Sync)

- ADR 0024 `Proposed → Provisional` mit Welle-5-C2-Merge `718c177`
  (`Accepted` mit Welle-7-Closure nach Welle-6-OTLP-Compose-Smoke-
  Verifikation) fuer Driven-Port-Trio `LogPort`/`MetricsPort`/
  `TracePort` (`GG-AR-PORT-DRN-008`).
- Ports liegen in `ports/driven/observability.py`. Drei
  `@runtime_checkable`-Protocols + `SpanContext`-frozen-dataclass;
  stateless, keine OTLP/SDK-Typen im Port-Layer (Core bleibt
  OTLP-frei).
- Null-Adapter-Trio unter `adapters/driven/observability_null/`
  fuer Welle-3-Multi-Agent- und Welle-2-Fault-Tests, damit Tests
  nicht zwingend OTLP-Collector brauchen. Default-Surface
  `call_count`+`last_call`; opt-in `record_calls=True` fuer
  `call_records`+`clear_calls()`.
- Trigger 006 (`--strict-bytes`) **deferred** auf Welle 6 (kein
  Bytes-Pfad in Welle 5; Trigger bleibt in `open/` mit Welle-6-
  Aktivierungs-Notiz).
- TickLoop-Hooks rein additiv: `tick.cycle`-Span umfasst die
  Tick-Arbeit, `event_queue_len`-Gauge nach `scheduler.pop_due`,
  `tick_count`-Counter am Tick-Ende, `fault.inject`-/`agent.tick`-
  Spans als Kinder; Schritt-Reihenfolge aus ADR 0022/0023/0026
  unangetastet. `tick_duration_ms` **nicht** aus dem Core
  emittiert — `AC-NO-TIME` verbietet Wall-Clock-Zugriff; Welle-6-
  OTLP-Adapter instrumentiert das extern.
- Hygiene-Folge: ADR 0029 `Accepted` (Schaerfung-ohne-Supersede
  von ADR 0002 §A-1 per ADR 0011-Pattern); 11. arch_check-Contract
  `AC-NO-COVERAGE-PRAGMA` verbietet `pragma: no cover`/`no branch`/
  `exclude file`. 32 Pragma-Vorkommen aus `src/grid_gym/**`
  entfernt (29 Protocol-Stubs ueber Regex-`exclude_lines`-Pattern,
  4 Dead-Code-Stellen geloescht).
- 1023 Unit-Tests + 19 Integration-Tests; Coverage 95.55% total
  (+1.04 ggue. Welle 4b). `make fullbuild` cache-frei gruen ohne
  Override.

### Welle 6 — OTLP-Adapter

- Produktiver `adapters/driven/telemetry-otlp/`-Adapter
  (Pfad gemaess `spec/architecture.md` §5 Z. 314
  `adapters/driven/telemetry-*`) mit OTLP-gRPC- oder
  OTLP-HTTP-Export.
- `deploy/compose.yml`-Erweiterung um OTLP-Collector-Service.
- `make fullbuild`-Compose-Smoke verifiziert mind. ein Span +
  ein Metric exportiert.

**Welle-6-Gate:** `make fullbuild` gruen mit OTLP-Collector-
Sibling, **dritter Sub-Bereich (Observability) abgeschlossen**
(parallel zu Welle-2-Gate „Faults abgeschlossen" und Welle-4-
Gate „Multi-Agent abgeschlossen"). Default-`CRITICAL_COV_TARGETS`
um `adapters/driven/telemetry-otlp` erweitert.

### Welle 7 — Closure (1/2 Tag)

- ADR 0022/0023/0024 (sowie ggf. ADR-Folgen zu Trigger 005/
  006/011 wenn aktiv) auf `Accepted`.
- `done/M3-faults-agents-observability.md` Closure-Notiz +
  `done/M3-results.md` Welle-Tabelle (Pattern analog
  `done/M2-devices-results.md`).
- `roadmap.md`: M3 auf `Done`, M3-DoD-Checkboxen aktivieren,
  `Naechster aktiver Slice: M4` setzen.
- Open-Trigger fuer M3-Restposten (z. B. RL-Adapter aus
  `GG-FUTURE-001/002`).
- M3-Welle-7-End-to-End-Sweep (analog M2-Welle-7 §4):
  S-1..S-6-Verification ist Pflicht-Punkt:
  - S-1 — M3-spezifisches Vorabraeumungs-Item
    (Trigger-Triage in Welle 0).
  - S-2 — Sub-Slicing-Schwelle (§3 Praeambel oben).
  - S-3 — Default-Gate ohne Override.
  - S-4 — kein M3-spezifisches Image-Hardening-Trigger
    (Image-Pin-Trigger aus `M2-Notes` ist optional).
  - S-5 — ADR-Erweiterungs-Pattern fortgefuehrt (3 neue ADRs
    0022/0023/0024 ohne Supersedes).
  - S-6 — Lastenheft-Coverage-Sweep nach M3-Closure (M4-
    Trigger erstellen, falls relevant).

---

## 4. Out-of-Scope (bleibt fuer M4+/M5+/M6+)

- **RL-Adapter** (`GG-FUTURE-001/002`) — eigener Slice nach
  M3-Closure. Multi-Agent-Bus aus Welle 3/4 ist RL-faehig,
  aber der RL-Trainings-Loop bleibt extern.
- **M4-Protokolladapter** (MQTT/Modbus/OPC-UA/DNP3/IEC) —
  M4.
- **SOLLTE-Geraete** (`GG-DEV-015..018`) — Trigger
  [`016..019`](../open/), eigene Slices nach M3.
- **SOLLTE-Netz** (`GG-GRID-005..007`) — Trigger
  [`020..022`](../open/), eigene Slices nach M3.
- **SOLLTE-Battery** (`GG-BESS-006..007`) — Trigger
  [`023..024`](../open/), eigene Slices nach M3.
- **UI / Demo-Seite** (`GG-UI-001..009`) — M5.
- **Performance-Benchmarks** (`GG-RT-004/005`) — M6.
- **SBOM-Generierung** (Trigger 008) — M6 mit Release-
  Workflow.
- **Snapshot-v2→v3-Lese-Migrations-Pfad** (M2-Erbschaft) —
  M6 `GG-PERSIST-*`-Slice.

---

## 5. Risiken und Fallback

- **Drei-Sub-Bereiche-Vermischung**: M3 hat drei verschiedene
  Sub-Bereiche (Faults, Multi-Agent, Observability) — Risiko
  einer Mega-Welle, die zerfaellt. *Fallback*: Wellen 1/2 nur
  Faults; Wellen 3/4 nur Multi-Agent; Wellen 5/6 nur
  Observability. Strikte Sub-Bereichs-Trennung. Falls eine
  Welle die Sub-Slicing-Schwelle ueberschreitet, in Na/Nb
  teilen.
- **ADR-Drift bei drei parallelen Sub-Bereichen**: drei ADRs
  (0022/0023/0024) koennten in verschiedener Reihenfolge
  `Provisional`/`Accepted` werden. *Fallback*: jede ADR
  hat eigene Akzeptanz-Bedingung (Welle-N-Closure); kein
  Querbezug zwischen ADRs erzwungen.
- **OTLP-Performance-Impact**: synchrone OTLP-Exporte koennen
  Tick-Loop-Latenz erhoehen. *Fallback*: async / batched-
  Export, Decision in Welle 5-ADR.
- **Trigger-011-Aktivierung sprengt Welle 3**: wenn die
  64-bit-Sub-Seed-Wortbreite tatsaechlich problematisch ist
  (z. B. fuer RL-Workloads), wird die ADR-Folge zu ADR 0007
  §5.2 ein Snapshot-Schema-Bump erfordern (analog ADR 0015).
  *Fallback*: Welle 3 in 3a/3b teilen; 3b traegt den
  Snapshot-Bump.
- **`make fullbuild`-OTLP-Collector-Sibling**: Compose-Smoke
  haengt jetzt von einem zusaetzlichen Service-Container ab.
  *Fallback*: OTLP-Collector als optionaler Smoke-Schritt
  hinter Feature-Flag, falls Sibling-Boot zu lange dauert.
- **M2-SOLLTE-Trigger-Drift**: 9 Open-Trigger
  (`016..024`) koennten in M3-Sub-Welle hineinrutschen, wenn
  eine Use-Case-Story sie erfordert. *Fallback*: Welle-0-
  Trigger-Triage haelt sie explizit als „out-of-scope fuer
  M3" fest; nur wenn ein Welle-N-Plan einen Trigger
  ausdruecklich konsumiert, wird er hochgenommen.
- **Observability-Ports-Vorgriff durch Multi-Agent/Faults**:
  Multi-Agent (Welle 3) und Faults (Welle 2) wollen
  potenziell schon Decision-/Recovery-Events via
  `LogPort`/`MetricsPort` emittieren, **bevor** Welle 5 die
  Ports ueberhaupt definiert. Welle 5 sagt zwar „Null-Adapter
  fuer Welle-3-/Welle-2-Tests" zu, aber das macht den
  Welle-2/3-Code zwangslaeufig Null-Adapter-aware. *Fallback*:
  ADR 0023 (Welle 3) entscheidet bewusst, ob `AgentBus` die
  Ports schon **injiziert** (= Ports stehen mit Null-Adapter)
  oder erst in Welle 6 verkabelt; gleiche Frage fuer
  FaultPort-Adapter in Welle 2. Konsequenz fuer den
  Welle-Plan: ADR 0023/0022 muss den Pre-Welle-5-Ports-
  Vertrag explizit als Out-of-Scope der Welle markieren oder
  einen Mini-Vorgriff (Ports-Definition vor Welle 5) als
  Welle-1/3-Lieferung dazunehmen.

---

## 6. Wandert nach

- ✓ `in-progress/M3-faults-agents-observability.md` (dieses
  Dokument, eroeffnet 2026-05-20 mit M3-Welle-0).
- `done/M3-faults-agents-observability.md` mit Closure-Notiz
  nach Welle 7.
- `done/M3-results.md` (Welle-Tabelle + Abnahme-Belege,
  Pattern aus `done/M2-devices-results.md`).
- `archive/`-Pfad nur, falls M3 umgeplant wird (z. B. M3
  nur Faults, M4 = Multi-Agent + Observability, M5+ neu
  nummeriert).

Forwarder-Stub-Pflicht entsteht erst, wenn ein
`Accepted`-ADR auf den `in-progress/`-Pfad zeigt (M3-Welle-1
liefert ADR 0022; der Stub kommt dann mit Welle 7 nach M1/M2-
Pattern).

---

## 7. Verifikationspfad

| Erfolg                                                | Verifikation (Dockerfile-Stage via `make <target>`) |
| ----------------------------------------------------- | ---------------------------------------------------- |
| Fault-Schema validiert + TickLoop-Hook                | `make test-unit` mit FaultPort-Protocol-Test + Scenario-Validator-Negativ-Pfaden |
| Battery-`cell_failure` + Grid-`voltage_drop` Faults   | `make test-unit` + `make test-integration` mit `fault_demo.yaml` |
| Recovery-Pfade dokumentiert + getestet                | `make test-unit` mit Recovery-Determinismus-Tests |
| Multi-Agent-Bus + `RuleBasedAgent`-Beispiel           | `make test-unit` mit AgentBus-Property-Test (Decision-Determinismus) |
| `LogPort`/`MetricsPort`/`TracePort` mit OTLP-Adapter  | `make fullbuild` Compose-Smoke mit OTLP-Collector-Sibling |
| Fault-Determinismus Property-Test                     | `make test-unit` mit `hypothesis @given(seed)`-Tests |
| Default-`make gates` ohne Override                    | `make gates` (Default-`CRITICAL_COV_TARGETS` um `core/faults`, `core/agents`, `ports/driven/observability` erweitert) |
| `make fullbuild` gruen ohne Override                  | `make fullbuild` — **M3-Abschluss-Gate** |
| ADR 0022/0023/0024 `Accepted`                         | `docs/plan/adr/0022-*.md`, `0023-*.md`, `0024-*.md` `Accepted` |
| Open-Trigger 011 entschieden                          | ADR-Folge in M3-Welle-3 mit `Accepted`-Status |
| End-to-End-Sweep S-1..S-6                             | `done/M3-results.md §4` mit Per-S-Item-Belegen |
