# Welle 7 — M3-Closure

**Status:** Done — geschlossen 2026-05-25 mit dem End-of-Wave-
Move-Folge-Commit. Welle 0/1/2/3/4a/4b/5/6 sind alle
abgeschlossen; die drei M3-Sub-Bereiche (Faults `Done`
2026-05-20, Multi-Agent `Done` 2026-05-22, Observability
**Foundation `Done` 2026-05-23, OTLP-Adapter `Done`
2026-05-25**) sind inhaltlich fertig. Welle 7 hat die formale
Closure geliefert: sechs M3-ADRs (0022..0027) auf `Accepted`
promoted (C1.1..C1.6), Trigger 006 (`--strict-bytes`)
entschieden (C2: verschoben), `done/M3-results.md` mit Welle-
Tabelle angelegt (C3), `roadmap.md` §3 M3 auf `Done` gesetzt
(C3), Trigger 030 (RL-Adapter) als M3-Restposten in `open/`
aktiviert (C3), S-1..S-6-End-to-End-Sweep ausgewertet (C4,
Detail in `M3-results.md §4`), Slice-Plan-Status-Sync (C5),
`make fullbuild` cache-frei gruen als Sanity (C6), und
End-of-Wave-Move beider Slice-Plan-Dokumente
(`M3-welle-7.md` + `M3-faults-agents-observability.md`) nach
`done/` mit Pfad-Folge-Edits.

**DoD-Checkliste (Welle-7-Abnahme):**

Konvention analog Roadmap §3 M3 — `[ ]` offen, `[x]` erfuellt,
`[~]` partiell. Status beim C0-Stand `In Progress`: alle Items
offen; Haken wandern mit C1/C2/C3-Beleg.

- [x] **ADR 0022 (`Fault Injection Protocol`) → `Accepted`** —
      Closure-Beleg ist Welle-1/2-Lieferung (Faults-Subsystem
      abgeschlossen 2026-05-20). **Erfuellt mit C1.1 `c971c6a`**;
      `Letzte inhaltliche Aenderung`-Pflichtfeld (ADR 0006 §4)
      gesetzt.
- [x] **ADR 0023 (`AgentBus Protocol`) → `Accepted`** —
      Closure-Beleg ist Welle-3/4-Lieferung (Multi-Agent-Subsystem
      abgeschlossen 2026-05-22). **Erfuellt mit C1.2 `670a4df`**;
      `Letzte inhaltliche Aenderung`-Pflichtfeld (ADR 0006 §4)
      gesetzt.
- [x] **ADR 0024 (`Observability Port Trio`) → `Accepted`** —
      Closure-Beleg ist Welle-5/6-Lieferung (OTLP-Adapter +
      Compose-Smoke abgeschlossen 2026-05-25). **Erfuellt mit
      C1.3 `d13e1f3`**; `Letzte inhaltliche Aenderung`-Pflichtfeld
      (ADR 0006 §4) gesetzt. Explizit als M3-Welle-7-Material in
      `done/M3-welle-6.md` DoD vermerkt.
- [x] **ADR 0025 (`Fault Recovery Pattern`) → `Accepted`** —
      Closure-Beleg ist Welle-2-Lieferung (Recovery-Engine +
      Fault-Demo/Property-Tests abgeschlossen 2026-05-20).
      **Erfuellt mit C1.4 `92daafc`**; `Letzte inhaltliche
      Aenderung`-Pflichtfeld (ADR 0006 §4) gesetzt.
- [x] **ADR 0026 (`Agent Drain Registry Pattern`) → `Accepted`** —
      Closure-Beleg ist Welle-4a-Lieferung (Agent-Registry,
      Drain, Lifecycle + Snapshot-Plumbing abgeschlossen
      2026-05-21). **Erfuellt mit C1.5 `2d0d0d4`**; `Letzte
      inhaltliche Aenderung`-Pflichtfeld (ADR 0006 §4) gesetzt.
