# 051 — Durchsetzungsschicht: Tool-Call-Gate + Handoff-Gate + Workflow-Skelett

**Status:** Next (Scope skizziert — **Review ausstehend**, noch kein laufender Slice)
**Datum:** 2026-06-19
**Quelle:** Trigger-Watch [`open/051`](../open/051-durchsetzungsschicht-enforcement-layer.md)
(v1.2.0/v1.3.0-Regelwerk-Delta — Grundlagen *Durchsetzungsschicht* + Modul 11).
Aktivierung durch das zweite Trigger-Kriterium: **bewusste Harness-Härtung**
(User-Mandat).
**Bezug:**

- [`open/051`](../open/051-durchsetzungsschicht-enforcement-layer.md) — der
  auslösende Trigger-Watch (erwartete Lieferung + Out-of-scope).
- [`AGENTS.md`](../../../../AGENTS.md) §2.1 (Docker-only), §3 (Gates vor Push),
  §7 (10-Schritt-Workflow) — die heute nur *inferential* gebundenen Regeln.
- [`harness/conventions.md`](../../../../harness/conventions.md) `MR-005` — die
  Sensors-Bindung läuft heute per ADR-Link; diese Schicht ergänzt die
  **mechanische** Bindung.
- [`harness/verification.md`](../../../../harness/verification.md) — Evidence-
  Schema für die Closure.
- [`ADR 0070`](../../adr/0070-scenario-scheduled-device-commands.md) — Format-
  Vorbild für die zu schreibende Folge-ADR.

---

## 1. Ziel

Das Regelwerk führt die **Durchsetzungsschicht** ein — die fail-closed Mechanik,
die aus „die Doku sagt X" ein „der Harness erzwingt X" macht. grid-gym bindet
aktuell **keinen** der drei Bindepunkte mechanisch: Docker-only, `make gates` vor
Handoff und das `# noqa`-Verbot leben nur als *inferential feedforward* in
[`AGENTS.md`](../../../../AGENTS.md). Ein driftender Agent kann sie ignorieren;
die Harness-Lüge „ich hab die Gates laufen lassen" bleibt unbewacht.

Dieser Slice bindet die drei Punkte mechanisch — versioniert (nicht lokal) — und
benennt die Grenzen ehrlich (Stolperdraht, keine Sandbox; CI bleibt das Netz).

**Vorbedingung (Trigger-Doc):** eine **Folge-ADR** für die Enforcement-Mechanik
muss zuerst stehen — die Schicht ist selbst Harness-Code und unterliegt dem
Steering-Loop. (Geplante Nummer: 0071.)

## 2. Drei Bindepunkte (2×2-Quadranten)

| Bindepunkt | Hook | Wann | Quadrant | Wirkung |
| --- | --- | --- | --- | --- |
| Tool-Call-Gate | `PreToolUse` (Bash) | vor jedem Tool-Call | computational feedforward | venv-erzeugende Befehle außerhalb Docker/make technisch erschweren |
| Handoff-Gate | `Stop` | vor „fertig"-Meldung | computational feedback | deterministisch prüfen, dass die Gates auf **genau diesem** Tree liefen |
| Workflow-Skelett | Slash-Command | beim Aufgaben-Start | inferential feedforward | den 10-Schritt-Workflow als feste Folge vorgeben |

## 3. Design-Entscheidungen (in die Folge-ADR)

- **Block-Mechanik:** Exit-Code **2 + stderr** als primärer Block-Pfad (für
  `PreToolUse` *und* `Stop` eindeutig: blockt + zeigt stderr dem Agenten). Die
  JSON-Decision-Variante (`permissionDecision` / `decision: block`) wird in der
  ADR als Alternative dokumentiert, ist aber nicht der Implementierungs-Pfad
  (vermeidet JSON-Schema-Unsicherheit zwischen Hook-Versionen).
- **Loop-Guard:** **session-gekoppelte Lock-Datei** unter `/tmp` (Key:
  `session_id` aus dem Stop-stdin), NICHT ein evtl. fehlendes Input-Flag. Erster
  Block legt das Lock an und blockt; der zweite Stop sieht das Lock → gibt frei
  (kein Endlos-Block bei dauerhaft rotem Gate).
- **Inhalts-Nachweis:** ein inhaltsbasierter Working-Tree-Hash (tracked+staged
  Content, commit-stabil). Eine Gate-Quittung wird **nur bei erfolgreichem**
  Gate-Lauf geschrieben und trägt Tree-Hash + Gate-Namen + Timestamp. Das
  Handoff-Gate vergleicht den aktuellen Tree-Hash gegen vorhandene Quittungen.
- **bootstrap-aware:** das Handoff-Gate verlangt nur **existierende** Gates
  (`make gates` + `make docs-check`); ein nicht vorhandenes Target wird nicht
  gefordert (wächst mit der Harness-Reife).
- **fail-closed:** fehlt der JSON-Parser, die git-Tooling oder ist der Input
  unlesbar → **blockieren**, nicht durchwinken.
- **Docker-only-Guard (eng gefasst):** denyt nur venv-erzeugende Befehle in
  **Befehlsposition** — `uv sync`, `uv run`, `uv pip`, `pip install`,
  `python -m venv`, nacktes `pip` — und nur, wenn NICHT in `docker …`/`make …`
  delegiert. Harmlose Fälle (`python3 -m py_compile`, `python3 -c` ohne Install)
  bleiben erlaubt (keine False-Positives gegen den Bestands-Workflow).
- **Self-Application-Sicherheit:** ob Claude-Code-Hooks mid-session hot-reloaden,
  ist quellenseitig uneindeutig. Mitigation: die Hook-Verdrahtung wird als
  **letzter** Schritt verdrahtet (nach gültiger Quittung); der Loop-Guard
  garantiert höchstens **einen** Extra-Zyklus. Worst case damit harmlos.

