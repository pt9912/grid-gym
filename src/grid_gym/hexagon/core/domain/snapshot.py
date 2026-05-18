"""Snapshot-Envelope-Konvention (Vorbereitung Welle 4, `GG-SIM-005`).

`SnapshotEnvelope` ist der Mini-Wrapper, der die Versionierung
mehrerer Sub-Snapshots (Scheduler, `RandomPort` per `ADR 0007 §5.1`,
TickLoop-State) traegt. Welle 1 fixiert die Konvention, Welle 4
baut den `TickLoop.snapshot()`-Pfad darauf auf.

Konvention (Slice-Plan M1 Welle 1 §3):
„Jedes Sub-Snapshot-Dokument im Snapshot-Envelope hat einen
`version: int`-Schluessel als erstes Feld." `canonical_json`
sortiert Dict-Schluessel lexikographisch, eine konkrete JSON-Feld-
Reihenfolge ist also nicht erzwingbar — nur die Anwesenheits-Pflicht
des `version`-Schluessels. `__post_init__` validiert sie typisiert,
damit Welle-4-Implementierer kein zweites Versionierungs-Schema
einfuehren.

**Payload-Canonical-Check (M2 Welle 0a, Trigger 014 Item 5):**
seit 2026-05-18 prueft `__post_init__` zusaetzlich rekursiv, dass
jeder Sub-Snapshot ausschliesslich canonical_json-faehige Werte
enthaelt (`hexagon/core/serialization/snapshot_codec.py::
assert_payload_canonical_compatible`). Damit erkennt der Envelope
einen Float-/Bytes-Smuggler frueh und typisiert
(`WrongTypeError(subsystem="snapshot_envelope", ...)` — Subklasse
von `SnapshotFormatError`), nicht erst beim spaeteren
`canonical_json`-Encoder.

Die Vertragsverletzungs-Klassen leben in `hexagon/core/errors.py`,
weil AC-DOMAIN-FROZEN unter `domain/**` nur Datenklassen zulaesst
(Frozen-Dataclasses, `FrozenModel`-Vererbung, `Enum`-Subklassen) —
Exception-Subklassen sind hier eine Ebene hoeher angesiedelt.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from grid_gym.hexagon.core.errors import (
    MissingSubSnapshotVersionError,
    NonIntegerSubSnapshotVersionError,
)
from grid_gym.hexagon.core.serialization.snapshot_codec import (
    assert_payload_canonical_compatible,
)


@dataclass(frozen=True, slots=True)
class SnapshotEnvelope:
    """Wrapper um benannte Sub-Snapshots mit Versionierungs-Konvention.

    Felder:
    - `version`: Envelope-Schema-Version (aktuell `1`); Welle-4-
      Bumps gehen ueber eine Folge-ADR.
    - `run_id`: verbindet zu `RunMetadata.run_id`.
    - `simulation_time`: Sim-Zeit des Snapshots in ms.
    - `sub_snapshots`: benannte Sub-Snapshots; jeder Wert MUSS einen
      `version: int`-Schluessel tragen.

    `__post_init__` validiert die Sub-Snapshot-Konvention frueh —
    nicht erst beim `canonical_json`-Aufruf — damit fehlerhafte
    Konstruktion im Aufrufer ankommt, nicht im Encoder. Iteration
    laeuft ueber `sorted(...)`, damit die zuerst geworfene Fehler-
    Meldung bei mehreren Verstoessen deterministisch derselbe
    Sub-Snapshot-Name ist (passt zur `canonical_json`-Sortier-
    Konvention).

    Sub-Klassen, die `__post_init__` ueberschreiben, MUESSEN
    `super().__post_init__()` aufrufen — sonst entfaellt die
    Sub-Snapshot-Validierung leise.
    """

    version: int
    run_id: str
    simulation_time: int
    sub_snapshots: Mapping[str, Mapping[str, object]]

    def __post_init__(self) -> None:
        for name, payload in sorted(self.sub_snapshots.items()):
            if "version" not in payload:
                raise MissingSubSnapshotVersionError(name)
            value = payload["version"]
            # bool ist `int`-Subklasse — explizit ausschliessen
            # (Schema-Versionen sind Ganzzahlen, nicht Wahrheitswerte).
            if isinstance(value, bool) or not isinstance(value, int):
                raise NonIntegerSubSnapshotVersionError(name, type(value).__name__)
            # Payload-Canonical-Check (M2 Welle 0a, Trigger 014 Item 5):
            # rekursive Pruefung, dass der Sub-Snapshot ausschliesslich
            # canonical_json-faehige Werte enthaelt. Wirft typisiert
            # WrongTypeError(subsystem="snapshot_envelope", ...) bei
            # Float-/Bytes-/Complex-/Non-str-Key-Eintraegen.
            assert_payload_canonical_compatible(
                payload, "snapshot_envelope", f"sub_snapshots.{name}"
            )
