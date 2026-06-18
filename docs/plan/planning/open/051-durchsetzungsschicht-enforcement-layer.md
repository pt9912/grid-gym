# 051 — Durchsetzungsschicht: Tool-Call-Gate + Handoff-Gate (v1.2.0)

**Status:** Open
**Datum:** 2026-06-18
**Quelle:** v1.2.0-Regelwerk-Delta-Analyse — Grundlagen-Digest
*Durchsetzungsschicht* + Modul 11 (Pre-completion-Checklist). Repo-Ist:
nur [`.claude/settings.local.json`](../../../../.claude/settings.local.json)
(Permission-Allowlist), **keine** Hooks, kein versioniertes Hook-Settings-File,
keine Slash-Commands.

---

## Trigger

v1.2.0 fuehrt die **Durchsetzungsschicht** ein: die fail-closed Mechanik,
die aus „die Doku sagt X" ein „der Harness erzwingt X" macht. Drei
Bindepunkte an der Agent-Schleife:

| Bindepunkt | Wann | 2×2-Quadrant | Wirkung |
| --- | --- | --- | --- |
| Tool-Call-Gate | vor jedem Tool-Call | computational feedforward | falsche Handlung technisch erschweren (Befehls-Guard) |
| Handoff-Gate | vor „fertig"-Meldung | computational feedback | deterministisch pruefen, dass die Gates wirklich liefen |
| Workflow-Skelett | beim Aufgaben-Start | inferential feedforward | Slice-Workflow als feste Schrittfolge vorgeben |

grid-gym bindet aktuell **keinen** dieser Punkte mechanisch. Die harten
Regeln (Docker-only, `make gates` vor Handoff, `# noqa`-Verbot) leben nur
als *inferential feedforward* in [`AGENTS.md`](../../../../AGENTS.md) — ein
driftender Agent kann sie ignorieren, ohne dass etwas blockt. Genau die
Harness-Luege-Klasse „ich hab die Gates laufen lassen" bleibt unbewacht.

## Erwartete Lieferung

Eine versionierte (nicht lokale) Hook-Verdrahtung in Claude Code:

- **Tool-Call-Gate** (`PreToolUse`): Befehls-Guard, der Bash-Befehle gegen
  die Docker-only-Regel prueft (lokales `uv`/`pip` ausserhalb Docker
  blockt). Stolperdraht, **keine** Sandbox — Interpreter-Umwege bleiben
  moeglich (ehrlich benannte Grenze).
- **Handoff-Gate** (`Stop`): inhaltsbasierter Nachweis (Working-Tree-Hash
  + Gate-Record), dass `make gates` / `make docs-check` auf **genau diesem**
  Tree-Stand liefen. Mit Loop-Guard (kein Endlos-Block) und bootstrap-aware
  (erzwingt nur existierende Gates).
- **Workflow-Skelett** (optional): Slash-Command, der den 10-Schritt-
  Workflow ([`AGENTS.md`](../../../../AGENTS.md) §7) als feste Folge vorgibt.

Ziel-Artefakte (noch nicht vorhanden):

```text
.claude/settings.json              # Hook-Verdrahtung (versioniert)
.claude/hooks/tool-call-gate.sh    # Befehls-Guard (Docker-only-Stolperdraht)
.claude/hooks/handoff-gate.sh      # Gate-Lauf-Nachweis (fail-closed, loop-guard)
tools/harness/working-tree-hash.sh # inhaltsbasierter Tree-Hash
tools/harness/record-gates.sh      # Gate-Lauf-Quittung
.claude/commands/slice.md          # Workflow-Skelett (optional)
```

## Aktivierungs-Kriterium

- **Steering-Loop-Signal:** dieselbe Drift ≥ 3× beobachtet (Handoff ohne
  Gate-Lauf; versehentlicher lokaler `uv`-Lauf ausserhalb Docker), **oder**
- bewusste Harness-Haertung (Maintainability) vor der M8-Meilenstein-
  Closure.
- **Voraussetzung:** Folge-ADR fuer die Enforcement-Mechanik (Bindepunkte,
  fail-closed, Grenzen ehrlich benannt) — die Schicht ist selbst
  Harness-Code und unterliegt dem Steering-Loop.

## Out-of-scope

- Sandbox-Haerte: `python -c "…"`-Umwege bleiben moeglich; **CI ist das
  Netz** fuer das, was der Stolperdraht nicht faengt.
- Frischer-Klon-Luecke (kein State → kein Nachweis pruefbar) — ebenfalls
  CI-gedeckt.

## Bezug

- v1.2.0 Grundlagen *Durchsetzungsschicht* (Drei Bindepunkte; Vier
  Design-Eigenschaften: fail-closed, Inhalts-Nachweis, Loop-Guard,
  bootstrap-aware).
- v1.2.0 Modul 11 (Pre-completion-Checklist-Middleware).
- [`harness/conventions.md`](../../../../harness/conventions.md) `MR-005`
  (Bindung heute via ADR-Link in der Sensors-Tabelle) — diese Schicht
  ergaenzt die **mechanische** Bindung.
