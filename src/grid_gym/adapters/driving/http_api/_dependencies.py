"""FastAPI-Dependencies fuer das HTTP-Driving-Interface
(M1 Welle 6a/6b + M5 Welle 1).

Gemeinsames Modul fuer `app.py` + `_runs_router.py` +
`_runs_action_router.py` — vermeidet Circular-Imports
zwischen App und Sub-Routern.

Aktueller Inhalt:

- `get_run_repository` — FastAPI-Dependency, die die
  injizierte `RunRepositoryPort`-Instanz aus
  `request.app.state.run_repository` liefert.
- `_RunRepositoryNotConfiguredError` — Konfigurations-
  Fehler, wenn die App ohne `RunRepositoryPort` startet.
"""

from __future__ import annotations

from typing import cast

from fastapi import Request

from grid_gym.hexagon.ports.driven.run_repository import RunRepositoryPort


class _RunRepositoryNotConfiguredError(RuntimeError):
    """Konfigurations-Fehler: HTTP-API ohne `RunRepositoryPort` gestartet.

    Erbt von `RuntimeError`, damit FastAPI das ohne Mapper-Konfig auf
    `500 Internal Server Error` mappt. Message in `__init__` (Slice 027
    Paket B TRY003-Drop).
    """

    def __init__(self) -> None:
        super().__init__(
            "RunRepositoryPort is not configured. Call "
            "grid_gym.adapters.driving.http_api.app.configure_run_repository "
            "before serving requests."
        )


def get_run_repository(request: Request) -> RunRepositoryPort:
    """Dependency-Provider fuer `RunRepositoryPort`.

    Wirft `_RunRepositoryNotConfiguredError`, wenn die App nicht
    konfiguriert ist — Endpoints muessen vor dem ersten Aufruf
    `configure_run_repository` durchlaufen haben. Verhindert,
    dass ein nicht konfigurierter Welle-6-Stand stillschweigend
    nichts persistiert.
    """
    repository = getattr(request.app.state, "run_repository", None)
    if repository is None:
        raise _RunRepositoryNotConfiguredError
    return cast(RunRepositoryPort, repository)