## 4. Tranchierung (je eigener Commit, Auto-Push)

### S0 — Folge-ADR (Vorbedingung) · `docs`

Architekturentscheidung für die Enforcement-Mechanik (Status `Proposed →
Provisional`): drei Bindepunkte, vier Design-Eigenschaften, Block-/Loop-/Hash-
Mechanik, ehrlich benannte Grenzen, Self-Application-Note. Eintrag in den
ADR-Index.

```text
docs/plan/adr/0071-enforcement-layer-hooks.md   # NEU
docs/plan/adr/README.md                         # + Index-Zeile
```

### S1 — Slice-Aktivierung · `docs`

Move des Trigger-Docs (reiner `git mv`, eigener Commit — Rename-Detection) nach
`in-progress/`, dann Rewrite zu vollem Slice-Plan (Status `In Progress`, DoD,
Tranchen, Evidence-Platzhalter). Roadmap- + Carveout-Index-Zeile (`T-051`) auf
„in Arbeit" zeigen.

### S2 — Nachweis-Skripte · `feat`

```text
tools/harness/working-tree-hash.sh   # NEU — inhaltsbasierter Tree-Hash
tools/harness/record-gates.sh        # NEU — Gate-Lauf-Quittung
.gitignore                           # + .harness-state/ (lokales Receipt-Verzeichnis)
Makefile                             # gates/docs-check rufen bei Erfolg record-gates.sh
```

Skripte: `#!/usr/bin/env bash`, `set -euo pipefail`. Kein SPDX nötig (außerhalb
der GPL-Boundary; ruff/arch-check/spdx fassen `.sh` nicht an).

### S3 — Hooks + Workflow-Skelett · `feat`

```text
.claude/hooks/tool-call-gate.sh   # NEU — PreToolUse-Bash-Guard (Docker-only-Stolperdraht)
.claude/hooks/handoff-gate.sh     # NEU — Stop-Gate (Tree-Hash↔Receipt, Loop-Guard, bootstrap-aware)
.claude/commands/slice.md         # NEU — Workflow-Skelett (10-Schritt, link-clean für d-check)
```

### S4 — Public-Contract-Sync · `docs`

[`harness/README.md`](../../../../harness/README.md) bekommt eine Enforcement-
Layer-Subsektion (Safety/Durchsetzung) + Pointer auf die Folge-ADR;
[`AGENTS.md`](../../../../AGENTS.md) §2.1/§3 je einen Pointer-Satz (Docker-only +
Gates-vor-Handoff jetzt mechanisch via `.claude/hooks`). CHANGELOG `[Unreleased]`.

### S5 — Closure · `feat`/`docs`

```text
.claude/settings.json   # NEU — Hook-Verdrahtung als LETZTER Schritt (CLAUDE_PROJECT_DIR-Pfade)
```

`make gates` + `make docs-check` grün (+ Quittung). Verification-Evidence nach
[`harness/verification.md`](../../../../harness/verification.md) in den Slice-Plan.
Folge-ADR `Provisional → Accepted`. Carveout-Index `T-051` → Resolved.
Slice-Move nach `done/` (reiner `git mv`). Memory-Eintrag.

## 5. Definition of Done

- [ ] Folge-ADR geschrieben + akzeptiert (Bindepunkte, vier Eigenschaften,
      Grenzen ehrlich benannt); im ADR-Index.
- [ ] Working-Tree-Hash-Skript deterministisch (gleicher Content → gleicher
      Hash; Edit → anderer Hash), standalone getestet.
- [ ] Gate-Quittungs-Skript schreibt valide Quittung; nur bei Gate-Erfolg
      ausgelöst.
- [ ] Tool-Call-Gate: denyt venv-Befehle außerhalb Docker/make (exit 2), lässt
      `make …`/`docker …`/`python3 -m py_compile` durch; fail-closed bei fehlendem Parser.
- [ ] Handoff-Gate: blockt ohne passende Quittung (exit 2), gibt beim zweiten Stop
      frei (Loop-Guard), passt Quittung↔Tree-Hash, bootstrap-aware.
- [ ] Workflow-Skelett-Slash-Command vorhanden, d-check-clean.
- [ ] `.claude/settings.json` versioniert; mit `/hooks` verifizierbar.
- [ ] `harness/README.md` + `AGENTS.md`-Pointer + CHANGELOG nachgezogen.
- [ ] `make gates` + `make docs-check` grün; Verification-Evidence im Slice.

## 6. Verification (Skizze)

- **Skript-Ebene (Docker-frei):** Tree-Hash zweimal → identisch; nach Edit →
  verschieden. Quittung valide im lokalen State-Verzeichnis.
- **Hook-Ebene (standalone):** Sample-stdin-JSON in beide Hooks pipen — deny-Fall,
  allow-Fall, Loop-Guard-Release, bootstrap-aware (fehlendes Target).
- **Gate-Ebene:** `make gates` + `make docs-check` grün (d-check prüft auch den
  neuen Slash-Command + ADR-/Slice-Links).
- **Integrations-Smoke:** `.claude/settings.json` per `/hooks` (manuell, nächste
  Session); Loop-Guard schließt Self-Lockout aus.

## 7. Out-of-scope (CI-gedeckt / Folge)

- Sandbox-Härte (`python -c`/`bash -c`-Umwege) — CI ist das Netz.
- Frischer-Klon-Lücke (kein State → kein Nachweis prüfbar) — CI-gedeckt.
- [`open/052`](../open/052-carveout-modul07-audit-trichter.md) (Carveout-Modul-07)
  bleibt separater Trigger-Watch.
