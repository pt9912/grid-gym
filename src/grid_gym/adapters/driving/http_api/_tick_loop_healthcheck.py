"""TickLoopHealthcheckAdapter — Adapter-Side Wall-Clock-Mess fuer
`GG-RT-001` 10ms-Modus (M6 Welle 4b-c).

Wrapt einen `TickLoop` und exposed Performance-Healthcheck-Metriken:
Tick-Dauer (p50/p95), verpasste Ticks und Backpressure-Status. Die
Mess-Substanz lebt **vollstaendig im Driving-Adapter-Layer**
(Welle-4b-c-D-1); der TickLoop in `hexagon/core/simulation/` bleibt
AC-NO-TIME-konform und unangetastet.

Implementation-Pattern:

- Der Driver (`_tick_loop_driver.py::DemoTickLoopDriver`) misst
  `time.perf_counter()` vor und nach jedem `TickLoop.tick()`-
  Aufruf und ruft `record_tick_duration(duration_ms)` am Adapter.
- Der Adapter haelt einen Ring-Buffer (`collections.deque`) der
  letzten N Tick-Dauern (Welle-4b-c-D-3: Window-Size 100).
- Der `healthcheck()`-Aufruf berechnet p50/p95/missed_ticks/
  backpressure_status und liefert das 6-Feld-JSON-Mapping.

Pflicht-`clock_source`-Parameter (Welle-4b-c-C0-Review-Folge F1)
erlaubt Test-Override via Fake-Clock-Injection; ohne diese
Injection waeren Unit-Tests real-time-abhaengig und flaky.

Backpressure-Schwelle (Welle-4b-c-D-4): jeder einzelne verpasste
Tick (Wall-Clock-Dauer > `tick_ms`) im Window setzt den Status
auf `delayed`; self-healing, sobald das Window weiterruckt und
keine Misses mehr enthaelt.

AC-NO-GOD-UTILS-konform (max 12 public methods); die public
Surface ist `record_tick_duration` + `healthcheck` + `tick_loop`-
Property.
"""

from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable
from typing import Final

from grid_gym.hexagon.ports.driving.run_execution import RunExecutionPort

# Welle-4b-c-D-3: Default-Window-Size 100 Ticks (10ms-Modus: 1 Sekunde
# Window; 100ms-Modus: 10 Sekunden; 1000ms-Modus: 100 Sekunden).
_DEFAULT_WINDOW_SIZE: Final[int] = 100

# Welle-4b-c-D-4: Backpressure-Status-Schwelle (binaer).
_STATUS_OK: Final[str] = "ok"
_STATUS_DELAYED: Final[str] = "delayed"

# pytest-benchmark default percentile-rank indices fuer die p50/p95-
# Berechnung; `int(n * 0.5)` und `int(n * 0.95)` sind sample-Rank-
# Approximationen (nearest-rank-Methode; reicht fuer Diagnose, nicht
# fuer wissenschaftliche Mess-Praezision).
_P50_RANK: Final[float] = 0.5
_P95_RANK: Final[float] = 0.95


