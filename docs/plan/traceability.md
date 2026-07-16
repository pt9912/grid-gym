# Rueckverfolgbarkeit (V-Modell) — grid-gym

> Ausgelagert aus `spec/lastenheft.md` §27 (Slice 063), damit der Vertrag
> (`lastenheft.md`) frei von Abwaerts-Verweisen bleibt. Dieses Dokument
> erfuellt die `GG-TRACE-001`-Anforderung. Die `27.x`-Abschnittsnummern
> sind zur Referenz-Kontinuitaet mit bestehenden Verweisen beibehalten.


Dieses Dokument fuehrt die **kuratierten, stabilen** Zuordnungen jeder
Lastenheft-Anforderung zu ihrem Design- und Testartefakt. Die zwei Tabellen
werden mit dem Projektfortschritt gepflegt:

- Die Design-Tabelle (§27.1) ist eine gegen `spec/architecture.md` **kuratierte,
  gegroundete Vorwaerts-Zuordnung** (Anforderung → implementierende `GG-AR-*`-Artefakte)
  — **kein** vollstaendiger Spiegel der `Bezug`-Rueckkanten (die Formen unterscheiden
  sich legitim). Die maschinelle Ableitung + formale Set-Konsistenz gegen die
  Bezug-Kanten (`derived`-Endzustand) ist vertagt
  ([Trigger 088](planning/open/088-27-1-consistency-gate-generator.md), d-check-Feature).
- Die Test-Tabelle (§27.3) ist aus dem Lastenheft ableitbar (Testtyp gemaess
  `GG-TESTTYPE-001..007`).

Die **Liefer-/Implementierungs-Rueckverfolgung** (Anforderung→Slice/Welle/ADR
inkl. Abdeckungs- und Waisen-Status) wird **nicht mehr hier handgepflegt** —
die frueher drift-anfaellige §27.2-Tabelle inkl. `✓`/`🔲`-Status wurde in
Slice 066 entfernt (`GG-TRACE-001`-Amendment). Diese Rueckverfolgung wird jetzt
per `make doc-trace` automatisch aus den Slice-, Wellen- und ADR-Artefakten
abgeleitet (d-check `trace`; kein Handpflege-Artefakt, kein Drift). Die
Meilensteine `M1..Mn` leben in
[`docs/plan/planning/in-progress/roadmap.md`](planning/in-progress/roadmap.md).

> **Wichtig — `make doc-trace` ist advisory und in _beide_ Richtungen unscharf:**
> 1. **`orphans=0` ≠ „alles geliefert".** Ein Requirement ist non-orphan, sobald es
>    hier design-/test-gemappt ist (§27.1/§27.3) — die `Coverage`-Spalte bezeugt
>    **Design-Zuordnung, nicht Implementierung**.
> 2. **Leere `Slices`-Spalte ≠ „ungebaut".** Die M-Wellen-Docs nennen nicht jede
>    Einzel-ID. Beispiel: `GG-FAULT-001..010` sind alle als **eine gebaute Suite**
>    geliefert (`src/…/core/faults`, M3), aber nur `GG-FAULT-001` ist in den Wellen-
>    Docs namentlich verankert → nur es traegt Slice-Links; `002..010` erscheinen
>    link-los, obwohl gebaut. Die `Slices`-Spalte spiegelt „welche ID ein Autor in ein
>    Slice-/Wellen-Doc getippt hat", nicht Lieferung.
>
> Der **belastbare Liefer-Status steht im Code / in den Tests**, nicht in dieser
> advisory-RTM. Weder die Waisen-Zahl noch die `Slices`-Spalte sind dafuer autoritativ.

---

## 27.1 Anforderung zu Design

