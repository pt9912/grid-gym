"""Callback-Exception-Boundary fuer den paho-mqtt-Loop-Thread (Slice 077 S2,
ADR 0078 §2.9).

Das `command_ack`-Echo laeuft im paho-`on_message`-Callback, also im
`loop_start()`-internen Thread. Wirft der Callback eine Exception, **stirbt** der
Loop-Thread (silent disconnect, kein Reconnect). Wie in `protocol_mqtt`
(ADR 0031 §2.4 / Alternative A7) werden Callback-Exceptions darum geschluckt +
geloggt, nicht propagiert — ein Fremd-/Fehl-Command-Payload darf den Publisher
nicht toeten.

Der Blind-Except lebt in dieser eigenen Datei, weil `tool.ruff.per-file-ignores`
+ die `arch_check`-`typed-errors-exempt`-Liste `BLE001`/AC-TYPED-ERRORS gezielt fuer
`.../error_translation.py`-Module freigeben (Muster `protocol_*/error_translation.py`).
Alle anderen Dateien des Adapters bleiben BLE-strict.
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

    Ausschliesslich an der paho-mqtt-Callback-Grenze (`on_message`) aufgerufen. Die
    Wahl (analog ADR 0031 §2.4): lieber **ein verlorenes Ack mit Audit-Trail im Log**
    als ein toter Loop-Thread → bess-ems' `MqttCommandSink` liefe sonst in
    `ack-timeout`→Safe-Stop. `label` ist ein menschenlesbares Log-Tag (z. B.
    `"command-ack[topic=battery/asset-1/command]"`).
    """
    try:
        return callback()
    except Exception:
        logger.exception("bess-ems-MQTT-Callback %s schlug fehl; ignoriert.", label)
        return None
