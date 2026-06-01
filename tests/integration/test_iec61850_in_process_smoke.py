# SPDX-License-Identifier: GPL-3.0-only
"""M4-Welle-5b-C2 Integration-Smoke fuer den IEC-61850-Adapter
(`Iec61850DeviceProtocolPort` gegen in-process
`pyiec61850.server.IedServer`).

ADR 0035 §2.5 Decision I-e: **kein** testcontainers-Container,
sondern ein in-process `IedServer` aus der gleichen Library wie
der Adapter-Client (`pyiec61850-ng`). Pattern-Praezedenz:
Welle-3-Decision-M-f (pymodbus in-process), Welle-4-Decision-O-e
(asyncua in-process), Welle-5a-Decision-D-e (dnp3-outstation
in-process). **Eine** Library wie Welle 3 und 4, **nicht** zwei
wie Welle 5a.

End-to-End-Pfad (Probe-Run-Befund 2026-06-01 verifiziert):

1. `IedServer(model_path=fixture)` laedt das libiec61850-natives
   CFG-Modell (`tests/integration/fixtures/iec61850/simpleIO.cfg`).
2. `server.start(port)` startet den TCP-Listener (intern via
   libiec61850-Daemon-Threads; kein eigener asyncio-Loop noetig —
   anders als Welle 5a).
3. `server.update_float/_int32/_visible_string` seedet die
   konfigurierten DAs mit Werten.
4. `MMSClient.read_value(reference, fc)` macht den Roundtrip via
   MMS-Wire-Protokoll.
5. Teardown: `server.stop()`. Library-internes Thread-Cleanup
   erfolgt synchron.

**Reference-Konvention** (Probe-Run-Befund): pyiec61850-ng
konkateniert MODEL-Name + LD-Name ohne Trennzeichen — das CFG
`MODEL(simpleIO){ LD(GenericIO){...} }` liefert Object-References
unter `simpleIOGenericIO/...`, **nicht** `simpleIO/GenericIO/...`.

**Decision I-f (Lizenz-Boundary):** Dieser Smoke-Test linkt gegen
`pyiec61850.server.IedServer` (GPLv3). Er ist via SPDX-Header
GPL-3.0-only lizenziert. `pyiec61850-ng` ist in
`[project.optional-dependencies.iec61850]` — Test wird mit
`pytest.importorskip` skipped, falls das Extra nicht installiert
ist.

**Wire-Compat-Limitation** (Probe-Run-Befund 2026-06-01): Bool-
Datatype mit FC=MX gibt Library-Default-Wert zurueck statt den
per `update_boolean` gesetzten Wert (CFG-DO-Struktur-Effekt; FC=ST
oder anderes DO-Pattern wuerde es korrekt machen). Welle-5b-
Spike-Smoke deckt deshalb **drei** Datatypes ab (float, int32,
string); Bool bleibt im Mock-Unit-Test verifiziert.

Cross-Cutting (Lastenheft Z. 1155-1157): Smoke ist Test-
Infrastruktur; **keine produktive Anlagensteuerung**.
"""

from __future__ import annotations

import contextlib
import socket
import time
from collections.abc import Iterator
from decimal import Decimal
from pathlib import Path
from typing import Any, Final

import pytest

# Decision I-f: Skip the entire module if `pyiec61850-ng` is not
# installed (Optional-Extra). The `importorskip` triggers a pytest
# skip with a clear message instead of an ImportError at collection
# time.
pytest.importorskip(
    "pyiec61850.server",
    reason="pyiec61850-ng not installed — run `uv sync --extra iec61850`",
)

