"""Callback-Exception-Boundary fuer den paho-mqtt-Loop-Thread
(M4 Welle 2, ADR 0031 §2.4).

paho-mqtt-Callbacks (`on_message`, `on_connect`, `on_disconnect`)
laufen im `loop_start()`-internen Thread. Wenn ein Callback eine
Exception wirft, **stirbt** der Loop-Thread und der Client geht in
einen kaputten Zustand (silent disconnect + kein Reconnect). Welle-2-
Wahl in ADR 0031 §2.4 / Alternative A7: Exceptions werden geschluckt
+ geloggt, nicht propagiert.

Dieses Modul kapselt den Blind-Except in eine eigene Datei, weil
`tool.ruff.per-file-ignores` in `pyproject.toml` `BLE001` explizit
fuer `src/grid_gym/adapters/driven/protocol_*/error_translation.py`
freigibt (siehe Z. 225 dort). Alle anderen Dateien im Modul bleiben
BLE-strict.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TypeVar

T = TypeVar("T")


def safe_callback(
    label: str,
    callback: Callable[[], T],
    *,
    logger: logging.Logger,
) -> T | None:
    """Fuehrt `callback()` aus und schluckt jede Exception in den Log.

    Wird ausschliesslich an der paho-mqtt-Callback-Grenze aufgerufen
    (`on_message`, `on_connect`, `on_disconnect`). Die Wahl in
    ADR 0031 §2.4 lautet: lieber **Verlust einzelner Messages
    mit Audit-Trail im Log** als toter Loop-Thread.

    `label` ist ein menschenlesbares Tag fuer die Log-Message
    (z. B. `"on_message[device_id=battery1]"`).

    Welle 6 (Cross-Adapter-Hardening) soll diesen Pfad um
    strukturierte Error-Metriken (`MetricsPort.counter`) und ein
    optionales Dead-Letter-Topic ergaenzen — siehe ADR 0031 §4
    Konsequenzen + ADR 0024 §4.5 als Pattern-Anker.
    """
    try:
        return callback()
    except Exception:
        logger.exception("MQTT-Callback %s schlug fehl; Message ignoriert.", label)
        return None
