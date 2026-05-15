# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- `spec/architecture.md` v0.1.0 — Architekturbeschreibung mit
  hexagonaler Sicht, Driving-/Driven-Ports (`GG-AR-PORT-*`),
  Architektur-Tabus (`GG-AR-TABU-*`), Komponenten (`GG-AR-COMP-*`),
  offenen Punkten (`GG-AR-OPEN-*`).
- `spec/lastenheft.md` §27 V-Modell-Rueckverfolgbarkeit mit drei
  Tabellen (Anforderung → Design / Implementierung / Test) und neuer
  Anforderung `GG-TRACE-001`.
- `docs/`-Skelett mit `plan/adr/`, `plan/planning/{open,next,in-progress,done}/`,
  `user/`, `archive/`.
- `docs/plan/adr/0001-documentation-and-planning-structure.md` —
  Dokumentations- und Planungsstruktur.
- `docs/plan/adr/0003-adr-lifecycle.md` — historischer ADR-Lifecycle als
  Ergaenzung zu ADR 0001 (Statuswerte
  `Proposed`/`Provisional`/`Accepted`/`Rejected`/`Withdrawn`/`Superseded`,
  Uebergangsregeln, Verhaeltnis zu ADR 0001 §3/§4, Pflege-Regeln
  fuer `architecture.md §19`-Eintraege je Status). Loest den
  impliziten Konflikt zwischen ADR 0001 (ADRs = Entscheidungen)
  und ADR 0002 (Spike-getriebener Vorschlag) auf, ohne ADR 0001
  inhaltlich zu ueberschreiben. Inzwischen durch ADR 0006 abgeloest.
- `docs/plan/adr/0006-adr-lifecycle-superseding-and-process-corrections.md`
  — aktive ADR-Lifecycle-Regel. Supersedes ADR 0003; klaert
  `Superseded`-Metadaten, Header-Schema, operative Spike-Artefakte,
  `Rejected` vs. `Withdrawn` und die Einordnung der ADR-0004-
  Retrofit-Regel fuer Lifecycle-Aenderungen.
- `docs/plan/adr/0004-identifier-based-cross-references.md` —
  Querverweise zwischen Spec-/Planungsartefakten nutzen Kennungen
  (`GG-*`, `GG-AR-*`, `GG-TRACE-*`, `AC-*`, ADR-Nummern) als
  primaere Referenz; `§…`-Hinweise sind nur Lesehilfen in Klammern.
  Retrofit-Regel: bei naechster Beruehrung umstellen.
- `docs/plan/adr/0005-type-check-gate.md` — `mypy --strict` als
  Pflicht-Gate fuer `GG-QG-005` Static-Analysis und automatisierte
  Teilabdeckung von `GG-PRINC-004` (LSP via Variance) und
  `GG-PRINC-005` (ISP via Protocol-Konformitaet). Status:
  `Provisional`, Acceptance synchron mit `ADR 0002`. `pyright` bleibt
  Developer-Tool ueber Pylance, nicht CI-Gate.
- `Dockerfile`-Stage `typecheck` und Makefile-Target `make typecheck`
  ergaenzt; Aggregator `gates` enthaelt jetzt `typecheck` zwischen
  `format-check` und `arch-check`.