# 2c-Mock-only-Fallback aktiviert (Welle-5b-C2, 2026-06-01):
# Probe-Run auf Python 3.12 lief sauber durch (`MMSClient.read_value`
# ↔ `IedServer(model_path=fixture)` roundtrip OK fuer float/int32/
# string). Auf dem grid-gym-Docker-Stack (Python 3.14) crasht die
# Library-`.so` aber im ersten `IedServer.start()`-Call mit Segfault
# (exit 139, Stack-Trace in `_pyiec61850.so`). Vermutete Ursache:
# pyiec61850-ng 1.6.1.2 manylinux1_x86_64-Wheel ist gegen Python
# 3.14-ABI nicht stabil — der Wheel-Build deklariert zwar Python
# 3.14-Support, aber die SWIG-Bindings sind unter 3.14-Conditions
# nicht erprobt.
#
# Decision I-e §2.5 Mock-only-Fallback explizit greift hier. Welle-5b-
# DoD bleibt erfuellbar via Mock-Unit-Tests (siehe
# `tests/unit/adapters/driven/protocol_iec61850/test_iec61850_protocol_port.py`
# — 18 Tests gegen Mock-Client decken Lifecycle + Read-Pfad + Error-
# Translation ab). Welle-6-Schaerfungs-Pfad: (a) auf Python 3.12-
# Runtime fixieren ODER (b) Library-Upgrade abwarten ODER (c) Wheel
# selbst gegen Python 3.14 rebuild.
pytestmark = pytest.mark.skip(
    reason=(
        "2c-Mock-only-Fallback aktiv (ADR 0035 §2.5): pyiec61850-ng "
        "1.6.1.2 Segfault auf Python 3.14 (Probe-Run lief auf 3.12). "
        "Welle-6-Schaerfung: Python-3.12-Runtime oder Library-Rebuild."
    )
)

from pyiec61850.server import IedServer

from grid_gym.adapters.driven.protocol_iec61850 import (
    Iec61850DeviceProtocolPort,
    Iec61850LnConfig,
    Iec61850ProtocolPortConfig,
)


_LOCALHOST: Final[str] = "127.0.0.1"
_CONNECT_TIMEOUT_S: Final[float] = 10.0
_CONNECT_INTERVAL_S: Final[float] = 0.1
_FIXTURE_PATH: Final[Path] = Path(__file__).parent / "fixtures" / "iec61850" / "simpleIO.cfg"


def _find_free_port() -> int:
    """Findet einen freien TCP-Port auf Localhost."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((_LOCALHOST, 0))
        return sock.getsockname()[1]


def _wait_for_port_open(host: str, port: int, timeout_s: float) -> None:
    """Bounded-Poll: failt nach `timeout_s`, sonst kehrt sofort
    zurueck, sobald der Server akzeptiert."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=0.2):
                return
        except OSError:
            time.sleep(_CONNECT_INTERVAL_S)
    pytest.fail(f"IEC-61850-Server :{port} nicht erreichbar innerhalb {timeout_s}s")


# Welle-5b-Datatypes (Probe-Run-Befund 2026-06-01): float/int32/
# string roundtrippen sauber mit den dokumentierten FCs. Bool ist
# offen (CFG-DO-Struktur-Issue) — Welle-6-Schaerfung. Die hier
# parametrisierten Werte werden im Smoke gegen den Server gesetzt
# und vom Adapter wieder gelesen.
_SMOKE_TARGETS: Final[list[tuple[str, str, str, str, Any]]] = [
    # (target_id, object_reference, fc, datatype, value)
    (
        "analog_voltage",
        "simpleIOGenericIO/GGIO1.AnIn1.mag.f",
        "MX",
        "float",
        230.5,
    ),
    (
        "analog_count",
        "simpleIOGenericIO/GGIO1.IntIn1.stVal",
        "MX",
        "int32",
        42,
    ),
    (
        "device_label",
        "simpleIOGenericIO/GGIO1.NamPlt.d",
        "DC",
        "string",
        "battery-1",
    ),
]


