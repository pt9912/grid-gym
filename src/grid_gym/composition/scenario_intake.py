"""Scenario-Intake-Bridge (Composition Root; Multi-Run-Execution S1,
ADR 0069 §2.1).

Der HTTP-Adapter darf `load_scenario` (`hexagon.core.scenario`) nicht
importieren — auch nicht indirekt (`AC-ADAPTER-PURE`, 041-C3b). Diese
Composition-Root-Funktion ist die Bridge und wird per Hook-Inversion
(`_register_scenario_intake`, ADR 0054) in den HTTP-Adapter injiziert:
`grid_gym.composition.asgi` registriert sie beim Import.

Sie nimmt ein rohes Scenario-Mapping aus dem `POST /scenarios`-Body
(numerische Decimal-Felder als Strings, ADR 0069 §2.1 Variante A),
kanonisiert es ueber denselben `str → Decimal`-Pfad wie der YAML-Intake
(`scenario_yaml.coerce_scenario_mapping`), berechnet den `scenario_hash`
ueber `load_scenario` und legt das kanonisierte `Scenario` im
`ScenarioStorePort` ab — aber nur, wenn der vom Client behauptete Hash mit
dem server-berechneten uebereinstimmt (Integritaets-Check).
"""

from __future__ import annotations

from collections.abc import Mapping

from grid_gym.hexagon.core.errors import ScenarioHashMismatchError
from grid_gym.hexagon.core.scenario.loader import load_scenario
from grid_gym.hexagon.ports.driven.scenario_store import ScenarioStorePort
from grid_gym.scenario_yaml import coerce_scenario_mapping


def intake_scenario(
    store: ScenarioStorePort,
    raw_scenario: Mapping[str, object],
    claimed_hash: str,
) -> str:
    """Kanonisiert + hasht ein Scenario-Mapping und legt es im Store ab.

    Wirft Subklassen von `ScenarioError` (`hexagon.core.errors`) bei
    Schema-Verletzung (inkl. `float` an einer Decimal-Stelle — der
    Validator lehnt typisiert ab) sowie `ScenarioYamlError` bei malformed
    Decimal-Strings; der Adapter mappt beide auf HTTP 422
    `invalid_scenario`. Wirft `ScenarioHashMismatchError`, wenn
    `claimed_hash` vom server-berechneten Hash abweicht (→ 422
    `scenario_hash_mismatch`).

    Gibt bei Erfolg den (server-berechneten == behaupteten) `scenario_hash`
    zurueck.
    """
    coerced = coerce_scenario_mapping(raw_scenario)
    loaded = load_scenario(coerced)
    if loaded.scenario_hash != claimed_hash:
        raise ScenarioHashMismatchError(claimed_hash, loaded.scenario_hash)
    store.put(loaded.scenario_hash, loaded.scenario)
    return loaded.scenario_hash
