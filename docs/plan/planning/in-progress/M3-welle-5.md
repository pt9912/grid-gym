# Welle 5 — Observability-Foundation (LogPort/MetricsPort/TracePort)

**Status:** Done — M3-Welle-5-Closure am 2026-05-23
(`7427daf..a690c02`, 6 Welle-5-Kern-Commits inkl. C0/C1/C2/Hygiene-
Folge/coverage-report-Target + diesem C3-Status-Sync). Welle 5
liefert den **dritten Sub-Bereich** (Observability) aus dem
M3-Slice-Plan und schliesst damit die Sub-Bereichs-Triade ab
(Welle 1+2 Faults, Welle 3+4a+4b Multi-Agent, Welle 5+6
Observability). M3-Welle 4 (Foundation 4a + Konkretisierung 4b)
war Ausgangsbasis (`8802dc0..ac7b47f` + C3-Sync `b5ba33a`).

**DoD-Verifikation (Welle-Schluss):**

- `make fullbuild` cache-frei gruen **ohne** Override (volle CI +
  Runtime-Image + Compose-Smoke + Trivy-Image-Audit). Welle-5-
  Abnahme-Kriterium aus ADR 0024 §4.1 erfuellt. Compose-Smoke-
  Verifikation auf Laufzeit-Stack-Liveness beschraenkt; OTLP-Span-/
  Metric-Export-Assertions bleiben Welle 6.
- `make test-unit`: **1023 Tests gruen** (Welle-4b-Endstand 992 →
  +29 Welle-5-C2 + 2 Hygiene-Folge-Tests = +31 Welle-5-Tests).
- `make test-integration`: **19 Tests gruen** (unveraendert
  gegenueber Welle-4b — Welle 5 fuegt keine Integration-Tests
  hinzu; Multi-Agent- und Fault-Demo-Pfade laufen unveraendert
  mit Default-`None`-Observability-Ports).
- `make gates` A-1 gruen ohne Override: lint, format-check,
  mypy `--strict` (192 source files), arch-check 17/17 contracts
  kept (inkl. neuer `AC-NO-COVERAGE-PRAGMA` per ADR 0029),
  coverage **95.55%** total / 96% line / ~91.76% critical-branch
  (90/85-Schwellen erfuellt; Anstieg +1.04 Punkte gegenueber
  Welle-4b-94.51% durch Dead-Code-Loeschung in der Hygiene-Folge),
  dep-audit gruen.
- ADR 0024: `Proposed → Provisional` (Welle-5-C2-Merge `718c177`).
  `Accepted` mit M3-Welle-7-Closure.
- ADR 0029 `Accepted` (Schaerfung-ohne-Supersede von ADR 0002 §A-1
  per ADR 0011-Pattern; 11. arch_check-Contract
  `AC-NO-COVERAGE-PRAGMA`).
- AC-PORTS-NO-OUT bleibt KEPT (3 neue Driven-Ports unter
  `hexagon/ports/driven/observability.py`, kein Driving-Port-
  Verletzer).
- `AC-NO-TIME` bleibt KEPT — `tick_duration_ms` ist nicht aus
  TickLoop emittiert (Wall-Clock im Core verboten); Welle 6
  OTLP-Adapter instrumentiert das extern.

