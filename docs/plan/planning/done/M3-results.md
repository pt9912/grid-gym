# M3 — Faults + Multi-Agent + Observability — Closure-Ergebnisse

**Status:** Done (2026-05-25). M3-Abschluss-Gate `make fullbuild`
cache-frei gruen **ohne** `CRITICAL_COV_TARGETS`-Override seit
Welle-6-C2 (`c61ab0d`) mit `otel-collector`-Sibling. Alle sechs
M3-ADRs (0022/0023/0024/0025/0026/0027) sind mit Welle-7
auf `Accepted` promoted.
**Bezug:** Slice-Plan
[`M3-faults-agents-observability.md`](../done-archive/M3-faults-agents-observability.md);
Welle-Slice-Begleit
[`M3-welle-5.md`](../done-archive/M3-welle-5.md) (Observability-Foundation),
[`M3-welle-6.md`](../done-archive/M3-welle-6.md) (OTLP-Adapter);
Roadmap [`../in-progress/roadmap.md`](../in-progress/roadmap.md)
§3 M3.

---

## 1. Welle-Tabelle

| Welle | Datum       | Lieferung                                                                                                                                                                                                       | Commits          |
| ----- | ----------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| 0     | 2026-05-20  | Vorabraeumung + Slice-Plan-Eroeffnung (S-1-Trigger-Triage)                                                                                                                                                       | `cfb7a72`, `4bd2673`, `f5de006`, `3e6170d` |
| 1     | 2026-05-20  | [`ADR 0022`](../../adr/0022-fault-injection-protocol.md) `Fault Injection Protocol`; `FaultInjectableDevice`-Sub-Protocol + `FaultPort` Driven-Port + Scenario-Validator-Haertung + TickLoop-Hook (Schritt A2); 773 Unit-Tests (+11)                              | `712d73b`, `7e0a497`, `823eda7`, `79bb50a` |
| 2     | 2026-05-20  | [`ADR 0025`](../../adr/0025-fault-recovery-pattern.md) `Fault Recovery Pattern` (Schaerfung-ohne-Supersede zu [`ADR 0022`](../../adr/0022-fault-injection-protocol.md)); Battery `cell_failure` + Grid `voltage_drop`; Recovery-Engine (`auto-recover-after-N-ticks` + `manual-via-command`); Property-Tests + Fault-Demo-Szenario + Postgres-Roundtrip | `1debd5e..91d44e2` (8 Commits inkl. drei Review-Folgen) |
| 3     | 2026-05-21  | [`ADR 0023`](../../adr/0023-agent-bus-protocol.md) `AgentBus Protocol`; `Agent`-Sub-Protocol + `AgentMessageBus` + `AgentMessage` + TickLoop-Schritt-D2-Hook; Code-Review-Folge mit 9 Findings als [`ADR-0011`](../../adr/0011-schaerfung-ohne-abloesung.md)-Schaerfungen                                    | `3dbe6af..d6f66fc` (5 Kern-Commits + 8 Wording-Polish + C3-Sync) |
| 4a    | 2026-05-21  | [`ADR 0026`](../../adr/0026-agent-drain-registry-pattern.md) `Agent Drain Registry Pattern`; TickLoop-`agents`-Kwarg + Schritt A0v/A0a + `_attach_agents()`-Lifecycle + `consume_for(...)` + Foundation-State-Snapshot + sechs neue Error-Klassen                     | `a24f733..da18c6d` |
| 4b    | 2026-05-22  | [`ADR 0027`](../../adr/0027-rule-based-agent-scenario-pattern.md) `Rule-Based Agent Scenario Pattern`; `RuleBasedAgent` + Scenario-`agents`-Block + bidirektionaler `agents.<type>.<id>`-Sub-Snapshot-Resume-Match + End-to-End-Demo; **`make fullbuild` cache-frei gruen ohne Override** | `8802dc0..ac7b47f` |
| 5     | 2026-05-23  | [`ADR 0024`](../../adr/0024-observability-port-trio.md) `Observability Port Trio` (`LogPort`/`MetricsPort`/`TracePort` als Driven-Ports + `SpanContext` + Null-Adapter-Trio + additive TickLoop-Hooks); [`ADR 0029`](../../adr/0029-no-coverage-pragma-contract.md) [`AC-NO-COVERAGE-PRAGMA`](../../adr/0029-no-coverage-pragma-contract.md) (Hygiene-Folge, `Accepted`); `coverage-report`-Make-Target | `7427daf..a690c02` (6 Welle-5-Kern-Commits) |
| 6     | 2026-05-25  | OTLP-Adapter-Trio (`OtlpLogAdapter`/`OtlpMetricsAdapter`/`OtlpTraceAdapter` gRPC); `build_otlp_adapters`-Factory + `flush_and_shutdown`-Helper; `deploy/compose.yml` `otel-collector`-Sibling; Integration-Smoke mit Tripel-Assert; Runbook `docs/user/observability.md`; [`AC-OTLP-ADAPTER-NO-TIME`](../../adr/0024-observability-port-trio.md) als 12. arch_check-Contract; **`make fullbuild` cache-frei gruen ohne Override mit OTLP-Collector** | `c98ce1a..46dbd6e` (C1 mit drei Review-Folgen + C2 + C3 + Code-Review-Folge inkl. Trigger-029-Fehlbefund-Closure) |
| 7     | 2026-05-25  | Closure: sechs M3-ADRs (0022..0027) `Provisional → Accepted`; Trigger-006-Decision (verschoben mit geschaerftem Aktivierungs-Kriterium); `done/M3-results.md`; `roadmap.md` M3 → `Done`; Open-Trigger fuer RL-Adapter; S-1..S-6-Sweep; End-of-Wave-Move | `c971c6a`, `670a4df`, `d13e1f3`, `92daafc`, `2d0d0d4`, `5480937`, `d1c8aab` + dieser Commit-Stack |