- `docs/plan/adr/0002-language-and-build-stack.md` — Entwurf zur
  Sprach- und Build-Wahl (Status: Provisional; schliesst bei Annahme
  `GG-AR-OPEN-001`). Begruendung MVP-getrieben; Future-Punkte als
  Zusatznutzen ausgewiesen. Auflage A-1 als Drei-Tool-Suite
  (`import-linter` + `ruff` + eigenes AST-Skript `tools/arch_check.py`)
  (inkl. `grimp`-SCC-Zykluscheck) mit fuenfzehn Contracts:
  AC-CORE-NO-ADAPTERS, AC-CORE-NO-DRIVING, AC-PORTS-NO-OUT,
  AC-PORTS-NO-FW (`GG-ARCHTEST-004`), AC-ADAPTER-PURE,
  AC-ADAPTER-LIGHTWEIGHT (AST-Heuristik), AC-NO-FW, AC-NO-IO-MOD,
  AC-NO-CYCLES (Graph-SCC statt `independence`), AC-NO-TIME,
  AC-NO-RAND, AC-NO-JSON, AC-DOMAIN-FROZEN, AC-NO-GOD-UTILS,
  AC-TYPED-ERRORS. Tabu-Abdeckungs-Matrix ausgewiesen mit
  Reststeuerung: `GG-AR-TABU-003` Logik-Anteil ist
  review-pflichtig. `ruff`-Per-File-Ignores normiert (`tests/**`,
  Error-Translation-Module, Adapter-DTZ-Scope) plus konkrete
  `flake8-tidy-imports`-Konfiguration (`banned-api` fuer
  `datetime.datetime.utcnow`, `banned-module-level-imports` fuer
  `random`/`secrets`/`numpy.random` in `core.*`). Rollenverteilung
  zwischen `ruff` und `tools/arch_check.py` ehrlich getrennt:
  `time.time`/`time.monotonic`/`asyncio.get_event_loop().time` und
  Aufruf-Site-Random sind explizit `tools/arch_check.py`,
  nicht `ruff`. `AC-NO-JSON` mit Whitelist fuer
  `src/grid_gym/core/serialization/canonical.py` (loest A-2-
  Selbstblockade). Auflage A-2 mit hartem Format-/Roundtrip-Vertrag:
  Vor-Normalisierung via `Decimal.quantize` + `ROUND_HALF_EVEN`,
  NaN/Infinity-Verbot (`allow_nan=False`), ISO-8601-UTC fuer
  Wall-Clock-Zeit, ganzzahlige Millisekunden fuer Simulationszeit,
  UTF-8-Bytes als Vertragsschnittstelle; `orjson` als
  Alternativ-Encoder mit Bytes-Gleichheits-Test zugelassen.
  Fallback-Trigger an `GG-RT-001/004/005`, `GG-REPLAY-007`,
  `GG-SAFE-006` gekoppelt; `GG-RT-004/005` als bewusst zu
  Go/No-Go hochgestufte `SOLLTE`-Anforderungen ausgewiesen.
  Konsequenzen (§6) fixieren Paketmanager (`uv` mit `uv.lock`),
  PEP-735-Dependency-Groups, Repo-Layout (Monolith
  `src/grid_gym/` mit `import-linter`-Layern; uv-Workspaces nicht
  verwendet); §6 ausdruecklich als „bei Acceptance" formuliert,
  §6.2 trennt Acceptance- von Provisional-Wirkung. **Status-Pfad
  dreistufig** (`Proposed → Provisional → Accepted`) mit
  Pre-Acceptance-Spike-0-Vertrag; `GG-AR-OPEN-001` wird erst nach
  gruenem Spike-0 in `architecture.md §19` als geschlossen
  markiert. `ruff.toml`-Block korrigiert: `banned-module-level-imports`
  unter `[tool.ruff.lint.flake8-tidy-imports]` platziert (vorher
  faelschlich eigene Sub-Tabelle); Spike-0 prueft die Konfiguration
  ueber `ruff check --no-cache`. K-CONTAIN auf `o` korrigiert.
  A-2-Vertrag implementierbar gemacht: numerisches Repraesentations-
  Modell (`Decimal` mit max. 6 Nachkommastellen, kein `float` im Kern),
  eigene `CanonicalEncoder`-Subklasse von `json.JSONEncoder` die
  `Decimal` ueber `format(value, "f")` emittiert (loest die Luecke,
  dass `json.dumps` `Decimal` nativ nicht kennt), Standard-Implementierung
  als konkrete Python-Skizze hinterlegt. AC-NO-JSON-Whitelist von
  Pseudo-`per-file-ignores`-Eintrag auf echte
  `[tool.grid_gym.arch_check]`-Konfigurationssektion umgestellt,
  die `tools/arch_check.py` als Single-Source-of-Truth liest
  (`json-dumps-whitelist`, `domain-frozen-extra`, `typed-errors-exempt`).
  Status-Pfad verweist jetzt auf ADR 0006 als aktive
  Lifecycle-Definition.
- `docs/plan/planning/in-progress/roadmap.md` — Roadmap-Skelett als
  Quelle fuer §27.2-Meilenstein-Marker.
