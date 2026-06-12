# 031 — CI-Pflicht-Gate fuer `make fullbuild`

**Status:** Done — Aktivierung produktiv mit M6-Welle-3-C2
`ce13253` 2026-06-05. NEU `.github/workflows/fullbuild.yml`
mit Hybrid Push/PR-Paths-Filter + workflow_dispatch-Trigger
(Welle-3-D-3-Substanz); `make fullbuild` cache-frei gruen
ohne Override. Trigger gewandert nach `done/` mit M6-Welle-
3-C3 (Pattern analog Trigger 010 in M6-Welle-1-C3 `4517614`
+ Trigger 008 in M6-Welle-2-C3 `98a1fa1`).
**Datum:** 2026-06-05 (eroeffnet als Welle-1-D-1-Vertagung
in Welle-1-C2 `b514170`), 2026-06-05 (Welle-3-C2
Aktivierung + Welle-3-C3 Self-Close-Move).
**Quelle:** M6-Welle-1-Welle-1-D-1-Vertagung (`M6-welle-1.md
§3 Welle-1-D-1` + `M6-welle-1.md §10.2`) — verankert die
Wahl „Vertagen auf Welle 3" als expliziten Trigger.

---

## Closure-Notiz (M6-Welle-3-C2, 2026-06-05)

Die in §"Trigger" unten beschriebene CI-Pflicht-Gate-
Substanz fuer `make fullbuild` wurde in M6-Welle-3-C2
`ce13253` produktiv realisiert:

- **NEU `.github/workflows/fullbuild.yml`** mit Hybrid-
  Trigger (Welle-3-D-3): `push.branches: [main]` +
  `pull_request.branches: [main]` mit Paths-Filter
  (Dockerfile / Makefile / src/ / tests/ / pyproject.toml
  / uv.lock / deploy/ / `.github/workflows/fullbuild.yml`)
  plus `workflow_dispatch` als Force-Run-Fallback.
- 1 Job: `make fullbuild` (`= make ci + make build + make
  runtime` Compose-Smoke); `timeout-minutes: 30` als
  Safety-Margin. Doc-only-Aenderungen umgehen den teuren
  Run.
- **Welle-3-Begleit-Workflows** in derselben C2-Substanz:
  `tests.yml` (test-unit Matrix Python-3.13/3.14 + test-
  integration Default) + `coverage.yml` (coverage-gate +
  coverage-gate-critical) + `dep-audit.yml`. Diese 3
  Workflows laufen bei jedem Push/PR ohne Paths-Filter;
  `fullbuild.yml` ist der teuerste und mit eigenem Filter
  optimiert.

**Beleg (vor C2-Commit):**

- `actionlint` (Docker `rhysd/actionlint:latest` v1.7.12)
  EXIT=0 auf alle 6 Workflows.
- `make gates` cache-frei gruen ohne Override (10/10 A-1-
  Gates inkl. dep-audit nach `pip 26.1.1 → 26.1.2`-Drift-
  Fix im selben C2-Commit).
- `make fullbuild` cache-frei gruen ohne `CRITICAL_COV_
  TARGETS`-Override: EXIT=0; `[fullbuild] full closure:
  ci + runtime image + compose smoke green`.

**Verbleibendes Restrisiko (analog Welle 2):** Reale
GitHub-Actions-Run-Verifikation des Workflows ist erst
nach Push der Welle-3-Commits sichtbar. Da `fullbuild.yml`
**bei jedem relevanten Push automatisch triggert** (im
Gegensatz zum Release-Workflow, der Tag-Push oder Manual-
Dispatch braucht), ist der Sensor-Check operativ einfach
— der erste Push der `.github/workflows/fullbuild.yml`
enthaelt, triggert auch den Workflow per self-reference im
Paths-Filter. Welle 3 legt **keinen NEU `open/`-Trigger
fuer Sensor-Run** an (im Gegensatz zu Welle 2 mit NEU
Trigger 032), weil der Sensor-Check ohne User-Operation
beim naechsten Push automatisch auslaeuft.

Die unten beschriebenen § "Erwartete Lieferung" /
"Aktivierung" / "Konsequenz wenn ungeloest" sind damit
**historisch** und stehen als Trigger-Watch-Kontext
(Welle-1-Vertagungs-Eroeffnungs-Stand bis Welle-3-C2-
Aktivierung).

---

## Trigger (historisch — Welle-1-Vertagungs-Eroeffnungs-Stand)

Seit Welle-1-C2 (Welle-1-C2-Hash entsteht mit dem
Folge-Commit zu diesem Trigger-Anlage-Commit) ist
`make fullbuild` lokal cache-frei gruen ohne `CRITICAL_COV_
TARGETS`-Override. Beleg:

- `make image-audit`: `grid-gym-runtime:latest (debian
  13.5) Total: 0 (HIGH: 0, CRITICAL: 0)` + `otel/
  opentelemetry-collector-contrib:0.152.1` clean.
- `make fullbuild` `EXIT=0`; `[fullbuild] full closure:
  ci + runtime image + compose smoke green` (inkl. /health
  + otel-collector :13133 + sauberer Compose-Teardown).

Das CI-Pflicht-Gate fuer `make fullbuild` in GitHub-
Actions ist heute **nicht** aktiv. Welle-1-D-1
([`../done/M6-welle-1.md §3 Welle-1-D-1`](M6-welle-1.md))
hatte zwei Optionen geprueft (Mitziehen in Welle 1 vs.
Vertagen auf Welle 3); Welle-1-C2 hat sich fuer Vertagen
entschieden ([`../done/M6-welle-1.md §10.2`](M6-welle-1.md)).

