# ADR 0045 — HTTP-API-Request-Body-Strict-Validation (M6 Welle 5b)

**Status:** Accepted — gezogen 2026-06-08 mit M6-Welle-7-C1
(dieser Commit; M6-Closure-Welle). Provisional-Schritt
2026-06-07 mit M6-Welle-5b-C1 (produktiv-belegt durch
`_BaseRequest`-Mixin + `RunCreateRequest`-Konsolidierung +
11 Integration-Smokes; `make ci`/`make fullbuild` cache-frei
gruen).
**Datum:** 2026-06-07
**Status geaendert am:** 2026-06-07 — Erstwurf `Proposed` →
`Provisional` nach Code-Beleg; 2026-06-08 — `Provisional →
Accepted` (M6-Welle-7-Closure).
**Bezug:**

- [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
  — Lifecycle- und Supersedes-Pflichten, auf denen die
  Schaerfungs-ohne-Supersedes-Form aufbaut.
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) —
  Schaerfung-ohne-Supersedes-Pattern (Form-Vorbild fuer
  diese ADR).
- [`ADR 0037`](0037-http-api-surface-pattern.md) — Ziel-ADR
  der Schaerfung; bleibt unveraendert `Accepted`.
- [`ADR 0028`](0028-link-maintenance-accepted-adr-bezug.md)
  — Link-Maintenance-Pattern fuer den ADR-Index-Update an
  der ADR-0037-Zeile.

---

## 1. Kontext

ADR 0037 (HTTP-API-Surface-Pattern, `Accepted` 2026-06-04)
verankert die REST + WebSocket-Surface fuer
`GG-API-001..004`. Drei Decisions sind dort final: §2.1
Action-Body-Vertrag (`POST /runs/{id}/control` mit
`{"action": "..."}`-Body), §2.2 kein separater
`UICommandPort`-Slot, §2.3 Roadmap-Typo `DRG-002`-Verwerfung.

Die Pydantic-Schema-Substanz wird in ADR 0037 §2.1 nur
**implizit** beruehrt: das Code-Beispiel zeigt
`ControlRequest` als Pydantic-`BaseModel`, der „Action vor
TickLoop-Call" validiert. Welcher Pydantic-Mode (Default vs
Strict, `extra`-Verhalten) gilt, ist nicht festgelegt — die
bestehende Implementation laeuft im Default-Pydantic-Mode,
weil das die Pydantic-Default-Position ist.

Stand `src/grid_gym/adapters/driving/http_api/_schemas.py`:
kein Request-Modell setzt `model_config` — alle Request-Bodies
laufen unter Pydantic-Default-Mode. Das ist fuer **Response-
Bodies** akzeptabel (Server kontrolliert die Felder), aber
fuer **Request-Bodies** problematisch gegen `GG-SAFE-008`
MUSS:

- **Extra-Felder werden silent ignoriert** (Default-Pydantic-
  `extra="ignore"`). Ein Client kann ein
  `POST /runs/{id}/control`-Body mit `{"action": "pause",
  "unknown_key": "evil_payload"}` schicken — der unknown_key
  wird verworfen ohne Diagnose. Bei Typo (`{"actoin":
  "pause"}`) gibt es einen anderen 422 (`field required`),
  aber das ist Glueck — kein Vertrag.
- **Type-Coercion ist aktiv** (Default-Pydantic-`strict=False`).
  Ein Body `{"seed": "42"}` (String statt Int) wird silent
  zu `42` konvertiert; `{"seed": "42abc"}` wird mit klarem
  Fehler abgelehnt. Asymmetrische Strenge — was strikter sein
  sollte, ist es nicht.

