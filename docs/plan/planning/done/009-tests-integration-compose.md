# 009 — `tests/integration/compose.yml` — Closure-Notiz

**Status:** Done — geschlossen 2026-05-17 mit M1 Welle 6c
(Commit `f7b699d`).
**Datum:** 2026-05-15 (geoeffnet); 2026-05-17 Closure mit
Welle-6c-Lieferung.
**Quelle:** `Makefile`-Target `test-integration` (graceful
fallback bis Welle 6).
**Verlinkt:** [`tests/integration/compose.yml`](../../../../tests/integration/compose.yml),
[`tests/integration/test_postgres_run_repository.py`](../../../../tests/integration/test_postgres_run_repository.py),
M1-Slice-Plan
[`M1-tick-loop-spine.md`](../in-progress/M1-tick-loop-spine.md)
§3 Welle 6c.

---

## Trigger (historisch)

`make test-integration` setzte eine `tests/integration/
compose.yml` voraus, fiel aber graceful zurueck:

```text
[test-integration] tests/integration/compose.yml fehlt — wird in
Welle 2 angelegt
```

`GG-TESTTYPE-002`, `GG-TEST-003`, `GG-TEST-011`
(Integrationstests fuer API, Persistenz, Telemetriepfad)
verlangen einen containerisierten Lauf.

## Lieferung

- **`tests/integration/compose.yml`** mit einem
  `test-runner`-Service, der den `source`-Stage des Dockerfile
  baut und `pytest tests/integration/` ausfuehrt.
- **Docker-Socket-Mount** in den test-runner-Container —
  testcontainers spawnt ephemere Sibling-Container (kein
  docker-in-docker, kein eigener Postgres-Service hier).
- **`tests/integration/test_postgres_run_repository.py`** als
  erster Welle-1-Integration-Test:
  - module-scope `postgres:16-alpine` via
    `testcontainers[postgres]`,
  - `alembic upgrade head` rollt das `runs`-Schema ein,
  - 5 Tests: Save→Get-Roundtrip aller `RunMetadata`-Felder,
    `exists`-True/False-Pfade, `RunNotFoundError`- und
    `RunAlreadyExistsError`-Negativ.
- **DSN-Konvertierung**: testcontainers liefert
  `postgresql+psycopg2://`; wir mappen auf
  `postgresql+psycopg://` (SQLAlchemy 2.x psycopg3-Dialect fuer
  alembic) und `postgresql://` (direktes `psycopg.connect`).

`make test-integration` ist nun gruen (5 passed).

## Aktivierungs-Kriterium (erfuellt)

Mit M1 Welle 6c (`PostgresRunRepository`-Slice) aktiviert; in
derselben Welle abgearbeitet.

## Wandert nach

`done/` (jetzt). M2 erweitert die Integration-Test-Suite um
Geraete-Adapter-Tests; das Compose-Setup bleibt unveraendert
(testcontainers spawnt zusaetzliche Container je Test). Eine
TimescaleDB-Service-Erweiterung kann mit `GG-PERSIST-005`-
Optionen kommen.
