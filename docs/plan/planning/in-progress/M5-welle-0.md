# Welle 0 — M5 Slice-Plan-Eroeffnung + Trigger-Triage

**Status:** In Progress — eroeffnet 2026-06-01 nach
M4-Welle-7-Closure (Liefer-Stack `bf23458` Pre-C0a +
`5b2dc24` Pre-C0b + `af97fd7` C0 + `05a1417` C0-Review
+ `d2071f0` C1 + `0c644f0` C2 + `121e255` C3 + `e745f10`
C4a + `72e8357` C4b + `4567222` Closure-Konsistenz-Audit
+ `e9aabd9` Self-Close-Move + `7f5beb8` Pre-C0b mit
README-Front-Matter-Audit + `f4a9ced` NEU ADR 0036
+ `e0c3f66` ADR 0036 §2.5 + Maintainer-Decision-Indication).
Vorabraeumung + Slice-Plan-Eroeffnung fuer M5 (UI + Demo —
`GG-UI-001..009` + `GG-DEMO-001..008`) ist diese
Wellen-Aufgabe. Pattern analog M4-Welle-0
([`../done/M4-welle-0.md`](../done/M4-welle-0.md)).

**Spec-Reife:** Inhaltlich final. Reines Doc-Arbeitspaket
(kein Code-Pfad-Wechsel; Pattern analog
[`../done/welle-0.md`](../done/welle-0.md) (M3-Welle-0)
und [`../done/M4-welle-0.md`](../done/M4-welle-0.md)).
Welle-0-Decision-Liste (§3) sammelt offene Fragen,
entscheidet sie aber nicht — Entscheidungen wandern in
Welle 1 und werden im jeweiligen M5-ADR konkretisiert.
**Bereits vor M5-Welle-0 angelegt:** ADR 0036
(UI-Stack-Wahl) mit Maintainer-Decision-Indication
„Option 1 (HTMX) + Chart.js" (siehe
[`../../adr/0036-ui-stack-choice.md`](../../adr/0036-ui-stack-choice.md)
§2-Header).

---

## 1. Context

M4 ist seit 2026-06-01 mit Welle-7-Closure abgeschlossen
([`../done/M4-results.md`](../done/M4-results.md)). M5 ist
laut [`roadmap.md §3 M5`](roadmap.md) der naechste aktive
Slice mit zwei Sub-Bereichen entlang
[`../../../../spec/lastenheft.md §17 + §24`](../../../../spec/lastenheft.md)
plus Cross-Cutting aus
[`../../../../spec/lastenheft.md §16`](../../../../spec/lastenheft.md):

- **UI** (`GG-UI-001..009`, **sechs MUSS** —
  `GG-UI-001..005` + `GG-UI-009` Datenqualitaet — und
  **drei SOLLTE** — `GG-UI-006..008` Geraete-Grafik /
  Fault-Injection-Form / Simulationszustaende): Web-UI
  nach `docker compose up` lokal, Live-Telemetry,
  Zeitreihen, Replay-Steuerung, Alarme, Datenqualitaet
  visuell unterscheidbar.
- **Demo** (`GG-DEMO-001..008`, **sechs MUSS** —
  `GG-DEMO-001..005` + `GG-DEMO-008` — und **zwei SOLLTE**
  — `GG-DEMO-006` Fault-Injection in Demo + `GG-DEMO-007`
  Agent in Demo): Lokale Demo-Umgebung, Netz + Batterie +
  Live-Telemetry binnen 30s, Replay-Szenario,
  dokumentierte Abnahmereihenfolge.

Plus Cross-Cutting:

- **HTTP-API-Surface** (`GG-API-001..004` aus
  [`../../../../spec/lastenheft.md §16`](../../../../spec/lastenheft.md)
  Kommunikationsschnittstellen): die in M1 angelegte
  Stub-Surface (`POST /runs` + `/health`) wird in M5 zur
  vollen REST + WebSocket vervollstaendigt. **Driving-
  Port-Erweiterung** unter
  [`../../../../spec/architecture.md §4.2`](../../../../spec/architecture.md)
  `GG-AR-PORT-DRV-*`-Familie; nicht zu verwechseln mit
  den Driven-Ports (DRN-007 `DeviceProtocolPort`)
  aus M4.
- **Demo-Pipeline:** `make demo` o. ae. als reproduzier-
  barer Abnahmebefehl (Lastenheft `GG-DEMO-008`).

### 1.1 Welle-0-Resultat-Skizze

