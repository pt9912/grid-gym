# AGENTS.md — Briefing fuer AI-Coding-Agenten

Dieses Dokument ist das Onboarding fuer jede AI-Session, die in diesem
Repo Code oder Doku aendert. Es traegt die **harten Regeln** und
**Pointer auf die kanonischen Quellen**, nicht deren Inhalt — Drift
zwischen `AGENTS.md` und ADRs/Slice-Plaenen wird so vermieden.

Der operative Harness-Einstieg liegt in [`harness/README.md`](harness/README.md).
Rollen, Reviews, Verification und Replay sind dort bzw. in
[`harness/roles.md`](harness/roles.md),
[`harness/review.md`](harness/review.md),
[`harness/verification.md`](harness/verification.md) und
[`harness/replay.md`](harness/replay.md) getrennt beschrieben.

Ergaenzend zu diesem Dokument: [`README.md`](README.md) (Projekt-
Ueberblick), [`README.de.md`](README.de.md) (deutsche Variante),
[`spec/architecture.md`](spec/architecture.md) (Architektur),
[`spec/lastenheft.md`](spec/lastenheft.md) (Anforderungen),
[`docs/plan/planning/README.md`](docs/plan/planning/README.md)
(Slice-Plan-Workflow + Wave-Self-Close-Konvention),
[`docs/plan/adr/README.md`](docs/plan/adr/README.md) (ADR-Index).

---

## Source Precedence

In dieser Reihenfolge lesen und Konflikte aufloesen:

1. [`spec/lastenheft.md`](spec/lastenheft.md) — normative
   Anforderungen, `GG-*`-IDs, Akzeptanzkriterien.
2. [`spec/architecture.md`](spec/architecture.md) — hexagonale
   Architektur, Ports, Adapter, `GG-AR-*`-Tabus.
3. [`spec/protocol_profiles.md`](spec/protocol_profiles.md) —
   technische Protokollprofil-Details.
4. [`docs/plan/adr/`](docs/plan/adr/) — Architekturentscheidungen.
5. Aktiver Slice in [`docs/plan/planning/in-progress/`](docs/plan/planning/in-progress/)
   oder [`docs/plan/planning/next/`](docs/plan/planning/next/) —
   konkrete Arbeit, DoD und Closure-Bedingungen.
6. Ausfuehrbare Vertraege: [`Makefile`](Makefile), [`Dockerfile`](Dockerfile),
   [`pyproject.toml`](pyproject.toml) und [`.github/workflows/`](.github/workflows/).
7. Nutzer- und Quality-Doku unter [`docs/user/`](docs/user/), besonders
   [`docs/user/code-review.md`](docs/user/code-review.md).
8. [`README.md`](README.md), [`README.de.md`](README.de.md) und
   [`CHANGELOG.md`](CHANGELOG.md).
9. [`harness/README.md`](harness/README.md) und diese Datei.

Bei Konflikt zwischen dieser Datei und einer kanonischen Quelle gewinnt
die Quelle, und diese Datei wird nachgezogen.

---

## 1. Repo-Layout

| Pfad                                       | Inhalt                                                                       |
| ------------------------------------------ | ---------------------------------------------------------------------------- |
| [`spec/`](spec/)                           | Sprach- und meilensteinfreie Spec (Lastenheft, Architektur).                 |
| [`docs/plan/adr/`](docs/plan/adr/)         | Architecture Decision Records. Lifecycle in [`ADR 0006`](docs/plan/adr/0006-adr-lifecycle-superseding-and-process-corrections.md). |
| [`docs/plan/planning/`](docs/plan/planning/) | Slice-Plaene + Roadmap, Lifecycle `open/` → `next/` → `in-progress/` → `done/`. |
| [`docs/user/`](docs/user/)                 | Operations-/Runbook-Doku (z. B. Observability).                              |
| [`harness/`](harness/)                     | Harness-Einstieg, Rollen, Review, Verification und Replay.                   |
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

### 2.6 Role Separation

Rollen sind Kontextgrenzen. Nutze
[`harness/roles.md`](harness/roles.md) fuer Planner-, Architect-,
Implementation-, Reviewer-, Verifier- und Validator-Vertraege.

