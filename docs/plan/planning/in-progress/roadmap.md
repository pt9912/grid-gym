# Roadmap — grid-gym

**Status:** Aktiv — Vorbedingungen 1+3+4 geschlossen, M1 abgeschlossen
**Stand:** 2026-05-20 (M1 `Done` mit Welle 0..7; M2 `Done` mit Welle 0..7; Welle 6c abgeschlossen; M3 ist der nächste aktive Slice)
**Bezug:** [Lastenheft](../../../../spec/lastenheft.md), [Architektur](../../../../spec/architecture.md)

---

## 1. Zweck

Diese Roadmap fuehrt die Meilensteine, die sich aus dem Lastenheft und
der Architektur ergeben. Sie ist die Quelle fuer die Status-Spalte
der `GG-TRACE-001`-Implementierungsmatrix
([Lastenheft §27.2](../../../../spec/lastenheft.md#272-anforderung-zu-implementierung))
mit `M[N]`-Markern.

`GG-AR-OPEN-001` (Sprach- und Build-Wahl) ist mit `ADR 0002`
(`Accepted` 2026-05-15) geschlossen. M1 (Tick-Loop-Spine) ist seit
2026-05-17 `Done` — Closure-Notiz in
[`done/M1-tick-loop-spine.md`](../done/M1-tick-loop-spine.md) +
Welle-Tabelle in
[`done/M1-tick-loop-results.md`](../done/M1-tick-loop-results.md).
M2..M6 sind vorbelegt (Scope-Skizze hier, aktive Slice-Plaene
wandern bei Aktivierung nach `next/` bzw. `in-progress/`).
Aktiver Slice: **M3 (Faults + Multi-Agent + Observability)** — Slice-Plan
wird mit M3-Welle-0-Start eroeffnet.

M2 ist abgeschlossen: Slice-Plan ist nach `done/` gewandert
([`done/M2-devices.md`](done/M2-devices.md)) inkl. Welle-7-Closure
(`done/M2-devices-results.md`).

---

## 2. Konvention

- Meilensteine werden fortlaufend numeriert (`M1`, `M2`, …).
- Jeder Meilenstein hat:
  - **Lieferziel** (was wird umgesetzt),
  - **Lastenheft-IDs** (`GG-*`),
  - **Architekturartefakte** (`GG-AR-*`),
  - **DoD-Checkliste** (Markdown-Checkboxen, einzeln pruefbar),
  - **Status** (Pending / In Progress / Done).
- Abgeschlossene Meilensteine wandern als Closure-Notiz nach
  `docs/plan/planning/done/`.
- Themes fuer kommende Meilensteine werden in `docs/plan/planning/next/`
  als Scope-Skizze gefuehrt, sobald die Vorbelegung hier konkret wird.
- DoD-Checkboxen werden NICHT in der Roadmap abgehakt, solange der
  Meilenstein offen ist — die Closure-Notiz in `done/` traegt den
  finalen Stand.

---

## 3. Meilensteine

### M1 — Tick-Loop-Spine (`Done`)

- **Lieferziel:** deterministischer Tick-Loop ohne Geraete:
  `ClockPort` (Driven), `RandomPort` (Driven, eigener ADR),
  Scheduler mit stabiler Tie-Breaking-Regel, Domain-Modelle
  (`Telemetry`, `Command`, `Event`, `Scenario`, `ReplaySample` als
  Frozen-Dataclasses), `canonical_json`-Anbindung an Snapshot-Pfad,
  minimaler FastAPI-Adapter + Postgres-Persistenz fuer `runs`.
  Geraetemodelle (Battery, PV, Load, ...) folgen in M2+.
- **Lastenheft-IDs:** `GG-SIM-001..005`, `GG-DATA-001..005`,
  `GG-ARCH-005..008`, `GG-PRINC-001..006`, `GG-SCN-001..008`,
  `GG-REPLAY-001..003`/`007`, `GG-API-001`/`003`,
  `GG-PERSIST-003`/`009` (minimaler `runs`-Repository).
- **Architekturartefakte:** `GG-AR-COMP-CORE`, `GG-AR-COMP-DOMAIN`,
  `GG-AR-COMP-SCHED`, `GG-AR-PORT-DRN-001` (`ClockPort`),
  `GG-AR-PORT-DRN-003` (`RunRepositoryPort`),
  `GG-AR-PORT-DRN-010` (`RandomPort` — via
  [`ADR 0007`](../../adr/0007-random-port.md)).
- **DoD-Checkliste:**
  - [x] Welle 0 — Vorbereitung (ADR 0007 Provisional, Trigger 001,
        Lock-Refresh) (2026-05-15).
  - [x] Welle 1 — Domain-Modelle (`Quality`/`CommandResult`/
        `RunMetadata`/`TelemetryPoint`/`Command`/`Event`/
        `SnapshotEnvelope`) (2026-05-17).
  - [x] Welle 2 — Driven-Ports (`ClockPort`/`RandomPort` +
        `MersenneTwisterRandomPort` Adapter, ADR 0007 Accepted)
        (2026-05-17).
  - [x] Welle 3 — Scheduler mit Tie-Breaking
        `(time, priority, source, sequence, event_id)` (`GG-ARCH-006`)
        (2026-05-17).
  - [x] Welle 4 — TickLoop + Snapshot-Envelope-Composition
        (`GG-SIM-005`, ADR 0010) (2026-05-17).
  - [x] Welle 5 — Scenario + Replay (`GG-SCN-001..008`,
        `GG-REPLAY-001..003/007`) (2026-05-17).
  - [x] Welle 6a — FastAPI-Adapter + `make openapi-validate` gruen
        (2026-05-17).
  - [x] Welle 6b — `RunRepositoryPort` + `InMemoryRunRepository`
        + FastAPI-Wiring (2026-05-17).
  - [x] Welle 6c — `PostgresRunRepository` + alembic + Integration-
        Tests via testcontainers; Triggers 009 + 010
        (`tests/integration/compose.yml` + `deploy/compose.yml`)
        (2026-05-17).
  - [x] Welle 6d — `make fullbuild` gruen mit explizitem
        `CRITICAL_COV_TARGETS`-Override (Default-Gate haengt an
        M2-`devices/battery`, siehe Abnahme-Hinweis unten)
        (2026-05-17).
  - [x] Welle 7 — Closure-Notiz
        [`done/M1-tick-loop-spine.md`](../done/M1-tick-loop-spine.md)
        + Welle-Tabelle in
        [`done/M1-tick-loop-results.md`](../done/M1-tick-loop-results.md);
        Triggers 009 + 010 nach `done/`, Trigger 015 (Production-
        Image-Hardening) in `open/` (2026-05-17).
  - [x] M1 als Ganzes auf Status `Done` gehoben und Slice-Plan
        nach `done/` gewandert (2026-05-17).
- **Abnahme-Hinweis:** Default-`make gates` (ohne
  `CRITICAL_COV_TARGETS`-Override) bleibt rot, solange
  `devices/battery` als Default-Critical-Target fehlt. Das ist
  per Slice-Plan-§3-Welle-4-§3-Welle-5-Doku erwartet — M1-DoD-
  Box „Welle 6d" akzeptiert den expliziten Override-Pfad als
  M1-Abschluss. Volle Default-Gruen-Linie schliesst M2 (siehe
  M2-DoD).
- **Status:** Done (2026-05-17) — Closure-Notiz
  [`done/M1-tick-loop-spine.md`](../done/M1-tick-loop-spine.md),
  Welle-Tabelle
  [`done/M1-tick-loop-results.md`](../done/M1-tick-loop-results.md).

### M2 — Geraetemodelle

**Slice-Plan:** [`done/M2-devices.md`](../done/M2-devices.md)
(Closure-Notiz); Welle-Tabelle + Abnahme-Belege:
[`done/M2-devices-results.md`](../done/M2-devices-results.md);
Welle-6c-Slice-Begleit:
[`done/welle-6c.md`](../done/welle-6c.md). Forwarder-Stub
unter [`in-progress/M2-devices.md`](M2-devices.md)
(ADR-Pfad-Stabilitaet per ADR 0006 §3).

- **Lieferziel:** produktive Geraetemodelle (Battery/BESS, PV,
  Load, Smart Meter, Grid Connection) als Konsumenten des
  Tick-Loops. `TickResult.emitted_telemetry` ist dann nicht mehr
  leer — Geraete emittieren `TelemetryPoint`-Tupel pro Tick.
  Geraete-Faults (mindestens Schnittstelle) und Snapshot-Versionierung
  pro Geraet.
- **Lastenheft-IDs:** `GG-DEV-001..014`, `GG-BESS-001..008`,
  `GG-GRID-001..007`. Plus Anschluss an
  `GG-SCN-001` (Geraete-Definitionen im Scenario werden produktiv
  konsumiert).
- **Architekturartefakte:** `GG-AR-COMP-DEVICES`, je Geraetetyp
  ein Submodul unter `hexagon/core/devices/`. `RandomPort.sub_port`-
  Konventionen fuer Geraete-Fault-Streams.
- **DoD-Checkliste:**
  - [x] `Battery`/BESS-Modell mit Lade-/Entlade-Vertrag
        (`GG-BESS-001..008`) — M2 Welle 2, ADR 0014 `Accepted`.
  - [x] `PV`-Modell — M2 Welle 3a, ADR 0016 `Accepted`.
        Welle-3-Minimum (konstantes `rated_power_kw`-Modell);
        Generationsprofil-Eingang ist Welle-5-Material.
  - [x] `Load`-Modell — M2 Welle 3b, ADR 0016 `Accepted`.
  - [x] `SmartMeter`-Modell — M2 Welle 4b (`94efb2a`),
        ADR 0018 `Accepted`.
  - [x] `GridConnection`-Modell (`GG-GRID-001..007`) — M2 Welle 4a
        (`b73b44a`), ADR 0017 `Accepted`.
  - [x] `TickLoop.tick()` ruft Geraete-`tick()`s in stabiler
        Reihenfolge auf; Telemetry-Sammlung pro Tick deterministisch
        sortiert — M2 Welle 6a (`27a441f`); Welle-6c (`c31052c`)
        pinnt die Determinismus-Pflicht zusaetzlich per
        Permutations-Property-Test + MVP-Demo-Determinismus-Run.
  - [x] Geraete-Snapshot-Sub-Snapshots in `SnapshotEnvelope`-
        Composition (Trigger 014 generischer Codec in Welle 0a
        geliefert — siehe `done/014-generic-snapshot-format-codec.md`)
        — M2 Welle 6a (`27a441f`), ADR 0015 `Accepted`.
  - [x] Default-`make gates` ohne `CRITICAL_COV_TARGETS`-Override
        gruen — `devices/battery`, `devices/pv`, `devices/load`
        haben ≥ 90 % Line + Branch (Welle-3-Review-C-1 hat den
        Default-`CRITICAL_COV_TARGETS` um PV/Load erweitert).
  - [x] M1-DoD-Restposten (M1 Welle 6d/7) sind als
        `done/M1-tick-loop-spine.md` geschlossen — M1 ist seit
        2026-05-17 `Done`.
- **Status:** Done (2026-05-20). M2-Abschluss-Gate
  `make fullbuild` cache-frei gruen **ohne**
  `CRITICAL_COV_TARGETS`-Override seit Welle-6c-Feat
  (`c31052c`). Welle 7 (M2-Closure, 2026-05-20) hat
  `done/M2-devices.md` + `done/welle-6c.md` +
  `done/M2-devices-results.md` etabliert und 9 SOLLTE-Open-
  Trigger (`016..024`) in `open/` aktiviert.

**Naechster aktiver Slice: M3.**

### M3 — Faults + Multi-Agent + Observability (Naechster aktiver Slice)

- **Lieferziel:** produktive Fault-Injection (`GG-FAULT-001..010`),
  Multi-Agent-Subsystem (`GG-AGENT-001..008`) und
  OpenTelemetry-Anbindung (`GG-OTEL-001..004`).
- **Lastenheft-IDs:** `GG-FAULT-001..010`, `GG-AGENT-001..008`,
  `GG-OTEL-001..004`, `GG-SAFE-001..006` (sicherheitsrelevante
  Pfad-Kennzeichnung der Fault-Klassen).
- **Architekturartefakte:** `GG-AR-COMP-FAULTS`,
  `GG-AR-COMP-AGENTS`, `GG-AR-PORT-DRN-008`
  (`LogPort`/`MetricsPort`/`TracePort`).
- **DoD-Checkliste:**
  - [ ] Fault-Definitions im Scenario werden vor `tick()` validiert
        (`GG-SCN-006`) und im Tick-Loop ausgeloest.
  - [ ] Mindestens ein konkreter Fault-Typ pro
        `Battery`/`Grid`-Achse implementiert (Beispiel:
        `voltage_drop`, `cell_failure`).
  - [ ] Recovery-Verhalten je Fault dokumentiert + getestet.
  - [ ] Multi-Agent-Bus implementiert (`GG-AGENT-001..008`); RL-
        Adapter koennen als separater Folge-Slice angehaengt werden
        (`GG-FUTURE-001/002`).
  - [ ] `LogPort`/`MetricsPort`/`TracePort` mit OTLP-Adapter.
  - [ ] Property-Tests fuer Fault-Determinismus
        (gleicher Seed + Fault-Sequenz → gleicher Telemetry-Export).

### M4 — Protokolladapter (Vorbelegung)

- **Lieferziel:** produktive Driven-Adapter fuer die in Spec §16
  genannten Protokolle (`GG-MQTT/MODB/OPCUA/DNP3/IEC-001`).
- **Lastenheft-IDs:** `GG-MQTT-001..00X`, `GG-MODB-001..00X`,
  `GG-OPCUA-001..00X`, `GG-DNP3-001..00X`, `GG-IEC-001..00X`.
- **Architekturartefakte:** `GG-AR-PORT-DRN-007`
  (`DeviceProtocolPort`), pro Protokoll ein
  `adapters/driven/protocol_<name>/`-Modul.
- **DoD-Checkliste:**
  - [ ] MQTT-Adapter (paho-mqtt) mit Topic-Mapping zu Geraete-
        Telemetry/Commands.
  - [ ] Modbus-Adapter (pymodbus).
  - [ ] OPC-UA-Adapter (asyncua).
  - [ ] DNP3-Adapter (oder dokumentierter Verzicht via
        `Out-of-Scope`-Note).
  - [ ] IEC-61850-Adapter (oder dokumentierter Verzicht).
  - [ ] AC-ADAPTER-LIGHTWEIGHT bleibt fuer alle protocol_*-Module
        gruen (kein Fachlogik-Sickern).
  - [ ] Integration-Tests pro Adapter via testcontainers (analog
        Welle 6c).

### M5 — UI + Demo (Vorbelegung)

- **Lieferziel:** Visualisierungs- und Demo-Layer
  (`GG-UI-001..009`, `GG-DEMO-001..00X`).
- **Lastenheft-IDs:** `GG-UI-001..009`, Demo-System aus Spec §24.
- **Architekturartefakte:** `GG-AR-COMP-UI`,
  `GG-AR-PORT-DRG-002` (`UICommandPort`, sofern getrennt vom
  HTTP-API).
- **DoD-Checkliste:**
  - [ ] Web-UI mit Live-Telemetry-Stream
        (`GG-UI-001..006`).
  - [ ] Scenario-Editor (`GG-UI-006..008`).
  - [ ] Demo-Lauf reproduzierbar via `make demo` o. ae.
  - [ ] UI nutzt nur `GG-API-001`/`002`/`003` — kein direkter
        Kern-Zugriff.

### M6 — Performance + Security + CI/CD-Haertung (Vorbelegung)

- **Lieferziel:** harte Performance-Schranken aus `GG-RT-001..005`,
  Sicherheits-Audit (`GG-SAFE-001..006`,
  `GG-SBOM-001..00X` ueber Trigger 008), CI/CD-Vollausbau
  (`GG-CICD-001..00X`).
- **Lastenheft-IDs:** `GG-RT-001..005`, `GG-SAFE-001..006`,
  `GG-CICD-001..00X`, `GG-DEPLOY-001..00X`.
- **DoD-Checkliste:**
  - [ ] 10.000-Points/s-Benchmark (`GG-RT-005`) reproduzierbar.
  - [ ] SBOM-Generierung im CI (Trigger 008 nach `done/`).
  - [ ] GitHub-Actions-Workflow gegen Python 3.13 + 3.14
        (Spike-0-Closure-D-8 + ADR 0002 §6.1).
  - [ ] Image-Audit (`make image-audit`) inkl. Vuln-Scan in CI.
  - [ ] Container-Smoke-Test mit `deploy/compose.yml`
        (`make runtime` pollt `/health`).

---

## 4. Vorbedingungen

Vor M1 muessen folgende Punkte geklaert sein:

- [x] **`GG-AR-OPEN-001` Sprach- und Build-Wahl** — geschlossen mit
      `ADR 0002` (`Accepted` 2026-05-15) und synchron `ADR 0005`
      (`Accepted` 2026-05-15). Spike-0 Closure-Notiz:
      [`docs/plan/planning/done/spike-0.md`](../done/spike-0.md).
- [x] **`GG-AR-OPEN-002` API/Simulation als ein oder zwei Prozesse**
      — geschlossen mit
      [`ADR 0012`](../../adr/0012-api-simulation-two-processes.md)
      (`Accepted` 2026-05-17): zwei Prozesse, Postgres als
      Persistenz-Bus. Welle-6c-`deploy/compose.yml` hat den
      Pattern de-facto implementiert; ADR 0012 formalisiert
      nachtraeglich. `spec/architecture.md` §19
      `GG-AR-OPEN-002`-Zeile entsprechend auf `Geschlossen`.
- [x] **Initiales Repository-Layout** gemaess der Hexagonalen Sicht
      (`GG-AR-P-002`, `GG-AR-TABU-001..008`) — sprachunabhaengig in
      `spec/architecture.md` §4.2 mit `hexagon/`-Gruppierung fixiert;
      Python-Paketnamen (`src/grid_gym/hexagon/{core,ports}/`,
      `src/grid_gym/adapters/`) durch `ADR 0002` §6.1 (`Accepted`
      2026-05-15) verbindlich.
- [x] **Trigger 001 (Code-Review-Doku + PR-Template)** — Post-
      Acceptance-Vorbedingung aus dem Dritten Spike-0-Review
      ([`done/spike-0-results.md`](../done/spike-0-results.md) §6).
      Erfuellt 2026-05-15 mit
      [`docs/user/code-review.md`](../../../user/code-review.md) und
      `.github/PULL_REQUEST_TEMPLATE.md`; Closure-Notiz in
      [`done/001-code-review-doc.md`](../done/001-code-review-doc.md).
