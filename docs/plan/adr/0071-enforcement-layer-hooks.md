# ADR 0071 — Durchsetzungsschicht: Tool-Call-Gate + Handoff-Gate + Workflow-Skelett via Claude-Code-Hooks (Accepted)

**Status:** Accepted — die Durchsetzungsschicht ist als
[`Slice-Plan 051`](../planning/in-progress/051-durchsetzungsschicht-enforcement-layer.md)
vollständig geliefert (S2/S3 Skripte + Hooks, S4 Public-Contract-Sync, S5 Closure).
Die Mechanik (drei Bindepunkte, bindepunkt-spezifisches fail-Verhalten,
inhaltsbasierter Nachweis) ist umgesetzt; `make gates`/`make docs-check` grün und
beide Hooks standalone verifiziert (19 Checks).
**Datum:** 2026-06-19
**Status geaendert am:** 2026-06-19 — `Proposed → Provisional` (S0; Plan v3 nach
zwei Review-Runden freigegeben, Owner-Mittragung des Voll-Mechanismus);
`Provisional → Accepted` (S5-Closure; Gates grün, Hooks standalone verifiziert).
**Bezug:**

- v1.3.0-Regelwerk-Grundlagen *Durchsetzungsschicht* (drei Bindepunkte; vier
  Design-Eigenschaften: fail-closed, Inhalts-Nachweis, Loop-Guard,
  bootstrap-aware) + Modul 11 (Pre-completion-Checklist) — das normative Vorbild.
- [`AGENTS.md`](../../../AGENTS.md) §2.1 (Docker-only), §3 (Gates vor Push), §7
  (10-Schritt-Workflow) — die heute nur *inferential* gebundenen Regeln, die diese
  ADR mechanisch verankert.
- [`harness/conventions.md`](../../../harness/conventions.md) `MR-005` — die
  Sensors-Bindung läuft heute per ADR-Link in der Sensors-Tabelle; diese Schicht
  ergänzt die **mechanische** Bindung (additive Ergänzung, kein Konflikt).
- [`harness/README.md`](../../../harness/README.md) — trägt seit S4 die
  Enforcement-Layer-Sektion + Pointer auf diese ADR.

---

## 1. Kontext

Das Regelwerk führt die **Durchsetzungsschicht** ein — die Mechanik, die aus
„die Doku sagt X" ein „der Harness erzwingt X" macht. grid-gym bindet die
Agenten-Handlungs-Schleife aktuell **nicht** mechanisch: Docker-only
([`AGENTS.md`](../../../AGENTS.md) §2.1) und „`make gates` vor Handoff" (§3) leben
nur als *inferential feedforward* — ein driftender oder vergesslicher Agent kann
sie ignorieren, ohne dass etwas blockt. Einzige Ausnahme ist das `# noqa`-Verbot:
es ist über das `noqa-gate` in `make gates` bereits mechanisch erzwungen — greift
aber nur, *wenn die Gates auch laufen*. Genau diese Voraussetzung ist unbewacht:
die [Harness-Lüge](../../../harness/conventions.md) „ich hab die Gates laufen
lassen" hat heute keinen mechanischen Wächter.

Repo-Ist vor dieser ADR: nur eine lokale Permission-Allowlist
(`.claude/settings.local.json`, gitignored), **keine** Hooks, kein versioniertes
Hook-Settings-File, keine Slash-Commands.

## 2. Decision

### 2.1 Drei Bindepunkte (2×2-Matrix)

Jeder Bindepunkt fällt in einen Quadranten der Guide/Sensor-Matrix:

| Bindepunkt | Hook | Wann | Quadrant | Wirkung |
| --- | --- | --- | --- | --- |
| **Tool-Call-Gate** | `PreToolUse` (Bash) | vor jedem Tool-Call | computational **feedforward** | venv-erzeugende Befehle außerhalb Docker/make technisch erschweren |
| **Handoff-Gate** | `Stop` | vor „fertig"-Meldung | computational **feedback** | deterministisch prüfen, dass die Gates auf **genau diesem** Tree liefen |
| **Workflow-Skelett** | Slash-Command | beim Aufgaben-Start | inferential feedforward | den 10-Schritt-Workflow ([`AGENTS.md`](../../../AGENTS.md) §7) als feste Folge vorgeben |

Zwei der drei *erzwingen* (computational); das Workflow-Skelett ist der schwächste
Bindepunkt (inferential) und bleibt das einzige, das ein Agent ignorieren kann.

