# 009 — `tests/integration/compose.yml`

**Status:** Open — Trigger-Watch
**Datum:** 2026-05-15
**Quelle:** [`Makefile`](../../../../Makefile) Target `test-integration`

---

## Trigger

Das Makefile-Target `test-integration` setzt eine
`tests/integration/compose.yml` voraus, faellt heute aber graceful
zurueck:

```text
[test-integration] tests/integration/compose.yml fehlt — wird in
Welle 2 angelegt
```

`GG-TESTTYPE-002`, `GG-TEST-003`, `GG-TEST-011` (Integrationstests
fuer API, Persistenz und Telemetriepfad) verlangen einen
containerisierten Lauf.

## Erwartete Lieferung

- `tests/integration/compose.yml` mit:
  - `postgres`-Service (Pflicht, `GG-PERSIST-005`),
  - `test-runner`-Service mit Docker-Socket-Mount (fuer
    testcontainers-Python),
  - optional: `timescaledb`/`influxdb` fuer Adapter-Tests,
  - optional: `otel-collector` fuer Telemetrie-Tests.
- Migrations-Setup: `test-runner` ruft `alembic upgrade head` vor
  den Tests auf.
- Fixture-Konvention: testcontainers stoppt eigene Container nach
  jedem Test; das Compose-File bringt nur die ortsfesten Dienste.

## Aktivierungs-Kriterium

Mit dem ersten Persistenz-Adapter-Slice (PostgreSQL-Repository,
`GG-PERSIST-001/005/008`).

## Wandert nach

- `next/`, sobald Persistenz-Slice skizziert ist,
- `in-progress/`, wenn aktiver Slice geplant ist.
