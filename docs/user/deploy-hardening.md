# Deploy-Hardening (`GG-DEPLOY-001..011`)

**Quelle:** M6-Welle-6 (Deploy-Hardening + IEC-Smoke-Pfad-B;
[`../plan/planning/in-progress/M6-welle-6.md`](../plan/planning/done-archive/M6-welle-6.md)).
**Stand:** 2026-06-08.

Dieses Dokument auditiert die produktive Substanz fuer die elf
`GG-DEPLOY-*`-IDs aus dem Lastenheft (§23). Pro ID werden
Substanz-Pfad, Test-Pfad und Lieferstatus dokumentiert. Pattern
analog [`safe-005-006-fallback-determinism.md`](safe-005-006-fallback-determinism.md)
(Welle 5c).

Welle 6 liefert die letzten beiden offenen MUSS/SOLLTE-IDs des
lokalen Deployment-Scopes: `GG-DEPLOY-006` (Three-State-
Healthcheck via NEU `GET /ready`) und `GG-DEPLOY-004`
(DevContainer-Konfiguration). Die verteilte-Deployment-Familie
`GG-DEPLOY-007..010` (Kubernetes / Rolling-Update / Zero-Downtime
/ Rollback) bleibt bewusst Post-MVP (M7+) und ist ueber
[Trigger 037](../plan/planning/open/037-deploy-007-010-multi-node-deployment.md)
verankert.

---

## Übersicht

