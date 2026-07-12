"""`DeviceServerPort` Driving-Port (Field-Server Pull-Seite, ADR 0075 §2.1).

Driving-Port-Vertrag fuer die **Server-/Outstation-Rolle** der Field-Server-
Surface: ein externes EMS (System-under-Test, z. B. `bess-ems`) als Feldbus-
**Master** pollt grid-gyms **simulierte** Geraete. Motivation ist die HIL/SUT-
Anbindung (`GG-TEST-004`, HIL-Konkretisierung; keine eigene `GG-*`-ID,
ADR 0075 §7).

**Schwester-Port (ADR 0075 §2.1)**: `DeviceServerPort` (Pull, hier) und der
driven-seitige `FieldPublishPort` (Push, Slice 073) sind zwei getrennt
typisierte Ports (ADR 0011-Schwester-Muster) — **kein** geteilter Vertrag. Der
gemeinsame Hebel ist die **Current-Value-Projektion**
(`adapters/driving/_field_current_value.CurrentValueProjection`, ADR 0075 §2.2):
ein Pull-Server serviert die Register aus dem letzten emittierten Wert pro
`(device_id, metric)` — er konsumiert **nicht** den fire-and-forget-
`TelemetryStreamPort` (der kann „letzter Wert JETZT" nicht liefern).

**Server-Lifecycle (ADR 0075 §2.4; NICHT der ADR-0030-connect-Spiegel)**:
`start()` = bind + listen + serve; **Bind-in-use ist ein harter Fehler vor dem
ersten Tick** (kein Lazy-Connect-Analogon). `stop()` = Listener graceful
drainen/schliessen. Beide werden **driver-getrieben** in der Kompositions-Schicht
gerufen (der Driver haelt den Run-Loop + die Projektion; ADR 0075 §2.3) — der
blockierende bind/close laeuft im Worker-Thread (`asyncio.to_thread`), damit er
den API-Event-Loop nicht stallt.

**Stateless aus Replay-Sicht (ADR 0075 §2.5)**: Server-State (Socket, Register-
Map-Materialisierung, Subscriber) ist **volatil**, kein `SnapshotEnvelope`-Slot.
Read-Serving ist replay-sicher (die Projektion ist eine reine Funktion der
emittierten Telemetrie). **Read-only**: der Inbound-Write→`Command`-Pfad ist
ausgegliedert (ADR 0075 §7).

**Sim-/Test-Charakter (ADR 0075 §2.6, `GG-SAFE-007`/`GG-NONGOAL-001`)**: keine
produktive Anlagensteuerung; Nur-Sim-Netz (kein Auth/TLS).

**Adapter (Slice 074)**: `ModbusDeviceServerAdapter` unter
`adapters/driving/device_server_modbus/` (`pymodbus`-Server).
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from grid_gym.hexagon.core.errors import GridGymError


@runtime_checkable
class DeviceServerPort(Protocol):
    """Driving-Port fuer die Field-Server-Pull-Seite (ADR 0075 §2.1).

    Pflicht-Surface:

    - `start() -> None`: bind + listen + serve. Wird vom Driver **vor** dem
      ersten Tick gerufen (Kompositions-Schicht, ADR 0075 §2.3/§2.4).
      Bind-in-use → `DeviceServerPortStartError` (harter Fehler; der Lauf
      startet nicht).
    - `stop() -> None`: Listener graceful drainen + schliessen. Wird vom Driver
      am Run-Ende (auch im Exception-Pfad) gerufen; idempotent nach
      erfolglosem/nicht-erfolgtem `start()`.

    Der Server serviert die Reads aus der Current-Value-Projektion, die ihm bei
    Konstruktion gereicht wird (nicht Teil der Port-Surface — der Driver
    aktualisiert die Projektion pro Tick).

    Adapter-Verantwortung (analog `DeviceProtocolPort`, ADR 0030 §4):

    1. **Sync-Surface**: alle Methoden sync; ein async-Server-Stack
       (`pymodbus`) marshalt adapter-intern (eigener Loop-Thread).
    2. **Idempotenz**: `stop()` nach erfolglosem `start()` ist No-op.
    3. **Volatile State**: kein Snapshot-Slot; Rebind ist Adapter-Sache.
    4. **Sim-/Test-Doku**: Modul-Docstring dokumentiert den Sim-/Test-Charakter
       (`GG-SAFE-007`); Nur-Sim-Netz.
    """

    def start(self) -> None:
        """Bind + listen + serve. Bind-in-use → `DeviceServerPortStartError`
        (harter Fehler vor dem ersten Tick)."""
        ...

    def stop(self) -> None:
        """Listener graceful drainen + schliessen. Idempotent nach
        erfolglosem/nicht-erfolgtem `start()`. Harte Close-Fehler →
        `DeviceServerPortStopError`."""
        ...


# ---------------------------------------------------------------------------
# Error-Hierarchie (ADR 0075 §2.1/§2.4; Muster analog `DeviceProtocolPortError`)
# ---------------------------------------------------------------------------


class DeviceServerPortError(GridGymError):
    """Wurzel der `DeviceServerPort`-Vertragsverletzungen (ADR 0075).

    Adapter werfen typed Subclasses (`DeviceServerPortStartError`,
    `DeviceServerPortStopError`).
    """


class DeviceServerPortStartError(DeviceServerPortError):
    """`start()` ist fehlgeschlagen — Server konnte nicht binden/listen.

    Insbesondere **Bind-in-use** (Port belegt) ist ein harter Fehler vor dem
    ersten Tick (ADR 0075 §2.4; **kein** Lazy-Connect-Analogon wie beim driven
    `DeviceProtocolPort`).
    """


class DeviceServerPortStopError(DeviceServerPortError):
    """`stop()` ist fehlgeschlagen — Server konnte nicht sauber
    drainen/schliessen.

    Idempotenz-Vertrag (ADR 0075 §2.1): `stop()` nach erfolglosem/nicht-
    erfolgtem `start()` ist No-op — diese Exception ist nur fuer **harte**
    Close-Probleme reserviert.
    """
