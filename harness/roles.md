# Agent Roles

Diese Datei trennt Rollen fuer AI-gestuetzte Arbeit an `grid-gym`.
Rollen sind Kontextgrenzen, keine Personen. Eine Person oder ein Agent
kann mehrere Rollen nacheinander ausfuehren, aber nicht mit demselben
Eingabe-Kontext und nicht ohne Uebergabe-Artefakt.

## Slice Sequence

```text
Planner -> Architect -> Implementation -> Reviewer -> Verifier -> Validator -> Planner
```

Jeder Rollenwechsel braucht ein sichtbares Artefakt: Plan, ADR-Bezug,
Diff, Findings, Verification-Evidence, Validation-Evidence oder
Closure-Notiz. Ohne Artefakt ist es kein Rollenwechsel, sondern nur ein
Kontextwechsel ohne Pruefbarkeit.

## Role Contracts

| Rolle | Primaere Frage | Eingabe-Kontext | Output |
| --- | --- | --- | --- |
| Planner | Was wird als naechstes klein genug geliefert? | Roadmap, aktiver Slice, `GG-*`-IDs, offene Trigger | Slice-/Tranche-Plan, Lifecycle-Entscheidung, Closure-Notiz |
| Architect | Passt die Loesung zu Architektur, ADRs und Gates? | Spec, Architektur, ADRs, Slice-Plan, Gate-Vertraege | bestaetigte ADR-Bezuege, Folge-ADR-Vorschlag oder Architektur-Finding |
| Implementation | Wie wird der Slice minimal und korrekt umgesetzt? | aktiver Slice, relevante Spec/ADR, `AGENTS.md`, engste Codepfade | Code-/Doku-Diff, lokale Sensor-Evidence, offene Risiken |
| Reviewer | Welche Risiken oder Vertragsbrueche enthaelt der Diff? | Plan, ADRs, Spec-Anker, Diff, relevante Tests | Findings mit HIGH/MEDIUM/LOW/INFO und Datei-/Zeilenbezug |
| Verifier | Erfuellt das Ergebnis DoD, Spec und Gates? | Slice-DoD, Diff, Tests, Make-Target-Ausgaben, Traceability | Verification-Evidence, fehlende Sensors, DoD-Abweichungen |
| Validator | Loest das Ergebnis den realen Demo-/Nutzer-/Release-Bedarf? | Nutzerpfad, README/Quickstart, Demo-Szenario, Runtime-Artefakt | Validation-Evidence oder Rueckgabe an Planner |

## Boundaries

### Planner

Der Planner bewegt Planning-Artefakte durch
`open/ -> next/ -> in-progress/ -> done/`, schneidet zu grosse Arbeit in
Tranchen und pflegt Roadmap sowie Bestandstabellen.

Der Planner implementiert nicht und stuft Review-Findings nicht ohne
Architektur- oder Verification-Artefakt herunter.

### Architect

Der Architect prueft ADR-Konformitaet, hexagonale Grenzen,
Port-/Adapter-Schnittstellen, `GG-AR-TABU-*`, Gate-Politik,
Lizenz-Boundaries, Replay-/Determinismus-Vertraege und
Release-/Distributionsentscheidungen.

Der Architect kann eine Folge-ADR verlangen oder vorschlagen. Accepted
ADRs werden nicht stillschweigend ueberschrieben.

### Implementation

Implementation setzt nur den aktiven Scope um. Sie nutzt die engsten
sinnvollen Sensors frueh und `make gates` als normalen Code-Handoff,
wenn Docker verfuegbar ist.

Implementation darf ADR-, Spec- oder Gate-Konflikte nicht pragmatisch
uebergehen. Bei Konflikt entsteht ein Uebergabe-Artefakt an Architect
oder Planner.

### Reviewer

Reviewer priorisiert Bugs, Vertragsbrueche, Architekturdrift,
Determinismus-/Replay-Risiken, fehlende Tests, Safety-Risiken,
Lizenz-Boundary-Verstoesse und Doku-Drift.

Findings folgen [`harness/review.md`](review.md). Der bestehende
grid-gym-Code-Review-Leitfaden unter
[`docs/user/code-review.md`](../docs/user/code-review.md) bleibt die
repo-spezifische Review-Quelle.

Reviewer verifiziert nicht die komplette DoD-Closure. Das ist Aufgabe
des Verifier.

### Verifier

Verifier prueft "built the thing right": DoD gegen Diff, Tests gegen
Spec-ID, Make-Targets gegen Handoff, Docs gegen Links, Carveouts gegen
Plan und Replay-/Golden-Evidence gegen Verhalten.

Verification-Evidence folgt [`harness/verification.md`](verification.md).
Sie ist ein eigenes Closure-Artefakt im Slice oder ein verlinktes
Evidence-Dokument, nicht nur eine Liste ausgefuehrter Gates.

Verifier darf nicht behaupten, ein Gate sei gruen, wenn es nicht
ausgefuehrt wurde. Nicht ausgefuehrte Sensors werden mit Grund gelistet.

### Validator

Validator prueft "built the right thing": Passt das Ergebnis zum Demo-
oder Nutzerpfad, zu README/Quickstart, UI, API, Runtime-Stack,
Observability und Release-Kommunikation?

Fuer `grid-gym` sind typische Validation-Fragen:

- Kann ein neuer Nutzer den lokalen Docker-/Compose-Pfad nachvollziehen?
- Laesst sich die Demo mit dem dokumentierten Szenario bedienen?
- Zeigen UI, API und WebSocket-Daten denselben fachlichen Laufzustand?
- Bleiben Simulation, Replay und Fault-Verhalten fuer die Zielperson
  nachvollziehbar und deterministisch?

## Conflict Handling

| Konflikt | Entscheidungspfad |
| --- | --- |
| Reviewer meldet ADR- oder `GG-AR-TABU-*`-Verstoss, Implementation widerspricht | Architect prueft ADR-Aktualitaet und Code. Output: bestaetigtes Finding oder Folge-ADR. |
| Verifier findet DoD-Luecke, Implementation haelt Scope fuer erledigt | Planner entscheidet: Slice zurueck, DoD anpassen oder Folge-Slice/Carveout mit Plan-Anker. |
| Validation ist rot, Verification ist gruen | Planner entscheidet, ob der Slice fachlich falsch geschnitten war oder ein Folge-Slice reicht. |
| Gate-Lockerung waere bequem | Architect/Planner brauchen ADR- oder Plan-Anker; Implementation aendert nicht still. |
| Replay/Fault-Golden driftet | Verifier prueft Toolchain/Inputs/Expectation zuerst, Architect entscheidet bei Vertragsaenderung. |

## Minimal Handoff Fields

Jede Rolle uebergibt knapp:

```text
Role:
Input context:
Changed artefacts:
Evidence:
Open risks:
Next role:
```

Diese Felder koennen als kurzer Abschnitt in Slice-Closure, PR-Text,
Review-Kommentar oder finalem Agent-Handoff stehen.
