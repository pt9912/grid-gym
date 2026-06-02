# Review Harness

Diese Datei standardisiert Reviews fuer `grid-gym`. Review beantwortet:
Welche Risiken, Vertragsbrueche oder Wartbarkeitsprobleme enthaelt ein
Diff, bevor Verification die DoD-Closure prueft?

Review ist eine Entscheidungsvorlage. Reviewer implementieren nicht,
verifizieren nicht vollstaendig gegen DoD und validieren nicht den
realen Nutzerbedarf.

## Input Context

Ein reproduzierbarer Review braucht mindestens:

| Quelle | Zweck |
| --- | --- |
| Diff oder PR-Patch | Was wurde geaendert |
| Aktiver Slice oder Plan | Scope, DoD, explizite Nicht-Ziele |
| Betroffene `GG-*`- und `GG-AR-*`-IDs | Produktvertrag und Akzeptanzkriterien |
| Betroffene ADRs | Architektur- und Toolentscheidungen |
| [`AGENTS.md`](../AGENTS.md) | Hard Rules |
| [`docs/user/code-review.md`](../docs/user/code-review.md) | Grid-gym-spezifische Review-Checkliste |
| [`harness/roles.md`](roles.md) | Rollenabgrenzung |
| [`harness/verification.md`](verification.md) | Abgrenzung zu Verification |
| Relevante Tests/Gates | Welche Sensors koennen Findings bestaetigen |

Ohne Plan- oder Spec-Kontext ist ein Review nur Codekritik, kein
Harness-Review.

## Finding Categories

Findings werden absteigend sortiert: HIGH vor MEDIUM vor LOW vor INFO.

| Kategorie | Bedeutung | Blockiert |
| --- | --- | --- |
| HIGH | Produktvertrag, Sicherheit, Datenintegritaet, Architekturgrenze, Lizenz-Boundary oder CI-Gate kann brechen | ja |
| MEDIUM | Wahrscheinliche Regression, fehlender Test, unklare Fehlerklassifikation oder relevantes Drift-Risiko | normalerweise vor Merge klaeren |
| LOW | Wartbarkeit, Doku-Praezision oder kleine Konsistenzluecke ohne unmittelbaren Vertragsbruch | nein |
| INFO | Beobachtung oder Kontext ohne Aenderungspflicht | nein |

### HIGH-Anker fuer `grid-gym`

Ein Finding ist HIGH, wenn es eines dieser Muster trifft:

- `GG-*`-Akzeptanzkriterium, `GG-SAFE-*`-Vertrag oder
  Determinismus-Invariante kann verletzt werden.
- Hexagonale Importregel, Port-/Adapter-Grenze, `GG-AR-TABU-*` oder ADR
  wird gebrochen.
- Simulation-, Replay- oder Fault-Verhalten kann nicht deterministisch
  reproduziert werden.
- Docker-only-Harness, `make gates`, Security-Gate, Coverage-Gate,
  `noqa-gate` oder `spdx-check` wird gelockert oder umgangen.
- Protokoll- oder UI-Adapter trifft fachliche Entscheidungen, die in den
  Domain-Kern gehoeren.
- Lizenz-Boundary fuer IEC-61850/GPL-nahe Pfade kann verletzt werden.
- Neue oeffentliche API-/UI-/Demo-Vertraege entstehen ohne Spec-/ADR-,
  Test- oder Doku-Anker.

### MEDIUM-Anker fuer `grid-gym`

Ein Finding ist MEDIUM, wenn es eines dieser Muster trifft:

- Neuer oeffentlicher API-, UI-, Replay-, Fault- oder Demo-Pfad hat
  keinen negativen Test oder keinen Boundary-Pin.
- Fehlerbehandlung ist plausibel, aber nicht klar als typisierter
  `GridGymError` oder Adapter-Boundary-Exception gefasst.
- Doku, README, CHANGELOG, ADR-Index oder Roadmap driftet gegen Spec
  oder implementiertes Verhalten.
- Tests belegen Verhalten, aber nicht die relevante `GG-*`- oder
  `ADR-*`-ID.
- Golden-/Replay-Erwartungen wurden geaendert, ohne die
  Output-Aenderung im Slice oder Commit zu begruenden.
- Ein LOW-Muster wiederholt sich und wird zum Drift-Signal.

## Review Lenses

Reviewer pruefen diese Linsen explizit und berichten auch
Negativbefunde fuer relevante Linsen.

| Linse | Prueffrage |
| --- | --- |
| Spec / Traceability | Sind `GG-*`-/`GG-AR-*`-/ADR-Anker korrekt, vollstaendig und testbar? |
| Architecture | Bleiben Hexagon, Ports, Adapter, Wiring und `GG-AR-TABU-*` sauber? |
| Docker-only / Gates | Bleibt der reproduzierbare `make`-/Docker-Harness intakt? |
| Determinism / Replay | Sind Seed, Scheduler, Canonical Serialization, Replay-Diff und Golden Cases stabil? |
| Fault / Safety | Bleiben Fault-Injection, Recovery und Safe-Default-Verhalten deterministisch und typisiert? |
| Adapter Purity | Uebersetzen Adapter nur Protokolle/Datenformate, statt Domain-Entscheidungen zu treffen? |
| Tests | Gibt es Happy-, Boundary- und Negative-Pins fuer neue Vertraege? |
| License / SPDX | Bleiben GPL-/IEC-61850-Boundaries und SPDX-Identifier korrekt? |
| Docs / Release | Sind README, `docs/user/`, ADR-Index, Roadmap und CHANGELOG konsistent? |

## Output Schema

Jedes Finding verwendet dieses Schema:

```text
<CATEGORY> <path>:<line> - <kurzer Titel>
Quelle: <GG-*|GG-AR-*|ADR-*|Hard Rule|Maintainability>
Befund: <1-2 beobachtbare Saetze>
Risiko: <warum das relevant ist>
Verifizierbar: <Sensor/Test/Review-only>
```

Am Ende jedes Reviews:

```text
Geprueft ohne Befund:
- <Linse oder Pfad>

Nicht geprueft:
- <Linse oder Pfad> - <Grund>
```

## Non-Goals

- Keine Implementierungsvorschlaege als Ersatz fuer Findings.
- Keine Refactors ausserhalb des Diff-Scopes.
- Keine DoD-Closure. Das ist Verifier-Aufgabe.
- Keine Validation gegen Nutzerbedarf. Das ist Validator-Aufgabe.
- Keine Abwertung von Findings, weil ihre Behebung unbequem ist.

## Steering Loop

Wenn dasselbe Finding dreimal auftritt:

1. Klassifikation in dieser Datei schaerfen.
2. Pruefen, ob `AGENTS.md`, ADR, Spec oder
   [`docs/user/code-review.md`](../docs/user/code-review.md) eine Hard
   Rule braucht.
3. Pruefen, ob ein computational Sensor moeglich ist (`make lint`,
   `make arch-check`, `make docs-check`, `make test-determinism`,
   `make test-replay`, `make test-fault`).
4. Falls es nur temporaer toleriert wird: Plan-Anker und Closure-
   Evidence aktualisieren.
