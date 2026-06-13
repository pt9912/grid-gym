"""Composition Root (ADR 0050 §2.5).

Paket ausserhalb von `grid_gym.adapters`, in dem Core-Builder
(`TickLoop`, `Scheduler`, `load_scenario`) mit konkreten Adaptern
verdrahtet werden duerfen, ohne `AC-ADAPTER-PURE` zu verletzen. Die
Demo-/Scenario-Bootstrap-Module wandern hierher (041-C3), damit die
HTTP-Adapter die `core.simulation`/`core.scenario`/`core.faults`-
Imports nicht mehr tragen.
"""
