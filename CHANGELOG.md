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
- `docs/plan/adr/0002-language-and-build-stack.md` Pre-Acceptance-
  Schliff (Trigger 011 abgearbeitet, `ADR 0006` §3-konform):
  Repository-Layout in §6.1 auf
  `src/grid_gym/{hexagon/{core,ports},adapters}/` praezisiert;
  alle fuenfzehn A-1 Contracts auf `hexagon.core.*`/`hexagon.ports.*`
  umgestellt (AC-CORE-NO-ADAPTERS/CORE-NO-DRIVING/PORTS-NO-OUT/
  PORTS-NO-FW/ADAPTER-PURE/ADAPTER-LIGHTWEIGHT/NO-FW/NO-IO-MOD/
  NO-CYCLES/NO-TIME/NO-RAND/NO-JSON/DOMAIN-FROZEN/NO-GOD-UTILS/
  TYPED-ERRORS); AC-NO-JSON-Whitelist und
  `[tool.grid_gym.arch_check]` `json-dumps-whitelist`-Pfad auf
  `src/grid_gym/hexagon/core/serialization/canonical.py`;
  Spike-0-Skelett-Pfad und A-2 Custom-Emitter-Verweise auf
  `grid_gym.hexagon.core.serialization.canonical`. Header
  `Letzte inhaltliche Aenderung` auf 2026-05-15 aktualisiert.
- `Dockerfile` `coverage-gate-critical`: vier `--cov=`-Pfade
  auf `src/grid_gym/hexagon/core/{simulation,devices/battery,scenario,replay}`
  umgestellt (downstream zu Trigger 011).
- `docs/plan/planning/`: Trigger
  `011-hexagon-layout-adr-0002-realign.md` von `open/` nach
  `done/` verschoben (Closure-Notiz mit Lieferumfang); `open/`-
  und `done/`-README-Bestandstabellen entsprechend gepflegt.
- `docs/plan/planning/next/spike-0.md` — Slice-Plan fuer Spike-0
  als Pre-Acceptance-Pflichtnachweis fuer `ADR 0002` und
  `ADR 0005`. Fuenf Wellen (Toolchain/Skelett, A-2 Custom-Emitter,
  `tools/arch_check.py` Contracts, 16 Verstoss-Branches,
  Acceptance-Hebung); Erfolgskriterien, Out-of-Scope-Liste,
  Risiken/Fallback und Verifikationspfad explizit ausgewiesen.
  `docs/plan/planning/next/README.md` Bestandstabelle ergaenzt.
- `docs/plan/planning/in-progress/roadmap.md` §4 Vorbedingungen
  praezisiert: `GG-AR-OPEN-001` verweist auf `next/spike-0.md`;
  Repository-Layout-Punkt verweist auf `hexagon/`-Gruppierung in
  `architecture.md` §4.2.
- **Spike-0 Welle 1** — Toolchain und Skelett:
  - `pyproject.toml` mit `[project]`, `[build-system]`
    (hatchling), `[dependency-groups]` (lint/arch/typecheck/
    test/audit/dev), `[tool.ruff.lint]` mit A-1-Regeln und
    Preview-Mode (`PLR0904`/`PLR0916` brauchen Preview in ruff
    0.15), `[tool.ruff.lint.flake8-tidy-imports]`,
    `[tool.ruff.lint.per-file-ignores]`,
    `[tool.ruff.lint.mccabe]`, `[tool.ruff.lint.pylint]`,
    `[tool.mypy]` `strict = true` mit Scope `files = ["src/grid_gym", "tools"]`,
    `[tool.importlinter]` mit `include_external_packages = true`
    und sieben Forbidden-Contracts (AC-CORE-NO-ADAPTERS,
    AC-CORE-NO-DRIVING, AC-PORTS-NO-OUT, AC-PORTS-NO-FW,
    AC-ADAPTER-PURE, AC-NO-FW, AC-NO-IO-MOD),
    `[tool.grid_gym.arch_check]` mit Whitelists,
    `[tool.pytest.ini_options]` mit Markern (`determinism`,
    `replay`, `fault`), `[tool.coverage.*]`.
  - `.python-version` → `3.14`.
  - `uv.lock` mit 65 Packages, alle aktuelle Versionen
    (ruff 0.15.13, mypy 2.1.0, import-linter 2.11, grimp 3.14,
    pytest 9.0.3, pytest-cov 7.1.0, hypothesis 6.152.7,
    pip-audit 2.10.0, openapi-spec-validator 0.8.5).
  - Skelett: `src/grid_gym/__init__.py` plus
    `hexagon/{__init__.py,core/{__init__.py,errors.py,
    domain,simulation,devices,scenario,replay,faults,agents,
    serialization}/__init__.py,ports/{driving,driven}/__init__.py}`
    und `adapters/{__init__.py,driving/__init__.py,driven/__init__.py}`.
    Sub-Pakete `domain..serialization` sind als leere Module
    angelegt, damit import-linter sie als Modulreferenz aufloesen
    kann.
  - `hexagon/core/errors.py` mit `GridGymError(Exception)` als
    Wurzel-Fehlerklasse (AC-TYPED-ERRORS, GG-CC-008).
  - `tools/arch_check.py` als ausfuehrbares Skelett (laedt
    `[tool.grid_gym.arch_check]` aus `pyproject.toml`, baut
    Import-Graph via `grimp`, gibt Zusammenfassung aus —
    Contract-Logik kommt in Welle 3).
  - `tests/__init__.py`, `tests/unit/__init__.py`,
    `tests/arch/__init__.py` plus
    `tests/unit/test_skeleton.py` mit zwei Smoke-Tests fuer
    `GridGymError`.
  - **Gate-Verifikation (alle gruen via Dockerfile-Stage):**
    `make lint` (ruff check, 23 files), `make format-check`
    (23 files), `make typecheck` (mypy --strict, 19 source
    files, 0 issues), `make arch-check` (7 Contracts kept),
    `make test-unit` (2 tests passed), `make dep-audit`
    (0 vulnerabilities in 65 packages).
