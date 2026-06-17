# ADR 0002 — Sprach- und Build-Stack

**Status:** Accepted
**Datum:** 2026-05-14
**Status geaendert am:** 2026-05-15 — `Provisional → Accepted`.
Spike-0 abgeschlossen: alle vier Pflicht-Gates (`make lint`,
`make arch-check`, `make typecheck`, `make test-unit`) gruen auf
`main`; 18 von 18 Contract-Verstoss-Verifikationen geliefert (siehe
`docs/plan/planning/done/spike-0-results.md §3`); zweiter
Pre-Acceptance-Review abgearbeitet (Blocker B-A/B-B/B-C, alle zehn
Drift-Items D-1..D-10 eingearbeitet); `make gates` als
Abschluss-Aggregator gruen. Schliesst [`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte). Vorher:
2026-05-14 — `Proposed → Provisional` mit Freigabe des
Spike-0-Vertrags; Operative Artefakte (`Dockerfile`, `Makefile`)
lagen als Spike-0-Pfad vor (vgl. `ADR 0006`).
**Letzte inhaltliche Aenderung:** 2026-05-15 — Pre-Acceptance-Schliff
nach dem zweiten Review (`ADR 0006` §3): AC-HEXAGON-PURE als 16.
Contract in §A-1 aufgenommen (Whitelist-basiert); §A-1
„fuenfzehn" → „sechzehn" an sechs Stellen synchronisiert;
AC-NO-IO-MOD aufgeteilt nach import-linter (Top-Level) /
`tools/arch_check.py` (Subpakete `urllib.request`/`http.client`/
`logging.handlers`); AC-DOMAIN-FROZEN um `slots=True`-Pflicht und
`FrozenModel`-`ast.Attribute`-Akzeptanz praezisiert (nur Top-Level-
Klassen via `tree.body`); AC-TYPED-ERRORS um Tuple-Form
`except (Exception, ...):` und Attribute-Form
`raise builtins.Exception(...)` / `except mod.Exception:` erweitert;
`[tool.importlinter] include_external_packages = true` als
Pflicht-Konfiguration in den operativen Anforderungen verankert;
§6.1 CI-Matrix-Aussage abgeschwaecht (heute Override via
`make ... PYTHON_VERSION=3.13`, GitHub-Actions-Workflow folgt nach
M1); §A-2 Custom-Emitter-Snippet auf heutigen Stand gebracht
(typisierte Fehlerklassen, `seen`-Zyklusabwehr,
`SurrogateNotAllowedError`, Signed-Zero-Normalisierung,
RFC-8259-Doku); Alternativ-Encoder-Vertrag um Cycle-Detection /
Surrogate-Rejection / Signed-Zero verschaerft. Inhaltlich vorher:
2026-05-15 — Repository-Layout und A-1-Contracts an
`hexagon/`-Gruppierung ausgerichtet (Trigger 011). 2026-05-14 —
A-2 Custom-Emitter eingefuehrt; Lifecycle-Sprache an ADR 0006
angepasst; `mypy --strict` als vierter Spike-0-Gate verankert.
**Bezug:** [Lastenheft](../../../spec/lastenheft.md),
[Architektur](../../../spec/architecture.md),
[ADR 0001](0001-documentation-and-planning-structure.md),
[ADR 0006](0006-adr-lifecycle-superseding-and-process-corrections.md) (Statuswerte und Uebergaenge),
[ADR 0005](0005-type-check-gate.md) (Type-Check als vierter Gate)
**Schliesst (bei Annahme):**
[`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte)

---

## 1. Kontext