## 2. Abnahme-Belege

- **`make fullbuild`-Gate**: cache-frei gruen **ohne**
  `CRITICAL_COV_TARGETS`-Override seit Welle-6-C2 (`c61ab0d`)
  mit `otel-collector`-Sibling im Compose-Smoke + Trivy-Audit
  fuer beide Tags (`grid-gym-runtime` + `$(OTEL_COLLECTOR_IMAGE)`).
- **Default-`CRITICAL_COV_TARGETS`** (Stand `46dbd6e`):
  ```text
  src/grid_gym/hexagon/core/simulation
  src/grid_gym/hexagon/core/devices/battery
  src/grid_gym/hexagon/core/devices/pv
  src/grid_gym/hexagon/core/devices/load
  src/grid_gym/hexagon/core/devices/grid_connection
  src/grid_gym/hexagon/core/devices/smart_meter
  src/grid_gym/hexagon/core/grid_model
  src/grid_gym/hexagon/core/scenario
  src/grid_gym/hexagon/core/replay
  src/grid_gym/hexagon/core/faults
  src/grid_gym/hexagon/core/agents
  src/grid_gym/adapters/driven/telemetry_otlp
  ```
  Coverage ≥ 90 % Line + Branch auf allen Targets
  (`make coverage-gate-critical`).
- **Unit-Tests**: 1138 (Welle-7-Stand, +376 ggue. M2-Welle-7-
  Stand von 762).
- **Integration-Tests**: 21 (Welle-7-Stand, +12 ggue. M2-Welle-7-
  Stand von 9). Inkl. Welle-2 fault_demo (5), Welle-4b
  agents_demo (5), Welle-6 OTLP-Smoke + Sentinel (2).
