# 051 — Durchsetzungsschicht: Tool-Call-Gate + Handoff-Gate + Workflow-Skelett

**Status:** Next (Scope skizziert — **v2, überarbeitet nach Review** 2026-06-19;
bereit zum Slice-Start nach Freigabe)
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

## 0. Review-Einarbeitung (2026-06-19)

v2 nach Reviewer-Findings (1 Blocker, 2 HIGH, 5 MEDIUM, 3 Nits). Adressiert:

- **BLOCKER** — `.gitignore:3` ignoriert `.claude/` komplett → versionierte Hooks
  nie committbar. **Fix:** `.gitignore`-Umbau (`dir/*` + Negation) als expliziter
  S2-Schritt **vor** S3, plus DoD-Punkt (§4 S2, §5).
- **HIGH-1** — pauschales fail-closed brickt das Tool-Call-Gate (kein Loop-Guard).
  **Fix:** fail-Verhalten **bindepunkt-spezifisch** — Tool-Call-Gate fail-**open**,
  Handoff-Gate fail-**closed** (§3, §5).
- **HIGH-2** — Loop-Lock nur auf `session_id` → Gate schweigt nach erstem Block.
  **Fix:** Lock auf `session_id` **+ Tree-Hash** (re-armt pro Tree-Stand) (§3, §5).
- **MEDIUM** — §1-noqa-Framing (noqa ist bereits gegatet), Closure-Edits
  invalidieren Quittung, JSON-Decision-Präzision (PreToolUse vs. Stop),
  `record-gates.sh` host-seitig am Aggregat-Target, Host-Parser explizit
  (`python3`-stdlib statt `jq`) — alle in §1/§3/§4 eingearbeitet.
- **Nits** — Self-Application von „uneindeutig" auf **entschieden** (Hot-Reload
  belegt) hochgezogen; Workflow-Skelett als „im Trigger optional, hier in-scope"
  benannt (§3).

## 1. Ziel

Das Regelwerk führt die **Durchsetzungsschicht** ein — die Mechanik, die aus
„die Doku sagt X" ein „der Harness erzwingt X" macht. grid-gym bindet die
Handlungs-Schleife aktuell **nicht** mechanisch: Docker-only und „`make gates`
vor Handoff" leben nur als *inferential feedforward* in
[`AGENTS.md`](../../../../AGENTS.md) — ein driftender Agent kann sie ignorieren,
ohne dass etwas blockt. (Das `# noqa`-Verbot ist die **Ausnahme**: es ist via
`noqa-gate` in `make gates` bereits mechanisch erzwungen — greift aber nur,
*wenn die Gates auch laufen*; genau das sichert das Handoff-Gate ab.) Die
Harness-Lüge „ich hab die Gates laufen lassen" bleibt unbewacht.

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

