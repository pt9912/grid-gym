# 082 — Delivery-Audit: SOLLTE-Rest (`— | Trace | should`)

**Status:** **Abgeschlossen (`done/`, 2026-07-14). Doku-only, kein Release.** Dritter
**Verifikations-Slice** (Muster [`080`](080-delivery-audit-sim-replay.md)/[`081`](081-delivery-audit-rest-muss.md)):
auditiert die 11 verbliebenen `— | Trace`-**SOLLTE** (RFC-2119 `should`, seit dem
d-check-v0.42.0-`modality`-Bump sichtbar). **Ergebnis: 6 geliefert (attribuiert),
5 offene/unadressierte SOLLTE** (kein Code, kein ADR, **keine** Deferral-Entscheidung —
bleiben korrekt „—"). Der MUSS-Satz (080/081) ist komplett verifiziert; diese 5 SOLLTE
sind **offen** und brauchen je eine Entscheidung (bauen oder bewusst zurückstellen+festhalten).
**Datum:** 2026-07-14

> **Korrektur (auf Owner-Einwand, 2026-07-15):** Eine frühere Fassung rahmte die 5 als
> „spec-sanktioniert deferred / terminal / nichts zu tun". Das war eine Rationalisierung —
> „unadressiert" ist **nicht** „deferred" (Deferral braucht eine Entscheidung, die es hier
> nicht gibt). Teil B ist entsprechend richtiggestellt.

---

## Motivation

Nach [`080`](080-delivery-audit-sim-replay.md)+[`081`](081-delivery-audit-rest-muss.md)
(kompletter MUSS-Satz, 0 Lücken) der SOLLTE-Rest. Bei SOLLTE ist **„nicht gebaut" kein
Compliance-Bruch** — aber auch **nicht automatisch „gelöst"**. Die 6 **gelieferten**
SOLLTE haben dasselbe „delivered-but-unmapped"-Problem wie die MUSS (ihr „—" ist
irreführend) → verifiziert + attribuiert. Die 5 **nicht gebauten** sind **offen**.

## Teil A — geliefert (6, verifiziert + attribuiert)

