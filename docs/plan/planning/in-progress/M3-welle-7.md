# Welle 7 — M3-Closure

**Status:** In Progress — eroeffnet 2026-05-25 mit C0 (dieses
Dokument). Welle 0/1/2/3/4a/4b/5/6 sind abgeschlossen; die drei
M3-Sub-Bereiche (Faults `Done` 2026-05-20, Multi-Agent `Done`
2026-05-22, Observability **Foundation `Done` 2026-05-23,
OTLP-Adapter `Done` 2026-05-25**) sind alle inhaltlich fertig.
Welle 7 ist die formale Closure-Welle: drei ADRs auf `Accepted`
promoten, einen verbliebenen Trigger entscheiden, M3-Ergebnisse
in einer Welle-Tabelle bündeln und den M3-Slice-Plan selbst
nach `done/` moven.

**DoD-Checkliste (Welle-7-Abnahme):**

Konvention analog Roadmap §3 M3 — `[ ]` offen, `[x]` erfuellt,
`[~]` partiell. Status beim C0-Stand `In Progress`: alle Items
offen; Haken wandern mit C1/C2/C3-Beleg.

- [ ] **ADR 0022 (`Fault Injection Protocol`) → `Accepted`** —
      Closure-Beleg ist Welle-1/2-Lieferung (Faults-Subsystem
      abgeschlossen 2026-05-20). `Letzte inhaltliche Aenderung`-
      Pflichtfeld (ADR 0006 §4) gesetzt.
- [ ] **ADR 0023 (`AgentBus Protocol`) → `Accepted`** —
      Closure-Beleg ist Welle-3/4-Lieferung (Multi-Agent-Subsystem
      abgeschlossen 2026-05-22). `Letzte inhaltliche Aenderung`-
      Pflichtfeld (ADR 0006 §4) gesetzt.
- [ ] **ADR 0024 (`Observability Port Trio`) → `Accepted`** —
      Closure-Beleg ist Welle-5/6-Lieferung (OTLP-Adapter +
      Compose-Smoke abgeschlossen 2026-05-25). `Letzte inhaltliche
      Aenderung`-Pflichtfeld (ADR 0006 §4) gesetzt. Explizit als
      M3-Welle-7-Material in `done/M3-welle-6.md` DoD vermerkt.
- [ ] **Trigger 006 (`--strict-bytes`) Entscheidung** —
      `aktivieren` oder konkrete Begruendung fuer Verschiebung in
      M4/M6-Re-Triage. Bezug: ADR 0005 `--strict-bytes`-Option +
      OTLP-Bytes-Vertrag aus Welle 6. Decision dokumentiert; bei
      Verschiebung wandert Trigger 006 in `open/` mit neuem
      Aktivierungs-Kriterium.
- [ ] **`done/M3-results.md`** angelegt, Pattern analog
      [`done/M2-devices-results.md`](../done/M2-devices-results.md):
      Welle-Tabelle (Welle 0..7 mit Status/Datum/Commit-Range),
      Test-Bilanz pro Welle (Unit + Integration), Coverage-
      Endstand, Closure-Verweis auf alle drei ADRs.
- [ ] **`roadmap.md` §3 M3 auf `Done`** — DoD-Checkboxen
      aktivieren (10.000-Punkte-Benchmark bleibt M6, andere
      M3-spezifische Items haken), Status auf `Done`, „Naechster
      aktiver Slice: M4 (Protokolladapter)" gesetzt.
- [ ] **Open-Trigger fuer M3-Restposten** angelegt, soweit nicht
      schon existent. Bekannte Kandidaten:
      - **RL-Adapter** (`GG-FUTURE-001/002`) — eigener Slice nach
        M3-Closure. Multi-Agent-Bus aus Welle 3/4 ist RL-faehig,
        aber der RL-Trainings-Loop bleibt extern.
      - Weitere Restposten werden im S-6-Sweep identifiziert.