- `Dockerfile` `source`-Stage: `COPY LICENSE README.md ./`
  ergaenzt — hatchling braucht beide fuer den editable Install
  im `uv sync --frozen --all-groups`.
- `Makefile` `lock-refresh`: Bug behoben. Das distroless
  `ghcr.io/astral-sh/uv:VERSION`-Image hat `/uv` als ENTRYPOINT
  und keine Shell — `uv lock` schlug mit ELF-Interpreter-Fehler
  fehl. Jetzt laeuft `lock-refresh` im projekteigenen
  `base`-Stage (python:3.14-slim + uv 0.5.31 gepinnt) als
  aktueller User (`--user $(id -u):$(id -g)` plus
  `UV_CACHE_DIR=/tmp/uv-cache`), produziert `uv.lock` mit
  korrekter User-Ownership.
- `docs/plan/planning/next/spike-0.md` Welle 3: neuer Contract
  `AC-HEXAGON-PURE` aufgenommen (Whitelist-basiert via
  `tools/arch_check.py`: Module unter `src/grid_gym/hexagon/**`
  duerfen nur stdlib, `grid_gym.*` und explizit whitelistete
  Dritt-Pakete (z. B. `pydantic` fuer `FrozenModel`)
  importieren — ersetzt brueckhafte Blacklist-Pflege in
  `AC-NO-FW` durch robuste Positive-Liste).
- `.gitignore` erweitert um Python-Build-/Test-Artefakte
  (`.venv/`, `__pycache__/`, `*.egg-info/`, `.pytest_cache/`,
  `.ruff_cache/`, `.mypy_cache/`, `coverage/`, `.hypothesis/`),
  Build-Output (`build/`, `dist/`) und IDE-Dateien
  (`.idea/`, `.vscode/`, `*.swp`). Projekt-Policy ist
  Docker-only — lokale Python-Umgebungen sollen nicht entstehen;
  die Eintraege fangen versehentliche Artefakte ab.
- `.dockerignore` neu angelegt. Reduziert den Build-Kontext auf
  die tatsaechlich per `COPY` referenzierten Pfade
  (`pyproject.toml`, `uv.lock`, `.python-version`, `src/`,
  `tests/`, `tools/`, `spec/`, `LICENSE`, `README.md`).
  Schliesst `.git/`, `.github/`, `docs/`, Editor-/IDE-Dateien,
  alle Python-Caches und die Projekt-Agent-Verzeichnisse aus.
  Beschleunigt jeden `docker build`-Aufruf und stabilisiert
  den Layer-Cache.
