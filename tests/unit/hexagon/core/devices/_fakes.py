"""Test-Doubles fuer das `DeviceModel`-Protocol (M2 Welle 1).

`NullDevice` ist eine minimale Implementation, die alle Protocol-
Member (fuenf Methoden + `device_id`-Property + `from_snapshot`-
Classmethod) mit No-Op-Verhalten erfuellt. Wird in
`test_protocol_contract.py` zur Adherence-Pruefung genutzt; M2
Welle 2..5 koennen die Klasse als Baseline-Vergleich und Plattform
fuer Tick-Loop-Integration-Tests wiederverwenden.

Konvention (siehe ADR 0013 §5): Test-Doubles liegen unter
`tests/unit/hexagon/core/devices/_fakes.py`. Konkrete Geraete-
Tests (Battery in Welle 2 etc.) duerfen `NullDevice` importieren,
um z. B. einen Tick-Loop mit gemischten Geraeten zu fahren.

Welle-1-Review (M-5): `applied_commands` ist eine **mutable
Instanz-State-Liste**. Aufrufer-Pflicht: pro Test eine frische
`NullDevice`-Instanz konstruieren — `@pytest.fixture(scope="module"|
"session")` ohne Reset verursacht Test-Leckage. Wenn Reuse noetig
ist, ruft der Test `device.applied_commands.clear()`.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Self

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import (
    DeviceTickContext,
    DeviceTickOutcome,
)
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.core.errors import (
    DeviceAlreadyInitializedError,
    DeviceNotInitializedError,
)
from grid_gym.hexagon.ports.driven.random import RandomPort


class NullDevice:
    """No-Op-Implementation des `DeviceModel`-Protocols.

    Methoden-Verhalten (Welle-1-Review-konform, ADR 0013 §§2.5-2.7):

    - `device_id` — gibt `self._scenario_device.id` zurueck oder
      wirft `DeviceNotInitializedError` pre-init.
    - `initialize(scenario_device, random)` — speichert beide
      Argumente. Zweite Invocation wirft
      `DeviceAlreadyInitializedError` (ADR 0013 §2.6).
    - `apply_command(command)` — pre-init `DeviceNotInitializedError`;
      sonst protokolliert in `applied_commands` und gibt
      `CommandResult.IGNORED` zurueck.
    - `tick(context)` — pre-init `DeviceNotInitializedError`; sonst
      gibt `DeviceTickOutcome(telemetry=())` zurueck und cached
      das Tupel in `self._last_telemetry`.
    - `snapshot()` — gibt `{"version": SNAPSHOT_VERSION}` zurueck
      (pre-init-zulaessig per ADR 0013 §2.6).
    - `telemetry()` — gibt das ==-identische Tupel vom letzten
      `tick()` zurueck (`()` pre-init).
    - `from_snapshot(state)` — Classmethod, akzeptiert
      `{"version": SNAPSHOT_VERSION}` und liefert eine frische
      NullDevice-Instanz; Mismatch wirft typed VersionError aus
      dem Welle-0a-Codec.
    """

    SNAPSHOT_VERSION: int = 1

    def __init__(self) -> None:
        self._scenario_device: ScenarioDevice | None = None
        self._random: RandomPort | None = None
        self.last_context: DeviceTickContext | None = None
        self.applied_commands: list[Command] = []
        self._last_telemetry: tuple[TelemetryPoint, ...] = ()

    # -- Pflicht-Property -------------------------------------------------

    @property
    def device_id(self) -> str:
        if self._scenario_device is None:
            raise DeviceNotInitializedError("device_id")
        return self._scenario_device.id

    # -- Optionale Test-Accessors ----------------------------------------

    @property
    def scenario_device(self) -> ScenarioDevice | None:
        """Test-Accessor; produktiver TickLoop nutzt `device_id`."""
        return self._scenario_device

    @property
    def random(self) -> RandomPort | None:
        """Test-Accessor; produktiver TickLoop nutzt `random` nicht."""
        return self._random

    # -- Lifecycle --------------------------------------------------------

    def initialize(
        self,
        scenario_device: ScenarioDevice,
        random: RandomPort,
    ) -> None:
        if self._scenario_device is not None:
            raise DeviceAlreadyInitializedError
        self._scenario_device = scenario_device
        self._random = random

    def apply_command(self, command: Command) -> CommandResult:
        if self._scenario_device is None:
            raise DeviceNotInitializedError("apply_command")
        self.applied_commands.append(command)
        return CommandResult.IGNORED

    def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
        if self._scenario_device is None:
            raise DeviceNotInitializedError("tick")
        self.last_context = context
        outcome = DeviceTickOutcome(telemetry=())
        self._last_telemetry = outcome.telemetry
        return outcome

    def snapshot(self) -> Mapping[str, object]:
        return {"version": self.SNAPSHOT_VERSION}

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        return self._last_telemetry

    # -- Welle-6a: set_run_id (Welle-3-Review-M-4 / Welle-6a-Review-C-1)

    def set_run_id(self, run_id: str) -> None:
        """No-Op: NullDevice traegt keine `run_id` in seiner
        Telemetrie (emittiert leere Tupel). Methode existiert nur,
        damit `isinstance(NullDevice(), DeviceModel)` nach der
        Welle-6a-Protocol-Erweiterung weiter haelt."""
        self._run_id: str = run_id

    # -- Roundtrip --------------------------------------------------------

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        # Welle-1-Note: NullDevice traegt keinen ueber `version`
        # hinausgehenden State; eine produktive Geraete-Implementation
        # ruft hier den Welle-0a-Generic-Codec
        # (`assert_required_keys`/`assert_int`/`VersionError`) auf.
        # Fuer den Test reicht ein direkter Vergleich, damit der
        # Roundtrip-Vertrag `from_snapshot(snapshot()) == device`
        # byte-stabil greift.
        version = state.get("version")
        if version != cls.SNAPSHOT_VERSION:
            from grid_gym.hexagon.core.errors import VersionError

            raise VersionError("null_device", expected=cls.SNAPSHOT_VERSION, found=version)
        return cls()

    # -- Equality (fuer Roundtrip-Vergleich) ------------------------------

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, NullDevice):
            return NotImplemented
        # Welle-1-NullDevice ist State-arm; Equality vergleicht den
        # post-init-relevanten Teil. Pre-init und post-init-Instanzen
        # gelten als gleich, solange beide keinen Tick-State haben.
        return self._scenario_device == other._scenario_device

    def __hash__(self) -> int:
        return hash(self._scenario_device)
