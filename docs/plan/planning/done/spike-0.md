# Slice-Plan — Spike-0 (Pre-Acceptance fuer ADR 0002 + ADR 0005)

**Status:** Done (geschlossen 2026-05-15)
**Datum:** 2026-05-15
**Bezug:** [`ADR 0002`](../../adr/0002-language-and-build-stack.md)
§A-1/§A-2 (`Accepted` 2026-05-15),
[`ADR 0005`](../../adr/0005-type-check-gate.md) (`Accepted` 2026-05-15),
[`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md)
§2 (Lifecycle-Tabelle, `Provisional → Accepted` erreicht),
[`roadmap.md`](../in-progress/roadmap.md) §4 Vorbedingungen 1+3 abgehakt.

---

## 0. Closure-Notiz (2026-05-15)

Spike-0 ist komplett. Alle fuenf Wellen abgeschlossen, alle
Pflicht-Gates gruen, beide ADRs (`ADR 0002` und `ADR 0005`) per
`Provisional → Accepted` gehoben. Per `ADR 0006` §3 sind die
ADR-Entscheidungstexte ab jetzt immutable; Aenderungen an den
A-1-/A-2-Vertraegen oder am mypy-Strict-Gate erfordern Nachfolge-ADRs.

### Welle-Tabelle

| Welle | Liefergegenstand | Commit |
| ----- | ---------------- | ------ |
| 1 — Toolchain + Skelett | `pyproject.toml`, `uv.lock`, `.python-version`, `src/grid_gym/{hexagon/{core,ports},adapters}/`, `tools/arch_check.py`-Skelett, Smoke-Test (44 Tests) | `cb2246a` |
| 2 — A-2 Custom-Emitter | `hexagon/core/serialization/canonical.py` (Property-Tests, Coverage 100 %) | `5298a0c` |
| 3 — `tools/arch_check.py` Contracts | 10 Architektur-Contracts (AC-HEXAGON-PURE bis AC-TYPED-ERRORS), erster Review (`aed2189` + Fixes `9d7a3fb`/`d0c8559`/`facd9aa`/`0e11ca8`) | `aed2189` |
| 4 — Verstoss-Verifikation | 18-fuer-18 Verstoss-Branches verify-and-revert auf main; Matrix in `spike-0-results.md §3` | `96eb8b5` |
| 5 — Acceptance-Hebung | Pre-Acceptance-Review (`fb90154`/`201daee`/`658c037`/`46b4ce6`), ADR Provisional → Accepted, Headers auf verbindlichen Stack, Move nach done/ | `5763445` / `3645473` / `522ec17` / (dieser Commit) |

### Lastenheft-IDs geschlossen

- `GG-AR-OPEN-001` — Sprach- und Build-Wahl. `spec/architecture.md`
  §19 traegt jetzt „Geschlossen mit `ADR 0002`".
- `roadmap.md` §4 Vorbedingung 1 (`GG-AR-OPEN-001`) und Vorbedingung 3
  (initiales Repository-Layout) abgehakt.

### Verweise auf Detail-Records

- **Verstoss × Gate Matrix**: `spike-0-results.md §3` (alle 18
  Verifikationen mit Test-Pattern und Violation-Detail).
- **Befunde Welle 1+2**: `spike-0-results.md §4` (uv-Image-Eigenheiten,
  hatchling, ruff-0.15-Drift, import-linter-Subpaket-Limit,
  Coverage-Gate-Schienen-Verifikation, Build-Arg-Parametrisierung).
- **Review-Trail**: `spike-0-results.md §6` (zwei unabhaengige Reviews
  durch `code-reviewer`-Subagent: erster Review nach Welle 3 mit
  4 Blockern, zweiter Review vor Welle 5 mit 3 weiteren Blockern und
  10 Drift-Items).

### Drift-Items eingearbeitet (D-1..D-10)

Alle zehn Items aus dem zweiten Review wurden vor Welle 5 in
ADR 0002 (§A-1/§A-2/§6.1) und ADR 0005 (§5.1) eingearbeitet —
detaillierte Liste in `spike-0-results.md §5`.

### Was bleibt offen

- **`GG-AR-OPEN-002`** (API/Simulation Prozess-Wahl) — eigene
  Folge-ADR.
- **`GG-AR-OPEN-003..010`** — unveraendert offen.
- **Triggers in `docs/plan/planning/open/`**:
  - `001-code-review-doc.md` (vor erster Adapter-PR)
  - `002-check-refs-tool.md` (bei Querverweis-Drift)
  - `003-random-port-adr.md` (mit erstem Domain-Slice)
  - `004-canonical-encoder-alternative-adr.md` (bei Perf-Druck)
  - `005-pyright-vs-mypy-reeval.md` (bei Generic-Protocols)
  - `006-mypy-strict-bytes.md` (nach `GG-DATA-005`-Konsolidierung)
  - `007-pyright-precommit-adr.md` (bei Editor-Parity-Druck)
  - `008-sbom-activation.md` (mit erster Release)
  - `009-tests-integration-compose.md` (mit erstem Persistenz-Adapter)
  - `010-deploy-compose.md` (mit erstem Deploy-Slice)
- **Welle-6+/Cosmetic-Items** aus den beiden Reviews
  (`spike-0-results.md §4.2`, §6.2): nicht-blockierend; werden bei
  Beruehrung der jeweiligen Bereiche mitgezogen.
- **`make fullbuild`** als End-to-End-Gate: M1-Abnahmebedingung, nicht
  Spike-0-Abschluss (`openapi-validate`/`image-audit`/`runtime`-Stages
  brauchen FastAPI-App und Compose-Files).

### Abschluss-Gate

`make gates` (Aggregator: `lint`, `format-check`, `typecheck`,
`arch-check`, `test-unit`, `coverage-gate`, `coverage-gate-critical`
mit `CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/serialization`,
`dep-audit`) lief gruen auf `main` (Status Stand des letzten
Welle-5-Commits — siehe `CHANGELOG.md` Unreleased-Sektion fuer den
finalen Lauf-Hash).

---

## Historischer Slice-Plan (Stand Welle 4)

Der nachfolgende Originaltext stammt aus der Planungsphase (Stand
nach Welle 4) und ist historisch erhalten. Massgeblich ist die
Closure-Notiz oben sowie `spike-0-results.md`.

---

## 1. Zweck

Spike-0 ist der Pre-Acceptance-Pflichtnachweis fuer `ADR 0002` und
synchron `ADR 0005`. Er konfiguriert das leere Skelett so, dass die
vier A-1-Gates und das ADR-0005-Type-Check-Gate auf `main` gruen
laufen und je Contract mindestens ein bewusst eingefuegter Verstoss
in einem Test-Branch rot wird.

Liefergegenstaende dieser Slice (Spike-0) sind operativ
(`Spike`/`Prototyp`-Artefakte gemaess `ADR 0006` §5,
Provisional-Stufe). Sie werden mit Acceptance von `ADR 0002` zur
verbindlichen Projektkonvention.

## 2. Erfolgskriterien (aus ADR 0002 Spike-0-Vertrag)

**Operatives Grundprinzip:** Alle Gates und Tests laufen ueber das
Multi-Stage-`Dockerfile` (Stages `lint`, `format-check`, `typecheck`,
`arch-check-imports`, `arch-check-custom`, `test-unit`, `coverage-gate`,
…), angesprochen ueber die `Makefile`-Targets (`make lint`,
`make typecheck`, `make arch-check`, `make gates`). Lokale `uv run`-
Aufrufe sind nur fuer Entwickler-Diagnose erlaubt; der **Gate-Vertrag
ist die Dockerfile-Stage**. CI ruft `make gates` (Pflicht-Gates) und
`make ci` (Pflicht-Gates + Integration + OpenAPI + Image-Audit) auf.

Spike-0 ist erfolgreich, wenn:

1. Alle vier A-1-Pflicht-Gates auf `main` gruen sind, jeweils als
   Dockerfile-Stage gebaut:
   - `make arch-check-imports` → Stage `arch-check-imports`
     (`uv run lint-imports`)
   - `make lint` → Stage `lint` (`uv run ruff check --no-cache`)
   - `make arch-check-custom` → Stage `arch-check-custom`
     (`uv run python tools/arch_check.py`)
   - `make typecheck` → Stage `typecheck`
     (`uv run mypy --config-file pyproject.toml`, ADR 0005)
   `make gates` aggregiert diese plus `format-check`, `test-unit`,
   `coverage-gate`, `coverage-gate-critical`, `dep-audit` und ist
   die Single-Source-of-Truth fuer den lokalen Gruen-Lauf.
2. Pro A-1-Contract (15) und pro `mypy --strict`-LSP-Beispiel (1)
   existiert ein separater Branch mit bewusst eingefuegtem Verstoss,
   in dem genau das erwartete Gate rot wird und kein anderes
   (gepruft via `make <gate>` und `make gates` pro Branch).
3. `make lint` akzeptiert die `[tool.ruff.lint.flake8-tidy-imports]`-
   Konfiguration ohne Warnung (Versions-Sanity-Check fuer die in
   ADR 0002 §A-1 dokumentierten Schluessel; ruff laeuft im
   Dockerfile-Stage `lint` mit `--no-cache`).

## 3. Liefer-Reihenfolge

Wellen sind atomar; jede Welle endet mit einem gruenen Lauf der
bis dahin aktiven Gates.

### Welle 1 — Toolchain und Skelett (Tag 1)

- `pyproject.toml` mit `[project]`, `[tool.uv]`,
  `[dependency-groups]` (`dev`, `test`, `lint`, `audit`,
  `typecheck`), `[tool.ruff.lint]` (A-1-Regelgruppen),
  `[tool.ruff.lint.flake8-tidy-imports]`,
  `[tool.ruff.lint.per-file-ignores]`,
  `[tool.ruff.lint.mccabe]`, `[tool.ruff.lint.pylint]`,
  `[tool.mypy]` (`strict = true`, `files`,
  `enable_error_code`), `[tool.importlinter]`
  (Layer-Contracts), `[tool.grid_gym.arch_check]`
  (Whitelists).
- `.python-version` → `3.14`.
- `uv.lock` durch `make lock-refresh`.
- Skelett: `src/grid_gym/{hexagon/{core,ports},adapters}/`
  mit leeren `__init__.py`-Dateien und einem minimalen
  `hexagon/core/errors.py` (`class GridGymError(Exception): ...`).
- `tools/arch_check.py` als ausfuehrbares Skelett (parsed `grimp`,
  liest `[tool.grid_gym.arch_check]`, gibt heute nur „OK" zurueck
  — Contract-Logik kommt in Welle 3).
- `tests/unit/__init__.py` plus `tests/arch/__init__.py`.
- **Gate-Status nach Welle 1** (alle ueber Dockerfile-Stages, via
  `make <target>`): `make lint`, `make format-check`,
  `make typecheck` (auf leerem Skelett trivial gruen),
  `make arch-check-imports` (keine Module → ok),
  `make arch-check-custom` (Skelett-OK). `make gates` als
  Aggregator-Lauf am Ende der Welle gruen.

### Welle 2 — A-2 Custom-Emitter + Property-Tests (Tag 2)

- `src/grid_gym/hexagon/core/serialization/canonical.py`:
  - `canonical_json(value) -> bytes` exakt nach ADR 0002 §A-2
    Punkt 3 (Custom-Emitter).
  - `CanonicalSerializationError` Domain-Fehler erbt von
    `GridGymError`.
- `tests/unit/hexagon/core/serialization/test_canonical.py`:
  - `hypothesis`-Property-Tests fuer
    - Decimal-Roundtrip (Fixed-Point-Notation, Tail-Nullen),
    - dict-Reihenfolge unabhaengig von Insertion-Order,
    - NaN/Infinity → `CanonicalSerializationError`,
    - `float`-Eingabe → `CanonicalSerializationError`,
    - Roundtrip Lesen → Schreiben byte-stabil fuer
      `Telemetry`/`Command`/`Event`-Domain-Skizzen.
- **Gate-Status nach Welle 2:** `make test-unit` (Dockerfile-Stage
  `test-unit`) gruen; `make coverage-gate` / `make coverage-gate-critical`
  (Dockerfile-Stages, mit Build-Arg-Scope auf
  `src/grid_gym/hexagon/core/serialization`, 90 % Line + Branch).

### Welle 3 — `tools/arch_check.py` Contract-Implementierung (Tag 3)

Implementiert die acht Contracts, die nicht von `import-linter`
oder `ruff` allein abgedeckt sind:

- AC-HEXAGON-PURE (Whitelist-basiert: jedes Modul unter
  `src/grid_gym/hexagon/**` darf NUR stdlib, `grid_gym.*` und
  explizit whitelistete Dritt-Pakete (z. B. `pydantic` fuer
  `FrozenModel`) importieren. Jedes andere `import X`/
  `from X import Y` ist ein Verstoss. Whitelist liegt in
  `[tool.grid_gym.arch_check] hexagon-import-whitelist`),
- AC-NO-CYCLES (SCC via `grimp`),
- AC-NO-TIME (Aufruf-Sites von `time.time`/`time.monotonic`/
  `time.perf_counter`/`time.process_time`/
  `asyncio.get_event_loop().time` in `hexagon.core.*`),
- AC-NO-RAND (Aufruf-Sites in `hexagon.core.*`),
- AC-NO-JSON (`json.dumps`/`json.dump`-Aufrufe ausserhalb
  `src/grid_gym/hexagon/core/serialization/canonical.py`),
- AC-DOMAIN-FROZEN (Klassen in `hexagon.core.domain.*` immutable),
- AC-NO-GOD-UTILS (Modul-/Klassen-Namens-Heuristik plus 5+ freie
  Funktionen ausserhalb `hexagon.core.{domain,serialization}`),
- AC-TYPED-ERRORS (Domain-/Application-Fehler erben von
  `hexagon.core.errors.GridGymError`),
- AC-ADAPTER-LIGHTWEIGHT (zyklomatische Komplexitaet 8,
  Domain-Enum-Branches, arithmetische Operationen auf
  Telemetriewerten).

Output-Format: `{contract_id} {module_or_symbol} {reason}` pro
Verstoss; Exit-Code 0/1.

- **Gate-Status nach Welle 3:** `make arch-check-custom` (Dockerfile-
  Stage `arch-check-custom`) gruen, weil das Skelett die Contracts
  nicht verletzt. `make arch-check` (Aggregator-Stage:
  `lint-imports` + `arch_check.py`) ebenfalls gruen. `make gates`
  Re-Run zur Sicherheit.

### Welle 4 — Verstoss-Branches (Tag 4)

Pro Contract ein eigener Branch `spike0/contract/{ID}` mit genau
einem absichtlich eingefuegten Verstoss. Erwartung:

- der zugeordnete Gate wird rot,
- keine anderen Gates werden rot.

Branch-Liste:

- `spike0/contract/AC-HEXAGON-PURE`
- `spike0/contract/AC-CORE-NO-ADAPTERS`
- `spike0/contract/AC-CORE-NO-DRIVING`
- `spike0/contract/AC-PORTS-NO-OUT`
- `spike0/contract/AC-PORTS-NO-FW`
- `spike0/contract/AC-ADAPTER-PURE`
- `spike0/contract/AC-ADAPTER-LIGHTWEIGHT`
- `spike0/contract/AC-NO-FW`
- `spike0/contract/AC-NO-IO-MOD`
- `spike0/contract/AC-NO-CYCLES`
- `spike0/contract/AC-NO-TIME`
- `spike0/contract/AC-NO-RAND`
- `spike0/contract/AC-NO-JSON`
- `spike0/contract/AC-DOMAIN-FROZEN`
- `spike0/contract/AC-NO-GOD-UTILS`
- `spike0/contract/AC-TYPED-ERRORS`
- `spike0/lsp-variance` (LSP-/Protocol-Variance-Verstoss fuer
  `mypy --strict`, ADR 0005 §4a)

CI-Setup ruft pro Branch `make gates` (Aggregator ueber alle
Dockerfile-Pflicht-Stages) auf. Erwartete Branch × Gate Matrix wird
in `docs/plan/planning/next/spike-0-results.md` dokumentiert (siehe
Welle 5). Pro Verstoss-Branch wird zusaetzlich der spezifische
`make <gate>`-Aufruf protokolliert, um zu zeigen, dass genau dieses
Gate rot wird und kein anderes.

### Welle 5 — Spike-0-Abschluss, Acceptance-Hebung (Tag 5)

- `docs/plan/planning/next/spike-0-results.md` mit Gate-Status
  pro Branch (Pflicht-Artefakt fuer Acceptance-Entscheidung).
- `ADR 0002` Statuswechsel: `Provisional → Accepted`,
  `Status geaendert am: 2026-05-XX`.
- `ADR 0005` Statuswechsel: `Provisional → Accepted` (synchron).
- `spec/architecture.md` §19: `GG-AR-OPEN-001`-Eintrag schliessen
  („Geschlossen mit `ADR 0002`").
- `docs/plan/planning/in-progress/roadmap.md` §4 Vorbedingung 1
  (`GG-AR-OPEN-001`) abgehakt; §4 Vorbedingung 3 (initiales
  Repository-Layout) ebenfalls (durch `ADR 0002` §6.1 verbindlich
  fixiert). §3 M1-Lieferziel folgt aus dem ersten Domain-Slice;
  §4 Vorbedingung 2 (`GG-AR-OPEN-002` API/Simulation Prozess-Wahl)
  bleibt offen — eigene Folge-ADR.
- Closure-Notiz `docs/plan/planning/done/spike-0.md` mit
  Welle-1..5-Tabelle (Commit-Verweise), Verweis auf 18-Contract-
  Matrix in `next/spike-0-results.md §3` (Living Document bleibt
  referenziell), Befunde-Verweis auf §4 und §6, Drift-Items-
  Eingearbeitet-Liste, „was bleibt offen" (Triggers 009/010,
  M1-Vorbereitungen).
- `Dockerfile`-, `Makefile`- **und `pyproject.toml`**-Header von
  „Spike-0-Pfad" auf „verbindlicher Stack gemaess `ADR 0002
  Accepted`" umstellen.
- **Abschluss-Gate:** `make gates` (Aggregator ueber Pflicht-Gates
  `lint`, `format-check`, `typecheck`, `arch-check`, `test-unit`,
  `coverage-gate`, `coverage-gate-critical` mit
  `CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/serialization`,
  `dep-audit`) gruen ist die Spike-0-Acceptance-Bedingung. Das
  ehemals geplante `make fullbuild` (CI + Runtime-Image-Build +
  Compose-Smoke) erfordert die FastAPI-`http_api`-App
  (`openapi-validate`/`image-audit`/`runtime`-Stages) und
  `deploy/compose.yml` / `tests/integration/compose.yml`, die alle
  M1-Slice-Artefakte sind (Triggers 009/010 in `open/`). `make
  fullbuild` ist deshalb **M1-Abnahmebedingung**, nicht
  Spike-0-Abschluss.

## 4. Out-of-Scope (bleibt fuer spaetere Slices)

- Echte Domain-Logik (Tick-Loop, Scheduler, Geraetemodelle) — kommt
  ab M1-Slice 2.
- `RandomPort`/`ClockPort`-Implementierungen (Folge-ADR
  `003-random-port-adr` in `open/`).
- API-Slice (FastAPI), Persistenz-Slice (PostgreSQL/Alembic),
  UI-Slice — alle nach Spike-0.
- `tests/integration/compose.yml` und `deploy/compose.yml`
  (Trigger 009 und 010 in `open/`).
- `docs/user/code-review.md` + PR-Template (Trigger 001 in
  `open/`); spaetestens vor der ersten Adapter-PR.
- SBOM-Scharfschaltung (Trigger 008 in `open/`).

## 5. Risiken und Fallback

- **AST-Heuristik in `tools/arch_check.py` faengt nicht alles**:
  Fallback ist die explizite Reststeuerung via Code-Review
  (Trigger 001). Spike-0 muss zeigen, dass die Heuristik den
  bewussten Verstoss faengt — nicht, dass sie jede denkbare
  Variante abdeckt.
- **`mypy --strict` LSP-Beispiel reagiert nicht zuverlaessig rot**:
  Dann scheitert ADR 0005 (`Provisional → Rejected`); eine
  Folge-ADR mit `pyright --strict` tritt an die Stelle. `ADR 0002`
  selbst bleibt davon unberuehrt.
- **`grimp`-SCC-Analyse produziert falsche Positive auf leerem
  Skelett**: Dann muss `tools/arch_check.py` einen Mindest-Modul-
  Schwellwert haben (nur SCCs mit > 1 Knoten und ohne Whitelist
  als Verstoss melden). Vorgesehen in Welle 3.
- **Build-Args / Coverage-Schwellen auf leerem Skelett**: Coverage-
  Gate ist auf `tests/unit/hexagon/core/serialization` beschraenkt
  (90 %); Gesamt-Coverage-Gate auf `src/grid_gym` waere auf leerem
  Skelett nicht erreichbar. Loesung: Coverage-Gate-Stage bleibt
  konfiguriert, wird aber erst ab M1-Slice 2 verbindlich
  ausgefuehrt; in Spike-0-Aggregator `gates` zunaechst weglassen
  oder mit reduziertem Scope laufen.

## 6. Wandert nach

- `in-progress/spike-0.md`, sobald Welle 1 begonnen ist.
- `done/spike-0.md` mit Closure-Notiz nach erfolgreichem
  Abschluss von Welle 5.
- `archive/`, falls Spike-0 scheitert und ADR 0002 auf `Rejected`
  geht; die Folge-ADR (z. B. Option D, Kotlin/JVM) bekommt einen
  eigenen Slice-Plan.

## 7. Verifikationspfad

| Erfolg                                              | Verifikation (Dockerfile-Stage via `make <target>`)                                          |
| --------------------------------------------------- | -------------------------------------------------------------------------------------------- |
| Vier A-1-Gates gruen auf `main`                     | `make gates` gruen (Aggregator: `lint`, `format-check`, `typecheck`, `arch-check`, `test-unit`, `coverage-gate`, `coverage-gate-critical`, `dep-audit`) |
| Sechzehn Verstoss-Branches: je nur ein Gate rot     | `spike-0-results.md` Branch × Gate Matrix; pro Branch `make <gate>`-Aufruf protokolliert     |
| `ruff` akzeptiert `flake8-tidy-imports`-Schluessel  | `make lint` ohne Warnung (Dockerfile-Stage `lint` mit `ruff check --no-cache`)                |
| `canonical_json` bytes-stabil                       | `make test-unit` gruen (Dockerfile-Stage `test-unit`, inkl. `hypothesis`-Properties)          |
| Coverage 90 % auf `serialization`                   | `make coverage-gate-critical CRITICAL_COV_TARGETS=src/grid_gym/hexagon/core/serialization` gruen |
| Spike-0-Abschluss-Gate                              | `make gates` gruen (Aggregator-Stage; `make fullbuild` ist M1-Slice-Abnahmebedingung — siehe Welle 5) |
| `GG-AR-OPEN-001` geschlossen                        | `spec/architecture.md` §19 zeigt „Geschlossen mit `ADR 0002`"                                  |
