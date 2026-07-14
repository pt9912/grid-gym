# 082 — Delivery-Audit: SOLLTE-Rest (`— | Trace | should`)

**Status:** **Abgeschlossen (`done/`, 2026-07-14). Doku-only, kein Release.** Dritter
**Verifikations-Slice** (Muster [`080`](080-delivery-audit-sim-replay.md)/[`081`](081-delivery-audit-rest-muss.md)):
auditiert die 11 verbliebenen `— | Trace`-**SOLLTE** (RFC-2119 `should`, seit dem
d-check-v0.42.0-`modality`-Bump sichtbar). **Ergebnis: 6 geliefert (attribuiert),
5 bewusst deferred (bleiben korrekt „—").** Damit ist der **gesamte `— | Trace`-Satz
aufgelöst** — jede Zeile ist entweder geliefert+attribuiert oder deferred-dokumentiert.
**Datum:** 2026-07-14

---

## Motivation

Nach [`080`](080-delivery-audit-sim-replay.md)+[`081`](081-delivery-audit-rest-muss.md)
(kompletter MUSS-Satz, 0 Lücken) der SOLLTE-Rest. Wichtiger Unterschied: bei SOLLTE ist
**„nicht gebaut" kein Compliance-Bruch** — ein Teil ist bewusst optional deferred. Die
6 **gelieferten** SOLLTE haben aber dasselbe „delivered-but-unmapped"-Problem wie die
MUSS (ihr „—" ist irreführend); die werden verifiziert + attribuiert.

## Teil A — geliefert (6, verifiziert + attribuiert)

| Anforderung | Code-Artefakt | Test |
| --- | --- | --- |
| [`GG-AGENT-002`](../../../../spec/lastenheft.md#gg-agent-002) Isoliert testbare Agenten | `hexagon/core/agents/_protocol.py` (`Agent`-Sub-Protocol, [`ADR 0023`](../../adr/0023-agent-bus-protocol.md)) | `tests/unit/hexagon/core/agents/test_protocol.py` |
| [`GG-AGENT-005`](../../../../spec/lastenheft.md#gg-agent-005) Konkurrierende Regelstrategien | `hexagon/core/agents/rule_based.py` + `bus.py` (Agenten konkurrieren über den Message-Bus) | `tests/unit/hexagon/core/agents/test_rule_based.py`, `test_bus.py` |
| [`GG-AGENT-006`](../../../../spec/lastenheft.md#gg-agent-006) Lokale Agenten-Zustände | `hexagon/core/agents/_protocol.py` + `rule_based.py` (agenten-lokaler State) | `tests/unit/hexagon/core/agents/test_rule_based.py` |
| [`GG-DEV-003`](../../../../spec/lastenheft.md#gg-dev-003) Geräte-Steuerbefehle | `hexagon/core/commands/scenario_command_engine.py` + `POST /control` ([`ADR 0039`](../../adr/0039-run-control-and-status-tracking.md)) | `tests/unit/hexagon/core/commands/test_scenario_command_engine.py`, `tests/unit/adapters/driving/http_api/test_runs_action_router.py` |
| [`GG-OTEL-004`](../../../../spec/lastenheft.md#gg-otel-004) Trace-Export | `hexagon/ports/driven/observability.py` (`TracePort`) + `adapters/driven/telemetry_otlp/` (OTLP-Spans) | `tests/integration/test_otlp_compose_smoke.py` |
| [`GG-SCN-007`](../../../../spec/lastenheft.md#gg-scn-007) Szenario-Replay-Verweise | `hexagon/core/domain/run.py` (`replay_of`) + Replay-Preflight | `tests/unit/composition/test_build_run_driver.py` |

## Teil B — bewusst deferred (5, bleiben korrekt „—")

Diese SOLLTE sind **nicht gebaut** — und das ist legitim (optional). Ihr `— | should` in
der RTM ist **korrekt und ehrlich**; sie werden **nicht** attribuiert (kein Feature).
Referenziert per Feature-Namen (nicht per ID), damit `doc-trace` sie nicht faelschlich
Slice 082 zuschreibt (Footgun aus [`080`](080-delivery-audit-sim-replay.md)):

- **3 zusätzliche Fault-Typen** — Modbus-Timeout, SOC-Sprung, Netzwerkpartition: keine
  dedizierten Fault-Typen im Code. Die **SOLLTE-Variante** des GG-FAULT-Musters (die
  MUSS-Pendants wurden in [`070`](070-gg-fault-004-frequency-drop.md)/[`071`](071-gg-fault-003-nan-injection.md)/[`072`](072-gg-fault-002-stale-data.md)
  gebaut). **Trigger-Kandidaten**, falls jemand sie will.
- **2 alternative Persistenz-Backends** — TimescaleDB, InfluxDB: nicht implementiert
  (grid-gym nutzt Postgres). Optional-Alternative, bewusst deferred.

## Befund

- **6/11 geliefert → attribuiert; 5/11 bewusst deferred → korrekt „—".** Der
  `— | Trace`-Satz schrumpft von 11 auf **5** (alle 5 = deferred SOLLTE).
- **Gesamter `— | Trace`-Satz damit aufgelöst:** MUSS ([`080`](080-delivery-audit-sim-replay.md)/[`081`](081-delivery-audit-rest-muss.md))
  komplett verifiziert (0 Lücken); SOLLTE hier (6 geliefert + 5 dokumentiert-deferred).
  Keine ungeklärte Zeile mehr — jedes verbleibende „—" ist ein **bewusster** optionaler Verzicht.

## DoD

- Die 6 gelieferten SOLLTE haben Code + Test + ID-Verankerung → doc-trace attribuiert
  Slice 082. ✅ (verifiziert). Die 5 deferred bleiben unattribuiert (korrekt). ✅
- Doku-only, kein Runtime-Delta → kein Release.

## Bezug

- Muster + Footgun-Konvention: [`080`](080-delivery-audit-sim-replay.md).
- [`docs/plan/traceability.md`](../../traceability.md) (§27, `Slices`-Spalte advisory);
  [`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md) (slice-getrieben).