- [x] **ADR 0027 (`Rule-Based Agent Scenario Pattern`) →
      `Accepted`** — Closure-Beleg ist Welle-4b-Lieferung
      (`RuleBasedAgent`, Scenario-`agents`-Block, Agent-
      Sub-Snapshots + Demo abgeschlossen 2026-05-22).
      **Erfuellt mit C1.6 `5480937`**; `Letzte inhaltliche
      Aenderung`-Pflichtfeld (ADR 0006 §4) gesetzt.
- [x] **Trigger 006 (`--strict-bytes`) Entscheidung** —
      **Erfuellt mit C2** (dieser Commit): Verschoben mit
      geschaerftem Aktivierungs-Kriterium. Befund: aktuell kein
      produktiver `bytes`/`bytearray`-Pfad im Domain-Code (das
      Snapshot-Codec verbietet `bytes`/`bytearray` sogar explizit;
      OTLP-Adapter nutzen Protocol-Buffer-Serialisierung der
      OTel-SDK als Library-interna). Aktivierung wandert in
      `next/`, sobald M4-Protokolladapter (MQTT/Modbus/OPC-UA),
      Snapshot-v2→v3-Lese-Migrations-Pfad oder ein OTLP-Trace-
      Roundtrip-Test einen ersten echten Binaer-Pfad einfuehrt.
      Detail-Dokumentation: [`../open/006-mypy-strict-bytes.md`](../open/006-mypy-strict-bytes.md)
      §Decision + §Aktivierungs-Kriterium.
- [x] **`done/M3-results.md`** angelegt, Pattern analog
      [`done/M2-devices-results.md`](../done/M2-devices-results.md):
      Welle-Tabelle (Welle 0..7 mit Status/Datum/Commit-Range),
      Test-Bilanz pro Welle (Unit + Integration), Coverage-
      Endstand, Closure-Verweis auf alle sechs M3-ADRs.
      **Erfuellt mit C3** (dieser Commit-Stack).
- [x] **`roadmap.md` §3 M3 auf `Done`** — DoD-Checkboxen
      aktivieren (10.000-Punkte-Benchmark bleibt M6, andere
      M3-spezifische Items haken), Status auf `Done`, „Naechster
      aktiver Slice: M4 (Protokolladapter)" gesetzt.
      **Erfuellt mit C3** (dieser Commit-Stack).
- [x] **Open-Trigger fuer M3-Restposten** angelegt:
      - **RL-Adapter** (`GG-FUTURE-001/002`) als
        [`../open/030-rl-adapter.md`](../open/030-rl-adapter.md)
        eroeffnet — `RL-Trainings-Loop bleibt extern`,
        Zielplattform-Triage offen (Gym/PettingZoo / Ray RLlib
        / Stable-Baselines3); Aktivierung bei externer
        RL-Workload, Trigger-026-BESS-Spike oder Welle-4c+-
        Multi-Agent-Erweiterung.
      - Weitere Restposten aus dem S-6-Sweep
        (`GG-AGENT-007/008`, `GG-SAFE-001..006`,
        Snapshot-v2→v3-Migration) bleiben in `done/M3-
        results.md` §5/§7 dokumentiert ohne eigenen
        Trigger — sie sind entweder explizit M5/M6-Material
        oder als Welle-4c+/M5-Erweiterung markiert.
      **Erfuellt mit C3** (dieser Commit-Stack).
