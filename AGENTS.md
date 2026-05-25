# AGENTS.md — Briefing fuer AI-Coding-Agenten

Dieses Dokument ist das Onboarding fuer jede AI-Session, die in diesem
Repo Code oder Doku aendert. Es traegt die **harten Regeln** und
**Pointer auf die kanonischen Quellen**, nicht deren Inhalt — Drift
zwischen `AGENTS.md` und ADRs/Slice-Plaenen wird so vermieden.

Ergaenzend zu diesem Dokument: [`README.md`](README.md) (Projekt-
Ueberblick), [`README.de.md`](README.de.md) (deutsche Variante),
[`spec/architecture.md`](spec/architecture.md) (Architektur),
[`spec/lastenheft.md`](spec/lastenheft.md) (Anforderungen),
[`docs/plan/planning/README.md`](docs/plan/planning/README.md)
(Slice-Plan-Workflow + Wave-Self-Close-Konvention),
[`docs/plan/adr/README.md`](docs/plan/adr/README.md) (ADR-Index).

---

## 1. Repo-Layout

| Pfad                                       | Inhalt                                                                       |
| ------------------------------------------ | ---------------------------------------------------------------------------- |
| [`spec/`](spec/)                           | Sprach- und meilensteinfreie Spec (Lastenheft, Architektur).                 |
| [`docs/plan/adr/`](docs/plan/adr/)         | Architecture Decision Records. Lifecycle in [`ADR 0006`](docs/plan/adr/0006-adr-lifecycle-superseding-and-process-corrections.md). |
| [`docs/plan/planning/`](docs/plan/planning/) | Slice-Plaene + Roadmap, Lifecycle `open/` → `next/` → `in-progress/` → `done/`. |
| [`docs/user/`](docs/user/)                 | Operations-/Runbook-Doku (z. B. Observability).                              |
| [`src/grid_gym/`](src/grid_gym/)           | Produktiv-Code (hexagonale Architektur — `hexagon/`/`adapters/`).            |
| [`tests/unit/`](tests/unit/)               | Unit-Tests (laufen via `make test-unit`).                                    |
| [`tests/integration/`](tests/integration/) | Integration-Tests mit testcontainers (laufen via `make test-integration`).   |
| [`tools/`](tools/)                         | Repo-Tooling (Architekturtest, Link-Validator, Diagnose).                    |
| [`deploy/`](deploy/)                       | Produktiv-Compose-Stack.                                                     |
| [`Makefile`](Makefile) + [`Dockerfile`](Dockerfile) | Alle Builds, Tests und Gates.                                       |

---

## 2. Harte Regeln

### 2.1 Docker-only

Kein lokales `.venv`, kein `pip install`, kein `uv sync` ausserhalb
von Dockerfile-Stages. Alles laeuft ueber `make` (das wiederum Docker
nutzt). Hintergrund: Toolchain-Reproduzierbarkeit + Supply-Chain-
Defense.

Falsch: `uv run python tools/foo.py` (legt lokal `.venv/` an).
Richtig: `docker compose -f tests/integration/compose.yml run --rm
test-runner uv run python tools/foo.py`.

### 2.2 `# noqa` ist verboten (Slice 027)

Inline-`# noqa`-Marker brechen das `noqa-gate` in `make gates`.
Ausnahmen werden in `pyproject.toml` `[tool.ruff.lint.per-file-
ignores]` mit Begruendung dokumentiert.

### 2.3 `git mv` + Inhalts-Rewrite: zwei Commits

Wenn eine Datei verschoben **und** der Inhalt umgeschrieben wird:
1. `git mv source target` → eigener Commit (reiner Move, Git erkennt
   `R`-Rename).
2. Inhalt umschreiben → zweiter Commit.

Sonst faellt die Rename-Detection unter die 50 %-Similarity-Schwelle
und `git log --follow` wird unzuverlaessig.

### 2.4 Wave-Self-Close-Commit-Konvention

Sobald ein Slice-Plan (`welle-*.md`, `M*-*.md`) den Status `Done`
erreicht, schliesst er seine eigene Commit-Sequenz mit einem reinen
`git mv` nach `done/`. Inhaltliche Folge-Edits (relative Link-
Anpassung, ADR-`Bezug:`-Pfad-Pflege per [`ADR 0028`](docs/plan/adr/0028-link-maintenance-accepted-adr-bezug.md),
README-Bestand-Sync) landen im **unmittelbar nachfolgenden** Commit.

Details: [`docs/plan/planning/README.md`](docs/plan/planning/README.md)
§Wave-Self-Close-Commit-Konvention.

### 2.5 Architektur ist sprach- und meilensteinfrei

