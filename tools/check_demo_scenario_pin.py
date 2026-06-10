"""CI-Drift-Lint fuer die zwei Demo-Abnahme-Pins (M7-Welle-2, D-8).

Recomputed beide Erwartungs-Hashes gegen das ausgelieferte
`deploy/scenarios/gg-demo.yaml` und vergleicht sie mit den
Modul-Konstanten in `tools/accept.py`:

- `EXPECTED_DEMO_SCENARIO_HASH` ← `LoadedScenario.scenario_hash`,
- `EXPECTED_DEMO_TELEMETRY_STREAM_HASH` ← `hash_telemetry_stream(
  run_demo_replay(scenario, seed=scenario.simulation.seed))`.

Beide Pfade laufen ueber **dieselbe** geteilte Substanz wie
`tools/accept.py` (`grid_gym.scenario_yaml` + `_demo_replay`), damit
Lint und CLI bauartbedingt identisch rechnen.

Zweck: eine YAML-Whitespace-/Key-Order-/Wert-Aenderung in
`gg-demo.yaml` flippt die Hashes und bricht **diesen** `make ci`-Gate
im selben PR — statt erst nachgelagert im Abnahme-Smoke. Bei Drift
nennt der Lint, **welche** Konstante in `tools/accept.py` anzupassen
ist. Exit `0` bei Match, `1` bei Drift.
"""

from __future__ import annotations

import sys

from grid_gym.hexagon.core.scenario.loader import load_scenario
from grid_gym.scenario_yaml import read_scenario_yaml

import accept
from _demo_replay import hash_telemetry_stream, run_demo_replay


def main() -> int:
    path = accept.DEFAULT_DEMO_SCENARIO_PATH
    loaded = load_scenario(read_scenario_yaml(path))
    scenario_hash = loaded.scenario_hash
    stream = run_demo_replay(loaded.scenario, seed=loaded.scenario.simulation.seed)
    stream_hash = hash_telemetry_stream(stream)

    drifts: list[tuple[str, str, str]] = []
    if scenario_hash != accept.EXPECTED_DEMO_SCENARIO_HASH:
        drifts.append(
            ("EXPECTED_DEMO_SCENARIO_HASH", accept.EXPECTED_DEMO_SCENARIO_HASH, scenario_hash)
        )
    if stream_hash != accept.EXPECTED_DEMO_TELEMETRY_STREAM_HASH:
        drifts.append(
            (
                "EXPECTED_DEMO_TELEMETRY_STREAM_HASH",
                accept.EXPECTED_DEMO_TELEMETRY_STREAM_HASH,
                stream_hash,
            )
        )

    if drifts:
        print(
            f"[check_demo_scenario_pin] DRIFT against {path.name}: "
            f"{len(drifts)} pin(s) out of date.",
            file=sys.stderr,
        )
        for name, expected, actual in drifts:
            print(
                f"[check_demo_scenario_pin]   {name}\n"
                f"      expected:   {expected}\n"
                f"      recomputed: {actual}\n"
                f"      → update tools/accept.py with the recomputed value "
                f"if the gg-demo.yaml change is intended.",
                file=sys.stderr,
            )
        return 1

    print(
        f"[check_demo_scenario_pin] {path.name} scenario + telemetry-stream pins match "
        f"tools/accept.py constants."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