| Anforderung | Code-Artefakt | Test |
| --- | --- | --- |
| [`GG-AGENT-002`](../../../../spec/lastenheft.md#gg-agent-002) Isoliert testbare Agenten | `hexagon/core/agents/_protocol.py` (`Agent`-Sub-Protocol, [`ADR 0023`](../../adr/0023-agent-bus-protocol.md)) | `tests/unit/hexagon/core/agents/test_protocol.py` |
| [`GG-AGENT-005`](../../../../spec/lastenheft.md#gg-agent-005) Konkurrierende Regelstrategien | `hexagon/core/agents/rule_based.py` + `bus.py` (Agenten konkurrieren über den Message-Bus) | `tests/unit/hexagon/core/agents/test_rule_based.py`, `test_bus.py` |
| [`GG-AGENT-006`](../../../../spec/lastenheft.md#gg-agent-006) Lokale Agenten-Zustände | `hexagon/core/agents/_protocol.py` + `rule_based.py` (agenten-lokaler State) | `tests/unit/hexagon/core/agents/test_rule_based.py` |
| [`GG-DEV-003`](../../../../spec/lastenheft.md#gg-dev-003) Geräte-Steuerbefehle | `hexagon/core/commands/scenario_command_engine.py` + `POST /control` ([`ADR 0039`](../../adr/0039-run-control-and-status-tracking.md)) | `tests/unit/hexagon/core/commands/test_scenario_command_engine.py`, `tests/unit/adapters/driving/http_api/test_runs_action_router.py` |
| [`GG-OTEL-004`](../../../../spec/lastenheft.md#gg-otel-004) Trace-Export | `hexagon/ports/driven/observability.py` (`TracePort`) + `adapters/driven/telemetry_otlp/` (OTLP-Spans) | `tests/integration/test_otlp_compose_smoke.py` |
| [`GG-SCN-007`](../../../../spec/lastenheft.md#gg-scn-007) Szenario-Replay-Verweise | `hexagon/core/domain/run.py` (`replay_of`) + Replay-Preflight | `tests/unit/composition/test_build_run_driver.py` |

## Teil B — offen / unadressiert (5, keine Deferral-Entscheidung)

Diese 5 SOLLTE sind **nicht gebaut** — und es gibt **keine** bewusste Zurückstellung:
kein Code, kein ADR, keine Deferral-Entscheidung. Sie „stehen nur im Lastenheft". SOLLTE
→ **kein Compliance-Bruch**, aber **offen** (nicht „gelöst"). Ihr `— | should` in der RTM
ist ehrlich = *unadressiert*. Referenziert per **Feature-Namen** (nicht per ID), damit
`doc-trace` sie nicht faelschlich Slice 082 zuschreibt (Footgun aus [`080`](080-delivery-audit-sim-replay.md)):

- **Modbus-Timeout** — **schärfster Fall.** Die Akzeptanz-Bedingung „*wenn der
  Modbus-Adapter implementiert ist*" ist **erfüllt** (`adapters/driven/protocol_modbus/`,
  M4) → die Akzeptanz ist **aktiv und unerfüllt**: es gibt keinen szenario-definierbaren
  Register-Timeout-Fault mit Recovery + Alarm (`connection_loss`/comm-failure ist
  adjazent, aber nicht das; das `timeout` im Modbus-Adapter ist Verbindungs-Config, kein
  Fault). **Echte offene SOLLTE.**
- **SOC-Sprung, Netzwerkpartition** — Bedingung self-referentiell („*wenn [das Feature]
  implementiert ist*"): schwächer signalisiert, aber ebenfalls **unadressiert** (keine
  dedizierten Fault-Typen). SOLLTE-Variante des GG-FAULT-Musters (MUSS-Pendants in
  [`070`](070-gg-fault-004-frequency-drop.md)/[`071`](071-gg-fault-003-nan-injection.md)/[`072`](072-gg-fault-002-stale-data.md) gebaut).
- **TimescaleDB, InfluxDB** (alternative Persistenz-Backends) — self-referentiell, nicht
  implementiert (grid-gym nutzt Postgres). Unadressiert-optional.

**Jede der 5 braucht eine Entscheidung: bauen (Implementierungs-Slice) oder bewusst
zurückstellen + festhalten (Trigger/ADR).** Bisher weder noch.

## Befund

- **6/11 geliefert → attribuiert; 5/11 offen (unadressiert) → korrekt „—".** Der
  `— | Trace`-Satz schrumpft von 11 auf **5**.
- **MUSS-Satz vollständig aufgelöst** ([`080`](080-delivery-audit-sim-replay.md)/[`081`](081-delivery-audit-rest-muss.md),
  0 Lücken). **SOLLTE: 6 geliefert, 5 offen.** Die 5 sind **nicht** „gelöst" — es sind
  **unadressierte** SOLLTE ohne Deferral-Entscheidung; ihr „—" ist ehrlich *offen*, kein
  „bewusster Verzicht".

## DoD

- Die 6 gelieferten SOLLTE haben Code + Test + ID-Verankerung → doc-trace attribuiert
  Slice 082. ✅ (verifiziert). Die 5 offenen SOLLTE bleiben unattribuiert (korrekt — kein
  Feature). ✅
- Die 5 offenen SOLLTE sind als **offen** ausgewiesen (nicht als deferred) → Owner-Entscheidung.
- Doku-only, kein Runtime-Delta → kein Release.

## Bezug

- Muster + Footgun-Konvention: [`080`](080-delivery-audit-sim-replay.md).
- [`docs/plan/traceability.md`](../../traceability.md) (§27, `Slices`-Spalte advisory);
  [`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md) (slice-getrieben).
