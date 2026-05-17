# ADR 0012 — API + Simulation als zwei Prozesse

**Status:** Accepted — kein Validierungs-Spike erforderlich.
Welle 6c (`deploy/compose.yml`, Commit `f7b699d`) hat den
Pattern bereits implementiert; diese ADR codifiziert die
de-facto-Entscheidung nachtraeglich. Direkter
`Proposed → Accepted`-Sprung per `ADR 0006 §2`-Klausel
(„ADR ohne Validierungsbedarf").
**Datum:** 2026-05-17
**Status geaendert am:** 2026-05-17 — `Proposed → Accepted`.
**Bezug:**
[Architektur](../../../spec/architecture.md) §19 (`GG-AR-OPEN-002`,
bei Acceptance dieser ADR von `Offen` auf `Geschlossen` zu setzen),
[Architektur](../../../spec/architecture.md) §16 (API/Simulation/UI
mit getrennten Healthchecks),
[`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
§2 (direktes Acceptance ohne Spike),
[`docs/plan/planning/done/M1-tick-loop-spine.md`](../planning/done/M1-tick-loop-spine.md)
§3 Welle 6c (operative Lieferung),
[`deploy/compose.yml`](../../../deploy/compose.yml)
(Production-Stack-Definition).

---

## 1. Kontext

`spec/architecture.md` §19 fuehrt `GG-AR-OPEN-002` als offene
architektonische Frage: API-Service und Simulationsdienst als
ein Prozess oder zwei. `roadmap.md` §4 Vorbedingungen listet
denselben Punkt als „offen, eigene Folge-ADR".

In M1 Welle 6c ist die Topologie de-facto fixiert worden:
`deploy/compose.yml` definiert `api` (FastAPI/uvicorn auf
`:8080`) und `simulation` (heute `sleep infinity`-Stub, M2+
TickLoop-Runner) als zwei separate Services. Beide teilen sich
den `postgres`-Service als gemeinsame Persistenzschicht.

Diese ADR formalisiert den Pattern, damit `GG-AR-OPEN-002`
geschlossen ist und M2-Geraetemodelle auf einer fixierten
Topologie aufsetzen koennen.

---

## 2. Entscheidung

**API-Service und Simulationsdienst laufen als zwei separate
Prozesse**, kommunizieren ueber Postgres als gemeinsame
Persistenzschicht und ueber HTTP fuer steuernde Aufrufe.

Konkret:

- **`api`-Service** (`adapters/driving/http_api`): FastAPI/uvicorn,
  HTTP-Port `:8080`, depends-on `postgres: service_healthy`.
  Stateless gegenueber dem Sim-State — schreibt nur `runs`-
  Metadaten und liest Telemetrie aus Postgres.
- **`simulation`-Service** (in M2+ `adapters/driving/sim_runner`
  oder ein TickLoop-Runner-Modul): laufender Prozess, der den
  `TickLoop` zyklisch fuettert. Welle-6c-Stand: `sleep infinity`-
  Stub. M2-Geraete bringen den produktiven Runner.
- **Kommunikationspfad** zwischen beiden Services:
  - Persistenz-Bus: Postgres-`runs`-Tabelle (heute), Postgres-
    Telemetry-Tabelle (M2 mit Geraeten), spaeter ggf.
    Message-Queue (M3 Multi-Agent).
  - Direkte HTTP-Aufrufe gibt es **nicht** — API steuert
    Simulation nur indirekt ueber `runs`-Status-Updates oder
    Konfigurations-Tabellen.
- **Healthchecks**: jeder Service liefert seinen eigenen
  Healthcheck (`/health` fuer api per Dockerfile-HEALTHCHECK;
  `simulation` mit eigenem Heartbeat-Mechanismus, der M2-Geraete-
  Slice bringt).

---

## 3. Begruendung

- **Failure-Isolation:** ein abgestuerzter TickLoop-Prozess
  bringt nicht den API-Service down — `/health` antwortet
  weiter, Operations-Teams sehen den Defect-Boundary klar.
- **Skalierungs-Asymmetrie:** API-Requests sind kurzlebig (ms-
  Range), Tick-Loops laufen typischerweise minuten- bis
  stunden-lang. In einem Single-Process-Setup wuerde uvicorn-
  Async-Loop und TickLoop um den GIL konkurrieren; Two-Process
  erlaubt OS-Scheduling-Trennung.
- **Persistenz-Bus statt Direkt-IPC:** Postgres ist ohnehin
  Pflicht-Komponente (`GG-PERSIST-001..009`); ein zweiter IPC-
  Layer (gRPC, Pipe, Socket) waere unnoetige Kopplung. Auch
  schreibt der Pattern den natuerlichen Replay-Vertrag fest:
  Telemetrie wird einmal geschrieben, von API + UI gelesen.
- **`spec/architecture.md` §16 verlangt getrennte
  Healthchecks** — das ist auf zwei Prozesse leichter
  abbildbar als auf einen einzelnen mit zwei Endpoints.
- **Welle 6c hat de-facto schon entschieden:** das ADR
  formalisiert die Realitaet, nicht eine zukuenftige Aenderung.

Alternative Optionen wurden gegen diese Entscheidung
abgewogen:

- **Ein-Prozess-Setup mit FastAPI-`BackgroundTasks`**:
  funktioniert fuer M1-Stub-Loops, kollidiert aber mit Multi-
  Agent (M3) und Performance-Schranken (M6, `GG-RT-005`
  10.000 Punkte/s). Verworfen.
- **API + Simulation + UI als drei Prozesse:** ueberzogen fuer
  M1/M2. UI bleibt M5-Scope; bis dahin reicht api + sim. Eine
  Folge-ADR kann UI-Trennung mit M5 nachschieben.

---

## 4. Reichweite

- `deploy/compose.yml` bleibt strukturell unveraendert; M2
  ersetzt nur den `simulation`-Stub-Container-Command durch den
  produktiven TickLoop-Runner.
- `spec/architecture.md` §19 muss `GG-AR-OPEN-002` von `Offen`
  auf „Geschlossen durch ADR 0012" umstellen — das ist eine
  zulaessige Aenderung am normativen Dokument
  (`ADR 0006 §5` operative Artefakte; `spec/architecture.md`
  ist normativ, aber `GG-AR-OPEN-*`-Eintraege duerfen bei
  Acceptance einer Folge-ADR geschlossen werden).
- `roadmap.md §4` Vorbedingungen: `GG-AR-OPEN-002`-Checkbox
  abgehakt mit Verweis auf diese ADR.
- M3 Multi-Agent kann eine Message-Queue als zusaetzlichen
  IPC-Pfad zwischen api und sim einfuehren — diese ADR
  schliesst das nicht aus, regelt aber Postgres als
  Default-Persistenz-Bus.

---

## 5. Operative Artefakte

- `deploy/compose.yml` (Welle 6c): api + simulation + postgres
  als drei Services. M2 ersetzt den `simulation`-Command.
- `Dockerfile` `runtime`-Stage: gemeinsames Image fuer beide
  Services; Trennung erfolgt nur ueber `command` + `entrypoint`
  im Compose.
- `spec/architecture.md` §19 `GG-AR-OPEN-002`: Status auf
  `Geschlossen` mit ADR-0012-Verweis.

---

## 6. Konsequenzen

- **Positiv:** `GG-AR-OPEN-002` geschlossen — M2 hat keine
  Topologie-Drift mehr als Risiko.
- **Positiv:** Failure-/Skalierungs-Isolation strukturell
  belegt.
- **Positiv:** Welle-6c-Compose-File bleibt unveraendert; ADR
  ist rein retrospektive Doku der bereits gebauten Realitaet.
- **Neutral:** ein gemeinsames Container-Image fuer beide
  Services bedeutet, dass alle Runtime-Deps (FastAPI + uvicorn
  + psycopg + alembic + zukuenftige TickLoop-Runner-Pakete) in
  einem Image landen. Bei wachsendem Footprint kann eine
  Folge-ADR `M6`-Scope das Image splitten.
- **Negativ:** Postgres als Persistenz-Bus zwischen beiden
  Services bedeutet, dass jede Tick-Telemetry-Persistierung in
  M2 eine DB-Round-Trip kostet. Performance-Schranken aus
  `GG-RT-005` koennen das verschaerfen — M6-Slice prueft, ob
  ein Batch-Insert / Streaming-Pfad noetig ist.

---

## 7. Nicht Gegenstand dieser ADR

- UI-Trennung als dritter Prozess — eigene Folge-ADR mit M5.
- Message-Queue zwischen api und sim — eigene Folge-ADR mit
  M3 (Multi-Agent-Bus).
- Image-Split (zwei separate Container-Images fuer api und
  sim) — eigene Folge-ADR mit M6 (Security/CI-Haertung).
- Skalierungs-Strategie (Anzahl `api`/`simulation`-Replicas) —
  ist Deployment-Konfig, keine Architektur-Entscheidung.
