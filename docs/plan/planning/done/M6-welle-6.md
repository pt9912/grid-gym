# Welle 6 — M6 Deploy-Hardening + IEC-Smoke-Pfad-B (`GG-DEPLOY-001..011` + Trigger 009)

**Status:** Done 2026-06-08 — C0 `fab6a8c` (Slice-Doc-Anlage) +
C1 `1d478e3` (NEU ADR 0046 Multi-Python-Test-Stage-Pattern,
`Provisional`) + C2 `f07e996` (feat/deploy: `/ready` + DevContainer +
IEC-Pfad-B + Audit-Doku + Smokes; inkl. Code-Review-Folge inline) +
C3 `79563c0` (Status/DoD-Sync) + C4a `79ac725` (Self-Close-Move
rename-only) + C4b `d8dd8d2` (Cross-Doc-Refs-Sync).
`make fullbuild`/`gates`/`test-iec61850`/`docs-check` cache-frei
gruen. ADR 0046 bleibt `Provisional` bis M6-Welle-7-Closure.
Self-Close-Folge C4a/C4b (Move nach `done/`) dient als
M6-Welle-7-Pre-C0a/Pre-C0b.

**C2-Realization-Notes (Abweichungen vom Slice-Plan, alle
verifiziert via `make fullbuild` cache-frei gruen):**

- `/ready`-Endpoint liegt in NEU `_ready_router.py` (nicht in
  `app.py`) — `app.py` haette sonst 6 public top-level functions
  (`AC-NO-GOD-UTILS` max 5). Pattern analog `_healthcheck_router.py`.
- ADR 0046 §2.2 korrigiert: Compat-Install via `python -m pip
  install --ignore-requires-python` statt `uv pip install` —
  `uv pip install` kennt das Flag nicht. Gilt auch fuer die
  Editable-Install von grid_gym selbst (eigener `requires-python`-
  Floor).
- Compat-Dep-Set erweitert um `psycopg`/`alembic`/
  `testcontainers[postgres]`, weil `tests/integration/conftest.py`
  diese zur Collection-Zeit importiert; `pyiec61850-ng==1.6.1.2`
  exakt gepinnt (1.6.1.3 bricht den Model-Loader).
- IEC-Smoke: zwei latente Slice-033-Bugs gefixt (durch den Skip
  seit Welle 5b verdeckt) — (a) `#`-SPDX-Header in `simpleIO.cfg`
  bricht den libiec61850-Parser → Test laedt aus kommentar-
  bereinigter Temp-Kopie (Fixture behaelt SPDX-Header); (b) String-
  Datatype-Assertions auf den dokumentierten `source`-Encoding-
  Vertrag (ADR 0035 §2.6) korrigiert.
- NEU 3 Unit-Tests (`test_health_adapter`/`test_ready_router`/
  `test_tick_loop_registry`), weil `coverage-gate` nur `tests/unit/`
  misst (die 7 Slice-Smokes sind Integration).
- **Code-Review-BLOCKER-Fix**: `configure_scenario_demo_run`
  registriert jetzt einen `TickLoopHealthcheckAdapter` am
  produktiven TickLoop — sonst meldet `/ready` die `simulation`-
  Komponente im Compose-Stack dauerhaft `degraded`-Stub und
  GG-DEPLOY-005 „Systemstatus healthy" waere nie erreichbar.
  Pin: NEU `test_m5_welle_5_demo_smoke.py::test_demo_ready_endpoint_
  reports_healthy`.
- `.devcontainer/` in den Dockerfile-`source`-COPY aufgenommen
  (docs-check + Deploy-Smoke brauchen die Datei im Build-Kontext);
  7 Doc-Link-Fixes nach dem Trigger-009-`open/ → done/`-Move.

**Pre-C0 abgeschlossen (M6-Welle-5c-Closure-Folge):**

- C4a `4db4715` — `git mv M6-welle-5c.md → done/` (Self-
  Close-Move, rename-only; dient gleichzeitig als Welle-6-
  Pre-C0a).
- C4b `56f26b9` — Cross-Doc-Refs-Sync nach Move +
  `done/README.md`-Eintrag (Welle-6-Pre-C0b). **Welle-5-
  Subdivision (5a + 5b + 5c) komplett** mit allen acht
  `GG-SAFE-*`-IDs auditiert (sechs ✓ produktiv, zwei ⚠
  partial mit `open/`-Triggern 034/035/036).

**Spec-Reife:** Inhaltlich final fuer Welle 6. Welle-6-
Decision-Liste (§3) schliesst Welle-6-D-1..D-6: Sub-
Slicing-Beschluss, `GG-DEPLOY-006`-Form, `GG-DEPLOY-004`-
Form, Trigger-009-Pfad, Audit-Form, ADR-Bedarf.

---

## 1. Context

Welle 6 ist die **Substanz-Welle fuer Deploy-Hardening +
IEC-Smoke-Pfad-B** und schliesst die letzten drei
substanziellen Luecken vor M6-Welle-7-Closure:

- **`GG-DEPLOY-006`**: Die Plattform MUSS Healthchecks
  fuer lokale Dienste bereitstellen. **Akzeptanz**
  (Lastenheft Z. 1876-1879): „API, UI, Datenbank und
  Simulationsdienst melden `healthy`, `degraded` oder
  `unhealthy` mit kurzer Ursache." **Architektur-Vorgabe**
  (`spec/architecture.md §4.2 Z. 237`):
  `GG-AR-PORT-DRV-007 HealthPort` ist als Driving-Port mit
  Three-State-Status (`healthy`/`degraded`/`unhealthy`)
  explizit registriert — Welle 6 implementiert diesen
  Driving-Port. **Substanz-Stand**: `GET /health` liefert
  heute ausschliesslich `{"status": "ok"}` (Liveness-Probe
  ohne Backend-Pruefung; `app.py:get_health`-Docstring
  vermerkt selbst: „Persistente Backend-Checks ... kommen
  mit Welle 6c als `/ready`-Endpoint dazu" — M3-Welle-6c
  hat das vertagt; Welle 6 loest es ein). `HealthPort`-
  Driving-Port-Surface existiert heute nicht.
- **`GG-DEPLOY-004`**: Die Plattform SOLLTE DevContainer
  unterstuetzen. **Akzeptanz** (Lastenheft Z. 1857-1861):
  „Wenn DevContainer-Unterstuetzung bereitgestellt wird,
  enthaelt das Repository eine dokumentierte DevContainer-
  Konfiguration mit Build-, Test- und Abnahmebefehlen."
  **Substanz-Stand**: kein `.devcontainer/`-Verzeichnis im
  Repo. SOLLTE ist konditional — wer es liefert, muss die
  drei Konvenienz-Befehle (Build, Test, Abnahme)
  dokumentieren.
- **`Trigger 009` IEC-Smoke-Reaktivierung** (M4-Erbschaft):
  `tests/integration/test_iec61850_in_process_smoke.py` ist
  seit M4-Welle-5b ueber `pytestmark = pytest.mark.skip(...)`
  deaktiviert (2c-Mock-only-Fallback per ADR 0035 §2.5).
  Pfad A (Library-Upgrade) ist **tot** (PyPI-Manifest
  `pyiec61850-ng==1.6.1.2` liefert auf Linux nur
  `py3-none-manylinux1_x86_64`-Wheel ohne cp-Tag — segfault
  auf Python 3.14, siehe
  [Trigger 009](../done/009-iec61850-smoke-reactivation.md)
  „Pfad A ist tot"). Welle 6 aktiviert **Pfad B** (Multi-
  Python-Test-Stage in Dockerfile mit Python 3.12 fuer den
  IEC-In-Process-Smoke; ADR-Pattern fuer Library-Compat-
  Test-Stages).

### 1.1 Existierende Substanz (Pre-C0-Audit, Code-verifiziert)

**`GG-DEPLOY-001..003` + `005` + `011`** (✓ produktiv per
Welle-1-Stand + Welle-5c-Hardening):

- `deploy/compose.yml` mit `postgres` + `api` +
  `otel-collector` + `simulation`-Stub; Welle-5c-`api`-
  `ports`-Klausel auf `127.0.0.1`-Default-Bind +
  `GRID_GYM_DEMO_HOST_BIND`-ENV-Override per
  `carveouts.md §2.7`-Auflage.
- `Dockerfile` runtime-Stage mit non-root-User,
  `HEALTHCHECK --interval=10s` gegen `:8080/health`,
  Linux-x86_64.
