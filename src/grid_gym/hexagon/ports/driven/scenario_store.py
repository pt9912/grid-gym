"""ScenarioStorePort — Content-Persistenz fuer kanonisierte Szenarien
(Multi-Run-Execution S1, [`ADR 0069`] §2.1).

Driven-Port-Vertrag: legt ein kanonisiertes `Scenario` unter seinem
`scenario_hash` ab und loest es per Hash wieder auf. Damit kann ein
hash-referenzierter Lauf (`POST /runs` `scenario_hash`) seinen Content
wiederfinden, ohne dass der Hash-Erzeuger (`POST /scenarios`) und der
Lauf-Ersteller denselben Prozess-State teilen.

Der `scenario_hash` ist der SHA-256 ueber die kanonische Form
(`hexagon.core.scenario.loader.load_scenario`); Schluessel und Inhalt
sind damit konsistent (`GG-SCN-003`/`GG-SCN-004`). Implementationen
MUESSEN deterministisch sein: ein nach `put` abgelegtes `Scenario` MUSS
strukturell gleich aus `get` zurueckkommen (Frozen-Dataclass-Roundtrip).
"""

from __future__ import annotations

from typing import Protocol

from grid_gym.hexagon.core.domain.scenario import Scenario


class ScenarioStorePort(Protocol):
    """Driven-Port fuer kanonisierte Szenario-Content-Persistenz
    (ADR 0069 §2.1)."""

    def put(self, scenario_hash: str, scenario: Scenario) -> None:
        """Legt ein kanonisiertes `Scenario` unter seinem `scenario_hash` ab.

        Idempotent: ein erneutes `put` mit demselben Hash ueberschreibt
        mit strukturell identischem Inhalt (der Hash determiniert den
        Content). Implementationen werfen KEINEN Duplikat-Fehler.
        """
        ...

    def get(self, scenario_hash: str) -> Scenario | None:
        """Liest das kanonisierte `Scenario` zu einem `scenario_hash`.

        Gibt `None` zurueck, wenn kein Content unter dem Hash abgelegt
        ist (non-error Lookup — der Aufrufer entscheidet ueber 404/422).
        """
        ...

    def exists(self, scenario_hash: str) -> bool:
        """Non-error-Lookup: `True`, wenn Content unter dem Hash liegt."""
        ...