- **Spike-0 Welle 2** — A-2 Custom-Emitter + Property-Tests:
  - `src/grid_gym/hexagon/core/serialization/canonical.py` mit
    `canonical_json(value: object) -> bytes` nach ADR 0002 §A-2
    Punkt 3 (stdlib-only Custom-Emitter, kein `json.dumps`).
    Eigenschaften: lexikographisch sortierte Dict-Keys,
    Fixed-Point-Notation fuer `Decimal` (`format(d, "f")`,
    Tail-Nullen bleiben erhalten), RFC-8259-konformes
    String-Escape (Steuerzeichen als `\\u00XX`), UTF-8-Bytes
    als Ergebnistyp.
  - Vier typisierte Fehlerklassen (AC-TYPED-ERRORS-konform,
    TRY003-clean): `CanonicalSerializationError` als Wurzel
    (erbt von `GridGymError`), `FloatNotAllowedError`,
    `NonFiniteDecimalError` (NaN/Infinity),
    `NonStringDictKeyError`, `UnsupportedTypeError(type_name)`.
  - `tests/unit/hexagon/core/serialization/test_canonical.py`
    mit 42 Tests: Basis-Typen (None/bool/int/str/list/dict),
    Decimal-Verhalten, Fehler-Faelle, sechs `hypothesis`-
    Property-Tests (Fixed-Point-Equivalence, Dict-Reihenfolge-
    Unabhaengigkeit, String-Roundtrip via `json.loads`,
    Listen-Laenge, Integer-Roundtrip, Decimal-in-Dict),
    Domain-Skizzen fuer Telemetry/Command/Event mit Roundtrip-
    Byte-Stabilitaet.
  - Test-Package-Skelett (`tests/unit/hexagon/__init__.py`,
    `tests/unit/hexagon/core/__init__.py`,
    `tests/unit/hexagon/core/serialization/__init__.py`).
  - **Gate-Verifikation:**
    - `make test-unit`: 44 tests passed (2 Skelett + 42 canonical).
    - `make coverage-gate-critical CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/serialization`:
      100 % Line + Branch auf 79 Statements / 38 Branches.
    - `make coverage-gate`: 100 % Branch auf `src/grid_gym`.
    - Regression: `make lint`, `make typecheck`, `make arch-check`
      bleiben gruen.
- `Dockerfile` `coverage-gate-critical`-Stage parametrisiert: neuer
  `ARG CRITICAL_COV_TARGETS` (Default: kritische Domain laut
  GG-COV-003 — `simulation`/`devices/battery`/`scenario`/`replay`),
  ueberschreibbar via `--build-arg` fuer Wellen mit Teilbereich.
  Shell-Loop expandiert die leerzeichengetrennte Liste zu
  `--cov=`-Argumenten fuer pytest.
- `Makefile` `coverage-gate-critical`-Target reicht
  `CRITICAL_COV_TARGETS` als optionalen Build-Arg-Override durch
  (`make coverage-gate-critical CRITICAL_COV_TARGETS=...`).
- `docs/plan/planning/next/spike-0-results.md` als Living Document
  fuer Spike-0 angelegt: Welle-Status, Verstoss-Branch × Gate
  Matrix (sechzehn Branches), Befunde aus Welle 1+2 (uv-Image-
  Eigenheiten, hatchling-LICENSE/README-Bedarf, ruff-0.15-Drift
  gegenueber ADR 0002 §A-1, import-linter-Subpaket-Limit,
  coverage-gate Build-Arg-Parametrisierung) und Drift-Liste fuer
  den finalen ADR-Schliff vor Acceptance.
- **Spike-0 Welle 4** — Verstoss-Verifikation (18 von 18 Contracts mit
  Zaehnen): pro Contract eine Violation auf `main` eingebaut, das
  erwartete Gate als rot bestaetigt, Violation sauber zurueckgerollt.
  Matrix in `docs/plan/planning/next/spike-0-results.md` §3 vollstaendig.
  Verify-and-revert ohne persistente Branches (Stay-on-Main-Policy).
  - 5 Contracts via `import-linter` (`AC-CORE-NO-ADAPTERS`,
    `AC-CORE-NO-DRIVING`, `AC-PORTS-NO-OUT`, `AC-PORTS-NO-FW`,
    `AC-ADAPTER-PURE`, `AC-NO-FW`, `AC-NO-IO-MOD` top-level).
  - 11 Contracts via `tools/arch_check.py` (`AC-HEXAGON-PURE`,
    `AC-NO-IO-MOD` nested, `AC-ADAPTER-LIGHTWEIGHT`, `AC-NO-CYCLES`,
    `AC-NO-TIME`, `AC-NO-RAND`, `AC-NO-JSON`, `AC-DOMAIN-FROZEN`,
    `AC-NO-GOD-UTILS`, `AC-TYPED-ERRORS` (Tuple-Form bestaetigt
    Welle-3-Fix B-3)).
  - 1 Contract via `mypy --strict` (LSP variance: `[override]` +
    `[explicit-override]` bei Return-Typ-Erweiterung `int` → `object`).
  - `AC-NO-CYCLES` Dedup-Mechanik aus dem B-2-Fix bestaetigt: ein
    2-Modul-Zyklus erzeugt eine einzige Violation, nicht zwei.
