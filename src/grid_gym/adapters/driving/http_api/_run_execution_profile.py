"""Run-Execution-Profil-Registrierung fuer `POST /runs`
(Slice 038, ADR 0073 §2.3).

Der Composition Root deklariert sein statisches Adapter-Profil
(`RunExecutionProfile`: `platform_arch`, `enabled_adapters`,
`config_hash`) und registriert es hier per Hook-Inversion
(ADR 0054-Muster, Praezedenz `_register_run_driver_builder` in
`_run_start_router.py`) — dieser Adapter importiert die
`composition`-Schicht **nicht** (`AC-ADAPTER-PURE`).

Default ist das **leere Profil** (Bare-Adapter-Entrypoint ohne
Composition): dessen Laeufe tragen leere Vollfelder und werden im
Replay-Preflight fail-closed rejected (`missing`-Reject, ADR 0073
§2.6) — bewusst **kein** Raise hier, die Durchsetzung sitzt im
Preflight, nicht an der Lauf-Anlage.
"""

from __future__ import annotations

from grid_gym.hexagon.core.domain.run import RunExecutionProfile

_run_execution_profile: RunExecutionProfile = RunExecutionProfile()


def _register_run_execution_profile(profile: RunExecutionProfile) -> None:
    """Injiziert das statische Composition-Root-Profil (ADR 0073
    §2.3). `POST /runs` erbt die Vollfelder jeder neuen
    `RunMetadata` aus diesem Profil."""
    global _run_execution_profile
    _run_execution_profile = profile


def get_run_execution_profile() -> RunExecutionProfile:
    """Liefert das registrierte Profil (leeres Profil, solange kein
    Composition Root registriert hat)."""
    return _run_execution_profile