- Quality-Gate-Erweiterung in `Dockerfile`/`Makefile`:
  `coverage-gate` zusaetzlich mit `--cov-branch` und 85%-Branch-Schwelle
  (`GG-COV-002`); neuer Stage `coverage-gate-critical` mit
  Modul-Filter `core/{simulation,devices/battery,scenario,replay}`
  und 90% Line/Branch (`GG-COV-003` MUSS); neuer Stage `dep-audit`
  mit `pip-audit --strict` gegen die per `uv export` materialisierte
  Lockfile (`GG-QG-002`/`GG-QA-005`); Makefile-Target `image-audit`
  mit `trivy image --exit-code 1 --severity HIGH,CRITICAL`
  (`GG-QG-002` SOLLTE); neuer Stage `openapi-validate` (FastAPI-Spec-
  Export + `openapi-spec-validator`, `GG-QG-006`). Aggregator
  `gates` erweitert um `coverage-gate-critical` und `dep-audit`;
  `ci` erweitert um `openapi-validate` und `image-audit`.
- `Dockerfile` (Multi-Stage) und `Makefile` als Spike-0-Geruest zu
  ADR 0002. Stages: `base`, `deps`, `source`, `lint`, `format-check`,
  `arch-check`/`arch-check-imports`/`arch-check-custom`,
  `test-unit`/`test-determinism`/`test-replay`/`test-fault`,
  `coverage-gate`, `build-app`, `runtime` (non-root, /health
  HEALTHCHECK, Port 8080). Makefile-Targets pro Stage plus
  Aggregator (`gates`, `ci`, `fullbuild`) und Maintenance
  (`lock-refresh`, `sbom`, `clean`). Pattern an
  `/Development/bess-ems/{Makefile,Dockerfile}` orientiert; Stack
  gemaess ADR 0002 (Python 3.13+/3.14, `uv`, `ruff`, `import-linter`,
  `tools/arch_check.py`, `pytest`, `hypothesis`, `testcontainers`).
  Artefakte greifen die Spike-0-Lieferliste auf und setzen die
  noch fehlenden Spike-0-Bausteine (`pyproject.toml`,
  `src/grid_gym/`, `tests/`, `tools/arch_check.py`) als kuenftig
  voraus. ADR-0002-Status ist `Provisional`; die Artefakte sind als
  Spike-0-Pfad gemaess ADR 0006 gekennzeichnet.