- [x] **End-to-End-Sweep S-1..S-6** (Pflicht-Punkt aus
      `M3-faults-agents-observability.md §3 Welle 7`, Pattern
      analog M2-Welle-7 §4). **Ausgewertet und dokumentiert in
      [`../done/M3-results.md`](../done/M3-results.md) §4**
      (C3-Closure-Artefakt). Zusammenfassung:
      - **S-1** (Trigger-Triage Welle 0) erfuellt.
      - **S-2** (Sub-Slicing-Schwelle) erfuellt — nur Welle 4
        wurde geteilt (4a/4b).
      - **S-3** (Default-Gate ohne Override) erfuellt seit
        Welle-4b und mit Welle-6-C2 (`c61ab0d`) bestaetigt.
      - **S-4** (kein M3-spezifisches Image-Hardening-Trigger)
        — Welle-6-Erbschaft (Collector-Tag-Pin + Trivy-Audit)
        reicht, kein neuer Trigger.
      - **S-5** (ADR-Erweiterungs-Pattern ohne Supersedes)
        erfuellt — sechs M3-ADRs (0022..0027) plus ADR 0029
        sind alle Schaerfungen ohne Supersedes.
      - **S-6** (Lastenheft-Coverage-Sweep) erfuellt — ein
        neuer Trigger `030-rl-adapter.md` (`GG-FUTURE-001/002`);
        weitere Restposten (`GG-AGENT-007/008` Welle-4c+/M5,
        `GG-SAFE-001..006` M6, Snapshot-v2→v3-Migration M6)
        bleiben in `M3-results.md §5/§7` dokumentiert ohne
        eigenen Trigger.