Die Architektur (`spec/architecture.md`) ist sprachunabhaengig
formuliert; die Modulgrenzen (`core/`, `ports/`, `adapters/`, `ui/`)
sind durch Dependency Rule und Architektur-Tabus festgelegt
([`GG-AR-TABU-001`](../../../spec/architecture.md#architektur-tabus-build-architekturtest)..008). Diese Entscheidung legt fest, in welcher
Sprache, mit welchem Build-Stack und mit welchen Querschnittsbibliotheken
der Simulationskern und die Driving-Adapter geliefert werden.

Sie betrifft **nicht** das Web-UI (`ui/`); dessen Stack wird in einer
spaeteren ADR adressiert (vgl. [`GG-AR-OPEN-007`](../../../spec/architecture.md#19-offene-architektonische-punkte)).

---

## 2. Bewertungskriterien

Abgeleitet aus dem Lastenheft. Gewichtung: P0 (Knock-out) > P1 > P2.

| Kennung   | Kriterium                                                                       | Bezug                                          | Gewicht |
| --------- | ------------------------------------------------------------------------------- | ---------------------------------------------- | ------- |
| K-DET     | Determinismus per Default; Tie-Breaking, kanonische Serialisierung machbar      | [`GG-SIM-001`](../../../spec/lastenheft.md#gg-sim-001)..004, [`GG-ARCH-006`](../../../spec/lastenheft.md#gg-arch-006), [`GG-DATA-005`](../../../spec/lastenheft.md#gg-data-005)      | P0      |
| K-REPRO   | Reproduzierbare Builds (Lockfiles, Container)                                   | [`GG-DEPLOY-002`](../../../spec/lastenheft.md#gg-deploy-002), [`GG-CICD-001`](../../../spec/lastenheft.md#gg-cicd-001)                     | P0      |
| K-TICK    | Tick-Dauer 100ms/1s zuverlaessig; 10ms als Diagnosemodus laufbar                 | [`GG-RT-001`](../../../spec/lastenheft.md#gg-rt-001), [`GG-RT-004`](../../../spec/lastenheft.md#gg-rt-004)/005                       | P0      |
| K-ARCH    | Architekturtest-Tooling fuer Modulgrenzen und Tabus verfuegbar                  | [`GG-ARCHTEST-001`](../../../spec/lastenheft.md#gg-archtest-001)..005, [`GG-AR-TABU-001`](../../../spec/architecture.md#4-architekturstruktur)..008      | P0      |
| K-OAS     | OpenAPI-Generierung oder -Validierung; WebSocket-Vertraege testbar              | [`GG-API-003`](../../../spec/lastenheft.md#gg-api-003), [`GG-TESTTYPE-004`](../../../spec/lastenheft.md#gg-testtype-004)                    | P1      |
| K-DB      | Stabile PostgreSQL-Treiber + Migrationswerkzeug; Timescale/Influx-Adapter moeglich | [`GG-PERSIST-001`](../../../spec/lastenheft.md#gg-persist-001)..009                           | P1      |
| K-OBS     | Strukturierte Logs, Metriken, OpenTelemetry-Exporter                            | [`GG-OTEL-001`](../../../spec/lastenheft.md#gg-otel-001)..004                               | P1      |
| K-TEST    | Unit/Integration/Architekturtest-Stack reif; Coverage-Reports                   | [`GG-TESTTYPE-001`](../../../spec/lastenheft.md#gg-testtype-001)..007, [`GG-COV-001`](../../../spec/lastenheft.md#gg-cov-001)..005          | P1      |
| K-CONTAIN | Container-Image klein und reproduzierbar; offline-faehig                        | [`GG-DEPLOY-001`](../../../spec/lastenheft.md#gg-deploy-001)/002/011                          | P1      |
| K-ECO     | Energie-/Power-Flow-Domaene: Bibliotheken oder Bindings verfuegbar               | [`GG-GRID-001`](../../../spec/lastenheft.md#gg-grid-001)/002/007, `GG-FUTURE-*` (MPC/RL)      | P2      |
| K-DEV     | Entwicklungs-Velocity; Hexagonal-Idiome; Team-Erfahrung                          | (Projekt-extern)                               | P2      |

---

## 3. Optionen

Jede Option wird gegen die Kriterien bewertet (`+` gut, `o` neutral,
`-` schlecht / Risiko, `??` projektabhaengig).

### Option A: Python 3.13+ mit FastAPI + Pydantic + uv

Versions-Anker (Stand 2026-05-14, gemaess [python.org status](https://devguide.python.org/versions/)):

- Python 3.12 ist im Security-Only-Modus (kein Bugfix mehr). Nicht
  als Minimum waehlen, weil EOL 2028-10 schon naeher rueckt.
- Python 3.13 ist Bugfix-Release (EOL 2029-10) — Minimum-Floor fuer
  Production.
- Python 3.14 ist Bugfix-Release (Erstrelease 2025-10-07, EOL 2030-10)
  — empfohlene Referenz-Runtime fuer Container-Image und Reference-
  Benchmarks. CI testet beide Versionen.
- Python 3.15 ist Prerelease, kein Production-Ziel; spaetere Aufnahme
  in die CI-Matrix als Folgearbeit.

| Kriterium  | Bewertung | Bemerkung                                                                                     |
| ---------- | --------- | --------------------------------------------------------------------------------------------- |
| K-DET      | o         | Dict-Iteration seit 3.7 stabil; Sortierung ist stabil; GC nicht-deterministisch — irrelevant fuer fachliche Outputs solange `RandomPort` gebondet ist. Floating-Point ist plattformabhaengig — gleiche `decimal`/`fractions` einsetzbar. |
| K-REPRO    | +         | `uv.lock`/`poetry.lock` reproduzierbar.                                                       |
| K-TICK     | o         | 100ms/1s problemlos. 10ms bei 100 Geraeten knapp; CPython-GIL limitiert Parallelitaet im Tick. |
| K-ARCH     | -         | Schwaechstes Glied: kein etabliertes „NetArchTest"-Pendant. Workarounds: `import-linter`, eigener AST-Walker. |
| K-OAS      | +         | FastAPI generiert OpenAPI; `pydantic` validiert.                                              |
| K-DB       | +         | `psycopg`, `asyncpg`, `alembic` ausgereift; Timescale/Influx-Clients verfuegbar.              |
| K-OBS      | +         | `structlog`, `prometheus-client`, `opentelemetry-python` reif.                                |
| K-TEST     | +         | `pytest`, `pytest-cov`, `hypothesis` (property-based).                                        |
| K-CONTAIN  | o         | `python:3.14-slim` als Basis ~125 MB; mit MVP-Stack (FastAPI, pydantic, psycopg, alembic, structlog, opentelemetry) realistisch 250–400 MB. Mit `pandapower`/`pypsa`/`scipy`/ML weitere ~600–900 MB. Imagegroesse wird als CI-Messpunkt gefuehrt; offline-faehig ist sie unabhaengig davon. |
| K-ECO      | ++        | Mit Abstand staerkstes Energie-Oekosystem fuer SOLLTE-/Folgearbeit: `pandapower`/`pypsa`/`OpenDSS`-Bindings adressieren [`GG-GRID-002`](../../../spec/lastenheft.md#gg-grid-002) (Power-Flow-Adapter), [`GG-GRID-005`](../../../spec/lastenheft.md#gg-grid-005)..007 (Inselnetz/Trafo/Blindleistung), [`GG-FUTURE-003`](../../../spec/lastenheft.md#gg-future-003). ML/RL fuer [`GG-FUTURE-001`](../../../spec/lastenheft.md#gg-future-001)/002 zusaetzlich. |
| K-DEV      | +         | Hoher Output, Hexagonal idiomatisch ueber Protokolle + DI.                                     |

**Hauptrisiko:** K-ARCH (Architekturtests) und K-TICK bei 10ms.

### Option B: Go 1.22+ mit Echo/Chi + sqlc + Goose

| Kriterium  | Bewertung | Bemerkung                                                                                     |
| ---------- | --------- | --------------------------------------------------------------------------------------------- |
| K-DET      | +         | Map-Iteration ist randomisiert (Sprachvorgabe!) — muss bewusst ueber Slices+Sort geloest werden, dann sehr deterministisch. |
| K-REPRO    | +         | `go.sum` reproduzierbar, Single-Binary.                                                        |
| K-TICK     | ++        | GC sehr schnell (< 1ms typisch), goroutine pro Geraet machbar, 10ms realistisch.              |
| K-ARCH     | o         | `go-arch-lint`, eigene Importtests; weniger reif als NetArchTest.                              |
| K-OAS      | o         | `oapi-codegen` reif; WebSocket-Vertraege manuell.                                              |
| K-DB       | +         | `pgx`, `sqlc`, `goose` ausgereift; Timescale ist Postgres-kompatibel.                          |
| K-OBS      | +         | `slog`, `otelgo`, `prometheus` reif.                                                            |
| K-TEST     | o         | `go test` reif; Coverage einfach; weniger ergonomisches Test-DSL als pytest/JUnit.            |
| K-CONTAIN  | ++        | Single-Binary, scratch-Image moeglich; < 30 MB.                                                |
| K-ECO      | -         | Sehr wenig Energie-Oekosystem; alles selbst.                                                   |
| K-DEV      | o         | Boilerplate fuer Domain-Modelle; Generics seit 1.18 helfen, aber kein `sealed`-Pendant.        |

**Hauptrisiko:** K-ECO (Energiedomaene) und Modell-Boilerplate.

### Option C: Rust (stable) mit Axum + sqlx + sqlx-cli

| Kriterium  | Bewertung | Bemerkung                                                                                     |
| ---------- | --------- | --------------------------------------------------------------------------------------------- |
| K-DET      | ++        | Kein GC, kein Hidden-Allocation-Jitter, starke Typgarantien fuer Sequenzierung.                |
| K-REPRO    | ++        | `Cargo.lock` reproduzierbar; deterministische Builds mit `RUSTFLAGS=...`.                      |
| K-TICK     | ++        | 10ms machbar; geringste Jitter-Risiken aller Optionen.                                         |
| K-ARCH     | -         | Sehr wenig Tooling fuer Architekturregeln auf Modulebene; eigene Crate-Boundaries der Mainline-Hebel. |
| K-OAS      | -         | `utoipa` reift; weniger ergonomisch als FastAPI/Spring-Tooling.                                |
| K-DB       | +         | `sqlx` reif (compile-time-checked queries); Timescale ueber Postgres.                          |
| K-OBS      | +         | `tracing`, `opentelemetry`-Crates reif.                                                        |
| K-TEST     | o         | Reife Unit-Tests; Integration mit Test-DB ergonomisch ueber `testcontainers`.                  |
| K-CONTAIN  | ++        | Sehr klein, scratch-faehig.                                                                    |
| K-ECO      | --        | Praktisch null Energie-Oekosystem im Open-Source; ML/RL ueber FFI moeglich, aber umstaendlich.  |
| K-DEV      | -         | Steilste Lernkurve; langsamere Iteration; hoechste Code-Komplexitaet pro Feature.              |

**Hauptrisiko:** K-DEV (Tempo) und K-ECO; lohnt sich nur bei harten Performance-/Determinismus-Anforderungen, die in `grid-gym` MVP-seitig nicht zwingend sind.

### Option D: Kotlin 2.x auf JVM 21 mit Ktor + jOOQ/Exposed + Gradle Multi-Module

| Kriterium  | Bewertung | Bemerkung                                                                                     |
| ---------- | --------- | --------------------------------------------------------------------------------------------- |
| K-DET      | +         | JVM ist gut beherrschbar; ZGC/Generational ZGC mit < 1ms Pausen praxistauglich; Floating-Point IEEE-754-konform. |
| K-REPRO    | +         | Gradle + version catalog + lockfiles.                                                          |
| K-TICK     | +         | 100ms/1s einfach; 10ms machbar mit ZGC, aber JIT-Warmup zu beachten.                          |
| K-ARCH     | ++        | `ArchUnit` ist Goldstandard fuer Architekturtests (Modulgrenzen, Tabus, zyklenfrei).           |
| K-OAS      | +         | OpenAPI Generator reif; `kotlinx.serialization` deterministisch.                               |
| K-DB       | +         | `jOOQ`, `Exposed`, Flyway/Liquibase reif; Timescale/Influx-Treiber verfuegbar.                 |
| K-OBS      | +         | Micrometer, OpenTelemetry-Java-Agent, structured-logging-Setups vorhanden.                     |
| K-TEST     | ++        | JUnit5 + Kotest + Testcontainers; sehr starkes Test-Oekosystem.                                |
| K-CONTAIN  | o         | Mit GraalVM Native Image klein (< 80 MB); ohne grosser (> 200 MB JRE).                          |
| K-ECO      | o         | Wenig Energie-Oekosystem, aber gute Java-Bindings (`OpenDSS`, JADE fuer Multi-Agent).          |
| K-DEV      | ++        | Starkes Hexagonal-Idiom (sealed classes, value classes, Result-Typen); Gradle-Multi-Module passt 1:1 zum geplanten Layout. |

**Hauptrisiko:** K-CONTAIN ohne Native Image; K-DEV bei Native-Image-Toolchain.

### Option E: C# / .NET 9 mit ASP.NET Minimal APIs + EF Core/Dapper + DbUp

| Kriterium  | Bewertung | Bemerkung                                                                                     |
| ---------- | --------- | --------------------------------------------------------------------------------------------- |
| K-DET      | +         | Modernes .NET-GC mit Server-GC < 1ms typisch.                                                  |
| K-REPRO    | +         | `packages.lock.json`, deterministische Builds.                                                 |
| K-TICK     | +         | 100ms/1s einfach; 10ms machbar mit AOT.                                                        |
| K-ARCH     | ++        | `NetArchTest` (in bess-ems im Einsatz, `AR-OPEN-009` geschlossen) — vermutlich identischer Stack. |
| K-OAS      | +         | `Microsoft.OpenApi`, `Swashbuckle`.                                                            |
| K-DB       | +         | `Npgsql`, `Dapper`, `DbUp` (analog bess-ems).                                                  |
| K-OBS      | +         | `OpenTelemetry .NET`, `Serilog`.                                                                |
| K-TEST     | +         | xUnit/NUnit + Testcontainers.NET.                                                              |
| K-CONTAIN  | o         | Mit Native AOT klein; ohne 100–200 MB.                                                          |
| K-ECO      | -         | Sehr wenig Energie-Oekosystem im Open-Source-Bereich.                                          |
| K-DEV      | +         | Starkes Hexagonal-Idiom, sehr nahe an bess-ems — Risiko: Projekt-Verwechslung mit bess-ems.    |

**Hauptrisiko:** K-ECO und Wahrnehmung „bess-ems-Klon" trotz unterschiedlicher Domaene.

---

## 4. Empfehlung

**Empfohlen: Option A (Python 3.13+, Referenz-Runtime 3.14) mit zwei
harten Auflagen, fallback Option D (Kotlin/JVM mit ArchUnit + ZGC).**

Begruendung (MVP-getrieben — Future-Punkte sind Zusatznutzen, nicht
Entscheidungsgrundlage):

- **Schema- und Szenariovalidierung (MVP).** [`GG-SCN-001`](../../../spec/lastenheft.md#gg-scn-001)/008 verlangt
  YAML-Schema-Validierung vor erstem Tick; [`GG-DATA-001`](../../../spec/lastenheft.md#gg-data-001)..004 verlangt
  ein einheitliches Telemetriemodell mit Wertebereichs- und
  Einheitenpruefung; [`GG-BESS-008`](../../../spec/lastenheft.md#gg-bess-008) Initialparameter-Validierung. Pydantic
  v2 ist hier deutlich vor jedem anderen Option-Stack.
- **OpenAPI als Vertrag (MVP).** [`GG-API-003`](../../../spec/lastenheft.md#gg-api-003) fordert maschinenlesbaren
  Vertrag fuer alle REST-Endpunkte. FastAPI generiert OpenAPI direkt aus
  pydantic-Modellen — Schema und Implementierung koennen nicht
  auseinanderdriften.
- **Determinismus- und Property-basierte Tests (MVP).** [`GG-SIM-001`](../../../spec/lastenheft.md#gg-sim-001)..004
  und [`GG-DATA-005`](../../../spec/lastenheft.md#gg-data-005) sind property-basiert pruefbar. `hypothesis` ist
  hier Industriestandard. Replay-Diff-Klassifikation ([`GG-REPLAY-007`](../../../spec/lastenheft.md#gg-replay-007))
  laesst sich als reine Python-Funktion mit `hypothesis`-Tests umsetzen.
- **MVP-Geraete- und Netzmodelle (MVP).** [`GG-GRID-001`](../../../spec/lastenheft.md#gg-grid-001)..004
  (vereinfachtes Leistungs-/Spannungsmodell) sind ohne externes
  Power-Flow-Tool erreichbar; `numpy` reicht. [`GG-GRID-002`](../../../spec/lastenheft.md#gg-grid-002) erlaubt
  optional einen Power-Flow-Adapter — Python's `pandapower` ist der
  natuerliche Pfad, wenn das aus SOLLTE in MUSS wandert.
- **Persistenz- und Migrationskette (MVP).** `psycopg` 3 (async) und
  `alembic` decken [`GG-PERSIST-001`](../../../spec/lastenheft.md#gg-persist-001)..009 vollstaendig ab; Timescale-
  und Influx-Adapter sind dort produktionsreif.
- **Observability (MVP).** `structlog`, `prometheus-client` und
  `opentelemetry-python` decken [`GG-OTEL-001`](../../../spec/lastenheft.md#gg-otel-001)..004 ohne Eigenbau.
- **Tick-Charakteristik (MVP).** [`GG-RT-001`](../../../spec/lastenheft.md#gg-rt-001) fordert fuer 100ms/1s
  Backpressure-Freiheit und macht 10ms zum Mess-/Diagnosemodus, nicht
  zum Echtzeitpfad. [`GG-RT-004`](../../../spec/lastenheft.md#gg-rt-004)/005 (100 Geraete, 10.000 Tick-Lauf,
  10.000 Punkte/s) ist in CPython 3.13/3.14 ohne C-Extension messbar
  erreichbar; Risiko bleibt, wird aber durch Slice-M1-Benchmark
  geprueft (siehe Fallback-Trigger unten).

Zusatznutzen ueber den MVP hinaus (nicht entscheidungstragend):
ML/RL-Toolchain fuer [`GG-FUTURE-001`](../../../spec/lastenheft.md#gg-future-001)/002, `pandapower`-Integration
fuer [`GG-FUTURE-003`](../../../spec/lastenheft.md#gg-future-003), Co-Simulation-Bindings fuer [`GG-FUTURE-006`](../../../spec/lastenheft.md#gg-future-006).

Schwaechstes Glied bleibt **K-ARCH** (P0): Python hat kein
NetArchTest/ArchUnit-Pendant. Das wird durch eine konkrete und
nachweisbare Auflage A-1 kompensiert (siehe unten). Wird A-1 nicht
erfuellbar, ist Python nicht haltbar.

### Auflagen bei Python-Annahme

A-1 schliesst das K-ARCH-Gate (P0); A-2 schliesst die
Determinismusluecke durch Serialisierung.

**Pflicht-Pfad zur ADR-Annahme (Spike-0 vor `Accepted`):**

K-ARCH ist ein P0-Knock-out-Kriterium, in dem Python die Bewertung
`-` traegt. Solange A-1 nicht nachweislich konfigurierbar ist,
darf diese ADR weder als `Accepted` gefuehrt noch [`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte)
als geschlossen markiert werden. Der Status-Pfad nutzt die in
[ADR 0006](0006-adr-lifecycle-superseding-and-process-corrections.md) definierten Lifecycle-Stufen und
ist hier konkret:

| ADR-Status     | Bedingung                                                                 | Wirkung auf [`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte)         |
| -------------- | ------------------------------------------------------------------------- | ------------------------------------ |
| `Proposed`     | aktueller Stand: Empfehlung samt Auflagen, ohne ausgefuehrten Nachweis    | bleibt offen                          |
| `Provisional`  | Projektowner bestaetigt Empfehlung; Spike-0 ist freigegeben               | bleibt offen, mit Verweis auf ADR    |
| `Accepted`     | Spike-0 ist gruen abgeschlossen (siehe Spike-0-Vertrag unten)              | wird mit „Geschlossen mit ADR 0002" in [`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte) in `architecture.md` markiert |

**Spike-0-Vertrag (Pre-Acceptance):**

Spike-0 ist ein zeitlich begrenztes (Empfehlung: max. 5
Personentage), gegen einen leeren oder minimalen `grid-gym`-Skeleton
ausgefuehrtes Spike-Projekt. Es liefert:

- ein funktionierendes Repository-Skelett (`src/grid_gym/{hexagon/{core,ports},adapters}`),
- alle sechzehn A-1-Contracts konfiguriert
  (`pyproject.toml`, `tests/arch/`, `tools/arch_check.py` inkl.
  `grimp`-SCC-Check),
- die `ruff`-Konfiguration aus Auflage A-1 inklusive der Per-File-Ignores,
- A-2 als kanonische Serialisierungsfunktion (Custom-Emitter, keine
  `json.JSONEncoder`-Subklasse) plus `hypothesis`-Property-Tests,
- die `mypy --strict`-Konfiguration aus
  [ADR 0005](0005-type-check-gate.md) (`[tool.mypy]` in
  `pyproject.toml`) als vierten Gate — ADR 0005 wird gemeinsam mit
  dieser ADR `Accepted`, der Type-Check ist deshalb Teil des
  Spike-0-Pflichtnachweises,
- einen CI-Workflow, der `lint-imports`, `ruff check`,
  `python tools/arch_check.py` und `mypy --strict` als **vier
  Gates** ausfuehrt,
- pro Contract einen bewusst eingefuegten Verstoss in einem
  separaten Branch, der den jeweiligen Gate rot werden laesst.

Spike-0 ist erfolgreich, wenn:

1. alle vier Gates (`lint-imports`, `ruff check`, `arch_check.py`,
   `mypy --strict`) auf `main` (sauberes Skelett) gruen sind,
2. jeder der sechzehn A-1-Verstoss-Branches genau seinen erwarteten
   Gate rot werden laesst und keinen anderen,
3. mindestens ein bewusst herbeigefuehrter LSP-/Protocol-Variance-
   Verstoss im Test-Branch laesst `mypy --strict` rot werden
   (Nachweis fuer das ADR-0005-Gate), und
4. `ruff check --no-cache` erkennt die in dieser ADR gezeigte
   `pyproject.toml`-Konfiguration ohne Warnung — insbesondere
   `[tool.ruff.lint.flake8-tidy-imports]` mit
   `banned-module-level-imports` und `[tool.ruff.lint.flake8-tidy-imports.banned-api]`
   werden vom installierten ruff akzeptiert. Falls eine kuenftige
   ruff-Version diese Schluessel umbenennt, wird die ADR per
   Folge-ADR angepasst, nicht Spike-0 umgangen.

Wird Spike-0 nicht erfolgreich abgeschlossen, ist Python nicht
haltbar; die ADR geht **vor Acceptance** auf `Rejected` (siehe
ADR 0006 Lifecycle-Tabelle: vor-Beschluss-Zustand), eine Folge-ADR
fuer einen anderen Stack tritt an die Stelle. Der Fallback-Trigger
„A-1 nicht erfuellbar" weiter unten beschreibt denselben Fall.

**Slice-M1-Abnahme (nach Acceptance):**

Sobald die ADR `Accepted` ist, sind A-1 und A-2 nicht nur
konfiguriert, sondern werden im Hauptprojekt fortlaufend gegen
echten Code gepflegt. Slice-M1-Abnahme verlangt zusaetzlich, dass
die ersten Domain- und Adapter-Module die Contracts ohne
Ausnahmen erfuellen.

#### A-1 — Architekturtests verbindlich automatisiert

`import-linter` allein deckt nur Import- und Zyklusregeln; mehrere
Tabus aus die Modulgrenzen-Vertraege [`GG-AR-TABU-001`](../../../spec/architecture.md#architektur-tabus-build-architekturtest)..008 in `architecture.md` sind Aufruf-, Immutability- oder
Fehlerstilregeln und brauchen eine **AST-basierte** Pruefung. A-1
ist deshalb eine Drei-Tool-Suite, deren CI-Job nur dann gruen ist,
wenn alle drei Tools sauber laufen.

Tool-Suite (Pflicht), mit ehrlicher Rollenverteilung:

| Tool                              | Rolle                                                                                                |
| --------------------------------- | ---------------------------------------------------------------------------------------------------- |
| `import-linter`                   | Modul- und Layer-Importgrenzen (`forbidden`-Contracts).                                              |
| `ruff` (Regelgruppen `BLE`, `TRY`, `DTZ`, `S`, `TID`, `B904` + `flake8-tidy-imports.banned-api`/`banned-module-level-imports`) | (a) Datetime-tz-Verstoesse (`DTZ`), (b) Blind-Except und try/except-Anti-Patterns (`BLE`, `TRY`, `B904`), (c) Banned-Imports (`random`, `secrets`, `numpy.random`) auf Modulebene in `hexagon/core/*` ueber `flake8-tidy-imports.banned-module-level-imports`, (d) Banned-API-Aufrufe (`datetime.datetime.utcnow`) ueber `flake8-tidy-imports.banned-api`, (e) Test-Security-Subset (`S`). **Nicht** durch ruff abgedeckt: `time.time`, `time.monotonic`, `asyncio.get_event_loop().time`, Aufrufe wie `random.random()` nach einem Re-Export — diese laufen ueber `tools/arch_check.py`. |
| `tools/arch_check.py` (eigenes AST-Skript) | (a) Zykluscheck (SCC via `grimp`), (b) Zeitfunktions-Calls in `hexagon/core/*` (`time.time`, `time.monotonic`, `asyncio.get_event_loop().time`, transitive Re-Exports), (c) Zufallsfunktions-Calls in `hexagon/core/*` (Aufruf-Site, nicht nur Import), (d) `json.dumps`/`json.dump`-Aufrufe ausserhalb der Whitelist, (e) Immutability fuer `hexagon.core.domain.*`, (f) God-Utility-Modul-/Klassenmuster, (g) `GridGymError`-Vererbung fuer Domain-/Application-Exceptions. |

Konfiguration und Contracts liegen versioniert unter `tests/arch/`
und `pyproject.toml`. Die Contracts sind:

| Contract-ID         | Tool          | Inhalt | Bezug |
| ------------------- | ------------- | ------ | ----- |
| AC-HEXAGON-PURE     | `tools/arch_check.py` (AST, Whitelist) | Module unter `src/grid_gym/hexagon/**` duerfen NUR stdlib (via `sys.stdlib_module_names`), `grid_gym.*` und explizit whitelistete Dritt-Pakete (`[tool.grid_gym.arch_check] hexagon-import-whitelist`, z. B. `pydantic` fuer `FrozenModel`) importieren. Ersetzt die brueckhafte Blacklist-Pflege in `AC-NO-FW`/`AC-PORTS-NO-FW` durch eine robuste Positive-Liste — neue Dritt-Pakete sind by-default verboten, bis sie ADR-fundiert whitelistet werden. | [`GG-AR-TABU-002`](../../../spec/architecture.md#architektur-tabus-build-architekturtest), [`GG-CC-003`](../../../spec/lastenheft.md#gg-cc-003) |
| AC-CORE-NO-ADAPTERS | import-linter `forbidden` | `hexagon.core.*` darf NICHT `adapters.*` importieren. | [`GG-AR-TABU-001`](../../../spec/architecture.md#4-architekturstruktur), [`GG-ARCH-003`](../../../spec/lastenheft.md#gg-arch-003) |
| AC-CORE-NO-DRIVING  | import-linter `forbidden` | `hexagon.core.*` darf NICHT `hexagon.ports.driving.*` importieren (Driving-Ports werden vom Kern angeboten, nicht aufgerufen). | [`GG-AR-TABU-001`](../../../spec/architecture.md#4-architekturstruktur) |
| AC-PORTS-NO-OUT     | import-linter `forbidden` | `hexagon.ports.*` darf NICHT `adapters.*` UND NICHT `hexagon.core.simulation`, `hexagon.core.devices`, `hexagon.core.scenario`, `hexagon.core.replay`, `hexagon.core.faults`, `hexagon.core.agents` importieren — Ports kennen nur `hexagon.core.domain`. | [`GG-AR-TABU-001`](../../../spec/architecture.md#4-architekturstruktur) |
| AC-PORTS-NO-FW      | import-linter `forbidden` | `hexagon.ports.*` darf KEINE Web-, Persistenz-, Messaging-, Datenbank- oder UI-Frameworks importieren: dieselbe Verbotsliste wie `AC-NO-FW`, ergaenzt um stdlib-IO (`socket`, `pathlib`, `logging.handlers`, `urllib.request`, `http.client`). | [`GG-ARCHTEST-004`](../../../spec/lastenheft.md#gg-archtest-004) |
| AC-ADAPTER-PURE     | import-linter `forbidden` | `adapters.*` darf NICHT `hexagon.core.simulation`, `hexagon.core.devices`, `hexagon.core.scenario`, `hexagon.core.replay`, `hexagon.core.faults`, `hexagon.core.agents` importieren — Adapter sehen nur `hexagon.core.domain` und `hexagon.ports.*`. **Reichweite: Import-Grenze** (siehe `AC-ADAPTER-LIGHTWEIGHT` fuer die Logik-Reichweite). | [`GG-AR-TABU-003`](../../../spec/architecture.md#architektur-tabus-build-architekturtest), [`GG-CC-002`](../../../spec/lastenheft.md#gg-cc-002) |
| AC-ADAPTER-LIGHTWEIGHT | `tools/arch_check.py` (AST, heuristisch) | Module unter `adapters.driven.protocol_*`, `adapters.driven.persistence_*` und `adapters.driving.*` MUESSEN strukturell schlank bleiben: pro Modul max. eine zyklomatische Komplexitaet von 8 je Funktion, keine `if/elif`-Ketten ueber Domain-Enums (`Quality`, `CommandResult`), keine arithmetischen Operationen ueber Telemetriewerten (`+`, `-`, `*`, `/` auf Feldern von `TelemetryPoint`/`Command`). Heuristisch, **kein vollstaendiger Nachweis** — siehe Reststeuerung unter Code-Review. | [`GG-AR-TABU-003`](../../../spec/architecture.md#architektur-tabus-build-architekturtest) (heuristischer Anteil), [`GG-CC-002`](../../../spec/lastenheft.md#gg-cc-002) |
| AC-NO-FW            | import-linter `forbidden` | `hexagon.core.*` darf KEINE Module aus `fastapi`, `uvicorn`, `psycopg`, `sqlalchemy`, `alembic`, `httpx`, `paho.mqtt`, `pymodbus`, `asyncua` u. ae. importieren. | [`GG-AR-TABU-002`](../../../spec/architecture.md#architektur-tabus-build-architekturtest), [`GG-CC-003`](../../../spec/lastenheft.md#gg-cc-003) |
| AC-NO-IO-MOD        | **Aufgeteilt:** import-linter `forbidden` deckt Top-Level-Module (`socket`, `pathlib`). `tools/arch_check.py` (`_check_no_io_mod_nested`, AST) deckt stdlib-Subpakete, die import-linter strukturell nicht in `forbidden_modules` aufnehmen kann (Subpakete externer Pakete sind dort nicht erlaubt): `urllib.request`, `http.client`, `logging.handlers`. | `hexagon.core.*` darf KEINE dieser Module importieren (rein zur Typannotation ueber `TYPE_CHECKING` erlaubt). | [`GG-AR-TABU-002`](../../../spec/architecture.md#architektur-tabus-build-architekturtest) |
| AC-NO-CYCLES        | `tools/arch_check.py` (Graph-Analyse via `grimp`) | Keine zyklischen Importpfade. Pruefung: `grimp.build_graph("grid_gym")`, dann Strongly-Connected-Components der Modul-Import-Kanten — jede SCC mit > 1 Knoten ist ein Verstoss. Bewusst **kein** `import-linter`-`independence`-Contract: `independence` verbietet jeden gegenseitigen Import (auch erlaubte Richtungen wie `adapters → ports`) und ist kein Zykluscheck. | [`GG-AR-TABU-004`](../../../spec/architecture.md#4-architekturstruktur), [`GG-CC-004`](../../../spec/lastenheft.md#gg-cc-004) |
| AC-NO-TIME          | **Aufgeteilt:** `ruff` deckt `DTZ001`–`DTZ012` (tz-naive `datetime`-Calls) plus `flake8-tidy-imports.banned-api` fuer `datetime.datetime.utcnow`. `tools/arch_check.py` deckt `time.time`, `time.monotonic`, `time.perf_counter`, `time.perf_counter_ns`, `time.process_time`, `asyncio.get_event_loop().time` als Aufrufe in `hexagon.core.*`. | `hexagon.core.*` darf keine Wall-Clock-/Monotonic-Quelle direkt verwenden. Zeit kommt aus `ClockPort`. | [`GG-AR-TABU-005`](../../../spec/architecture.md#architektur-tabus-build-architekturtest), [`GG-ARCH-007`](../../../spec/lastenheft.md#gg-arch-007) |
| AC-NO-RAND          | **Aufgeteilt:** `ruff` `flake8-tidy-imports.banned-module-level-imports` verbietet Module-Level-Imports von `random`, `secrets`, `numpy.random` in `hexagon.core.*`. `tools/arch_check.py` faengt zusaetzlich Aufruf-Sites ab (z. B. nach Re-Export oder lokalem Import). | `hexagon.core.*` darf weder `random.*`, `secrets.*`, `numpy.random.*` noch transitive Re-Exports davon aufrufen. Zufall kommt aus `RandomPort`. | [`GG-SIM-001`](../../../spec/lastenheft.md#gg-sim-001), [`GG-SCN-002`](../../../spec/lastenheft.md#gg-scn-002), [`GG-AR-PORT-DRN-010`](../../../spec/architecture.md#driven-ports-vom-kern-aufgerufen) |
| AC-NO-JSON          | `tools/arch_check.py` (AST) | Produktionscode unter `src/grid_gym/**` darf `json.dumps`/`json.dump` nicht direkt aufrufen, **ausser** in einem einzigen explizit gewhitelisteten Modul: `src/grid_gym/hexagon/core/serialization/canonical.py` — dies ist die Implementierung von `canonical_json` aus A-2 und die einzige erlaubte `json.dumps`-Aufrufstelle. Die Whitelist ist namentlich in `tools/arch_check.py` und in `pyproject.toml` hinterlegt; jede Erweiterung erfordert ADR-Verweis. | [`GG-DATA-005`](../../../spec/lastenheft.md#gg-data-005) |
| AC-DOMAIN-FROZEN    | `tools/arch_check.py` (AST, nur Top-Level-Klassen via `tree.body`) | Klassen in `hexagon.core.domain.*` MUESSEN entweder `@dataclass(frozen=True, slots=True)` sein — **beide** Keywords als `ast.Constant(value=True)` — oder von einer `FrozenModel`-Basisklasse (Pydantic mit `model_config = ConfigDict(frozen=True)`) erben. `FrozenModel` wird als literaler Klassenname erkannt, sowohl als `ast.Name` als auch als `ast.Attribute` (`mod.FrozenModel`); andere Frozen-Konventionen erfordern Re-Alias oder ADR-Erweiterung. Nested/conditional ClassDefs (in `try`/`if`-Bodies oder Funktionen) sind out-of-scope. | [`GG-AR-TABU-006`](../../../spec/architecture.md#architektur-tabus-build-architekturtest), [`GG-CC-007`](../../../spec/lastenheft.md#gg-cc-007) |
| AC-NO-GOD-UTILS     | `tools/arch_check.py` (AST) | Verboten: Modulnamen `*_utils.py`, `helpers.py`, `common.py`, `misc.py`; Klassen, deren Name auf `Utils`/`Helper`/`Manager`/`Misc` endet; statische Module mit > 5 oeffentlichen freien Funktionen ausserhalb `hexagon.core.domain` und `hexagon.core.serialization`. | [`GG-AR-TABU-007`](../../../spec/architecture.md#architektur-tabus-build-architekturtest), [`GG-CC-006`](../../../spec/lastenheft.md#gg-cc-006) |
| AC-TYPED-ERRORS     | ruff `BLE001` + `TRY002`/`TRY003` + `tools/arch_check.py` | Verbot von `raise Exception(...)`/`raise BaseException(...)`, inkl. Attribute-Form (`raise builtins.Exception(...)` / `raise mod.Exception`); `except Exception:` nur in deklarierten Adapter-Boundary-Modulen (siehe `ruff per-file-ignores` unten) erlaubt — inkl. Tuple-Form `except (Exception, ...):` (rekursiv ueber Tuple-Elements) und Attribute-Form `except mod.Exception:`. Alle Domain-/Application-Fehler erben von `hexagon.core.errors.GridGymError`. | [`GG-AR-TABU-008`](../../../spec/architecture.md#architektur-tabus-build-architekturtest), [`GG-CC-008`](../../../spec/lastenheft.md#gg-cc-008) |

Operative Anforderung:

- Im CI laufen drei Jobs: `lint-imports`, `ruff check`, `python tools/arch_check.py`.
  Jeder Job mit Exit-Code != 0 bricht den Build ([`GG-CICD-003`](../../../spec/lastenheft.md#gg-cicd-003), [`GG-QG-001`](../../../spec/lastenheft.md#gg-qg-001),
  [`GG-ARCHTEST-005`](../../../spec/lastenheft.md#gg-archtest-005)).
- `[tool.importlinter]` MUSS `include_external_packages = true` setzen,
  sobald `forbidden_modules` externe Pakete (z. B. `fastapi`, `socket`)
  enthaelt — sonst lehnt `lint-imports` die Top-Level-Konfiguration ab.
  Diese Einstellung ist Pflicht-Bestandteil der A-1-Suite.
- Jeder Verstoss erzeugt eine maschinenlesbare Ausgabe mit
  Contract-ID, betroffenem Modul/Symbol und Verletzungsgrund
  ([`GG-QG-002`](../../../spec/lastenheft.md#gg-qg-002)).
- Hinzufuegen eines neuen Top-Level-Adapter- oder Core-Pakets ohne
  Pflege der Contract-Listen in `pyproject.toml` bricht den Build
  (Whitelist-Pflicht).
- Slice-M1-Abnahmekriterium: alle sechzehn Contracts oben sind
  konfiguriert, alle drei CI-Jobs sind gruen, **und** je Contract
  ist mindestens ein bewusst herbeigefuehrter Verstoss in einem
  Test-Branch als rot nachgewiesen.

#### `ruff`-Konfiguration (Scope und Per-File-Ignores)

`ruff` wird zentral in `pyproject.toml` konfiguriert. Globale Regelgruppen:

```toml
[tool.ruff.lint]
select = [
    # AC-TYPED-ERRORS / GG-CC-008 — Fehlerstil
    "BLE",     # blind-except
    "TRY",     # try/except patterns
    "B904",    # raise-from in except
    "B",       # flake8-bugbear (Design-Bugs: mutable defaults, etc.)
    # AC-NO-TIME / GG-AR-TABU-005
    "DTZ",     # tz-naive datetime calls (Teilabdeckung)
    # Sicherheit
    "S",       # bandit security; subset relevant
    # AC-NO-RAND / GG-AR-TABU-005 (Aufruf-Site ergaenzend in arch_check.py)
    "TID",     # banned imports / banned-api
    # GG-CC-001 — Methoden klein und fokussiert
    "C901",    # mccabe complexity
    "PLR0911", # too-many-return-statements
    "PLR0912", # too-many-branches
    "PLR0913", # too-many-arguments
    "PLR0915", # too-many-statements (max. 30 logische Zeilen)
    "PLR0916", # too-many-boolean-expressions
    "PLR2004", # magic-value-comparison
    # GG-PRINC-002 / GG-PRINC-005 / GG-CC-006 — SRP/ISP-Heuristiken (Klassen-Ebene)
    "PLR0902", # too-many-instance-attributes (SRP-Signal: fette Klassen)
    "PLR0903", # too-few-public-methods (Faux-Klassen / Data-Bag-Verdacht)
    "PLR0904", # too-many-public-methods (SRP/ISP-Signal: zu breite API)
    # GG-CC-005 — sprechende Namen (heuristisch)
    "N",       # pep8-naming (Klassen, Funktionen, Konstanten)
    # Code-Hygiene
    "RET",     # flake8-return (sauberer Kontrollfluss)
    "SIM",     # flake8-simplify (Refaktorisierungs-Hinweise)
    "ARG",     # flake8-unused-arguments (unbenutzte Parameter sind oft Smell)
    "RUF",     # ruff-spezifisch (Async, mutable class attrs etc.)
]

[tool.ruff.lint.mccabe]
# GG-CC-001: Methoden klein und fokussiert. McCabe-Komplexitaet 10 ist
# der etablierte Industrie-Standard fuer „lesbar/testbar".
max-complexity = 10

[tool.ruff.lint.pylint]
# GG-CC-001: max. 30 logische Zeilen pro Methode/Funktion.
# Akzeptanzkriterium aus dem Lastenheft 1:1 abgebildet.
max-statements = 30
max-branches = 12
max-args = 5
max-returns = 6
max-bool-expr = 4
# GG-PRINC-002 / GG-PRINC-005 — SRP/ISP-Heuristiken auf Klassen-Ebene.
# Schwellen liegen am ergonomischen Ende der Empfehlung (vergleichbar
# mit detekt-Defaults `LargeClass.threshold` und `TooManyFunctions`).
max-public-methods = 12
max-attributes = 7
# PLR0903 (too-few-public-methods) braucht keinen Wert — ruff meldet
# Klassen mit weniger als 2 oeffentlichen Methoden; Dataclasses und
# Pydantic-Modelle sind automatisch ausgenommen.

[tool.ruff.lint.flake8-tidy-imports]
# AC-NO-RAND: Modulimport-Verbot global (Aufruf-Site-Check ergaenzend
# in tools/arch_check.py). Per Per-File-Ignore unten ("src/grid_gym/adapters/**" =
# ["TID"]) wird derselbe Import in adapters/* zugelassen, wo er fachlich
# erlaubt ist. Tests sind ueber "tests/**" = ["TID"] ebenfalls ausgenommen.
banned-module-level-imports = ["random", "secrets", "numpy.random"]

[tool.ruff.lint.flake8-tidy-imports.banned-api]
# AC-NO-TIME: datetime.datetime.utcnow ist von DTZ nicht erfasst.
"datetime.datetime.utcnow" = { msg = "Use ClockPort.now(tz=UTC) — GG-AR-TABU-005" }

[tool.ruff.lint.per-file-ignores]
# Tests duerfen assert, fixture-eigene Patterns und blind-except verwenden;
# DTZ/BLE/TRY/S sind in tests/** auf das jeweils sinnvolle Minimum reduziert.
"tests/**" = [
    "S101", "S104", "S105", "S106", "S311",   # asserts und fixture-Patterns
    "BLE001", "TRY003",                          # Fehler-Boilerplate in Tests
    "DTZ", "TID",                                # Zeit/Import-Tabus
    "C901",                                       # Komplexitaet in Tests OK
    "PLR0911", "PLR0912", "PLR0913", "PLR0915", "PLR0916", "PLR2004",  # zu-viel-*
    "PLR0902", "PLR0903", "PLR0904",             # SRP/ISP-Heuristiken (Tests duerfen Helper-Klassen)
    "N802", "N803", "N806",                      # Test-Naming (z. B. snake_case-Tests)
    "ARG001", "ARG002",                          # ungenutzte Fixture-Parameter
    "RUF012",                                    # mutable class attrs in Tests
]
# Adapter-Boundary-Module duerfen externe Exceptions zu Domain-Fehlern
# uebersetzen und brauchen dazu `except Exception:`. Die Liste ist
# abschliessend; jede Erweiterung erfordert ADR-Verweis.
"src/grid_gym/adapters/driving/http_api/error_translation.py" = ["BLE001"]
"src/grid_gym/adapters/driven/protocol_*/error_translation.py" = ["BLE001"]
"src/grid_gym/adapters/driven/persistence_*/error_translation.py" = ["BLE001"]
# DTZ ist nur in core fachlich verboten; Adapter duerfen `datetime.now(tz=...)`
# fuer Wall-Clock-Zeitstempel verwenden, wenn der Wert ausschliesslich an
# Telemetrie-/Audit-Metadaten geht und nicht in Domain-Entscheidungen einfliesst.
"src/grid_gym/adapters/**" = ["DTZ", "TID"]
```

Zusaetzlich definiert `pyproject.toml` eine eigene Sektion fuer
`tools/arch_check.py`, ueber die alle nicht-ruff-Whitelists
zentral und maschinenlesbar gefuehrt werden:

```toml
[tool.grid_gym.arch_check]
# AC-NO-JSON: einzige Pfade, in denen `json.dumps`/`json.dump`-Aufrufe
# erlaubt sind. tools/arch_check.py liest diese Liste und meldet jede
# Aufruf-Site ausserhalb als Verstoss. Erweiterung erfordert ADR-Verweis.
json-dumps-whitelist = [
    "src/grid_gym/hexagon/core/serialization/canonical.py",
]

# AC-DOMAIN-FROZEN: zusaetzliche Module, die wie hexagon.core.domain.* immutable
# sein muessen (z. B. Snapshot-Datenklassen, die ausserhalb hexagon.core.domain leben).
domain-frozen-extra = []

# AC-TYPED-ERRORS: Module, in denen `except Exception:` zugelassen ist
# (deckungsgleich mit den ruff-Per-File-Ignores oben, aber als
# einziger Single-Source-of-Truth fuer arch_check.py konsumierbar).
typed-errors-exempt = [
    "src/grid_gym/adapters/driving/http_api/error_translation.py",
    "src/grid_gym/adapters/driven/protocol_*/error_translation.py",
    "src/grid_gym/adapters/driven/persistence_*/error_translation.py",
]
```

Das frueher hier vorgeschlagene leere ruff-Per-File-Ignore
`"src/grid_gym/hexagon/core/serialization/canonical.py" = []` wurde
entfernt — ein leerer Ignore-Eintrag ist fuer ruff ein No-Op und
ergab keine wirksame Whitelist. Die Whitelist fuer AC-NO-JSON
lebt jetzt ausschliesslich in `[tool.grid_gym.arch_check]` und
wird von `tools/arch_check.py` ausgewertet.

`ruff`-Reichweite ist damit konkret nachvollziehbar; was ruff
nicht erfassen kann (`time.time`/`time.monotonic`-Calls, JSON-
Aufruf-Sites, Frozen-Klassen, God-Utility-Heuristik,
`GridGymError`-Vererbung, Zykluscheck), faengt `tools/arch_check.py`
ab.

Reichweiten-Vertrag fuer ruff-Regeln:

| Regelgruppe       | Wirksamer Scope                                                                                  |
| ----------------- | ------------------------------------------------------------------------------------------------ |
| `DTZ` (AC-NO-TIME)| `src/grid_gym/hexagon/core/**` und `src/grid_gym/hexagon/ports/**` (Adapter ausgenommen, siehe oben)              |
| `BLE`/`TRY`/`B904`| `src/grid_gym/**` ausser explizit gelisteten Error-Translation-Modulen                            |
| `S`               | `src/grid_gym/**`; in `tests/**` nur ohne `S101/S104/S105/S106/S311`                              |
| `TID`             | `src/grid_gym/**`; ergaenzt `import-linter` um schnelle Per-File-Banned-Imports                   |

#### Code-Review-Auflage (Reststeuerung fuer TABU-003)

`AC-ADAPTER-PURE` + `AC-ADAPTER-LIGHTWEIGHT` decken **nur Import-
und strukturelle Aspekte** von [`GG-AR-TABU-003`](../../../spec/architecture.md#architektur-tabus-build-architekturtest). Fachliche
Entscheidungen direkt im Adaptercode (z. B. ein Adapter, der
Wertebereiche prueft, statt das dem Kern zu ueberlassen) sind
statisch nicht voll erkennbar.

Verbindliche Reststeuerung:

- Jede Adapter-PR enthaelt ein Review-Checklisten-Item „keine fachlichen
  Entscheidungen im Adapter" mit konkreter Begruendung der gewaehlten
  Mapping-Funktionen.
- Diese Review-Anforderung ist in `docs/user/code-review.md` (Folgearbeit)
  und im PR-Template verankert.
- [`GG-AR-TABU-003`](../../../spec/architecture.md#architektur-tabus-build-architekturtest) gilt damit als **automatisierbar verifiziert (Import-Grenze
  und Komplexitaets-Heuristik)** und **review-pflichtig (Logik-Grenze)**.

Tabu-Abdeckungs-Matrix:

| Tabu              | Abgedeckt durch                                                                              |
| ----------------- | -------------------------------------------------------------------------------------------- |
| [`GG-AR-TABU-001`](../../../spec/architecture.md#4-architekturstruktur)    | AC-CORE-NO-ADAPTERS, AC-CORE-NO-DRIVING, AC-PORTS-NO-OUT                                      |
| [`GG-AR-TABU-002`](../../../spec/architecture.md#architektur-tabus-build-architekturtest)    | AC-HEXAGON-PURE (Whitelist), AC-NO-FW, AC-NO-IO-MOD; in `hexagon.ports.*` zusaetzlich AC-PORTS-NO-FW ([`GG-ARCHTEST-004`](../../../spec/lastenheft.md#gg-archtest-004)) |
| [`GG-AR-TABU-003`](../../../spec/architecture.md#architektur-tabus-build-architekturtest)    | AC-ADAPTER-PURE (Imports) + AC-ADAPTER-LIGHTWEIGHT (Heuristik) + Code-Review-Auflage (Logik)  |
| [`GG-AR-TABU-004`](../../../spec/architecture.md#4-architekturstruktur)    | AC-NO-CYCLES (SCC-Analyse via `grimp`)                                                        |
| [`GG-AR-TABU-005`](../../../spec/architecture.md#architektur-tabus-build-architekturtest)    | AC-NO-TIME                                                                                    |
| [`GG-AR-TABU-006`](../../../spec/architecture.md#architektur-tabus-build-architekturtest)    | AC-DOMAIN-FROZEN                                                                              |
| [`GG-AR-TABU-007`](../../../spec/architecture.md#architektur-tabus-build-architekturtest)    | AC-NO-GOD-UTILS                                                                               |
| [`GG-AR-TABU-008`](../../../spec/architecture.md#architektur-tabus-build-architekturtest)    | AC-TYPED-ERRORS                                                                               |

#### A-2 — Kanonische Serialisierung als getestete Library-Funktion

- `grid_gym.hexagon.core.serialization.canonical.canonical_json(value) -> bytes`
  ist die einzige erlaubte JSON-Serialisierungsstelle im Produktionscode
  (gewhitelistet in AC-NO-JSON). Vertrag:
  - festgelegte Feldreihenfolge (lexikographisch),
  - Float-Praezision (max. 6 Nachkommastellen, banker's rounding),
  - Integer-Sequenzen,
  - ISO-8601-UTC fuer Wall-Clock-Zeitstempel,
  - ganzzahlige Millisekunden fuer Simulationszeit
  ([`GG-DATA-005`](../../../spec/lastenheft.md#gg-data-005)).
- Property-basierte Tests via `hypothesis` in
  `tests/unit/hexagon/core/serialization/test_canonical.py` weisen nach: zwei
  semantisch identische Inputs erzeugen identische Bytes; Roundtrip
  Lesen → Schreiben ist stabil; alle Telemetry/Command/Event-Domain-
  Objekte aus [`GG-AR-COMP-DOMAIN`](../../../spec/architecture.md#5-komponentensicht) sind roundtrip-stabil.
- `canonical_json` ist intern als einziges Modul von der AC-NO-JSON-
  Regel ausgenommen. Die Implementierung MUSS folgende Vor-Normalisierung
  und Encoder-Optionen einhalten:

  1. **Numerisches Repraesentations-Modell.** Numerische Domain-Werte (Leistung,
     Energie, Frequenz, Spannung, Strom, Temperatur, SOC, …) werden intern als
     `Decimal` mit maximal 6 Nachkommastellen gefuehrt. Eingaben des Typs `float`
     werden an der Domain-Eingangsgrenze (Pydantic-Validator, Scenario-Loader,
     Adapter-Mapping) durch
     `Decimal(str(value)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)`
     normalisiert. **Innerhalb des Kerns existiert kein `float`** — `canonical_json`
     darf voraussetzen, dass numerische Felder bereits `int`, `Decimal` oder
     `bool` sind. Ein `float`, der den Kern erreicht, ist ein Verstoss gegen die
     Domain-Validierung, nicht ein Serialisierungsproblem.
  2. **Wertebereich und Verbote** (Eingabe-Vertrag von `canonical_json`):
     - Erlaubte Typen: `None`, `bool`, `int`, `Decimal`, `str`, `dict[str, …]`,
       `list[…]`, `tuple[…]`. Alle anderen Typen — insbesondere `float` —
       loesen `CanonicalSerializationError` aus.
     - `Decimal("NaN")`/`Decimal("Infinity")`/`Decimal("-Infinity")` sind in
       kanonischen Ausgaben **nicht erlaubt** ([`GG-DATA-003`](../../../spec/lastenheft.md#gg-data-003) markiert solche
       Werte als Qualitaetsstatus `nan`/`invalid`; sie tauchen in Telemetrie
       als Qualitaetsfeld auf, nicht als numerischer Wert). Treffen sie
       dennoch ein, wirft `canonical_json` einen typisierten
       `CanonicalSerializationError`.
     - Dictionary-Schluessel MUESSEN `str` sein; numerische oder Tuple-Keys
       sind verboten (entsprechen nicht dem JSON-Datenmodell).
     - Wall-Clock-Zeitstempel werden vor dem Aufruf auf `datetime` mit
       `tzinfo=UTC` normalisiert und als ISO-8601-UTC-String uebergeben
       (`...Z`-Suffix); Sub-Sekunden mit max. 6 Stellen. Diese Normalisierung
       gehoert nicht in `canonical_json`, sondern in die Domain-Eingangsgrenze.
     - Simulationszeit wird als ganzzahlige Millisekunde (`int`) uebergeben.
     - `bytes` werden als Base64-String mit Praefix `b64:` uebergeben, sofern
       sie ueberhaupt im Domain-Modell vorkommen (heute nicht — Reserve fuer
       Snapshot-Payloads).
  3. **Custom-Emitter** (Standard-Implementierung). `json.dumps` ist **nicht**
     verwendbar, weil `Decimal` weder von der Standard-Bibliothek noch
     ueber `default=` als JSON-Zahl emittiert werden kann (`default=` darf
     nur JSON-Native-Werte zurueckgeben, und ein Rueckgabewert `str(decimal)`
     wuerde als JSON-String serialisiert, nicht als Zahl). Stattdessen
     implementiert `canonical.py` einen kleinen, vollstaendig kontrollierten
     JSON-Emitter:

     ```python
     # hexagon/core/serialization/canonical.py — einzige AC-NO-JSON-Ausnahme
     # (Skizze; die produktive Implementation in
     # `src/grid_gym/hexagon/core/serialization/canonical.py` ist der
     # autoritative Stand.)
     from decimal import Decimal

     _ESCAPE = {
         '"': '\\"', "\\": "\\\\",
         "\b": "\\b", "\f": "\\f", "\n": "\\n", "\r": "\\r", "\t": "\\t",
     }
     _SURROGATE_LOW, _SURROGATE_HIGH = 0xD800, 0xDFFF


     class CanonicalSerializationError(GridGymError):
         """Wurzel der Vertragsverletzungen."""


     class FloatNotAllowedError(CanonicalSerializationError):
         def __init__(self) -> None:
             super().__init__("float not allowed — convert to Decimal at domain ingress")


     class NonFiniteDecimalError(CanonicalSerializationError):
         def __init__(self) -> None:
             super().__init__("NaN/Infinity not allowed in canonical output")


     class NonStringDictKeyError(CanonicalSerializationError):
         def __init__(self) -> None:
             super().__init__("dict keys must be str")


     class UnsupportedTypeError(CanonicalSerializationError):
         def __init__(self, type_name: str) -> None:
             super().__init__(f"unsupported type: {type_name}")


     class SurrogateNotAllowedError(CanonicalSerializationError):
         def __init__(self) -> None:
             super().__init__("surrogate code points are not allowed")


     class CircularReferenceError(CanonicalSerializationError):
         def __init__(self) -> None:
             super().__init__("circular reference detected in input")


     def canonical_json(value: object) -> bytes:
         parts: list[str] = []
         _emit(value, parts, seen=set())
         return "".join(parts).encode("utf-8")


     def _emit(value: object, out: list[str], seen: set[int]) -> None:
         # `seen` traegt id() der gerade in Bearbeitung befindlichen
         # Container — _emit_dict/_emit_array fuegen ihren id hinzu, der
         # finally-Block entfernt ihn wieder (Diamond-Pattern bleibt OK).
         if value is None: out.append("null")
         elif value is True: out.append("true")
         elif value is False: out.append("false")
         elif isinstance(value, int): out.append(str(value))
         elif isinstance(value, Decimal):
             if not value.is_finite(): raise NonFiniteDecimalError
             # Signed-Zero-Normalisierung: `Decimal("-0")` -> `Decimal("0")`
             # via copy_abs() — semantisch identische Nullen sind byte-stabil.
             if value.is_zero(): value = value.copy_abs()
             out.append(format(value, "f"))
         elif isinstance(value, str): out.append(_emit_string(value))
         elif isinstance(value, dict): _emit_dict(value, out, seen)
         elif isinstance(value, list | tuple): _emit_array(value, out, seen)
         elif isinstance(value, float): raise FloatNotAllowedError
         else: raise UnsupportedTypeError(type(value).__name__)


     def _emit_dict(value: dict, out: list[str], seen: set[int]) -> None:
         cid = id(value)
         if cid in seen: raise CircularReferenceError
         seen.add(cid)
         try:
             keys: list[str] = []
             for k in value:
                 if not isinstance(k, str): raise NonStringDictKeyError
                 keys.append(k)
             keys.sort()
             out.append("{")
             for i, k in enumerate(keys):
                 if i: out.append(",")
                 out.append(_emit_string(k)); out.append(":")
                 _emit(value[k], out, seen)
             out.append("}")
         finally:
             seen.discard(cid)


     def _emit_array(value, out: list[str], seen: set[int]) -> None:
         cid = id(value)
         if cid in seen: raise CircularReferenceError
         seen.add(cid)
         try:
             out.append("[")
             for i, item in enumerate(value):
                 if i: out.append(",")
                 _emit(item, out, seen)
             out.append("]")
         finally:
             seen.discard(cid)


     def _emit_string(s: str) -> str:
         buf = ['"']
         for ch in s:
             if ch in _ESCAPE: buf.append(_ESCAPE[ch])
             elif _SURROGATE_LOW <= ord(ch) <= _SURROGATE_HIGH:
                 raise SurrogateNotAllowedError
             elif ord(ch) < 0x20: buf.append(f"\\u{ord(ch):04x}")
             else: buf.append(ch)
         buf.append('"')
         return "".join(buf)
     ```

     Eigenschaften des Emitters:
     - **Typisierte Fehlerklassen** (AC-TYPED-ERRORS-konform, TRY003-clean):
       `CanonicalSerializationError` als Wurzel, plus `FloatNotAllowedError`,
       `NonFiniteDecimalError`, `NonStringDictKeyError`,
       `UnsupportedTypeError(type_name)`, `SurrogateNotAllowedError`,
       `CircularReferenceError`. Messages stehen im Constructor, nicht am
       Call-Site.
     - Deterministisch by-construction: Reihenfolge ueber `sorted(keys)`,
       keine impliziten Konvertierungen, keine Drittpartei-Heuristiken.
     - **Cycle-Detection**: `seen: set[int]` traegt `id()` der gerade
       in Bearbeitung befindlichen Container; `_emit_dict`/`_emit_array`
       fangen Rekursion frueh ab und entfernen den `id` im `finally` —
       Diamond-Patterns (gleicher Container mehrfach an verschiedenen
       Stellen, kein Zyklus) bleiben zulaessig.
     - `Decimal` wird direkt als JSON-Zahl in Fixed-Point-Notation
       emittiert (`format(value, "f")`). Tail-Nullen bleiben erhalten —
       Quantisierung auf max. 6 Stellen passiert an der Domain-Eingangs-
       grenze (Pydantic-Validator, Scenario-Loader, Adapter-Mapping)
       ueber `Decimal(str(value)).quantize(Decimal("0.000001"), rounding=ROUND_HALF_EVEN)`,
       nicht hier. **Signed-Zero-Normalisierung**: `Decimal("-0")` →
       `Decimal("0")` via `.copy_abs()` (byte-stabil ueber Vorzeichen).
     - `float` ist verboten (`FloatNotAllowedError`).
     - **Surrogate-Codepoints** (U+D800..U+DFFF) sind verboten
       (`SurrogateNotAllowedError`) — weder gueltiges UTF-8 noch
       gueltiges JSON (RFC 8259 §7); Adapter, die rohe Bytes hochheben,
       muessen Surrogate vorher bereinigen.
     - JSON-Strings folgen RFC 8259: doppelte Anfuehrungszeichen, Backslash-
       Escape, Steuerzeichen `<0x20` als `\u00XX`. U+2028/U+2029
       (line/paragraph separator) und U+007F (DEL) werden RFC-konform
       literal emittiert — Pre-ES2019-JavaScript-`eval()`-Konsumenten
       muessen einen modernen `JSON.parse`-Parser nutzen.
     - Encoding: UTF-8-Bytes; kein Umweg ueber `str` an Konsumenten.
  4. **Ergebnistyp** ist `bytes` (UTF-8). Alle Schreibpfade (Persistenz,
     Replay-Diff, WebSocket-Frame) konsumieren `bytes` direkt; ein Round-Trip
     ueber `str` ist verboten, um implizite Re-Encodings auszuschliessen.

  Als deterministischer Alternativ-Encoder ist `orjson` mit
  `OPT_SORT_KEYS | OPT_PASSTHROUGH_SUBCLASS` plus einer
  `default=`-Bridge zulaessig, sofern (a) die Decimal-Bridge
  Fixed-Point-Notation als JSON-Zahl emittiert (orjson kann das ueber
  einen Custom-Stream-Adapter, nicht ueber `default=` allein — eine
  Wrapper-Implementierung muss das nachweisen), (b) die Vor-Normalisierung
  aus Punkt 2 unveraendert davor laeuft, (c) die Tests bytes-identische
  Ausgabe zwischen der Standard-Implementierung (Custom-Emitter, oben) und
  der Alternativ-Implementierung nachweisen **inklusive Cycle-Detection
  (typisierter `CircularReferenceError`), Surrogate-Rejection
  (`SurrogateNotAllowedError`) und Signed-Zero-Normalisierung**. Wahl
  des Alternativ-Encoders
  ist eine eigene Folge-ADR fuer Performance-/Implementierungs-Alternativen;
  A-2 fixiert den **Vertrag** (Format-Details aus Punkt 2) und die
  **Standard-Implementierung** (Custom-Emitter aus Punkt 3) verbindlich —
  Alternativen muessen beides erfuellen, nicht nur das Erste.

- Contract AC-NO-JSON aus A-1 erzwingt die Nutzung an allen anderen
  Stellen.

#### Beide Auflagen

Zwei Versagensszenarien mit unterschiedlichem Lifecycle-Effekt
(gemaess ADR 0006):

- **Spike-0 rot (vor Acceptance):** A-1 oder A-2 lassen sich im
  Skelett nicht gruen konfigurieren. ADR 0002 geht auf `Rejected`;
  [`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte) bleibt offen; eine Folge-ADR (vermutlich Option
  D, Kotlin/JVM) tritt an die Stelle.
- **A-1/A-2 unhaltbar nach Acceptance:** Die Contracts oder der
  Custom-Emitter erweisen sich im Hauptprojekt als nicht haltbar
  (z. B. eine wesentliche Bibliothek verletzt einen Contract
  reproduzierbar, ohne dass eine Anpassung moeglich ist). In
  diesem Fall wird ADR 0002 nicht „zurueckgezogen" — das verbietet
  ADR 0006 fuer Accepted-ADRs — sondern durch eine Nachfolge-ADR
  `Superseded`. Die Nachfolge-ADR dokumentiert: welchen
  Contract/Vertrag sie ersetzt, welche Migrationsstrategie greift
  und ob [`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte) wieder geoeffnet wird.

### Wann Option D (Kotlin/JVM) gezogen wird

Die Fallback-Trigger sind direkt an Lastenheft-Akzeptanzkriterien
gekoppelt, nicht an externe Schwellwerte. Tritt einer der folgenden
Punkte ein, wird Option D aktiviert.

**Hinweis zur Stufenhochstufung:** [`GG-RT-001`](../../../spec/lastenheft.md#gg-rt-001) ist `MUSS` und damit
ein Hard-Fail-Trigger ohne Auslegungsspielraum. [`GG-RT-004`](../../../spec/lastenheft.md#gg-rt-004) und
[`GG-RT-005`](../../../spec/lastenheft.md#gg-rt-005) sind im Lastenheft `SOLLTE`. Diese ADR stuft beide
fuer die Sprachwahl bewusst zu **Go/No-Go-Triggern** hoch: ein
Verstoss in der Referenzumgebung waere zwar lastenheftkonform mit
dokumentierter Abweichung machbar, ist aber als Signal fuer
strukturelle Sprach-/Runtime-Untauglichkeit zu werten. Wer diese
Hochstufung nicht mittragen will, muss diese ADR aendern, bevor
sie als `Accepted` gefuehrt wird.

Trigger:

- **[`GG-RT-001`](../../../spec/lastenheft.md#gg-rt-001)-Verstoss bei 100 ms/1 s** (`MUSS`-Hard-Fail). Demo-
  Konfiguration mit 100 ms oder 1 s Tick-Groesse zeigt im Healthcheck
  Backpressure-Status `true` oder verpasste Ticks ueber 1.000 Ticks.
- **[`GG-RT-004`](../../../spec/lastenheft.md#gg-rt-004)-Verstoss im Benchmark-Szenario** (`SOLLTE`,
  hochgestuft). Benchmark mit 100 Geraeten und 10.000 Ticks erzeugt
  verlorene Events oder nichtdeterministischen Replay-Diff
  ([`GG-REPLAY-007`](../../../spec/lastenheft.md#gg-replay-007), [`GG-SAFE-006`](../../../spec/lastenheft.md#gg-safe-006)).
- **[`GG-RT-005`](../../../spec/lastenheft.md#gg-rt-005)-Verstoss im Telemetriepfad** (`SOLLTE`, hochgestuft).
  Telemetrieport-Messung unterschreitet 10.000 Punkte/s mit
  256-Byte-Payload in der Referenzumgebung dauerhaft, auch mit
  gepuffertem Persistenzpfad.
- **A-1 nicht erfuellbar / Spike-0 rot.** Die sechzehn Contracts aus
  A-1 (`import-linter`, `ruff`, `tools/arch_check.py` inkl. `grimp`-
  Zykluscheck) lassen sich nicht so konfigurieren, dass [`GG-AR-TABU-001`](../../../spec/architecture.md#architektur-tabus-build-architekturtest)..008
  reproduzierbar erfasst werden — etwa weil AST-Pruefung wesentliche
  Verletzungen verfehlt, die `grimp`-SCC-Analyse falsche Positive
  produziert oder die Whitelist-Pflege im CI nicht haltbar ist. In
  diesem Fall scheitert bereits Spike-0 (siehe Auflage A-1 und Status-Pfad),
  bevor die ADR `Accepted` werden kann.
- **Lastenheft-Aenderung.** Eine spaetere Aenderung normiert
  < 10 ms-Tick im Produktionspfad (heute explizit nicht;
  [`GG-RT-001`](../../../spec/lastenheft.md#gg-rt-001) macht 10 ms zum Diagnose-/Messmodus).

---

## 5. Entscheidung

Der Akzeptanzbeschluss verlaeuft entlang des dreistufigen
Status-Pfads aus den Auflagen-Sektionen dieser ADR (Pflicht-Pfad zur
ADR-Annahme):

1. **Proposed → Provisional:** Projektowner stimmt der Empfehlung
   (Option A mit Auflagen A-1/A-2) zu, gibt Spike-0 frei. ADR
   wird auf `Provisional` gesetzt; der Eintrag fuer [`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte)
   in `architecture.md` erhaelt einen Verweis auf diese ADR, wird
   aber nicht als geschlossen markiert.
2. **Provisional → Accepted:** Spike-0 wird gegen den Spike-0-Vertrag
   aus den Auflagen-Sektionen dieser ADR abgeschlossen. Erst dann
   wird ADR auf `Accepted` gesetzt und [`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte) in
   `architecture.md` mit „Geschlossen mit ADR 0002" markiert.
3. **Spike-0 rot (Proposed/Provisional → Rejected):** Vor Acceptance
   wird die ADR auf `Rejected` gesetzt (ADR-0006-Lifecycle); ein
   Folge-ADR (Option D oder anderer Stack) tritt an die Stelle.
4. **Nach Acceptance unhaltbar (Accepted → Superseded):** Wenn A-1
   oder A-2 nach Acceptance im Hauptprojekt nicht haltbar sind, wird
   ADR 0002 durch eine Nachfolge-ADR `Superseded` (ADR-0006-Lifecycle:
   `Withdrawn` ist Vor-Beschluss, `Superseded` post-Acceptance).

_Aktueller Status: `Proposed` — kein Beschluss._

---

## 6. Konsequenzen (bei Acceptance von Option A)

**Bei Acceptance** (d. h. nach gruenem Spike-0; siehe Status-Pfad in den
Auflagen- und Entscheidungs-Sektionen dieser ADR) schliesst diese ADR
[`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte) mit den folgenden
konkreten Wahlen. Solange die ADR auf `Proposed` oder `Provisional`
steht, sind diese Wahlen die **Absicht** der Empfehlung, aber kein
verbindlicher Stack-Beschluss; insbesondere darf [`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte) in `architecture.md`
[`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte) bis dahin **nicht** als geschlossen markieren.

Es verbleibt **keine** „Paketmanager- oder Layout-Frage" als
Folgearbeit; spaetere Wechsel benoetigen eine eigene ADR, die diese
hier abloest.

### 6.1 Sprache, Runtime, Build-Stack (verbindlich)

| Aspekt              | Wahl                                              | Begruendung                                                                              |
| ------------------- | ------------------------------------------------- | ---------------------------------------------------------------------------------------- |
| Sprache             | Python — Minimum 3.13, Referenz-Runtime 3.14       | Option A aus den Bewertungs-/Empfehlungs-Sektionen dieser ADR. Versions-Auswahl per Lifecycle-Stand (2026-05-14: 3.13 Bugfix bis 2029-10, 3.14 Bugfix bis 2030-10; 3.12 nur noch Security; 3.15 Prerelease, kein Production-Ziel). |
| Paketmanager + Lock | `uv` mit `uv.lock`                                 | Rust-Implementierung, schnelle CI-Resolves, lockfile-first, eingebauter Python-Toolchain-Manager. Passt zu [`GG-DEPLOY-002`](../../../spec/lastenheft.md#gg-deploy-002)/011 (offline, reproduzierbar) und [`GG-CICD-001`](../../../spec/lastenheft.md#gg-cicd-001) (reproduzierbarer Build). |
| Dependency Groups   | `[dependency-groups]` in `pyproject.toml` nach PEP 735 (Gruppen `dev`, `test`, `lint`, `docs`) | Trennt produktive Laufzeit-Abhaengigkeiten von Test-/Lint-/Build-Toolchain ([`GG-CICD-002`](../../../spec/lastenheft.md#gg-cicd-002)/005/006), ohne mehrere `pyproject.toml`-Dateien anlegen zu muessen. |
| uv-Workspaces       | NICHT verwendet                                      | Modulgrenzen aus die Modulgrenzen-Vertraege [`GG-AR-TABU-001`](../../../spec/architecture.md#architektur-tabus-build-architekturtest)..008 in `architecture.md` werden durch Import-Contracts (A-1) erzwungen, nicht durch separate Distribution-Pakete. uv-Workspaces sind trigger-basierte Folgearbeit, falls einzelne `grid-gym`-Pakete extern konsumiert werden sollen. |
| Repository-Layout   | Monolith mit `src/grid_gym/{hexagon/{core,ports},adapters}/`-Layout und `import-linter`-Layern | Eine Distribution, eine Lock-Datei; klare Trennung `src/` (Produktion) vs. `tests/` (Tests, von A-1-Tabus teilweise ausgenommen). `hexagon/` gruppiert fachlichen Kern und Ports gemaess `architecture.md` §4.2. |
| Project-Definition  | Ein `pyproject.toml` im Root                       | Eine Lock-Datei, eine CI-Resolve, ein Distribution-Punkt                                  |
| Toolchain-Pinning   | `.python-version` (uv-kompatibel) auf `3.14`; Override via `make <target> PYTHON_VERSION=3.13` getestet. CI-Matrix gegen `3.13` und `3.14` aktiviert sich mit erstem GitHub-Actions-Workflow (Folgewelle nach M1). | reproduzierbarer Build ([`GG-CICD-001`](../../../spec/lastenheft.md#gg-cicd-001)); Floor und Referenz-Runtime sind explizit testbar |
| HTTP/WebSocket      | FastAPI + `uvicorn`                                | OpenAPI aus Code ([`GG-API-003`](../../../spec/lastenheft.md#gg-api-003)), WebSocket nativ ([`GG-API-002`](../../../spec/lastenheft.md#gg-api-002))                            |
| Validierung         | Pydantic v2                                        | Schema- und Wertebereichspruefung ([`GG-SCN-008`](../../../spec/lastenheft.md#gg-scn-008), [`GG-SAFE-001`](../../../spec/lastenheft.md#gg-safe-001)/008, [`GG-DATA-002`](../../../spec/lastenheft.md#gg-data-002)/003)     |
| Persistenz-Treiber  | `psycopg` 3 (async) + `alembic`                    | [`GG-PERSIST-001`](../../../spec/lastenheft.md#gg-persist-001)..009, Migrationen ([`GG-PERSIST-008`](../../../spec/lastenheft.md#gg-persist-008)); Repository-Pattern (kein ORM) bleibt offen unter [`GG-AR-OPEN-003`](../../../spec/architecture.md#19-offene-architektonische-punkte) |
| Strukturierte Logs  | `structlog` + stdlib `logging`                     | [`GG-OTEL-002`](../../../spec/lastenheft.md#gg-otel-002)                                                                              |
| Metriken            | `prometheus-client`                                | [`GG-OTEL-003`](../../../spec/lastenheft.md#gg-otel-003)                                                                              |
| Tracing (optional)  | `opentelemetry-python` mit OTLP-Exporter           | [`GG-OTEL-001`](../../../spec/lastenheft.md#gg-otel-001)/004                                                                          |
| Test-Framework      | `pytest`, `pytest-cov`, `pytest-asyncio`           | [`GG-TESTTYPE-001`](../../../spec/lastenheft.md#gg-testtype-001)/002, [`GG-COV-001`](../../../spec/lastenheft.md#gg-cov-001)..005                                                   |
| Property-Tests      | `hypothesis`                                       | [`GG-SIM-001`](../../../spec/lastenheft.md#gg-sim-001)..004, [`GG-DATA-005`](../../../spec/lastenheft.md#gg-data-005)                                                           |
| Integration-Tests   | `testcontainers-python` (Postgres, ggf. Influx)    | [`GG-TESTTYPE-002`](../../../spec/lastenheft.md#gg-testtype-002), [`GG-PERSIST-005`](../../../spec/lastenheft.md#gg-persist-005)                                                        |
| Architekturtests    | Tool-Suite aus A-1: `import-linter` + `ruff` (`BLE`, `TRY`, `DTZ`, `S`, `TID`, `B904`) + `tools/arch_check.py` (inkl. `grimp`-SCC-Zykluscheck) mit sechzehn Contracts und scope-gesteuerten ruff-Per-File-Ignores; Code-Review-Auflage fuer Logik-Anteil von TABU-003 | [`GG-ARCHTEST-001`](../../../spec/lastenheft.md#gg-archtest-001)..005, [`GG-AR-TABU-001`](../../../spec/architecture.md#architektur-tabus-build-architekturtest)..008                                              |

### 6.2 Wirkung auf andere Dokumente

Die folgenden Dokument-Aenderungen werden **erst bei `Accepted`**
ausgefuehrt, nicht bei `Proposed`/`Provisional`:

- die Modulgrenzen-Vertraege [`GG-AR-TABU-001`](../../../spec/architecture.md#architektur-tabus-build-architekturtest)..008 in `architecture.md` (Verzeichnisstruktur) wird mit
  Python-Paketnamen aktualisiert (`src/grid_gym/hexagon/core/...`,
  `src/grid_gym/hexagon/ports/...`, `src/grid_gym/adapters/...`).
- [`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte) in `architecture.md` markiert [`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte) als „Geschlossen
  mit ADR 0002".
- `roadmap.md` Vorbedingung 1 ([`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte)) ist erledigt.

Bereits bei `Provisional` (Spike-0 freigegeben) erlaubt sind:

- Eintrag in [`GG-AR-OPEN-001`](../../../spec/architecture.md#19-offene-architektonische-punkte) in `architecture.md` als „Verweis auf ADR 0002 (Spike-0
  laufend)" — schliesst den Punkt **nicht**, signalisiert nur den
  laufenden Beschluss.

Davon unberuehrt bleibt offen:

- [`GG-AR-OPEN-003`](../../../spec/architecture.md#19-offene-architektonische-punkte) (ORM vs. leichter Treiber) — diese ADR fixiert
  `psycopg` 3 als Treiber, aber nicht das Repository-/ORM-Muster.

---

## 7. Offene Folge-Punkte (nicht durch diese ADR geschlossen)

- **[`GG-AR-OPEN-002`](../../../spec/architecture.md#19-offene-architektonische-punkte)** API/Simulation als ein oder zwei Prozesse —
  Composition-Root-Entscheidung; eigener ADR.
- **[`GG-AR-OPEN-003`](../../../spec/architecture.md#19-offene-architektonische-punkte)** Persistenzzugriffsmuster (Repository-Pattern
  vs. SQLAlchemy-Core vs. SQLAlchemy-ORM) — eigener ADR. `psycopg` 3
  als Treiber ist hier gesetzt, die Schicht darueber nicht.
- **[`GG-AR-OPEN-004`](../../../spec/architecture.md#19-offene-architektonische-punkte)..010** unveraendert offen.
- ADR fuer `RandomPort`-Implementierung (gebondeter PRNG,
  Seeding-Kette) — Folgearbeit, schliesst keinen `GG-AR-OPEN-*`,
  aber materiell wichtig fuer [`GG-SIM-001`](../../../spec/lastenheft.md#gg-sim-001).
- ADR fuer Performance-/Implementierungs-Alternativen der kanonischen
  Serialisierung (`orjson`-Bridge, `msgspec`, Rust-Backend) — die
  Format-Details aus A-2 (Punkt 2) und die Standard-Implementierung
  (Custom-Emitter aus A-2 Punkt 3) sind durch diese ADR fix; eine
  Folge-ADR darf nur die Umsetzungsroute aendern und muss
  Byte-Gleichheit gegenueber dem Standard-Emitter nachweisen.