- [ ] **End-to-End-Sweep S-1..S-6** (Pflicht-Punkt aus
      `M3-faults-agents-observability.md §3 Welle 7`, Pattern
      analog M2-Welle-7 §4):
      - **S-1 — M3-spezifisches Vorabraeumungs-Item**
        (Trigger-Triage in Welle 0) nachverifizieren: hat
        Welle 0 alle relevanten Open-Trigger entweder
        konsumiert oder explizit als out-of-scope markiert?
      - **S-2 — Sub-Slicing-Schwelle** (§3 Praeambel): keine
        Welle hat die Sub-Slicing-Schwelle ueberschritten;
        Welle 4 wurde planmaessig in 4a/4b geteilt. Verifikation
        per Wellen-Tabelle in `done/M3-results.md`.
      - **S-3 — Default-Gate ohne Override**: `make fullbuild`
        cache-frei gruen ohne `CRITICAL_COV_TARGETS`-Override
        (war Welle-6-DoD; mit Welle-6-Closure verifiziert).
      - **S-4 — kein M3-spezifisches Image-Hardening-Trigger**
        (Image-Pin-Trigger aus `M2-Notes` ist optional; M3
        hat keinen neuen Hardening-Bedarf eingebracht). Wenn
        die Welle-6-Erbschaft (`OTEL_COLLECTOR_IMAGE` Pin,
        `tools/diagnose_otlp_span_export.py`) hier ausreicht,
        kein neuer Trigger.
      - **S-5 — ADR-Erweiterungs-Pattern fortgefuehrt**: drei
        neue ADRs (0022/0023/0024) plus eine Folge-ADR (0029
        `AC-NO-COVERAGE-PRAGMA`) ohne Supersedes; ADR-0011-
        Pattern (Schaerfung-ohne-Ablöesung) konsistent angewandt.
        Verifikation: keine Supersedes-Eintraege in den vier
        ADRs.
      - **S-6 — Lastenheft-Coverage-Sweep**: pruefen, welche
        M3-relevanten `GG-*`-IDs durch die Welle 1-6 erfuellt
        sind und welche fuer M4 (Protokolladapter) oder
        spaeter offen bleiben. Neue `open/`-Trigger fuer M4-
        Vorlauf-Items, falls relevant.
- [ ] **`make gates` A-1 gruen ohne Override** — Stand bleibt
      Welle-6-Ergebnis (`46dbd6e`); kein neuer Code in Welle 7,
      aber Re-Verifikation als Sanity-Check vor End-of-Wave-Move.
- [ ] **`M3-faults-agents-observability.md` → `done/`** via
      Wave-Self-Close-Commit-Konvention; relative Link- und
      Bezug-Pfade-Pflege im Folge-Commit (ADR 0028). Closure-
      Notiz im Slice-Plan-Header + Wellen-Historie um Welle 6+7
      ergaenzt.
- [ ] **`M3-welle-7.md` → `done/`** via Wave-Self-Close-Commit-
      Konvention; End-of-Wave-Move-Folge analog Welle 6.

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

### C1 — `docs(adr)`: ADR 0022/0023/0024 → `Accepted` (3 Sub-Commits)

C1 promotet die drei M3-Sub-Bereichs-ADRs in eigenen Commits, damit
jeder ADR-Stand individuell nachvollziehbar bleibt:

| Sub-Commit | ADR | Closure-Beleg |
| ---------- | --- | ------------- |
| **C1.1** | ADR 0022 (`Fault Injection Protocol`) | Welle-1/2-Lieferung; `BatteryFaultAdapter` + `GridFaultAdapter` produktiv (Welle 2 `91d44e2`) |
| **C1.2** | ADR 0023 (`AgentBus Protocol`) | Welle-3/4-Lieferung; `AgentMessageBus` + `RuleBasedAgent` + bidirektionaler Snapshot-Resume-Match produktiv (Welle 4b) |
| **C1.3** | ADR 0024 (`Observability Port Trio`) | Welle-5/6-Lieferung; Port-Trio + OTLP-Adapter-Trio + Compose-Smoke produktiv (Welle 6 `46dbd6e`) |

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

Triage am konkreten OTLP-Bytes-Vertrag aus Welle 6:

- **Option Aktivieren**: ADR 0005 `--strict-bytes` scharf
  schalten, dep-audit + typecheck-Stage entsprechend anpassen,
  Welle-6-Code (`_factory.py`, `_config.py`) verifizieren.
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
  auf alle drei ADRs. Pattern analog
  [`done/M2-devices-results.md`](../done/M2-devices-results.md).
- **`roadmap.md` §3 M3** auf `Done`: DoD-Checkboxen
  aktivieren, Status setzen, „Naechster aktiver Slice: M4"
  ergaenzen.
- **Open-Trigger fuer M3-Restposten**: pro RL-Adapter
  (`GG-FUTURE-001/002`) ein neuer `open/`-Eintrag, plus alle
  S-6-Sweep-Befunde.

### C4 — `docs(plan)`: End-to-End-Sweep S-1..S-6

S-1..S-6-Sweep-Ergebnisse als eigener Commit dokumentiert. Pro
Sweep-Item ein DoD-Haken in diesem Dokument; Befunde, die Folge-
Trigger ausloesen, werden in C3 (Open-Trigger-Block) konsumiert
— C4 ist dann reiner Verifikations-Beleg.

