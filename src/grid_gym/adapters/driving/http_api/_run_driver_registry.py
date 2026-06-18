"""RunDriverRegistry — per-`run_id` Driver-Lifecycle fuer Multi-Run-Execution
(S2, ADR 0069 §2.2).

Generalisierung der single-run `TickLoopRegistry` (ADR 0039 Decision 13) zu
einem Mapping `{run_id: RunDriver}`, das pro aktivem Lauf einen Driver haelt,
startet und stoppt — mit **bounded concurrency** (konfigurierbares Maximum;
Ueberschuss → `RunConcurrencyLimitError` statt unbounded Task-Spawn) und einem
`stop_all()` fuer die Lifespan-Shutdown-Naht (jeder Driver garantiert
`finalize()` ueber seine eigene Run-End-Naht, ADR 0067).

Adapter-intern (kein Driving-Port-Slot, analog `TickLoopRegistry`); `RunDriver`
ist ein strukturelles Protocol, das `DemoTickLoopDriver` erfuellt (S3 fuettert
die Registry mit echten Drivern ueber `POST /runs/{id}/start`).
"""

from __future__ import annotations

from typing import Final, Protocol, cast

from fastapi import Request

from grid_gym.hexagon.core.errors import (
    RunAlreadyActiveError,
    RunConcurrencyLimitError,
)

_DEFAULT_MAX_ACTIVE_RUNS: Final[int] = 8
"""Gewaehlter Default fuer gleichzeitig aktive Laeufe. Konfigurierbar pro
Registry-Instanz; Re-Eval unter Last (`GG-RT-001`-Backpressure)."""


class RunDriver(Protocol):
    """Strukturelles Driver-Protokoll fuer die `RunDriverRegistry`.

    `DemoTickLoopDriver` erfuellt es (`start()` synchron-idempotent,
    `stop()` async + `finalize()`-garantiert, ADR 0067).
    """

    def start(self) -> None:
        """Startet den Driver (idempotent)."""
        ...

    async def stop(self) -> None:
        """Stoppt den Driver + garantiert `finalize()` (ADR 0067)."""
        ...


class RunDriverRegistry:
    """Adapter-internes `{run_id: RunDriver}`-Mapping mit bounded concurrency
    (Multi-Run-Execution S2, ADR 0069 §2.2)."""

    def __init__(self, *, max_active_runs: int = _DEFAULT_MAX_ACTIVE_RUNS) -> None:
        self._drivers: dict[str, RunDriver] = {}
        self._max_active_runs = max_active_runs

    def register_and_start(self, run_id: str, driver: RunDriver) -> None:
        """Registriert + startet einen Driver fuer `run_id`.

        Wirft `RunAlreadyActiveError`, wenn fuer `run_id` schon ein Driver
        laeuft; `RunConcurrencyLimitError`, wenn das Maximum aktiver Laeufe
        erreicht ist — Reject **vor** dem Start (kein verwaister Task).
        """
        if run_id in self._drivers:
            raise RunAlreadyActiveError(run_id)
        if len(self._drivers) >= self._max_active_runs:
            raise RunConcurrencyLimitError(self._max_active_runs)
        driver.start()
        self._drivers[run_id] = driver

    async def stop(self, run_id: str) -> None:
        """Stoppt + entfernt den Driver fuer `run_id`; no-op, wenn keiner
        aktiv ist."""
        driver = self._drivers.pop(run_id, None)
        if driver is not None:
            await driver.stop()

    async def stop_all(self) -> None:
        """Stoppt + entfernt **alle** aktiven Driver (Lifespan-Shutdown-Naht).
        Jeder `stop()` garantiert `finalize()` (ADR 0067)."""
        for driver in list(self._drivers.values()):
            await driver.stop()
        self._drivers.clear()

    def is_active(self, run_id: str) -> bool:
        """`True`, wenn fuer `run_id` ein Driver aktiv registriert ist."""
        return run_id in self._drivers

    @property
    def active_count(self) -> int:
        """Anzahl aktuell aktiver Driver."""
        return len(self._drivers)


class _RunDriverRegistryNotConfiguredError(RuntimeError):
    """Konfigurations-Fehler: HTTP-API ohne `RunDriverRegistry` gestartet
    (Multi-Run-Execution S2/S3, ADR 0069 §2.2/§2.4).

    Erbt von `RuntimeError`, damit FastAPI das auf `500 Internal Server
    Error` mappt — analog `_TickLoopRegistryNotConfiguredError`.
    """

    def __init__(self) -> None:
        super().__init__(
            "RunDriverRegistry is not configured. Call "
            "grid_gym.adapters.driving.http_api._run_driver_setup."
            "configure_run_driver_registry before serving requests."
        )


def get_run_driver_registry(request: Request) -> RunDriverRegistry:
    """Dependency-Provider fuer die `RunDriverRegistry` (Multi-Run-Execution
    S3, ADR 0069 §2.4). Pattern analog `get_tick_loop_registry`.

    Wirft `_RunDriverRegistryNotConfiguredError`, wenn die App nicht
    konfiguriert ist — der `POST /runs/{id}/start`-Endpoint benoetigt die
    Registry.
    """
    registry = getattr(request.app.state, "run_driver_registry", None)
    if registry is None:
        raise _RunDriverRegistryNotConfiguredError
    return cast(RunDriverRegistry, registry)