`GG-SAFE-008` MUSS-Akzeptanz
([Lastenheft §20 GG-SAFE-008](../../../spec/lastenheft.md#gg-safe-008),
Z. 1404-1408): „REST-, WebSocket- und alle implementierten
Adapter-Eingaben werden gegen Schema, Wertebereiche und
Zielressourcen validiert, bevor sie in den Simulationskern
gelangen." Die Default-Pydantic-Mode-Substanz erfuellt „gegen
Schema" nur mit Schwaechen: Extra-Felder UND Type-Coercion
verstecken Fehler in einer Schicht, deren Aufgabe es ist, sie
zu fangen.

**ADR-0011-Constraint:** ADR 0037 ist `Accepted`; per
[ADR 0006](0006-adr-lifecycle-superseding-and-process-corrections.md)
§3 + ADR 0011 §2 sind direkte Edits am Accepted-Text
verboten. Die Schaerfung muss als **separate** ADR `B` mit
eigenem Header geschrieben werden; ADR 0037 bleibt
unveraendert; der ADR-Index wird per ADR 0028-Pattern
gepflegt.

ADR 0045 schliesst die Luecke: Pydantic-Strict-Mode +
`extra="forbid"` werden zur **Pflicht-Substanz fuer
Request-Bodies** an REST-Endpunkten gemacht. Response-Bodies
bleiben unveraendert (siehe §4 Out-of-Scope).

---

## 2. Entscheidung

ADR 0045 fixiert vier orthogonale Punkte:

### §2.1 Pflicht-Substanz fuer Request-Bodies

Jeder Pydantic-`BaseModel`, der als FastAPI-Request-Body an
einem REST-Endpunkt unter `src/grid_gym/adapters/driving/
http_api/` konsumiert wird, MUSS folgende `model_config`-
Substanz haben:

```python
from pydantic import BaseModel, ConfigDict

class _BaseRequest(BaseModel):
    """Gemeinsame Strict-Mode-Basis fuer alle REST-Request-
    Bodies (ADR 0045 §2.1)."""

    model_config = ConfigDict(
        strict=True,
        extra="forbid",
    )
```

- **`strict=True`**: keine Type-Coercion. Pydantic akzeptiert
  nur Inputs, die im exakten Ziel-Typ angeliefert werden
  (Int kommt als JSON-Number, String kommt als JSON-String,
  Bool kommt als JSON-Bool). Ein Body mit `{"seed": "42"}`
  wird mit `Input should be a valid integer [type=int_type,
  input_value='42', input_type=str]` rejected.
- **`extra="forbid"`**: unbekannte Felder fuehren zu 422 mit
  `Extra inputs are not permitted [type=extra_forbidden]`.
  Tippfehler im Client (z. B. `"actoin"` statt `"action"`)
  werden sichtbar statt silent verworfen.

Konkrete Anwendung: `_BaseRequest` lebt in
`src/grid_gym/adapters/driving/http_api/_schemas.py`. Alle
drei aktuellen Request-Modelle erben:

- `ControlRequest` (`POST /runs/{id}/control`).
- `FaultInjectionRequest` (`POST /runs/{id}/faults`).
- `RunCreateRequest` (`POST /runs`) — siehe §2.4 zur
  Konsolidierung des Modells aus `app.py` nach
  `_schemas.py`, damit die Strict-Mode-Substanz uniform gilt.

Pattern-Verbot: per-Endpunkt-Bypass via
`model_config = ConfigDict(strict=False)` oder
`extra="allow"` an einem Request-Body ist **ADR-Bruch**.
Wenn ein konkreter Endpunkt Strict-Mode strukturell nicht
einhalten kann (z. B. wegen externer Vertrags-Anforderung),
muss eine ADR-Schaerfung an ADR 0045 §2.1 die Ausnahme
explizit zulassen (Pattern analog ADR 0011: separate
Schaerfungs-ADR ueber ADR 0045).

### §2.2 Response-Bodies bleiben unveraendert

Response-Bodies sind NICHT betroffen — unabhaengig davon, in
welchem Modul sie liegen:

- In `_schemas.py`: `RunDetailResponse`, `RunStatusResponse`,
  `ControlResponse`, `SnapshotResponse`,
  `FaultInjectionResponse`, `AlarmDto`/`AlarmsResponse`,
  `DeviceStateEntry`/`DevicesResponse`, `ErrorResponse`.
- In `app.py`: `HealthResponse`. `RunCreateResponse` lebt
  ebenfalls in `app.py` und wandert per §2.4 nach
  `_schemas.py` — sein Strict-Mode-Status aendert sich
  durch den Umzug NICHT (er bleibt Default-Mode, weil
  Response).

Default-Pydantic-Mode bleibt fuer Response-Bodies, weil:

- Der Server kontrolliert die Felder (kein externer Eingang).
- Strict-Mode an Response-Bodies bricht bei spaeteren Schema-
  Erweiterungen (neue Felder in Response-Modellen wuerden
  Tests brechen, die Snapshots des alten Schemas halten).
- Lastenheft `GG-SAFE-008` adressiert Eingaben („bevor sie
  in den Simulationskern gelangen"), nicht Ausgaben.

§2.2 fixiert das explizit, damit kuenftige Reviews nicht
versehentlich Response-Bodies in den Strict-Mode ziehen.

### §2.3 WebSocket-Subscribe-Inputs

WebSocket-Endpunkte unter `WS /runs/{run_id}/telemetry` und
`WS /runs/{run_id}/alarms-stream` sind aktuell
**Subscribe-only**: die Server-Side liest keine Client-
Payloads in den Kern (siehe
`src/grid_gym/adapters/driving/http_api/_runs_action_router.py`
— beide WS-Handler iterieren ueber `TelemetryStreamPort.
subscribe` bzw. `AlarmStreamPort.subscribe`, ohne
`websocket.receive_*` zu konsumieren).

ADR 0045 schreibt deshalb fuer WebSocket-Inputs **keinen**
Pydantic-Strict-Mode-Vertrag vor. Wenn ein spaeterer Client-
WS-Payload-Pfad eingefuehrt wird (z. B. Bidi-Steuerung), muss
die neue Surface separat audited und ADR 0045 entsprechend
geschaerft werden.

`run_id`-Path-Parameter-Validation an WebSocket-Endpoints
ist gesondert: sie liegt auf der FastAPI-Routing-Surface,
nicht auf der Pydantic-Schema-Surface, und wird von ADR 0045
nicht verankert (siehe §7 Out-of-Scope).

### §2.4 RunCreateRequest-Konsolidierung

`RunCreateRequest` und `RunCreateResponse` sind heute lokal
in `src/grid_gym/adapters/driving/http_api/app.py:139-160`
definiert, waehrend die uebrigen Request-/Response-Schemas
(`ControlRequest`, `FaultInjectionRequest`,
`RunDetailResponse`, etc.) in `_schemas.py` konsolidiert
sind. Diese Asymmetrie ist historisch gewachsen und ohne
inhaltliche Begruendung.

Die Konsolidierung verschiebt beide Modelle nach
`_schemas.py`:

```python
# In _schemas.py (Field / BaseModel / RunState bereits dort
# importiert; _BaseRequest siehe §2.1):
class RunCreateRequest(_BaseRequest):
    """POST /runs Request-Body."""

    scenario_hash: str = Field(..., min_length=64, max_length=64)
    seed: int = Field(..., ge=0, le=2**32 - 1)
    tick_ms: int = Field(..., gt=0)


class RunCreateResponse(BaseModel):
    """POST /runs Response-Body."""

    run_id: str = Field(...)
    state: RunState = Field(...)
```

`app.py` importiert anschliessend beide Modelle aus
`_schemas` statt sie lokal zu definieren. Damit:

- Strict-Mode-Vertrag (§2.1) wirkt auch auf `POST /runs` —
  ohne Konsolidierung wuerde `RunCreateRequest` der einzige
  Default-Mode-Request bleiben (Vertrags-Loch).
- Alle Request-/Response-Schemas leben uniform in
  `_schemas.py`.
- `app.py` bleibt schlank und enthaelt nur App-Konstruktion
  + Endpoint-Wiring, keine Schema-Definitionen.

Die Konsolidierung ist nicht optional: ohne sie ist
ADR 0045 §2.1 fuer `RunCreateRequest` nicht erfuellt
(Default-Pydantic-Mode bliebe wirksam, weil das Modell den
`_BaseRequest`-Mixin nicht erbt).

---

## 3. Begruendung

- **[`GG-SAFE-008`](../../../spec/lastenheft.md#gg-safe-008)-MUSS-Akzeptanz erfuellen.** Lastenheft
  Z. 1404-1408 verlangt Validation „gegen Schema,
  Wertebereiche und Zielressourcen, bevor Eingaben in den
  Simulationskern gelangen". Default-Pydantic-Mode mit
  silent extra-Field-Drop und Type-Coercion erfuellt
  „gegen Schema" nur mit Schwaechen; Strict-Mode +
  extra-forbid macht den Vertrag verbindlich.
- **Schwester-Strenge zur Quality-Pipeline-Substanz** (vgl.
  `GG-SAFE-001..004`-Audit unter
  `docs/user/safe-001-004-quality-pipeline.md`): dort werden
  Quality-Statuswerte deterministisch emittiert; ADR 0045
  liefert die analoge Strenge an der Eingangs-Schicht — kein
  silent-Drop, kein silent-Convert.
- **Tippfehler-Sichtbarkeit.** Ein Client, der
  `{"actoin": "pause"}` schickt (Tippfehler), bekommt
  unter Default-Mode entweder einen `field required`-
  Fehler (Glueck) oder eine missverstaendliche Antwort
  („Action default-validiert"; aber `action` fehlt
  tatsaechlich, der unknown_key wurde verworfen). Mit
  `extra="forbid"` ist die Diagnose direkt: „Extra inputs
  are not permitted: actoin". Praeziserer Diagnose-Pfad fuer
  Client-Entwickler.
- **Schaerfung ohne Supersedes (ADR 0011-Pattern).** ADR
  0037 §2.1 + §2.2 + §2.3 bleiben textlich unveraendert;
  nur die implizite Pydantic-Mode-Substanz wird additiv
  geschaerft. ADR 0037-Substanz bleibt in Kraft, ADR 0045
  liegt parallel. Pattern-Vorbild ist ADR 0044 (Schaerfung
  zu ADR 0043 §2.2) — gleiches Strukturmuster: separate
  ADR-Datei, Bezug-Zeile, ADR-Index-Update, A bleibt
  `Accepted`.
- **Zentraler Mixin statt per-Endpunkt-Konfiguration.**
  Strict-Mode + extra-forbid als gemeinsame Basis-Klasse
  `_BaseRequest` ist kohaerenter als per-Model-Repetition:
  ein zentraler Vertrags-Anker, drei (spaeter ggf. mehr)
  erbende Konkrete. Vermeidet Drift, wenn neue Request-
  Bodies hinzukommen.

---

## 4. Reichweite

- ADR 0037 bleibt textlich unveraendert (`Accepted`-
  Immutability per ADR 0006 §3 + ADR 0011 §2). ADR 0045 ist
  eine parallele Schwester-ADR.
- `src/grid_gym/adapters/driving/http_api/_schemas.py`
  enthaelt den NEU `_BaseRequest`-Mixin sowie die
  konsolidierten `RunCreateRequest`/`RunCreateResponse`.
  Alle Request-Modelle (`ControlRequest`,
  `FaultInjectionRequest`, `RunCreateRequest`) erben
  `_BaseRequest`.
- `src/grid_gym/adapters/driving/http_api/app.py` importiert
  `RunCreateRequest`/`RunCreateResponse` aus `_schemas.py`
  statt sie lokal zu definieren.
- Response-Modelle, WebSocket-Endpoints, FastAPI-Routing-
  Surface, Snapshot-/Domain-Schemas bleiben **unangetastet**.
- ADR-Index Aktive-ADRs-Tabelle ADR-0037-Zeile bekommt
  „Schaerfungen / Folge-ADRs"-Spalte um ADR-0045-Eintrag
  (Index-Pflege per ADR 0011 §4); ADR-0045-Zeile NEU
  angelegt.
- Integration-Smokes unter `tests/integration/test_m6_welle_
  5b_safe_007_008_smoke.py` belegen die Vertrags-Substanz:
  - `test_safe_008_rest_extra_field_rejected` (extra-forbid
    Beleg).
  - `test_safe_008_rest_type_coercion_rejected` (Strict-Mode
    Beleg).
- Bestehende Tests in `tests/unit/` und `tests/integration/`,
  die `RunCreateRequest`/`ControlRequest`/`FaultInjectionRequest`
  mit Type-Coercion-Eingaben (`seed="42"`) oder extra-Feldern
  konstruieren, muessen im selben Commit, in dem der
  `_BaseRequest`-Mixin landet, an den Strict-Vertrag
  ausgerichtet werden (Pflicht-Inline-Fix).

---

## 5. Lieferung

Lieferplan, Commit-Hashes und Verifikations-Gates fuer die
produktive Implementation der §2-Entscheidung leben in der
zugehoerigen Slice-Doc
[`M6-welle-5b.md`](../planning/done/M6-welle-5b.md).
Status-Pfad (`Proposed → Provisional → Accepted`): siehe
Status-Header dieser ADR.

---

## 6. Konsequenzen

- **Positiv:** `GG-SAFE-008`-MUSS-Akzeptanz fuer REST-
  Request-Bodies wird verbindlich („gegen Schema" mit
  exakter Type- und Field-Strenge). Audit-Trail durch
  zentralen `_BaseRequest`-Mixin.
- **Positiv:** Tippfehler-Diagnose ist eindeutig (extra-
  forbid 422-Fehler statt silent-Drop). Client-Entwicklung
  wird einfacher zu debuggen.
- **Positiv:** Schaerfung ohne Supersedes — ADR 0037-
  Substanz bleibt textlich unangetastet. Pattern-Konsistenz
  mit ADR 0011 + ADR 0044.
- **Positiv:** `_BaseRequest`-Mixin ist Erweiterungspunkt
  fuer zukuenftige Request-Modelle; neue Request-Bodies
  erben automatisch den Vertrag.
- **Negativ:** Bestehende Tests, die Pydantic-Default-
  Mode-Coercion ausnutzen (z. B. `RunCreateRequest(seed=
  "42", ...)` in Unit-Tests), brechen. Diese ADR verlangt,
  dass solche Tests im selben Commit angeglichen werden,
  in dem der Strict-Mode-Mixin landet (Pflicht-Inline-Fix).
- **Negativ:** Strict-Mode schliesst Client-Konvenienz aus
  (z. B. einen `tick_ms` als JSON-String `"100"` zu schicken
  funktioniert nicht mehr). Akzeptabel, weil
  `GG-SAFE-008`-Vertragsstrenge ueber Client-Convenience
  geht.
- **Neutral:** Response-Bodies bleiben unveraendert. Drift-
  Risiko gegen spaetere Schema-Erweiterungen wird vermieden.
- **Neutral:** WebSocket-Subscribe-Inputs bleiben out-of-
  scope (bestehende Telemetry-/Alarm-WS-Endpunkte sind
  Subscribe-only; keine Client-Payload-Konsumption am Kern).
- **Neutral:** `run_id`-Path-Parameter-Validation bleibt
  out-of-scope (FastAPI-Routing-Surface, nicht Pydantic-
  Schema-Surface).

---

## 7. Nicht Gegenstand dieser ADR

- **Aufhebung von ADR 0037 §2.1/§2.2/§2.3.** Action-Body-
  Vertrag, kein-UICommandPort-Decision, DRG-002-Verwerfung
  bleiben unveraendert.
- **Strict-Mode an Response-Bodies.** Explizit ausgeklammert
  in §2.2.
- **WebSocket-Client-Payload-Validation.** WebSocket-
  Endpunkte sind Subscribe-only; explizit ausgeklammert
  in §2.3. Wenn ein spaeterer Bidi-Pfad eingefuehrt wird,
  ist eine ADR-Schaerfung an ADR 0045 noetig.
- **`run_id`-UUID-Validation an Path-Parameters.** FastAPI-
  Routing-Surface, nicht Pydantic-Schema-Surface; ADR 0045
  beruehrt das nicht.
- **Adapter-Side-Input-Validation** (Protocol-Adapter-
  Reads von externen Geraeten). ADR 0045 deckt nur die
  Driving-Side (REST-Request-Bodies); die Driven-Side
  bleibt orthogonal.
- **Custom Pydantic-Validators** (z. B. Cross-Field-
  Validation per `@model_validator` in
  `FaultInjectionRequest`). Custom-Validators sind orthogonal
  zu `model_config`-Mode; ADR 0045 beruehrt sie nicht.
- **Pydantic-Version-Pin-Bump.** `pydantic>=2.13` (siehe
  `pyproject.toml`) bleibt unangetastet; `strict=True` +
  `extra="forbid"` werden seit Pydantic 2.0 unterstuetzt.
- **Vendor-spezifische Schema-Formate** (z. B. JSON-Schema-
  Draft-2020-12). Pydantic-erzeugte OpenAPI-Schemata bleiben
  Pydantic-natives Format.
- **Multi-Layer-Validation-Strategie** (Schema → Wertebereich
  → Zielressource). ADR 0045 deckt nur Schema-Layer (Type
  + Field-Set); Wertebereiche bleiben Per-Endpoint-
  Pydantic-`Field`-Constraints (z. B. `Field(..., ge=0,
  le=2**32 - 1)`); Zielressourcen-Validation bleibt
  Endpoint-Logik (z. B. `_healthcheck_router._require_run_
  or_404`-Helper).
