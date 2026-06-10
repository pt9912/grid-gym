"""Abnahme-CLI fuer GG-MVP-003 (M7-Welle-2).

Ein-Schritt-Orchestrator, der die drei MVP-Abnahme-Sub-Pruefungen
sequenziell **ohne fail-fast** fuehrt und einen maschinenlesbaren
`AbnahmeReport` als **einziges** JSON-Objekt auf stdout schreibt:

- **Step A — Szenario-Validierung**: `read_scenario_yaml` +
  `load_scenario` (Core-I/O-frei) plus Vergleich des
  `LoadedScenario.scenario_hash` gegen `EXPECTED_DEMO_SCENARIO_HASH`.
- **Step B — Deterministischer Replay**: zwei Headless-Laeufe ueber
  den geteilten `_demo_replay.run_demo_replay`-Helper (produktiver
  `build_tick_loop` + Fault-Composition), Determinismus via
  `diff_replay` (leer/volatil) plus Stream-Hash gegen
  `EXPECTED_DEMO_TELEMETRY_STREAM_HASH`.
- **Step C — Demo-Healthcheck**: `/ready`-Poll gegen den laufenden
  Demo-Stack (D-7: Aufrufer startet `make demo` vorher); erwartet
  HTTP 200 + Top-Level `status == "healthy"`.

Alle drei Sub-Step-Entries sind im JSON **immer** praesent (Vertrag
fuer CI-Consumer). Step B haengt datenseitig an Step A: faellt Step A,
laeuft Step B als `fail` mit Dependency-`reason`. Step C ist
stack-, nicht scenario-abhaengig und laeuft unabhaengig.

**stdout-Vertrag:** stdout ist JSON-only (ein `AbnahmeReport`). Alle
Logs/Tracebacks gehen nach stderr, damit `make accept | jq` ohne
Vorfilter parst.

**Tri-State-Exit (D-9):** `0` Aggregate-Pass · `1` Aggregate-Fail
(inkl. Stack-nicht-ready, fehlende/unlesbare Szenario-Datei,
Hash-Drift) · `2` Tool-Error (CLI-interner Bug: kaputtes YAML mit
`YAMLError`, Replay-Crash, Pydantic-Validation-Crash). Bei Exit 2
fehlt das stdout-JSON ganz.

`EXPECTED_DEMO_*`-Pins sind Modul-Konstanten (D-8 Option A); der
CI-Drift-Lint `tools/check_demo_scenario_pin.py` recomputed beide
gegen `deploy/scenarios/gg-demo.yaml` und bricht, wenn die YAML-Datei
ohne Pin-Update driftet.
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
import urllib.error
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any, Final, Literal

from pydantic import BaseModel, ConfigDict

from grid_gym.hexagon.core.domain.replay import (
    ReplayDeltaClassification,
    replay_sample_from_point,
)
from grid_gym.hexagon.core.domain.scenario import Scenario
from grid_gym.hexagon.core.errors import GridGymError
from grid_gym.hexagon.core.replay.diff import diff_replay
from grid_gym.hexagon.core.scenario.loader import LoadedScenario, load_scenario
from grid_gym.scenario_yaml import ScenarioYamlError, read_scenario_yaml

from _demo_replay import hash_telemetry_stream, run_demo_replay

# Repo-Root = tools/.. ; Default-Abnahme-Szenario ist das ausgelieferte Demo.
DEFAULT_DEMO_SCENARIO_PATH: Final[Path] = (
    Path(__file__).resolve().parents[1] / "deploy" / "scenarios" / "gg-demo.yaml"
)

# Default-`/ready`-URL des Demo-Stacks (D-7: Aufrufer startet `make demo`).
DEFAULT_READY_URL: Final[str] = "http://localhost:8000/ready"

# Bounded-Poll-Timeout fuer den einmaligen `/ready`-Probe (kein Retry —
# der Aufrufer haelt den Stack per D-7 bereit; ein hakender Stack ist ein
# erwartetes Step-C-`fail`, kein Tool-Error).
_READY_PROBE_TIMEOUT_S: Final[float] = 5.0

# Erwartungs-Hashes fuer das ausgelieferte `deploy/scenarios/gg-demo.yaml`.
# Update bei jeder intendierten Aenderung des Demo-Szenarios; der
# `make ci`-Gate `tools/check_demo_scenario_pin.py` recomputed beide und
# bricht bei Drift mit Angabe, welche Konstante anzupassen ist (D-8).
EXPECTED_DEMO_SCENARIO_HASH: Final[str] = (
    "00ac59d8c2fb163a826e42d3da0f584400b7592915292caebb0a3ce879e591c6"
)
EXPECTED_DEMO_TELEMETRY_STREAM_HASH: Final[str] = (
    "2d13dbb9be8a5541539a7d59b38b301a168ccd9208e364dbc54ee456fbe2b148"
)

_EXIT_PASS: Final[int] = 0
_EXIT_FAIL: Final[int] = 1
_EXIT_TOOL_ERROR: Final[int] = 2

# Einziger Pass-HTTP-Status fuer den `/ready`-Probe (Step C).
_HTTP_OK: Final[int] = 200

# Step C liefert (HTTP-Status, Body); `0` signalisiert „nicht erreichbar"
# (Connection-Refused/Timeout) — ein deterministisches Step-C-`fail`
# (Exit 1) per D-9, kein Tool-Error.
ReadyFetcher = Callable[[], "tuple[int, Mapping[str, Any]]"]


class _CheckBase(BaseModel):
    """Strict-Mode-Basis fuer die drei Sub-Check-Modelle (D-3; Pattern
    analog ADR 0045 `_BaseRequest`). `reason` ist present-on-fail
    (auf Pass `None` → via `exclude_none` nicht serialisiert)."""

    model_config = ConfigDict(strict=True, extra="forbid")

    status: Literal["pass", "fail"]
    reason: str | None = None


class ScenarioValidationCheck(_CheckBase):
    """Step A: `scenario_hash` ist auf Pass gesetzt (sonst `None`)."""

    scenario_hash: str | None = None


class ReplayDeterminismCheck(_CheckBase):
    """Step B: `diff_count` + `volatile_only` sind gesetzt, sobald der
    Replay tatsaechlich lief (auf Dependency-Fail `None`)."""

    diff_count: int | None = None
    volatile_only: bool | None = None


class DemoHealthcheckCheck(_CheckBase):
    """Step C: `ready_payload` ist bewusst **nicht** strict-typed
    (`Mapping[str, Any]`), damit additive `/ready`-Komponenten den
    Schema-Vertrag nicht brechen (D-3 + §2 Punkt 3)."""

    endpoint: str | None = None
    ready_payload: Mapping[str, Any] | None = None


class _Checks(BaseModel):
    """Die drei Sub-Checks als fixe Schema-Keys (`extra="forbid"`)."""

    model_config = ConfigDict(strict=True, extra="forbid")

    scenario_validation: ScenarioValidationCheck
    replay_determinism: ReplayDeterminismCheck
    demo_healthcheck: DemoHealthcheckCheck


class AbnahmeReport(BaseModel):
    """Maschinenlesbarer Aggregat-Status (`GG-MVP-003`).

    `overall_status` ist binaer (`pass`/`fail`); der Tri-State steckt
    nur im Exit-Code (D-9). `schema_version` ist string-monoton
    (`"1"`, `"2"`, …); ein Schema-Bump inkrementiert um genau 1."""

    model_config = ConfigDict(strict=True, extra="forbid")

    schema_version: Literal["1"] = "1"
    overall_status: Literal["pass", "fail"]
    checks: _Checks


def _run_scenario_validation(
    scenario_path: Path,
) -> tuple[ScenarioValidationCheck, LoadedScenario | None]:
    """Step A. Faengt **alle** Szenario-Daten-Fehler aus dem Lade-/
    Validier-/Hash-Pfad als Exit-1-`fail`:
    - `GridGymError` deckt `ScenarioError` (Validator) **und** die
      Canonical-Serialisierungs-Fehler der `scenario_hash`-Berechnung
      (`WrongTypeError`/`SnapshotFormatError` — z. B. ein YAML-`float`
      in einem Decimal-Allowlist-Feld, das die `str`-Koercion umgeht);
    - `ScenarioYamlError` deckt den Helper (Non-Mapping-Root + malformed
      Decimal-String);
    - `OSError` deckt fehlende/unlesbare Datei.
    `yaml.YAMLError` (Parser-Bruch) ist **kein** `GridGymError`, wird
    nicht gefangen und eskaliert zu Exit 2 (D-9 — CLI-internal)."""
    try:
        loaded = load_scenario(read_scenario_yaml(scenario_path))
    except (OSError, ScenarioYamlError, GridGymError) as exc:
        return (
            ScenarioValidationCheck(status="fail", reason=f"{type(exc).__name__}: {exc}"),
            None,
        )
    if loaded.scenario_hash != EXPECTED_DEMO_SCENARIO_HASH:
        return (
            ScenarioValidationCheck(
                status="fail",
                scenario_hash=loaded.scenario_hash,
                reason=(
                    f"scenario hash drift: expected {EXPECTED_DEMO_SCENARIO_HASH}, "
                    f"got {loaded.scenario_hash}"
                ),
            ),
            loaded,
        )
    return (
        ScenarioValidationCheck(status="pass", scenario_hash=loaded.scenario_hash),
        loaded,
    )


def _run_replay_determinism(scenario: Scenario | None) -> ReplayDeterminismCheck:
    """Step B. `scenario is None` (Step A gefehlt) → Dependency-`fail`
    ohne Replay-Lauf. Sonst zwei Headless-Laeufe; ein echter
    Replay-Crash bleibt **ungefangen** und eskaliert zu Exit 2 (D-9 —
    Headless-Runner-Crash ist CLI-internal, kein Sub-Step-Signal)."""
    if scenario is None:
        return ReplayDeterminismCheck(
            status="fail",
            reason="dependency: scenario load failed (see scenario_validation)",
        )
    seed = scenario.simulation.seed
    stream_a = run_demo_replay(scenario, seed=seed)
    stream_b = run_demo_replay(scenario, seed=seed)
    samples_a = [replay_sample_from_point(point, index) for index, point in enumerate(stream_a)]
    samples_b = [replay_sample_from_point(point, index) for index, point in enumerate(stream_b)]
    deltas = diff_replay(samples_a, samples_b, tick_ms=1000, volatile_fields=frozenset())
    diff_count = len(deltas)
    volatile_only = all(
        delta.classification == ReplayDeltaClassification.VOLATIL for delta in deltas
    )
    stream_hash = hash_telemetry_stream(stream_a)
    determinism_ok = diff_count == 0 or volatile_only
    hash_ok = stream_hash == EXPECTED_DEMO_TELEMETRY_STREAM_HASH
    if determinism_ok and hash_ok:
        return ReplayDeterminismCheck(
            status="pass", diff_count=diff_count, volatile_only=volatile_only
        )
    reasons: list[str] = []
    if not determinism_ok:
        reasons.append(f"non-volatile replay diff: {diff_count} deltas")
    if not hash_ok:
        reasons.append(
            f"stream hash drift: expected {EXPECTED_DEMO_TELEMETRY_STREAM_HASH}, got {stream_hash}"
        )
    return ReplayDeterminismCheck(
        status="fail",
        diff_count=diff_count,
        volatile_only=volatile_only,
        reason="; ".join(reasons),
    )


def _run_demo_healthcheck(ready_fetcher: ReadyFetcher) -> DemoHealthcheckCheck:
    """Step C. HTTP-Connection-Fail / Non-200 / `status != "healthy"`
    sind **erwartete** Step-C-`fail`-Signale (Exit 1), kein Tool-Error
    (D-9). Der Fetcher signalisiert Nicht-Erreichbarkeit mit Status
    `0`."""
    endpoint = "/ready"
    status_code, payload = ready_fetcher()
    if status_code == 0:
        return DemoHealthcheckCheck(
            status="fail",
            endpoint=endpoint,
            reason=f"ready endpoint not reachable ({payload.get('error', 'unknown')})",
        )
    if status_code != _HTTP_OK:
        return DemoHealthcheckCheck(
            status="fail",
            endpoint=endpoint,
            ready_payload=payload,
            reason=f"ready endpoint returned HTTP {status_code}",
        )
    ready_status = payload.get("status")
    if ready_status != "healthy":
        return DemoHealthcheckCheck(
            status="fail",
            endpoint=endpoint,
            ready_payload=payload,
            reason=f"ready status not healthy: {ready_status}",
        )
    return DemoHealthcheckCheck(status="pass", endpoint=endpoint, ready_payload=payload)


def build_report(scenario_path: Path, ready_fetcher: ReadyFetcher) -> AbnahmeReport:
    """Orchestriert Step A → B → C ohne fail-fast und aggregiert
    `overall_status` erst nach Step C. Alle drei Sub-Step-Entries sind
    im Ergebnis immer praesent."""
    scenario_check, loaded = _run_scenario_validation(scenario_path)
    scenario = loaded.scenario if loaded is not None else None
    replay_check = _run_replay_determinism(scenario)
    healthcheck = _run_demo_healthcheck(ready_fetcher)
    checks = _Checks(
        scenario_validation=scenario_check,
        replay_determinism=replay_check,
        demo_healthcheck=healthcheck,
    )
    sub_checks = (scenario_check, replay_check, healthcheck)
    overall: Literal["pass", "fail"] = (
        "pass" if all(check.status == "pass" for check in sub_checks) else "fail"
    )
    return AbnahmeReport(overall_status=overall, checks=checks)


def http_ready_fetcher(url: str) -> ReadyFetcher:
    """Produktiver `/ready`-Fetcher (stdlib-urllib, analog
    `tools/wait_otel_collector.py`). Connection-Fehler → `(0, {...})`;
    Non-JSON-Body → `(code, {...})`. Wirft selbst nicht — Step C
    klassifiziert den Tuple-Inhalt."""

    def fetch() -> tuple[int, Mapping[str, Any]]:
        try:
            with urllib.request.urlopen(url, timeout=_READY_PROBE_TIMEOUT_S) as response:
                body = response.read()
                code = int(response.status)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return 0, {"error": repr(exc)}
        try:
            payload = json.loads(body)
        except json.JSONDecodeError as exc:
            return code, {"error": f"non-JSON ready body: {exc}"}
        if not isinstance(payload, dict):
            return code, {"error": "ready body is not a JSON object"}
        return code, payload

    return fetch


def _parse_args(argv: Sequence[str] | None) -> tuple[Path, str]:
    parser = argparse.ArgumentParser(
        prog="accept",
        description="GG-MVP-003 Abnahme-CLI: Szenario-Validierung + Replay-Determinismus "
        "+ Demo-Healthcheck als maschinenlesbarer JSON-Status.",
    )
    parser.add_argument(
        "scenario_path",
        nargs="?",
        type=Path,
        default=DEFAULT_DEMO_SCENARIO_PATH,
        help="Pfad zur Demo-Szenario-YAML (Default: deploy/scenarios/gg-demo.yaml).",
    )
    parser.add_argument(
        "--ready-url",
        default=DEFAULT_READY_URL,
        help=f"`/ready`-URL des laufenden Demo-Stacks (Default: {DEFAULT_READY_URL}).",
    )
    args = parser.parse_args(argv)
    return args.scenario_path, args.ready_url


def main(argv: Sequence[str] | None = None, *, ready_fetcher: ReadyFetcher | None = None) -> int:
    """CLI-Entry. stdout traegt **nur** das `AbnahmeReport`-JSON;
    Tracebacks gehen nach stderr. Exit-Code per D-9 (0/1/2)."""
    scenario_path, ready_url = _parse_args(argv)
    fetcher = ready_fetcher if ready_fetcher is not None else http_ready_fetcher(ready_url)
    # Tri-State-Exit-2-Grenze (D-9): jeder ungefangene CLI-interne Fehler
    # (YAMLError, Replay-Crash, Pydantic-Validation-Crash) ist ein
    # Tool-Error mit Traceback auf stderr — bewusst breiter `except` (per
    # `tools/accept.py`-Per-File-Ignore BLE001 in pyproject.toml).
    try:
        report = build_report(scenario_path, fetcher)
    except Exception:
        traceback.print_exc()
        return _EXIT_TOOL_ERROR
    sys.stdout.write(report.model_dump_json(exclude_none=True) + "\n")
    return _EXIT_PASS if report.overall_status == "pass" else _EXIT_FAIL


if __name__ == "__main__":
    raise SystemExit(main())