- `make demo` + `make runtime` Demo-/Smoke-Targets;
  beide rufen `docker compose up -d --wait`.
- Offline-Faehigkeit per `--no-pull`-Build-Pattern in
  Welle 0b/1.

**`GG-DEPLOY-006` Partial-Substanz** (⚠ partial — Liveness-
only `/health`; Three-State-Aggregation fehlt):

- `GET /health` in
  `src/grid_gym/adapters/driving/http_api/app.py` liefert
  `HealthResponse(status="ok")`-Konstante; kein Backend-
  Probe.
- Welle-4b-c-Substanz
  `src/grid_gym/adapters/driving/http_api/_tick_loop_healthcheck.py`
  liefert ein 6-Feld-Mapping mit `p50/p95/missed_ticks/
  backpressure_status` ueber `GET /runs/{run_id}/healthcheck`-
  Endpoint (pro Lauf). Welle 6 aggregiert das in einen
  globalen `/ready`-Endpoint inkl. Postgres- + OTel-
  Collector-Probe.
- Dockerfile-HEALTHCHECK (Container-Liveness) und Compose-
  `depends_on.condition: service_healthy` (Boot-Reihenfolge)
  bleiben unveraendert auf `/health` (Liveness-Semantik
  reicht fuer Restart-Logik); `/ready` ist Readiness-
  Semantik fuer Kubernetes-/Reverse-Proxy-Pattern.

**`GG-DEPLOY-007..010`** (⏸ M7+ per Lastenheft-
Traceability Z. 2308): Kubernetes-Manifeste / Rolling-
Updates / Zero-Downtime / Rollback sind explizit
M7+-Material und kein Welle-6-Scope.

**Trigger 009 IEC-Smoke-Pfad-B** (✗ Lücke, aktiviert in
Welle 6):

- `tests/integration/test_iec61850_in_process_smoke.py`
  Modul-Level-`pytestmark = pytest.mark.skip(reason="2c-
  Mock-only-Fallback aktiv (ADR 0035 §2.5; Welle-6b-C3-
  Defer): pyiec61850-ng 1.6.1.2 ...")` deaktiviert das
  In-Process-Smoke seit M4-Welle-5b.
- 18 Mock-Client-Unit-Tests in
  `tests/unit/adapters/driven/protocol_iec61850/test_iec61850_protocol_port.py`
  decken Lifecycle + Read-Pfad + Error-Translation gegen
  den `pyiec61850-ng`-Mock ab — der Real-Library-
  Roundtrip ist aktuell nicht in CI.
- Probe-Run-Befund (Trigger 009): pyiec61850-ng 1.6.1.2
  laeuft sauber auf Python 3.12; nur Python 3.14 segfaultet
  am SWIG-Layer.
- Welle 6 fuegt eine Dockerfile-Stage `iec61850-test` auf
  Python-3.12-Basis ein, registriert sie als separates
  Pytest-Target und hebt den Skip-Marker auf.

### 1.2 Welle-6-Lieferziel

**Substanz-Welle** (Pattern abweichend von Welle 5a/5b/5c —
diese waren Audit-/Hardening-Wellen; Welle 6 liefert
neue Hexagon-/Adapter-/Build-Substanz):

1. **NEU `HealthPort`-Driving-Adapter-Side + `GET /ready`-
   Endpoint** (Welle-6-C2): `GG-AR-PORT-DRV-007`
   (Architektur §4.2 Z. 237) realisiert als Driving-
   Adapter-Surface in `adapters/driving/http_api/_health_adapter.py`
   (Pattern analog Welle-4b-c-`_tick_loop_healthcheck.py`-
   Driving-Adapter — keine Hexagon-Core-Driving-Port-
   Definition, weil die Probe-Orchestrierung Driven-
   Side-Externals (Postgres-`ping()` + HTTP-Probe an
   OTel-Collector + TickLoop-Adapter-Mapping) beruehrt,
   die im Core eine Schichten-Verletzung waeren). FastAPI-
   Endpoint `GET /ready` wrapt den Adapter. Three-State-
   Status (`healthy`/`degraded`/`unhealthy`) plus
   Komponenten-Breakdown ueber die **vier Lastenheft-
   Pflicht-Komponenten** (`api`/`ui`/`db`/`simulation`) +
   Ursachen-String pro Komponente. Pro Lastenheft Z. 1876-
   1879. Welle-6-D-2 dokumentiert Probe-Details +
   Aggregations-Regel.