### 2.2 Vier Design-Eigenschaften — mit **bindepunkt-spezifischem** fail-Verhalten

Die vier Eigenschaften der Durchsetzungsschicht (fail-closed, Inhalts-Nachweis,
Loop-Guard, bootstrap-aware) werden übernommen — mit einer entscheidenden
Differenzierung beim fail-Verhalten:

- **fail-Verhalten ist NICHT pauschal fail-closed:**
  - **Tool-Call-Gate (`PreToolUse`) = fail-OPEN.** Es hat **keinen** Loop-Guard;
    ein Parser-/Hook-Eigenfehler dürfte nicht *jeden* Bash-Call blocken (Session
    tot). Daher: nur bei **positivem Match** denyen; bei Eigenfehler/unlesbarem
    Input **durchwinken** — CI ist das Netz.
  - **Handoff-Gate (`Stop`) = fail-CLOSED.** Fehlt der Parser, die git-Tooling
    oder ist der Input unlesbar → **blockieren**. Der Loop-Guard bindet den
    Blast-Radius auf einen Zyklus.
- **Inhalts-Nachweis (host-seitig):** ein inhaltsbasierter Working-Tree-Hash über
  **tracked + staged + untracked-nicht-ignoriert** (`git ls-files` +
  `git ls-files --others --exclude-standard`). Damit deckt der Hash genau das ab,
  *was committbar ist bzw. was der Docker-Build-Context (`docker build .`)
  testet* — der Build zieht das **Dateisystem**, nicht den git-Index, also zählt
  auch eine neue, noch nicht `git add`-de Quelldatei mit. `--exclude-standard`
  lässt das (gitignorte) Receipt-Verzeichnis automatisch fallen → **kein
  Selbst-Referenz-Churn** durch die Quittung. Die `make`-Targets fahren die Gates
  *im Container* → die Quittung wird **host-seitig** geschrieben (der Stop-Hook
  liest host-seitig), trägt Host-Tree-Hash + Gate-Namen + Timestamp, als
  Recipe-Zeile **nach** dem Docker-Target und **nur am Aggregat-Target**
  (`make gates`, `make docs-check`), nicht je Sub-Gate, und nur bei Erfolg.
- **Loop-Guard:** Lock-Datei (unter `/tmp`), geschlüsselt auf **`session_id` +
  Tree-Hash** — NICHT nur `session_id` (sonst schwiege das Gate nach dem ersten
  Block für den Rest der Session, und ein neuer, ungegateter Tree-Stand rutschte
  durch). So **re-armt** der Guard pro distinktem Tree-Stand und terminiert
  garantiert. `session_id` stammt aus dem Stop-stdin (kein Verlass auf ein evtl.
  fehlendes Input-Flag).
- **bootstrap-aware:** das Handoff-Gate verlangt nur **existierende** Gates
  (`make gates` + `make docs-check`); ein nicht vorhandenes Target wird nicht
  gefordert (wächst mit der Harness-Reife).

### 2.3 Block-Mechanik, Parser, Verdrahtung

- **Block-Pfad:** Exit-Code **2 + stderr** (für `PreToolUse` *und* `Stop`
  eindeutig: blockt + zeigt stderr dem Agenten). Die JSON-Decision-Variante ist
  Alternative, nicht Implementierungs-Pfad — und ist **nicht austauschbar**:
  `PreToolUse` blockt mit `hookSpecificOutput.permissionDecision: "deny"`, `Stop`
  mit **top-level** `decision: "block"` + `reason`.
- **Host-JSON-Parser:** `python3` (stdlib `json`) — **nicht** `jq` (host-seitig
  nicht garantiert). `python3 -c` ohne Install ist vom Docker-only-Guard gedeckt.
- **Docker-only-Guard (eng gefasst):** denyt nur venv-erzeugende Befehle in
  **Befehlsposition** (`uv sync`, `uv run`, `uv pip`, `pip install`,
  `python -m venv`, nacktes `pip`) und nur, wenn NICHT in `docker …`/`make …`
  delegiert. Harmlose Fälle (`python3 -m py_compile`, `python3 -c`) bleiben erlaubt.
- **Self-Application:** Claude-Code-Hooks reloaden mid-session (File-Watcher).
  Daher wird das Settings-File als **letzter** Schritt verdrahtet (nach gültiger
  Quittung); der eine Extra-Block bei der Closure ist durch den Loop-Guard auf
  einen Zyklus begrenzt.

Artefakt-Set (Slice-Plan S2/S3/S5):

