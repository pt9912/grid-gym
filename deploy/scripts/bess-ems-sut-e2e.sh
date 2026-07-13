#!/usr/bin/env bash
# Slice 077 S3 — bess-ems-MQTT-only-E2E-Verifikation (ADR 0078 §2.6).
#
# Faehrt den realen cross-repo-Stack (deploy/compose.bess-ems-sut.yml): grid-gym
# publisht den breiten bess-ems-Feldenvelope je Tick, die unveraenderte bess-ems-EMS
# (offizielle Image, Digest-gepinnt) konsumiert ihn im MQTT-only-SUT-Modus. PASS-
# Kriterien (alle noetig):
#
#   1. bess-ems verlaesst den Safety-Fallback  → `"EventId":1701` (Control cycle
#      emitted command) erscheint (Gutfall, SUT-Doc §5).
#   2. KEIN `ack-timeout` (EventId 1903)       → grid-gyms command_ack-Echo (§2.9)
#      haelt bess-ems' MqttCommandSink vom Fallback ab.
#   3. der `fault`-Topic feuert                → der injizierte `cell_failure` wird
#      als `battery/single-bess-1/fault` auf dem Draht mitgeschnitten.
#   4. command_ack-Echo auf dem Draht          → `battery/single-bess-1/command/ack`
#      (bess-ems `command` → grid-gym Ack) mitgeschnitten.
#
# Nur-Sim-Netz (GG-SAFE-007): anonymes Plaintext-MQTT, keine produktive Steuerung.
set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
COMPOSE="$REPO_ROOT/deploy/compose.bess-ems-sut.yml"
PROJECT="bess-ems-sut-e2e"
DC=(docker compose -p "$PROJECT" -f "$COMPOSE")
GOOD_SIGNAL_TIMEOUT="${GOOD_SIGNAL_TIMEOUT:-150}"
OBSERVE_AFTER_GOOD="${OBSERVE_AFTER_GOOD:-90}"

cleanup() { "${DC[@]}" down -v >/dev/null 2>&1 || true; }
trap cleanup EXIT

echo "[e2e] building grid-gym runtime image (cached if unchanged)..."
docker build --target runtime -t grid-gym-runtime:latest "$REPO_ROOT" >/dev/null

echo "[e2e] starting stack (mosquitto + postgres + bess-ems + grid-gym + capture)..."
"${DC[@]}" up -d

echo "[e2e] waiting up to ${GOOD_SIGNAL_TIMEOUT}s for the good signal (EventId 1701)..."
seen_good=0
deadline=$(( SECONDS + GOOD_SIGNAL_TIMEOUT ))
while (( SECONDS < deadline )); do
  if "${DC[@]}" logs bess-ems 2>/dev/null | grep -q '"EventId":1701'; then
    seen_good=1
    break
  fi
  sleep 3
done

echo "[e2e] observing ${OBSERVE_AFTER_GOOD}s for the scheduled fault window + recovery..."
sleep "$OBSERVE_AFTER_GOOD"

bess_logs="$("${DC[@]}" logs bess-ems 2>/dev/null || true)"
capture="$("${DC[@]}" logs capture 2>/dev/null || true)"

good_cycles=$(printf '%s' "$bess_logs" | grep -c '"EventId":1701' || true)
ack_timeouts=$(printf '%s' "$bess_logs" | grep -c 'reason=ack-timeout' || true)
fault_msgs=$(printf '%s' "$capture" | grep -c 'battery/single-bess-1/fault ' || true)
ack_msgs=$(printf '%s' "$capture" | grep -c 'battery/single-bess-1/command/ack ' || true)
last_decision=$(printf '%s' "$bess_logs" | grep -oE 'decision=[a-z-]+' | tail -1 || true)

echo "--------------------------------------------------------"
echo "[e2e] good signal (EventId 1701) seen:   ${seen_good} (count=${good_cycles})"
echo "[e2e] ack-timeout warnings (want 0):      ${ack_timeouts}"
echo "[e2e] fault-topic messages on the wire:   ${fault_msgs}"
echo "[e2e] command/ack echoes on the wire:     ${ack_msgs}"
echo "[e2e] last control decision:              ${last_decision:-<none>}"
echo "--------------------------------------------------------"

fail=0
[[ "$seen_good" == 1 ]] || { echo "[e2e] FAIL: bess-ems never left the safety-fallback (no EventId 1701)"; fail=1; }
[[ "$ack_timeouts" == 0 ]] || { echo "[e2e] FAIL: ${ack_timeouts} ack-timeout(s) — command_ack echo not effective"; fail=1; }
(( fault_msgs > 0 )) || { echo "[e2e] FAIL: fault topic never fired on the wire"; fail=1; }
(( ack_msgs > 0 )) || { echo "[e2e] FAIL: no command_ack echo captured on the wire"; fail=1; }

if (( fail == 0 )); then
  echo "[e2e] PASS — an unmodified bess-ems consumes grid-gym as a conformant field over MQTT,"
  echo "[e2e]        leaves the safety-fallback, and grid-gym's ack echo prevents ack-timeout."
fi
exit "$fail"