2. **NEU `.devcontainer/devcontainer.json`** (Welle-6-C2)
   mit drei dokumentierten Befehlen
   (Build/Test/Abnahme) — schliesst `GG-DEPLOY-004`-
   konditional („Wenn DevContainer-Unterstuetzung
   bereitgestellt wird ...").

3. **NEU Dockerfile-Stage `iec61850-test`** (Welle-6-C2)
   auf Python-3.12-Basis + Makefile-Target
   `test-iec61850` + Skip-Marker-Removal in
   `tests/integration/test_iec61850_in_process_smoke.py` —
   loest Trigger 009 IEC-Pfad-B.

4. **NEU ADR 0046 `Multi-Python-Test-Stage-Pattern`**
   (Welle-6-C1) als ADR-0011-Schaerfung zum Dockerfile-
   Build-Pattern (kein Supersedes) — verankert die
   Library-Compat-Test-Stage-Konvention im Repo, sodass
   zukuenftige Library-Inkompats (z. B. asyncua-Folge)
   denselben Pattern wiederverwenden koennen.

5. **NEU `docs/user/deploy-hardening.md`** (Welle-6-C2)
   Audit-Tabelle: alle 11 `GG-DEPLOY-*`-IDs auditiert mit
   Substanz-Pfad / Test-Pfad / Status; Pattern analog
   `safe-005-006-fallback-determinism.md`.

6. **NEU Integration-Smokes** (Welle-6-C2):
   - `test_deploy_006_ready_endpoint_three_state_canonical`:
     `/ready` mit allen Backends gruen → `healthy`; jeder
     der vier Komponenten (api/ui/db/simulation) liefert
     `ComponentStatus.state == "healthy"`; HTTP-Status 200.
   - `test_deploy_006_ready_endpoint_unhealthy_when_db_down`:
     simuliert DB-Ausfall (Mock `RunRepositoryPort.ping()`
     → `False`) → Komponente `db` ist `unhealthy` mit
     Ursache; Top-Level `status == "unhealthy"`; HTTP-
     Status 503.
   - `test_deploy_006_ready_endpoint_simulation_stub_reflects_degraded`:
     ohne aktivem TickLoop liefert die `simulation`-
     Komponente `degraded` mit Stub-Ursache (Welle-6-D-2
     Sub-Form B); kein `unhealthy`-Pseudo-Ausfall.
   - `test_deploy_006_ready_endpoint_tickloop_status_mapping`:
     `_tick_loop_healthcheck.backpressure_status == "ok"`
     → `simulation` `healthy`; `"delayed"` → `degraded`
     mit Ursache, die `missed_ticks_count`-Zaehlwert
     enthaelt. Kein `unhealthy`-Pfad ueber den TickLoop-
     Adapter (siehe Welle-6-D-2-Begruendung — `delayed` und
     `missed > 0` sind im Adapter gekoppelt).
   - `test_deploy_004_devcontainer_config_present`:
     `.devcontainer/devcontainer.json` enthaelt die drei
     Pflicht-Befehle (Build/Test/Abnahme; Quell-Datei-
     Inspektion).
   - `test_deploy_004_devcontainer_build_section_pins_base_stage`:
     `.devcontainer/devcontainer.json` enthaelt eine
     `build`-Section mit `dockerfile: "../Dockerfile"` +
     `target: "base"` (kein `image:`-Verweis auf einen
     floating `:latest`-Tag).
   - `test_trigger_009_iec61850_skipmark_is_versions_conditional`:
     `tests/integration/test_iec61850_in_process_smoke.py`
     traegt einen `pytest.mark.skipif(sys.version_info >=
     (3, 13), ...)`-Marker (kein blanker
     `pytest.mark.skip`-Marker; Quell-Datei-Inspektion).
     Default-Python 3.14 skip-t weiterhin; Python-3.12-Stage
     laeuft real-library — die `iec61850-test`-Stage-Ausfuehrung
     wird separat in `make test-iec61850` verifiziert.

### 1.3 Welle-6-Anti-Scope

- **Keine Kubernetes-Manifeste** (`GG-DEPLOY-007`) —
  M7+ per Lastenheft-Traceability Z. 2308; Architektur-
  Verankerung in [Trigger 037](../open/037-deploy-007-010-multi-node-deployment.md)
  (Multi-Node-Deployment-Familie; M6-Welle-6-Audit-Folge).
- **Kein Rolling-Update / Zero-Downtime / Rollback**
  (`GG-DEPLOY-008..010`) — M7+; gemeinsam mit
  `GG-DEPLOY-007` in [Trigger 037](../open/037-deploy-007-010-multi-node-deployment.md)
  verankert.
- **Kein produktiver Sim-Runner fuer den `simulation`-
  Compose-Service** — der Compose-Service-Stub bleibt
  `sleep infinity` (Welle 6c); Welle 6 liefert
  ausschliesslich die Health-Probe-Surface (mit ehrlichem
  Stub-Reflektieren als Sub-Form B; siehe Welle-6-D-2).
  Ein produktiver Sim-Runner-Service kommt mit M2-Welle-7-
  Pattern, nicht hier.
- **Kein NEU Driven-Port** fuer Health-Probes — Welle 6
  fuehrt `HealthPort` als NEU **Driving-Port** ein
  (`GG-AR-PORT-DRV-007`-Pflicht-Implementation; Architektur
  §4.2 Z. 237); auf der Driven-Seite werden ausschliesslich
  existierende Surfaces wiederverwendet (NEU `ping()`-
  Methode an `RunRepositoryPort` als ADR-0011-Schaerfung,
  kein NEU Driven-Port).
- **NEU Driving-Adapter-Modul `_health_adapter.py`** ist
  **im Scope** (Pflicht-Implementation der HealthPort-
  Surface); Aggregation lebt im Adapter, nicht im
  Hexagon-Core (`HealthPort` ist Driving-Port: vom Adapter
  IN den Kern, nicht umgekehrt).
- **Keine Aktivierung der Mock-Substanz-Reduzierung** —
  18 Mock-Client-Unit-Tests bleiben (ADR 0035 §2.5
  Mock-Pattern bleibt gueltig; Trigger 009 Pfad B ist
  Add-on, nicht Replacement).
- **Keine `pyiec61850-ng`-Version-Bump** auf 2.0.x (Pfad A)
  — Pfad A ist tot. Pfad B (Multi-Python-Stage) ist die
  einzig aktive Loesung.
- **Kein NEU ADR fuer `/ready`-Endpoint** — ADR 0037
  (HTTP-API-Surface-Pattern) deckt den Endpoint additiv ab;
  ADR-0011-Schaerfung waere overengineering fuer einen
  einzelnen Endpoint. ADR 0046 ist **ausschliesslich** fuer
  das Multi-Python-Test-Stage-Pattern.

---

## 2. Scope

Welle 6 liefert **vier Commit-Substanz-Items** ueber 4
Commits (C0..C3), plus Self-Close-Folge C4a/C4b.

1. **Slice-Doc-Anlage** (C0, dieser Commit) — dieses
   Dokument; `in-progress/README.md`-Bestand auf Welle 6;
   `M6-perf-security-cicd.md §3.1` Welle-6-Zeile
   `Pending → In Progress 2026-06-07`; `roadmap.md §4 M6`
   aktive Welle auf 6; `M6-perf-security-cicd.md §3.2
   Welle 6`-Vorbelegung aufgeloest in §3.1.
2. **ADR 0046** (C1) — NEU
   `docs/plan/adr/0046-multi-python-test-stage-pattern.md`
   `Provisional`; ADR-0011-Schaerfung zum Dockerfile-
   Build-Pattern fuer Library-Compat-Test-Stages.
3. **Code-/Build-Substanz** (C2):
   - NEU `GET /ready`-Endpoint in
     `adapters/driving/http_api/app.py` mit `ReadyResponse`-
     Schema + Komponenten-Probes (api/db/otel/tickloop).
   - NEU `.devcontainer/devcontainer.json` mit dokumentierten
     Build/Test/Abnahme-Kommandos.
   - NEU Dockerfile-Stage `iec61850-test` auf Python-
     3.12-Basis + separates uv-Sync mit `--python 3.12`.
   - NEU Makefile-Target `test-iec61850` (faehrt die
     Stage hoch, ruft `pytest tests/integration/test_iec61850_*`
     intern).
   - `tests/integration/test_iec61850_in_process_smoke.py`
     Skip-Marker-Removal.
   - NEU `docs/user/deploy-hardening.md` Audit-Tabelle
     mit allen 11 `GG-DEPLOY-*`-IDs.
   - NEU `tests/integration/test_m6_welle_6_deploy_smoke.py`
     mit 7 Smoke-Tests (siehe §1.2).
   - Trigger 009 wandert nach `done/` (resolved via Welle 6).
4. **Status/DoD-Sync** (C3) — Status-Flip + ADR 0046
   `Provisional → Provisional` (bleibt; M6-Closure-Welle 7
   flippt auf `Accepted`); aktive Welle auf Welle 7.

Self-Close-Folge C4a/C4b laufen nach C3 als M6-Welle-7-Pre-
C0a/Pre-C0b.

---

## 3. Architektur-Entscheidungen (Welle-6-Decision-Liste)

### Welle-6-D-1 — Sub-Slicing-Beschluss

**Frage:** Wird Welle 6 in Sub-Slices 6a/6b zerlegt?

Optionen:

- **A — Monolithische Welle 6** (alle 3 Luecken + Trigger
  009 + Audit-Doku in einer Welle).
- **B — Sub-Slicing 6a (Deploy-Hardening) + 6b (Trigger
  009 IEC-Pfad-B)**.

**Welle-6-Final: Option A (Monolithisch).** Begruendung:

- User-Ask „Alles fixen" → eine Welle 6 schliesst alle
  ausstehenden M6-Substanz-Items vor M6-Welle-7-Closure.
- Trigger 009 ist Repo-Novum (zweiter Python-Major-
  Stage), aber abgegrenzt zu einer Dockerfile-Stage —
  Welle-6-C2 traegt die Last in einem einzelnen Commit.
- Pattern-Konsistenz: Welle 5a/5b/5c waren Audit-Wellen
  mit C0/C2/C3-Stack; Welle 6 ist Substanz-Welle mit
  C0/C1/C2/C3-Stack (C1 fuer ADR 0046).
- Sub-Slicing-Schwelle (Welle-0-D-4) ist „> 1 Tag
  Substanz-Volume" — Welle 6 ist 2-3 Tage, knapp ueber
  der Schwelle; aber wenn Trigger 009 ausgegliedert
  wuerde, blieben fuer Welle 6a nur 0.5-1 Tag substanz
  (knapp unter Schwelle). Konsolidieren ist sauberer.

### Welle-6-D-2 — `GG-DEPLOY-006` Healthcheck-Three-State-Form

**Frage:** Wie wird die Three-State-Akzeptanz
(`healthy`/`degraded`/`unhealthy` + Ursache) realisiert?

Optionen:

- **A — `/health` erweitern**: Bestehender Endpoint
  liefert `{status, components, reason}`-Body statt
  `{"status":"ok"}`.
- **B — Neuer `/ready`-Endpoint**: `/health` bleibt
  Liveness-only; `/ready` ist Readiness mit Backend-
  Probes.

**Welle-6-Final: Option B (Neuer `/ready`-Endpoint).**
Begruendung:

- **Industrie-Pattern**: Kubernetes + Cloud-Run + Nomad
  unterscheiden Liveness (kann der Prozess Requests
  empfangen?) von Readiness (sind alle Backends
  erreichbar?). Wer `grid-gym` spaeter in einer
  Kubernetes-Umgebung deployed, bekommt die richtigen
  Probe-Semantiken out-of-the-box.
- **Substanz-Erbschaft**: Der bestehende
  `app.py:get_health`-Docstring vermerkt explizit
  „Persistente Backend-Checks ... kommen mit Welle 6c als
  `/ready`-Endpoint dazu" — Welle 6 loest diese
  vorgemerkte Pflicht ein, statt sie durch
  `/health`-Erweiterung zu uebergehen.
- **Compat**: Dockerfile `HEALTHCHECK` und Compose
  `depends_on.condition: service_healthy` bleiben
  unveraendert auf `/health`. Ein Container, dessen
  Postgres temporaer hakt, ist nicht „liveness-tot" —
  Restart wuerde Symptom verschlimmern (Postgres bleibt
  hakend, Container restart-loopt). Mit Liveness-/
  Readiness-Split signalisiert Readiness `503`, Liveness
  bleibt `200` — sauberes Failure-Mode-Mapping.
- **Test-Sensitivitaet**: ein `/health`-Erweiterung wuerde
  die Welle-5b-`test_safe_007_openapi_description_marks_simulation`
  + `test_safe_008_rest_invalid_payload_rejected_422`-
  Suite indirekt touchen; `/ready` ist additiv ohne
  Drift-Risiko.

**Konkrete `/ready`-Form**:

- Response-Schema `ReadyResponse`:
  `status: Literal["healthy", "degraded", "unhealthy"]`,
  `components: dict[str, ComponentStatus]` mit
  `ComponentStatus = {state: Literal["healthy",
  "degraded", "unhealthy"], reason: str | None}`. Per-
  Komponente-Three-State (statt binaer), damit die Komponenten-
  Ebene das Lastenheft-Z.-1876-Wortlaut „mit kurzer Ursache"
  pro Dienst tragen kann.
- Komponenten-Probes (vier **Lastenheft-Pflicht-Komponenten**,
  alle mit ≤1 s Timeout, parallel via `asyncio.gather`):
  - `api`: liveness-konforme Trivial-Probe — immer
    `healthy` bei laufendem Prozess. Der `/ready`-Endpoint
    laeuft im selben Prozess; wenn er antwortet, ist
    `api` per Definition erreichbar. Reflektiert
    nicht `/health` redundant, sondern markiert die
    API-Surface als auditiert in der Komponenten-Tabelle
    (Lastenheft-Wortlaut-Erfuellung).
  - `ui`: HTML-Route-Probe — interner HTTP-GET an der UI-
    Root (`/`); der `base.html`-Template-Render belegt,
    dass das UI-Surface (`adapters/driving/ui/templates/`)
    laedt + den Sim/Prod-Banner traegt. **Erlaeuterung**
    UI vs API: das UI-Layer ist FastAPI-render
    (HTMX-Templates), lebt im selben `api`-Container, aber
    architektonisch eigene Driving-Adapter-Surface
    (`adapters/driving/ui/`); der Lastenheft-Z.-1876-
    Wortlaut „API, UI" wird damit pro-Komponente
    abgedeckt — auch wenn beide Surfaces den gleichen
    Container teilen.
  - `db`: `RunRepositoryPort.ping()` (NEU; default-
    Implementation `SELECT 1` an
    `PostgresRunRepository`; `InMemoryRunRepository`
    gibt immer `True`).
  - `simulation`: probt den `simulation`-Compose-Service
    via `TickLoop`-Liveness-Marker. Der Service ist heute
    `sleep infinity`-Stub (Welle 6c); fuer die `/ready`-
    Welle gibt es zwei Sub-Form-Optionen:
    - **Sub-Form A**: Wenn ein TickLoop in-process laeuft
      (`DemoTickLoopDriver` ueber `app.state.tick_loop`),
      `_tick_loop_healthcheck.healthcheck()`-Output
      mappen (Code-verifiziert siehe naechster Bullet):
      `backpressure_status == "ok"` → `healthy`;
      `"delayed"` → `degraded` mit Ursache
      `"tick delayed; missed N ticks"`.
    - **Sub-Form B**: Wenn kein TickLoop laeuft (Compose-
      Stub `sleep infinity`; Demo-Stack ohne
      `GRID_GYM_DEMO_SCENARIO_PATH`), Status `degraded`
      mit Ursache `"simulation service is sleep-infinity
      stub (M2-Welle-7-pattern reactivates produktiv-
      TickLoop runner)"` — ehrliches Reflektieren des
      Stub-Stands (Stub ist erwartetes Compose-Verhalten,
      kein `unhealthy`-Ausfall).
- **`_tick_loop_healthcheck`-Mapping (Code-verifiziert
  Z. 152-153)**: der Adapter setzt
  `status = _STATUS_DELAYED if missed > 0 else _STATUS_OK`
  — **`delayed` und `missed > 0` sind gekoppelt** und
  koennen nicht separat auf zwei Three-State-Ebenen
  abgebildet werden. Mapping ist deshalb binaer-aus-
  Adapter-Sicht (`ok` → `healthy`; `delayed` → `degraded`);
  ein `unhealthy`-Pfad fuer „katastrophale TickLoop-
  Drift" ist absichtlich NICHT in dieser Welle modelliert
  — der `_tick_loop_healthcheck`-Adapter unterscheidet
  heute keine Severity zwischen „1 missed tick" und „100
  missed ticks". Ein dritter Severity-State waere
  Welle-X-Material (eigener Trigger falls Stakeholder-
  Bedarf entsteht).
- Aggregations-Regel: jede Komponente `unhealthy` →
  Endpoint-Status `unhealthy`; sonst falls eine
  Komponente `degraded` → `degraded`; sonst `healthy`.
- HTTP-Status: `200` bei `healthy`/`degraded`; `503` bei
  `unhealthy` (Kubernetes-Readiness-Konvention).
- **Nicht im Lastenheft-Pflicht-Komponenten-Set, aber im
  System**: `otel-collector` wird **nicht** in der
  Lastenheft-Z.-1876-Vier-Komponenten-Liste gefuehrt — der
  Collector ist Observability-Sibling (Welle-3-C2), nicht
  ein Lastenheft-Pflicht-Dienst (`GG-OTEL-001..004` sind
  optional). Audit-Doku `deploy-hardening.md` notiert
  Collector-Liveness als „nicht-Pflicht-Komponente".

### Welle-6-D-3 — `GG-DEPLOY-004` DevContainer-Form

**Frage:** Wie wird die DevContainer-Konfiguration
realisiert?

Optionen:

- **A — `.devcontainer/devcontainer.json` mit `image:`-
  Verweis** auf einen gepinten Tag (z. B.
  `grid-gym-base:latest`).
- **B — `.devcontainer/devcontainer.json` mit
  `build:`-Section** und `dockerfile: "../Dockerfile"`
  + `target: "base"`.
- **C — Separater DevContainer-Dockerfile**.

**Welle-6-Final: Option B (`build:`-Section + `target:
"base"`).** Begruendung:

- **Substanz-Wiederverwendung**: Das Dockerfile hat eine
  `base`-Stage (Python 3.14 + uv) und eine `runtime`-Stage
  (non-root, uvicorn-ENTRYPOINT). DevContainer braucht die
  `base`-Stage (uv + Python; kein non-root-User noetig,
  weil VS-Code-Server uid-mapped) — Build-Aufwand
  identisch, kein zweites Dockerfile zu pflegen.
- **Floating-Tag-Vermeidung**: ein `image:`-Verweis auf
  `grid-gym-base:latest` waere floating-tag-anfaellig
  (Maintainer-Rebuild liefert anderen Layer-Stack ohne
  Tag-Bump). Die `build:`-Section laesst VS-Code-Server den
  `base`-Stage beim Reopen rebuilden — gleiche Substanz wie
  `make build --target base`.
- **Drift-Minimierung**: Ein separater DevContainer-
  Dockerfile (Option C) wuerde bei Python-/uv-/Dependency-
  Bump in zwei Stellen synchronisiert werden muessen.
- **Drei Pflicht-Befehle**: `devcontainer.json` traegt
  `postCreateCommand` (Build: `uv sync --all-groups`),
  `postStartCommand` (Test: `make test-unit`) und ein
  `customizations.vscode.tasks`-Eintrag (Abnahme: `make
  demo`); Lastenheft-Akzeptanz „dokumentierte
  Konfiguration mit Build-, Test- und Abnahmebefehlen" ist
  damit ueber drei explizite Hooks erfuellt.

### Welle-6-D-4 — Trigger 009 IEC-Pfad-B Form

**Frage:** Wie wird der IEC-In-Process-Smoke
reaktiviert?

Optionen:

- **A — Dockerfile-Stage `iec61850-test` auf Python-
  3.12-Basis** mit separatem `uv sync --python 3.12`.
- **B — Eigene Docker-Compose-Service** mit Python-3.12-
  Image fuer den IEC-Smoke.
- **C — Pfad-A reaktivieren** (auf `pyiec61850-ng` 2.0.x
  warten).

**Welle-6-Final: Option A (Dockerfile-Stage) + versions-
bedingter Skip-Marker statt Modul-Removal.** Begruendung:

- **Pfad-A ist tot** (Trigger 009): kein cp314-Wheel
  auf PyPI; passiv-Pfad ohne Eskalations-Mechanismus.
- **Option B (Compose-Service)** waere Overkill: der IEC-
  Smoke braucht keinen Sibling-Sim-Container, nur einen
  zweiten Python-Interpreter. Compose-Service-Boot fuer
  einen einzigen Pytest-Lauf vergroessert die CI-
  Pipeline-Komplexitaet.
- **Option A** isoliert den Multi-Python-Cost auf eine
  Dockerfile-Stage. Default-`make test-integration` faehrt
  weiterhin Python-3.14-Stage; der Multi-Python-Cost
  ist opt-in via `make test-iec61850`.
- **CI-Pfad-Coordination (Skip-Marker-Form)**: ein
  blankes `pytestmark = pytest.mark.skip(...)`-Removal
  wuerde den Test auf Python-3.14 ausfuehren → Segfault.
  Welle-6-C2 ersetzt den unconditional Skip durch einen
  **versions-bedingten Skip**:
  `pytestmark = pytest.mark.skipif(sys.version_info >=
  (3, 13), reason="IEC-In-Process-Smoke laeuft real-
  library nur auf Python 3.12 — Trigger 009 Pfad B;
  pyiec61850-ng segfault auf >=3.13. Use 'make
  test-iec61850'.")`.
- **Folgen pro Pfad**:
  - Default `make test-integration` (Python 3.14): Skip
    bleibt aktiv per Versions-Check → kein Segfault, kein
    Smoke-Lauf.
  - `make test-iec61850` (Python-3.12-Stage): Skip greift
    nicht → real-library Smoke laeuft.
  - `make ci` (Default-Python 3.14): Skip aktiv im
    Default-Pfad. Welle-6-C2 erweitert die `ci`-Recipe
    um `make test-iec61850` als zusaetzlichen Schritt
    (Trigger-009-Coordination-Pflicht „Default-`make
    test-integration` muss beide Stages koordinieren"),
    sodass die normale Abnahme BEIDE Stages durchlaeuft.
- **Pattern-Verallgemeinerung**: Wenn asyncua oder eine
  andere Library spaeter denselben cp-Tag-Bruch hat,
  funktioniert das gleiche Pattern (`<lib>-test`-Stage,
  eigenes uv-Sync, separates Make-Target, versions-
  bedingter Skip-Marker im Test). ADR 0046 verankert
  das Pattern.

### Welle-6-D-5 — Audit-Form

**Frage:** Wie wird die `GG-DEPLOY-001..011`-Substanz in
einer Audit-Doku verankert?

**Welle-6-Final: Audit-Doku
`docs/user/deploy-hardening.md`** mit elf-Spalten-Tabelle
analog `safe-005-006-fallback-determinism.md` (Welle 5c).

Begruendung:

- **Pattern-Konsistenz** mit Welle 5a/5b/5c: jede
  abgeschlossene Lastenheft-Kategorie bekommt ein
  `docs/user/<kategorie>.md`-Audit-Doc.
- **Reviewer-Trail**: `GG-DEPLOY-001..006/011` sind alle
  ✓ produktiv nach Welle 6; `007..010` sind ⏸ M7+.
  Die Audit-Doku macht den Stand sichtbar.

### Welle-6-D-6 — ADR-Schaerfungs-Bedarf

**Frage:** Erfordert Welle 6 NEU ADRs oder Schaerfungen
bestehender ADRs?

**Welle-6-Final: NEU ADR 0046 `Multi-Python-Test-Stage-
Pattern` (`Provisional` in C1) mit zweigliedrigem
Scope.** Begruendung:

- **§2.1 Dockerfile-Multi-Python-Stage-Pattern**: ADR-
  0011-Schaerfung zum Dockerfile-Build-Pattern (additive
  Multi-Python-Stage; Default-`base`-Stage bleibt Python
  3.14). Trigger 009 erwaehnt den ADR explizit:
  „Eventueller ADR 0036 wenn das Pattern repo-weit als
  'Library-Compat-Test-Stage'-Pattern wiederverwendet
  wird" — Trigger-Aktivierung produziert diesen ADR
  (Nummer 0046, weil 0036 ist UI-Stack-Choice).
- **§2.2 Library-Compat-Install-Form**: ADR-0011-
  Schaerfung zum uv-Install-Pattern. Stage installiert
  via `uv pip install --system --no-deps -e .` plus
  `uv pip install --system --ignore-requires-python
  <set>` statt `uv sync --frozen`. ADR 0002 §2 Sprach-
  Floor (`>=3.13`) bleibt **unangetastet**;
  `pyproject.toml` + `uv.lock` werden in C2 **nicht**
  editiert. Die Install-Form ist explizit Library-
  Compat-Stage-Scope, nicht Default-Runtime-/Build-Pfad.
  Pattern verallgemeinerbar fuer asyncua-/andere Library-
  Inkompats, falls die je auftreten.
- **`/ready`-Endpoint braucht keinen NEU ADR**: ADR 0037
  (HTTP-API-Surface-Pattern) deckt additive Endpoints ab;
  Three-State-Status ist ein Implementation-Detail-Vertrag,
  kein Architektur-Vertrag.
- **`HealthPort` Driving-Adapter-Side braucht keinen
  NEU ADR**: Pattern analog zur Welle-4b-c-`_tick_loop_
  healthcheck.py`-Driving-Adapter-Side; GG-AR-PORT-DRV-
  007 ist als Driving-Adapter-Surface (nicht als pure
  Hexagon-Core-Driving-Port) realisiert — die Probe-
  Orchestrierung (DB + OTel-HTTP-Probe + TickLoop-Adapter)
  beruehrt Driven-Side-Externals, die in einem Core-
  basierten Driving-Port-Service-Implementation eine
  Schichten-Verletzung wuerden. Doku-Anker in
  `deploy-hardening.md` Audit-Tabelle.
- **DevContainer braucht keinen NEU ADR**: SOLLTE-
  Konvenienz; kein Architektur-Vertrag.

---

## 4. Liefer-Reihenfolge (4 Commits)

### Pre-C0 — bereits erledigt (M6-Welle-5c-Closure-Folge)

- `4db4715` (Pre-C0a: `git mv M6-welle-5c.md → done/`).
- `56f26b9` (Pre-C0b: Cross-Doc-Refs-Sync + done/README-
  Eintrag).

### C0 — `docs(plan)`: M6-welle-6 Slice-Doc

**Dieser Commit.** Enthaelt:

- NEU `M6-welle-6.md` (dieses Dokument).
- `in-progress/README.md` Bestand-Tabelle NEU
  `M6-welle-6.md`-Zeile.
- `M6-perf-security-cicd.md §3.1` Welle-6-Zeile
  `Pending → In Progress 2026-06-07`; Aktive-Welle-Block
  oben mit Welle-6-Stack-Anfang.
- `roadmap.md §4 M6` aktive Welle auf 6 mit Welle-6-
  Stack-Anfang.

### C1 — `docs(adr)`: NEU ADR 0046 Multi-Python-Test-Stage

- NEU `docs/plan/adr/0046-multi-python-test-stage-pattern.md`
  `Status: Provisional` (ADR-0011-Schaerfung zum Dockerfile-
  Build-Pattern).
- `docs/plan/adr/README.md` ADR-0046-Zeile + Status
  `Provisional`.

### C2 — `feat(deploy)` + `docs(user)`: /ready + DevContainer + IEC-Pfad-B + Audit-Doku + Smokes

Code- + Build- + Doku-Merge mit:

- NEU `/ready`-Endpoint:
  - `ReadyResponse` + `ComponentStatus` in
    `_schemas.py` (Pydantic v2 strict, analog ADR 0045).
  - `RunRepositoryPort.ping()` Protocol-Methode + 2
    Implementations (`InMemoryRunRepository` → `True`;
    `PostgresRunRepository` → `SELECT 1`).
  - `get_ready()` Endpoint-Handler in `app.py` mit
    parallelen Probes (asyncio.gather mit 1s timeout
    pro Komponente).
  - HTTP-Status-Mapping: `200` healthy/degraded;
    `503` unhealthy.
- NEU `.devcontainer/devcontainer.json`:
  - `build: { dockerfile: "../Dockerfile", target:
    "base" }` (VS-Code-Server baut die `base`-Stage
    selbst beim Reopen; kein Floating-`latest`-Tag).
  - `postCreateCommand: "uv sync --all-groups"`.
  - `customizations.vscode.tasks` mit drei Tasks
    („Build", „Test", „Abnahme").
- NEU Dockerfile-Stage `iec61850-test` (Pattern spiegelt
  die bestehende `base`-Stage; Dockerfile Z. 34 + Z. 43):
  - `FROM python:3.12-slim AS iec61850-base` — separate
    Stage damit Default-`base` (Python 3.14) unberuehrt
    bleibt.
  - `COPY --from=uv-binary /uv /usr/local/bin/uv` —
    uv-Binary aus dem `uv-binary`-Stage (gleicher Pattern
    wie `base`); ohne diesen Schritt ist `uv` im 3.12-
    Image nicht installiert.
  - `WORKDIR /src` + `COPY pyproject.toml ./`.
  - **Install-Strategie (ADR-0002-Vertragstreu):**
    `uv sync` wuerde an `requires-python = ">=3.13"` aus
    `pyproject.toml` scheitern (ADR 0002 §2 Floor; 3.12
    explizit ausgeschlossen — Z. 93 „Security-Only-
    Modus"). Statt `uv sync` nutzt die Stage einen pip-
    kompatiblen Install-Pfad:
    `RUN uv pip install --system --no-deps -e .` (grid_gym
    selbst path-installed) plus `RUN uv pip install
    --system --ignore-requires-python <pinned-set>` fuer
    die iec61850-spezifischen Deps (pyiec61850-ng + pytest
    + pytest-asyncio + plus stdlib-Wrapper-Set; konkrete
    Pin-Liste in ADR 0046 §2). Damit bleibt
    `pyproject.toml` + `uv.lock` **unangetastet**; ADR
    0002-Vertrag voll intakt; der Stage-Install ist eine
    bewusste Library-Compat-Schaerfung per ADR 0046.
  - `FROM iec61850-base AS iec61850-test` + `COPY src/
    tests/` + Default-`CMD` ruft `pytest` gegen den IEC-
    In-Process-Smoke.
- **`requires-python` bleibt `>=3.13`** — keine
  Floor-Aenderung, kein ADR-0002-Schaerfungs-Bedarf.
  Risiko-Mitigation siehe Risk R7.
- NEU Makefile-Target `test-iec61850`:
  - `docker build --target iec61850-test -t
    grid-gym-iec61850-test:latest .`.
  - `docker run --rm grid-gym-iec61850-test:latest`.
- `make ci`-Recipe-Erweiterung: hinter dem bestehenden
  `make test-integration`-Aufruf ein zusaetzlicher
  `make test-iec61850`-Aufruf (Trigger-009-Coordination-
  Pflicht; macht die normale Abnahme Multi-Stage-tauglich).
- `tests/integration/test_iec61850_in_process_smoke.py`
  Modul-Level-`pytestmark` von `pytest.mark.skip(...)` auf
  `pytest.mark.skipif(sys.version_info >= (3, 13), ...)`
  umgehaengt (versions-bedingter Skip statt unconditional;
  Default-Pfad bleibt segfault-frei, Python-3.12-Stage
  laeuft real-library).
- NEU `docs/user/deploy-hardening.md` Audit-Tabelle (alle
  11 `GG-DEPLOY-*`).
- NEU `tests/integration/test_m6_welle_6_deploy_smoke.py`
  mit 7 Smokes (siehe §1.2).
- Trigger 009 wandert nach `done/`:
  `git mv docs/plan/planning/open/009-iec61850-smoke-reactivation.md
  docs/plan/planning/done/009-iec61850-smoke-reactivation.md`.
- `open/README.md` Trigger-009-Eintrag entfernen; `done/
  README.md` Trigger-009-Eintrag ergaenzen.
- **Verifikation (lokal vor C2-Commit):**
  - `make gates` cache-frei gruen (10/10 A-1-Gates).
  - `make ci` cache-frei gruen.
  - `make test-iec61850` cache-frei gruen (NEU Target).
  - `make fullbuild` cache-frei gruen.
  - `make docs-check` cache-frei gruen.

### C3 — `docs(plan)`: Status/DoD-Sync + aktive Welle auf Welle 7

- `M6-welle-6.md` Status `In Progress → Done 2026-06-07`
  mit Liefer-Hash-Stack `C0..C3`.
- `M6-perf-security-cicd.md §3.1` Welle-6-Zeile `In
  Progress → Done`; Aktive-Welle-Block auf Welle 7;
  `§3.2 Welle 6`-Vorbelegung als „aufgeloest" notiert.
- `roadmap.md §4 M6` aktive Welle auf 7 + Welle-6-
  Abschluss-Notiz.
- `in-progress/README.md` Bestand-Tabelle Welle-6-Zeile
  `In Progress → Done`.
- ADR 0046 bleibt `Provisional` (M6-Welle-7-Closure
  flippt auf `Accepted` mit allen anderen M6-ADRs).

### Welle-6-Closure-Folge (nach C3)

- C4a `git mv M6-welle-6.md → done/` (rename-only).
- C4b Cross-Doc-Refs-Sync nach Move + `done/README.md`-
  Eintrag.

C4a/C4b dienen gleichzeitig als M6-Welle-7-Pre-C0a/Pre-C0b.

---

## 5. Critical Files

**Welle-6-NEU (geschrieben in C0/C1/C2):**

- `docs/plan/planning/in-progress/M6-welle-6.md` (C0,
  dieser Commit).
- `docs/plan/adr/0046-multi-python-test-stage-pattern.md`
  (C1).
- `.devcontainer/devcontainer.json` (C2).
- `docs/user/deploy-hardening.md` (C2).
- `tests/integration/test_m6_welle_6_deploy_smoke.py` (C2).

**Welle-6-MODIFY (in C0/C2/C3):**

- `docs/plan/planning/in-progress/README.md` (C0 + C3).
- `docs/plan/planning/in-progress/M6-perf-security-cicd.md`
  (C0 + C3).
- `docs/plan/planning/in-progress/roadmap.md` (C0 + C3).
- `docs/plan/adr/README.md` (C1 + C3).
- `src/grid_gym/adapters/driving/http_api/_health_adapter.py`
  (C2 — **NEU** Driving-Adapter-Side-`HealthPort`-Surface
  mit den vier Pflicht-Komponenten-Probes; Pattern analog
  `_tick_loop_healthcheck.py`. **Kein**
  `hexagon/ports/driving/health.py` — siehe Welle-6-D-6
  fuer die Architektur-Schichten-Begruendung).
- `src/grid_gym/adapters/driving/http_api/app.py` (C2 —
  NEU `/ready`-Endpoint, ruft `HealthPort`-Adapter).
- `src/grid_gym/adapters/driving/http_api/_schemas.py`
  (C2 — NEU `ReadyResponse` + `ComponentStatus` mit
  Three-State-Domaene).
- `src/grid_gym/hexagon/ports/driven/run_repository.py`
  (C2 — NEU `ping()` Protocol-Methode).
- `src/grid_gym/adapters/driven/persistence_postgres/run_repository.py`
  (C2 — NEU `ping()` Implementation).
- `src/grid_gym/adapters/driven/persistence_inmemory/run_repository.py`
  (C2 — NEU `ping()` Implementation).
- `Dockerfile` (C2 — NEU `iec61850-test`-Stage).
- `Makefile` (C2 — NEU Target `test-iec61850`).
- `tests/integration/test_iec61850_in_process_smoke.py`
  (C2 — Skip-Marker-Removal).
- `docs/plan/planning/open/README.md` (C2 — Trigger 009
  raus).
- `docs/plan/planning/done/README.md` (C2 — Trigger 009
  rein).

**Welle-6-MOVE (in C2):**

- `git mv docs/plan/planning/open/009-iec61850-smoke-reactivation.md
  docs/plan/planning/done/009-iec61850-smoke-reactivation.md`.

**Welle-6-UNBERUEHRT (kein Edit):**

- `GET /health` Endpoint + Dockerfile-`HEALTHCHECK` —
  Welle-6-D-2 ergaenzt `/ready` additiv, beruehrt nicht
  Liveness.
- `deploy/compose.yml` `api`-`ports`-Klausel (Welle-5c-
  Hardening bleibt unveraendert).
- Welle-5a/5b/5c-Audit-Dokus.
- Hexagon-Core-Substanz (`hexagon/core/**`) — kein
  Healthcheck-Material lebt im Core.
- ADRs 0041-0045 + alle aelteren ADRs.
- `pyproject.toml`/`uv.lock`/`pre-commit-config`.
- Alle `.github/workflows/`-Files (Welle-6-Substanz ist
  Build-Side; CI laeuft automatisch ueber die existierenden
  Workflows mit dem neuen `make test-iec61850`-Target).

---

## 6. Verifikationspfad

**Welle-6-Gate:**

- `make docs-check` cache-frei gruen.
- `make gates` cache-frei gruen (10/10 A-1-Gates).
- `make ci` cache-frei gruen.
- `make test-iec61850` cache-frei gruen (NEU Target;
  Python-3.12-Stage faehrt hoch + IEC-In-Process-Smoke
  laeuft real-library gruen).
- `make fullbuild` cache-frei gruen.

**DoD-Verifikation (§9):**

- C0 (dieser Commit) liefert nur Doc-Substanz +
  Status/Bestand-Sync.
- C1 prueft ADR 0046 `Provisional`-Status + ADR-0011-
  Schaerfung-Hinweis.
- C2 prueft:
  - 7 NEU Smoke-Tests gruen.
  - `/ready`-Endpoint liefert Three-State-Status mit
    Component-Breakdown.
  - `.devcontainer/devcontainer.json` traegt die drei
    Pflicht-Befehle.
  - `make test-iec61850` faehrt die `iec61850-test`-Stage
    hoch + IEC-Smoke laeuft real-library gruen.
  - Trigger 009 von `open/` nach `done/` gewandert.
  - Audit-Doku `docs/user/deploy-hardening.md` zeigt
    `GG-DEPLOY-001..006/011` als ✓ produktiv +
    `007..010` als ⏸ M7+.
- C3 prueft Status-Flip + aktive Welle auf Welle 7 +
  ADR 0046 bleibt `Provisional` (Closure-Welle 7 flippt).

**Abnahme-Verifikation:**

- `GG-DEPLOY-006` MUSS-Akzeptanz produktiv: `/ready`
  liefert `healthy`/`degraded`/`unhealthy` mit
  Komponenten-Breakdown + Ursachen-String pro
  Komponente (Lastenheft Z. 1876-1879).
- `GG-DEPLOY-004` SOLLTE konditional erfuellt: `.devcontainer/`
  enthaelt dokumentierte Build-/Test-/Abnahme-Befehle
  (Lastenheft Z. 1859-1861).
- Trigger 009 (IEC-Smoke-Pfad-B) aufgeloest: IEC-In-
  Process-Smoke laeuft real-library in `iec61850-test`-
  Stage; Mock-Substanz bleibt orthogonal als Unit-Test-
  Fallback.

---

## 7. Risiken

**R1 — `/ready`-Probe-Latency reisst CI-Boot-Smoke.**
`make runtime` testet heute nur `/health`; ein zu langer
`/ready`-Probe (z. B. Postgres-Connect ohne Pool) koennte
den Compose-Boot-Smoke ueber die `--wait-timeout 60`s
treiben.
**Mitigation:** `/ready` ist nicht im `make runtime`-
Smoke-Pfad. Compose-Boot pollt weiterhin `/health`
(Liveness, sofort `200`). `/ready` wird ausschliesslich
von Integration-Smokes getestet. Plus pro Komponente
1s-Timeout via `asyncio.wait_for` — worst-case 1s pro
Komponente, parallel ueber `asyncio.gather`.

**R2 — Multi-Python-Stage explodiert Build-Cache.** Die
NEU `iec61850-test`-Stage erfordert ein separates uv-
Sync mit Python 3.12 — das duplikiert den Image-Layer
(zweiter `.venv` mit allen Dependencies).
**Mitigation:** Stage ist opt-in via `make test-iec61850`;
Default-`make build` faehrt die Stage nicht hoch. Plus
Docker-Buildx-Cache-Mount fuer den `uv-cache`-Pfad in der
neuen Stage (analog Default-Stage). Plus Multi-Python-Cost
in ADR 0046 als bewusst akzeptiert dokumentiert.

**R3 — DevContainer-Floating-Tag bei `image:`-Verweis.**
Ein `image: grid-gym-base:latest`-Verweis waere floating
(Maintainer-Rebuild produziert anderen Layer-Stack ohne
Tag-Bump; alte VS-Code-Session koennte Stale-Image
konsumieren).
**Mitigation (in Welle-6-D-3 Final verankert):**
`build:`-Section mit `dockerfile: "../Dockerfile"` +
`target: "base"` als Default-Form; VS-Code-Server baut
die `base`-Stage selbst beim Reopen — identische Substanz
wie `make build --target base`, kein Tag-Mismatch moeglich.
Smoke `test_deploy_004_devcontainer_build_section_pins_base_stage`
pinnt das in CI.

**R4 — Trigger 009 wandert verfrueht nach `done/`.**
Wenn Welle 6 die IEC-Smoke aktiviert aber das Pattern
spaeter (z. B. CI) instabil wird, koennte der Trigger
fruehzeitig als geschlossen markiert sein.
**Mitigation:** Trigger 009 wandert nur dann, wenn der
Welle-6-C2-Run + die 7 NEU Smokes inkl.
`test_trigger_009_iec61850_skipmark_is_versions_conditional`
plus die Stage-Ausfuehrung in `make test-iec61850`
cache-frei gruen sind. ADR 0046 dokumentiert das
Reaktivierungs-Pattern, sodass ein erneuter Trigger
trivial waere falls die `iec61850-test`-Stage spaeter
faellt.

**R5 — `RunRepositoryPort.ping()` veraendert Driven-Port-
Vertrag.** NEU Protocol-Methode an einem etablierten
Driven-Port; Adapter-Implementierungen muessen mitziehen.
**Mitigation:** Welle 6 traegt beide existierenden
Implementations selbst nach (`InMemoryRunRepository` +
`PostgresRunRepository`). Welle-6-C2-Verifikation prueft,
dass keine `Protocol`-Mismatches in `make typecheck` (mypy
strict) entstehen.

**R7 — Python-3.12-Install gegen `requires-python=
>=3.13` (ADR-0002-Vertragstreu).** Die NEU `iec61850-
test`-Stage installiert grid-gym auf Python 3.12, aber
`pyproject.toml` enforciert `requires-python = ">=3.13"`
per ADR 0002 §2 (Z. 93: 3.12 ist Security-Only und
explizit ausgeschlossen). `uv sync --frozen` wuerde die
Installation ablehnen; eine Floor-Relaxierung in
`pyproject.toml` waere ein ADR-0002-Vertragsbruch.
**Mitigation (in D-4 final verankert):** Stage nutzt
`uv pip install --system --no-deps -e .` (grid_gym
path-install ohne Dep-Resolve) plus `uv pip install
--system --ignore-requires-python <pinned-set>` fuer die
iec61850-spezifischen Deps. `pyproject.toml` + `uv.lock`
bleiben unangetastet; ADR 0002-Vertrag intakt; die
Install-Form-Schaerfung ist von ADR 0046 §2.2 explizit
abgedeckt. Code-Audit (grep ueber `src/grid_gym/` nach
3.13-only-Syntax-Features) hat ausschliesslich
`type X = Y`-Aliases (PEP 695, 3.12+ unterstuetzt)
gefunden — die Adapter-Module sind unter Python 3.12
lauffaehig.

**R6 — Welle-6-Scope ist zu gross fuer eine Welle.**
Drei substantielle Items (`/ready` + DevContainer +
IEC-Pfad-B) plus ADR plus Audit-Doku plus 7 Smokes.
**Mitigation:** User-Ask „Alles fixen" hat das explizit
gewollt; Sub-Slicing 6a/6b wurde in D-1 erwogen und
verworfen. Falls C2-Substanz im Run zu gross wird, kann
ein zweiter C2-Commit (C2a + C2b) den Cut machen —
Pattern aus Welle-3 (`feat(observability)`-Doppel-Commit).

---

## 8. Wandert nach

- **Self-Close-Move im eigenen Welle-Stack**: nach C3
  schliesst die Welle ihre eigene Commit-Sequenz mit
  `git mv M6-welle-6.md → ../done/M6-welle-6.md` (C4a) +
  Cross-Doc-Refs-Sync (C4b). Pattern analog M6-Welle-5c-
  C4a `4db4715`/C4b `56f26b9`.
- C4a/C4b dienen gleichzeitig als M6-Welle-7-Pre-C0a/Pre-
  C0b.
- `done/README.md`-Eintrag fuer `M6-welle-6.md` ergaenzen
  (C4b).
- ADR 0046 bleibt `Provisional` bis M6-Welle-7-Closure
  (alle M6-ADRs flippen dort gemeinsam auf `Accepted`).
- Trigger 009 ist nach C2 in `done/` — die `done/README.md`-
  Trigger-Tabelle bekommt einen Eintrag mit Closure-
  Stack-Hash.

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] **C0 — NEU `M6-welle-6.md`** mit §1..§9-Struktur
  (dieser Commit).
- [x] **C0 — `in-progress/README.md`** Bestand-Tabelle
  NEU `M6-welle-6.md`-Zeile.
- [x] **C0 — `M6-perf-security-cicd.md §3.1`** Welle-6-
  Zeile `Pending → In Progress 2026-06-07`.
- [x] **C0 — `roadmap.md §4 M6`** aktive Welle auf 6.
- [ ] **C1 — NEU `docs/plan/adr/0046-multi-python-test-
  stage-pattern.md`** `Provisional` (ADR-0011-Schaerfung
  zum Dockerfile-Build-Pattern).
- [ ] **C1 — `docs/plan/adr/README.md`** ADR-0046-Zeile.
- [ ] **C2 — NEU `_health_adapter.py` Driving-Adapter-
  Side-`HealthPort`-Surface** mit den **vier Lastenheft-
  Pflicht-Komponenten** (api/ui/db/simulation) + Three-
  State-`ComponentStatus` (Pattern analog `_tick_loop_
  healthcheck.py`; kein `hexagon/ports/driving/health.py`).
- [ ] **C2 — NEU `/ready`-Endpoint** + `ReadyResponse` +
  `RunRepositoryPort.ping()` (2 Implementations).
- [ ] **C2 — `pyproject.toml` + `uv.lock` UNBERUEHRT**
  (Library-Compat-Stage installiert via `uv pip install
  --no-deps -e .` + `--ignore-requires-python <set>`;
  ADR-0002-Vertrag intakt; Risk R7).
- [ ] **C2 — NEU `.devcontainer/devcontainer.json`** mit
  drei dokumentierten Befehlen.
- [ ] **C2 — NEU Dockerfile-Stage `iec61850-test`** auf
  Python-3.12-Basis + Makefile-Target `test-iec61850`.
- [ ] **C2 — `tests/integration/test_iec61850_in_process_smoke.py`**
  Skip-Marker auf `pytest.mark.skipif(sys.version_info
  >= (3, 13), ...)` umgehaengt (kein blanker Removal —
  Default-Python 3.14 skip-t weiterhin).
- [ ] **C2 — `make ci`-Recipe** erweitert um `make
  test-iec61850` (Trigger-009-Coordination-Pflicht).
- [ ] **C2 — NEU `docs/user/deploy-hardening.md`** Audit-
  Tabelle (alle 11 `GG-DEPLOY-*`).
- [ ] **C2 — NEU `tests/integration/test_m6_welle_6_deploy_smoke.py`**
  mit 7 Smokes.
- [ ] **C2 — Trigger 009 wandert nach `done/`** (`git mv`
  + open/README-Removal + done/README-Eintrag).
- [ ] **C2 — `make gates`** cache-frei gruen.
- [ ] **C2 — `make ci`** cache-frei gruen.
- [ ] **C2 — `make test-iec61850`** cache-frei gruen.
- [ ] **C2 — `make fullbuild`** cache-frei gruen.
- [ ] **C3 — `M6-welle-6.md`** Status `In Progress → Done
  2026-06-07` mit Liefer-Hash-Stack.
- [ ] **C3 — `M6-perf-security-cicd.md §3.1`** Welle-6-
  Zeile `In Progress → Done` + Aktive-Welle-Block auf
  Welle 7.
- [ ] **C3 — `roadmap.md §4 M6`** aktive Welle auf 7 +
  Welle-6-Abschluss-Notiz.
- [ ] **C3 — `in-progress/README.md`** Bestand-Tabelle
  Welle-6-Zeile `In Progress → Done`.
- [ ] **C3 — `make docs-check`** cache-frei gruen.

**Anti-Scope-Verifikation (Welle 6 NICHT):**

- [x] Keine Kubernetes-Manifeste (`GG-DEPLOY-007`) —
  M7+.
- [x] Kein Rolling-Update / Zero-Downtime / Rollback
  (`GG-DEPLOY-008..010`) — M7+.
- [x] Kein separater UI-Container (UI ist Driving-Adapter
  in `adapters/driving/ui/`; lebt im `api`-Container, aber
  eigene Komponente in der Three-State-Tabelle).
- [x] Kein produktiver Sim-Runner (Compose-Service-Stub
  bleibt `sleep infinity`; `simulation`-Komponente in
  `/ready` reflektiert den Stub-Stand ehrlich per
  Welle-6-D-2 Sub-Form B).
- [x] Kein NEU Driven-Port fuer Health-Probes (NEU
  `ping()`-Methode an existierendem
  `RunRepositoryPort` ist Schaerfung, kein NEU Port).
- [x] **NEU `HealthPort`-Driving-Adapter-Side IST im
  Scope** (per `GG-AR-PORT-DRV-007` Architektur-Pflicht
  als Driving-Adapter-Surface realisiert, nicht als
  Hexagon-Core-Driving-Port — Pattern analog Welle-4b-c-
  `_tick_loop_healthcheck.py`; Probe-Orchestrierung
  beruehrt Driven-Side-Externals).
- [x] Keine Reduzierung der Mock-Substanz (18 Mock-
  Unit-Tests bleiben).
- [x] Keine `pyiec61850-ng`-Version-Bump auf 2.0.x
  (Pfad A tot).
- [x] Kein NEU ADR fuer `/ready`-Endpoint (ADR 0037
  deckt additiv).
- [x] Kein NEU ADR fuer DevContainer (SOLLTE-
  Konvenienz).

---

## References

- [`../done/M6-welle-5c.md`](../done/M6-welle-5c.md) —
  Welle-5c (SOLLTE-Items + IP/Netz-Beschraenkung;
  `GG-SAFE-005/006`) — vorhergehende Welle; schliesst
  die Welle-5-Subdivision (5a + 5b + 5c).
- [`../done/009-iec61850-smoke-reactivation.md`](../done/009-iec61850-smoke-reactivation.md)
  — Trigger 009 IEC-Pfad-B-Spec; wandert in C2 nach
  `done/`.
- [`M6-perf-security-cicd.md §3.2 Welle 6`](../in-progress/M6-perf-security-cicd.md)
  — M6-Slice-Plan Welle-6-Vorbelegung.
- [`../../../../spec/lastenheft.md §23 GG-DEPLOY-001..011`](../../../../spec/lastenheft.md)
  — Lastenheft-Akzeptanz fuer Deploy-IDs (Z. 1833-1920);
  plus Realisierungs-Traceability §23 (Z. 2307-2309
  fuer `GG-DEPLOY-001..011`).
- [`../../../../spec/architecture.md §15`](../../../../spec/architecture.md)
  — Architektur-§15 Beobachtbarkeit (Metrik-Liste; bietet
  den Kontext fuer Three-State-Status, ohne Healthcheck-
  Endpoint-Form normativ vorzugeben).
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md)
  — Pattern-Vorbild fuer ADR 0046 (Schaerfung des
  Dockerfile-Build-Patterns ohne Supersedes).
- [`../../adr/0035-iec61850-adapter-profile.md`](../../adr/0035-iec61850-adapter-profile.md)
  §2.5 — Mock-only-Fallback-Begruendung; bleibt
  orthogonal gueltig (Mock-Unit-Tests bleiben).
- [`../../adr/0037-http-api-surface-pattern.md`](../../adr/0037-http-api-surface-pattern.md)
  — additive `/ready`-Endpoint-Vertrag ohne NEU ADR.
- [`../../../user/safe-005-006-fallback-determinism.md`](../../../user/safe-005-006-fallback-determinism.md)
  + [`../../../user/safe-007-008-sim-prod-input-validation.md`](../../../user/safe-007-008-sim-prod-input-validation.md)
  + [`../../../user/safe-001-004-quality-pipeline.md`](../../../user/safe-001-004-quality-pipeline.md)
  — Welle-5*-Audit-Doc-Vorbilder; Welle 6 liefert das
  vierte Audit-Doc `deploy-hardening.md`.