```text
.gitignore                           # .claude/-Re-Include (dir/* + Negation), .harness-state/ ergaenzen
tools/harness/working-tree-hash.sh   # inhaltsbasierter Tree-Hash (Host)
tools/harness/record-gates.sh        # Gate-Lauf-Quittung (Host, am Aggregat-Target)
.claude/hooks/tool-call-gate.sh      # PreToolUse-Bash-Guard, fail-OPEN
.claude/hooks/handoff-gate.sh        # Stop-Gate, fail-CLOSED
.claude/commands/slice.md            # Workflow-Skelett (10-Schritt)
.claude/settings.json                # Hook-Verdrahtung (versioniert; CLAUDE_PROJECT_DIR-Pfade)
```

### 2.4 Grenzen — ehrlich benannt

- **Stolperdraht, keine Sandbox.** Der Docker-only-Guard prüft Befehlspositionen;
  Interpreter-Umwege (`bash -c "…"`, `python -c "…"`) bleiben möglich. Wert: gegen
  *versehentliche* Drift, nicht gegen böswillige.
- **Frischer-Klon-Lücke.** Kein State (gelöschte Quittungen, cleaner Tree) → kein
  Nachweis prüfbar. Dort ist **CI das Netz**.
- **Tool-Call-Gate fail-open** bedeutet: ein Hook-Eigenfehler blockt nicht — die
  nicht gefangene Drift fängt CI. Diese Grenzen zu benennen ist Pflicht; ein Gate,
  das mehr Deckung vortäuscht, wäre selbst eine Harness-Lüge.

## 3. Verworfene Alternativen

- **Pauschal fail-closed über beide Gates** — verworfen: das Tool-Call-Gate hat
  keinen Loop-Guard, ein Eigenfehler würde *jeden* Bash-Call blocken (Session tot).
  Daher fail-open dort, fail-closed nur am Loop-Guard-geschützten Handoff-Gate (§2.2).
- **Loop-Lock nur auf `session_id`** — verworfen: das Gate schwiege nach dem ersten
  Block für den Rest der Session; ein neuer, ungegateter Tree-Stand rutschte durch.
  Lock auf `session_id` + Tree-Hash re-armt pro Stand (§2.2).
- **Hash nur über tracked+staged** — verworfen: `docker build .` zieht das
  Dateisystem; eine untracked, noch nicht `git add`-de Quelldatei würde real
  getestet, aber im Hash fehlen. Daher `git ls-files` + `--others --exclude-standard`.
- **`jq` als Parser** — verworfen: host-seitig nicht garantiert; `python3`-stdlib ist
  verfügbar und vom Docker-only-Guard gedeckt.
- **Status quo (nur `AGENTS.md`-Doku, inferential)** — schließt die Harness-Lüge
  „Gates liefen" nicht; genau der Anlass dieser ADR.

## 4. Konsequenzen

- NEU: versionierte Hook-Verdrahtung (`.claude/settings.json` + `.claude/hooks/`),
  Nachweis-Skripte (Working-Tree-Hash + Gate-Quittung, Host-seitig),
  Workflow-Skelett-Slash-Command, `.gitignore`-Umbau (selektives
  `.claude/`-Re-Include). Die konkreten Pfade trägt das Artefakt-Set in §2.3.
- Docker-only und „Gates vor Handoff" sind ab Closure **mechanisch** gebunden
  (computational), nicht mehr nur als AGENTS.md-Prosa (inferential) — ergänzt
  `MR-005` um die mechanische Bindungs-Ebene.
- bindepunkt-spezifisches fail-Verhalten (Tool-Call-Gate fail-open,
  Handoff-Gate fail-closed) ist dokumentierte Design-Entscheidung, kein Versehen.
- **Workflow-Konsequenz:** der Inhalts-Hash ist strikt — Post-Gate-Closure-Edits
  (`git mv` nach `done/`, CHANGELOG, Memory) ändern den Tree-Hash ⇒ das
  Handoff-Gate nag't bei der Closure genau **einmal**, dann Loop-Guard-Release.
- Out-of-Scope (CI-gedeckt): Sandbox-Härte (Interpreter-Umwege), Frischer-Klon-
  Lücke. Selbst Harness-Code → unterliegt dem Steering-Loop (Härtung am Wächter
  in Folge-Wellen).
- Status: `Accepted` (S5-Closure: `make gates`/`make docs-check` grün, beide Hooks
  standalone verifiziert — 19 Checks).
