"""`DeviceModel`-Protocol (M2 Welle 1, `GG-DEV-001..003`).

Definiert den Vertrag, den jedes konkrete Geraetemodell
(`hexagon/core/devices/<typ>/...` in Welle 2..5) implementieren
MUSS. ADR 0013 fixiert das Placement als **Core-internes Protocol**
(nicht Driving-Port) — Geraete sind fachliche Modelle, die der
Core konsumiert; sie sind keine externen Systeme.

**Vertragsspiegel zu `GG-DEV-001`-Akzeptanz:** "Jedes Geraetemodell
implementiert mindestens `initialize`, `tick`, `apply_command`,
`snapshot` und `telemetry`." — alle fuenf Methoden hier als
Protocol-Vertrag.

**Lifecycle-Konvention** (siehe Architecture §6 Tick-Loop-
Datenfluss-Schritt 5):

1. Einmalig vor dem ersten Tick: `initialize(scenario_device,
   random)`. Geraete speichern `scenario_device` (id/type/params)
   und einen per-Device `RandomPort` (typischerweise
   `random.sub_port(device_id)` per ADR 0007 §5).
2. Pro Tick fuer dieses Geraet, falls Pending-Commands vorliegen:
   `apply_command(cmd)` je Command — Geraet wendet den Befehl auf
   internen Zustand an und gibt einen `CommandResult`-Status zurueck
   (`accepted`/`limited`/`rejected`/...).
3. Pro Tick: `tick(context)` — Geraet schreitet seinen Zustand
   um genau einen Tick fort und gibt `DeviceTickOutcome` (Telemetrie)
   zurueck.
4. Snapshot-Pfad: `snapshot()` liefert ein Mapping mit
   `version: int`-Erstfeld; `telemetry()` ein Tupel mit der
   aktuellen Telemetrie (typischerweise gecached vom letzten Tick).

**Snapshot-Vertrag**: `snapshot()` MUSS ein `Mapping[str, object]`
mit `version: int` als erstem Feld liefern (Konvention aus M1
Welle 1, geschaerft fuer Geraete in M2 Welle 0a Trigger 014).
`SnapshotEnvelope.__post_init__` prueft das beim Composition-
Aufruf (`hexagon/core/domain/snapshot.py`).

**Roundtrip-Pflicht je Geraet** (M2 Welle 1 Konvention fuer
Welle 2..5): jede konkrete Implementation hat zusaetzlich eine
`from_snapshot(state: Mapping[str, object])`-Classmethod (nicht
Teil des Protocols, weil Classmethods im `typing.Protocol`-Vertrag
unhandlich sind). Tests pruefen `from_snapshot(snapshot()) == device`
byte-stabil je Geraet.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, runtime_checkable

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext, DeviceTickOutcome
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.ports.driven.random import RandomPort


@runtime_checkable
class DeviceModel(Protocol):
    """Vertrag fuer ein Geraet im Tick-Loop (`GG-DEV-001..003`).

    Methoden-Surface:

    - `initialize(scenario_device, random) -> None`
    - `apply_command(command) -> CommandResult`
    - `tick(context) -> DeviceTickOutcome`
    - `snapshot() -> Mapping[str, object]` (mit `version: int` als
      Erst-Feld)
    - `telemetry() -> tuple[TelemetryPoint, ...]` (aktueller Stand,
      typischerweise gecached vom letzten Tick)

    `@runtime_checkable` erlaubt `isinstance(obj, DeviceModel)` —
    pruefen wird aber nur das Vorhandensein der Methoden-Namen,
    nicht ihre Signaturen. Fuer scharfe Vertrags-Tests siehe
    `tests/unit/hexagon/core/devices/test_protocol_contract.py`.
    """

    def initialize(
        self,
        scenario_device: ScenarioDevice,
        random: RandomPort,
    ) -> None:
        """Initialisiert das Geraet aus der Scenario-Definition.

        Aufrufer-Pflicht: einmalig vor dem ersten `tick()`-Aufruf.
        `random` ist typischerweise das Ergebnis von
        `RootRandomPort.sub_port(scenario_device.id)` (ADR 0007 §5).
        Geraete speichern `scenario_device` und `random` als Instanz-
        Zustand; spaetere Aufrufe von `tick()`/`apply_command()`/
        `snapshot()` lesen daraus.
        """
        ...

    def apply_command(self, command: Command) -> CommandResult:
        """Wendet einen Steuerbefehl auf den internen Zustand an
        (`GG-DEV-003`).

        Aufrufer-Pflicht (TickLoop): vor `tick()` im selben Tick.
        Rueckgabe ist einer der `CommandResult`-Werte
        (`accepted`/`rejected`/`limited`/`expired`/`failed`/
        `ignored`, `GG-DATA-004`). Befehle ausserhalb der
        Geraete-Grenzen werden typisiert mit `limited` oder
        `rejected` beantwortet, nicht durch Exceptions.
        """
        ...

    def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
        """Schreitet den internen Zustand um genau einen Tick fort
        und gibt die im Tick erzeugte Telemetrie zurueck.

        Determinismus-Vertrag (`GG-SIM-001/004`): gleicher Seed +
        gleiche Command-Sequenz + identischer `DeviceTickContext`-
        Stream → byte-identische `DeviceTickOutcome.telemetry`.
        """
        ...

    def snapshot(self) -> Mapping[str, object]:
        """Liefert den Geraete-Zustand als `Mapping[str, object]`.

        Konvention (M1 Welle 1 / M2 Welle 0a Trigger 014): das
        Mapping enthaelt `version: int` als Erst-Feld. Der
        `SnapshotEnvelope.__post_init__` prueft diese Konvention
        und zusaetzlich Payload-Canonical-Kompatibilitaet rekursiv;
        Geraete-Implementationen brauchen die Pruefung nicht selbst
        zu duplizieren.

        Implementationen MUESSEN zusaetzlich eine
        `from_snapshot(state: Mapping[str, object]) -> DeviceModel`-
        Classmethod anbieten (nicht Teil des Protocols, weil
        Classmethods in `typing.Protocol` unhandlich sind). Tests
        pruefen `from_snapshot(snapshot()) == device` byte-stabil.
        """
        ...

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        """Liefert den aktuellen Telemetrie-Stand des Geraets.

        Typischerweise gecached vom letzten `tick()`-Aufruf; vor
        dem ersten Tick liefert die Methode `()` (leeres Tupel).
        Wird verwendet, wenn Aufrufer Telemetrie ohne Tick-
        Fortschreibung benoetigen (z. B. Sub-Snapshot-Composition,
        Aggregator-Tests).
        """
        ...