Wenn S-1..S-6 keine neuen Befunde liefern (Optimal-Fall), kann
C4 mit C3 zusammen committed werden.

### C5 — `docs(plan)`: in-progress/README.md + Slice-Plan-Sync

- `in-progress/README.md`: `M3-faults-agents-observability.md`-
  Eintrag entfernen (wandert nach `done/`); `M3-welle-7.md`-
  Eintrag entfernen (wandert nach `done/`); M3-Slice-Plan-
  Status auf `Done` syncen.
- `done/README.md`: neuer Eintrag fuer
  `M3-faults-agents-observability.md`, `M3-welle-7.md`,
  `M3-results.md`.
- `M3-faults-agents-observability.md`: Status-Header auf `Done`,
  Wellen-Historie um Welle 6 und Welle 7 ergaenzen.
- DoD-Haken in diesem Dokument auf `[x]`.

### C6 — Welle-7-Verifikation

- `make gates` cache-frei gruen (Sanity-Check; kein neuer Code,
  aber alle Doku-Aenderungen sollen `make docs-check` mitziehen).
- `make test-integration` cache-frei gruen.
- `make docs-check` cache-frei gruen.

Wenn alles gruen: weiter mit End-of-Wave.

### End-of-Wave — `chore`: git mv M3-welle-7.md + M3-faults-agents-observability.md → done/ (rename-only)

Per Wave-Self-Close-Commit-Konvention zwei reine
`git mv`-Operationen (in zwei Commits, damit die Rename-Historie
sauber als `R`-Rename erkannt wird):

1. `git mv M3-welle-7.md ../done/M3-welle-7.md`
2. `git mv M3-faults-agents-observability.md ../done/M3-faults-agents-observability.md`

Inhalts-Folge-Edits (relative Link-Anpassung in beiden
Dokumenten, Pfad-Pflege per
[`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md))
in einem unmittelbar nachfolgenden Commit.

---

## 1. Context

M3 hat drei parallele Sub-Bereiche (Faults, Multi-Agent,
Observability) ueber acht Wellen geliefert (Welle 0..6). Jeder
Sub-Bereich hat seine eigene ADR (0022/0023/0024); jede ADR ist
im `Provisional`-Zustand stehen geblieben, bis die zugehoerigen
Wellen abgeschlossen sind. Welle 7 ist die einzige Welle ohne
neuen Code — sie sammelt die formalen Closure-Schritte ein.

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

- ADR-Promotionen (0022, 0023, 0024) auf `Accepted` mit
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

**Konsumierte Folge-ADRs (bereits `Accepted` und unangetastet):**

- ADR 0025 — `Fault Recovery Pattern` (Welle 2, `Accepted`).
- ADR 0026 — `Agent Drain Registry Pattern` (Welle 4a, `Accepted`).
- ADR 0027 — `Rule-Based Agent Scenario Pattern` (Welle 4b,
  `Accepted`).
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
C1 (drei Sub-Commits) ist parallelisierbar zu C2/C3, weil ADR-
Files isoliert sind.

C4 kann mit C3 zusammen, wenn S-1..S-6 keine neuen Befunde
liefert.

## 5. Critical Files

**Geaendert (Welle 7):**

- `docs/plan/adr/0022-fault-injection-protocol.md` (Status +
  Letzte inhaltliche Aenderung).
- `docs/plan/adr/0023-agent-bus-protocol.md` (dito).
- `docs/plan/adr/0024-observability-port-trio.md` (dito).
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
- `make test-integration` cache-frei gruen.
- `make docs-check` cache-frei gruen — alle relative Link-
  Anpassungen aus dem End-of-Wave-Move aufgeloest.

Vor jedem Sub-Commit (insbesondere C1.1/C1.2/C1.3 und C2/C3):

- `make docs-check` exit 0 als minimaler Sanity-Check.

Nach dem End-of-Wave-Move:

- `make docs-check` exit 0 — relative Pfade in
  `M3-faults-agents-observability.md` und `M3-welle-7.md`
  zeigen jetzt auf `../in-progress/`, `../open/`, `../adr/`
  statt der lokalen `done/`-Sibling-Pfade. Pflicht-Folge-Edit
  analog `ac70eda` aus Welle 6.

## 7. Risiken

- **ADR-Promotionen blockieren auf einer offenen Decision**:
  ADR 0022/0023/0024 koennten beim `Accepted`-Schritt feststellen,
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
