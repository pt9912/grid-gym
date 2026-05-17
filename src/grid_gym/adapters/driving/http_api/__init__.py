"""HTTP-API Driving-Adapter (`GG-API-001..003`, M1 Welle 6a).

Re-Exportiert die FastAPI-`app`-Instanz fuer:
- `make runtime` (uvicorn-Start: `grid_gym.adapters.driving.http_api:app`).
- `make openapi-validate` (Dockerfile-Stage importiert `app.openapi()`).

Modul-Struktur:
- `app.py` baut die FastAPI-App, die Endpoints und die Pydantic-
  Schemas.
"""

from __future__ import annotations

from grid_gym.adapters.driving.http_api.app import app

__all__ = ["app"]
