# Replay and Golden Sets

Diese Datei uebertraegt Replay-/Golden-Set-Denken auf `grid-gym`.
Ziel: Simulation-, Replay-, Fault- und Demo-Aenderungen sollen nicht nur
punktuell gruen sein, sondern gegen stabile Projektzustaende erneut
abspielbar bleiben.

## Scope

Replay gilt fuer alle Pfade, die deterministische oder user-facing
Verhaltensartefakte erzeugen oder vergleichen:

- Tick-Loop, Scheduler, Seed- und `RandomPort`-Verhalten
- Scenario-Loader, Scenario-Hash und kanonische Serialisierung
- Snapshot-Erzeugung, Snapshot-Fortsetzung und Replay-Diff
- Fault-Injection, Fault-Recovery und Safe-Default-Pfade
- Agent-Bus- und RuleBasedAgent-Szenarien
- Demo-YAML, Demo-Run, UI/API/WebSocket-Demo-Pfade
- Protocol-Adapter-Smokes, soweit sie Simulationsergebnisse oder
  Lifecycle-Evidence beeinflussen

## Golden Case

Ein Golden Case beschreibt einen reproduzierbaren Lauf:

```text
Name:
Input project state:
Scenario / command:
Seed / time base:
Expected actions:
Expected changed files or persisted records:
Expected telemetry / events / alarms:
Expected replay diff:
Expected idempotency result:
Expected safety behaviour:
Evidence test:
```

Nicht jeder Golden Case braucht externe `testdata`-Dateien. Kleine,
fokussierte Cases duerfen im Test selbst als In-Memory-Fixture stehen.
Externe Goldens sind Pflicht, wenn ein ganzes user-facing Artefakt
stabil bleiben soll oder wenn ein Diff im Test schwer lesbar wird.

## Current Sensor Families

| Familie | Golden-/Replay-Vertrag | Aktuelle Evidence |
| --- | --- | --- |
| Determinismus | Gleicher Seed + gleiche Inputs erzeugen gleiche kanonische Ausgabe | `make test-determinism` — `determinism`-Marker auf Seed-/Scheduler-/Permutations-/`canonical_json`-/`RandomPort`-Property-Suiten (Slice 054) |
| Replay | Replay-Samples, Snapshot-Fortsetzung und Diff-Klassifikation bleiben stabil | `make test-replay` — `replay`-Marker auf Replay-Diff-/Finalize- und Profil-Preflight-E2E-Suiten |
| Faults | Fault-Aktivierung, Recovery und Safety-Pfade bleiben deterministisch | `make test-fault` — `fault`-Marker auf Fault-Engine-, Per-Device-Fault-Injection- und Fault-Port-Suiten (Slice 054) |
| Unit/Properties | Domain-, Scenario-, Device- und Adapter-Vertraege bleiben lokal gepinnt | `make test-unit` |
| Integration | Postgres, OTLP, API und Compose-Pfade laufen gegen echte Services | `make test-integration` |
| Demo/Runtime | Runtime-Image, Compose-Smoke und Demo-Pfade bleiben bedienbar | `make fullbuild` oder engerer Demo-Smoke |

## Replay Rules

- Jeder neue deterministische Simulationspfad bekommt mindestens einen
  Happy-, Boundary- und Negative-Pin.
- Jeder neue Replay- oder Snapshot-Vertrag bekommt einen Case fuer
  Fresh-State und einen fuer Wiederholung/Idempotenz.
- Jeder Fault- oder Safety-Pfad bekommt einen Case fuer Aktivierung,
  Recovery und "no partial unsafe state".
- Scenario-, JSON- und YAML-artige Artefakte pruefen Struktur und, wo
  user-facing relevant, stabile Sortierung.
- Whole-file Golden Snapshots werden nur dort eingesetzt, wo
  Strukturpruefung nicht reicht. Normalisierung darf semantische
  Unterschiede nicht verstecken.
- Golden Updates sind eine bewusste Produktentscheidung. Slice, Commit
  oder Verification-Evidence muss sagen, warum sich erwarteter Output
  geaendert hat.
- Bei Drift wird zuerst Toolchain/Image, dann Input/Scenario, dann
  Erwartung und erst danach eine echte Regression vermutet.

## Verification Evidence

Wenn ein Slice Simulation-, Replay-, Fault- oder Demo-Verhalten aendert,
enthaelt die Verification-Evidence nach
[`harness/verification.md`](verification.md) zusaetzlich:

```text
Replay / Golden:
- Affected flows:
- Golden cases added:
- Golden cases updated:
- Golden cases replayed:
- Intentional output changes:
- Drift diagnosis:
```

## When to Add External testdata

Lege externe Fixtures unter dem relevanten Paket oder Testbereich an,
wenn:

- ein erwartetes Artefakt laenger als ein kurzer Inline-String ist,
- mehrere Dateien zusammen einen Szenariozustand bilden,
- ein Demo-, Replay- oder Fault-Output fuer Nutzer sichtbar stabil
  bleiben muss,
- ein Review sonst nicht erkennen kann, ob die Aenderung absichtlich ist.

Halte externe Goldens klein. Ein Golden soll einen Vertrag pinnen, nicht
ein komplettes Demo-Projekt konservieren.

## Review Hooks

Reviewer sollen bei Simulation-, Replay-, Fault- oder Demo-Diffs fragen:

- Gibt es einen Happy-, Boundary- und Negative-Case?
- Ist der Seed-/Clock-/Scenario-Input explizit?
- Sind volatile Felder im Replay-Diff korrekt klassifiziert?
- Gibt es einen Recovery- oder Safe-Default-Case fuer Fault-Pfade?
- Wurde ein Golden geaendert, ohne dass Slice oder Commit die
  Output-Aenderung begruendet?