- **C0** (dieser Commit): Slice-Doc-Anlage + Welle-0-Auf-
  raeumung (Welle-0-Doc, Welle-0-Decision-Liste, Trigger-
  Drift-Notiz).
- **C1:** M5-Slice-Plan eroeffnen als
  `M5-ui-demo.md`-Dokument unter `in-progress/` (Pattern
  analog M4-Welle-0-C1 mit `M4-protocol-adapters.md`).
  Welle 1..7-Vorbelegung; Lastenheft-Cluster-Mapping;
  Decision-Liste konsolidiert; Out-of-Scope + Risiken
  + Verifikationspfad.
- **C2:** Trigger-Triage (alle aktiven `open/`-Trigger
  re-pruefen; M5-relevante markieren).

### 1.2 Bezug zur Maintainer-Decision-Indication ADR 0036

Vor Welle-0-Eroeffnung wurde die UI-Stack-Frage im
Sondierungs-Gespraech entschieden (Pre-M5-Welle-0-ADR
[`../../adr/0036-ui-stack-choice.md`](../../adr/0036-ui-stack-choice.md)
mit Status `Proposed` + Maintainer-Decision-Indication
2026-06-01):

- **UI-Stack:** Option 1 (FastAPI + HTMX + Jinja2 +
  Chart.js).
- **Charting-Library:** Chart.js (orthogonale Sub-
  Decision).
- **Begruendung:** Architektur-Reinheit + Single-Stack-
  Python + 10 statt 15 A-1-Gates + Welle-Tempo +
  `feedback_docker_only`-Treue ueber UX-Glanz
  priorisiert.
- **Migrationspfad** zu Option 1b (SvelteKit-SPA) oder
  Plotly.js/ECharts in Welle 6+ offen, falls
  Stakeholder-Druck spaeter aufkommt.

Die Decision-Festschreibung erfolgt formal in
M5-Welle-1-ADR-Schaerfung auf `Provisional` (Pattern
analog ADR 0030..0035 in M4).

### 1.3 Existierende Substanz im Repo

Stand 2026-06-01 (M4-Closure):

- **FastAPI** `>=0.136` + **uvicorn[standard]** `>=0.47`
  in `[project] dependencies` seit M1-Welle-7.
- [`src/grid_gym/adapters/driving/http_api/app.py`](../../../../src/grid_gym/adapters/driving/http_api/app.py)
  exportiert `app` mit `/health` + `POST /runs`-Stub.
- **`httpx >=0.27`** als Test-Client.
- **`make openapi-validate`**-Dockerfile-Stage validiert
  `app.openapi()` gegen `openapi-spec-validator` (M1).
- [`deploy/compose.yml`](../../../../deploy/compose.yml)
  als produktiver Compose-File.
- **`GG-AR-COMP-UI`-Slot** in
  [`../../../spec/architecture.md §5`](../../../../spec/architecture.md)
  auf `ui/`-Top-Level-Verzeichnis vorbelegt (das
  Verzeichnis existiert **noch nicht**).
- **5 produktive Geraetemodelle** (`battery`/`pv`/`load`/
  `grid_connection`/`smart_meter`) aus M2 — bereit fuer
  Live-Telemetry.
- **5 produktive Protocol-Adapter** (MQTT/Modbus/OPC-UA/
  DNP3/IEC-61850) aus M4 — bereit fuer Demo-Szenarien
  mit echten Library-Pfaden.

### 1.4 Welle-7-Erbschaft aus M4

Aus [`../done/M4-results.md §5`](../done/M4-results.md):

- **Trigger 009** (IEC-61850-In-Process-Smoke
  Reaktivierung): Pfad A passiv ODER Pfad B als eigener
  Slice (Dockerfile-Multi-Python-Test-Stage). M5-Welle-0-
  Trigger-Triage entscheidet, ob Pfad B in M5 Welle-?
  angegangen wird oder weiter deferred bleibt.
- **Base-Image-Bump** fuer krb5-CVE-Drift seit
  M3-Welle-7-`c61ab0d`: eigener Slice-Trigger in
  M5-Welle-0 oder fruehestmoeglicher Schaerfungs-Welle
  (`make fullbuild` ist pre-existing rot).