[`spec/architecture.md`](spec/architecture.md) referenziert ADRs und
Modul-Pfade, aber **keine** Wellen, Slices, Commit-Hashes oder
Closure-Daten. Die zeitliche Schicht lebt in
[`docs/plan/planning/in-progress/roadmap.md`](docs/plan/planning/in-progress/roadmap.md)
und den `M*-results.md`-Closure-Notizen.

---

## 3. Quality Gates

| Befehl                  | Was es prueft                                                         |
| ----------------------- | --------------------------------------------------------------------- |
| `make gates`            | 9 A-1-Pflicht-Gates (lint, format-check, mypy --strict, arch-check `N` contracts, test-unit, coverage-gate 90/85, critical-coverage 90, dep-audit, noqa-gate). |
| `make test-integration` | Sibling-Container-Tests (testcontainers; Postgres, OTLP-Collector).   |
| `make fullbuild`        | `ci` + Runtime-Image + Compose-Smoke + Trivy-Image-Audit fuer alle relevanten Tags. |
| `make docs-check`       | Markdown-Link-Validator (`tools/check_refs.py`). Prueft alle Bezuege im Repo. |

**Vor jedem Push:** mindestens `make gates` + `make docs-check`
gruen. Vor Welle-/Meilenstein-Closure zusaetzlich `make fullbuild`.

---

## 4. ADR- und Slice-Plan-Lifecycle

- **ADR-Lifecycle:** `Proposed` → `Provisional` → `Accepted` →
  optional `Superseded`. Details:
  [`ADR 0006`](docs/plan/adr/0006-adr-lifecycle-superseding-and-process-corrections.md).
- **Schaerfung-ohne-Supersede:** Folge-ADR ergaenzt einen bestehenden
  Accepted-ADR ohne Ablösung. Pattern:
  [`ADR 0011`](docs/plan/adr/0011-schaerfung-ohne-abloesung.md).
- **`Bezug:`-Pfad-Pflege bei Move:** ADRs mit Verweis auf einen
  verschobenen Slice-Plan werden direkt nachgezogen, kein Forwarder-
  Stub. Pattern: [`ADR 0028`](docs/plan/adr/0028-link-maintenance-accepted-adr-bezug.md).
- **Slice-Plan-Workflow:** Trigger lebt in `open/`, geplante Arbeit
  in `next/`, aktive Slices in `in-progress/`, abgeschlossene in
  `done/`. Sehe
  [`docs/plan/planning/README.md`](docs/plan/planning/README.md).
- **Slice-Naming:** Welle-Slice-Begleit als `M{N}-welle-{X}.md`
  (z. B. `M3-welle-6.md`). Verhindert Kollisionen ueber
  Meilensteine.

---

## 5. Markdown-Konvention

- **Dateinamen / Pfade / Kennungen** stehen in Backticks
  (Monospace). Wenn klickbar, packe Codeblock in einen Markdown-
  Link: `` [`foo.md`](foo.md) `` rendert zu klickbarem Monospace.
- **`tools/check_refs.py`** prueft alle Markdown-Links im Repo —
  jeder broken Link bricht `make docs-check`. Tabellen-
  Bestand-Zeilen in `docs/plan/planning/**/README.md` sind
  bewusst als Links formatiert, damit Drift bei Move/Rename
  automatisch faellt.

---

## 6. Commit-Konvention

- **Format:** `<type>(<scope>): <kurzer-headline>` (Conventional
  Commits). Typen: `feat`, `fix`, `chore`, `docs`, `test`, `build`.
- **Co-Authored-By:** Bei AI-assistierten Commits Co-Authored-By-
  Trailer setzen (z. B. `Co-Authored-By: Claude Opus 4.7 (1M context)
  <noreply@anthropic.com>`).
- **HEREDOC fuer Multi-Line-Messages:** Bei Bash-`git commit -m`
  immer `$(cat <<'EOF' ... EOF)` nutzen, damit Formatierung
  erhalten bleibt.
- **Sicherheit:** keine destruktiven Git-Operationen ohne
  explizite Userfreigabe (`push --force`, `reset --hard`,
  `checkout .`, `branch -D`).

---

## 7. Was NICHT in `AGENTS.md` gehoert

- **Konkrete ADR-Inhalte** — ADRs haben einen eigenen Lifecycle.
- **Slice-Plan-Status** oder Commit-Hashes — leben in
  `roadmap.md` + `planning/`.
- **Architektur-Beschreibungen** — leben in `spec/architecture.md`.
- **Wellen-Historie** — lebt in `M*-results.md`-Closure-Notizen.

`AGENTS.md` traegt nur Pointer auf diese Quellen, nie deren Inhalt
in Kopie. Bei Konflikt zwischen `AGENTS.md` und der kanonischen
Quelle gewinnt **immer** die Quelle, und `AGENTS.md` wird
nachgezogen.