- **fail-Verhalten ist bindepunkt-spezifisch** (NICHT pauschal fail-closed — das
  wäre für das Tool-Call-Gate ein Footgun):
  - **Tool-Call-Gate (`PreToolUse`) = fail-OPEN.** Es hat **keinen** Loop-Guard;
    ein Parser-/Hook-Eigenfehler dürfte nicht *jeden* Bash-Call blocken (Session
    tot). Daher: nur bei **positivem Match** denyen; bei Eigenfehler/unlesbarem
    Input **durchwinken** — CI ist das Netz (konsistent mit „Stolperdraht, keine
    Sandbox").
  - **Handoff-Gate (`Stop`) = fail-CLOSED.** Fehlt Parser/git-Tooling oder ist
    der Input unlesbar → **blockieren**. Der Loop-Guard bindet den Blast-Radius
    auf einen Zyklus.
- **Block-Mechanik:** Exit-Code **2 + stderr** als primärer Block-Pfad (für
  `PreToolUse` *und* `Stop` eindeutig: blockt + zeigt stderr dem Agenten). Die
  JSON-Decision-Variante wird in der ADR als Alternative dokumentiert (nicht der
  Implementierungs-Pfad) — dabei **sauber getrennt**, da *nicht* austauschbar:
  `PreToolUse` blockt mit `hookSpecificOutput.permissionDecision: "deny"`, `Stop`
  blockt mit **top-level** `decision: "block"` + `reason`.
- **Loop-Guard:** Lock-Datei unter `/tmp`, geschlüsselt auf **`session_id` +
  Tree-Hash** (NICHT nur `session_id` — sonst schwiege das Gate nach dem ersten
  Block für den Rest der Session und ein neuer, ungegateter Tree-Stand rutschte
  durch). So **re-armt** der Guard bei jeder Inhaltsänderung: er blockt **einmal
  pro distinktem Tree-Stand** und terminiert weiterhin garantiert. `session_id`
  ist in der aktuellen Stop-stdin vorhanden (statt eines evtl. fehlenden Flags).
- **Inhalts-Nachweis (host-seitig):** ein inhaltsbasierter Working-Tree-Hash
  (tracked+staged Content, commit-stabil). Die `make`-Targets fahren die Gates
  *im Container* — die Quittung wird daher **host-seitig** geschrieben (der
  Stop-Hook liest host-seitig) und trägt den **Host**-Tree-Hash + Gate-Namen +
  Timestamp. Als Recipe-Zeile **nach** dem Docker-Target und **nur am
  Aggregat-Target** (`gates`, `docs-check`), nicht je Sub-Gate (sonst verfrühte
  Quittung), und nur bei **erfolgreichem** Lauf. Das Handoff-Gate vergleicht den
  aktuellen Tree-Hash gegen vorhandene Quittungen.
- **Host-JSON-Parser explizit:** `python3` (stdlib `json`) — **nicht** `jq`
  (host-seitig nicht garantiert). `python3 -c`/`-m json.tool` ohne Install ist
  vom Tool-Call-Gate-Carveout gedeckt; so blockt das Handoff-Gate nicht dauerhaft
  auf Hosts ohne `jq`.
- **bootstrap-aware:** das Handoff-Gate verlangt nur **existierende** Gates
  (`make gates` + `make docs-check`); ein nicht vorhandenes Target wird nicht
  gefordert (wächst mit der Harness-Reife).
- **Docker-only-Guard (eng gefasst):** denyt nur venv-erzeugende Befehle in
  **Befehlsposition** — `uv sync`, `uv run`, `uv pip`, `pip install`,
  `python -m venv`, nacktes `pip` — und nur, wenn NICHT in `docker …`/`make …`
  delegiert. Harmlose Fälle (`python3 -m py_compile`, `python3 -c` ohne Install)
  bleiben erlaubt (keine False-Positives gegen den Bestands-Workflow). Ehrlich
  benannte Grenze: `bash -c "…"`/`python -c "…"`-Umwege bleiben möglich.
- **Closure-Edits invalidieren die Quittung (Workflow-Konsequenz):** der
  Inhalts-Hash ist strikt — jeder Edit *nach* dem Gate-Lauf (Pflicht-`git mv`
  nach `done/`, CHANGELOG, Memory in S5) ändert den Tree-Hash ⇒ Quittung stale ⇒
  Stop blockt **einmal**, dann Loop-Guard-Release. Konsistent mit der Philosophie
  (Gates sind das Letzte vor Stop), aber bewusst benannt: **Post-Gate-Closure-
  Edits ⇒ das Gate nag't genau einmal.**
- **Self-Application-Sicherheit (entschieden):** Claude-Code-Hooks **reloaden
  mid-session** (offizielle Doku: direkte Edits an Hooks in den Settings werden
  vom File-Watcher automatisch übernommen). Damit ist die Mitigation **nötig**,
  nicht bloß vorsichtig: die Hook-Verdrahtung (`settings.json`) wird als
  **letzter** Schritt verdrahtet (nach gültiger Quittung); der eine Extra-Block
  bei der S5-Closure ist **sicher** (nicht hypothetisch) und durch den Loop-Guard
  auf **einen** Zyklus begrenzt.

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

### S2 — Nachweis-Skripte + `.gitignore`-Umbau (Voraussetzung für S3/S5) · `feat`

**Kritisch (Blocker-Fix):** `.gitignore:3` ignoriert aktuell **`.claude/`
komplett** — versionierte Hooks (S3) und `settings.json` (S5) wären sonst nicht
committbar (`git add .claude/…` macht still nichts). Ein Verzeichnis-Exclude
lässt sich nicht per simpler Negation re-includen; es braucht das `dir/*`-Muster:

```text
# .gitignore — Zeile 3 `.claude/` ersetzen durch selektives Re-Include:
.claude/*
!.claude/settings.json
!.claude/hooks/
!.claude/commands/
# .claude/settings.local.json bleibt ignoriert (lokale Permission-Allowlist)
```

Dateien dieser Tranche:

```text
tools/harness/working-tree-hash.sh   # NEU — inhaltsbasierter Tree-Hash (Host)
tools/harness/record-gates.sh        # NEU — Gate-Lauf-Quittung (Host, am Aggregat-Target)
.gitignore                           # .claude/-Re-Include (s. o.) + .harness-state/ ergänzen
Makefile                             # gates/docs-check: record-gates.sh NACH dem Docker-Target, nur am Aggregat
```

Skripte: `#!/usr/bin/env bash`, `set -euo pipefail`. Kein SPDX nötig (außerhalb
der GPL-Boundary; ruff/arch-check/spdx fassen `.sh` nicht an). `git check-ignore`
nach dem Umbau belegt, dass die drei `.claude/`-Artefakte trackbar sind und
`settings.local.json` ignoriert bleibt.

### S3 — Hooks + Workflow-Skelett · `feat`

```text
.claude/hooks/tool-call-gate.sh   # NEU — PreToolUse-Bash-Guard, fail-OPEN (Docker-only-Stolperdraht)
.claude/hooks/handoff-gate.sh     # NEU — Stop-Gate, fail-CLOSED (Tree-Hash↔Receipt, Loop-Guard session_id+hash, bootstrap-aware)
.claude/commands/slice.md         # NEU — Workflow-Skelett (10-Schritt, link-clean für d-check)
```

Das Workflow-Skelett war im Trigger als *optional* markiert; hier bewusst
**in-scope** (billig, vervollständigt den dritten Bindepunkt).

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
      bindepunkt-spezifisches fail-Verhalten, Grenzen ehrlich benannt); im ADR-Index.
