# Demo-Compose-Hardening — Host-Port-Bind

**Quelle:** M6-Welle-5c (SOLLTE-Items + IP/Netz-
Beschraenkung;
[`../plan/planning/done/M6-welle-5c.md`](../plan/planning/done-archive/M6-welle-5c.md)).
**Stand:** 2026-06-07.

Dieses Dokument richtet sich an Maintainer und Demo-Operator,
die `deploy/compose.yml` lokal oder im Lab betreiben. Es
beschreibt den Host-Port-Bind des `api`-Services und den
ENV-Override-Pfad fuer abweichende Demo-Netzwerk-Topologien.

---

## Hintergrund

`deploy/compose.yml` liefert das kanonische Demo-Stack-Profil
(`make demo` / `make runtime`). Der `api`-Service mappt
intern `:8080` auf einen Host-Port und ist damit von ausserhalb
des Compose-Networks erreichbar.

Die `carveouts.md §2.7`-Auflage (Permanent-Out-of-Scope-
Block) verankert die IP-/Netz-Beschraenkung als separate
Auflagen-Schicht ueber dem Lastenheft (es gibt **keinen**
einzelnen Lastenheft-ID dafuer). Sinn: das Demo-Stack ist
nicht fuer Multi-User-Zugriff oder offene Lab-Netze gehaertet;
der Bind muss per Default die Reichweite auf den Maintainer-
Host beschraenken.

`GG-SAFE-008` (REST-Input-Validation) ist davon abzugrenzen
— es regelt Eingaben **am Endpoint**, nicht die Erreichbarkeit
des Endpoints. `GG-DEPLOY-011` regelt Offline-Runs (kein
Outbound-Network-Egress), nicht den Inbound-Port-Bind.

---

## Default-Verhalten

`deploy/compose.yml` bindet per Default an **`127.0.0.1`**:

```yaml
services:
  api:
    ports:
      - "${GRID_GYM_DEMO_HOST_BIND:-127.0.0.1}:8000:8080"
```

Ergebnis:

- `curl http://127.0.0.1:8000/health` vom Maintainer-Host
  funktioniert.
- `curl http://<host-lan-ip>:8000/health` von einem anderen
  Host im LAN trifft den Endpoint **nicht** — das Docker-
  Daemon-Bind ist auf das Loopback-Interface beschraenkt.

Damit ist das Demo-Stack per Default nicht ueber LAN/WAN
erreichbar, auch wenn das Host-Firewall-Regelwerk
fehlkonfiguriert oder offen ist.

## ENV-Override fuer Lab-/Remote-Demo

Die Compose-`${VAR:-default}`-Interpolation erlaubt einen
expliziten Bind-Override per Environment-Variable, ohne
`compose.yml` zu editieren:

```bash
# Lab-Setup mit einer dedizierten Lab-LAN-IP:
export GRID_GYM_DEMO_HOST_BIND=10.0.50.42
make demo

# Oder fuer einen Remote-Demo-Stack ueber alle Interfaces
# (NUR in isolierten Lab-Netzen — siehe Risiko-Warnung):
export GRID_GYM_DEMO_HOST_BIND=0.0.0.0
make demo
```

Reset auf den sicheren Default:

```bash
unset GRID_GYM_DEMO_HOST_BIND
make demo
```

## Risiko-Warnung

Wer `GRID_GYM_DEMO_HOST_BIND=0.0.0.0` setzt, **muss** sich
bewusst sein:

- Das Demo-Stack hat **keine Auth** im UI-Layer
  (`carveouts.md §2.7` „Multi-User + Auth im UI-Layer"
  permanent Out-of-Scope).
- Das Demo-Stack ist **nur Simulation** und nicht fuer
  produktive Anlagensteuerung freigegeben (`GG-SAFE-007`;
  siehe [`safe-007-008-sim-prod-input-validation.md`](safe-007-008-sim-prod-input-validation.md)).
- REST-Eingaben sind via `GG-SAFE-008` strict-validiert
  (Pydantic v2 mit `strict=True` + `extra="forbid"`), aber
  WebSocket- und UI-Endpunkte sind unauthentifiziert.

Konsequenz: ein `0.0.0.0`-Bind ist **nur** in einem
abgegrenzten Lab-Netz akzeptabel, in dem entweder eine
externe Firewall-/Reverse-Proxy-Schicht das Auth-/Egress-
Loch schliesst oder der gesamte Netzwerksegment vertraut
ist.

## Verifikation

`tests/integration/test_m6_welle_5c_safe_005_006_compose_smoke.py::test_demo_compose_host_bind_defaults_to_loopback`
inspiziert die `deploy/compose.yml`-Quelle und pinnt zwei
Eigenschaften in CI:

1. Die `api`-`ports`-Klausel enthaelt die Substring
   `"127.0.0.1"` als Default-Bind.
2. Die `api`-`ports`-Klausel enthaelt die Substring
   `"GRID_GYM_DEMO_HOST_BIND"` als ENV-Override-Anker.

Falls jemand die Klausel auf `0.0.0.0`-Default zuruecksetzt
oder den ENV-Override entfernt, schlaegt der Smoke an.

---

## Bezug

- [`../plan/planning/in-progress/carveouts.md §2.7`](../plan/planning/in-progress/carveouts.md):
  normative Quelle fuer die IP-/Netz-Beschraenkung
  („separate Auflagen-Schicht, kein einzelner Lastenheft-
  ID").
- [`safe-007-008-sim-prod-input-validation.md`](safe-007-008-sim-prod-input-validation.md):
  `GG-SAFE-007` (Sim/Prod-Marker) + `GG-SAFE-008` (Input-
  Validation am Endpoint).
- [`safe-005-006-fallback-determinism.md`](safe-005-006-fallback-determinism.md):
  `GG-SAFE-005/006` Schwester-Audit der gleichen Welle.
- `Makefile`-Targets `demo` / `runtime` — sie sourcen
  `GRID_GYM_DEMO_HOST_BIND` aus dem Maintainer-Environment
  durch zur Compose-Interpolation.
