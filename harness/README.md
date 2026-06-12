# Harness

Dieser Harness verbindet Spezifikationen, ADRs, Slice-Plaene,
Quality-Gates und Betriebsdokumentation fuer `grid-gym`. Er ist kein
Ersatz fuer `spec/` oder `docs/`, sondern der Einstiegspunkt fuer
Menschen und AI-Coding-Agenten.

Wenn diese Datei einer kanonischen Quelle widerspricht, gewinnt die
kanonische Quelle und diese Datei wird angepasst.

## Source Precedence

| Rang | Quelle | Charakter |
| --- | --- | --- |
| 1 | [`spec/lastenheft.md`](../spec/lastenheft.md) | Normative Anforderungen, `GG-*`-IDs, Akzeptanzkriterien, Quality- und Sicherheitsvertraege |
| 2 | [`spec/architecture.md`](../spec/architecture.md) | Hexagonale Architektur, Ports, Adapter, Tabus, Testarchitektur |
| 3 | [`spec/protocol_profiles.md`](../spec/protocol_profiles.md) | Technische Protokollprofil-Details fuer Adapter |
| 4 | [`docs/plan/adr/`](../docs/plan/adr/) | Architekturentscheidungen und ADR-Lifecycle |
| 5 | [`docs/plan/planning/in-progress/`](../docs/plan/planning/in-progress/) und [`next/`](../docs/plan/planning/next/) | Aktuelle Slice-Arbeit, Roadmap, DoD, Closure-Bedingungen |
| 6 | [`Makefile`](../Makefile), [`Dockerfile`](../Dockerfile), [`pyproject.toml`](../pyproject.toml), [`.github/workflows/`](../.github/workflows/) | Ausfuehrbare Build-, Test-, Gate- und CI-Vertraege |
| 7 | [`docs/user/`](../docs/user/) | Nutzer-, Operations-, Review- und Observability-Doku |
| 8 | [`README.md`](../README.md), [`README.de.md`](../README.de.md), [`CHANGELOG.md`](../CHANGELOG.md) | Produktueberblick und Release-Kommunikation |
| 9 | [`AGENTS.md`](../AGENTS.md) | Agent-Briefing und Hard Rules |
| 10 | Diese Datei | Harness-Einstieg |

## Guides

Feedforward-Quellen, die Arbeit vor der Umsetzung lenken:

| Quelle | Inhalt |
| --- | --- |
| [`spec/lastenheft.md`](../spec/lastenheft.md) | `GG-*`-IDs, Prioritaeten, Akzeptanzkriterien, Nicht-Ziele |
| [`spec/architecture.md`](../spec/architecture.md) | `GG-AR-*`-Prinzipien, Ports, Komponenten, Tabus, Testarchitektur |
| [`docs/plan/adr/README.md`](../docs/plan/adr/README.md) | ADR-Index und Entscheidungsueberblick |
| [`docs/plan/planning/in-progress/roadmap.md`](../docs/plan/planning/in-progress/roadmap.md) | Meilenstein-, Wellen- und Slice-Status |
| [`docs/plan/planning/README.md`](../docs/plan/planning/README.md) | Slice-Lifecycle und Wave-Self-Close-Konvention |
| [`docs/user/code-review.md`](../docs/user/code-review.md) | Grid-gym-spezifische Code-Review-Linsen |
| [`harness/roles.md`](roles.md) | Rollen, Uebergaben und Konfliktpfade |
| [`harness/review.md`](review.md) | Review-Kategorien, Prueflinsen und Output-Schema |
| [`harness/replay.md`](replay.md) | Replay-/Golden-Regeln fuer Simulation, Faults und Demo |
| [`harness/verification.md`](verification.md) | Verification-Evidence und Slice-Closure-Schema |
| [`AGENTS.md`](../AGENTS.md) | Hard Rules, Commit-Konvention, Markdown-Regeln |

## Sensors

Feedback-Gates, die reale Projektzustaende messen:

| Target | Charakter | Wann verwenden |
| --- | --- | --- |
| `make lint` | Ruff-Regeln inkl. Safety-, Komplexitaets-, Naming- und Import-Verbote | Nach Python-Codeaenderungen |
| `make format-check` | Ruff-Format ohne Auto-Fix | Vor Handoff mit Python-Diff |
| `make typecheck` | `mypy --strict` gemaess [`ADR 0005`](../docs/plan/adr/0005-type-check-gate.md) | Nach Typ-, Port- oder API-Aenderungen |
| `make arch-check` | Import-Linter plus `tools/arch_check.py` fuer `GG-AR-TABU-*` | Nach Architektur-, Port-, Adapter- und Dependency-Aenderungen |
| `make docs-check` | Markdown-Link-Validator | Nach Doku-, Spec-, ADR- oder Planning-Aenderungen |
| `make spdx-check` | SPDX-Identifier-Gate fuer Lizenz-Boundaries | Nach IEC-61850-/License-Boundary-Aenderungen |
| `make noqa-gate` | Hard-Gate gegen `# noqa`-Marker | Nach Python-Diff und vor `make gates` |
| `make test-unit` | Unit- und Property-Tests | Nach produktiven Codeaenderungen |
| `make test-determinism` | Determinismus-Tests fuer Seed, Scheduler und kanonische Ausgabe | Nach Simulation-, Random-, Scenario- oder Replay-Aenderungen |
| `make test-replay` | Replay-Marker-Tests | Nach Replay-, Snapshot- oder Diff-Aenderungen |
| `make test-fault` | Fault-Injection-Marker-Tests | Nach Fault-, Safety- oder Recovery-Aenderungen |
| `make test-integration` | Compose-/testcontainers-Integration | Nach Persistenz-, OTLP-, API-, Compose- oder Adapter-Integration |
| `make coverage-gate` | Gesamt-Coverage 90 Prozent Line / 85 Prozent Branch | Nach produktiven Codeaenderungen |
| `make coverage-gate-critical` | Critical-Coverage 90 Prozent fuer kritische Domain | Nach Safety-, Simulation-, Device-, Scenario- oder Replay-Aenderungen |
| `make dep-audit` | Dependency-Audit gegen Lockfile | Nach Dependency- oder Lockfile-Aenderungen |
| `make image-audit` | Trivy gegen Runtime-Image und OTLP-Collector-Image | Vor Release-/Runtime-Handoff |
| `make openapi-validate` | FastAPI-OpenAPI-Export und Validator | Nach HTTP-API-Aenderungen |
| `make gates` | Inner-loop Closure: 10 Pflicht-Gates | Normaler Abschluss fuer Codeaenderungen |
| `make ci` | `gates` plus Integration, OpenAPI und Image-Audit | Vor groesseren Handoffs |
| `make fullbuild` | `ci` plus Runtime-Image und Compose-Smoke | Vor Welle-/Meilenstein-Closure |

