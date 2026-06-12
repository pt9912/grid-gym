# Abnahme-CLI (`make accept`, `GG-MVP-003`)

**Status:** Produktiv ab M7-Welle-2 (2026-06-10).
**Bezug:**
[`spec/lastenheft.md §3 GG-MVP-003`](../../spec/lastenheft.md)
(Z. 138-144),
[`docs/plan/adr/0045-http-api-request-strict-validation.md`](../plan/adr/0045-http-api-request-strict-validation.md)
(Pydantic-Strict-Vorbild),
[`docs/user/gg-demo-008-abnahme.md`](gg-demo-008-abnahme.md)
(manuelle Demo-Reihenfolge — Abgrenzung siehe unten).

Diese Doku beschreibt den **automatisierten** MVP-Abnahmepfad:
ein einziger Befehl fuehrt deterministische Replay-Pruefung,
Szenario-Validierung und Demo-Healthcheck aus und liefert einen
**maschinenlesbaren** JSON-Status (`GG-MVP-003`-Akzeptanz).

## Aufruf

```bash
make demo && make accept
```

- `make demo` startet den Demo-Stack (Compose-up + Postgres + OTel +
  API; bind auf `http://localhost:8000`).
- `make accept` laeuft auf dem Host (`uv run python tools/accept.py`),
  fuehrt die drei Sub-Pruefungen und schreibt den `AbnahmeReport` als
  **einziges** JSON-Objekt auf stdout.

**Reihenfolge ist Pflicht:** Step C (Healthcheck) pollt das laufende
Stack via `GET /ready`. Der Aufrufer startet den Stack (Decision D-7) —
`make accept` pollt nur. Ohne laufenden Stack ist Step C ein
deterministisches `fail` (kein Tool-Error).

Nicht-Default-Host-Bind:

```bash
uv run python tools/accept.py --ready-url http://127.0.0.1:9000/ready
```

### stdout ist JSON-only

stdout traegt **ausschliesslich** das `AbnahmeReport`-JSON. uv-Sync-
Banner, Logs und Tracebacks gehen nach stderr. CI-Consumer parsen
daher ohne Vorfilter:

```bash
make demo
make accept | jq '.overall_status'      # "pass" | "fail"
make accept | jq '.checks.replay_determinism'
```

## Die drei Sub-Pruefungen

Die Sub-Steps laufen **sequenziell A → B → C ohne fail-fast** — ein
Sub-Step-Fail bricht den Lauf nicht ab, der CLI aggregiert alle drei
Status. Alle drei Entries sind im JSON **immer** praesent.

1. **Step A — Szenario-Validierung.** Laedt
   `deploy/scenarios/gg-demo.yaml` (`grid_gym.scenario_yaml.read_scenario_yaml`
   + Core-`load_scenario`) und vergleicht den
   `LoadedScenario.scenario_hash` gegen `EXPECTED_DEMO_SCENARIO_HASH`.
2. **Step B — Deterministischer Replay.** Faehrt das Demo-Szenario
   **zweimal** headless mit gleichem Seed (produktiver
   `build_tick_loop` + Fault-Composition aus `scenario.faults` +
   `scenario.agents`) ueber `MIN_DETERMINISM_TICKS` (= 100) Ticks und
   prueft zwei Eigenschaften:
   - **Determinismus:** beide Telemetry-Streams sind via `diff_replay`
     leer (bzw. nur `VOLATIL`).
   - **Referenz-Treue:** der Stream-Hash entspricht
     `EXPECTED_DEMO_TELEMETRY_STREAM_HASH`.

   **Semantik des Referenz-Streams:** der gepinte Stream ist die
   **deterministische Projektion** des Demo-Verhaltens (Agents +
   Faults + LoadOverlays an; Alarm-UUID/Run-Repository aus, weil
   `uuid4()`-Alarm-IDs nicht reproduzierbar sind). Es ist **kein**
   Byte-Abzug des produktiven `uuid4`-Demo-Laufs.
3. **Step C — Demo-Healthcheck.** Pollt `GET /ready` (Three-State-
   Endpoint) und erwartet HTTP 200 + Top-Level `status == "healthy"`.
   Step C haengt am laufenden Stack, nicht am Szenario; er laeuft
   daher auch dann, wenn Step A/B fehlschlagen.

