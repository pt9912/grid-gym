# 025 — GitHub-Actions-CI-Workflow mit vier Gates (M3-Vorzieh-Slice)

**Status:** Done — geschlossen 2026-05-25 nach Bestaetigung des
ersten produktiven CI-Laufs (`run 26237825003`, 2026-05-21,
Commit `01796ae`, alle vier Pflicht-Gates `success`).
M6-Vorzieh-Slice: der volle CI/CD-Ausbau (`GG-CICD-001..00X`)
bleibt M6-Material (roadmap.md §3 M6), aber die vier Pflicht-
Gates fuer `pull_request`-Validation wurden frueher gezogen,
damit M3-Welle-4b und alle Folge-Wellen einen automatischen
GitHub-Side-Check haben.

**Datum:** 2026-05-21 — eroeffnet aus M3-Welle-4a-C3-Closure;
2026-05-25 — geschlossen.

**Verlinkt:**

- [`Dockerfile`](../../../../Dockerfile) — Stages
  `lint`, `arch-check-imports`, `arch-check-custom`,
  `typecheck`.
- [`Makefile`](../../../../Makefile) — Targets
  `lint`, `arch-check-imports`, `arch-check-custom`,
  `typecheck`.
- [`roadmap.md`](../in-progress/roadmap.md) §3 M6
  (`GG-CICD-001..00X` Vorbelegung).
- [`ADR 0002`](../../adr/0002-language-and-build-stack.md)
  §A-1 (`AC-HEXAGON-PURE`, `AC-PORTS-NO-OUT`, etc. — die
  vom `arch-check-imports`-Gate enforcten Contracts).
- [`ADR 0005`](../../adr/0005-type-check-gate.md)
  (`mypy --strict` als Pflicht-Gate).

---

## 1. Zweck

Vier-Gate-Workflow fuer GitHub-Actions, der bei jedem
`push` auf `main` und jedem `pull_request` die folgenden vier
Quality-Gates parallel ausfuehrt:

1. **`lint-imports`** — `import-linter` mit den
   Layer-/Forbidden-Contracts aus `pyproject.toml`
   (AC-CORE-NO-ADAPTERS, AC-PORTS-NO-OUT, AC-ADAPTER-PURE,
   AC-NO-FW, AC-NO-IO-MOD, AC-CORE-NO-DRIVING, AC-PORTS-NO-FW).
   Dockerfile-Stage `arch-check-imports`; Makefile-Target
   `make arch-check-imports`.
2. **`ruff check`** — Stil-/Statisches-Linting (alle Rule-
   Categories aus `pyproject.toml`-Konfiguration: E, F, W, B,
   I, N, UP, C4, SIM, ARG, RUF, PL, TRY, ...). Dockerfile-
   Stage `lint`; Makefile-Target `make lint`.
3. **`python tools/arch_check.py`** — Custom-AST-Checks
   (AC-DOMAIN-FROZEN, Decimal-Constraints, RandomPort-
   Sub-Port-Konvention, etc.). Dockerfile-Stage
   `arch-check-custom`; Makefile-Target
   `make arch-check-custom`.
4. **`mypy --strict`** — Type-Check-Gate (ADR 0005).
   Dockerfile-Stage `typecheck`; Makefile-Target
   `make typecheck`.

Die vier Gates muessen unabhaengig (parallel) laufen koennen
— jedes hat seinen eigenen Dockerfile-Stage ohne Cross-Stage-
Abhaengigkeit ausser dem gemeinsamen `source`-Layer.

## 2. Lieferumfang

**Code:**

- `.github/workflows/ci.yml` — Workflow mit vier Jobs
  (`lint-imports`, `ruff-check`, `arch-check-custom`,
  `typecheck`) plus optionalem Aggregator-Job `gates-summary`.
  Jeder Job baut das Docker-Image fuer seinen Stage und
  fuehrt ihn aus.

**Trigger-/Doc:**

- Dieses Dokument (`docs/plan/planning/in-progress/
  025-github-actions-four-gates.md`).

**Bewusst NICHT umgesetzt** (M6-Material):

- Tests (`test-unit`, `test-integration`) — sind in
  `make gates` enthalten, aber nicht in den vier
  Pflicht-Gates der User-Spec.
- Coverage-Gates (`coverage-gate`, `coverage-gate-critical`).
- `dep-audit` (`pip-audit`).
- `make fullbuild`-Smoke-Test mit Compose.
- Image-Audit (`trivy`).
- SBOM-Generierung.
- Release-Workflow.
- Python-Multi-Version-Matrix (3.13/3.14) — Spike-0-D-8.

## 3. Verifikation

- `make arch-check-imports`, `make lint`,
  `make arch-check-custom`, `make typecheck` jeweils
  cache-frei gruen vor C0.
- `.github/workflows/ci.yml` ist syntaktisch valides YAML
  (action.yml-Schema).
- Lokal mit `act` testbar (`act -j lint-imports`), aber nicht
  Pflicht — der echte Push triggert die Workflows.
- Aktionen pinnen Versionen via Commit-SHA oder Major-Tag
  (`uses: actions/checkout@v4` o. ae.).

## 4. Closure (2026-05-25)

**Verifikation der Akzeptanz-Kriterien (§3):**

- `make arch-check-imports`, `make lint`,
  `make arch-check-custom`, `make typecheck` waren vor C0
  jeweils cache-frei gruen — siehe
  Welle-4a-C3-Closure-Commit `556baaf`.
- `.github/workflows/ci.yml` ist syntaktisch valides YAML;
  GitHub-Actions hat den Workflow ohne Schema-Fehler
  angenommen ab dem ersten Lauf.
- Versions-Pinning per Major-Tag (`actions/checkout@v4`
  etc.) eingehalten.

**Erster produktiver CI-Lauf:**

| Feld         | Wert                                                                              |
| ------------ | --------------------------------------------------------------------------------- |
| Run-ID       | `26237825003`                                                                     |
| Commit       | `01796ae` (ci: GitHub-Actions-Workflow mit vier Pflicht-Gates (Trigger 025))      |
| Datum        | 2026-05-21 16:05 UTC                                                              |
| Conclusion   | `success`                                                                         |
| Jobs         | `lint-imports (import-linter)`, `ruff check (lint)`, `arch-check-custom (tools/arch_check.py)`, `mypy --strict` — alle `success` |

Alle vier Pflicht-Gates aus der User-Spec wurden vom ersten
Lauf an gruen ausgefuehrt; auch alle ~30 Folge-Laeufe bis zum
Closure-Zeitpunkt (zuletzt `26383797368` fuer Slice-028-
Closure, 2026-05-25) sind `success` — der Workflow ist
stabil produktiv.

**Geliefert:**

- `.github/workflows/ci.yml` mit vier parallelen Jobs
  (`lint-imports`, `ruff check (lint)`, `arch-check-custom`,
  `typecheck`); jeder Job baut die zugehoerige Dockerfile-
  Stage und fuehrt sie aus. Kein Aggregator-Job — der
  GitHub-Actions-Required-Checks-Mechanismus reicht.

**Bewusst nicht umgesetzt (bleibt M6-Material):**

- Tests / Coverage-Gates / dep-audit / fullbuild-Smoke /
  trivy-Image-Audit / SBOM / Release-Workflow /
  Multi-Python-Matrix — siehe §2 „Bewusst NICHT umgesetzt".
  Wenn M6-CI/CD-Vollausbau anlaeuft oder die Pflicht-Gate-
  Liste fuer M3/M4 erweitert werden soll, kann der Workflow
  inkrementell um zusaetzliche Jobs ergaenzt werden.