class TickLoopHealthcheckAdapter:
    """Driving-Adapter-Side Healthcheck-Surface (Welle-4b-c-D-1).

    Wrapt einen `TickLoop` und sammelt Wall-Clock-Tick-Dauern in
    einem Ring-Buffer (Welle-4b-c-D-3 fixed window). Liefert das
    `healthcheck()`-Mapping mit p50/p95/missed_ticks/backpressure_
    status pro `GET /runs/{run_id}/healthcheck`-Endpoint-Aufruf.

    Single-Thread-asyncio-Annahme (Welle-4b-c §7-R3): der Driver
    (DemoTickLoopDriver) laeuft im FastAPI-Lifespan-Event-Loop;
    `deque.append()` und das Lesen mehrerer Elemente in
    `healthcheck()` sind atomic zueinander, weil zwischen `await`-
    Punkten keine andere Coroutine laufen kann. Multi-Thread-Driver
    waere Anti-Scope-Bruch.
    """

    __slots__ = ("_clock", "_durations_ms", "_tick_loop", "_window_size")

    def __init__(
        self,
        tick_loop: RunExecutionPort,
        *,
        window_size: int = _DEFAULT_WINDOW_SIZE,
        clock_source: Callable[[], float] = time.perf_counter,
    ) -> None:
        self._tick_loop = tick_loop
        self._window_size = window_size
        # Welle-4b-c-C0-Review-Folge F1: clock_source-Default-Argument
        # mit Test-Override-Pflicht. Test-Code injiziert Fake-Clock
        # fuer deterministische Duration-Sequences.
        self._clock = clock_source
        self._durations_ms: deque[float] = deque(maxlen=window_size)

    @property
    def tick_loop(self) -> RunExecutionPort:
        """TickLoop-Read-Access fuer Driver/Registry."""
        return self._tick_loop

    @property
    def clock_source(self) -> Callable[[], float]:
        """Clock-Source-Read-Access (z. B. fuer Driver-Mess).

        Driver ruft `self.clock_source()` vor + nach `tick_loop.tick()`
        und uebergibt die Differenz in ms an `record_tick_duration`.
        """
        return self._clock

    def record_tick_duration(self, duration_ms: float) -> None:
        """Driver-Hook: ruft pro tick() mit der gemessenen
        Wall-Clock-Dauer in Millisekunden.

        Pre-condition: `duration_ms >= 0` (negative Dauer wuerde auf
        Clock-Drift hinweisen — Welle-4b-c-Anti-Scope).
        """
        self._durations_ms.append(duration_ms)

    def healthcheck(self) -> dict[str, object]:
        """Liefert das 6-Feld-Healthcheck-Mapping (Welle-4b-c §1.2 +
        D-5 JSON-only-Output).

        Output-Felder:
        - `tick_duration_ms_p50`: Median der juengsten N Tick-Dauern.
        - `tick_duration_ms_p95`: 95-Perzentil-Jitter.
        - `missed_ticks_count`: Anzahl Ticks mit Dauer > `tick_ms`
          im aktuellen Window.
        - `backpressure_status`: `"ok"` wenn `missed_ticks_count
          == 0`; `"delayed"` sonst (Welle-4b-c-D-4 Single-Miss-
          Schwelle).
        - `tick_ms`: Konfigurierte Tick-Groesse (Convenience-Read).
        - `window_size`: Tatsaechliche Anzahl Ticks im Window
          (bis Window-Size erreicht).

        Bei leerem Window (kein record_tick_duration-Call seit Adapter-
        Init): alle numerischen Felder `0.0`/`0`; status `"ok"`.

        **Praezisions-Hinweis (Welle-4b-c-C2-Review-Folge F3):** die
        p50/p95-Berechnung nutzt nearest-rank-Approximation
        (`int(n * 0.5)`/`int(n * 0.95)`). Bei kleinen Windows
        (`n < 20`) ist die p95-Aussage entsprechend ungenau (z. B.
        `n=5` → `int(0.95*5)=4` → letzter sortierter Wert). Fuer
        MVP-Diagnose ausreichend; spaetere Schaerfung auf
        linear-interpolation (analog `numpy.percentile`) waere
        Welle-X-Material.
        """
        durations = list(self._durations_ms)
        tick_ms = self._tick_loop.tick_ms
        if not durations:
            return self._empty_window_payload(tick_ms)

        sorted_durations = sorted(durations)
        n = len(sorted_durations)
        p50_idx = min(int(n * _P50_RANK), n - 1)
        p95_idx = min(int(n * _P95_RANK), n - 1)
        missed = sum(1 for d in durations if d > tick_ms)
        status = _STATUS_DELAYED if missed > 0 else _STATUS_OK
        return {
            "tick_duration_ms_p50": sorted_durations[p50_idx],
            "tick_duration_ms_p95": sorted_durations[p95_idx],
            "missed_ticks_count": missed,
            "backpressure_status": status,
            "tick_ms": tick_ms,
            "window_size": n,
        }

    def _empty_window_payload(self, tick_ms: int) -> dict[str, object]:
        return {
            "tick_duration_ms_p50": 0.0,
            "tick_duration_ms_p95": 0.0,
            "missed_ticks_count": 0,
            "backpressure_status": _STATUS_OK,
            "tick_ms": tick_ms,
            "window_size": 0,
        }