@pytest.fixture
def _iec61850_server() -> Iterator[tuple[IedServer, int]]:
    """In-process IedServer fuer Welle-5b-Smoke.

    Lifecycle: `IedServer(model_path=fixture)` -> `start(port)` ->
    `update_*` fuer Smoke-Werte -> yield -> `stop()`. Server
    arbeitet intern mit Daemon-Threads — kein eigener asyncio-Loop
    noetig (anders als Welle 5a mit dnp3-outstation).

    Welle-5b-C2-Review-Folge 2026-06-01: `IedServer(...)` und
    `server.start(port)` sind jetzt **innerhalb** des try/finally
    (vorher: ausserhalb → bei start-Exception lief das `stop()`
    im finally nicht und libiec61850-Daemon-Threads leckten).
    """
    port = _find_free_port()
    server: IedServer | None = None
    try:
        server = IedServer(model_path=str(_FIXTURE_PATH))
        server.start(port=port)
        _wait_for_port_open(_LOCALHOST, port, _CONNECT_TIMEOUT_S)
        # Seed all smoke targets.
        for _target_id, reference, _fc, datatype, value in _SMOKE_TARGETS:
            if datatype == "float":
                server.update_float(reference, float(value))
            elif datatype == "int32":
                server.update_int32(reference, int(value))
            elif datatype == "string":
                server.update_visible_string(reference, str(value))
            else:
                pytest.fail(f"Smoke-Setup: unbekannter datatype={datatype!r}")
        # Settle-Phase: TCP-Listen ist offen, aber MMS-Server-
        # internes Setup (TLS-Handshake-Vorbereitung etc.) braucht
        # noch ein paar Millisekunden, bevor der erste Client-Read
        # sauber durchgeht. Probe-Run hat ein `time.sleep(0.5)`-Wait
        # an dieser Stelle gehabt.
        time.sleep(0.5)
        yield server, port
    finally:
        if server is not None:
            with contextlib.suppress(Exception):
                server.stop()


def _build_config(port: int) -> Iec61850ProtocolPortConfig:
    """Profil mit einem Read-Target pro Welle-5b-Smoke-Eintrag."""
    points: dict[str, Iec61850LnConfig] = {}
    for target_id, reference, fc, datatype, _value in _SMOKE_TARGETS:
        points[target_id] = Iec61850LnConfig(
            object_reference=reference,
            functional_constraint=fc,  # type: ignore[arg-type]
            datatype=datatype,  # type: ignore[arg-type]
            access="read",
        )
    return Iec61850ProtocolPortConfig(
        host=_LOCALHOST,
        ied_name="SimpleIO",
        port=port,
        points=points,
        response_timeout_s=5.0,
    )


@pytest.mark.parametrize(
    ("target_id", "object_reference", "fc", "datatype", "expected_value"),
    _SMOKE_TARGETS,
    ids=[entry[0] for entry in _SMOKE_TARGETS],
)
def test_iec61850_adapter_read_roundtrip(
    _iec61850_server: tuple[IedServer, int],
    target_id: str,
    object_reference: str,
    fc: str,
    datatype: str,
    expected_value: Any,
) -> None:
    """End-to-End: Adapter connect + `read_value(reference, fc)` +
    Decode liefert den vor-konfigurierten Wert zurueck."""
    _server, port = _iec61850_server
    _ = object_reference  # Parametrierung-Doku, nicht im Body benutzt
    _ = fc
    _ = datatype
    config = _build_config(port)
    adapter = Iec61850DeviceProtocolPort(config)
    adapter.start()
    try:
        telemetry = adapter.read(target_id)
        assert telemetry is not None
        assert telemetry.device_id == target_id
        assert telemetry.source == f"protocol_iec61850.{target_id}"
        if datatype == "float":
            assert isinstance(telemetry.value, Decimal)
            assert float(telemetry.value) == pytest.approx(float(expected_value))
        elif datatype in ("int32", "string"):
            assert telemetry.value == expected_value
    finally:
        adapter.stop()


def test_iec61850_adapter_read_after_value_update(
    _iec61850_server: tuple[IedServer, int],
) -> None:
    """Wert-Update am Server wird vom Adapter im naechsten
    `read_value()`-Roundtrip gesehen."""
    server, port = _iec61850_server
    config = _build_config(port)
    adapter = Iec61850DeviceProtocolPort(config)
    adapter.start()
    try:
        telemetry = adapter.read("analog_voltage")
        assert telemetry is not None
        assert float(telemetry.value) == pytest.approx(230.5)

        # Update server value (gleiche Library — kein zweiter Process).
        server.update_float("simpleIOGenericIO/GGIO1.AnIn1.mag.f", 415.0)

        telemetry = adapter.read("analog_voltage")
        assert telemetry is not None
        assert float(telemetry.value) == pytest.approx(415.0)
    finally:
        adapter.stop()