Wer geplant oder implementiert hat, reviewt oder verifiziert nicht mit
demselben Eingabe-Kontext. Jeder Rollenwechsel braucht ein
Uebergabe-Artefakt: Plan, ADR-Bezug, Diff, Findings,
Verification-Evidence, Validation-Evidence oder Closure-Notiz.

### 2.7 Review und Verification sind getrennt

Reviews folgen [`harness/review.md`](harness/review.md) und dem
grid-gym-Code-Review-Leitfaden
[`docs/user/code-review.md`](docs/user/code-review.md). Findings werden
als HIGH/MEDIUM/LOW/INFO klassifiziert.

Slice-Closure braucht Verification-Evidence nach
[`harness/verification.md`](harness/verification.md). Gates allein
reichen nicht: Die Evidence muss DoD, Spec-/ADR-IDs, ausgefuehrte
Sensors, nicht ausgefuehrte Sensors und Risiken sichtbar verbinden.

### 2.8 Replay- und Golden-Disziplin

Aenderungen an Simulation, Determinismus, Replay, Fault-Injection oder
Demo-Verhalten folgen [`harness/replay.md`](harness/replay.md). Neue
oder geaenderte Verhaltensvertraege brauchen Happy-, Boundary- und
Negative-Pins oder eine begruendete Carveout-/Folge-Slice-Notiz.

---

## 3. Quality Gates

| Befehl                  | Was es prueft                                                         |
| ----------------------- | --------------------------------------------------------------------- |
| `make gates`            | 10 A-1-Pflicht-Gates (lint, format-check, mypy --strict, arch-check `N` contracts, test-unit, coverage-gate 90/85, critical-coverage 90, dep-audit, noqa-gate, spdx-check). |
| `make test-integration` | Sibling-Container-Tests (testcontainers; Postgres, OTLP-Collector).   |
| `make fullbuild`        | `ci` + Runtime-Image + Compose-Smoke + Trivy-Image-Audit fuer alle relevanten Tags. |
| `make docs-check`       | Markdown-Link-Validator (`tools/check_refs.py`). Prueft alle Bezuege im Repo. |

**Vor jedem Push:** mindestens `make gates` + `make docs-check`
gruen. Vor Welle-/Meilenstein-Closure zusaetzlich `make fullbuild`.
Wenn ein naheliegender Sensor wegen Docker, Sandbox oder Umgebung nicht
gelaufen ist, muss der Handoff den Grund nennen.

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

## 7. Minimal Agent Workflow

1. [`harness/README.md`](harness/README.md) lesen.
2. Rolle aus [`harness/roles.md`](harness/roles.md) bestimmen.
3. Source Precedence anwenden und relevante Spec/ADR/Slice-Doku lesen.
4. Betroffene `GG-*`-, `GG-AR-*`, `ADR-*`- und Slice-IDs benennen.
5. Kleinste sinnvolle Aenderung umsetzen.
6. Engsten passenden Sensor laufen lassen; bei Codeaenderungen nach
   Moeglichkeit `make gates`.
7. Bei Replay-, Fault-, Determinismus- oder Demo-Aenderungen Evidence
   nach [`harness/replay.md`](harness/replay.md) festhalten.
8. Verification-Evidence nach
   [`harness/verification.md`](harness/verification.md) festhalten,
   wenn ein Slice geschlossen oder ein oeffentlicher Vertrag beruehrt
   wurde.
9. Oeffentliche Vertraege in README, `docs/user/`, ADR-Index, Roadmap,
   Slice oder CHANGELOG nachziehen.
10. Im Handoff ausgefuehrte Sensors, nicht ausgefuehrte Sensors und
    verbleibende Risiken klar nennen.

---

## 8. Was NICHT in `AGENTS.md` gehoert

- **Konkrete ADR-Inhalte** — ADRs haben einen eigenen Lifecycle.
- **Slice-Plan-Status** oder Commit-Hashes — leben in
  `roadmap.md` + `planning/`.
- **Architektur-Beschreibungen** — leben in `spec/architecture.md`.
- **Wellen-Historie** — lebt in `M*-results.md`-Closure-Notizen.

`AGENTS.md` traegt nur Pointer auf diese Quellen, nie deren Inhalt
in Kopie. Bei Konflikt zwischen `AGENTS.md` und der kanonischen
Quelle gewinnt **immer** die Quelle, und `AGENTS.md` wird
nachgezogen.
