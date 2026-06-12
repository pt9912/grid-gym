"""Geteilte Konstanten der `DeviceProtocolPort`-Composition-
Wrapper (M7-Welle-3b-C2-Review-Folge F4).

Genau ein Best-Effort-Catch-Tupel fuer die Callback-/Adapter-
Nebenkanaele beider Wrapper (`_protocol_otel_wrap.py` →
TracePort-Adapter-Bugs, ADR 0024 §2.4;
`_protocol_comm_failure_wrap.py` → `on_alarm`-Nebenkanal,
ADR 0053 §2.4). Vorher lebte das Tupel wortgleich in beiden
Modulen („identisches Pattern"-Kommentar) — Single-Source
verhindert Drift bei kuenftigen Erweiterungen.

Semantik (Slice 034 F9 + ADR 0024 §2.4): bekannte
Callback-Bug-Klassen werden geschluckt (der Haupt-Pfad hat
Vorrang vor dem Nebenkanal), unbekannte Exceptions propagieren
als sichtbares Signal statt stiller Swallow.
"""

from __future__ import annotations

BEST_EFFORT_CALLBACK_EXCEPTIONS: tuple[type[BaseException], ...] = (
    RuntimeError,
    AttributeError,
    TypeError,
    ValueError,
    KeyError,
    OSError,
)
