"""Statisches Run-Execution-Profil des In-Memory-Composition-Root
(Slice 038, ADR 0073 §2.3-§2.5).

Alle heutigen Composition-Pfade (ASGI-Entrypoint, Demo-Setups)
verdrahten dieselben Adapter-Packages: den HTTP-Driving-Adapter
(`http_api`) und die In-Memory-Persistenz-Familie
(`persistence_inmemory`: RunRepository, TelemetrySink,
ReplaySnapshot, ScenarioStore). `max_age_ms` bleibt in allen
produktiven Pfaden `None` (ADR 0052 §2.4: Demo-Wiring ohne
`STALE`-Stage) — die ConfigView v1 hasht genau diesen Zustand.

Ein kuenftiger Postgres-Composition-Pfad deklariert sein eigenes
Profil (`persistence_postgres` statt/neben `persistence_inmemory`)
und unterscheidet sich damit sichtbar im Preflight.
"""

from __future__ import annotations

import platform

from grid_gym.hexagon.core.domain.run import (
    RunExecutionProfile,
    canonical_enabled_adapters,
    canonical_platform_arch,
)
from grid_gym.hexagon.core.serialization.config_view import config_hash_for


def default_run_execution_profile() -> RunExecutionProfile:
    """Profil des In-Memory-Composition-Root (ADR 0073 §2.3).

    `platform_arch` liest `platform.machine()` des laufenden
    Prozesses (Composition darf Umgebung lesen; der Core nicht,
    ADR 0073 §2.5) und normalisiert per
    `canonical_platform_arch`.
    """
    return RunExecutionProfile(
        platform_arch=canonical_platform_arch(platform.machine()),
        enabled_adapters=canonical_enabled_adapters(("http_api", "persistence_inmemory")),
        config_hash=config_hash_for(max_age_ms=None),
    )
