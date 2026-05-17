# 010 — `deploy/compose.yml` — Closure-Notiz

**Status:** Done — geschlossen 2026-05-17 mit M1 Welle 6c + 6d
(Commits `f7b699d` + `b5243fe`).
**Datum:** 2026-05-15 (geoeffnet); 2026-05-17 Closure mit
Welle-6c/d-Lieferung.
**Quelle:** `Makefile`-Target `runtime` (Healthcheck-Polling
gegen `deploy/compose.yml`).
**Verlinkt:** [`deploy/compose.yml`](../../../../deploy/compose.yml),
[`Dockerfile`](../../../../Dockerfile) `runtime`-Stage,
M1-Slice-Plan
[`M1-tick-loop-spine.md`](../done/M1-tick-loop-spine.md)
§3 Welle 6c/6d.

---

## Trigger (historisch)

`make runtime` startete den `runtime`-Image-Build und sollte das
Image gegen ein `deploy/compose.yml`-Stack pollen (`/health`-
Polling, `GG-DEPLOY-001`/`003`). Bis Welle 6 lag das compose-File
nicht vor, daher fiel `make runtime` graceful aus.

## Lieferung

`deploy/compose.yml` mit drei Services:

- **`postgres`**: `postgres:16-alpine` mit
  `pg_isready`-healthcheck. Datenbank `grid_gym`, User
  `grid_gym`, Password `grid_gym` (Test-/Demo-Setup; produktive
  Geheimnisse kommen mit `GG-DEPLOY-006` und einer
  Secrets-ADR).
- **`api`**: `grid-gym-runtime:latest`-Image,
  `python -m uvicorn` auf `:8080`, depends-on
  `postgres: service_healthy`. `GRID_GYM_DATABASE_URL`-Env
  zeigt auf den `postgres`-Service. Dockerfile-`ENTRYPOINT`
  per `entrypoint: []` neutralisiert.
- **`simulation`**: Welle-6c-Stub-Container mit
  `sleep infinity` als Platzhalter fuer den TickLoop-Runner
  (M2-Verantwortung). `healthcheck: test: ["NONE"]` deaktiviert
  den Dockerfile-curl-HEALTHCHECK, weil der Stub keinen
  Webserver hat.

`make runtime` ist nun gruen: baut das Runtime-Image, startet
den Stack, pollt `/health` bis `200 OK`, tears down. Welle 6d
hat zusaetzlich `apt-get upgrade -y` im Runtime-Stage und
`PYTHONPATH=/app/src` ergaenzt — `make image-audit`
(trivy --ignore-unfixed) und der Compose-Smoke laufen zusammen
mit dem `make fullbuild`-Aggregator gruen.

## Aktivierungs-Kriterium (erfuellt)

Mit M1 Welle 6c (FastAPI-Adapter + Postgres-Persistenz)
aktiviert; abgeschlossen mit Welle 6d (M1-Abschluss-Gate
`make fullbuild` mit `CRITICAL_COV_TARGETS`-Override).

## Wandert nach

`done/` (jetzt). M2 bringt produktive Geraete + TickLoop-Runner,
die den `simulation`-Service auf einen echten Entry umstellen.
M6 (Security/CI-Haertung, Roadmap §3) erweitert um Secrets-
Management und produktions-taugliche `GRID_GYM_*`-ENV.
Open-Trigger 015 (Production-Image-Hardening:
shebang-Rewrite / `uv sync --no-editable`) ist der unmittelbare
Welle-6d-Erbe.