Wenn ein Sensor wegen Umgebung, Sandbox oder Docker nicht laeuft, den
Grund im Handoff nennen. Keine gruene Closure behaupten, wenn der
passende Sensor nicht ausgefuehrt wurde.

## Traceability

- Jede oeffentliche Verhaltensaenderung braucht einen `GG-*`-, `GG-AR-*`-,
  `ADR-*`- oder Slice-Anker.
- Neue oder geaenderte Anforderungen brauchen Evidence: Test, Gate, ADR,
  Demo oder dokumentierte Closure.
- Neue ADRs aktualisieren [`docs/plan/adr/README.md`](../docs/plan/adr/README.md).
- Planning-Dokumente folgen `open/ -> next/ -> in-progress/ -> done/`.
- Slice-Closure braucht Verification-Evidence nach
  [`harness/verification.md`](verification.md).
- Replay-, Determinismus-, Fault- oder Demo-Aenderungen brauchen
  Replay-/Golden-Evidence nach [`harness/replay.md`](replay.md).
- Accepted ADRs werden nicht inhaltlich umgeschrieben; Korrekturen
  entstehen als Folge-ADR oder per [`ADR-0011`](../docs/plan/adr/0011-schaerfung-ohne-abloesung.md)-Schaerfung-ohne-Abloesung.

## Role Separation

Rollen sind Kontextgrenzen, keine Personen. Die verbindliche
Rollenreferenz liegt in [`harness/roles.md`](roles.md).

Standardsequenz fuer Slice-Arbeit:

```text
Planner -> Architect -> Implementation -> Reviewer -> Verifier -> Validator -> Planner
```

Jeder Rollenwechsel braucht ein Uebergabe-Artefakt. Review-Findings
folgen [`harness/review.md`](review.md); Verification-Evidence folgt
[`harness/verification.md`](verification.md). Das sind getrennte
Artefakte.

## Scope Boundaries

- `grid-gym` ist eine offline-lokale Simulations- und Demo-Plattform,
  kein produktiver BESS-Controller.
- Simulationsadapter versprechen keine reale Anlagensteuerung
  (`GG-SAFE-007`, `GG-NONGOAL-001`).
- Hexagonale Grenzen gelten: Fachlogik bleibt in `hexagon/`, konkrete
  I/O-, HTTP-, UI-, Persistenz- und Protokollintegration bleibt in
  `adapters/` oder `deploy/`.
- Determinismus ist Produktvertrag: gleiche Seeds, gleiche Szenarien und
  gleiche Inputs muessen stabile kanonische Ausgaben ergeben.
- Docker-only ist verpflichtend. Host-Toolchain-Befehle duerfen nicht als
  alleiniger Verifikationsnachweis fuer einen Handoff dienen.
- Quality-Gates, Coverage-Schwellen, Architekturregeln und Suppression-
  Verbote duerfen nicht still gelockert werden.

## Minimal Agent Workflow

1. Diese Datei und [`AGENTS.md`](../AGENTS.md) lesen.
2. Rolle aus [`harness/roles.md`](roles.md) bestimmen.
3. Relevante Spec, Architektur, ADR und aktiven Slice lesen.
4. Betroffene `GG-*`-, `GG-AR-*`, `ADR-*`- und Slice-IDs benennen.
5. Kleinste sinnvolle Aenderung planen.
6. Engsten passenden Sensor laufen lassen.
7. Bei Codeaenderungen nach Moeglichkeit `make gates` ausfuehren.
8. Bei Replay-, Fault-, Determinismus- oder Demo-Aenderungen Evidence
   nach [`harness/replay.md`](replay.md) festhalten.
9. Verification-Evidence nach [`harness/verification.md`](verification.md)
   festhalten, wenn ein Slice geschlossen oder ein oeffentlicher Vertrag
   beruehrt wurde.
10. Oeffentliche Doku, ADR-Index, Roadmap, Slice, README oder CHANGELOG
    aktualisieren, wenn ein oeffentlicher Vertrag beruehrt wurde.
11. Handoff mit Rolle, ausgefuehrten Sensors, offenen Sensors und Risiken.
