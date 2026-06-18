"""Scenario-Command-Engine-Paket (ADR 0070, Trigger 046).

Liefert die pro Tick faelligen scenario-geplanten Steuerbefehle an den TickLoop
(`ScenarioCommandEngine`) — Schwester-Konstrukt zur `ScenarioFaultEngine`
(ADR 0059), aber Punkt-in-der-Zeit statt Zeitfenster.
"""

from grid_gym.hexagon.core.commands.scenario_command_engine import ScenarioCommandEngine

__all__ = ["ScenarioCommandEngine"]
