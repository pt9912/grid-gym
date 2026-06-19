#!/usr/bin/env bash
# handoff-gate.sh — Stop-Gate (ADR 0071, Slice 051).
#
# Prueft deterministisch, dass `make gates` UND `make docs-check` auf GENAU
# dem aktuellen Working-Tree liefen (Quittung `.harness-state/gates-<hash>.json`,
# geschrieben von record-gates.sh). Fehlt der Nachweis → Stop blockieren.
#
# Vier Eigenschaften (ADR 0071 §2.2):
# - fail-CLOSED: fehlt python3/git/Hash oder ist der Input unlesbar → blockieren.
# - Loop-Guard: Lock-Datei je (session_id + tree-hash). Erster Block legt sie an;
#   ein zweiter Stop desselben Stands gibt frei (kein Deadlock). Eine
#   Inhaltsaenderung erzeugt einen neuen Tree-Hash → das Gate re-armt.
# - Inhalts-Nachweis: vergleicht den aktuellen Working-Tree-Hash gegen die Quittung.
# - bootstrap-aware: verlangt nur Aggregat-Targets, die im Makefile existieren.
set -uo pipefail

LOCK_PREFIX="/tmp/grid-gym-handoff"

# block <lock-key> <stderr-reason>: blockt (exit 2) ODER gibt frei, wenn fuer
# diesen Stand schon einmal geblockt wurde (Loop-Guard; Lock bleibt liegen).
block() {
  local lock="${LOCK_PREFIX}-${1}.lock"
  if [ -f "$lock" ]; then
    exit 0
  fi
  : > "$lock" 2>/dev/null || true
  printf '%s\n' "$2" >&2
  exit 2
}

# fail-closed: ohne python3 kein Parser fuer session_id/Quittung.
if ! command -v python3 >/dev/null 2>&1; then
  block "noparse" "[handoff-gate] BLOCKED (fail-closed): python3 fehlt — Gate-Nachweis nicht pruefbar."
fi

input="$(cat)"

session_id="$(
  CLAUDE_HOOK_INPUT="$input" python3 -c 'import json, os, sys
try:
    data = json.loads(os.environ.get("CLAUDE_HOOK_INPUT", ""))
    print((data or {}).get("session_id", "") or "nosid")
except Exception:
    sys.exit(3)' 2>/dev/null
)" || session_id=""
[ -n "$session_id" ] || block "noparse" "[handoff-gate] BLOCKED (fail-closed): Stop-Input nicht lesbar (kein session_id)."

repo_root="$(git rev-parse --show-toplevel 2>/dev/null)" || repo_root=""
[ -n "$repo_root" ] || block "${session_id}-nogit" "[handoff-gate] BLOCKED (fail-closed): kein git-Repo — Tree-Hash nicht pruefbar."

tree_hash="$(bash "$repo_root/tools/harness/working-tree-hash.sh" 2>/dev/null)" || tree_hash=""
[ -n "$tree_hash" ] || block "${session_id}-nohash" "[handoff-gate] BLOCKED (fail-closed): Working-Tree-Hash nicht berechenbar (git/sha256sum?)."

# bootstrap-aware: nur existierende Aggregat-Targets verlangen.
required=""
for target in gates docs-check; do
  if grep -qE "^${target}:" "$repo_root/Makefile" 2>/dev/null; then
    required="${required} ${target}"
  fi
done
required="$(printf '%s' "$required" | xargs 2>/dev/null || true)"
[ -n "$required" ] || exit 0  # bootstrap: keine Aggregat-Gates → nicht blocken.

receipt="$repo_root/.harness-state/gates-${tree_hash}.json"
missing="$(
  CLAUDE_RECEIPT="$receipt" CLAUDE_REQUIRED="$required" python3 -c 'import json, os
receipt = os.environ["CLAUDE_RECEIPT"]
required = os.environ["CLAUDE_REQUIRED"].split()
try:
    with open(receipt, encoding="utf-8") as fh:
        have = set(json.load(fh).get("gates", []))
except Exception:
    have = set()
print(" ".join(g for g in required if g not in have))' 2>/dev/null
)" || missing="$required"  # fail-closed: Parse-Fehler → als fehlend behandeln.

if [ -n "$missing" ]; then
  block "${session_id}-${tree_hash}" "[handoff-gate] BLOCKED (fail-closed, ADR 0071): keine Gate-Quittung fuer den aktuellen Working-Tree (${tree_hash:0:12}…). Fehlend: ${missing}. Bitte 'make gates' und 'make docs-check' auf diesem Stand fahren, dann erneut beenden. (Loop-Guard: der naechste Stop desselben Stands wird freigegeben; eine spaetere Inhaltsaenderung re-armt das Gate.)"
fi

exit 0  # alle erforderlichen Gates fuer diesen Tree-Stand quittiert → Handoff erlaubt.
