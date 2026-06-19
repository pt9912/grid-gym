#!/usr/bin/env bash
# tool-call-gate.sh — PreToolUse-Bash-Guard (ADR 0071, Slice 051).
#
# Docker-only-Stolperdraht: denyt venv-erzeugende Befehle in BEFEHLSPOSITION
# (`uv …`, nacktes `pip`/`pip3`, `python -m venv`, `python -m pip`) — aber NUR,
# wenn sie nicht ueber `docker …`/`make …` delegiert sind (dort steht `uv` als
# Argument, nicht als Kommando).
#
# fail-OPEN (ADR 0071 §2.2): PreToolUse hat KEINEN Loop-Guard — ein Parser-/
# Hook-Eigenfehler darf nicht jeden Bash-Call blocken (Session tot). Daher:
# nur bei positivem Match exit 2 (deny); bei fehlendem python3, unlesbarem
# Input oder Nicht-Bash-Tool exit 0 (durchwinken). CI ist das Netz.
#
# Grenze (ehrlich benannt): nur Befehlsposition, quote-naiv — Interpreter-
# Umwege (`bash -c "…"`, `python -c "…"`) faengt dieser Stolperdraht NICHT.
set -uo pipefail

# fail-open: ohne python3 kein Parser → durchwinken.
command -v python3 >/dev/null 2>&1 || exit 0

input="$(cat)"

CLAUDE_HOOK_INPUT="$input" python3 <<'PY'
import json
import os
import re
import shlex
import sys

raw = os.environ.get("CLAUDE_HOOK_INPUT", "")
try:
    data = json.loads(raw)
except Exception:
    sys.exit(0)  # fail-open: unlesbarer Input

if not isinstance(data, dict) or data.get("tool_name") != "Bash":
    sys.exit(0)  # nur Bash-Tool-Calls

command = (data.get("tool_input") or {}).get("command", "")
if not isinstance(command, str) or not command.strip():
    sys.exit(0)

# Top-Level-Segmente (quote-naiv = Stolperdraht): &&, ||, |, ;, &, newline.
segments = re.split(r"&&|\|\||[;\n|&]", command)
denied = []
for seg in segments:
    seg = seg.strip()
    if not seg:
        continue
    try:
        tokens = shlex.split(seg)
    except ValueError:
        continue  # unbalancierte Quotes (z. B. bash -c "…") → Grenze, ueberspringen
    # fuehrende VAR=value-Env-Zuweisungen ueberspringen
    i = 0
    while i < len(tokens) and re.match(r"^[A-Za-z_][A-Za-z0-9_]*=", tokens[i]):
        i += 1
    if i >= len(tokens):
        continue
    head = os.path.basename(tokens[i])
    rest = tokens[i + 1:]
    if head == "uv":
        denied.append(seg)  # kein lokales uv (AGENTS §2.1)
    elif head in ("pip", "pip3"):
        denied.append(seg)  # nacktes pip
    elif head == "python" or head == "python3" or re.match(r"^python3\.\d+$", head):
        # nur venv/pip-via-python denyen; -c, -m py_compile, script.py erlauben
        if "-m" in rest:
            j = rest.index("-m")
            module = rest[j + 1] if j + 1 < len(rest) else ""
            if module in ("venv", "pip"):
                denied.append(seg)

if denied:
    sys.stderr.write(
        "[tool-call-gate] BLOCKED (Docker-only, ADR 0071): venv-erzeugender "
        "Befehl in Befehlsposition ausserhalb docker/make:\n"
    )
    for seg in denied:
        sys.stderr.write(f"  - {seg}\n")
    sys.stderr.write(
        "Stattdessen ueber make/Docker fahren (z. B. 'make gates' oder "
        "'docker compose -f tests/integration/compose.yml run --rm test-runner …').\n"
        "Grenze: Interpreter-Umwege (bash -c/python -c) faengt dieser "
        "Stolperdraht nicht — CI ist das Netz.\n"
    )
    sys.exit(2)  # deny

sys.exit(0)  # allow
PY
