"""ReadinessProbeAdapter — Driving-Adapter-Side `/ready`-Probe
(M6 Welle 6; `GG-DEPLOY-006` Three-State-Readiness, Lastenheft
Z. 1876-1879).

Welle-6-D-2 + D-6 verankern den Adapter im **Driving-Adapter-Layer**
(`GG-AR-PORT-DRV-007` als Adapter-Surface, Pattern analog
`_tick_loop_healthcheck.py`). **Kein** `hexagon/ports/driving/
health.py`-Core-Driving-Port: die Probe-Orchestrierung beruehrt
Driven-Side-Externals (Postgres-`ping()`, UI-Template-Load,
TickLoop-Adapter-Mapping), die in einem Core-basierten Driving-Port
eine Schichten-Verletzung waeren.

Vier **Lastenheft-Pflicht-Komponenten** (Welle-6-D-2):

- ``api``: Liveness-konforme Trivial-Probe — der `/ready`-Endpoint
  laeuft im selben Prozess; antwortet er, ist `api` per Definition
  erreichbar. Synchron, ohne Timeout-Bedarf.
- ``ui``: HTML-Template-Load-Probe (`ui._templates.ui_surface_loads`)
  — belegt, dass das UI-Surface auflaedt. I/O-behaftet → unter
  Timeout in einem Thread.
- ``db``: `RunRepositoryPort.ping()` — In-Memory → immer `True`,
  Postgres → `SELECT 1`. I/O-behaftet → unter Timeout in einem
  Thread.
- ``simulation``: TickLoop-Backpressure-Mapping. Liegt ein
  `TickLoopHealthcheckAdapter` vor (Sub-Form A), wird
  `backpressure_status` gemappt (`ok` → `healthy`, `delayed` →
  `degraded`). Liegt keiner vor (Sub-Form B; Compose-`sleep
  infinity`-Stub oder Demo-Stack ohne TickLoop), `degraded` mit
  Stub-Ursache. Synchron (In-Memory-Adapter-Read).

Aggregations-Regel (Welle-6-D-2): jede Komponente `unhealthy` →
Top-Level `unhealthy`; sonst eine `degraded` → `degraded`; sonst
`healthy`. HTTP-Status-Mapping (im `app.py`-Endpoint): `200` bei
`healthy`/`degraded`, `503` bei `unhealthy`.

Die I/O-Probes (`ui`, `db`) laufen parallel via `asyncio.gather`
mit Per-Probe-Timeout (`asyncio.wait_for`); ein Timeout oder eine
Backend-Exception wird ueber `return_exceptions=True` eingefangen
und auf `unhealthy` gemappt (kein breites `except` im Adapter-Code).
"""

from __future__ import annotations

import asyncio
from typing import Final

from grid_gym.adapters.driving.http_api._schemas import (
    ComponentState,
    ComponentStatus,
    ReadyResponse,
)
from grid_gym.adapters.driving.http_api._tick_loop_healthcheck import (
    TickLoopHealthcheckAdapter,
)
from grid_gym.adapters.driving.ui._templates import ui_surface_loads
from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort

# Welle-6-D-2: Per-Probe-Timeout fuer die I/O-Probes (≤ 1 s).
_PROBE_TIMEOUT_S: Final[float] = 1.0

# Welle-6-D-2 Sub-Form B: ehrliche Stub-Ursache fuer den
# `simulation`-Service ohne aktiven TickLoop (Compose-`sleep
# infinity`-Stub ist erwartetes Verhalten, kein `unhealthy`-Ausfall).
_SIMULATION_STUB_REASON: Final[str] = (
    "simulation service is sleep-infinity stub (M2-Welle-7-pattern "
    "reactivates produktiv-TickLoop runner)"
)