- **Total-Coverage**: 96 % line (4702 statements, 150 missed).
- **A-1-Contracts**: 19 (`make arch-check` zeigt
  „Contracts: 7 kept, 0 broken" import-linter + arch_check
  „all contracts kept" 12-stufig). 6 import-linter + 13
  arch_check (inkl. [`AC-NO-COVERAGE-PRAGMA`](../../adr/0029-no-coverage-pragma-contract.md) aus Welle 5 +
  [`AC-OTLP-ADAPTER-NO-TIME`](../../adr/0024-observability-port-trio.md) aus Welle 6 + `AC-TICK-LOOP-PRIVATE-
  RESUME-ERRORS` aus Slice 028).
- **`make image-audit`**: gruen
  (`trivy --ignore-unfixed` ohne HIGH/CRITICAL fuer
  `grid-gym-runtime:latest` und
  `otel/opentelemetry-collector-contrib:0.152.1`).
- **`make dep-audit`**: gruen (pip-audit ohne Schwachstellen;
  inkl. `grpcio` + `opentelemetry-exporter-otlp-proto-grpc`).
- **`make noqa-gate`**: gruen (kein `# noqa`-Marker im Code;
  Slice 027 + Folge-Slices).

## 3. Pro-Welle-Reviews

| Welle | Externer Review                                       | Review-Fix-Commit(s)                                                                  |
| ----- | ----------------------------------------------------- | ------------------------------------------------------------------------------------- |
| 0     | — (S-1-Trigger-Triage und Slice-Plan-Eroeffnung)      | n/a                                                                                   |
| 1     | ✓ Welle-1-Review-Folge                                | in feat-Commits kombiniert (`712d73b..79bb50a`)                                       |
| 2     | ✓ drei Review-Folgen (C2a/C2b/C2c)                    | `93618cf` (C2a), `2844482` (C2b), `91d44e2` (C2c Items-7-10)                          |
| 3     | ✓ Welle-3-Review-Folge (9 Findings 1H + 4M + 4L)      | `d6f66fc` (kombiniert in feat-Commit)                                                 |
| 4a    | ✓ Welle-4a-Review-Folge                               | in feat-Commit kombiniert (`a24f733..da18c6d`)                                        |
| 4b    | ✓ Welle-4b-C2-Review-Folge + dep-audit-Fix            | `11b2ca9` (C2-Review-Folge), `ac7b47f` (starlette-Upgrade PYSEC-2026-161)              |
| 5     | ✓ Welle-5-Review-Folge (H-1 + M-1/-2/-3 + L-1/-3/-4 + N-3) | in `7427daf..a690c02` kombiniert; [`ADR 0029`](../../adr/0029-no-coverage-pragma-contract.md)-Hygiene-Folge separat                |
| 6     | ✓ C1-Review-Folge (H-1..H-3 + M-1..M-6 + L-1/-2/-4) + Code-Review-Folge auf Welle-6-Closure-Stand | `3f887b5` (H), `c19c69d` (M), `5493831` (L), `46dbd6e` (Code-Review-Folge mit H-1 Sampler-Pin + 4 M + 4 L + 2 N) |
| 7     | ✓ M3-Welle-7-End-to-End-Sweep                         | dieser Commit-Stack                                                                   |

## 4. S-1..S-6-Verification (M3-Welle-7-End-to-End-Sweep)

Spiegelt das M2-Welle-7-Pattern (siehe
[`M2-devices-results.md §4`](M2-devices-results.md)); referenziert
[`M3-faults-agents-observability.md §3 Welle 7`](../done-archive/M3-faults-agents-observability.md)
S-1..S-6-Items:

- **S-1 (M3-Vorabraeumungs-Item, Trigger-Triage in Welle 0)** —
  erfuellt in Welle 0 (`cfb7a72..3e6170d`); alle relevanten
  M2-Open-Trigger explizit als out-of-scope fuer M3 markiert
  (SOLLTE-Geraete/-Netz/-Battery bleiben fuer eigene Slices nach
  M3, siehe §5 unten). M3-Welle 0 hat zusaetzlich
  `M3-faults-agents-observability.md §1` als Slice-Plan eroeffnet
  und Sub-Bereichs-Konvention (Faults/Multi-Agent/Observability)
  festgelegt.
- **S-2 (Sub-Slicing-Schwelle)** — erfuellt in
  `M3-faults-agents-observability.md §3 Praeambel`; aktiv
  eingesetzt fuer Welle 4 (4a/4b geteilt; Multi-Agent-
  Konkretisierung war zu gross fuer eine Welle). Welle 5
  und Welle 6 sind als einzelne Wellen unter der
  Schwelle geblieben; Welle 6 selbst hatte interne Sub-Commits
  C0/C1/C2/C3 + Review-Folgen, aber kein Welle-6a/6b-Split.
- **S-3 (Default-Gate ohne Override)** — erfuellt seit
  Welle 4b (`b5ba33a`); Welle 6 (`c61ab0d`) bestaetigt
  `make fullbuild` cache-frei gruen **ohne** Override
  mit OTLP-Collector-Sibling.
- **S-4 (M3-spezifisches Image-Hardening-Trigger)** — kein
  M3-spezifischer Hardening-Trigger erforderlich. Image-Pin-
  Trigger aus M2-Notes ist optional und bleibt M6-Material.
  Welle 6 hat als Nebenbefund den OTLP-Collector-Tag
  (`otel/opentelemetry-collector-contrib:0.152.1`) gepinnt und
  in `make image-audit` mit aufgenommen — keine eigene
  Hardening-ADR noetig.
- **S-5 (ADR-Erweiterungs-Pattern, ohne Supersedes)** — erfuellt
  durch sechs neue M3-ADRs (0022/0023/0024/0025/0026/0027) plus
  eine Hygiene-Folge-ADR (0029 [`AC-NO-COVERAGE-PRAGMA`](../../adr/0029-no-coverage-pragma-contract.md) aus Welle
  5b/Slice 027), alle als Schaerfungen ohne Supersedes ([`ADR 0011`](../../adr/0011-schaerfung-ohne-abloesung.md)-
  Pattern konsequent fortgefuehrt). Verifikation: keine
  Supersedes-Eintraege in den sechs ADRs (manuell geprueft
  per `grep -l "Supersedes:" docs/plan/adr/002[2-7]*.md` — kein
  Treffer).
- **S-6 (Lastenheft-Coverage-Sweep nach M3-Closure)** — erfuellt
  in Welle 0c (initial) + M3-Welle-7-Re-Sweep:
  - [`GG-FAULT-001`](../../../../spec/lastenheft.md#gg-fault-001)..010: erfuellt durch Welle 1+2 ([`ADR 0022`](../../adr/0022-fault-injection-protocol.md) +
    [`ADR 0025`](../../adr/0025-fault-recovery-pattern.md)).
  - [`GG-AGENT-001`](../../../../spec/lastenheft.md#gg-agent-001)..006: erfuellt durch Welle 3+4a+4b ([`ADR 0023`](../../adr/0023-agent-bus-protocol.md) +
    [`ADR 0026`](../../adr/0026-agent-drain-registry-pattern.md) + [`ADR 0027`](../../adr/0027-rule-based-agent-scenario-pattern.md)). [`GG-AGENT-007`](../../../../spec/lastenheft.md#gg-agent-007) (Deadlines) und
    [`GG-AGENT-008`](../../../../spec/lastenheft.md#gg-agent-008) (Async) bleiben Welle-4c+/M5-Material.
  - [`GG-OTEL-001`](../../../../spec/lastenheft.md#gg-otel-001)..004: erfuellt durch Welle 5+6 ([`ADR 0024`](../../adr/0024-observability-port-trio.md) +
    OTLP-Adapter + Compose-Smoke).
  - [`GG-SAFE-001`](../../../../spec/lastenheft.md#gg-safe-001)..006: M6-Material (Sicherheits-Audit-Slice).
  - **RL-Restposten**: [`GG-FUTURE-001`](../../../../spec/lastenheft.md#gg-future-001)/002 (RL-Adapter) wandert
    als neuer Open-Trigger in `open/` (siehe §5 unten).

## 5. Welle-7-Erbschaft fuer M4+/M5+/M6+

Diese Items sind explizit als M3-Closure-Restposten in `open/`
aktiviert oder bleiben aktiv:

**RL-Adapter** ([`GG-FUTURE-001`](../../../../spec/lastenheft.md#gg-future-001)/002 — eigener Slice nach
M3-Closure, der Multi-Agent-Bus aus Welle 3/4 ist RL-faehig,
aber der RL-Trainings-Loop bleibt extern):

- Trigger [`030-rl-adapter`](../open/030-rl-adapter.md) — RL-
  Adapter ueber den AgentBus als externer Trainings-Loop;
  Zielplattform-Triage offen (Gym/PettingZoo vs.
  Ray RLlib vs. Stable-Baselines3).

**Multi-Agent-Erweiterungen** (Welle-4c+/M5):

- [`GG-AGENT-007`](../../../../spec/lastenheft.md#gg-agent-007) (Agent-Deadlines) — Welle 4c oder M5-Folge-
  Slice.
- [`GG-AGENT-008`](../../../../spec/lastenheft.md#gg-agent-008) (Async-Multi-Agent-Bus, `AsyncRandomPort`) —
  M5 oder spaeter; [`ADR 0007`](../../adr/0007-random-port.md) §6 nennt das als bewusst
  zurueckgestellten Folge-Punkt.

**M3-Forward-Linked Triggers** (bereits vor M3 vermerkt, jetzt
re-triaged):

- Trigger 006 (`--strict-bytes`) — *verschoben mit geschaerftem
  Aktivierungs-Kriterium* (M3-Welle-7-C2-Decision, siehe
  [`../done/006-mypy-strict-bytes.md`](../done-archive/006-mypy-strict-bytes.md)
  §Decision). Aktivierung bei M4-Protokolladapter-Binaer-Pfad,
  Snapshot-v2→v3-Migrations-Lese-Pfad oder OTLP-Trace-Roundtrip-
  Test.
- Trigger 029 (OTLP-Span-gRPC-Export-Edge-Case) — *Fehlbefund,
  geschlossen* (Welle-6-Befund: war ein Span-Regex-Bug im Smoke-
  Test, nicht im OTLP-Pfad; siehe
  [`029-otlp-span-grpc-export-edge-case.md`](../done-archive/029-otlp-span-grpc-export-edge-case.md)
  §0 Closure-Befund).

**Diagnose-Tooling-Erbschaft aus Welle 6:**

- `tools/diagnose_otlp_span_export.py` — Matrix-Diagnose mit
  Internal-Counter-Scrape als wiederverwendbares Pattern fuer
  kuenftige OTLP-Debugging-Faelle.
- `deploy/otel-collector-config.yaml`
  `service.telemetry.metrics.readers.pull.exporter.prometheus`-
  Block — echte Operations-Affordance fuer Internal-Counter-
  Scrape.
- `docs/user/observability.md` §4.3-§4.4 — Padding-Format-
  Hinweis pro Signal-Typ + `force_flush()`-Anti-Pattern-
  Warnung (Lerneffekt aus Trigger 029).

**SOLLTE-Geraete/-Netz/-Battery aus M2-Welle-7-Erbschaft**
bleiben weiterhin als eigene Slices nach M3-Closure aktiv
(siehe
[`M2-devices-results.md §5`](M2-devices-results.md), Trigger
[`016..024`](../open/)).

## 6. M3-Wandert-Nach

- ✓ `in-progress/M3-faults-agents-observability.md` (vollzogen
  2026-05-20 mit Welle-0-Start) → `done/M3-faults-agents-
  observability.md` (vollzogen mit Welle-7-End-of-Wave-Move
  in einem nachfolgenden Commit). Forwarder-Stub bleibt in
  `in-progress/` per [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) §3 (Accepted-ADRs zeigen
  weiterhin auf den `in-progress/`-Pfad).
- ✓ `in-progress/M3-welle-5.md` (vollzogen mit Welle-5-End-of-
  Wave) → ✓ `done/M3-welle-5.md`.
- ✓ `in-progress/M3-welle-6.md` (vollzogen mit Welle-6-End-of-
  Wave `245add8`) → ✓ `done/M3-welle-6.md`.
- `in-progress/M3-welle-7.md` (Slice-Begleit, dieses Closure-
  Dokument lebt parallel dazu) → `done/M3-welle-7.md` mit
  End-of-Wave-Move analog Welle 6.
- M4 wechselt jetzt von `Vorbelegung` (in
  `roadmap.md §3 M4`) auf `Naechster aktiver Slice` — der
  M4-Slice-Plan wird mit M4-Welle-0-Start eroeffnet.

## 7. Nicht-vollzogene Items (bewusst)

- **M3-Status-Header in `M3-faults-agents-observability.md`**:
  bleibt nach End-of-Wave-Move `In Progress` als historisches
  Artefakt im Datei-Body (§1..§7 sind die Slice-Plan-Inhalte
  aus der laufenden M3-Phase); der `Done`-Status ist im
  Closure-Block (§0 `**Status:**`) gesetzt. Diese Inkonsistenz
  ist bewusst — der Slice-Plan ist historisch und sollte
  nicht retroaktiv umgeschrieben werden (gleiches Pattern wie
  `done/M1-tick-loop-spine.md` und `done/M2-devices.md`).
- **`tool_version`-Bump**: bleibt auf `0.1.0`
  (`pyproject.toml`); ein Release-Bump kommt mit M6
  ([`GG-CICD-007`](../../../../spec/lastenheft.md#gg-cicd-007) Release-Workflow + Trigger 008 SBOM-
  Aktivierung).
- **Snapshot-v2→v3-Lese-Migrations-Pfad**: M3 hat den Schema-
  Vertrag um Sub-Snapshots (`devices.<typ>.<id>`,
  `grid_model`, `agents.<typ>.<id>`, `agent_bus`,
  `pending_agent_commands`) erweitert. Schema-Bump auf v3 mit
  Lese-Migrations-Pfad bleibt M6-Material
  (`GG-PERSIST-*`-Slice analog M2-Welle-7-Erbschaft).
- **[`GG-AGENT-007`](../../../../spec/lastenheft.md#gg-agent-007) Deadlines + [`GG-AGENT-008`](../../../../spec/lastenheft.md#gg-agent-008) Async**: bleiben
  Welle-4c+/M5-Material (siehe §5 oben).
- **[`GG-SAFE-001`](../../../../spec/lastenheft.md#gg-safe-001)..006 Sicherheits-Audit**: bleibt M6-Material
  (Sicherheits-Audit-Slice in der M6-Vorbelegung).
