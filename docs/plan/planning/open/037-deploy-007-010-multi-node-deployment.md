# 037 — `GG-DEPLOY-007..010` Multi-Node-Deployment-Familie (Lücke)

**Status:** Open — Substanz-Lücke aus M6-Welle-6-Audit
**Datum:** 2026-06-07
**Quelle:** M6-Welle-6-C0 (Deploy-Hardening + IEC-Smoke-
Pfad-B; siehe
[`../in-progress/M6-perf-security-cicd.md`](../in-progress/M6-perf-security-cicd.md)
§3.1 Welle-Status-Tabelle: „`GG-DEPLOY-007..010` ⏸ M7+
per Lastenheft-Traceability Z. 2308").

---

## Lastenheft-Akzeptanz

Die Vier IDs decken die **Multi-Node-Deployment-Familie** ab
(thematisch gekoppelt: K8s-Manifeste sind Vorbedingung fuer
Rolling-Update/Zero-Downtime/Rollback):

- **`GG-DEPLOY-007` SOLLTE** (Z. 1881-1887):
  > Die Plattform SOLLTE Kubernetes-faehig deploybar sein.
  > Akzeptanz: Wenn Kubernetes-Deployment unterstuetzt wird,
  > sind Manifeste oder Helm/Kustomize-Artefakte fuer API,
  > UI, Simulationsdienst und Persistenzadapter dokumentiert.

- **`GG-DEPLOY-008` SOLLTE** (Z. 1889-1895):
  > Rolling Updates SOLLTEN fuer spaetere verteilte
  > Deployments unterstuetzt werden.
  > Akzeptanz: Wenn verteiltes Deployment implementiert ist,
  > dokumentiert die Plattform Update-Strategie,
  > Healthcheck-Gating und Verhalten laufender Simulationen.

- **`GG-DEPLOY-009` KANN** (Z. 1897-1903):
  > Zero-Downtime-Deployment KANN fuer nicht laufkritische
  > Dienste unterstuetzt werden.
  > Akzeptanz: Wenn Zero-Downtime-Deployment implementiert
  > ist, sind betroffene Dienste, Einschraenkungen und
  > Ausschluss laufender Simulationen dokumentiert.

- **`GG-DEPLOY-010` SOLLTE** (Z. 1905-1911):
  > Rollback-Unterstuetzung SOLLTE fuer verteilte
  > Deployments bereitgestellt werden.
  > Akzeptanz: Wenn verteiltes Deployment implementiert ist,
  > dokumentiert die Plattform Rollback fuer API, UI,
  > Simulationsdienst und Datenbankschema inklusive Grenzen
  > bei migrationsbedingten Datenmodell-Aenderungen.

**Architektur-Anforderung** (`spec/architecture.md §16
Z. 915-917`):

> Kubernetes-Manifeste sind SOLLTE; Rolling Update,
> Zero-Downtime und Rollback sind explizit als **Trigger-
> getriebene Folgearbeit dokumentiert** (`GG-DEPLOY-007..
> 010`).

Diese Trigger-Notiz ist genau die in der Architektur
geforderte Verankerung — bisher hat die Norm-Vorgabe ohne
korrespondierenden Trigger gelebt (Welle-6-Audit-Befund).

## Substanz-Stand (Welle-6-Audit 2026-06-07)

- ✗ **Kein Kubernetes-Manifest-Artefakt im Repo**: kein
  `deploy/k8s/`, kein `deploy/helm/`, kein
  `deploy/kustomize/`-Verzeichnis. Compose-Stack
  (`deploy/compose.yml`) ist die einzige Deployment-Form.

- ✗ **Keine Rolling-Update-Doku**: weder ein
  Strategie-Dokument noch Healthcheck-Gating-Hooks fuer
  verteiltes Deployment. Welle-6-`/ready`-Endpoint wird
  als Readiness-Probe-Surface produktiv (Welle-6-D-2);
  Verwendung in K8s-Manifesten ist explizit aufgehoben (M7+).

- ✗ **Keine Zero-Downtime-Doku**: kein dokumentierter
  Ausschluss „laufender Simulationen" gegen Deployment-
  Drift. Lastenheft-Akzeptanz ist konditional
  („KANN"); ohne Trigger-Aktivierung bleibt sie unerfuellt.

- ✗ **Keine Rollback-Strategie**: kein dokumentierter
  Rollback-Pfad fuer API/UI/Simulationsdienst/Datenbank.
  Die M1-Welle-6c-Alembic-Basismigration hat einen
  `downgrade()`-Pfad, aber keinen expliziten Rollback-Test
  pro Migration.

- **Bestehende Substanz, die wiederverwendet werden kann**:
  - `deploy/compose.yml` mit 4 Services + Healthchecks (M1-
    Welle-6c) — Vorbild fuer K8s-Service/Deployment-Mapping.
  - `/ready`-Endpoint mit Three-State-Status (Welle-6-C2) —
    fuer K8s-Readiness-Probe direkt verwendbar.
  - Dockerfile multi-stage (runtime-Stage; non-root + Port
    8080) — Container-Image-Substanz steht.
  - Alembic-Migrationen (M1-Welle-6c) — Vorbild fuer K8s-Job-
    based-Migration-Step.

## Erwartete Lieferung

Bei Aktivierung (siehe Aktivierungs-Bedingung) entweder ein
eigenstaendiger Slice oder eine M7-Welle-Vorbelegung:

1. **K8s-Manifest-Artefakte** unter `deploy/k8s/` (oder
   `deploy/helm/`-Chart, je nach D-1-Entscheidung im
   Folge-Slice-C0):
   - `Deployment` fuer `api` mit Readiness-Probe gegen
     `/ready` + Liveness-Probe gegen `/health` (Welle-6-
     Substanz wiederverwendbar). **Abgrenzung:** `/ready`
     ist nur Backend-/Surface-Readiness; es ist kein Nachweis
     „keine aktiven Simulationen" und darf nicht als
     Active-Run-Gate fuer Rollouts interpretiert werden.
   - **UI-Artefakt-Vertrag** fuer `GG-DEPLOY-007`:
     Entweder dokumentierte Co-Location im `api`-Deployment
     mit eigener Route/Ingress-Regel fuer die UI-Surface
     (`/`, HTML-Template-Render, Sim/Prod-Banner) oder ein
     separates `Deployment`/`Service`, falls die Topologie im
     Folge-Slice-C0 auf getrennte UI-Prozesse wechselt. In
     beiden Varianten muss das Artefakt die UI-Surface
     explizit neben API, Simulation und Persistenzadapter
     ausweisen.
   - `Deployment` fuer `simulation` (sobald produktiver
     Sim-Runner existiert — sonst Stub-Service).
   - `Service` (ClusterIP) fuer api + simulation.
   - `Ingress` oder LoadBalancer-Service fuer externen
     Zugriff; bei Co-Location routet die Ingress-Form API-
     Pfade und UI-Root sichtbar getrennt. **IP-/Netz-
     Beschraenkung ist Pflicht**: K8s-Externalisierung muss
     `carveouts.md §2.7` analog zum Demo-Compose umsetzen
     (z. B. Ingress-Source-Range-Whitelist,
     `NetworkPolicy`, dokumentierte externe
     Firewall-/Reverse-Proxy-Boundary oder bewusst
     isolierter Lab-LoadBalancer). Ein unauthentifizierter
     UI/API-Pfad darf nicht still als offen erreichbarer
     Cluster-/Internet-Einstieg ausgeliefert werden.
   - `StatefulSet` fuer Postgres (oder Verweis auf externes
     Postgres-/Managed-Postgres-/Operator-Pattern).
   - `Job` als **alleiniger Migration-Owner** fuer Alembic-
     `upgrade`; `initContainer` duerfen nur DB-Erreichbarkeit
     und Schema-Head pruefen/abwarten, aber keine Migration
     ausfuehren.
   - `ConfigMap` + `Secret` fuer ENV-Variablen aus
     `compose.yml`-Substanz.

2. **Rolling-Update-Strategie-Doku** in
   `docs/user/k8s-deploy.md` (oder `deploy/k8s/README.md`):
   - `Deployment.spec.strategy.type: RollingUpdate` mit
     `maxUnavailable: 0` + `maxSurge: 1` fuer api (kann
     unterbrechungsfrei).
   - Verhalten laufender Simulationen: **Lastenheft-
     Pflicht** zu dokumentieren (Akzeptanz Z. 1893-1895).
     Welle-6-`/ready` ist nur Probe-Surface; `degraded` kann
     HTTP 200 liefern und „no TickLoop → degraded" ist kein
     Active-Run-Nachweis. Der Folge-Slice MUSS ein eigenes
     Active-Run-Gate dokumentieren und testen (z. B.
     `RunRepository`-/`TickLoopRegistry`-Abfrage,
     Maintenance-Lock oder Pre-Rollout-Job). Rolling-Update
     darf nur starten, wenn dieses Gate „keine aktiven
     Laeufe" meldet ODER explizit ein **Rolling-Update-only**
     Modus „active runs killing" akzeptiert, dokumentiert und
     getestet wird.

3. **Zero-Downtime-Doku** (konditional via `GG-DEPLOY-009`
   `KANN`):
   - Welche Dienste sind Zero-Downtime-faehig (api nur fuer
     zustandslose HTTP-Pfade; simulation, live connections und
     postgres haben Einschraenkungen).
   - Ausschluss laufender Simulationen **strenger als Rolling-
     Update**: Zero-Downtime darf nur behauptet werden, wenn
     das Active-Run-Gate „keine aktiven Laeufe" meldet. Ein
     akzeptierter „active runs killing"-Modus schliesst den
     Zero-Downtime-Claim fuer diesen Rollout explizit aus.
   - **WebSocket-/Live-Connection-Grenze** fuer API/UI:
     bestehende WebSocket-Verbindungen gelten nur dann als
     Zero-Downtime-faehig, wenn der Folge-Slice Load-Balancer-
     Draining, Reconnect-Semantik und UI-Recovery dokumentiert
     und testet. Sonst werden WebSocket-/Live-Telemetry-Pfade
     explizit aus der Zero-Downtime-Behauptung ausgeschlossen.

4. **Rollback-Strategie-Doku**:
   - Image-Tag-Pin-Konvention (kein floating `latest`;
     Welle-5c-D-4-`ports`-Hardening-Pattern uebertragbar).
   - Alembic-`downgrade()`-Pfad pro Migration + NEU separater
     Rollback-Sensor (z. B. `make migration-rollback-check`
     oder `make test-db-rollback`) gegen eine ephemere Test-DB.
     Aufnahme dieses Sensors in `make ci`, `make fullbuild`
     oder einen verbindlichen Workflow ist ein ADR-/Plan-
     Pruefpunkt (siehe Anti-Scope); der Sensor darf nie gegen
     persistente Demo-/Stakeholder-Daten laufen.
   - Grenzen: **Lastenheft-Pflicht** zu dokumentieren
     („migrationsbedingte Datenmodell-Aenderungen" sind
     ggf. nicht rollback-faehig — Z. 1909-1911).

5. **NEU K8s-Validierungs-Sensor** fuer Manifest-Pruefung:
   `make k8s-validate` mit `kubeconform` oder `kubectl
   --dry-run=server` gegen ein Sibling-Kind-Cluster. Das
   Target bleibt zunaechst ein eigenstaendiger Sensor; die
   Aufnahme in `make ci`, `make fullbuild` oder einen
   verbindlichen Workflow ist ein separater ADR-/Plan-
   Pruefpunkt (siehe Anti-Scope).

6. **NEU K8s-Smoke** (lokal via kind), bewusst **nicht** im
   Default-`make test-integration`-Pfad:
   `tests/k8s/test_k8s_deployment_smoke.py` plus separates
   `make test-k8s`-Target analog Welle-6-`make test-iec61850`.
   Hintergrund: `make test-integration` ruft heute pauschal
   `pytest tests/integration/` auf; ein Kind/K8s-Smoke unter
   `tests/integration/` wuerde dadurch implizit Teil von
   `make ci`/`make fullbuild`. Falls der Folge-Slice aus
   historischen Gruenden doch `tests/integration/` nutzt, MUSS
   der Test per eigener Marker-/Makefile-Auswahl aus dem
   Default-Runner ausgeschlossen sein, bis ein ADR-/Plan-Anker
   die Gate-Aufnahme beschliesst. Der Smoke startet einen
   kind-Cluster, deployed die Manifeste, pollt `/ready` und
   prueft die UI-Route separat (HTML-Surface + Sim/Prod-
   Marker), damit `GG-DEPLOY-007` nicht nur API/Simulation/
   Persistenz abdeckt.

   Mindest-Pins:
   - Happy: `api`-Deployment wird ready, UI-Route liefert
     HTML, `simulation`-Stub/Runner ist gemaess dokumentiertem
     Status sichtbar, Postgres/Migration-Job laeuft einmalig;
     `initContainer` fuehren keine Alembic-Migration aus.
     Der externe Zugriff ist ueber eine explizite
     IP-/Netz-Boundary abgesichert (Ingress-Whitelist,
     NetworkPolicy, dokumentierte externe Boundary oder
     isolierter Lab-LoadBalancer) und die Doku nennt, dass
     UI/API weiterhin unauthentifiziert sind.
   - Boundary: Rolling-Update fuer `api` mit
     `maxUnavailable: 0`/`maxSurge: 1` bleibt ready und
     dokumentiert das Verhalten laufender Simulationen ueber
     das separate Active-Run-Gate, nicht ueber `/ready`;
     falls Zero-Downtime fuer Live-UI behauptet wird, bleibt
     eine WebSocket-/Live-Telemetry-Verbindung ueber Rollout
     hinweg nutzbar oder reconnectet kontrolliert.
   - Negative: Rollout bei aktiver Simulation wird blockiert
     oder explizit als "active runs killing" dokumentiert und
     getestet; letzteres ist **kein** Zero-Downtime-Pfad.
     Jeder Zero-Downtime-Claim mit aktivem
     "active runs killing" schlaegt fehl. Rollback-Grenzen
     fuer nicht downgrade-faehige Migrationen schlagen
     kontrolliert an statt still zu "succeeden". Ein
     offen exponierter Ingress/LoadBalancer ohne die oben
     dokumentierte IP-/Netz-Boundary schlaegt ebenfalls fehl,
     weil `carveouts.md §2.7` die Auth-Luecke nur ueber die
     Auflagen-Schicht akzeptiert.

7. **Audit-Doku-Sync**: nach Implementation wird die
   kanonische Deploy-Hardening-Audit-Tabelle synchronisiert
   (Welle-6-C2 plant `docs/user/deploy-hardening.md`; falls
   Welle 6 den Pfad bis zur Aktivierung umbenennt oder nicht
   anlegt, zieht der Folge-Slice zuerst diesen Trigger und die
   kanonische Audit-Surface nach). `GG-DEPLOY-007..010`
   flippt dort von ⏸ M7+ auf ✓ produktiv. Trigger 037 wandert
   nach `done/` mit dem aufloesenden Slice.

## Aktivierungs-Bedingung

- **Stakeholder-Bedarf fuer Multi-Node-Deployment**: konkrete
  Stakeholder-Anfrage „grid-gym in unserem K8s-Cluster
  deploybar". Heute kein konkreter Anker.
- **Skalierungs-Druck**: wenn die Demo / Abnahme ueber
  einen einzelnen Compose-Host nicht mehr ausreicht (z. B.
  Multi-Reviewer-Demo-Stack oder CI-Compose-Parallelisierung).
- **Compliance-Druck** (Production-Deployment): wenn ein
  Stakeholder einen produktionsnahen Deployment-Pfad
  abnehmen will (auch wenn `grid-gym` strukturell
  Simulation-only bleibt per `GG-SAFE-007`).
- **Architektur-Pflicht-Aufloesung**: Architektur §16
  Z. 916 fordert „Trigger-getriebene Folgearbeit". Diese
  Notiz erfuellt die Verankerungs-Pflicht; die volle
  Auspraegung haengt am Stakeholder-Anker.

## Anti-Scope

- **Keine produktive Anlagensteuerung** — strukturell per
  `GG-SAFE-007` + Lastenheft Z. 1161-1163 ausgeschlossen.
  K8s-Deployment bleibt Simulation-only (die Sim/Prod-
  Marker aus Welle 5b — UI-Banner, OpenAPI-Description,
  Adapterkonfiguration — gelten auch fuer K8s-Deployment).
- **Keine Production-Cloud-Anbindung** (AWS/GCP/Azure-
  spezifische Manifeste) — grid-gym bleibt Cloud-agnostisch;
  Vanilla-K8s ist das Ziel.
- **Keine Auto-Scaling/HPA-Substanz** — Lastenheft fordert
  das nicht; HPA waere Production-Concern.
- **Keine GitOps-Substanz** (ArgoCD/Flux/...) — out-of-
  scope; die Manifeste sind statisch deploybar.
- **Kein neuer Driving-/Driven-Port** — K8s-Deployment ist
  Operations-/Build-Schicht, kein Architektur-Vertrag-
  Wechsel.
- **Kein automatischer NEU-ADR-Zwang fuer statische K8s-
  Manifeste** — reine Operations-Artefakte unter
  `deploy/k8s/` koennen Slice-Substanz bleiben. **ADR-
  Pruefpunkt im Folge-Slice-C0:** Sobald `make k8s-validate`
  oder `make test-k8s` in `make ci`, `make fullbuild` oder
  einen verbindlichen Workflow aufgenommen wird, entsteht ein
  repo-weiter Gate-Vertrag und braucht ADR-/Plan-Anker
  analog den bestehenden Quality-Gates. Dasselbe gilt, wenn
  ein Probe-, Rollout- oder Rollback-Pattern repo-weit fuer
  mehrere Services wiederverwendet werden soll. Ein DB-
  Rollback-Sensor (`make migration-rollback-check` /
  `make test-db-rollback`) bleibt ebenfalls separat, bis seine
  Aufnahme in `make ci`, `make fullbuild` oder GitHub Actions
  explizit per ADR-/Plan-Anker beschlossen ist.

## Bezug

- [`../in-progress/M6-perf-security-cicd.md`](../in-progress/M6-perf-security-cicd.md)
  §3.1 Welle-Status-Tabelle — Welle-6-Substanz fuer
  `GG-DEPLOY-006` (`/ready`-Endpoint) ist die Vorbedingung
  fuer K8s-Readiness-Probe; `GG-DEPLOY-007..010` bleiben dort
  als M7+-Folgearbeit verankert.
- `spec/lastenheft.md` Z. 1881-1911 + §27.2 Z. 2308
  (Traceability) — Akzeptanz-Quelle und „Post-MVP"-Defer-
  Vermerk.
- `spec/architecture.md` §16 Z. 915-917 — Architektur-
  Vorgabe „Trigger-getriebene Folgearbeit".
- [`carveouts.md §2.7`](../in-progress/carveouts.md) — IP-/
  Netz-Beschraenkung im Demo-Compose; K8s-Deployment muss
  die Auflagen-Schicht analog umsetzen (Ingress-Form mit
  expliziter Whitelist).
- [`../../adr/0043-image-audit-strategy.md`](../../adr/0043-image-audit-strategy.md)
  — Image-Audit-Pattern (M6-Welle-1); Vorbild fuer K8s-
  Image-Tag-Pin-Strategie.
- [`../../../user/safe-007-008-sim-prod-input-validation.md`](../../../user/safe-007-008-sim-prod-input-validation.md)
  — Sim/Prod-Marker-Substanz; gilt auch fuer K8s-
  Deployment (Marker-Surfaces mitschleppen).