- **OTel-Span-Wrap-Pattern** aus M4-Welle-6a — direkt
  reusable nur fuer Driven-Boundaries (das Welle-6a-
  `_protocol_otel_wrap.py`-Composition-Wrapper-Pattern
  wrappt `DeviceProtocolPort.read/write`-Calls).
  HTTP-API und UI sind **Driving-Ports**
  (`GG-AR-PORT-DRV-*`, siehe
  [`../../../../spec/architecture.md §4.2`](../../../../spec/architecture.md)),
  nicht Driven. Driving-Side-Analogon waere
  **FastAPI-Middleware** oder OpenTelemetry-ASGI-
  Instrumentation (`opentelemetry-instrumentation-
  fastapi`), nicht das gleiche Composition-Wrapper-
  Pattern. Welle 3/4 entscheidet, ob OTel-Instrumentation
  der HTTP-API als Driving-Side-Pattern eingezogen wird
  (Folge-Trigger falls relevant).
- **`AC-ADAPTER-LIGHTWEIGHT`-Coverage-Pfad-Filter** aus
  Welle-6b-C3 (Slice-034-F13, `2539574`) — flat-file
  `_protocol_*.py`-Helper unter `adapters/driven/`-Pfad
  ist gegated. Falls M5 cross-Driving-Helper unter
  `adapters/driving/_http_api_*.py` einfuehrt, koennte
  ein analoger Filter-Eintrag in
  `_is_adapter_lightweight_path` noetig werden
  (Welle-?-Folge falls Cross-Driving-Helper auftauchen).
- **GPL-Boundary-Pattern** aus M4-Welle-5b/6b
  (`check_spdx.py` + `AC-IEC61850-GPL-BOUNDARY`): nicht
  M5-relevant (keine GPL-isolierten UI-Komponenten
  vorgesehen mit Maintainer-Decision Option 1 + Chart.js
  — alle MIT/BSD).

---

## 2. Scope

Welle 0 liefert **drei Doc-Items** ueber 3 Commits:

1. **Slice-Doc-Anlage** (dieser Commit C0): M5-Welle-0-
   Doc als Index zur Welle.
2. **M5-Slice-Plan-Eroeffnung** (C1): `M5-ui-demo.md` in
   `in-progress/` mit Welle 0..7-Vorbelegung, Lastenheft-
   Cluster-Mapping, Decision-Liste, Out-of-Scope, Risiken,
   Verifikationspfad. Pattern analog `M4-protocol-
   adapters.md`.
3. **Trigger-Triage** (C2): Welle-0-Decision-Liste +
   Trigger-Drift-Notiz (siehe §3) durch alle aktiven
   `open/`-Trigger durchgehen; M5-relevante markieren;
   `in-progress/README.md`-Aktive-Welle-Block auf Welle 1
   ausrichten.

---

## 3. Architektur-Entscheidungen

### Welle-0-Decision-Liste (offene Fragen)

Welle 0 **entscheidet keine** dieser Fragen — sie sammelt
sie und reicht sie an Welle 1+ weiter, wo sie im jeweiligen
ADR konkretisiert werden:

- **Decision 1 (UI-Stack-Wahl):** ADR 0036 Status
  `Proposed` mit Maintainer-Decision-Indication „Option 1
  (HTMX) + Chart.js". Formale Festschreibung auf
  `Provisional` in M5-Welle-1-ADR-Schaerfung **nach
  HTMX-FastAPI-Smoke-Probe-Run in Welle-1-Pre-C0**
  (Probe verifiziert: FastAPI rendert Jinja2-Template,
  HTMX-Element triggert Server-Call, WS-Push aktualisiert
  Partial — minimal-Pattern fuer Live-Update-Eignung).
- **Decision 2 (UI-Layout-Lokation):** `ui/` als Top-Level-
  Verzeichnis (per Spec-§5-Architektur-Vorbelegung) ODER
  `src/grid_gym/adapters/driving/ui/` (per Hexagonal-
  Architektur-Pattern). Welle-2-Entscheidung im Welle-2-
  Slice-Doc.
- **Decision 3 (WebSocket vs SSE fuer Live-Telemetry):**
  FastAPI `@app.websocket` ist nativ, aber Server-Sent-
  Events (SSE) sind einfacher zu skalieren und Browser-
  Reconnect-tolerant. Welle-3-Entscheidung mit Probe-Run-
  Beleg (Pattern analog M4-Welle-4-OPC-UA-Loop-Thread-
  Sondierung).
- **Decision 4 (Replay-Controls-API-Vertrag):** Welche
  konkrete REST-Surface fuer `start_run`/`pause_run`/
  `resume_run`/`stop_run`/`get_status`? `POST /runs/{id}/
  pause` vs `POST /runs/{id}` mit Action-Field — welcher
  REST-Stil? Welle-1-Entscheidung im HTTP-API-Surface-ADR
  (potenziell ADR 0037).
