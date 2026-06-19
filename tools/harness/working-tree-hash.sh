#!/usr/bin/env bash
# working-tree-hash.sh — inhaltsbasierter Working-Tree-Hash (ADR 0071, Slice 051).
#
# Hasht den Inhalt von tracked + staged + untracked-nicht-ignorierten Dateien.
# Damit deckt der Hash genau das ab, was committbar ist bzw. was der
# Docker-Build-Context (`docker build .`) aus dem Dateisystem zieht — eine
# neue, noch nicht `git add`-de Quelldatei zaehlt mit; gitignorte Pfade
# (inkl. `.harness-state/`) fallen via `--exclude-standard` heraus, sodass
# die Gate-Quittung den Hash nicht selbst veraendert (kein Self-Referenz-Churn).
#
# Deterministisch (NUL-sichere, LC_ALL=C-sortierte, deduplizierte Dateiliste),
# commit-stabil (inhalts- statt diff-/status-basiert). Gibt einen
# sha256-Hex-Hash auf stdout aus. Fail-loud: fehlt git/sha256sum oder ist
# kein Repo da, bricht das Skript ab (der Stop-Hook wertet das fail-closed).
set -euo pipefail

repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

# KEINE Command-Substitution in eine Variable: das wuerde die NUL-Bytes
# strippen. Stattdessen direkt durch die Pipe streamen.
{
  git ls-files -z
  git ls-files -z --others --exclude-standard
} | LC_ALL=C sort -z -u | {
  while IFS= read -r -d '' path; do
    # Tracked-aber-geloeschte Dateien (im Index, nicht auf Platte) werden
    # uebersprungen — ihre Abwesenheit aendert den Hash korrekt mit.
    if [ -f "$path" ]; then
      sha256sum -- "$path"
    fi
  done
} | sha256sum | cut -d' ' -f1