| ID | Lastenheft-Anforderung | Substanz-Pfad | Test-Pfad | Status |
| -- | ---------------------- | ------------- | --------- | ------ |
| **[`GG-DEPLOY-001`](../../spec/lastenheft.md#gg-deploy-001)** | MUSS Docker Compose (API + UI + Simulationsdienst + Persistenz lokal). | `deploy/compose.yml` (postgres + api + ui-co-located + simulation-Stub); Doku [`demo-compose-hardening.md`](demo-compose-hardening.md). | `tests/integration/test_m5_welle_5_demo_smoke.py` + Compose-Smoke `tests/integration/test_m6_welle_5c_safe_005_006_compose_smoke.py`. | ✓ **Produktiv** (M1+0b) |
| **[`GG-DEPLOY-002`](../../spec/lastenheft.md#gg-deploy-002)** | MUSS offline lauffaehig nach lokaler Bereitstellung. | `Dockerfile` (`UV_PYTHON_DOWNLOADS=never`, `uv sync --frozen` lockfile-first, kein curl\|sh in der Build-Kette); `deploy/compose.yml` ohne Runtime-Pull. | `make runtime`-Compose-Smoke (offline-Boot + `/health`-Poll). | ✓ **Produktiv** (M1+0b) |
| **[`GG-DEPLOY-003`](../../spec/lastenheft.md#gg-deploy-003)** | MUSS Linux-x86_64 deploybar + Healthcheck-Nachweis. | `Dockerfile` runtime-Stage (`python:3.14-slim`, non-root `grid-gym:1001`, `EXPOSE 8080`, `HEALTHCHECK` curl `/health`). | `make runtime`-Compose-Smoke (Linux-Referenz; `/health` 200). | ✓ **Produktiv** (M1+0b) |
| **[`GG-DEPLOY-004`](../../spec/lastenheft.md#gg-deploy-004)** | SOLLTE DevContainer mit Build-/Test-/Abnahme-Befehlen. | **NEU** `.devcontainer/devcontainer.json` (`build.target: "base"` gegen `../Dockerfile`; `postCreateCommand: uv sync --all-groups`; drei `tasks` Build/Test/Abnahme = `make build`/`make ci`/`make fullbuild`). | `tests/integration/test_m6_welle_6_deploy_smoke.py::test_deploy_004_devcontainer_config_present` + `::test_deploy_004_devcontainer_build_section_pins_base_stage`. | ✓ **Produktiv** (Welle 6) |
| **[`GG-DEPLOY-005`](../../spec/lastenheft.md#gg-deploy-005)** | MUSS `docker compose up`-Demo, Systemstatus `healthy`. | `deploy/compose.yml` + Lifespan-Demo-Stack (`GRID_GYM_DEMO_SCENARIO_PATH`); `GET /ready` aggregiert `healthy`, wenn alle vier Komponenten gruen sind. | `tests/integration/test_m5_welle_5_demo_smoke.py` + `::test_deploy_006_ready_endpoint_three_state_canonical`. | ✓ **Produktiv** (M1+5) |
| **[`GG-DEPLOY-006`](../../spec/lastenheft.md#gg-deploy-006)** | MUSS Healthcheck `healthy`/`degraded`/`unhealthy` mit kurzer Ursache fuer API/UI/DB/Simulation. | **NEU** `GET /ready` ([ADR 0037](../plan/adr/0037-http-api-surface-pattern.md)-additiver Endpoint): `src/grid_gym/adapters/driving/http_api/_health_adapter.py::ReadinessProbeAdapter` (vier Probes `api`/`ui`/`db`/`simulation`, parallel via `asyncio.gather`, Three-State-Aggregation) + `app.py::get_ready` (HTTP 200 healthy/degraded, 503 unhealthy) + `_schemas.py::ReadyResponse`/`ComponentStatus` + **NEU** `RunRepositoryPort.ping()` (`SELECT 1` Postgres / `True` In-Memory). `GET /health` bleibt Liveness-only. | `tests/integration/test_m6_welle_6_deploy_smoke.py` (`::test_deploy_006_ready_endpoint_three_state_canonical` + `_unhealthy_when_db_down` + `_simulation_stub_reflects_degraded` + `_tickloop_status_mapping`) + Unit `tests/unit/adapters/driving/http_api/test_health_adapter.py`. | ✓ **Produktiv** (Welle 6) |
| **[`GG-DEPLOY-007`](../../spec/lastenheft.md#gg-deploy-007)** | SOLLTE Kubernetes-faehig (Manifeste / Helm / Kustomize). | ✗ Post-MVP — kein `deploy/k8s/`-Artefakt im Repo (bewusste M7+-Grenze). | — | ⏸ **M7+** → [Trigger 037](../plan/planning/open/037-deploy-007-010-multi-node-deployment.md) |
| **[`GG-DEPLOY-008`](../../spec/lastenheft.md#gg-deploy-008)** | SOLLTE Rolling Updates fuer verteiltes Deployment. | ✗ Post-MVP — verteiltes Deployment ist nicht im MVP-Scope. | — | ⏸ **M7+** → [Trigger 037](../plan/planning/open/037-deploy-007-010-multi-node-deployment.md) |
| **[`GG-DEPLOY-009`](../../spec/lastenheft.md#gg-deploy-009)** | KANN Zero-Downtime fuer nicht laufkritische Dienste. | ✗ Post-MVP — KANN-Item; verteiltes Deployment nicht im MVP-Scope. | — | ⏸ **M7+** → [Trigger 037](../plan/planning/open/037-deploy-007-010-multi-node-deployment.md) |
| **[`GG-DEPLOY-010`](../../spec/lastenheft.md#gg-deploy-010)** | SOLLTE Rollback fuer verteilte Deployments inkl. DB-Schema. | ✗ Post-MVP — verteiltes Deployment nicht im MVP-Scope (Alembic-Migrations-Rollback ist lokal vorhanden, aber kein verteilter Deployment-Rollback). | — | ⏸ **M7+** → [Trigger 037](../plan/planning/open/037-deploy-007-010-multi-node-deployment.md) |
| **[`GG-DEPLOY-011`](../../spec/lastenheft.md#gg-deploy-011)** | MUSS Simulations-/Abnahmelaeufe ohne externe Netzverbindung. | `Makefile` `runtime`-Compose-Smoke (offline-Boot); `deploy/compose.yml` auf lokalem Host-/Container-Netz; Replay/Fault/Persistenz laufen ohne externe Konnektivitaet (Welle-5c-IP/Netz-Beschraenkung). | `make runtime`-Compose-Smoke + Compose-Smoke `tests/integration/test_m6_welle_5c_safe_005_006_compose_smoke.py`. | ✓ **Produktiv** (M1+0b) |

**Legende**:

- ✓ **Produktiv**: Akzeptanz vollstaendig erfuellt + Smoke-/Unit-
  Test pinnt das in CI.
- ⏸ **M7+**: bewusste Post-MVP-Grenze; Trigger verankert den
  Folge-Pfad. Kein Substanz-Anspruch im MVP.

---

## `GET /ready` — Three-State-Healthcheck (`GG-DEPLOY-006`)

Liveness (`GET /health`) und Readiness (`GET /ready`) sind
getrennt (Kubernetes-/Cloud-Run-/Nomad-Pattern; Welle-6-D-2):

- **`GET /health`** bleibt Liveness-only — antwortet `{"status":
  "ok"}`, solange der Prozess laeuft. Dockerfile-`HEALTHCHECK` und
  Compose-`depends_on.condition: service_healthy` bleiben darauf.
  Ein Container mit temporaer hakendem Postgres ist **nicht**
  „liveness-tot" (ein Restart wuerde das Symptom verschlimmern).
- **`GET /ready`** ist Readiness mit Backend-Probes ueber die vier
  Lastenheft-Pflicht-Komponenten:

| Komponente | Probe | `healthy` | `degraded` | `unhealthy` |
| ---------- | ----- | --------- | ---------- | ----------- |
| `api` | In-Process-Liveness (der Endpoint laeuft im selben Prozess). | immer, wenn der Endpoint antwortet. | — | — |
| `ui` | `ui._templates.ui_surface_loads()` laedt das `base.html`-Layout. | Template laedt. | — | Template-Load wirft (`TemplateNotFound` o. ae.). |
| `db` | `RunRepositoryPort.ping()` (`SELECT 1` Postgres / `True` In-Memory). | ping `True`. | — | ping `False` oder Backend-Exception/Timeout. |
| `simulation` | TickLoop-Backpressure-Mapping (`TickLoopHealthcheckAdapter`). | `backpressure_status == "ok"`. | `"delayed"` (mit `missed_ticks_count`) **oder** kein aktiver TickLoop (Compose-`sleep infinity`-Stub). | — (`delayed`/`missed` sind im Adapter gekoppelt; kein `unhealthy`-Pfad ueber den TickLoop, Welle-6-D-2). |

**Aggregations-Regel** (Welle-6-D-2): jede Komponente `unhealthy`
→ Top-Level `unhealthy`; sonst eine `degraded` → `degraded`;
sonst `healthy`. **HTTP-Status**: `200` bei `healthy`/`degraded`,
`503` bei `unhealthy` (Kubernetes-Readiness-Konvention).

Die I/O-Probes (`ui`, `db`) laufen parallel unter Per-Probe-
Timeout (1 s; `asyncio.wait_for` + `asyncio.gather(return_
exceptions=True)`); eine Backend-Exception oder ein Timeout wird
auf `unhealthy` gemappt.

**Nicht-Pflicht-Komponente**: der `otel-collector` (Observability-
Sibling, Welle-3-C2) ist **nicht** Teil der Lastenheft-Vier-
Komponenten-Liste (`GG-OTEL-001..004` sind optional) und wird im
`/ready`-Breakdown nicht gefuehrt.

Architektur-Anker: `GG-AR-PORT-DRV-007` ist als Driving-Adapter-
Surface realisiert (kein Hexagon-Core-Driving-Port), weil die
Probe-Orchestrierung Driven-Side-Externals beruehrt (Postgres-
`ping()`, UI-Template-Load, TickLoop-Adapter) — Welle-6-D-6.

---

## DevContainer (`GG-DEPLOY-004`)

`.devcontainer/devcontainer.json` baut die `base`-Dockerfile-Stage
(`build.target: "base"`, kein floating `:latest`-Image-Tag — der
VS-Code-Server baut die Stage beim Reopen selbst) und richtet die
Dev-Umgebung per `postCreateCommand: "uv sync --all-groups"` ein.
Drei dokumentierte VS-Code-Tasks erfuellen die Lastenheft-
Akzeptanz „Build-, Test- und Abnahmebefehle":

| Task | Kommando | Zweck |
| ---- | -------- | ----- |
| **Build** | `make build` | Runtime-Image (`GG-DEPLOY-001`). |
| **Test** | `make ci` | Pflicht-Gates + Integration + OpenAPI + Image-Audit. |
| **Abnahme** | `make fullbuild` | Voller Abnahme-Lauf (M-Closure-Gate). |

---

## IEC-61850-Smoke-Pfad-B (Trigger 009 / ADR 0046)

Querbezug (kein `GG-DEPLOY-*`, aber Welle-6-Build-Substanz): die
NEU Dockerfile-Stage `iec61850-test` (Python 3.12) reaktiviert den
IEC-61850-In-Process-Smoke real-library. Default-`make
test-integration` (Python 3.14) skippt den Smoke versions-bedingt
(`pytest.mark.skipif(sys.version_info >= (3, 13))`); `make
test-iec61850` faehrt die 3.12-Stage. `make ci` koordiniert beide.
Pattern verankert in [ADR 0046](../plan/adr/0046-multi-python-test-stage-pattern.md);
Trigger-Aufloesung siehe
[`../plan/planning/done/009-iec61850-smoke-reactivation.md`](../plan/planning/done-archive/009-iec61850-smoke-reactivation.md).

---

## Bezüge

- [M6-Welle-6 Slice-Doc](../plan/planning/done-archive/M6-welle-6.md)
  — Decision-Liste (D-1..D-6) + Liefer-Reihenfolge.
- [ADR 0046 — Multi-Python-Test-Stage-Pattern](../plan/adr/0046-multi-python-test-stage-pattern.md)
  — `iec61850-test`-Stage.
- [ADR 0037 — HTTP-API-Surface-Pattern](../plan/adr/0037-http-api-surface-pattern.md)
  — `/ready` ist ein additiver Endpoint unter diesem Pattern.
- [demo-compose-hardening.md](demo-compose-hardening.md) —
  Compose-Stack-Haertung (`GG-DEPLOY-001/005`).
- Lastenheft §23 (`GG-DEPLOY-001..011`, Z. 1833-1921);
  Architektur §4.2 (`GG-AR-PORT-DRV-007`, Z. 237) + §15
  (Healthcheck, Z. 822).