- `docs/plan/planning/open/` mit elf Trigger-Watch-Dateien
  (`001-code-review-doc.md` bis `011-hexagon-layout-adr-0002-realign.md`)
  und aktualisiertem `README.md` mit Bestandstabelle. Macht die
  bisher impliziten Folgearbeiten aus ADR 0002/0004/0005, Makefile
  und Dockerfile sichtbar (`docs/user/code-review.md`,
  `tools/check_refs.py`, `RandomPort`-ADR, Alternativ-Encoder-ADR,
  mypy/pyright-Re-Eval, `--strict-bytes`, pyright-Pre-Commit-ADR,
  SBOM-Scharfschaltung, `tests/integration/compose.yml`,
  `deploy/compose.yml`, ADR-0002-Contract-Anpassung an `hexagon/`).
  Schliesst die Luecke gegenueber `ADR 0001` §4 („Offene Trigger
  bleiben in `open/`").

### Changed

- `spec/lastenheft.md` Version `0.6` → `0.8` (V-Modell-Abschnitt §27,
  §27.1 gegen `architecture.md` verknuepft).
- `spec/lastenheft.md` §27.1 praezisiert: `GG-CC-*`-Zeile in einzelne
  Tabu-Mappings aufgeteilt; `GG-CC-001/005` als Code-Review-Gegenstand
  markiert; neue Zeilen fuer `GG-ACCEPT/DEMO/TRACE/TEST/COV/QG/QA`;
  neuer Unterabschnitt §27.1.1 listet Scope-/Definitions-Anforderungen
  (`GG-TERM/SEED/MVP/NONGOAL/FUTURE`), die bewusst kein Design-Artefakt haben.
- Verweise auf „Roadmap §26" praezisiert: aktive Meilensteine leben
  in `docs/plan/planning/in-progress/roadmap.md`; §26 listet nur
  `GG-FUTURE-*`.
- `README.md` Projektstruktur aktualisiert.
- `GG-AR-OPEN-001`-Beschreibung in `architecture.md` praezisiert:
  betrifft Sprache und Runtime des Simulationskerns, der Adapter
  und der Build-Toolchain; Modulgrenzen aus `GG-AR-P-002` und
  `GG-AR-TABU-001..008` bleiben sprachunabhaengig.
- ADR 0002 Python-Versions-Anker auf den Lebenszyklus-Stand
  vom 2026-05-14 aktualisiert: Minimum-Floor von `3.12+` auf
  `3.13+` gehoben (3.12 ist nur noch Security-Only), Referenz-
  Runtime und Container-Image auf `3.14` gesetzt (Bugfix bis
  2030-10), CI-Matrix laeuft gegen `3.13` und `3.14`. Versions-
  Begruendung als eigener Block in der Option-A-Sektion hinterlegt.
- Retrofit ADR 0004: alle `§…`-Verweise in ADR 0002,
  `lastenheft.md` `GG-TRACE-001`-Tabellen, `architecture.md`
  Rueckverfolgbarkeitstabelle und `roadmap.md` durch
  Kennungs-Verweise ersetzt. Verbleibende `§…`-Eintraege beziehen
  sich nur auf Sektionen ohne eigene Kennung (Testarchitektur in
  `architecture.md`) und sind als Klammer-Lesehilfen gekennzeichnet.
- ruff-Auswahl in ADR 0002 erweitert um Klassen-Ebene-Heuristiken
  und Code-Hygiene: `PLR0902/PLR0903/PLR0904` (SRP/ISP-Signale),
  `PLR0916`/`PLR2004` (Bedingungs- und Magic-Number-Detection),
  `B`/`RET`/`SIM`/`ARG`/`RUF` (Design-Bugs, Kontrollfluss,
  Refaktorisierung), `N` (pep8-naming als Heuristik fuer
  `GG-CC-005`). `[tool.ruff.lint.pylint]` mit
  `max-public-methods=12`, `max-attributes=7`, `max-bool-expr=4`.
  `tests/**`-Per-File-Ignore entsprechend gelockert.
- §27.1-Mapping fuer `GG-PRINC-001..006` in fuenf Einzel-Zeilen
  aufgespalten (SOLID-Prinzipien einzeln zugeordnet zu ruff-Regeln,
  ADR 0005, Architektur-Tabus); `GG-CC-005` von „Code-Review" auf
  ruff `N` plus Code-Review-Rest umgestellt; `GG-CC-001`-Anteil
  bleibt bei ruff (`PLR0915` etc.).
- ADR 0002 `ruff`-Konfiguration um Methodenlaengen-Gate ergaenzt:
  `C901`, `PLR0911`, `PLR0912`, `PLR0913`, `PLR0915` mit
  `max-complexity=10`, `max-statements=30`, `max-branches=12`,
  `max-args=5`, `max-returns=6` — bildet `GG-CC-001`
  Methodenlaengen-Akzeptanzkriterium 1:1 auf ruff ab.
  `tests/**`-Per-File-Ignore um `PLR*`/`C901` erweitert (Tests
  duerfen lang/komplex sein).
- `GG-CC-001` in §27.1 von „Code-Review-Gegenstand" auf
  automatisierten ruff-Check umgestellt; Restanteil bleibt Review.
- `spec/architecture.md` §4.2 Verzeichnisstruktur: `core/` und
  `ports/` zu einer `hexagon/`-Gruppierungsebene zusammengefasst
  (`hexagon/core/{domain,simulation,devices,scenario,replay,faults,agents}`,
  `hexagon/ports/{driving,driven}`). Folge-Updates in derselben
  Datei: Tabu-Familie `GG-AR-TABU-001/002` referenziert
  `hexagon/core/*`; Komponentensicht §5 fuehrt `hexagon/core/*`
  als Modul-Pfade; Prosa-Erwaehnungen `core/devices/battery` und
  `core/agents` umgestellt. ADR-0002-Contracts und Coverage-Pfade
  in `Dockerfile`/`Makefile` referenzieren noch `core.*` —
  Anpassung als Trigger-Watch
  (`docs/plan/planning/open/011-hexagon-layout-adr-0002-realign.md`)
  vor `ADR 0002 Accepted` vorgesehen.
- `spec/architecture.md` §17 Testarchitektur erhaelt die Kennung
  `GG-AR-TEST-001` (gemaess `ADR 0004` §2.2: Sektion ohne Kennung
  bei naechster Beruehrung umstellen). `spec/architecture.md` §18
  Rueckverfolgbarkeitstabelle und `spec/lastenheft.md` §27.1
  Design-Tabelle (neun Zeilen: `GG-TESTTYPE-*`, `GG-ARCHTEST-*`,
  `GG-CICD-*`, `GG-DEMO-*`, `GG-ACCEPT-*`, `GG-TEST-*`, `GG-COV-*`,
  `GG-QG-*`, `GG-QA-*`) verweisen jetzt auf `GG-AR-TEST-001` statt
  „Testarchitektur in `architecture.md` (§17 — noch keine eigene
  Kennung)".
- `spec/architecture.md` §4.2 Verzeichnisstruktur: Hinweis ergaenzt,
  dass sprachspezifische Paketnamen (z. B. `src/grid_gym/...` fuer
  Python) erst mit Acceptance von `ADR 0002` in die
  Verzeichnisstruktur uebernommen werden.
- `spec/architecture.md` §18 SOLID-Zeile (`GG-AR-P-001..014`) um
  Hinweis ergaenzt, dass das Detail-Mapping pro `GG-PRINC-*` in
  `GG-TRACE-001` (`lastenheft.md` §27.1) zu finden ist.
- `spec/lastenheft.md` §27.3 Anforderung-zu-Test um `GG-TRACE-001`
  ergaenzt (Documentation Test — Self-Verification der drei
  Trace-Tabellen; Folgearbeit `tools/check_refs.py`).

### Fixed

- A-2 in ADR 0002: `json.JSONEncoder`-Subklassen-Ansatz konnte
  verschachtelte `Decimal`-Werte nicht serialisieren
  (`json.dumps`/`default()`-Mechanik laesst rohe JSON-Zahlen aus
  `default` nicht zu). Ersetzt durch einen kleinen Custom-Emitter
  (~60 Zeilen, stdlib-only) mit deterministischer Reihenfolge,
  Fixed-Point-`Decimal`-Ausgabe und explizitem `float`-Verbot.
- Lifecycle-Sprache in ADR 0002 an ADR 0006 angeglichen: Vor
  Acceptance scheitert Spike-0 nach `Rejected`; nach Acceptance
  unhaltbare A-1/A-2 fuehren zu `Superseded` durch Nachfolge-ADR
  (nicht „zurueckgezogen", was per ADR 0006 nur als `Withdrawn`
  und nur pre-Beschluss zulaessig waere).
- Spike-0-Vertrag von drei auf vier Gates erweitert
  (`lint-imports`, `ruff check`, `arch_check.py`, `mypy --strict`).
  ADR 0005 ist damit synchroner Bestandteil der Acceptance, nicht
  optionale Folge-Entscheidung.
- ADR 0002 von `Proposed` auf `Provisional` gehoben — die
  Spike-0-Artefakte (`Dockerfile`, `Makefile`) liegen vor und
  bilden den validierten Pfad gemaess ADR 0006. ADR 0005
  ebenfalls auf `Provisional` (synchron). Status-Header beider
  ADRs um `Status geaendert am` und `Letzte inhaltliche Aenderung`
  ergaenzt.
- Dockerfile- und Makefile-Header als Spike-0-Pfad gekennzeichnet
  (ADR 0006).
- `GG-AR-OPEN-001`-Eintrag in `architecture.md` an den neuen
  Provisional-Status angepasst („Vorgeschlagen, Spike-0 laufend",
  Status-Spalte „Offen (Spike-0 laeuft)") gemaess ADR 0006
  Formelhilfe.
- ADR 0003 per `Superseded`-Metadaten auf ADR 0006 umgestellt; der
  historische Entscheidungstext bleibt unveraendert.
- §7 Offene Folge-Punkte in ADR 0002: Kanonische-Serialisierung-
  Eintrag von „Formatdetails verfeinern" auf „Performance-/
  Implementierungs-Alternativen" umgestellt — die Format-Details
  sind durch A-2 jetzt fix, eine Folge-ADR darf nur die
  Umsetzungsroute aendern und muss Byte-Gleichheit nachweisen.
- `Dockerfile` `typecheck`-Stage: `uv run mypy --config-file pyproject.toml`
  ohne Kommandozeilen-Pfade aufgerufen. Die `[tool.mypy] files`-
  Direktive (`ADR 0005` §5.1) ist damit alleinige Single-Source-of-
  Truth fuer den Scope-Vertrag; Kommandozeilen-Pfade haetten die
  Direktive ueberlagert.