Step B konsumiert das in Step A geladene `Scenario`-Objekt. Faellt
Step A, fuehrt Step B keinen Replay aus, sondern wird mit
`status="fail"` + `reason="dependency: scenario load failed …"`
aufgenommen (alle drei Entries bleiben praesent).

## JSON-Schema-Vertrag

Der `AbnahmeReport` ist ein Pydantic-`strict`+`extra="forbid"`-Modell
(Vorbild [`ADR 0045`](../plan/adr/0045-http-api-request-strict-validation.md)). Happy-Path (ohne `reason`):

```json
{
  "schema_version": "1",
  "overall_status": "pass",
  "checks": {
    "scenario_validation": {"status": "pass", "scenario_hash": "<sha256>"},
    "replay_determinism": {"status": "pass", "diff_count": 0, "volatile_only": true},
    "demo_healthcheck": {"status": "pass", "endpoint": "/ready", "ready_payload": {"status": "healthy", "...": "..."}}
  }
}
```

- `overall_status` ist **binaer** (`"pass"`/`"fail"`) — der Tri-State
  steckt nur im Exit-Code.
- `reason` ist **present-on-fail**: auf Pass weggelassen
  (`exclude_none`).
- `schema_version` ist string-monoton (`"1"`, `"2"`, …); ein
  Schema-Bump inkrementiert um genau 1.
- `demo_healthcheck.ready_payload` ist der durchgereichte
  `/ready`-Body und bewusst **nicht** strict-typed — additive
  `/ready`-Komponenten brechen den Schema-Vertrag nicht.

## Exit-Codes (Tri-State, D-9)

| Exit | Bedeutung | stdout-JSON |
| --- | --- | --- |
| `0` | Aggregate-Pass: alle drei Sub-Pruefungen `pass`. | vollstaendig, `overall_status == "pass"` |
| `1` | Aggregate-Fail: mindestens eine Sub-Pruefung `fail` (inkl. Stack-nicht-ready, fehlende/unlesbare Szenario-Datei, Hash-Drift, `/ready` nicht `healthy`). | valide, `overall_status == "fail"` |
| `2` | Tool-Error: CLI-interner Bug (kaputtes YAML mit `YAMLError`, Replay-Crash, Pydantic-Validation-Crash). | fehlt/unvollstaendig; Traceback auf stderr |

CI unterscheidet damit „Abnahme failed (JSON liefert Details — Team
fixt Szenario/Stack)" von „CLI selbst kaputt (Maintainer-
Investigation)". Wichtig: HTTP-Connection-Refused, Non-200 oder
`status != "healthy"` beim `/ready`-Poll sind **Exit 1** (erwartetes
Step-C-Signal), **nicht** Exit 2.

## Pin-Lifecycle + CI-Drift-Lint

Die zwei Erwartungs-Hashes (`EXPECTED_DEMO_SCENARIO_HASH`,
`EXPECTED_DEMO_TELEMETRY_STREAM_HASH`) sind Modul-Konstanten in
`tools/accept.py`. Aendert sich `deploy/scenarios/gg-demo.yaml`
intendiert, **muessen** beide Konstanten mit aktualisiert werden.

Der `make ci`-Gate `make accept-pin-check`
(`tools/check_demo_scenario_pin.py`) recomputed beide Hashes ueber
denselben geteilten `tools/_demo_replay.py`-Helper wie der CLI und
bricht bei Drift mit Angabe, **welche** Konstante anzupassen ist —
damit landet der Bruch im selben PR wie die YAML-Aenderung, nicht
erst nachgelagert.

Recompute lokal:

```bash
make accept-pin-check          # Docker-Stage; grün = Pins aktuell
```

## Abgrenzung zu `gg-demo-008-abnahme.md`

[`gg-demo-008-abnahme.md`](gg-demo-008-abnahme.md) beschreibt die
**manuelle** 6-Schritt-Abnahmereihenfolge fuer `GG-DEMO-008`, die ein
Operator/Reviewer durcharbeitet (Walkthrough). Diese Doku deckt
orthogonal den **automatisierten** `GG-MVP-003`-Pfad ab (ein-Schritt-
Aufruf + maschinenlesbarer JSON-Status). Beide koexistieren mit
getrennten Anwendungsfaellen — kein Ersatz, keine Migration.