Design-Artefakte beziehen sich auf [`spec/architecture.md`](../../spec/architecture.md);
`GG-AR-*`-Kennungen sind dort definiert: Prinzipien `GG-AR-P-*`, Ports
`GG-AR-PORT-DRV-*` / `GG-AR-PORT-DRN-*`, Komponenten `GG-AR-COMP-*`,
Architektur-Tabus `GG-AR-TABU-*`. (Offene architektonische Punkte `GG-AR-OPEN-*`
sind seit der §19-Aufloesung nicht mehr in `architecture.md`, sondern in der
Planung [offen] bzw. im ADR-Index [geschlossen].)
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
| GG-ARCH-006        | [`GG-AR-COMP-CORE`](../../spec/architecture.md#5-komponentensicht) + [`GG-AR-COMP-SCHED`](../../spec/architecture.md#5-komponentensicht) Tie-Breaking + [`GG-AR-P-008`](../../spec/architecture.md#2-architekturprinzipien) Determinismus-Invariante                          |
| GG-ARCH-007        | [`GG-AR-COMP-CORE`](../../spec/architecture.md#5-komponentensicht) + [`GG-AR-P-006`](../../spec/architecture.md#2-architekturprinzipien) + [`GG-AR-PORT-DRN-001`](../../spec/architecture.md#driven-ports-vom-kern-aufgerufen) (`ClockPort`) + [`GG-AR-TABU-005`](../../spec/architecture.md#architektur-tabus-build-architekturtest)                                              |
| GG-ARCH-008        | [`GG-AR-COMP-CORE`](../../spec/architecture.md#5-komponentensicht) + [`GG-AR-P-007`](../../spec/architecture.md#2-architekturprinzipien) Live- und Replay-Tick-Loop geteilt                                                  |
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
| GG-SCN-001..005, 007, 008    | [`GG-AR-COMP-SCENARIO`](../../spec/architecture.md#5-komponentensicht) Validierungs-Pipeline |
| GG-SCN-006         | [`GG-AR-COMP-SCENARIO`](../../spec/architecture.md#5-komponentensicht) (Fault-Validierung vor Tick) + [`GG-AR-COMP-FAULTS`](../../spec/architecture.md#5-komponentensicht) (Fault-Injection-Ausführung) |
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
| GG-CICD-001..007   | [`GG-AR-TEST-001`](../../spec/architecture.md#17-testarchitektur) + [`GG-AR-COMP-DEPLOY`](../../spec/architecture.md#5-komponentensicht)                                                              |
| GG-DEPLOY-001..011 | [`GG-AR-COMP-DEPLOY`](../../spec/architecture.md#5-komponentensicht) |
| GG-DEMO-001..008   | [`GG-AR-COMP-DEPLOY`](../../spec/architecture.md#5-komponentensicht) (Compose-Demo) + [`GG-AR-TEST-001`](../../spec/architecture.md#17-testarchitektur) (E2E/Demo-Abnahme)                            |
| GG-ACCEPT-001..003 | [`GG-AR-TEST-001`](../../spec/architecture.md#17-testarchitektur) + `GG-TRACE-001`                                                                   |
| GG-TRACE-001       | Rueckverfolgbarkeitstabelle in `architecture.md` (§18) — Quelle fuer diese §27.1-Tabelle             |
| GG-TEST-001..008   | [`GG-AR-TEST-001`](../../spec/architecture.md#17-testarchitektur) (Replay-/Fault-/Determinismus-Tests)                                               |

### 27.1.1 Anforderungen ohne Design-Artefakt

Die folgenden Anforderungsfamilien sind **Scope-, Definitions- oder
Zukunftsanforderungen** und mappen bewusst auf kein
Design-Artefakt in `architecture.md`:

| Lastenheft-Kennung      | Begruendung                                                       |
| ----------------------- | ----------------------------------------------------------------- |
| GG-TERM-001..006        | n/a — normative Begriffsdefinition (Vokabular `MUSS`/`DARF NICHT`/`SOLLTE`/`KANN`) |
| GG-MVP-001..004         | n/a — Scope-Festlegung; Auspraegung lebt in einzelnen `GG-SIM/DEV/...`-IDs |
| GG-NONGOAL-001..005     | n/a — explizite Scope-Grenzen (negativ definierte Anforderung)     |
| GG-FUTURE-001..006      | n/a — `KANN`-Zukunftsanforderungen `GG-FUTURE-*`; Design folgt erst bei Aktivierung im Abnahmescope |

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
| GG-FAULT-002       | Unit Test                        |
| GG-FAULT-003       | Unit Test                        |
| GG-FAULT-004       | Unit Test                        |
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
| GG-TRACE-001       | Documentation Test (Self-Verification — Existenz und Pflege der zwei kuratierten Trace-Tabellen §27.1/§27.3 + der `make doc-trace`-Liefer-Rueckverfolgung, Folgearbeit: `make docs-check` (d-check)) |

---
