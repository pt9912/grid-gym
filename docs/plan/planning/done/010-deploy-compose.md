# 010 — `deploy/compose.yml`

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-15
**Quelle:** [`Makefile`](../../../../Makefile) Target `runtime`;
`GG-DEPLOY-001/005`, `GG-DEMO-001..008`

---

## Trigger

Das Makefile-Target `runtime` setzt eine `deploy/compose.yml`
voraus und bricht heute ab, wenn sie fehlt:

```text
[runtime] deploy/compose.yml fehlt — wird mit der Deploy-Slice
angelegt
```

`GG-DEPLOY-001` MUSS Docker Compose; `GG-DEPLOY-005` MUSS
`docker compose up` als Start-Kommando; `GG-DEMO-001` MUSS lokal
startbare Demo-Umgebung.

## Erwartete Lieferung

- `deploy/compose.yml` mit:
  - `api`-Service (FastAPI, Port 8080, `/health`-Healthcheck),
  - `simulation`-Service (optional separat, `GG-AR-OPEN-002`),
  - `ui`-Service (Web-UI, `GG-UI-001`),
  - `postgres`-Service (Pflicht, `GG-PERSIST-005`),
  - optionale `timescaledb`/`influxdb`/`otel-collector`-Services.
- Offline-Faehigkeit: kein Pull aus dem Internet zur Laufzeit
  (`GG-DEPLOY-002/011`).
- Healthcheck-Wartepunkt: `docker compose up -d --wait` gruen.

## Aktivierungs-Kriterium

Mit dem ersten Deploy-Slice (Compose + API-Slice + Persistenz-
Migrationspfad).

## Abhaengig von

- `tests/integration/compose.yml` (siehe 009) liefert das
  Postgres-Setup-Muster.
- `GG-AR-OPEN-002` (API/Simulation als ein oder zwei Prozesse)
  beeinflusst die Service-Topologie.

## Wandert nach

- `next/`, sobald Deploy-Slice skizziert ist,
- `in-progress/`, wenn aktiver Slice geplant ist.