- **Decision 5 (Demo-Szenario-Inhalt):** Welche
  Geraete-Konfiguration als kanonisches Demo-Szenario
  (`GG-DEMO-002/003`)? Mindestens 1 Netzanschluss + 1
  Batterie; weitere optional. Welle-5-Entscheidung im
  Demo-Pipeline-Slice-Doc.
- **Decision 6 (Demo-Reproduzierbarkeits-Pflicht):**
  `make demo` als Pflicht-Target ODER `python -m
  grid_gym demo`-Module? `GG-DEMO-008` verlangt
  „reproduzierbaren Abnahmebefehl". Welle-5-Entscheidung.
- **Decision 7 (Charting-Library-Final):** Chart.js als
  Maintainer-Indication; Welle-3-Slice-Doc-Final-Decision
  (siehe ADR 0036 §2.5 + §7-Folge-Pflicht). Moegliche
  Upgrades auf Plotly.js/ECharts in Welle 6+/M6.
- **Decision 8 (Bundle-Auslieferungs-Pattern):**
  **Maintainer-Default aus ADR 0036 §2.1: Chart.js
  vendored als Single-File-Static-Asset (~70 KB) ohne
  Build-Tooling.** Welle-2-Slice-Doc bestaetigt diesen
  Default; Re-Eval nur falls Static-Asset-Footprint im
  Welle-2-Probe-Run kippt (z. B. > 500 KB Total-UI-
  Asset-Bundle). Diese Decision ist also degradiert von
  „Wahlfrage" zu „Welle-2-Bestaetigung".
- **Decision 9 (UICommandPort-Separation):**
  [`roadmap.md §3 M5`](roadmap.md) erwaehnt
  „`GG-AR-PORT-DRG-002` (`UICommandPort`, sofern getrennt
  vom HTTP-API)". Frage: separater Port fuer UI-getriebene
  Commands (Replay-Steuerung, Fault-Injection-Form-
  Submit) oder Wiederverwendung der `GG-API-001`-REST-
  Surface? Welle-1-Entscheidung im HTTP-API-Surface-ADR
  (zusammen mit Decision 4 — Replay-Controls-API-
  Vertrag). **Anmerkung:** Roadmap-Suffix
  `GG-AR-PORT-DRG-002` ist ein Typo gegen
  `../../../../spec/architecture.md §4.2`-Namens-Konvention
  `GG-AR-PORT-DRV-*` (Driving). `GG-AR-PORT-DRV-002` ist
  bereits `ScenarioPort`; ein neuer Driving-Port-Slot
  brauchte eine freie Nummer. Roadmap-Bug zu fixen in
  Welle-1-Top-Level-Doku-Sync.
- **Decision 10 (Roadmap-M5-Status-Header):** Aktuell ist
  `roadmap.md §3 M5` mit Header „Vorbelegung" markiert.
  Frage: in Welle-0-C2 auf „In Progress" flippen (analog
  M4-Welle-0-C2-Status-Flip) oder bewusst auf
  „Vorbelegung" belassen bis M5-Welle-1-Code-Lieferung
  (analog ADR-Lifecycle `Proposed → Provisional` nach
  C2-Code-Merge)? Welle-0-C2-Entscheidung, nicht hier.

### Trigger-Drift-Notiz (zur Aufnahme in C2)

Folgende offene Trigger sind potenziell M5-relevant
(in C2-Trigger-Triage zu pruefen):

- **Trigger 004**
  ([`open/004-canonical-encoder-alternative-adr.md`](../open/004-canonical-encoder-alternative-adr.md)):
  Re-Eval auf M5/M6 verschoben in
  M4-Welle-6a-C3; pruefen ob WebSocket-Live-Telemetry-
  Throughput im Demo-Szenario Performance-Druck erzeugt
  und Re-Eval ausloest.
- **Trigger 008** (`open/008-sbom-activation.md`): SBOM-
  Generierung; ggf. M6-Material, aber wenn M5-Closure
  einen Release-Tag braucht, koennte Trigger 008 mit
  M5-Welle-7-Closure aktiviert werden.
- **Trigger 009** (`open/009-iec61850-smoke-
  reactivation.md`): Welle-6b-Erbschaft; Pfad B als
  eigener Slice — entweder M5-Welle-0 oder spaeter.
  Realistisch eher orthogonal zu M5; Triage entscheidet.