- **Coverage-Gate Negativ-Verifikation (Welle 2):**
  - **pytest-cov-Schiene** (`--cov-fail-under=90`, kombiniert):
    bewusst eingefuegte ungetestete Funktion drueckte Coverage
    auf 79.73 %, Stage rot mit `FAIL Required test coverage of
    90% not reached`. Nach Revert wieder 100 %, working tree clean.
  - **XML-Branch-Schiene** in Isolation: synthetische
    `coverage-critical.xml` mit `branch-rate="0.5"` an die
    Python-Check-Logik des Dockerfile-Stages gefuettert; meldet
    `50.00% < 90.00%`, exit 1. Sanity mit `branch-rate="0.95"`:
    exit 0.
  - **Erkenntnis:** coverage.py mit `--cov-branch` decomposiert
    one-line `if cond: body` nicht in separate Branch-Arcs;
    Statement-Level-Branches fuehren immer dazu, dass Line- und
    Branch-Coverage zusammen fallen. Damit feuert pytest-cov's
    kombinierter Check vor dem XML-Branch-Check. Die XML-Schiene
    ist defense-in-depth, nicht Hauptgate. Befund dokumentiert
    in `spike-0-results.md` §4.2.
- **Spike-0 Welle 3** — `tools/arch_check.py` Contract-Implementierung:
  - Framework: `Violation`-Datentyp (`@dataclass(frozen=True, slots=True)`),
    `ArchCheckConfig` aus `[tool.grid_gym.arch_check]` in
    `pyproject.toml`, AST-Walker, stderr-Output im Format
    `{contract_id}\\t{location}\\t{detail}`, Exit-Code 0/1.
  - Neun Contracts implementiert, die `import-linter` und `ruff`
    nicht abdecken:
    - **`AC-HEXAGON-PURE`** (Whitelist): Module unter
      `src/grid_gym/hexagon/**` duerfen nur stdlib (via
      `sys.stdlib_module_names`), `grid_gym.*` und explizit
      whitelistete Dritt-Pakete (`hexagon-import-whitelist` in
      `[tool.grid_gym.arch_check]`) importieren.
    - **`AC-NO-JSON`**: `json.dumps`/`json.dump`-Aufrufe ausserhalb
      der `json-dumps-whitelist` (heute nur
      `hexagon/core/serialization/canonical.py`).
    - **`AC-NO-TIME`** (Aufruf-Site): `time.time`/`time.monotonic`/
      `time.perf_counter`/`time.perf_counter_ns`/`time.process_time`
      unter `hexagon/core/**`.
    - **`AC-NO-RAND`** (Aufruf-Site): `random.*`/`secrets.*`/
      `numpy.random.*` unter `hexagon/core/**`.
    - **`AC-DOMAIN-FROZEN`**: Klassen in `hexagon/core/domain/**`
      (plus `domain-frozen-extra`) muessen
      `@dataclass(frozen=True, ...)` oder von `FrozenModel` erben.
    - **`AC-NO-GOD-UTILS`**: Modul-Namen (`*_utils.py`, `helpers.py`,
      `common.py`, `misc.py`), Klassen-Namens-Suffixe
      (`Utils`/`Helper`/`Manager`/`Misc`), max. 5 oeffentliche
      Top-Level-Funktionen ausserhalb `hexagon/core/domain` und
      `hexagon/core/serialization`.
    - **`AC-TYPED-ERRORS`**: kein `raise Exception(...)` /
      `raise BaseException(...)`; `except Exception:` nur in
      `typed-errors-exempt`-Pfaden.
    - **`AC-NO-CYCLES`**: Importzyklen via `grimp.build_graph`
      und `find_shortest_chain`-Rueckpfaden zwischen direkten
      Import-Paaren.
    - **`AC-ADAPTER-LIGHTWEIGHT`**: zyklomatische Komplexitaet
      `<= 8` fuer Funktionen unter
      `adapters/driven/protocol_*`/`persistence_*` und
      `adapters/driving/**`.
  - `[tool.grid_gym.arch_check]` um `hexagon-import-whitelist`
    erweitert.
  - **Gate-Verifikation (alle gruen via Dockerfile-Stages + make):**
    - `make arch-check`: 7 import-linter Contracts kept,
      arch_check.py meldet „all contracts kept" (9 AST-/grimp-
      Contracts gruen).
    - `make lint`/`format-check`/`typecheck`: Regression gruen
      (mypy --strict, 21 source files).
    - `make test-unit`: 44 tests passed.
    - `make coverage-gate-critical CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/serialization`:
      100 % Line + Branch.
- `tests/unit/hexagon/core/serialization/test_canonical.py`:
  Float-Equality-Vergleiche auf `pytest.approx` umgestellt
  (`RUF069`-Compliance unter ruff 0.15 preview-Mode).

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
