"""Protocol-Adherence-Tests fuer `FaultInjectableDevice`
(M3 Welle 1, ADR 0022 §2.1).

Pruefen:

- Ein `NullFaultInjectableDevice` (erweitert `NullDevice`) erfuellt
  das `FaultInjectableDevice`-Protocol via `isinstance(...)`
  (`@runtime_checkable`).
- Ein reines `NullDevice` (M2-Welle-1) erfuellt es **NICHT** —
  Closed-Set-Pattern aus ADR 0022 §2.1 verhindert implizite
  Fault-Faehigkeit fuer M2-Devices.
- `inject_fault(fault_type, payload)` ist Pflicht-Methode mit der
  erwarteten Signatur.
- Sub-Protocol erweitert `DeviceModel`: ein
  `FaultInjectableDevice` ist auch ein `DeviceModel`.

Welle-2-Implementer (BatteryDevice + GridConnectionDevice)
werden diese Tests pro Geraete wiederholen mit den jeweiligen
Type-/Payload-Verträgen.
"""

from __future__ import annotations

from collections.abc import Mapping

import pytest

from grid_gym.hexagon.core.devices import DeviceModel
from grid_gym.hexagon.core.faults import FaultInjectableDevice
from tests.unit.hexagon.core.devices._fakes import NullDevice

# Slice 054: fault-Sensor-Traeger fuer `make test-fault`.
pytestmark = pytest.mark.fault


class NullFaultInjectableDevice(NullDevice):
    """Test-Fake: NullDevice + leerer Fault-Hook.

    Welle-1-Test-Pattern (analog `NullDevice` aus M2-Welle-1):
    minimaler Implementer, der die Protocol-Surface erfuellt
    ohne Geraete-spezifische Semantik.
    """

    def __init__(self) -> None:
        super().__init__()
        self.injected_faults: list[tuple[str, Mapping[str, object]]] = []

    def inject_fault(
        self,
        fault_type: str,
        payload: Mapping[str, object],
    ) -> None:
        self.injected_faults.append((fault_type, payload))

    def clear_fault(self, fault_type: str) -> None:
        """Welle-2-Review-Folge H-2: symmetrische Recovery-Surface."""
        self.injected_faults.append((f"clear:{fault_type}", {}))


def test_null_fault_injectable_device_satisfies_fault_protocol() -> None:
    """ADR 0022 §2.1 Closed-Set: ein expliziter Implementer
    erfuellt `FaultInjectableDevice`."""
    device = NullFaultInjectableDevice()
    assert isinstance(device, FaultInjectableDevice)


def test_null_fault_injectable_device_is_also_device_model() -> None:
    """ADR 0022 §2.1: `FaultInjectableDevice` erweitert
    `DeviceModel` — der Implementer ist beides."""
    device = NullFaultInjectableDevice()
    assert isinstance(device, DeviceModel)


def test_null_device_without_inject_fault_fails_fault_protocol() -> None:
    """ADR 0022 §2.1 Closed-Set: ein nacktes `NullDevice` (M2-
    Welle-1) ohne `inject_fault`-Methode erfuellt das
    Sub-Protocol **NICHT**. Verhindert implizite Fault-
    Faehigkeit fuer alle M2-Geraete."""
    device = NullDevice()
    assert not isinstance(device, FaultInjectableDevice)
    assert isinstance(device, DeviceModel)  # M2-Surface unveraendert


def test_inject_fault_signature_accepts_fault_type_and_payload() -> None:
    """Pflicht-Methode hat die ADR-0022-§2.1-Signatur
    `(fault_type: str, payload: Mapping[str, object]) -> None`."""
    device = NullFaultInjectableDevice()
    device.inject_fault("cell_failure", {"affected_cell_index": 3})
    assert device.injected_faults == [("cell_failure", {"affected_cell_index": 3})]


def test_null_fault_injectable_device_snapshot_roundtrip() -> None:
    """Welle-1-Review L-4: `from_snapshot(snapshot()) ==
    device`-Vertrag (ADR 0013 §2.4) bleibt fuer das Sub-Protocol
    erhalten. `cls()` in `NullDevice.from_snapshot` produziert
    via `Self`-Typing eine Instanz der Subklasse (nicht der
    Base-Klasse), und beide erfuellen weiterhin
    `FaultInjectableDevice`."""
    device = NullFaultInjectableDevice()
    snapshot = device.snapshot()
    restored = NullFaultInjectableDevice.from_snapshot(snapshot)
    assert isinstance(restored, NullFaultInjectableDevice)
    assert isinstance(restored, FaultInjectableDevice)
    assert restored == device  # NullDevice-Equality (state-arm)