- **Trigger Base-Image-Bump (krb5-CVE)**: aktuell als
  M5-Welle-0-Trigger in
  [`../done/M4-results.md §5`](../done/M4-results.md)
  vermerkt, aber **noch nicht als offener Trigger in
  `open/` angelegt**. C2 muss diesen als
  `open/010-base-image-krb5-cve-bump.md` (oder
  aequivalent) anlegen.

---

## 4. Liefer-Reihenfolge (3 Commits)

### C0 — `docs(plan)`: M5-welle-0 Slice-Doc

**Diff:** dieses Dokument + `in-progress/README.md`-
Bestand-Eintrag.

### C1 — `docs(plan)`: M5-Slice-Plan eroeffnen — ui-demo

**Diff:**

- NEU `in-progress/M5-ui-demo.md` (Pattern analog
  `M4-protocol-adapters.md`): Welle 0..7-Vorbelegung,
  Lastenheft-Cluster-Mapping (`GG-UI-001..009` +
  `GG-DEMO-001..008` + `GG-API-001..004` Cross-Cutting),
  Welle-Sub-Slicing-Praeambel (Schwelle: wenn eine Welle
  >300 Zeilen Slice-Doc ODER >5 Commits geplant ist),
  Out-of-Scope (M6-Material wie `GG-SAFE-001..006`,
  Snapshot-v3, RL-Adapter aus M3-Erbschaft), Risiken,
  Verifikationspfad.
- `in-progress/README.md` — Bestand-Eintrag fuer
  `M5-ui-demo.md`.

### C2 — `docs(plan)`: M5-Welle-0 Trigger-Triage

**Diff:**

- Welle-0-Decision-Liste (§3 dieses Dokument) auf C2-
  Stand aktualisiert (sollte unveraendert bleiben, weil
  Welle 0 keine Decisions selbst trifft).
- Trigger-Drift-Notiz produktiv: alle aktiven
  `open/`-Trigger geprueft; M5-relevante mit „Aktivierung
  in M5-Welle-?" markiert; ggf. neue Open-Trigger
  angelegt (z. B. `open/010-base-image-krb5-cve-bump.md`).
- Status-Flip: M5-welle-0 → Done; `in-progress/
  README.md`-Aktive-Welle-Block auf M5-Welle-1 ausgerichtet.

---

## 5. Critical Files

| Datei                                                | Phase | Aktion                                                    |
| ---------------------------------------------------- | ----- | --------------------------------------------------------- |
| `docs/plan/planning/in-progress/M5-welle-0.md`       | C0    | CREATE (dieses Dokument)                                  |
| `docs/plan/planning/in-progress/M5-ui-demo.md`       | C1    | CREATE (M5-Slice-Plan; Welle 0..7-Vorbelegung)            |
| `docs/plan/planning/in-progress/README.md`           | C0/C1 | EDIT (Bestand-Eintraege + Aktive-Welle-Block)             |
| `docs/plan/planning/in-progress/roadmap.md`          | C2    | EDIT (M5-Status-Header auf In Progress)                   |
| `docs/plan/planning/open/010-base-image-krb5-cve-bump.md` | C2 | CREATE (bedingt — falls C2-Triage entscheidet, dass Trigger explizit angelegt wird) |
| `docs/plan/planning/open/README.md`                  | C2    | EDIT (bedingt — NEU 010-Trigger-Eintrag, nur wenn Datei oben angelegt) |

---

## 6. Verifikationspfad

**Welle-0-DoD:**

1. `M5-welle-0.md` produktiv mit §1-§8.
2. `M5-ui-demo.md` produktiv mit Welle 0..7-Vorbelegung
   + Lastenheft-Cluster-Mapping + Decision-Liste +
   Out-of-Scope + Risiken + Verifikationspfad.
3. `in-progress/README.md`-Bestand-Tabelle hat
   `M5-welle-0.md` + `M5-ui-demo.md` als Eintraege.
4. `in-progress/README.md`-Aktive-Welle-Block auf
   M5-Welle-1 ausgerichtet.
5. `roadmap.md §3 M5`-Header gemaess **Decision 10**
   (§3 Welle-0-Decision-Liste) — entweder auf
   `In Progress` flippen (analog M4-Welle-0-C2-
   Status-Flip-Pattern) oder bewusst auf `Vorbelegung`
   belassen bis M5-Welle-1-Code-Lieferung. C2-
   Entscheidungspunkt; in §3 als Decision 10 verankert.
