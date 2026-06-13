"""TickLoopRegistry — HTTP-Adapter-internes Multi-Run-Mapping
(M5 Welle 4a, ADR 0039 Decision 13).

Welle-4a-Stub: dict-basiertes ``{run_id: TickLoop}``-Mapping mit
zwei Public-Methoden (``register`` + ``tick_loop_for``). Single-
Run-Demo-Setup im FastAPI-Lifespan registriert genau einen
Demo-TickLoop; produktive Multi-Run-Implementation in Welle 5
(Scenario-Loader) ersetzt den Stub.

**Kein Driving-Port-Slot:** Hexagonal-Architektur-Hinweis (ADR
0037 Decision API-2): UI/API-Adapter holen den `TickLoop` direkt
ueber Adapter-State, kein neuer Port-Vertrag noetig. Der
Adapter-interne Lookup ist Implementation-Detail des HTTP-
Drivings, kein Domain-Konzept.
"""

from __future__ import annotations

from typing import cast

from fastapi import Request

from grid_gym.adapters.driving.http_api._tick_loop_healthcheck import (
    TickLoopHealthcheckAdapter,
)
from grid_gym.hexagon.ports.driving.run_execution import RunExecutionPort


class TickLoopRegistry:
    """Adapter-internes ``{run_id: TickLoop}``-Mapping (M5 Welle 4a).

    Welle-4a-Stub: Single-Run-Demo-Setup. Produktive Multi-Run-
    Variante in Welle 5 wird vom Scenario-Loader gefuellt, sobald
    ein neuer Run via ``POST /runs`` mit Scenario-Body angelegt
    wird; bis dahin bleibt die Surface minimal.

    Welle-4b-c-Extension (`GG-RT-001` Backpressure-Healthcheck):
    Zusaetzlich zum TickLoop-Mapping haelt die Registry pro
    `run_id` einen optionalen `TickLoopHealthcheckAdapter`. Welle-
    4b-c-D-1 verankert die Adapter-Side-Mess-Substanz; die Registry
    ist der einzige Lookup-Punkt fuer den `GET /runs/{id}/
    healthcheck`-Endpoint.
    """

    def __init__(self) -> None:
        self._tick_loops: dict[str, RunExecutionPort] = {}
        self._healthcheck_adapters: dict[str, TickLoopHealthcheckAdapter] = {}

    def register(self, tick_loop: RunExecutionPort) -> None:
        """Registriert einen `TickLoop` unter seiner `run_id`.

        Ueberschreibt eine vorhandene Registrierung mit demselben
        `run_id` (Welle-4a-Stub-Behavior; produktive Welle-5-
        Variante koennte hier `RunAlreadyRegisteredError` werfen,
        wenn der `run_id` doppelt belegt wird).
        """
        self._tick_loops[tick_loop.run_id] = tick_loop

    def tick_loop_for(self, run_id: str) -> RunExecutionPort | None:
        """Liefert den `TickLoop` zu `run_id` oder ``None``.

        Aufrufer (HTTP-Endpoints) muessen den `None`-Fall
        behandeln — z. B. mit 503 Service Unavailable, wenn der
        Run zwar persistiert ist, aber kein aktiver Tick-Driver
        laeuft (Welle-4a-Demo-Stub deckt nur den einen
        ``demo-run-0001`` ab).
        """
        return self._tick_loops.get(run_id)

    def register_healthcheck_adapter(
        self,
        run_id: str,
        adapter: TickLoopHealthcheckAdapter,
    ) -> None:
        """Registriert einen `TickLoopHealthcheckAdapter` unter
        `run_id` (Welle-4b-c).

        Pattern analog `register(tick_loop)`. Aufrufer ist
        typischerweise das Demo-Lifespan-Setup nach
        `TickLoopRegistry.register(tick_loop)` und Adapter-
        Konstruktion.
        """
        self._healthcheck_adapters[run_id] = adapter

    def healthcheck_adapter_for(
        self,
        run_id: str,
    ) -> TickLoopHealthcheckAdapter | None:
        """Liefert den `TickLoopHealthcheckAdapter` zu `run_id`
        oder ``None`` (Welle-4b-c).

        Aufrufer (`GET /runs/{run_id}/healthcheck`-Endpoint)
        antwortet mit 503 Service Unavailable, wenn der Run
        zwar existiert (Repository), aber kein Healthcheck-
        Adapter registriert ist — kein aktiver Tick-Driver.
        """
        return self._healthcheck_adapters.get(run_id)

    def any_healthcheck_adapter(self) -> TickLoopHealthcheckAdapter | None:
        """Liefert einen beliebigen registrierten Healthcheck-Adapter
        oder ``None`` (M6 Welle 6, `/ready` simulation-Probe).

        Der Demo-Setup ist Single-Run; der erste Eintrag
        repraesentiert den `simulation`-Service fuer den nicht-run-
        bezogenen `/ready`-Endpoint (Welle-6-D-2 Sub-Form A). Gibt
        ``None`` zurueck, wenn kein Tick-Driver laeuft (Compose-
        `sleep infinity`-Stub oder Demo-Stack ohne Scenario) — der
        `/ready`-Adapter meldet `simulation` dann `degraded`
        (Sub-Form B).
        """
        for adapter in self._healthcheck_adapters.values():
            return adapter
        return None


class _TickLoopRegistryNotConfiguredError(RuntimeError):
    """Konfigurations-Fehler: HTTP-API ohne `TickLoopRegistry` gestartet.

    Erbt von ``RuntimeError``, damit FastAPI das ohne Mapper-Konfig
    auf 500 Internal Server Error mappt.
    """

    def __init__(self) -> None:
        super().__init__(
            "TickLoopRegistry is not configured. Call "
            "grid_gym.adapters.driving.http_api.app.configure_tick_loop_registry "
            "before serving requests."
        )


def get_tick_loop_registry(request: Request) -> TickLoopRegistry:
    """Dependency-Provider fuer die `TickLoopRegistry` (M5 Welle 4a).

    Wirft `_TickLoopRegistryNotConfiguredError`, wenn die App nicht
    konfiguriert ist — analog `get_run_repository`. Welle-4a-
    Endpoints (`POST /control` + `GET /status`) brauchen die
    Registry, damit Pause/Resume/Stop und Live-Tick-Counter
    funktionieren.
    """
    registry = getattr(request.app.state, "tick_loop_registry", None)
    if registry is None:
        raise _TickLoopRegistryNotConfiguredError
    return cast(TickLoopRegistry, registry)