- [x] **`make gates` A-1 gruen ohne Override** — Stand bleibt
      Welle-6-Ergebnis (`46dbd6e`); kein neuer Code in Welle 7,
      aber Re-Verifikation als Sanity-Check vor End-of-Wave-Move.
      **Erfuellt mit C6** (2026-05-25): `make fullbuild`-Aggregator
      umfasst `make ci` (mit `gates`-Sub-Aggregator) und liefert
      „mandatory A-1 gates green: lint, format-check, typecheck
      (mypy --strict, ADR 0005), arch-check (19 contracts),
      test-unit, coverage-gate (90% line / 85% branch),
      coverage-gate-critical (90% critical domain), dep-audit,
      noqa-gate (Slice 027 — no # noqa marker)".
- [x] **`make fullbuild` M3-Abschluss-Gate gruen ohne Override** —
      Stand bleibt Welle-6-Ergebnis (OTLP-Collector-Sibling +
      Compose-Smoke); Re-Verifikation vor End-of-Wave-Move.
      **Erfuellt mit C6** (2026-05-25): `make fullbuild` cache-
      frei gruen mit `[fullbuild] full closure: ci + runtime
      image + compose smoke green`. Compose-Smoke faehrt
      `deploy/compose.yml` mit `otel-collector`-Sibling hoch,
      pollt `/health` und Collector-`:13133` und faehrt sauber
      runter. Trivy-Image-Audit gruen fuer
      `grid-gym-runtime:latest` + `$(OTEL_COLLECTOR_IMAGE)`.
- [x] **`M3-faults-agents-observability.md` → `done/`** via
      Wave-Self-Close-Commit-Konvention; relative Link- und
      Bezug-Pfade-Pflege im Folge-Commit (ADR 0028). Closure-
      Notiz im Slice-Plan-Header + Wellen-Historie um Welle 6+7
      ergaenzt. **Erfuellt mit End-of-Wave-Move 2/2** (`79dcb42`
      reiner `git mv`) + Folge-Edit-Commit (dieser): sechs ADRs
      (0022..0027) ziehen ihren `M3-faults-agents-observability.
      md`-Bezug von `../planning/in-progress/` auf
      `../planning/done/` um; intern-relative
      `../in-progress/M3-faults-agents-observability.md`-Verweise
      in done/-Schwester-Dokumenten (welle-0..welle-4b,
      M3-welle-5/6/7, M3-results) auf den jetzt selben
      `done/`-Pfad korrigiert; Roadmap-Sibling-Link in
      `M3-faults-agents-observability.md` auf
      `../in-progress/roadmap.md` umgebogen.
- [x] **`M3-welle-7.md` → `done/`** via Wave-Self-Close-Commit-
      Konvention; End-of-Wave-Move-Folge analog Welle 6.
      **Erfuellt mit End-of-Wave-Move 1/2** (`d3daf71` reiner
      `git mv`) + Folge-Edit-Commit (dieser): relative
      Pfad-Verweise in `M3-welle-7.md` selbst sind durch die
      Sed-Korrekturen oben mit erfasst worden; DoD-Haken
      und in-progress/README.md + done/README.md gepflegt.

Kanonische Slice-Spezifikation:
[`M3-faults-agents-observability.md §3 Welle 7`](M3-faults-agents-observability.md)
— dieses Dokument ist lesefreundlicher Index + per-Welle-
Tracking, nicht als Ersatz.

**Commit-Sequenz (geplant):**

### C0 — `docs(plan)`: welle-7 Slice-Doc (dieses Dokument)

Eroeffnet Welle 7 mit Closure-Scope. Plus `in-progress/README.md`-
Sync (M3-welle-7.md-Eintrag im Bestand) und Slice-Plan-Status-
Text-Sync (Welle-6-Closure + Welle-7-Eroeffnung).

Per Wave-Self-Close-Commit-Konvention
([`planning/README.md`](../README.md)) **kein Pre-C0-Move** — der
M3-Slice-Plan bleibt bis zur Welle-7-End-of-Wave-Folge in
`in-progress/`.

### C1 — `docs(adr)`: ADR 0022..0027 → `Accepted` (6 Sub-Commits)

C1 promotet die sechs M3-ADRs in eigenen Commits, damit jeder
ADR-Stand individuell nachvollziehbar bleibt:

| Sub-Commit | ADR | Closure-Beleg |
| ---------- | --- | ------------- |
| **C1.1** | ADR 0022 (`Fault Injection Protocol`) | Welle-1/2-Lieferung; `BatteryFaultAdapter` + `GridFaultAdapter` produktiv (Welle 2 `91d44e2`) |
| **C1.2** | ADR 0023 (`AgentBus Protocol`) | Welle-3/4-Lieferung; `AgentMessageBus` + `RuleBasedAgent` + bidirektionaler Snapshot-Resume-Match produktiv (Welle 4b) |
| **C1.3** | ADR 0024 (`Observability Port Trio`) | Welle-5/6-Lieferung; Port-Trio + OTLP-Adapter-Trio + Compose-Smoke produktiv (Welle 6 `46dbd6e`) |
| **C1.4** | ADR 0025 (`Fault Recovery Pattern`) | Welle-2-Lieferung; Recovery-Engine + Fault-Demo/Property-Tests produktiv (Welle 2 `91d44e2`) |
| **C1.5** | ADR 0026 (`Agent Drain Registry Pattern`) | Welle-4a-Lieferung; Registry + Drain + Lifecycle + Snapshot-Plumbing produktiv (Welle 4a) |
| **C1.6** | ADR 0027 (`Rule-Based Agent Scenario Pattern`) | Welle-4b-Lieferung; `RuleBasedAgent` + Scenario-`agents`-Block + Demo produktiv (Welle 4b `ac7b47f`) |

Jeder Sub-Commit setzt:

- ADR-Header: `Status: Accepted` (von `Provisional`) + Datum
  2026-05-25 (oder neueres Closure-Datum).
- `Letzte inhaltliche Aenderung`-Pflichtfeld (ADR 0006 §4)
  aktualisiert.
- Falls eine Folge-Schaerfung noetig ist (z. B. weil Welle-6-
  Befunde noch nicht in der ADR stehen): per ADR-0011-Pattern
  ohne Supersede.

`make docs-check` muss nach jedem Sub-Commit exit 0 liefern.

### C2 — `docs(plan)`: Trigger 006 (`--strict-bytes`) Entscheidung

Triage am konkreten OTLP-Bytes-Vertrag aus Welle 6. C2 ist
**entscheidungspflichtig, aber aenderungsarm**: keine produktiven
Code-, Tooling- oder Gate-Konfigurationsaenderungen in Welle 7.

- **Option Aktivieren**: Trigger 006 wandert nach `next/` mit
  konkretem Folge-Slice fuer ADR 0005 `--strict-bytes`, dep-audit +
  typecheck-Stage-Anpassung und Verifikation der relevanten
  Bytes-Pfade. Die Aktivierung selbst erfolgt nicht in Welle 7.
- **Option Verschieben**: Trigger 006 bleibt `open/` mit neuem
  Aktivierungs-Kriterium (z. B. „M4-Protokolladapter bringt
  konkrete `bytes`-Pfade"). Begruendung dokumentiert.

Decision-Commit aktualisiert
[`docs/plan/planning/open/006-mypy-strict-bytes.md`](../open/006-mypy-strict-bytes.md)
und dieses Dokument (DoD-Haken).

### C3 — `docs(plan)`: M3-results.md + roadmap.md + Open-Trigger

Dreifach-Closure-Commit (oder zwei Sub-Commits, falls
Granularitaet sinnvoll):

- **`done/M3-results.md`** (neu) — Welle-Tabelle (Welle 0..7
  mit Status/Datum/Commit-Range), Test-Bilanz pro Welle
  (Unit + Integration), Coverage-Endstand, Closure-Verweis
  auf alle sechs M3-ADRs. Pattern analog
  [`done/M2-devices-results.md`](../done/M2-devices-results.md).
- **`roadmap.md` §3 M3** auf `Done`: DoD-Checkboxen
  aktivieren, Status setzen, „Naechster aktiver Slice: M4"
  ergaenzen.
- **Open-Trigger fuer bekannte M3-Restposten**: pro RL-Adapter
  (`GG-FUTURE-001/002`) ein neuer `open/`-Eintrag. Weitere
  S-6-Sweep-Befunde werden in C4 dokumentiert und dort als
  `open/`-Trigger angelegt oder explizit als nicht triggerwuerdig
  begruendet.

### C4 — `docs(plan)`: End-to-End-Sweep S-1..S-6

S-1..S-6-Sweep-Ergebnisse als eigener Commit dokumentiert. Pro
Sweep-Item ein DoD-Haken in diesem Dokument; Befunde, die Folge-
Trigger ausloesen, werden in C4 selbst oder in einem unmittelbaren
Folge-Commit als `open/`-Trigger angelegt.

Wenn S-1..S-6 keine neuen Befunde liefern (Optimal-Fall), kann
C4 mit C3 zusammen committed werden.

### C5 — `docs(plan)`: Slice-Plan-Sync vor End-of-Wave

- `M3-faults-agents-observability.md`: Wellen-Historie um Welle 6
  und Welle 7 ergaenzen; Closure-Notiz vorbereiten, aber
  Status-Header bleibt bis nach C6 `In Progress`.
- Bis dahin erfuellte DoD-Haken in diesem Dokument setzen; Gate-
  und Move-Haken bleiben bis C6 bzw. End-of-Wave-Folge offen.
- README-Bestandspflege passiert erst nach den reinen `git mv`-
  Commits im End-of-Wave-Folge-Edit, damit die
  Wave-Self-Close-Commit-Konvention eingehalten bleibt.

### C6 — Welle-7-Verifikation

- `make gates` cache-frei gruen (Sanity-Check; kein neuer Code,
  aber alle Doku-Aenderungen sollen `make docs-check` mitziehen).
- `make fullbuild` cache-frei gruen (M3-Abschluss-Gate aus dem
  kanonischen Slice-Plan).
- `make test-integration` cache-frei gruen.
- `make docs-check` cache-frei gruen mit dem Vor-Move-Pfadstand.

Wenn alles gruen: `M3-faults-agents-observability.md` und dieses
Dokument auf `Done` synchronisieren und weiter mit End-of-Wave.

### End-of-Wave — reine Moves nach `done/`

Per Wave-Self-Close-Commit-Konvention zwei reine
`git mv`-Operationen (in zwei Commits, damit die Rename-Historie
sauber als `R`-Rename erkannt wird):

1. `git mv M3-welle-7.md ../done/M3-welle-7.md`
2. `git mv M3-faults-agents-observability.md ../done/M3-faults-agents-observability.md`

Inhalts-Folge-Edits (relative Link-Anpassung in beiden
Dokumenten, Pfad-Pflege per
[`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md))
in einem unmittelbar nachfolgenden Commit. Dieser Folge-Edit enthaelt
auch:

- `in-progress/README.md`: `M3-faults-agents-observability.md`-
  Eintrag entfernen; `M3-welle-7.md`-Eintrag entfernen.
- `done/README.md`: neue Eintraege fuer
  `M3-faults-agents-observability.md`, `M3-welle-7.md`,
  `M3-results.md`.
- `make docs-check` exit 0 nach den finalen relativen Link-
  Anpassungen.

---

## 1. Context

M3 hat drei parallele Sub-Bereiche (Faults, Multi-Agent,
Observability) ueber sieben Lieferwellen (Welle 0..6) plus
Closure-Welle 7 geliefert. Die
Sub-Bereiche haben drei Basis-ADRs (0022/0023/0024) und drei
konkretisierende Folge-ADRs (0025/0026/0027); alle sechs stehen
bis zur Welle-7-Closure auf `Provisional`. Welle 7 ist die einzige
Welle ohne neuen Code — sie sammelt die formalen Closure-Schritte
ein.

**Welle-6-Closure-Stand (Basis fuer Welle 7):**

- C0..C3 + Code-Review-Folge produktiv (`47a46b0..46dbd6e`,
  inkl. C2 `c61ab0d`, C3 `47a46b0`, Closure-Docs `11eb670`,
  End-of-Wave-Move `245add8`, Pfad-Folge `ac70eda`, Trigger-
  029-Schaerfung `24dfb2e`, Trigger-029-Move `1f8f69a`,
  Trigger-029-Closure `7fbafbb`, Code-Review-Folge `46dbd6e`).
- Trigger 029 als Fehlbefund geschlossen
  ([`../done/029-otlp-span-grpc-export-edge-case.md`](../done/029-otlp-span-grpc-export-edge-case.md)).
- Integration-Smoke gruen mit vollem Tripel Span+Metric+Log
  (`tests/integration/test_otlp_compose_smoke.py`).
- Runbook `docs/user/observability.md` aktiv mit
  Format-Drift-Hinweisen + Internal-Counter-Diagnose.

**Was Welle 7 nicht ist:**

- Kein produktiver Code-Slice. Kein neuer Adapter, kein neues
  Modul, keine Schema-Aenderung.
- Kein Trigger fuer SOLLTE-Geraete/-Netz/-Battery (`GG-DEV-015..`,
  `GG-GRID-005..`, `GG-BESS-006..`) — die bleiben in `open/`,
  M3-Welle-7 konsumiert sie nicht.
- Kein RL-Adapter (`GG-FUTURE-001/002`) — bleibt eigener Slice
  nach M3-Closure.

## 2. Scope

**In Scope:**

- ADR-Promotionen (0022..0027) auf `Accepted` mit
  Closure-Belegen.
- Trigger 006 Decision (Aktivieren vs. Verschieben).
- `done/M3-results.md` als Wellen-Tabelle + Test-/Coverage-
  Endstand-Snapshot.
- `roadmap.md` §3 M3 auf `Done`.
- Open-Trigger fuer M3-Restposten (mindestens RL-Adapter,
  weitere aus S-6-Sweep).
- End-to-End-Sweep S-1..S-6.
- End-of-Wave-Move M3-welle-7.md + M3-faults-agents-
  observability.md → `done/`.

**Out-of-Scope (eigene Slices oder andere Meilensteine):**

- Produktiver Code in `src/`, `tools/`, `tests/`, `deploy/`,
  `Makefile`, `pyproject.toml`. Wenn ein Closure-Befund
  Code-Aenderung erfordert (z. B. Trigger-006-Aktivierung), wird
  das in einem eigenen Slice nach Welle 7 erledigt.
- M4-Protokolladapter (MQTT/Modbus/OPC-UA/DNP3/IEC) — eigener
  Slice-Plan, nach M3-Closure.
- SOLLTE-Geraete/-Netz/-Battery — Trigger 016..024, eigene
  Slices.
- UI / Demo-Seite (`GG-UI-001..009`) — M5.
- Performance-Benchmarks (`GG-RT-004/005`) — M6.

## 3. Architektur-Entscheidungen

Welle 7 hat keine neuen Architektur-Entscheidungen — sie
**konsumiert** die in Welle 1..6 getroffenen Entscheidungen.

**Konsumierte ADRs auf `Accepted`-Promotion-Pfad:**

- ADR 0022 — `Fault Injection Protocol` (Welle 1/2).
- ADR 0023 — `AgentBus Protocol` (Welle 3/4).
- ADR 0024 — `Observability Port Trio` (Welle 5/6).
- ADR 0025 — `Fault Recovery Pattern` (Welle 2).
- ADR 0026 — `Agent Drain Registry Pattern` (Welle 4a).
- ADR 0027 — `Rule-Based Agent Scenario Pattern` (Welle 4b).

**Konsumierte Hygiene-/Prozess-ADRs (bereits `Accepted` und
unangetastet):**

- ADR 0029 — `AC-NO-COVERAGE-PRAGMA Contract` (Welle 5b/Slice 027,
  `Accepted`).

**Mögliche Welle-7-Folge-Entscheidung (Trigger 006):**

- Aktivierung von `--strict-bytes` (ADR 0005) waere eine
  produktive Code-Aenderung — geht nicht in Welle 7, sondern
  in einen Folge-Slice. Wenn aktiviert, Trigger 006 wandert in
  `next/` mit konkretem Slice-Plan; wenn verschoben, bleibt in
  `open/` mit neuem Aktivierungs-Kriterium.

## 4. Liefer-Reihenfolge

C0 → C1 → C2 → C3 → C4 → C5 → C6 → End-of-Wave (zwei Moves +
Folge-Edits). Reihenfolge ist nicht streng linear, aber zwingend
fuer C5 (Sync gegen C1/C2/C3/C4-Stand) und End-of-Wave (nach
C6-Verifikation).

C2 und C3 sind unabhaengig — koennen in beliebiger Reihenfolge.
C1 (sechs Sub-Commits) ist parallelisierbar zu C2/C3, weil ADR-
Files isoliert sind.

C4 kann mit C3 zusammen, wenn S-1..S-6 keine neuen Befunde
liefert.

## 5. Critical Files

**Geaendert (Welle 7):**

- `docs/plan/adr/0022-fault-injection-protocol.md` (Status +
  Letzte inhaltliche Aenderung).
- `docs/plan/adr/0023-agent-bus-protocol.md` (dito).
- `docs/plan/adr/0024-observability-port-trio.md` (dito).
- `docs/plan/adr/0025-fault-recovery-pattern.md` (dito).
- `docs/plan/adr/0026-agent-drain-registry-pattern.md` (dito).
- `docs/plan/adr/0027-rule-based-agent-scenario-pattern.md` (dito).
- `docs/plan/planning/in-progress/roadmap.md` (M3 auf `Done`,
  DoD-Checkboxen aktivieren).
- `docs/plan/planning/in-progress/M3-faults-agents-observability.md`
  (Status-Header + Wellen-Historie um Welle 6+7; wandert dann
  selbst nach `done/`).
- `docs/plan/planning/in-progress/M3-welle-7.md` (dieses
  Dokument; DoD-Haken; wandert selbst nach `done/`).
- `docs/plan/planning/open/006-mypy-strict-bytes.md` (Decision-
  Dokumentation).
- `docs/plan/planning/done/README.md` (neue Eintraege fuer
  M3-results, M3-faults-agents-observability, M3-welle-7).
- `docs/plan/planning/in-progress/README.md` (M3-Eintraege
  entfernen).

**Neu (Welle 7):**

- `docs/plan/planning/done/M3-results.md` (Welle-Tabelle +
  Test-/Coverage-Endstand + Closure-Verweise).
- Ggf. `docs/plan/planning/open/030-*.md` ... fuer
  S-6-Sweep-Befunde + RL-Adapter (Anzahl haengt vom Sweep ab).

**Nicht geaendert (Welle 7):**

- Alles unter `src/`, `tools/`, `tests/`, `deploy/`, `Makefile`,
  `pyproject.toml`. Welle 7 ist reine Doku-Welle.

## 6. Verifikationspfad

C6 verifiziert:

- `make gates` cache-frei gruen.
- `make fullbuild` cache-frei gruen.
- `make test-integration` cache-frei gruen.
- `make docs-check` cache-frei gruen mit dem Vor-Move-Pfadstand.

Vor jedem Sub-Commit (insbesondere C1.1..C1.6 und C2/C3):

- `make docs-check` exit 0 als minimaler Sanity-Check.

Nach dem End-of-Wave-Move:

- `make docs-check` exit 0 — relative Pfade in
  `M3-faults-agents-observability.md` und `M3-welle-7.md`
  zeigen jetzt auf `../in-progress/`, `../open/`, `../../adr/`
  statt der lokalen `done/`-Sibling-Pfade. Pflicht-Folge-Edit
  analog `ac70eda` aus Welle 6.

## 7. Risiken

- **ADR-Promotionen blockieren auf einer offenen Decision**:
  ADR 0022..0027 koennten beim `Accepted`-Schritt feststellen,
  dass eine Folge-Schaerfung noetig ist (z. B. weil ein
  Welle-6-Befund noch nicht in ADR 0024 steht). *Fallback*:
  Schaerfung-ohne-Supersede per ADR-0011-Pattern in C1; der
  betroffene Sub-Commit traegt die Schaerfung mit, bevor er
  auf `Accepted` setzt.
- **Trigger 006 ist nicht entscheidbar ohne weiteren Input**:
  `--strict-bytes` betrifft den konkreten OTLP-Bytes-Vertrag,
  der erst mit M4-Protokolladaptern an mehreren Stellen sichtbar
  wird. *Fallback*: Verschiebung in `open/` mit Aktivierungs-
  Kriterium „M4-Welle XY bringt konkrete `bytes`-Pfade" ist die
  legitime Entscheidung. C2 muss nicht zwingend „Aktivieren"
  produzieren.
- **S-6-Sweep findet mehr Restposten als erwartet**: das
  Lastenheft hat viele `GG-*`-IDs; ein gruendlicher Sweep
  koennte 10+ Folge-Trigger ausloesen. *Fallback*: Sweep als
  „Best Effort" definieren — relevante Trigger fuer M4 jetzt,
  alles andere wandert in einen separaten Open-Trigger
  „`M3-Welle-7-S-6-Sweep-Backlog`" mit Liste.
- **End-of-Wave-Move bricht relative Links**: zwei Doku-Files
  wandern gleichzeitig, Cross-Referenzen zwischen ihnen muessen
  korrekt aufloesen. *Fallback*: `make docs-check` nach jedem
  Move-Folge-Commit; ADR 0028 ist der verbindliche Link-
  Maintenance-Vertrag.
- **`make gates` haengt an einem Welle-6-Restposten**: wenn die
  Welle-6-Code-Review-Folge (`46dbd6e`) ein Gate brechen sollte
  (z. B. weil ein Lint-Fix nicht stabil ist), muss das in einem
  eigenen Fix-Commit ausserhalb Welle 7 behoben werden. *Fallback*:
  Welle 7 wartet, bis `make gates` gruen ist; Welle-6-Fix wird
  vor C6 nachgezogen.

## 8. Wandert nach

- ✓ `in-progress/M3-welle-7.md` (dieses Dokument, eroeffnet
  2026-05-25 mit C0).
- `done/M3-welle-7.md` nach End-of-Wave-Move (rename-only,
  Wave-Self-Close-Konvention).
- `done/M3-faults-agents-observability.md` — der M3-Slice-Plan
  selbst wandert mit Welle-7-End-of-Wave nach `done/`.
- `done/M3-results.md` (neu in Welle 7, lebt direkt in `done/`).
