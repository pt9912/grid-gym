# Rueckverfolgbarkeit (V-Modell) — grid-gym

> Ausgelagert aus `spec/lastenheft.md` §27 (Slice 063), damit der Vertrag
> (`lastenheft.md`) frei von Abwaerts-Verweisen bleibt. Dieses Dokument
> erfuellt die `GG-TRACE-001`-Anforderung. Die `27.x`-Abschnittsnummern
> sind zur Referenz-Kontinuitaet mit bestehenden Verweisen beibehalten.


Diese Matrix verbindet jede Lastenheft-Anforderung mit ihrem Design-,
Implementierungs- und Testartefakt. Die drei Tabellen werden mit dem
Projektfortschritt gepflegt:

- Die Design-Tabelle (§27.1) ist gegen `spec/architecture.md` v0.1.0
  gepflegt (`GG-AR-*`-Kennungen).
- Die Implementierungs-Tabelle (§27.2) wird befuellt, sobald erste
  Code-Artefakte und Meilensteine definiert sind. Die Meilensteine
  `M1..Mn` leben in
  [`docs/plan/planning/in-progress/roadmap.md`](planning/in-progress/roadmap.md);
  die `GG-FUTURE-*`-Anforderungen in diesem Lastenheft sind
  ausschliesslich `KANN`-Punkte und nicht der Meilenstein-Plan.
- Die Test-Tabelle (§27.3) ist bereits jetzt aus dem Lastenheft ableitbar.

Status-Marker fuer die Implementierungs-Tabelle:

- ✓ `M[N]` — implementiert (Liefergegenstand des angegebenen Meilensteins)
- 🔲 — nicht implementiert (mit Verweis auf offene Frage oder Folgearbeit)

---

## 27.1 Anforderung zu Design

Design-Artefakte beziehen sich auf [`spec/architecture.md`](../../spec/architecture.md);
`GG-AR-*`-Kennungen sind dort definiert: Prinzipien `GG-AR-P-*`, Ports
`GG-AR-PORT-DRV-*` / `GG-AR-PORT-DRN-*`, Komponenten `GG-AR-COMP-*`,
Architektur-Tabus `GG-AR-TABU-*`, offene Punkte `GG-AR-OPEN-*`.
Querverweise nutzen Kennungen als primaere Referenz (siehe [`ADR 0004`](adr/0004-identifier-based-cross-references.md));
`§…`-Hinweise sind nur Lesehilfen in Klammern, wo eine Sektion noch
keine eigene Kennung traegt.

