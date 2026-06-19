#!/usr/bin/env bash
# record-gates.sh — host-seitige Gate-Lauf-Quittung (ADR 0071, Slice 051).
#
# Aufruf: record-gates.sh <gate-name> [<gate-name> ...]
#
# Schreibt/ergaenzt `.harness-state/gates-<tree-hash>.json` mit den bestandenen
# Gate-Namen + UTC-Zeitstempel. NUR am Aggregat-Target aufrufen (`make gates`,
# `make docs-check`) und NUR nach Erfolg: die make-Recipe kettet diese Zeile
# hinter das (im Container laufende) Gate, daher host-seitig mit Host-Tree-Hash.
# Das Handoff-Gate (Stop-Hook) liest die Quittung host-seitig und vergleicht
# ihren Tree-Hash gegen den aktuellen Working-Tree.
#
# Quittung pro Tree-Stand ist additiv/idempotent: ein `gates`- und ein
# `docs-check`-Lauf auf demselben Tree ergeben eine Quittung mit beiden Namen.
# JSON via python3-stdlib (jq host-seitig nicht garantiert; ADR 0071 §2.3).
set -euo pipefail

if [ "$#" -lt 1 ]; then
  echo "usage: record-gates.sh <gate-name> [<gate-name> ...]" >&2
  exit 2
fi

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

tree_hash="$(bash tools/harness/working-tree-hash.sh)"
state_dir=".harness-state"
mkdir -p "$state_dir"
receipt="$state_dir/gates-${tree_hash}.json"

python3 - "$receipt" "$tree_hash" "$@" <<'PY'
import datetime
import json
import os
import sys

receipt, tree_hash, *gates = sys.argv[1:]

data = {"tree_hash": tree_hash, "gates": []}
if os.path.exists(receipt):
    try:
        with open(receipt, encoding="utf-8") as fh:
            data = json.load(fh)
    except (OSError, ValueError):
        data = {"tree_hash": tree_hash, "gates": []}

merged = sorted(set(data.get("gates", [])) | set(gates))
out = {
    "tree_hash": tree_hash,
    "gates": merged,
    "recorded_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
}
with open(receipt, "w", encoding="utf-8") as fh:
    json.dump(out, fh, indent=2, sort_keys=True)
    fh.write("\n")
print(f"[record-gates] {receipt}: {merged}")
PY