6. Welle-0-Trigger-Triage durchgefuehrt; M5-relevante
   Trigger markiert; ggf. NEU
   `open/010-base-image-krb5-cve-bump.md`.
7. `make docs-check` cache-frei gruen.

**Welle-0-Gate:** `make docs-check` cache-frei gruen.
`make gates` weiter gruen (Welle 0 hat kein Code-Diff).

---

## 7. Risiken

- **M5-Scope-Praeambel-Drift:** UI-Pflicht (`GG-UI-001..009`)
  + Demo-Pflicht (`GG-DEMO-001..008`) + HTTP-API-Surface-
  Vervollstaendigung (`GG-API-001..004`) sind 3 Sub-
  Bereiche, die in M3-Multi-Sub-Bereich-Pattern (Faults +
  Multi-Agent + Observability) gut funktioniert haben.
  Welle-Plan in C1 muss klar zwischen UI-Foundation
  (Welle 2), Live-Telemetry (Welle 3) und Demo-Pipeline
  (Welle 5) trennen.
- **HTTP-API-Surface-vs-UI-Pflicht-Konflikt:** Welle 1
  liefert die volle REST + WebSocket-Surface; Welle 2
  liefert UI-Layout, das die Surface konsumiert.
  Reihenfolge muss in C1 streng vorgegeben werden, sonst
  bricht die Welle-1-DoD.
- **Welle-Sub-Slicing-Druck:** falls Welle 2 (UI-
  Foundation) zu gross wird (HTMX-Setup + Routing + Test-
  Pattern + Chart.js-Vendoring + Quality-Marker-Pattern
  + ...), kann sie in 2a/2b sub-geslict werden (Pattern
  analog M4-Welle-5a/5b).
- **Chart.js-Live-Streaming-Pattern unerprobt:** WebSocket-
  Push + Chart.js-`update()`-Frequenz ist nicht im Repo
  vorab verprobt. Welle-3-Probe-Run muss das vor C2-
  Implementation pruefen (Pattern analog M4-Welle-5a-C1-
  Probe-Run fuer nfm-dnp3-Wire-Compat).
- **Base-Image-Bump-Verzoegerung:** `make fullbuild`
  bleibt rot, solange krb5-CVE-Drift nicht adressiert
  wird. Welle-Plan muss klarstellen, dass `make gates`
  (10 A-1-Gates) das harte Welle-Closure-Gate bleibt;
  `make fullbuild` ist M5-Welle-?-oder-spaeter-Material.

---

## 8. Wandert nach

- Bei C2-Closure (Welle-0-Done): `M5-welle-0.md` bleibt
  vorerst in `in-progress/` (Pattern analog
  `M4-welle-0.md`, das mit M4-Welle-1-Pre-C0
  Self-Close-Move `556ae9f` gemoved wurde). Self-Close-
  Move folgt als M5-Welle-1-Pre-C0.
- `M5-ui-demo.md` bleibt in `in-progress/` bis
  M5-Welle-7-Closure (analog `M4-protocol-adapters.md`).
- Welle 1 (HTTP-API-Surface + UI-Stack-Decision-
  Festschreibung) als naechster aktiver Schritt mit
  ADR 0036-Schaerfung auf `Provisional` und ggf. NEU
  ADR 0037 fuer HTTP-API-Surface (Decision 4).

---

## References

- [`../done/M4-welle-0.md`](../done/M4-welle-0.md) —
  Pattern-Praezedenz fuer Welle-0-Slice-Doc-Struktur.
- [`../done/M4-results.md`](../done/M4-results.md) §5 —
  Welle-7-Erbschaft + M5-naechster-Schritt-Verankerung.
- [`../../adr/0036-ui-stack-choice.md`](../../adr/0036-ui-stack-choice.md)
  — Pre-M5-Welle-0-Sondierungs-ADR (UI-Stack-Wahl mit
  Maintainer-Decision-Indication „Option 1 + Chart.js").
- [`../../../spec/lastenheft.md §17 + §24`](../../../../spec/lastenheft.md)
  — UI-Pflicht + Demo-System.
- [`../../../spec/architecture.md §5`](../../../../spec/architecture.md)
  — `GG-AR-COMP-UI`-Slot in `ui/`-Top-Level-Verzeichnis;
  `GG-AR-COMP-API` in `adapters/driving/http_api`.
- [`roadmap.md §3 M5`](roadmap.md) — M5-Vorbelegung
  (Lieferziel, Lastenheft-IDs, Architekturartefakte,
  DoD-Checkliste).