| Lastenheft-Kennung | Design-Artefakt                                                                                  |
| ------------------ | ------------------------------------------------------------------------------------------------ |
| GG-ARCH-001        | Schichtenmodell + `GG-AR-COMP-*`-Komponentenfamilie                                              |
| GG-ARCH-002        | [`GG-AR-P-002`](../../spec/architecture.md#2-architekturprinzipien) Hexagonale Architektur                                                              |
| GG-ARCH-003        | Dependency Rule + [`GG-AR-TABU-001`](../../spec/architecture.md#architektur-tabus-build-architekturtest) / [`GG-AR-TABU-002`](../../spec/architecture.md#architektur-tabus-build-architekturtest)                                             |
| GG-ARCH-004        | [`GG-AR-COMP-DEVICES`](../../spec/architecture.md#5-komponentensicht) + [`GG-AR-PORT-DRN-007`](../../spec/architecture.md#driven-ports-vom-kern-aufgerufen)                                                       |
| GG-ARCH-005        | [`GG-AR-COMP-CORE`](../../spec/architecture.md#5-komponentensicht) Tick-Loop + Domain-Event ([`GG-AR-COMP-DOMAIN`](../../spec/architecture.md#5-komponentensicht))                                  |
| GG-ARCH-006        | [`GG-AR-COMP-SCHED`](../../spec/architecture.md#5-komponentensicht) Tie-Breaking + [`GG-AR-P-008`](../../spec/architecture.md#2-architekturprinzipien) Determinismus-Invariante                          |
| GG-ARCH-007        | [`GG-AR-PORT-DRN-001`](../../spec/architecture.md#driven-ports-vom-kern-aufgerufen) (`ClockPort`) + [`GG-AR-TABU-005`](../../spec/architecture.md#architektur-tabus-build-architekturtest)                                              |
| GG-ARCH-008        | [`GG-AR-P-007`](../../spec/architecture.md#2-architekturprinzipien) Live- und Replay-Tick-Loop geteilt                                                  |
| GG-PRINC-001       | [`GG-AR-P-001`](../../spec/architecture.md#2-architekturprinzipien)..014 Architekturprinzipien — SOLID gesamt als Architekturzusicherung; automatisierte Teilabdeckung siehe `GG-PRINC-002..006` |
| GG-PRINC-002       | SRP — `ruff` `PLR0902` (max-attributes), `PLR0904` (max-public-methods), `C901` (McCabe), `PLR0915` (max-statements); Restanteil bleibt Code-Review |
| GG-PRINC-003       | OCP — primaer Code-Review; AST-Heuristik (Verbot von `isinstance(x, ConcreteType)` in `core/*`) ist Folgearbeit |
| GG-PRINC-004       | LSP — `mypy --strict` Type-Check-Gate ([`ADR 0005`](adr/0005-type-check-gate.md)) prueft Variance-Verstoesse in Subtypen; Restanteil Code-Review |
| GG-PRINC-005       | ISP — `ruff` `PLR0904` (max-public-methods, Schwelle 12), `PLR0903` (too-few-public-methods); mypy-Protocol-Konformitaet via [`ADR 0005`](adr/0005-type-check-gate.md); Restanteil Code-Review |
| GG-PRINC-006       | DIP — [`GG-AR-TABU-001`](../../spec/architecture.md#architektur-tabus-build-architekturtest)/002 + [`AC-CORE-NO-ADAPTERS`](adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)/[`AC-CORE-NO-DRIVING`](adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)/[`AC-NO-FW`](adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)/[`AC-PORTS-NO-FW`](adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) (vier von fuenfzehn A-1-Contracts in [`ADR 0002`](adr/0002-language-and-build-stack.md)) |
| GG-CC-002          | [`GG-AR-TABU-003`](../../spec/architecture.md#architektur-tabus-build-architekturtest) (Adapter-Logikverbot)                                                            |
| GG-CC-003          | [`GG-AR-TABU-002`](../../spec/architecture.md#architektur-tabus-build-architekturtest) (Domain ohne Framework-Imports)                                                  |
| GG-CC-004          | [`GG-AR-TABU-004`](../../spec/architecture.md#architektur-tabus-build-architekturtest) (keine Zyklen)                                                                    |
| GG-CC-006          | [`GG-AR-TABU-007`](../../spec/architecture.md#architektur-tabus-build-architekturtest) (keine God-Utility-Classes)                                                       |
| GG-CC-007          | [`GG-AR-TABU-006`](../../spec/architecture.md#architektur-tabus-build-architekturtest) (immutable Domain-Objekte) + [`GG-AR-COMP-DOMAIN`](../../spec/architecture.md#5-komponentensicht)                                  |
| GG-CC-008          | [`GG-AR-TABU-008`](../../spec/architecture.md#architektur-tabus-build-architekturtest) (explizite Fehlerbehandlung)                                                      |
| GG-CC-001          | `ruff` `PLR0915`/`PLR0912`/`PLR0913`/`PLR0911`/`C901` mit `max-statements=30`, `max-complexity=10` ([`ADR 0002`](adr/0002-language-and-build-stack.md), A-1 `ruff`-Konfiguration); Restanteil bleibt Code-Review |
| GG-CC-005          | `ruff` `N` (pep8-naming, formale Konsistenz von Klassen-/Funktions-/Konstantennamen); fachliche Bedeutung der Namen bleibt Code-Review |
| GG-SIM-001..004    | [`GG-AR-COMP-CORE`](../../spec/architecture.md#5-komponentensicht) Tick-Loop + [`GG-AR-P-008`](../../spec/architecture.md#2-architekturprinzipien) Determinismus-Invariante                              |
| GG-SIM-005         | [`GG-AR-PORT-DRV-005`](../../spec/architecture.md#driving-ports-vom-kern-angeboten) (`SnapshotPort`)                                                              |
| GG-SIM-006         | [`GG-AR-PORT-DRV-003`](../../spec/architecture.md#driving-ports-vom-kern-angeboten) (`ReplayPort`) + [`GG-AR-P-007`](../../spec/architecture.md#2-architekturprinzipien) geteilter Tick-Loop                            |
| GG-SIM-007         | [`GG-AR-COMP-CORE`](../../spec/architecture.md#5-komponentensicht) Wall-Clock-Multiplikatoren (Replay-Faktoren)                                    |
| GG-SIM-008         | [`GG-AR-PORT-DRV-001`](../../spec/architecture.md#driving-ports-vom-kern-angeboten) (`RunControlPort`)                                                            |
| GG-SIM-009         | [`GG-AR-COMP-DOMAIN`](../../spec/architecture.md#5-komponentensicht) `RunMetadata` + [`GG-AR-COMP-PERSIST`](../../spec/architecture.md#5-komponentensicht) Schema                                    |
| GG-RT-001          | [`GG-AR-COMP-CORE`](../../spec/architecture.md#5-komponentensicht) Tick-Dauer 10ms–1s, MVP-Modus-Definition                                        |
| GG-RT-002          | [`GG-AR-COMP-CORE`](../../spec/architecture.md#5-komponentensicht) + [`GG-AR-P-008`](../../spec/architecture.md#2-architekturprinzipien) Determinismus-Invarianten                                       |
| GG-RT-003          | [`GG-AR-COMP-DOMAIN`](../../spec/architecture.md#5-komponentensicht) Quality-Markierung (`stale`) + [`GG-AR-PORT-DRN-001`](../../spec/architecture.md#driven-ports-vom-kern-aufgerufen)                            |
| GG-RT-004/005      | [`GG-AR-COMP-OBS`](../../spec/architecture.md#5-komponentensicht) Metriken + [`GG-AR-COMP-CORE`](../../spec/architecture.md#5-komponentensicht) Commit-Pipeline                                      |
| GG-RT-006          | [`GG-AR-COMP-REPLAY`](../../spec/architecture.md#5-komponentensicht) Replay-Faktor-Tabelle                                                          |
| GG-DATA-001..004   | [`GG-AR-COMP-DOMAIN`](../../spec/architecture.md#5-komponentensicht) (TelemetryPoint, Command, Quality)                                            |
| GG-DATA-005        | [`GG-AR-COMP-DOMAIN`](../../spec/architecture.md#5-komponentensicht) + [`GG-AR-COMP-SCENARIO`](../../spec/architecture.md#5-komponentensicht) kanonische Serialisierung                              |
| GG-DEV-001         | [`GG-AR-COMP-DEVICES`](../../spec/architecture.md#5-komponentensicht) Geraetemodell-Vertrag                                                         |
| GG-DEV-002         | [`GG-AR-COMP-DOMAIN`](../../spec/architecture.md#5-komponentensicht) `TelemetryPoint`                                                               |
| GG-DEV-003         | [`GG-AR-COMP-DOMAIN`](../../spec/architecture.md#5-komponentensicht) `Command` + REST/WS-API in [`GG-AR-COMP-API`](../../spec/architecture.md#5-komponentensicht)                                    |
| GG-DEV-010..018    | [`GG-AR-COMP-DEVICES`](../../spec/architecture.md#5-komponentensicht) (MVP- und SOLLTE-Modelle)                                                     |
| GG-BESS-001..008   | [`GG-AR-COMP-DEVICES`](../../spec/architecture.md#5-komponentensicht) (Batteriemodell) + [`GG-AR-P-010`](../../spec/architecture.md#2-architekturprinzipien) Eingabe-Sicherheit                           |
| GG-GRID-001..007   | [`GG-AR-COMP-DEVICES`](../../spec/architecture.md#5-komponentensicht) (Netzmodell)                                                                  |
| GG-SCN-001..008    | [`GG-AR-COMP-SCENARIO`](../../spec/architecture.md#5-komponentensicht) Validierungs-Pipeline                                                        |
| GG-REPLAY-001..006 | [`GG-AR-COMP-REPLAY`](../../spec/architecture.md#5-komponentensicht) + [`GG-AR-PORT-DRV-003`](../../spec/architecture.md#driving-ports-vom-kern-angeboten)                                                         |
| GG-REPLAY-007      | [`GG-AR-COMP-REPLAY`](../../spec/architecture.md#5-komponentensicht) Diff-Klassifikation                                                            |
| GG-FAULT-001..010  | [`GG-AR-COMP-FAULTS`](../../spec/architecture.md#5-komponentensicht) Fault-Injection-Architektur                                                    |
| GG-AGENT-001..008  | [`GG-AR-COMP-AGENTS`](../../spec/architecture.md#5-komponentensicht) Multi-Agent-Subsystem                                                          |
| GG-API-001         | [`GG-AR-COMP-API`](../../spec/architecture.md#5-komponentensicht) REST-Endpunkte (`/runs`, `/runs/{id}/...`)                                        |
| GG-API-002         | [`GG-AR-COMP-API`](../../spec/architecture.md#5-komponentensicht) WebSocket-Telemetrie                                                              |
| GG-API-003         | [`GG-AR-COMP-API`](../../spec/architecture.md#5-komponentensicht) OpenAPI                                                                            |
| GG-API-004         | [`GG-AR-COMP-API`](../../spec/architecture.md#5-komponentensicht) Fehlerformat                                                                       |
| GG-MQTT-001        | [`GG-AR-COMP-PROTOCOLS`](../../spec/architecture.md#5-komponentensicht) + [`GG-AR-PORT-DRN-007`](../../spec/architecture.md#driven-ports-vom-kern-aufgerufen)                                                       |
| GG-MODB-001        | [`GG-AR-COMP-PROTOCOLS`](../../spec/architecture.md#5-komponentensicht) + [`GG-AR-PORT-DRN-007`](../../spec/architecture.md#driven-ports-vom-kern-aufgerufen)                                                       |
| GG-OPCUA-001       | [`GG-AR-COMP-PROTOCOLS`](../../spec/architecture.md#5-komponentensicht) + [`GG-AR-PORT-DRN-007`](../../spec/architecture.md#driven-ports-vom-kern-aufgerufen)                                                       |
| GG-DNP3-001        | [`GG-AR-COMP-PROTOCOLS`](../../spec/architecture.md#5-komponentensicht) + [`GG-AR-PORT-DRN-007`](../../spec/architecture.md#driven-ports-vom-kern-aufgerufen)                                                       |
| GG-IEC-001         | [`GG-AR-COMP-PROTOCOLS`](../../spec/architecture.md#5-komponentensicht) + [`GG-AR-PORT-DRN-007`](../../spec/architecture.md#driven-ports-vom-kern-aufgerufen)                                                       |
| GG-SNMP-001        | [`GG-AR-COMP-PROTOCOLS`](../../spec/architecture.md#5-komponentensicht) + [`GG-AR-PORT-DRN-007`](../../spec/architecture.md#driven-ports-vom-kern-aufgerufen)                                                       |
| GG-LWM2M-001       | [`GG-AR-COMP-PROTOCOLS`](../../spec/architecture.md#5-komponentensicht) + [`GG-AR-PORT-DRN-007`](../../spec/architecture.md#driven-ports-vom-kern-aufgerufen)                                                       |
| GG-UI-001..009     | [`GG-AR-COMP-UI`](../../spec/architecture.md#5-komponentensicht)                                                                                     |
| GG-PERSIST-001..004 | [`GG-AR-COMP-PERSIST`](../../spec/architecture.md#5-komponentensicht) Schema + [`GG-AR-PORT-DRN-002`](../../spec/architecture.md#driven-ports-vom-kern-aufgerufen)                                                 |
| GG-PERSIST-005     | [`GG-AR-COMP-PERSIST`](../../spec/architecture.md#5-komponentensicht) (PostgreSQL Pflicht)                                                          |
| GG-PERSIST-006/007 | [`GG-AR-COMP-PERSIST`](../../spec/architecture.md#5-komponentensicht) optionale Adapter (Timescale / Influx)                                         |
| GG-PERSIST-008     | [`GG-AR-COMP-PERSIST`](../../spec/architecture.md#5-komponentensicht) Migrations-Schicht                                                             |
| GG-PERSIST-009     | [`GG-AR-PORT-DRN-003`](../../spec/architecture.md#driven-ports-vom-kern-aufgerufen) + [`GG-AR-COMP-PERSIST`](../../spec/architecture.md#5-komponentensicht) `RunRepositoryPort`                                     |
| GG-OTEL-001..004   | [`GG-AR-COMP-OBS`](../../spec/architecture.md#5-komponentensicht) + [`GG-AR-PORT-DRN-008`](../../spec/architecture.md#driven-ports-vom-kern-aufgerufen)                                                             |
| GG-SAFE-001..004   | [`GG-AR-P-010`](../../spec/architecture.md#2-architekturprinzipien) Sicherer Default + [`GG-AR-COMP-CORE`](../../spec/architecture.md#5-komponentensicht) Quality-Markierung                               |
| GG-SAFE-005        | [`GG-AR-P-010`](../../spec/architecture.md#2-architekturprinzipien) Sicherer Default (Fallback-Variante in [`GG-AR-COMP-DEVICES`](../../spec/architecture.md#5-komponentensicht))                          |
| GG-SAFE-006        | [`GG-AR-COMP-REPLAY`](../../spec/architecture.md#5-komponentensicht) Diff + [`GG-AR-COMP-OBS`](../../spec/architecture.md#5-komponentensicht) Replay-Diff-Status                                      |
| GG-SAFE-007        | [`GG-AR-P-011`](../../spec/architecture.md#2-architekturprinzipien) Trennung Simulation/Produktion                                                        |
| GG-SAFE-008        | [`GG-AR-COMP-API`](../../spec/architecture.md#5-komponentensicht) Eingabe-Validierung + [`GG-AR-COMP-SCENARIO`](../../spec/architecture.md#5-komponentensicht) Scenario-Validator                     |
| GG-TESTTYPE-001..007 | [`GG-AR-TEST-001`](../../spec/architecture.md#18-rueckverfolgbarkeit-architektur--lastenheft)                                                                                  |
| GG-ARCHTEST-001..005 | [`GG-AR-TABU-001`](../../spec/architecture.md#architektur-tabus-build-architekturtest)..008 + [`GG-AR-TEST-001`](../../spec/architecture.md#18-rueckverfolgbarkeit-architektur--lastenheft)                                                          |
| GG-CICD-001..007   | [`GG-AR-TEST-001`](../../spec/architecture.md#18-rueckverfolgbarkeit-architektur--lastenheft) + [`GG-AR-COMP-DEPLOY`](../../spec/architecture.md#5-komponentensicht)                                                              |
| GG-DEPLOY-001..011 | [`GG-AR-COMP-DEPLOY`](../../spec/architecture.md#5-komponentensicht)                                                                                 |
| GG-DEMO-001..008   | [`GG-AR-COMP-DEPLOY`](../../spec/architecture.md#5-komponentensicht) (Compose-Demo) + [`GG-AR-TEST-001`](../../spec/architecture.md#18-rueckverfolgbarkeit-architektur--lastenheft) (E2E/Demo-Abnahme)                            |
| GG-ACCEPT-001..003 | [`GG-AR-TEST-001`](../../spec/architecture.md#18-rueckverfolgbarkeit-architektur--lastenheft) + `GG-TRACE-001`                                                                   |
| GG-TRACE-001       | Rueckverfolgbarkeitstabelle in `architecture.md` (§18) — Quelle fuer diese §27.1-Tabelle             |
| GG-TEST-001..008   | [`GG-AR-TEST-001`](../../spec/architecture.md#18-rueckverfolgbarkeit-architektur--lastenheft) (Replay-/Fault-/Determinismus-Tests)                                               |
| GG-COV-001..005    | [`GG-AR-TEST-001`](../../spec/architecture.md#18-rueckverfolgbarkeit-architektur--lastenheft) (Coverage-Block und Quality Gates)                                                 |
| GG-QG-001..007     | [`GG-AR-TEST-001`](../../spec/architecture.md#18-rueckverfolgbarkeit-architektur--lastenheft) (Quality Gates) + [`GG-AR-COMP-DEPLOY`](../../spec/architecture.md#5-komponentensicht) (CI-Gating)                                   |
| GG-QA-001..006     | [`GG-AR-TEST-001`](../../spec/architecture.md#18-rueckverfolgbarkeit-architektur--lastenheft) + [`GG-AR-TABU-001`](../../spec/architecture.md#architektur-tabus-build-architekturtest)..008 (statische Pruefungen)                                     |

### 27.1.1 Anforderungen ohne Design-Artefakt

Die folgenden Anforderungsfamilien sind **Scope-, Definitions- oder
Zukunftsanforderungen** und mappen bewusst auf kein
Design-Artefakt in `architecture.md`:

| Lastenheft-Kennung      | Begruendung                                                       |
| ----------------------- | ----------------------------------------------------------------- |
| GG-TERM-001..006        | n/a — normative Begriffsdefinition (Vokabular `MUSS`/`DARF NICHT`/`SOLLTE`/`KANN`) |
| GG-SEED-001             | n/a — Projekt-Seed-Konvention (Test-Setup-Vorgabe, keine Architektur) |
| GG-MVP-001..004         | n/a — Scope-Festlegung; Auspraegung lebt in einzelnen `GG-SIM/DEV/...`-IDs |
| GG-NONGOAL-001..005     | n/a — explizite Scope-Grenzen (negativ definierte Anforderung)     |
| GG-FUTURE-001..006      | n/a — `KANN`-Zukunftsanforderungen `GG-FUTURE-*`; Design folgt erst bei Aktivierung im Abnahmescope |

---

## 27.2 Anforderung zu Implementierung

Erstmalig befuellt im Rahmen eines Lastenheft-Sweeps
(2026-05-18). Eintraege folgen der Roadmap-Vorbelegung:
✓ `M1` = vom M1-Tick-Loop-Spine geliefert (Closure-Notiz
[`done/M1-tick-loop-spine.md`](planning/done-archive/M1-tick-loop-spine.md));
🔲 `M[N]` = vorbelegt, Lieferziel des angegebenen Meilensteins
laut [`roadmap.md`](planning/in-progress/roadmap.md);
🔲 `Post-MVP` = SOLLTE-Anforderung jenseits des MVP-Scopes
ohne aktiven Slice. Querverweise auf Module sind Pfade unterhalb
von `src/grid_gym/` bzw. `tools/` und `Dockerfile`/`Makefile`/
`deploy/` an der Repo-Wurzel.

**Range-Konvention** (Review-Befund M-8): `001..005` fuer
zusammenhaengende Bereiche, `001..005, 008` fuer Loecher.
Reine `/`-Trennung (z. B. `006/007`) ist nicht mehr zugelassen,
weil sie maschinelle Range-Auswertung gegenueber `..` brittle
macht.

**Ausnahme** (Review-Befund M-9): `GG-TERM-003` (§2 Glossar,
„kanonisches Ergebnis") taucht in §6..§25 auf, hat aber keinen
Implementierungs-Charakter — Behandlung in §27.1.1
(`GG-TERM-001..006 — n/a, normative Begriffsdefinition`).
Damit ist `GG-TERM-003` bewusst nicht in der Implementations-
Matrix unten.

**Status-Re-Sweep 2026-07-10 (Slice 060).** Die Status-Spalte wurde gegen den
gelieferten Code-Stand (M8 / v0.3.1) re-verifiziert — die urspruengliche
Befuellung stand auf M1/M2-Stand und wurde nach M3..M8 nie
nachgezogen (Dutzende gelieferte Anforderungen standen noch auf `🔲`). `✓ M[N]`
heisst geliefert; die `kommt mit M[N]`/`— M[N]`-Formulierungen in der
Implementierungs-Spalte sind **historische Liefer-Ziele** und gelten als
erfuellt, wo die Status-Spalte `✓` zeigt. Verbleibend `🔲`:

- **MUSS-Luecken:** `GG-RT-006` (Zeit-Multiplikatoren `0.5x/1x/10x/unbounded`
  — Tick-Frequenz ist heute Aufrufer-Sache, keine Multiplikator-Config) und
  `GG-PERSIST-009` (Lauf-Loeschung — kein `DELETE`-Endpoint / Repository-`delete`).
- **SOLLTE / Post-MVP:** `GG-PERSIST-006..007` (Timescale/Influx),
  `GG-DEPLOY-004..010` (nur Kubernetes-Teil; Compose/Offline geliefert),
  `GG-SNMP-001`/`GG-LWM2M-001` (Device-Management-Adapter, Trigger 047).
- **Ziel offen:** `GG-COV-004..005` (95%-Coverage-Ziel; Pflicht-Gate 90/85).

| Lastenheft-Kennung   | Implementierung                                                                                                                                                                                                                                                                                                                                                                                | Status      |
| -------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------- |
| GG-SIM-001..004      | `hexagon/core/simulation/scheduler.py` (Tie-Breaking, `GG-ARCH-006`), `hexagon/core/simulation/tick_loop.py` (Tick-Pipeline + `RandomPort`/`ClockPort`-Injektion). Determinismus-Property in `tests/unit/hexagon/core/simulation/`.                                                                                                                                                            | ✓ M1        |
| GG-SIM-005           | `hexagon/core/simulation/tick_loop.py::snapshot/from_snapshot`, `hexagon/core/domain/snapshot.py` (`SnapshotEnvelope`), Composition via `hexagon/ports/driven/random.py::snapshot_as_mapping` ([`ADR 0010`](adr/0010-randomport-snapshot-as-mapping.md)).                                                                                                                                                                                    | ✓ M1        |
| GG-SIM-006           | `hexagon/core/replay/mapper.py` (CSV/JSON-Lines-Import, `GG-REPLAY-001/002`), `hexagon/core/replay/diff.py` (Diff, `GG-REPLAY-007`). Tick-Prozessor wird in M3 produktiv mit Replay-Source verkabelt.                                                                                                                                                                                          | ✓ M1        |
| GG-SIM-007           | `hexagon/core/simulation/tick_loop.py` laeuft heute ohne Wall-Clock-Wait — der Aufrufer entscheidet ueber Tick-Frequenz (`tests/unit/hexagon/core/simulation/test_tick_loop.py`). Replay-Faktoren sind `GG-RT-006`.                                                                                                                                                                            | ✓ M1        |
| GG-SIM-008           | Snapshot/Resume traegt Pause/Resume de-facto (`TickLoop.from_snapshot`). Formale `RunControlPort`-API ([`GG-AR-PORT-DRV-001`](../../spec/architecture.md#driving-ports-vom-kern-angeboten)) kommt mit Multi-Agent / Run-Lifecycle.                                                                                                                                                                                                                          | ✓ M5 |
| GG-SIM-009           | `hexagon/core/domain/run.py` (`RunMetadata`), `adapters/driven/persistence_postgres/` (Postgres-`runs`-Repository, M1). Voller Export inklusive Telemetrie + Alarme braucht `TelemetrySinkPort` / `AlarmSinkPort` (M3).                                                                                                                                                              | ✓ M1+M3 |
| GG-RT-001            | `hexagon/core/scenario/loader.py` validiert `tick_ms` (10/100/1000) ueber Scenario-Schema. Demo-Konfiguration + Backpressure-Healthcheck sind `GG-RT-005`-Tail (M6).                                                                                                                                                                                                                          | ✓ M1+M6 |
| GG-RT-002            | `hexagon/core/simulation/scheduler.py` Tie-Breaking + Determinismus-Property; gleicher Seed → byte-identische Reihenfolge.                                                                                                                                                                                                                                                                    | ✓ M1        |
| GG-RT-003            | `hexagon/core/domain/quality.py` Enum-Wert `stale` vorhanden; `max_age`-basierte Markierung im Tick-Schritt 6 (Quality-Markierung) kommt mit M3 ([`GG-AR-COMP-CORE`](../../spec/architecture.md#5-komponentensicht) Quality-Pipeline). M2-Geraete liefern Wert+Quality-Tupel ohne stale-Logik.                                                                                                                                                | ✓ M6/M7 |
| GG-RT-004/005        | Performance-Benchmark (100 Geraete, 10.000 Punkte/s) — `GG-RT-005`-Akzeptanz ist M6-Pflicht-Item.                                                                                                                                                                                                                                                                                            | ✓ M6 |
| GG-RT-006            | Replay-Faktor-Tabelle / Time-Multiplier (`0.5x/1x/10x/unbounded`). **Offen**: die Tick-Frequenz ist heute Aufrufer-Sache (`GG-SIM-007`), es gibt keine Multiplikator-Konfiguration.                                                                                                                                                                                                                                                                                                            | 🔲 Open (MUSS-Luecke) |
| GG-DATA-001          | `hexagon/core/domain/telemetry.py::TelemetryPoint` (Frozen-Dataclass).                                                                                                                                                                                                                                                                                                                          | ✓ M1        |
| GG-DATA-002          | `TelemetryPoint.unit: str` Feld vorhanden. Einheiten-Whitelist-Enforcement ist Geraete-Emitter-Verantwortung (M2) — Domain-Klasse haelt nur den Stringtyp.                                                                                                                                                                                                                                    | ✓ M1+M2 |
| GG-DATA-003          | `hexagon/core/domain/quality.py::Quality` Enum mit `valid/stale/estimated/limited/invalid/nan/missing/fault_injected`.                                                                                                                                                                                                                                                                         | ✓ M1        |
| GG-DATA-004          | `hexagon/core/domain/command_result.py::CommandResult` Enum mit `accepted/rejected/limited/expired/failed/ignored`.                                                                                                                                                                                                                                                                            | ✓ M1        |
| GG-DATA-005          | `hexagon/core/serialization/canonical.py::canonical_json` ([`ADR 0002`](adr/0002-language-and-build-stack.md) §A-2); [`AC-NO-JSON`](adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) Whitelist auf dieses Modul. Payload-Canonical-Check `hexagon/core/serialization/snapshot_codec.py` (M2, Trigger 014).                                                                                                                                                                       | ✓ M1        |
| GG-DEV-001           | `DeviceModel`-Protocol (`initialize`/`apply_command`/`tick`/`snapshot`/`telemetry` + `device_id`-Property + `from_snapshot`-Classmethod) in `hexagon/core/devices/_protocol.py` (M2). [`ADR 0013`](adr/0013-device-model-protocol.md) `Accepted` mit Review-Schaerfungen (§§2.5-2.8 + §8). Geraete-Implementationen (`GG-DEV-010..014`) sind weiterhin M2. | ✓ M2 |
| GG-DEV-002           | `TelemetryPoint` (M1) deckt das Datenmodell ab; das `telemetry()`-Surface ist mit dem Protocol (M2) verbindlich. Geraete-Implementationen emittieren TelemetryPoints ab M2.                                                                                                                                                                                                | ✓ M2 |
| GG-DEV-003           | `Command` + `CommandResult` (M1) decken das Datenmodell ab; `apply_command(cmd) -> CommandResult` ist mit dem Protocol (M2) verbindlich.                                                                                                                                                                                                                                       | ✓ M2 |
| GG-DEV-010           | `BatteryDevice` in `hexagon/core/devices/battery/` (M2, [`ADR 0014`](adr/0014-battery-snapshot-schema.md) `Accepted`). Minimalmodell, Snapshot-Roundtrip, Determinismus-Property ueber 100 Ticks, Trigger-013-Test mit `tick_ms=100`. Demo-Szenario folgt mit M2.                                                                                                                                                       | ✓ M2 |
| GG-DEV-011           | `PvDevice` in `hexagon/core/devices/pv/` (M2, [`ADR 0016`](adr/0016-pv-load-device-pattern.md) `Accepted`). Konstantes `rated_power_kw`-Erzeugungsmodell mit `set_power_kw`-Override; Sign-Vertrag-Pruefung + Snapshot-Roundtrip + Determinismus-Property ueber 100 Ticks.                                                                                                                                                    | ✓ M2 |
| GG-DEV-013           | `LoadDevice` in `hexagon/core/devices/load/` (M2, [`ADR 0016`](adr/0016-pv-load-device-pattern.md) `Accepted`). Spiegel zu PV; Sign-Konvention „Load verbraucht nicht-negativ".                                                                                                                                                                                                                                              | ✓ M2 |
| GG-DEV-012, 014      | MVP-Geraete `grid_connection`/`smart_meter` — M2.                                                                                                                                                                                                                                                                                                                                      | ✓ M2 |
| GG-DEV-015..018      | SOLLTE-Geraete (`ev_charger`, `transformer`, `wind_turbine`, `diesel_generator`) — eigene Slices nach M2-Closure.                                                                                                                                                                                                                                                                              | ✓ M8 |
| GG-BESS-001..005, 008 | `BatteryDevice` + `BatteryConfig` + `validate_set_power_command` (M2, [`ADR 0014`](adr/0014-battery-snapshot-schema.md) `Accepted`). SOC-Fortschreibung mit Wirkungsgrad, Ramp-Limit, SOC-Hard-Clamp, Initialvalidierung pro Feld.                                                                                                                                                                                              | ✓ M2 |
| GG-BESS-006/007      | SOLLTE: Temperatur, Zellspannungs-Delta — eigene Slices nach M2-Closure.                                                                                                                                                                                                                                                                                                                       | ✓ M8 |
| GG-GRID-001..004     | Netzbilanzmodell (Frequenz/Spannung/Lasten/Lastspruenge) — M2 (Modul `hexagon/core/grid_model/`).                                                                                                                                                                                                                                                              | ✓ M2 |
| GG-GRID-005..007     | SOLLTE: Inselnetz, Transformatorgrenzen, Blindleistung — eigene Slices nach M2-Closure.                                                                                                                                                                                                                                                                                                        | ✓ M8 |
| GG-SCN-001..008      | `hexagon/core/scenario/loader.py` (Mapping-Input, Hash via `canonical_json`), `hexagon/core/scenario/validator.py` (`GG-SCN-008`-Vorab-Validierung inkl. Payload-Canonical via Trigger 014). YAML-Adapter ist M2/M3-Driven-Adapter, Mapping-Input ist hexagon-pur.                                                                                                                            | ✓ M1        |
| GG-REPLAY-001..003   | `hexagon/core/replay/mapper.py` (CSV/JSON-Lines, `time_mapping=monotonic|index`).                                                                                                                                                                                                                                                                                                              | ✓ M1        |
| GG-REPLAY-004..006   | Replay-Diff-Status / Telemetrie-Replay-Monitoring kommt mit M3 (`GG-SAFE-006`-Pfad).                                                                                                                                                                                                                                                                                                            | ✓ M3 |
| GG-REPLAY-007        | `hexagon/core/replay/diff.py` (`diff_replay`, Trigger 013 `tick_ms`-Parameter in M2 (Commit `48f0106`) geliefert; Closure-Notiz [`done/013-replay-diff-tick-ms-parameter.md`](planning/done-archive/013-replay-diff-tick-ms-parameter.md)).                                                                                                                                       | ✓ M1+M2     |
| GG-FAULT-001..010    | Fault-Injection-Subsystem (`hexagon/core/faults/`) — M3.                                                                                                                                                                                                                                                                                                                                       | ✓ M3 |
| GG-AGENT-001..008    | Multi-Agent-Bus (`hexagon/core/agents/`) — M3.                                                                                                                                                                                                                                                                                                                                                  | ✓ M3 |
| GG-API-001           | `adapters/driving/http_api/app.py::POST /runs` (Stub mit `RunRepositoryPort.save`). `GET /runs/{id}/...` (Lauf-Status, Telemetrie-Stream, Steuerung) kommt mit M3/M5.                                                                                                                                                                                                                          | ✓ M3/M5 |
| GG-API-002           | WebSocket-Telemetrie — M3 (`TelemetrySinkPort` + UI-Konsum).                                                                                                                                                                                                                                                                                                                                    | ✓ M3/M5 |
| GG-API-003           | `adapters/driving/http_api/app.py` exportiert `app.openapi()`; `make openapi-validate` (Dockerfile-Stage) prueft Spec gegen `openapi-spec-validator`.                                                                                                                                                                                                                                         | ✓ M1        |
| GG-API-004           | FastAPI/pydantic liefern impliziten Default-Fehlerformat; RFC-7807-konformer Body + Domain-Fehler-Mapping (`adapters/driving/http_api/error_translation.py`) kommt mit M3.                                                                                                                                                                                                                    | ✓ M3 |
| GG-MQTT-001          | MQTT-Adapter (`adapters/driven/protocol_mqtt/`) — M4 ([`ADR 0031`](adr/0031-mqtt-adapter-profile.md) `Provisional`; siehe [`spec/protocol_profiles.md`](../../spec/protocol_profiles.md) §MQTT). Topic-Schema inline, `canonical_json`-Codec, QoS 0/1, Per-Target `queue.Queue`-Marshal, Mosquitto-Integration-Smoke.                                                                                                                       | ✅ M4       |
| GG-MODB-001          | Modbus-Adapter (`adapters/driven/protocol_modbus/`) — M4 + Slice 031 ([`ADR 0032`](adr/0032-modbus-adapter-profile.md) `Provisional`; siehe [`spec/protocol_profiles.md`](../../spec/protocol_profiles.md) §Modbus-TCP). Register-Schema inline, 5 Datatypes, direkt-sync, FC03/FC10-Defaults mit FC04/FC06-Overrides, in-process pymodbus-Smoke.                                                                                            | ✅ M4       |
| GG-OPCUA-001         | OPC-UA-Adapter (`adapters/driven/protocol_opcua/`) — M4 + Slice 032 ([`ADR 0033`](adr/0033-opcua-adapter-profile.md) `Provisional`; siehe [`spec/protocol_profiles.md`](../../spec/protocol_profiles.md) §OPC-UA). **Erster rein-async-Stack** im Repo via eigenen `OpcuaLoopThread`. 8 Datatypes, Polling-Read + Direct-Write, in-process `asyncua.Server`-Smoke.                                                                          | ✅ M4       |
| GG-DNP3-001          | DNP3-Adapter (`adapters/driven/protocol_dnp3/`) — M4 ([`ADR 0034`](adr/0034-dnp3-adapter-profile.md) `Provisional`; siehe [`spec/protocol_profiles.md`](../../spec/protocol_profiles.md) §DNP3). **Zwei-Library-Setup** `nfm-dnp3` (Master, MIT, produktiv) + `dnp3-outstation` (Outstation, MIT, **nur Test-Sibling**). Group/Variation-Set `{(1,1),(1,2),(30,1),(30,5)}`, Class-0-Polling-Read mit Resultat-Filter-by-Index. **Erfuellung ueber Pfad A** (Adapter geliefert); historische Akzeptanz erlaubte alternativ dokumentierten Out-of-Scope-Verzicht (Slice 034 F15: Audit-Trail-Note).            | ✅ M4       |
| GG-IEC-001           | IEC-61850-Adapter (`adapters/driven/protocol_iec61850/`) — M4 + Slice 033 ([`ADR 0035`](adr/0035-iec61850-adapter-profile.md) `Provisional`; siehe [`spec/protocol_profiles.md`](../../spec/protocol_profiles.md) §IEC-61850). **GPLv3-isoliert** per SPDX-Header pro Datei (Decision I-f; **erstmaliger Repo-Praezedenzfall** fuer GPL-isolierte Sub-Module in einem sonst MIT-Projekt). `pyiec61850-ng` als opt-in Extra `pip install grid-gym[iec61850]`. Datatype-Set `{bool,int32,float,string}` × FC `{MX,ST,SP,CF,DC}`. Integration-Smoke aktuell unter 2c-Mock-only-Fallback (Python-3.14-SWIG-Inkompat; Folge-Schaerfung). **Erfuellung ueber Pfad A** (Adapter geliefert); historische Akzeptanz erlaubte alternativ dokumentierten Out-of-Scope-Verzicht (Slice 034 F15: Audit-Trail-Note). | ✅ M4       |
| GG-SNMP-001          | SNMP-Adapter (`adapters/driven/protocol_snmp/`) — Device-Management-/Telemetry-Folgearbeit. Profil, ADR, Library-Wahl, Smoke-Sibling und Implementierung sind noch offen; Trigger-Watch [`047-device-management-protocol-adapters.md`](planning/open/047-device-management-protocol-adapters.md). Kein Support-Claim bis Adapter + Profil geliefert sind.                                                                                                                                        | 🔲 Open     |
| GG-LWM2M-001         | LwM2M-Adapter (`adapters/driven/protocol_lwm2m/`) — Device-Management-/Telemetry-Folgearbeit. Profil, ADR, Library-Wahl, Smoke-Sibling und Implementierung sind noch offen; Trigger-Watch [`047-device-management-protocol-adapters.md`](planning/open/047-device-management-protocol-adapters.md). Kein Support-Claim bis Adapter + Profil geliefert sind.                                                                                                                                      | 🔲 Open     |
| GG-UI-001..009       | Web-UI (`ui/`-Modul) — M5.                                                                                                                                                                                                                                                                                                                                                                       | ✓ M5 |
| GG-PERSIST-001       | `adapters/driven/persistence_postgres/` mit `runs`-Schema. Telemetrie-/Alarm-Schema folgt mit `TelemetrySinkPort` (M3).                                                                                                                                                                                                                                                                       | ✓ M1+M3 |
| GG-PERSIST-002..004  | Telemetrie-Persistenz, Alarm-Persistenz, Retention-Policies — M3.                                                                                                                                                                                                                                                                                                                              | ✓ M3 |
| GG-PERSIST-005       | Postgres als Pflicht-Backend — `adapters/driven/persistence_postgres/` + `deploy/compose.yml` Postgres-Service.                                                                                                                                                                                                                                                                                | ✓ M1        |
| GG-PERSIST-006..007  | SOLLTE: Timescale / Influx — Post-MVP.                                                                                                                                                                                                                                                                                                                                                          | 🔲 Post-MVP |
| GG-PERSIST-008       | `alembic.ini` + `adapters/driven/persistence_postgres/migrations/` (`alembic upgrade head` in M1). Folge-Migrations kommen mit Telemetrie/Alarm-Schema (M3).                                                                                                                                                                                                                          | ✓ M1        |
| GG-PERSIST-009       | `hexagon/ports/driven/run_repository.py::RunRepositoryPort` + `InMemoryRunRepository` + `PostgresRunRepository`. Lauf-Loeschung via `DELETE /runs/{id}` ist **offen** (kein DELETE-Endpoint und kein Repository-`delete`).                                                                                                                                                                                | ✓ M1 (Vertrag), 🔲 Open (Delete-Operation, MUSS-Luecke) |
| GG-OTEL-001..004     | `LogPort`/`MetricsPort`/`TracePort` (`hexagon/ports/driven/observability.py`) + OTLP-Adapter — M3.                                                                                                                                                                                                                                                                                              | ✓ M3 |
| GG-SAFE-001..004     | Quality-Markierung-Pipeline (`GG-RT-003`-Pfad) — M3 mit der Tick-Loop-Quality-Stage 6. `RandomPort`-Seeding (`GG-SEED-001`) ist [`ADR 0007`](adr/0007-random-port.md) (`Accepted` 2026-05-17).                                                                                                                                                                                                                          | ✓ M6/M7 |
| GG-SAFE-005          | Geraete-Fallback-Verhalten (sicherer Default je Geraet) — M2 mit `BatteryDevice.apply_command` / Sicherheitsgrenzen-Validierung.                                                                                                                                                                                                                                                              | ✓ M2 |
| GG-SAFE-006          | Replay-Diff-Status-Markierung — M3 mit Replay-Source-Integration.                                                                                                                                                                                                                                                                                                                              | ✓ M3 |
| GG-SAFE-007          | Trennung Simulation/Produktion — `GG-NONGOAL-001` + `README.md`-Disclaimer. Architektur-Pruefung in `tools/arch_check.py` ([`AC-HEXAGON-PURE`](adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-Whitelist).                                                                                                                                                                                                                                       | ✓ M1        |
| GG-SAFE-008          | `hexagon/core/scenario/validator.py` (Eingabe-Validierung vor Tick) + `adapters/driving/http_api/app.py` (pydantic-Request-Schemas).                                                                                                                                                                                                                                                            | ✓ M1        |
| GG-TEST-001..018     | `tests/unit/**` (Property-/Smoke-/Negativ-Tests, 268 Tests M1), `tests/integration/**` (Postgres-Roundtrip via testcontainers). Replay- / Fault- / Determinismus-Marker via `make test-replay` / `test-fault` / `test-determinism`.                                                                                                                                                  | ✓ M1+M3 |
| GG-TESTTYPE-001..007 | Testtyp-Definitionen werden ueber pytest-Marker (`pyproject.toml` (`[tool.pytest.ini_options]`)) und Makefile-Targets erzwungen. E2E-/Demo-Marker kommen mit M5.                                                                                                                                                                                                                                                          | ✓ M5 |
| GG-ARCHTEST-001..005 | `tools/arch_check.py` (AST + grimp-SCC) + `import-linter` (16 A-1-Contracts, `pyproject.toml [tool.importlinter]`). Aggregator `make arch-check`.                                                                                                                                                                                                                                              | ✓ M1        |
| GG-COV-001..002      | `Dockerfile::coverage-gate`-Stage (`--cov-fail-under=$COVERAGE_THRESHOLD`, Branch via `coverage.xml`-Parse).                                                                                                                                                                                                                                                                                    | ✓ M1        |
| GG-COV-003           | `Dockerfile::coverage-gate-critical`-Stage (`CRITICAL_COV_TARGETS`-Liste, 90%-Schwelle). Default-Gate ohne Override gruen ab M2 (Battery liefert `devices/battery` ≥ 90 %).                                                                                                                                                                                                            | ✓ M2 |
| GG-COV-004..005      | Coverage-Reporting-Artefakte (`coverage.xml`) geliefert; das **95%-Ziel ist offen** (Pflicht-Gate steht bei 90/85).                                                                                                                                                                                                                                                                                                              | ✓ M6 (Artefakte), 🔲 offen (95%-Ziel; Gate 90/85) |
| GG-QG-001..005       | `make gates`-Aggregator (lint, format-check, typecheck mypy --strict, arch-check 16 Contracts, test-unit, coverage-gate, coverage-gate-critical, dep-audit). Konfiguration in `pyproject.toml` + Dockerfile-Stages.                                                                                                                                                                          | ✓ M1        |
| GG-QG-006            | `Dockerfile::openapi-validate`-Stage exportiert `app.openapi()` und prueft per `openapi-spec-validator`.                                                                                                                                                                                                                                                                                       | ✓ M1        |
| GG-QG-007            | Image-Audit (`make image-audit`, trivy `--ignore-unfixed`). Production-Image-Hardening (Trigger 015) geschlossen.                                                                                                                                                                                                                                                                     | ✓ M1        |
| GG-QA-001..006       | `make lint` (ruff BLE/TRY/B/DTZ/S/TID/PLR*/N), `make typecheck` (mypy --strict, [`ADR 0005`](adr/0005-type-check-gate.md)), `make dep-audit` (pip-audit `--strict`), `make image-audit` (trivy). SBOM ist `GG-CICD-007` (M6).                                                                                                                                                                                                | ✓ M1        |
| GG-CICD-001..006     | `Makefile`-Targets `gates` / `ci` / `fullbuild` decken den Build-/Test-/Gate-/Image-Pfad ab. GitHub-Actions-Matrix gegen 3.13+3.14 ist M6.                                                                                                                                                                                                                                                     | ✓ M6 |
| GG-CICD-007          | SBOM-Generierung (`make sbom VERSION=...` Stub vorhanden, scharf erst mit Artefakt-Veroeffentlichung) — Trigger 008 (`open/`), M6.                                                                                                                                                                                                                                                             | ✓ M6 |
| GG-DEPLOY-001..003   | `Dockerfile` runtime-Stage (non-root, /health-HEALTHCHECK, Port 8080), `deploy/compose.yml` (postgres + api + simulation-Stub). Trigger 015 hat shebang-Rewrite / `uv sync --no-editable` / direkte uvicorn-Binary nachgezogen.                                                                                                                                                  | ✓ M1+0b     |
| GG-DEPLOY-004..010   | Offline-Faehigkeit (kein Internet-Zugriff zur Laufzeit, `--no-pull` build), Linux-x86_64-Referenz, Multi-Service-Compose mit Healthchecks. Kubernetes-Manifeste sind Post-MVP.                                                                                                                                                                                                                | ✓ M1 (Compose), 🔲 Post-MVP (Kubernetes) |
| GG-DEPLOY-011        | `make runtime`-Compose-Smoke pollt `/health` mit Timeout — Verifikation gruen.                                                                                                                                                                                                                                                                                                          | ✓ M1+0b     |
| GG-DEMO-001..008     | Demo-Szenario `tests/integration/scenarios/mvp_demo.yaml` (`GG-MVP-002`-Pflicht) + Demo-UI-Lauf — M2 (Szenario) bzw. M5 (UI-Demo).                                                                                                                                                                                                                                                    | ✓ M2/M5 |
| GG-ACCEPT-001..003   | Abnahme-Artefakte: Closure-Notizen in `docs/plan/planning/done/` + Slice-Plan-Stack. Spike-0-Closure (`done/spike-0.md`), M1-Closure (`done/M1-tick-loop-spine.md` + `done/M1-tick-loop-results.md`), Trigger-Closures (`done/0NN-*`).                                                                                                                                                       | ✓ M1        |
| GG-TRACE-001         | Diese §27.2-Tabelle + §27.1-Tabelle + §27.3-Tabelle. `make docs-check` (d-check) validiert Markdown-Querverweise (`make docs-check`). Der initiale Sweep (2026-05-18) hat die §27.2-Befuellung mechanisch durchgefuehrt.                                                                                                                                                                                       | ✓ M1+0c     |

---

## 27.3 Anforderung zu Test

Die Testtypen entsprechen `GG-TESTTYPE-001..007`.
Die Tabelle deckt diejenigen Anforderungen ab, deren Testtyp bereits aus dem
Lastenheft ableitbar ist; weitere Eintraege folgen mit der Implementierung.

| Lastenheft-Kennung | Testtyp                          |
| ------------------ | -------------------------------- |
| GG-SIM-001         | Unit Test                        |
| GG-SIM-002         | Unit Test                        |
| GG-SIM-003         | Unit Test                        |
| GG-SIM-004         | Unit Test                        |
| GG-SIM-005         | Unit Test                        |
| GG-RT-001          | Unit Test                        |
| GG-RT-002          | Integration Test                 |
| GG-RT-003          | Unit Test                        |
| GG-DATA-001        | Unit Test                        |
| GG-DATA-002        | Unit Test                        |
| GG-DATA-003        | Unit Test                        |
| GG-BESS-001        | Unit Test                        |
| GG-BESS-002        | Unit Test                        |
| GG-BESS-005        | Unit Test                        |
| GG-GRID-001        | Unit Test                        |
| GG-GRID-003        | Unit Test                        |
| GG-SCN-001         | Validation/Unit Test             |
| GG-SCN-005         | Validation Test                  |
| GG-REPLAY-001      | Replay-Diff Test                 |
| GG-REPLAY-003      | Replay-Diff Test                 |
| GG-FAULT-001       | Integration Test                 |
| GG-FAULT-005       | Integration Test                 |
| GG-AGENT-001       | Unit Test                        |
| GG-AGENT-004       | Integration Test                 |
| GG-API-001         | API Contract Test                |
| GG-API-002         | API Contract Test                |
| GG-API-003         | API Contract Test                |
| GG-API-004         | API Contract Test                |
| GG-MQTT-001        | Integration Test                 |
| GG-MODB-001        | Integration Test                 |
| GG-OPCUA-001       | Integration Test                 |
| GG-DNP3-001        | Integration Test                 |
| GG-IEC-001         | Integration Test                 |
| GG-UI-001          | E2E Test                         |
| GG-UI-005          | E2E Test                         |
| GG-PERSIST-001     | Persistence Test                 |
| GG-PERSIST-006     | Persistence/Retention Test       |
| GG-OTEL-001        | Telemetrie Test                  |
| GG-OTEL-002        | Telemetrie Test                  |
| GG-SAFE-001        | Security Test                    |
| GG-SAFE-004        | Security Test                    |
| GG-ARCH-001        | Architekturtest                  |
| GG-ARCH-005        | Architekturtest                  |
| GG-CICD-001        | CI/CD Verification               |
| GG-DEPLOY-001      | Container Test                   |
| GG-DEMO-001        | E2E Test                         |
| GG-ACCEPT-001      | Acceptance/Documentation Test    |
| GG-TRACE-001       | Documentation Test (Self-Verification — Existenz und Pflege der drei Trace-Tabellen, Folgearbeit: `make docs-check` (d-check)) |

---
