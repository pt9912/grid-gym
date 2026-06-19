---
description: Slice-Workflow-Skelett (10 Schritte) fuer grid-gym
---

# Slice-Workflow (grid-gym)

Feste Schrittfolge fuer die Arbeit an einem Slice — der dritte Bindepunkt der
Durchsetzungsschicht (*Workflow-Skelett*, inferential feedforward). Es ist der
schwaechste der drei: das Tool-Call-Gate und das Handoff-Gate *erzwingen*, dieses
Skelett *leitet*. Quelle: [`AGENTS.md`](../../AGENTS.md) §7.

1. [`harness/README.md`](../../harness/README.md) lesen — Source Precedence,
   Guides, Sensors, Safety.
2. Rolle aus [`harness/roles.md`](../../harness/roles.md) bestimmen
   (Planner / Architect / Implementation / Reviewer / Verifier / Validator).
3. Source Precedence anwenden und die relevante Spec-/ADR-/Slice-Doku lesen.
4. Betroffene Kennungen benennen (Requirement-, Architektur-, ADR- und Slice-IDs).
5. Kleinste sinnvolle Aenderung umsetzen.
6. Engsten passenden Sensor laufen lassen; bei Codeaenderungen nach Moeglichkeit
   `make gates`.
7. Bei Replay-, Fault-, Determinismus- oder Demo-Aenderungen Evidence nach
   [`harness/replay.md`](../../harness/replay.md) festhalten.
8. Verification-Evidence nach [`harness/verification.md`](../../harness/verification.md)
   festhalten, wenn ein Slice geschlossen oder ein oeffentlicher Vertrag beruehrt wurde.
9. Oeffentliche Vertraege nachziehen (README, Operations-Doku, ADR-Index, Roadmap,
   Slice-Plan, CHANGELOG).
10. Im Handoff ausgefuehrte Sensors, nicht ausgefuehrte Sensors und verbleibende
    Risiken klar nennen.

**Vor dem Beenden:** `make gates` und `make docs-check` muessen auf dem aktuellen
Working-Tree gelaufen sein — das Handoff-Gate (Stop-Hook) prueft das mechanisch
und blockt sonst (fail-closed, mit Loop-Guard).