- [ ] **`.gitignore` umgebaut** (Blocker): `.claude/settings.json`/`hooks/`/`commands/`
      versioniert, `.claude/settings.local.json` bleibt ignoriert — belegt via
      `git check-ignore`.
- [ ] Working-Tree-Hash-Skript deterministisch (gleicher Content → gleicher
      Hash; Edit → anderer Hash), standalone getestet.
- [ ] Gate-Quittungs-Skript schreibt valide Quittung **host-seitig** (Host-Tree-
      Hash), nur bei Gate-Erfolg, nur am Aggregat-Target (`gates`/`docs-check`).
- [ ] Tool-Call-Gate: denyt venv-Befehle außerhalb Docker/make (exit 2), lässt
      `make …`/`docker …`/`python3 -m py_compile` durch; **fail-open** bei
      Eigenfehler/fehlendem Parser (kein Loop-Guard ⇒ darf die Session nie killen).
- [ ] Handoff-Gate: blockt ohne passende Quittung (exit 2, **fail-closed**), Lock
      auf `session_id`+Tree-Hash (re-armt pro Tree-Stand), gibt beim zweiten Stop
      desselben Stands frei (Loop-Guard), passt Quittung↔Tree-Hash, bootstrap-aware.
- [ ] Workflow-Skelett-Slash-Command vorhanden, d-check-clean.
- [ ] `.claude/settings.json` versioniert; mit `/hooks` verifizierbar.
- [ ] `harness/README.md` + `AGENTS.md`-Pointer + CHANGELOG nachgezogen.
- [ ] `make gates` + `make docs-check` grün; Verification-Evidence im Slice.

## 6. Verification (Skizze)

- **Skript-Ebene (Docker-frei):** Tree-Hash zweimal → identisch; nach Edit →
  verschieden. Quittung valide im lokalen State-Verzeichnis.
- **Hook-Ebene (standalone):** Sample-stdin-JSON in beide Hooks pipen.
  Tool-Call-Gate: deny-Match (exit 2), allow (`make`/`docker`), **fail-open** bei
  kaputtem/unlesbarem Input (exit 0 — Session bleibt am Leben). Handoff-Gate:
  ohne Quittung → exit 2 + Lock; zweiter Stop **gleichen** Tree-Stands → exit 0;
  **neuer** Tree-Stand → re-armt (blockt erneut); bootstrap-aware (fehlendes Target).
- **Gate-Ebene:** `make gates` + `make docs-check` grün (d-check prüft auch den
  neuen Slash-Command + ADR-/Slice-Links).
- **Integrations-Smoke:** `.claude/settings.json` per `/hooks` (manuell, nächste
  Session); Loop-Guard schließt Self-Lockout aus.

## 7. Out-of-scope (CI-gedeckt / Folge)

- Sandbox-Härte (`python -c`/`bash -c`-Umwege) — CI ist das Netz.
- Frischer-Klon-Lücke (kein State → kein Nachweis prüfbar) — CI-gedeckt.
- [`open/052`](../open/052-carveout-modul07-audit-trichter.md) (Carveout-Modul-07)
  bleibt separater Trigger-Watch.