class ReadinessProbeAdapter:
    """Driving-Adapter-Side Readiness-Probe fuer `GET /ready`
    (M6 Welle 6, `GG-DEPLOY-006`).

    Konstruktor-Injektion der Probe-Abhaengigkeiten: das
    `RunRepositoryPort` (db-Probe) und optional ein
    `TickLoopHealthcheckAdapter` (simulation-Probe Sub-Form A).
    Der Endpoint-Handler in `app.py` resolved beide aus dem
    App-State und ruft `check()`.
    """

    __slots__ = ("_run_repository", "_simulation_healthcheck", "_timeout_s")

    def __init__(
        self,
        *,
        run_repository: RunRepositoryPort,
        simulation_healthcheck: TickLoopHealthcheckAdapter | None = None,
        timeout_s: float = _PROBE_TIMEOUT_S,
    ) -> None:
        self._run_repository = run_repository
        self._simulation_healthcheck = simulation_healthcheck
        self._timeout_s = timeout_s

    async def check(self) -> ReadyResponse:
        """Probt alle vier Komponenten und aggregiert den Three-
        State-Status (Welle-6-D-2).

        Die I/O-Probes (`ui`/`db`) laufen parallel unter Per-Probe-
        Timeout; `api`/`simulation` sind synchron (kein I/O). Jede
        Probe-Exception (inkl. `TimeoutError`) wird via
        `return_exceptions=True` eingefangen und auf `unhealthy`
        gemappt.
        """
        ui_result, db_result = await asyncio.gather(
            self._probe_ui(),
            self._probe_db(),
            return_exceptions=True,
        )
        components: dict[str, ComponentStatus] = {
            "api": self._build_api_status(),
            "ui": _result_to_status(ui_result),
            "db": _result_to_status(db_result),
            "simulation": self._build_simulation_status(),
        }
        return ReadyResponse(status=_aggregate(components), components=components)

    async def _probe_ui(self) -> ComponentStatus:
        await asyncio.wait_for(asyncio.to_thread(ui_surface_loads), self._timeout_s)
        return ComponentStatus(state="healthy")

    async def _probe_db(self) -> ComponentStatus:
        reachable = await asyncio.wait_for(
            asyncio.to_thread(self._run_repository.ping),
            self._timeout_s,
        )
        if not reachable:
            return ComponentStatus(
                state="unhealthy",
                reason="run repository ping returned False",
            )
        return ComponentStatus(state="healthy")

    def _build_api_status(self) -> ComponentStatus:
        # Liveness-konforme Trivial-Probe (Welle-6-D-2): der Endpoint
        # laeuft im selben Prozess — antwortet er, ist `api`
        # erreichbar. Markiert die API-Surface als auditiert in der
        # Komponenten-Tabelle (Lastenheft-Wortlaut-Erfuellung).
        return ComponentStatus(state="healthy")

    def _build_simulation_status(self) -> ComponentStatus:
        if self._simulation_healthcheck is None:
            return ComponentStatus(state="degraded", reason=_SIMULATION_STUB_REASON)
        return _simulation_status_from_report(self._simulation_healthcheck.healthcheck())


def _result_to_status(result: ComponentStatus | BaseException) -> ComponentStatus:
    """Mappt ein `asyncio.gather(return_exceptions=True)`-Ergebnis:
    eine Exception (Timeout, Backend-Fehler) → `unhealthy` mit
    Diagnose; sonst der von der Probe gelieferte `ComponentStatus`."""
    if isinstance(result, BaseException):
        return ComponentStatus(
            state="unhealthy",
            reason=f"probe failed: {type(result).__name__}: {result}",
        )
    return result


def _aggregate(components: dict[str, ComponentStatus]) -> ComponentState:
    """Welle-6-D-2 Aggregations-Regel: jede `unhealthy` → `unhealthy`;
    sonst eine `degraded` → `degraded`; sonst `healthy`."""
    states = {component.state for component in components.values()}
    if "unhealthy" in states:
        return "unhealthy"
    if "degraded" in states:
        return "degraded"
    return "healthy"


def _simulation_status_from_report(report: dict[str, object]) -> ComponentStatus:
    """Mappt das `TickLoopHealthcheckAdapter.healthcheck()`-Output
    (Welle-6-D-2 Sub-Form A): `backpressure_status == "ok"` →
    `healthy`; `"delayed"` → `degraded` mit `missed_ticks_count`-
    Zaehlwert in der Ursache. Ein `unhealthy`-Pfad ueber den
    TickLoop-Adapter existiert nicht — `delayed` und `missed > 0`
    sind im Adapter gekoppelt (Welle-6-D-2-Begruendung)."""
    if report["backpressure_status"] == "ok":
        return ComponentStatus(state="healthy")
    missed = report["missed_ticks_count"]
    return ComponentStatus(
        state="degraded",
        reason=f"tick delayed; missed {missed} ticks",
    )
