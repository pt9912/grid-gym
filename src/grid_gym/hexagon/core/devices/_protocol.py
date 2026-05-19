"""`DeviceModel`-Protocol (M2 Welle 1, `GG-DEV-001..003`).

Definiert den Vertrag, den jedes konkrete Geraetemodell
(`hexagon/core/devices/<typ>/...` in Welle 2..5) implementieren
MUSS. ADR 0013 fixiert das Placement als **Core-internes Protocol**
(nicht Driving-Port) — Geraete sind fachliche Modelle, die der
Core konsumiert; sie sind keine externen Systeme.

**Vertragsspiegel zu `GG-DEV-001`-Akzeptanz:** "Jedes Geraetemodell
implementiert mindestens `initialize`, `tick`, `apply_command`,
`snapshot` und `telemetry`." Welle-1-Review-Schaerfung (ADR 0013
§§2.5-2.8) erweitert das um eine `device_id`-Property und eine
`from_snapshot`-Classmethod, beides als mechanisch enforcte
Protocol-Bestandteile.

**Lifecycle-Konvention** (Architecture §6 Tick-Loop-Datenfluss-
Schritt 5 + ADR 0013 §2.6):

1. Einmalig vor dem ersten Tick: `initialize(scenario_device,
   random)`. Geraete speichern `scenario_device` (id/type/params)
   und einen per-Device `RandomPort` (typischerweise
   `random.sub_port(device_id)` per ADR 0007 §5). Zweite
   `initialize`-Invocation wirft `DeviceAlreadyInitializedError`.
2. Pro Tick fuer dieses Geraet, fuer jeden Pending-Command:
   `apply_command(cmd)` — Geraet wendet den Befehl auf internen
   Zustand an und gibt einen `CommandResult`-Status zurueck
   (`accepted`/`limited`/`rejected`/...). Ordering folgt
   Scenario-Source (ADR 0013 §2.3).
3. Pro Tick: `tick(context)` — Geraet schreitet seinen Zustand um
   genau einen Tick fort und gibt `DeviceTickOutcome` (Telemetrie)
   zurueck.
4. Snapshot-Pfad: `snapshot()` liefert ein Mapping mit
   `version: int`-Erstfeld; `telemetry()` ein Tupel mit der
   aktuellen Telemetrie (gecached vom letzten Tick, ==-identisch
   zu `tick().telemetry`).

**Pre-init-Vertrag** (ADR 0013 §2.6): `tick()`, `apply_command()`,
`device_id` werfen `DeviceNotInitializedError` vor `initialize()`.
`snapshot()` und `telemetry()` sind pre-init zulaessig und liefern
minimal `{"version": N}` bzw. `()`.

**Snapshot-Vertrag**: `snapshot()` MUSS ein `Mapping[str, object]`
mit `version: int` als erstem Feld liefern (Konvention aus M1
Welle 1, geschaerft fuer Geraete in M2 Welle 0a Trigger 014).
`SnapshotEnvelope.__post_init__` prueft das beim Composition-
Aufruf (`hexagon/core/domain/snapshot.py`).

**Roundtrip-Pflicht je Geraet** (ADR 0013 §2.4, Welle-1-Review
C-3): `from_snapshot(state: Mapping[str, object]) -> Self` ist
Pflicht-Bestandteil des Protocols (Classmethod). Tests pruefen
`from_snapshot(snapshot()) == device` byte-stabil je Geraet.

**Protocol-Evolution** (ADR 0013 §2.8): das Base-Protocol ist
durch M2 closed (Welle 2..7). Post-MVP-Erweiterungen (M3 Faults,
M4 Protocol-Adapter) kommen als separate Sub-Protocols
(`FaultInjectableDevice(DeviceModel)`, etc.), nicht als
Methoden-Erweiterung des Base.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol, Self, runtime_checkable

from grid_gym.hexagon.core.domain.command import Command
from grid_gym.hexagon.core.domain.command_result import CommandResult
from grid_gym.hexagon.core.domain.device import DeviceTickContext, DeviceTickOutcome
from grid_gym.hexagon.core.domain.scenario import ScenarioDevice
from grid_gym.hexagon.core.domain.telemetry import TelemetryPoint
from grid_gym.hexagon.ports.driven.random import RandomPort


@runtime_checkable
class DeviceModel(Protocol):
    """Vertrag fuer ein Geraet im Tick-Loop (`GG-DEV-001..003`).

    Pflicht-Surface (alle Member):

    - `device_id: str` (Property) — Identitaet aus Scenario-Definition.
    - `initialize(scenario_device, random) -> None`
    - `apply_command(command) -> CommandResult`
    - `tick(context) -> DeviceTickOutcome`
    - `snapshot() -> Mapping[str, object]` (mit `version: int` als
      Erst-Feld)
    - `telemetry() -> tuple[TelemetryPoint, ...]` (==-identisch zu
      `tick().telemetry` des letzten Tick; `()` pre-init)
    - `from_snapshot(state) -> Self` (Classmethod) — Rekonstruktion
      aus einem zuvor erzeugten `snapshot()`-Mapping.

    `@runtime_checkable` erlaubt `isinstance(obj, DeviceModel)` —
    pruefen wird das Vorhandensein der Methoden- + Property-Namen
    (nicht Signaturen). Fuer scharfe Vertrags-Tests siehe
    `tests/unit/hexagon/core/devices/test_protocol_contract.py`.
    """

    @property
    def device_id(self) -> str:
        """Liefert die Geraete-ID aus dem in `initialize()`
        uebergebenen `ScenarioDevice.id` (ADR 0013 §2.7).

        Pre-init: wirft `DeviceNotInitializedError`. Welle 6 nutzt
        die Property fuer `SnapshotEnvelope.sub_snapshots`-Keys
        (`devices.<device_id>`), TickLoop fuer Tie-Breaking.
        """
        ...

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

        Zweite Invocation wirft `DeviceAlreadyInitializedError`
        (ADR 0013 §2.6; Devices sind nicht resettable — Reset-
        Workflow geht ueber `from_snapshot`).
        """
        ...

    def apply_command(self, command: Command) -> CommandResult:
        """Wendet einen Steuerbefehl auf den internen Zustand an
        (`GG-DEV-003`).

        Aufrufer-Pflicht (TickLoop): vor `tick()` im selben Tick,
        fuer jeden Pending-Command in Scenario-Source-Reihenfolge
        (ADR 0013 §2.3). Rueckgabe ist einer der `CommandResult`-
        Werte (`accepted`/`rejected`/`limited`/`expired`/`failed`/
        `ignored`, `GG-DATA-004`). Befehle ausserhalb der
        Geraete-Grenzen werden typisiert mit `limited` oder
        `rejected` beantwortet, nicht durch Exceptions.

        Pre-init: wirft `DeviceNotInitializedError`.
        """
        ...

    def tick(self, context: DeviceTickContext) -> DeviceTickOutcome:
        """Schreitet den internen Zustand um genau einen Tick fort
        und gibt die im Tick erzeugte Telemetrie zurueck.

        Determinismus-Vertrag (`GG-SIM-001/004`): gleicher Seed +
        gleiche Command-Sequenz + identischer `DeviceTickContext`-
        Stream → byte-identische `DeviceTickOutcome.telemetry`.

        Implementations-Pflicht (ADR 0013 §2.5): Geraet cached
        `DeviceTickOutcome.telemetry` intern, damit `telemetry()`
        anschliessend dasselbe Tupel zurueckliefert.

        Pre-init: wirft `DeviceNotInitializedError`.
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

        Pre-init: zulaessig, liefert `{"version": <SNAPSHOT_VERSION>}`
        ohne weiteren State (ADR 0013 §2.6).
        """
        ...

    def telemetry(self) -> tuple[TelemetryPoint, ...]:
        """Liefert den aktuellen Telemetrie-Stand des Geraets.

        Vertrag (ADR 0013 §2.5): Pure-Read-Accessor auf das
        ==-identische Tupel, das `tick(ctx_n)` zuletzt geliefert
        hat. Pre-init: `()` (leeres Tupel).

        Wird verwendet, wenn Aufrufer Telemetrie ohne Tick-
        Fortschreibung benoetigen (z. B. Sub-Snapshot-Composition,
        Aggregator-Tests wie SmartMeter in Welle 4).
        """
        ...

    @classmethod
    def from_snapshot(cls, state: Mapping[str, object]) -> Self:
        """Rekonstruiert das Geraet aus einem `snapshot()`-Mapping.

        Vertrag (ADR 0013 §2.4): `from_snapshot(snapshot()) ==
        device` ist byte-stabil. Mismatch zwischen `state["version"]`
        und der erwarteten Version wirft typisiert
        `VersionError(subsystem="<device-type>", expected=N,
        found=...)` aus dem Welle-0a-Generic-Codec
        (`hexagon/core/serialization/snapshot_codec.py`).
        Strukturelle Mismatches werfen `MissingKeysError`/
        `WrongTypeError` analog.

        Konkrete Implementationen kommen mit Welle 2..5; NullDevice
        liefert die Baseline-Implementation als Test-Pattern.
        """
        ...

    def set_run_id(self, run_id: str) -> None:
        """Setzt den `TelemetryPoint.run_id`-Wert (`GG-DATA-001`).

        Vertrag (Welle-3-Review-M-4 / Welle-6a-Review-C-1):
        `TickLoop` ruft `set_run_id(run_id)` einmal nach
        `initialize(...)` und vor dem ersten `tick(...)`, damit
        emittierte `TelemetryPoint`s die echte run_id tragen. Vor
        diesem Aufruf liefert das Device Telemetrie mit
        `run_id=""` (Sentinel `_RUN_ID_UNSET` aus den Geraete-
        Modellen). Pre-init zulaessig (Welle 6 TickLoop ruft das
        Hook ggf. vor dem `initialize`-Aufruf, falls der Loader
        die run_id schon kennt; siehe Welle-4a-Review M-4-Test
        `test_set_run_id_pre_init_is_allowed` in PV/Load/Battery/
        GridConnection/SmartMeter).
        """
        ...