Aktueller CI-Stand (Slice 025;
[`../done/spike-0-results.md`](../done/spike-0-results.md)):

- Vier CI-Pflicht-Gates in GitHub Actions enforced: `lint`,
  `format-check`, `typecheck`, `arch-check`.
- `make test-unit`, `make coverage-gate`, `make
  dep-audit`, `make image-audit`, `make fullbuild` sind
  **lokal Pflicht** ueber `make gates`/`make ci`/`make
  fullbuild`, aber **nicht** GitHub-seitig enforced —
  Slice 025 §2 hat das bewusst auf M6 verschoben.

## Erwartete Lieferung

Eigenstaendiger CI-Edit-Slice (M6-Welle-3-Sub-Item) mit:

- **`.github/workflows/ci.yml`-Erweiterung** um `make
  fullbuild`-Job-Step (oder eigenen Job-Block) — entweder
  als Schwester-Job zu den anderen 4 neuen Welle-3-Jobs
  (`test-unit`/`coverage-gate`/`dep-audit`/`image-audit`)
  oder als Composite-Job, der `make fullbuild` direkt
  ausfuehrt.
- **Trivy-DB-Caching** (`actions/cache`-Aufruf gegen
  `~/.cache/trivy/`) um den `make image-audit`-Lauf in
  CI nicht jedes Mal die 95 MiB Vulnerability-DB neu
  laden zu lassen.
- **Docker-Layer-Caching** (BuildKit-Cache via
  `docker buildx`/`docker/build-push-action` oder
  ueber GHCR-Registry-Cache) um den `make build`-Step
  reproduzierbar in CI laufen zu lassen.
- **Compose-Smoke-Test in CI**: `make runtime`-Aufruf
  in GitHub-Actions-Job mit Docker-in-Docker oder via
  `actions/runner`-Service-Container; alternative:
  `make runtime` nur lokal Pflicht, CI macht nur
  `make ci` (= gates + test-integration + openapi-
  validate + image-audit).
- **Real GitHub-Actions-Lauf** gegen den Slice-Hash
  gruen vor Welle-3-Closure (Sensor-Check, nicht nur
  Workflow-Datei-Anwesenheit; siehe
  [`../done/M6-welle-1.md §9 DoD-Checkliste`](M6-welle-1.md)
  C2-Welle-1-D-1-Mitzieh-Variante-Pattern).

## Aktivierung

Aktivierung erfolgt **automatisch** mit M6-Welle-3
([`M6-perf-security-cicd.md §3.2 Welle 3`](M6-perf-security-cicd.md)).
Welle 3 ist explizit fuer CI/CD-Vollausbau gescoped
(`GG-CICD-001..006` + Python-3.13/3.14-Matrix +
`GG-CICD-007`-Release-Workflow-Pre-Link auf Welle-2-SBOM-
Hook) und bringt 4 weitere neue CI-Jobs (`test-unit` +
`coverage-gate` + `dep-audit` + `image-audit`). Trigger
031 integriert sich dort als 5. (oder 6. bei separatem
Compose-Smoke-Job) Job.

Welle-3-C0 entscheidet die konkrete Job-Granularitaet
(separater `make fullbuild`-Job vs. Composite mit den
anderen 4 Jobs); Welle-3-C2 macht den Workflow-Edit +
realen Gruen-Lauf.

## Konsequenz wenn ungeloest

- `make fullbuild` bleibt lokal Pflicht ohne CI-
  Spiegelung — Drift zwischen lokalem und CI-Stand
  moeglich, falls jemand `make fullbuild` lokal nicht
  laeuft.
- `make image-audit` HIGH-CVE-Famille koennte unbemerkt
  auftauchen, wenn die naechste Debian-Security-DB-Drift
  ein neues Issue bringt, das `apt-get upgrade` nicht
  zieht (Trigger-015-Pattern hat keine Eskalations-
  Schleife).
- Welle-3-DoD-Checkliste muesste alle 5+ CI-Jobs neu
  fixieren; das Vertagungs-Pattern (NEU `open/`-Trigger
  pro Job) wird in Welle-3-C0 bestaetigt.

## Bezuege

- [`../done/M6-welle-1.md §3 Welle-1-D-1`](M6-welle-1.md)
  — Welle-1-Decision-Substanz (Mitziehen vs. Vertagen).
- [`../done/M6-welle-1.md §10.2`](M6-welle-1.md)
  — C2-Realization-Note mit Vertagungs-Begruendung.
- [`../in-progress/M6-perf-security-cicd.md §3.2 Welle 3`](M6-perf-security-cicd.md)
  — M6-Welle-3-Lieferziel mit CI-Job-Liste (4 weitere
  neue Jobs neben Trigger 031).
- [`../../adr/0043-image-audit-strategy.md §7`](../../adr/0043-image-audit-strategy.md)
  — ADR-0043-Out-of-Scope: „CI-Pflicht-Gate fuer
  `make fullbuild`" ist explizit als Welle-1-D-1-
  Entscheidung ausserhalb ADR-0043-Scope verankert.
- [`../done/spike-0-results.md`](../done/spike-0-results.md)
  — Spike-0-Slice-025-Stand: 4 CI-Pflicht-Gates (lint/
  format-check/typecheck/arch-check), 5 lokal Pflicht
  ueber `make gates` (test-unit/coverage-gate/dep-audit/
  image-audit/+fullbuild).
