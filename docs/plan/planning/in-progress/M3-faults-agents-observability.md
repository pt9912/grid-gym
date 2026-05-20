# Slice-Plan — M3 Faults + Multi-Agent + Observability — In Progress

**Status:** In Progress — eroeffnet 2026-05-20 mit M3-Welle-0
(`cfb7a72`/`4bd2673`/`f5de006`/`3e6170d`). **Welle 1 (Fault-
Foundation) abgeschlossen am 2026-05-20** mit
`712d73b`/`7e0a497`/`823eda7`/`79bb50a` + Status-Sync C3 (diesem
Commit): ADR 0022 `Proposed → Provisional`,
`FaultInjectableDevice` Sub-Protocol + `FaultPort` Driven-Port
+ Validator-Target-Haertung + TickLoop-Hook + 11 neue Tests
(773 Unit-Tests total, +11 ggue. M3-Welle-0-Stand). Drei
distinkte Sub-Bereiche (Faults, Multi-Agent, Observability)
werden ueber Welle 0..7 verteilt geliefert. M3-Slice-Plan
wandert nach `done/` mit Welle-7-Closure.

**Naechster Schritt:** Welle 2 (Battery-Fault + Grid-Fault
konkret: `cell_failure` + `voltage_drop` + Recovery-Logik +
Property-Tests; Adapter unter `adapters/driven/fault_battery/`
und `adapters/driven/fault_grid/`).

**Datum:** 2026-05-20 (in `in-progress/` direkt eroeffnet,
kein `next/`-Zwischenschritt — M2-Welle-7-Closure hatte M3
bereits als „naechsten aktiven Slice" ausgewiesen).

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

- Slice-Begleit-Doc [`welle-0.md`](welle-0.md) (C0
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

### Welle 2 — Battery- und Grid-Fault-Konkretisierung

- `BatteryFault` mit `cell_failure`-Beispiel (SOC-Verlust
  oder Spannungs-Drop).
- `GridFault` mit `voltage_drop`-Beispiel
  (`GridConnectionDevice`-State-Mutation).
- Recovery-Verhalten je Fault: `auto-recover-after-N-ticks`
  als Default; `manual-via-command` als alternativer Pfad.
- Property-Test: gleicher Seed + gleiche Fault-Sequenz →
  byte-identische Telemetry (Pattern aus M2-Welle-6c, siehe
  `done/M2-devices.md` §3 Welle 6c +
  `done/M2-devices-results.md` §3 Zeile „Welle 6c");
  M1-Welle-3-Tie-Breaking-Determinismus
  (`done/M1-tick-loop-results.md`) ist die zweite Referenz.

**Welle-2-Gate:** `make test-integration` gruen mit
End-to-End-Fault-Szenario (`tests/integration/scenarios/
fault_demo.yaml`).

### Welle 3 — Multi-Agent-Foundation (AgentBus + AgentPort)

- ADR-Folge (geplant **ADR 0023**, `Provisional` mit Welle-3-
  Merge, `Accepted` mit Welle-7-Closure) fuer Multi-Agent-Bus +
  AgentPort.
- `Agent`-Protocol + `AgentBus` + Sub-Random-Stream-
  Konvention (`RandomPort.sub_port(f"agent-{id}")`).
- TickLoop-Integration: AgentBus.tick(...) zwischen Device-
  Iteration und GridModel-Update.
- Trigger 011 (`MLRandomPort`-Sub-Seed-Wortbreite) wird hier
  entschieden — ADR-Folge zu ADR 0007 §5.2 entweder zum
  Hochbumpen auf 128 bit oder zur Einfuehrung von
  `MLRandomPort` mit eigener Seeding-Kette.

**Sub-Slicing-Erwartung:** Welle 3 koennte in 3a (AgentBus-
Core) und 3b (Sub-Random-Stream-Konvention + Trigger-011-
Entscheidung) zerfallen, sobald die ADR-Implementation den
Scope der Welle ueberschreitet.

### Welle 4 — Multi-Agent-Subsystem konkret

- Mind. ein konkreter Agent-Typ als Beispiel (z. B.
  `RuleBasedAgent` mit fester Regel-Tabelle).
- Agent-Decision-Loop deterministisch + property-tested
  (gleicher Seed + gleicher Welt-Zustand → gleiche
  Entscheidungs-Sequenz).

**Welle-4-Gate:** Default-`CRITICAL_COV_TARGETS` um
`core/agents` erweitert. `make fullbuild` gruen ohne
Override (zweiter Sub-Bereich abgeschlossen).

### Welle 5 — Observability-Foundation (LogPort/MetricsPort/TracePort)

- ADR-Folge (geplant **ADR 0024**, `Provisional` mit Welle-5-
  Merge, `Accepted` mit Welle-7-Closure) fuer Driven-Port-Trio
  `LogPort`/`MetricsPort`/`TracePort` (`GG-AR-PORT-DRN-008`).
- Ports liegen in `ports/driven/observability.py`.
- M1-Test-Doubles (Null-Adapter) fuer Welle-3-Multi-Agent-
  und Welle-2-Fault-Tests, damit Tests nicht zwingend OTLP-
  Collector brauchen.
- Trigger 006 (`--strict-bytes`) wird hier entschieden —
  OTLP-Protobuf-Bytes-Pfade pruefen.

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