Kanonische Slice-Spezifikation:
[`M3-faults-agents-observability.md §3 Welle 5`](M3-faults-agents-observability.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht als Ersatz.

**Commit-Sequenz (geplant):**

### C0 — `docs(plan)`: welle-5 Slice-Doc (dieses Dokument)

Eroeffnet Welle 5 mit Scope-Skizze, geplanter Liefer-Reihenfolge,
Risiken und Anti-Scope. Plus `in-progress/README.md`-Sync
(M3-welle-5.md-Eintrag im Bestand).

Per Wave-Self-Close-Commit-Konvention
([`planning/README.md`](../README.md)) **kein Pre-C0-Move** mehr —
welle-4b.md hat sich mit `47abaec` selbst geschlossen.

### C1 — `docs(adr)`: ADR 0024 Proposed + M3-welle-5.md §3-Triage-Resultate

ADR 0024 (Observability-Port-Trio): `LogPort`, `MetricsPort`,
`TracePort` als Driven-Ports unter `ports/driven/observability.py` mit
`GG-AR-PORT-DRN-008`-Kennung. Welle-5-Triage-Resultate (offene
Decision-Items, z. B. Null-Adapter-Default-Verhalten, Trigger-006-
Aktivierungs-Zeitpunkt) werden in §3 dieses Dokuments dokumentiert.

### C2 — `feat(welle-5)`: Observability-Port-Trio + Null-Adapters + Hooks

Produktive Lieferung:

- 3 Port-Protocols (`LogPort` / `MetricsPort` / `TracePort`) in
  `hexagon/ports/driven/observability.py`.
- 3 Null-Adapter (Test-Doubles) in
  `adapters/driven/observability_null/`. Default fuer Welle-2-Fault-
  und Welle-3/4-Multi-Agent-Tests (kein OTLP-Collector noetig).
  - Null-Adapters liefern standardmaessig `call_count` + `last_call` für
    standardisierte Assertions; `record_calls=True` aktiviert vollstaendige
    Call-History (Default: `False`).
- TickLoop-Hooks: `MetricsPort` fuer Tick-Telemetrie (Tick-Dauer,
  Devices/Agents/Faults-Counts), `LogPort` fuer Tick-Logs.
- Agent-Hooks: `LogPort` fuer Agent-Decision-Logs, `TracePort` fuer
  optional Span-Wrapping um `Agent.decide()`.
- Fault-Hooks: `TracePort` fuer Span-Wrapping um `inject_fault()`,
  `LogPort` fuer Fault-Audit-Trail.

Trigger 006 (`--strict-bytes`) Entscheidung am OTLP-Protobuf-Bytes-
Pfad: moeglich, dass `--strict-bytes` in Welle 5 noch nicht
aktiviert wird (Bytes-Vertrag entsteht erst in Welle 6 mit OTLP-
Adapter). Dann bleibt Trigger 006 offen mit Welle-6-Aktivierungs-
Notiz.

### C3 — `docs(plan)`: Welle-5 Status/DoD-Sync

Status `In Progress → Done`. Welle-5-Gate-Beleg
(`make fullbuild` cache-frei gruen ohne Override). M3-Welle 6
(OTLP-Adapter) als naechster Schritt im
[`in-progress/README.md`](README.md) vermerkt.

### End-of-Wave — `chore`: git mv M3-welle-5.md → done/ (rename-only)

Per Wave-Self-Close-Commit-Konvention reiner
`git mv M3-welle-5.md ../done/M3-welle-5.md`. Inhalts-Folge-Edits
(relative Link-Anpassung dieses Dokuments, Bezug-Pfade-Pflege per
[`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md))
in einem unmittelbar nachfolgenden Commit.

---

## 1. Context

M3 liefert drei distinkte Sub-Bereiche entlang der Welle 0..7:

- **Faults** (Welle 1+2) — `Done` 2026-05-20.
- **Multi-Agent** (Welle 3 + 4a + 4b) — `Done` 2026-05-22.
- **Observability** (Welle 5 + 6) — **diese Welle eroeffnet 5.**

Welle 5 ist die Foundation-Welle des Observability-Bereichs: Port-
Trio + Null-Adapter + Hooks in TickLoop/Agents/Faults. Welle 6
folgt mit dem produktiven OTLP-Adapter und der Compose-Smoke-
Verifikation.

Quellen:

- M3-Slice-Plan
  [`M3-faults-agents-observability.md §3 Welle 5`](M3-faults-agents-observability.md)
  (kanonische Spec).
- Lastenheft §19 Telemetrie (`GG-OTEL-001..004`).
- Architektur §4.2 Driven-Ports-Tabelle (`GG-AR-PORT-DRN-008`
  Observability-Port-Trio), §15 Beobachtbarkeit.
- Welle-4b-Closure-Doc
  [`done/welle-4b.md`](../done/welle-4b.md)
  (Welle-4-Abnahme-Belege als Ausgangsbasis).
- Trigger 006
  [`open/006-mypy-strict-bytes.md`](../open/006-mypy-strict-bytes.md)
  (`--strict-bytes`-Entscheidung am Bytes-Vertrag — moeglicher Welle-5-
  oder Welle-6-Konsument).

## 2. Scope

**In-Scope (Welle 5):**

- `LogPort`-Protocol + Null-Adapter.
- `MetricsPort`-Protocol + Null-Adapter.
- `TracePort`-Protocol + Null-Adapter (Span/SpanContext-Surface
  orientiert an OpenTelemetry-Konventionen, ohne OTLP-Bindung).
- Verdrahtung in TickLoop (Tick-Telemetrie + Tick-Logs).
- Verdrahtung in `AgentMessageBus` / Agent-Decision-Pfad.
- Verdrahtung in Fault-Adapter (Fault-Injection-Spans + Audit-Log).
- Null-Adapter liefern default `call_count` + `last_call`; optionaler
  `record_calls=True`-Modus ergänzt full-fidelity `call_records` als
  Test-Assertion-Surface.
- ADR 0024 `Proposed → Provisional`.

**Out-of-Scope (Welle 6+):**

- OTLP-gRPC/HTTP-Export-Adapter — Welle 6.
- OTLP-Collector-Service in `deploy/compose.yml` — Welle 6.
- `make fullbuild`-Compose-Smoke mit Span/Metric-Export-Verifikation
  — Welle 6.
- Dashboards, Alerts, Trace-Korrelation in Multi-Service-Szenarien
  — Post-M3.

## 3. Architektur-Entscheidungen

Formalisiert in
[`ADR 0024`](../../adr/0024-observability-port-trio.md) `Proposed`
(M3-Welle-5-C1, 2026-05-23). Die nachfolgende Liste ist die mit C1
fixierte Triage-Vorgabe; ADR 0024 schreibt sie normativ auf und
ergaenzt Begruendung, Reichweite, Konsequenzen und Out-of-Scope.

- Port-Surface-Form:
  - `Protocol`, optional `@runtime_checkable`, state-los.
  - keine Default-Methoden, keine Seiteneffekte auf Port-Ebene.
  - **Keine** externen OTLP/SDK-Typen in `ports/`-Layer.
- TracePort-Vertrag:
  - kleiner, interner `SpanContext`-Record mit
    `trace_id`, `span_id`, optional `parent_span_id` (String-basiert).
  - `start_span(name: str, *, parent: SpanContext | None = None, attributes: Mapping[str, object] | None = None) -> SpanContext`
  - `end_span(context: SpanContext) -> None`
  - `record_event(context: SpanContext, name: str, attributes: Mapping[str, object] | None = None) -> None`
  - `TracePort` definiert bewusst `SpanContext` als Pflichtparam in beiden Terminal-Methoden; Call-Sites prüfen daher vor dem Aufruf, ob der Kontext vorhanden ist.
  - Falls `None` dennoch geliefert wird, gilt **No-Op** als erlaubtes Fallback-Verhalten (keine Exception, keine Seiteneffekte).
- Null-Adapter-Standardverhalten:
  - default `record_calls=False`, aber `call_count` + `last_call`
    sind immer verfügbar.
  - `record_calls=True` zusätzlich: `call_records` als append-only
    Sequenz + `clear_calls()`.
- TickLoop/Agent/Fault-Hooks:
  - Reihenfolge und Einhängepunkte in C1 fixieren, keine
    bestehende Schritt- oder Broadcast-Reihenfolge veraendern.
- Trigger-006:
  - Entscheidungszeitpunkt bleibt offen; `--strict-bytes`-Freigabe mit
    Welle-6-OTLP-Bytes-Vertrag koordiniert.

## 4. Liefer-Reihenfolge

Siehe Commit-Sequenz oben (C0 → C1 → C2 → C3 → End-of-Wave).

## 5. Critical Files (anticipated)

- `src/grid_gym/hexagon/ports/driven/observability.py` — **neu**
  (`LogPort` + `MetricsPort` + `TracePort`).
- `src/grid_gym/adapters/driven/observability_null/__init__.py` —
  **neu** (`NullLogAdapter` + `NullMetricsAdapter` + `NullTraceAdapter`).
- `src/grid_gym/hexagon/core/simulation/tick_loop.py` — Hooks fuer
  Tick-Telemetrie + Logs.
- `src/grid_gym/hexagon/core/agents/bus.py` /
  `src/grid_gym/hexagon/core/agents/_protocol.py` — Decision-Telemetry.
- `src/grid_gym/hexagon/core/faults/*` — Span-/Audit-Hooks.
- `src/grid_gym/hexagon/core/scenario/loader.py` —
  `build_tick_loop(..., log_port=, metrics_port=, trace_port=)`-
  Symmetrie analog ADR 0021/0022/0023.
- `tools/arch_check.py` — moeglicher neuer AC-Contract (z. B.
  `AC-OBS-NULL-DEFAULT`).

## 6. Verifikationspfad

- `make gates` A-1 gruen ohne Override (lint, format-check, mypy
  `--strict`, arch-check, test-unit, coverage-gate,
  critical-coverage, dep-audit).
- `make test-unit`: alle bestehenden Tests + neue Welle-5-Tests
  gruen (~30-50 zusaetzliche Tests erwartet).
- `make test-integration`: Multi-Agent-Demo
  (`agents_demo.yaml`) + Fault-Demo gruen mit Null-Adapter-
  Default-Verdrahtung.
- `make fullbuild` cache-frei gruen ohne Override
  (Welle-5-Abnahme-Kriterium; Compose-Smoke-Verifikation ohne OTLP-Collector-Asserts).
- `make fullbuild` ist die Gesamtabnahme der Welle; die separaten
  `test-unit`/`test-integration` ACs bleiben dennoch als gezielte
  Welle-5-Regressionen für Ports, Hooks und Null-Adapter bestehen.
- Welle-6-Postcondition: Compose-Smoke-Verifikation der Span-/Metric-
  Export-Pipeline mit produktivem OTLP-Adapter.
- AC-PORTS-NO-OUT bleibt KEPT — 3 neue Driven-Ports, kein
  Driving-Port-Verletzer.

## 7. Risiken

- **R-1** — `--strict-bytes` (Trigger 006) blockiert Welle 6, falls
  in Welle 5 falsch entschieden. *Mitigation:* Entscheidung in Welle 5
  bewusst offen lassen, Welle 6 trifft die Aktivierung am konkreten
  OTLP-Bytes-Pfad. Trigger 006 bleibt `Open`.
- **R-2** — Null-Adapter-Default senkt Test-Coverage (Telemetrie-
  Aufrufe nicht assertierbar). *Mitigation:* Null-Adapters exponieren
  auf dem Default-Pfad strukturierte Call-Oberflaechen (`call_count`,
  `last_call`) und Welle-5-Tests muessen diese mitlaufen.
- **R-3** — `TracePort` ohne OTLP-Konsument ist schwer ohne
  Welle 6 zu validieren. *Mitigation:* Vertrag an OpenTelemetry-
  Span/SpanContext-Konventionen anlehnen; Welle 6 muss kompatibel
  bleiben oder eine Folge-ADR-Schaerfung schreiben.
- **R-4** — ADR-0024-Triage zeigt evtl., dass die Welle 5 in 5a
  (Foundation, ADR 0024 Proposed) + 5b (Verdrahtung) gesplittet
  werden sollte. *Mitigation:* Split offen lassen; C2-Scope nach
  C1-Triage konkretisieren.
- **R-5** — Hook-Verdrahtung in TickLoop/Agents/Faults kann mit
  ADR 0026 (Agent-Drain-Reihenfolge) und ADR 0022 (Fault-Hook-Pfad)
  kollidieren. *Mitigation:* Hooks rein additiv anhaengen, keine
  bestehenden Schritte umstellen; pruefen, dass Schritt A0v/A0a/D2
  ihre Atomizitaets-/Reihenfolge-Vertraege behalten.

## 8. Wandert nach

Per Wave-Self-Close-Commit-Konvention
([`planning/README.md`](../README.md)) — am Ende der Welle-5-
Sequenz reiner `git mv M3-welle-5.md ../done/M3-welle-5.md`, gefolgt von
einem Inhalts-Folge-Commit fuer relative Link-Anpassungen + Bezug-
Pfade-Pflege (ADR 0028).
