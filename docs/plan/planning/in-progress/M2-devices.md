# Slice-Plan — M2 Geraetemodelle — In Progress

**Status:** In Progress — Welle 0/1/2/3/4/5/6 abgeschlossen
(Welle 6 = 6a + 6b + 6c), zuletzt Welle 6c am 2026-05-20
(`8a3aa2f` Slice-Doc + `c31052c` feat). Welle 0/1/2/3 am
2026-05-18, Welle 4 (4a + 4b + Closure) am 2026-05-19.
Welle 0a/0b/0c (`3322cb8`, `1f19996`, `ee37f36`, `314f853`) +
Welle-0-Review-Fixes (`d490905` / `51a5f4e` / `6d39c7a` /
`df99d97` / `6e108d6`), Welle 1 (`b927e7a`) + Welle-1-Review-
Folge (`88252f1` / `9a61823` / `129c137` / `a6c912c` /
`6e108d6`), Welle 2 (`6247228` / `48f0106` / `5866117` /
`9a138c2`) + Welle-2-Review-Folge (`4600e79` / `eb09e9b` /
`d7bc2d9` / `f4988ff` / `bd13882`), Welle 3a (`2abbd12`) +
Welle 3b + Closure (`e5d3c9a`) + Welle-3-Review-Folge
(`6cad963` / `ea875c3` / `60582e7` / `45a9be6` / `b4e3ce7`),
Welle 4a (`b73b44a`) + Welle-4a-Review-Folge (`579cd5a` /
`1ed976a` / `7ad78e4` / `bdce682`), Welle 4b (`94efb2a`) +
Welle-4b-Review-Folge (`1093b2c` / `bc94a8c` / `d3769dc` /
`85dced7`). Default-`make gates` cache-frei gruen ohne
`CRITICAL_COV_TARGETS`-Override (Default-Liste enthaelt jetzt
alle fuenf MVP-Geraete) plus `core/grid_model` (Welle 5).
Welle 5 (5a + 5b + Closure) am 2026-05-19 abgeschlossen:
Welle 5a (`268a1c0`) + Welle-5a-Review-Folge (`676f684` /
`16f8b9b` / `91e0118` / `1af57b8`); Welle 5b (`fa02c0b`)
+ Welle-5b-Review-Folge (`5f64f78` / `47c054a` / `12ad8f9` /
`e5f8f86` / `29d23bb`). Welle 6a (`27a441f`) + Welle-6a-
Review-Folge (`ff45c11` / `e3909f0` / `f7f21a6` / `da8deef` /
`779fcea`) liegt. Welle 6b (`0f1c597`, kombiniert Implementation
+ Review-Folge: Scenario-Loader-Device-Factory + LoadEvent/
LoadProfile-Wiring + GridConnection-Auto-Schluss + 14
Review-Findings ohne Supersede-ADR) am 2026-05-19 abgeschlossen.
Welle 6c am 2026-05-20 abgeschlossen: Slice-Doc (`8a3aa2f`) +
`feat` (`c31052c`, MVP-Demo-Szenario + Determinismus-/Postgres-
Integrationstest + ScenarioDevice-Permutations-Property-Test).
762 Unit-Tests gruen (+1 vs. Welle 6b), 7 Integration-Tests
gruen (+2 vs. Welle 6b); `make fullbuild` gruen ohne Override
(M2-Welle-6c-Abschluss-Gate). ADR 0015 (Snapshot-Envelope-v2) und ADR 0021 (Scenario-Loader +
TickLoop-Event-Wiring) in Welle-6c-Closure auf `Accepted` gehoben.
Naechster Schritt ist **Welle 7 (M2-Closure)** — Welle 6 ist
in 6a (TickLoop + Snapshot) + 6b (Scenario-Loader) + 6c (MVP-
Demo + Closure) komplett geliefert.
M1-Spine
(`Tick-Loop`, `Scheduler`, `RandomPort`, `ClockPort`, Scenario,
Replay, FastAPI-Adapter, Postgres-Persistenz) liegt; M2 fuellt
den bisher leeren `hexagon/core/devices/`-Slot mit den MVP-
Geraetemodellen `battery`, `pv`, `load`, `smart_meter`,
`grid_connection` und macht `TickResult.emitted_telemetry`
produktiv.
**Datum:** 2026-05-18 (in `next/` eroeffnet);
Move `next/` → `in-progress/`: 2026-05-18 mit Welle-0a-Start.
**Bezug:**
- [`roadmap.md`](roadmap.md) §3 M2 (Vorbelegung,
  „Naechster aktiver Slice: M2").
- M1-Closure-Notiz
  [`done/M1-tick-loop-spine.md`](../done/M1-tick-loop-spine.md)
  + Ergebnisse
  [`done/M1-tick-loop-results.md`](../done/M1-tick-loop-results.md)
  §7 (Welle-7-End-to-End-Sweep, S-1..S-6).
- [`ADR 0002`](../../adr/0002-language-and-build-stack.md)
  §A-1 (`AC-HEXAGON-PURE`, `AC-PORTS-NO-OUT`, `AC-DOMAIN-FROZEN`).
- [`ADR 0007`](../../adr/0007-random-port.md) §5 (`RandomPort.
  sub_port`-Konvention fuer Geraete-Fault-Streams).
- [`ADR 0010`](../../adr/0010-randomport-snapshot-as-mapping.md)
  (`RandomPort.snapshot_as_mapping`-Composition-API — Geraete-
  Sub-Snapshots koppeln hier rein).
- Lastenheft §9 (`GG-DEV-001..018`), §10 (`GG-BESS-001..008`),
  §11 (`GG-GRID-001..007`), §3 (`GG-MVP-002`: End-to-End-
  Szenario mit Netzanschluss/PV/Load/Smart-Meter/Battery).
- Triggers
  [`done/013-replay-diff-tick-ms-parameter.md`](../done/013-replay-diff-tick-ms-parameter.md)
  (Welle 2 abgeschlossen 2026-05-18),
  [`done/014-generic-snapshot-format-codec.md`](../done/014-generic-snapshot-format-codec.md)
  (Welle 0a abgeschlossen 2026-05-18),
  [`done/015-runtime-image-hardening.md`](../done/015-runtime-image-hardening.md)
  (Welle 0b abgeschlossen 2026-05-18).

---

## 1. Zweck

M2 liefert die **produktiven Geraetemodelle** als
Konsumenten des M1-Tick-Loops:

- `DeviceModel`-Vertrag (`GG-DEV-001`) mit `initialize`/`tick`/
  `apply_command`/`snapshot`/`telemetry` als Protocol,
- die MVP-Geraete `battery`, `pv`, `load`, `smart_meter`,
  `grid_connection` unter `hexagon/core/devices/<typ>/`
  (`GG-DEV-010..014`, `GG-MVP-002`-Pflicht; deckt sich mit
  `GG-AR-COMP-DEVICES`-Geraeteliste in `spec/architecture.md`
  §5),
- Batteriemodell mit SOC, Lade-/Entlade-Grenzen, Wirkungsgraden,
  Ramp-Limits, Sicherheitsgrenzen, Initialvalidierung
  (`GG-BESS-001..005`/`008`),
- vereinfachtes **Netzbilanzmodell** unter
  `hexagon/core/grid_model/` (**nicht** unter `devices/`, weil
  `GG-AR-COMP-DEVICES` §5 das Modell nicht als Geraet listet;
  systemweite Bilanz ist eine Tick-Loop-Verantwortung neben
  dem Geraete-Tick) mit Frequenz-/Spannungs-/Lastpfaden
  (`GG-GRID-001..004`),
- `TickResult.emitted_telemetry` befuellt mit deterministisch
  sortierten `TelemetryPoint`-Tupeln pro Tick,
- Geraete-Sub-Snapshots in `SnapshotEnvelope`-Composition
  (via Trigger 014 generalisierter Snapshot-Codec).

M2 schliesst zugleich die **drei Welle-7-Erbschafts-Triggers**
ab, die als „M2-Welle-0-Pflicht-Aktivierung" markiert sind
(siehe `done/M1-tick-loop-results.md` §7):

- Trigger 014 (`generic-snapshot-format-codec`) — sechstes
  Subsystem (`devices/battery`-Validierung) loest die
  Generalisierung mechanisch aus.
- Trigger 015 (`runtime-image-hardening`) — vor neuen Adaptern
  raeumen (`uv sync --no-editable`, Shebang-Rewrite, Base-Image-
  Patch-Strategie).
- Trigger 013 (`replay-diff-tick-ms-parameter`) — Welle 2
  enthaelt einen Battery-Property-Test mit `tick_ms=100`, der
  Trigger 013 ueber `diff_replay(..., tick_ms=100)` mechanisch
  schliesst. Das Demo-Szenario `mvp_demo.yaml` bleibt bei
  `tick_ms=1000` (M1-Konsistenz, siehe §3 Welle 2 und §3
  Welle 6).

**Fault Injection** (`GG-FAULT-001..010`), **Multi-Agent**
(`GG-AGENT-001..008`), **Protokolladapter** (MQTT/Modbus/OPC-UA/
DNP3/IEC) und **OTEL-Tracing** (`GG-OTEL-001..004`) bleiben
explizit out-of-scope — siehe §4. Sie sind M3/M4.

## 2. Erfolgskriterien

M2 ist erfolgreich, wenn:

1. **Default `make gates` ohne `CRITICAL_COV_TARGETS`-Override
   gruen** (S-3 aus M1-Welle-7-Sweep). Erfordert:
   - `src/grid_gym/hexagon/core/devices/battery/` ≥ 90 % Line +
     Branch — Default-`CRITICAL_COV_TARGETS` aus Dockerfile
     `coverage-gate-critical`-Stage (`hexagon/core/simulation
     devices/battery scenario replay`) faellt ohne Override
     durch.
   - kein Welle-Plan darf einen erweiterten `CRITICAL_COV_TARGETS=
     …`-Override als M2-Akzeptanz-Pfad eintragen; Override gilt
     nur als kurzfristiger Welle-Lokal-Krueck, niemals als
     M2-Abschluss-Gate.
2. **`make fullbuild` gruen** auf `main` ohne Welle-6d-Hack-
   Restposten:
   - `deploy/compose.yml::api` benutzt den Dockerfile-`uvicorn`-
     `ENTRYPOINT` direkt, ohne `python -m`-Indirection und ohne
     `entrypoint: []`-Override (Welle-6d-Pattern auf api-Service
     entfernt). Der `simulation`-Stub-Service haelt `entrypoint:
     []` + `sleep infinity` bewusst — er ist kein Webserver und
     wird in M2-Welle-6 durch den Geraete-TickLoop-Runner
     ersetzt.
   - `PYTHONPATH=/app/src`-Workaround ist entfernt
     (`uv sync --no-editable` installiert Wheels direkt in
     site-packages, plus Shebang-Rewrite fuer Binary-Aufrufe),
   - Base-Image-Patch-Strategie ist explizit dokumentiert:
     Welle-0b waehlt Trigger-015-Option-A (in-image
     `apt-get upgrade -y` bleibt im runtime-Stage), weil trivy
     `python:3.14-slim` als Debian-laggard sieht; Wechsel auf
     ein eigenes `grid-gym-base:debian-13-patched`
     (Trigger-015-Option-B) eskaliert auf M6. Siehe Closure-
     Notiz [`done/015-runtime-image-hardening.md`](../done/015-runtime-image-hardening.md).
3. **MVP-Demo-Szenario (`GG-MVP-002`) liegt im Repo**:
   `tests/integration/scenarios/mvp_demo.yaml` oder gleichwertig
   mit Netzanschluss + PV + Load + Smart Meter + Battery,
   deterministischem Smoke-Test (`make test-integration` startet
   das Szenario, verifiziert ≥ 1 Tick Live-Telemetrie).
4. **Determinismus-Property je Geraet**:
   - gleicher Seed + Scenario-Hash → byte-identische
     `TickResult.emitted_telemetry` ueber ≥ 100 Ticks.
   - `Battery.snapshot()` → `Battery.from_snapshot()` → Roundtrip
     produziert byte-identische Folge-Ticks (`GG-SIM-005`).
5. **Trigger-Abarbeitung**:
   - Trigger 014 (`generic-snapshot-format-codec`) nach `done/`
     mit generischer `SnapshotFormatError`-Basis und Aliasen fuer
     die bestehenden M1-Subklassen (Backward-Compat zu Welle-5-
     Tests).
   - Trigger 015 (`runtime-image-hardening`) nach `done/` mit
     dokumentiertem `Dockerfile`-`runtime`-Stage ohne Pragma-
     Hacks.
   - **Trigger 013** (`replay-diff-tick-ms-parameter`) nach
     `done/` — **Welle 2 ist verbindlich**, nicht „sobald
     irgendein Geraet". Closure-Anker ist der Battery-Pflicht-
     Test `tests/unit/hexagon/core/devices/battery/
     test_replay_diff_tick_ms.py` (`tick_ms=100`,
     `diff_replay(..., tick_ms=100)` byte-stabil; siehe §3
     Welle 2 „`tick_ms`-Konvention").
6. **`SnapshotEnvelope.sub_snapshots` enthaelt Geraete-Sub-
   Snapshots** mit `version: int`-Discriminator (ADR 0007/0010-
   Konvention auf Geraete uebertragen). **Pro-Geraet-Pflicht:**
   jede der fuenf MVP-Implementationen (`BatteryDevice`,
   `PvDevice`, `LoadDevice`, `SmartMeterDevice`,
   `GridConnectionDevice`) plus das Welle-5-Netzbilanzmodell
   liefern einen Snapshot-Roundtrip-Contract-Test
   (`from_snapshot(snapshot()) == device` byte-stabil) +
   `version: int`-Erst-Feld-Pruefung. Diese sechs Tests sind
   Welle-N-DoD-Items (siehe Welle 2..5); fehlt einer, ist die
   jeweilige Welle nicht abgeschlossen. Welle 6 verifiziert
   zusaetzlich, dass alle sechs Sub-Snapshots in
   `SnapshotEnvelope.sub_snapshots` zusammengefuehrt sind.
7. **Welle-7-S-1..S-6-Items adressiert**:
   - S-1 (Trigger 014) — Welle 0.
   - S-2 (Sub-Slicing-Heuristik) — §3 Praeambel dieses Plans,
     siehe „Sub-Slicing-Schwelle" unten.
   - S-3 (kein Override) — Erfolgskriterium 1.
   - S-4 (Trigger 015) — Welle 0.
   - S-5 (ADR-Erweiterungs-Pattern fortfuehren) — Welle 1/2
     liefern neue Domain-Form ⇒ neue Erweiterungs-ADR ohne
     Supersedes (z. B. ADR 0013 `DeviceModel`-Protocol, ADR 0014
     `Battery`-Snapshot-Schema).
   - S-6 (Lastenheft §6..§25 Coverage-Sweep) — Welle 0
     mechanisch durchdiffen, Restposten als neue Open-Triggers
     anlegen.

## 3. Liefer-Reihenfolge (Wellen)

**Sub-Slicing-Schwelle (S-2 aus M1-Welle-7-Sweep):** Eine Welle
wird **vor** dem Start in 2 oder mehr Sub-Wellen geteilt, wenn
mindestens eine der folgenden Schwellen erkennbar ist:

- Lieferung beruehrt mehr als ein Driving- *und* ein Driven-
  Adapter-Modul gleichzeitig (M1-Welle-6-Lehre: FastAPI +
  Postgres in einer Welle haben ungeplant in 6a/b/c/d zerfallen).
- DoD-Checkliste der Welle hat > 6 Items, von denen mindestens
  zwei auf unterschiedlichen `make`-Gates aufsetzen
  (`openapi-validate` vs. `test-integration` vs. `image-audit`).
- Welle muesste zwei `*FormatError`-Subsysteme gleichzeitig
  einfuehren (verschaerft Trigger 014).

Wird eine Schwelle nach Start sichtbar, ist Sub-Slicing der
Default — die Welle-Bezeichnung wandert von `Welle N` zu
`Welle Na/Nb/...` mit Eintrag in den Closure-Ergebnissen, **nicht
in diesem Plan rueckwirkend**. Dieser Plan dokumentiert
Welle 0..7 als Erwartungswert.

Wellen sind atomar; jede Welle endet mit einem gruenen Lauf
der bis dahin aktiven Gates (`make gates` — moeglichst ohne
Override, sonst mit explizitem Welle-lokalem
`CRITICAL_COV_TARGETS`).

### Welle 0 — Pflicht-Vorabraeumung (Sub-gesliced 0a / 0b / 0c)

Diese Welle leistet ausschliesslich Welle-7-Erbschafts-Arbeit
aus M1; **kein** Geraete-Code, **kein** Verbreitern der
Domain-Form. Sub-Slicing-Schwelle aus §3 hat gegriffen (drei
unabhaengige Sub-Items mit verschiedenen `make`-Gates).

#### Welle 0a — Trigger 014 (`Done` 2026-05-18, Commit `3322cb8`)

- **S-1 / Trigger 014** (`generic-snapshot-format-codec`)
  geschlossen:
  - `SnapshotFormatError(GridGymError)` + Kategorien
    (`MissingKeysError`, `WrongTypeError`,
    `ListItemWrongTypeError`, `VersionError`) in `errors.py`.
  - Fuenf M1-Per-Subsystem-Roots via Multi-Inheritance an die
    generische Basis gebunden; Leaf-Klassen byte-identisch.
  - `hexagon/core/serialization/snapshot_codec.py` neu mit
    Free-Functions `assert_required_keys`, `assert_int`,
    `assert_mapping`, `assert_payload_canonical_compatible`.
  - Scenario-Validator ruft Free-Function fuer `params`/
    `payload`-Felder auf (Float-/Bytes-Injection typisiert).
  - `SnapshotEnvelope.__post_init__` (Item 5) prueft jetzt
    zusaetzlich rekursiv Payload-Canonical-Kompatibilitaet je
    Sub-Snapshot; wirft typisiert
    `WrongTypeError(subsystem="snapshot_envelope", ...)` bei
    Verstoss.
  - 268 Unit-Tests gruen; `make gates` mit M1-Override gruen.
  - Closure-Notiz: [`done/014-generic-snapshot-format-codec.md`](../done/014-generic-snapshot-format-codec.md).

#### Welle 0b — Trigger 015 (`Done` 2026-05-18, Commit `ee37f36`)

- **S-4 / Trigger 015** (`runtime-image-hardening`)
  geschlossen:
  - `uv sync --frozen --no-dev --no-editable` im `build-app`-
    Stage; `PYTHONPATH=/app/src`-Workaround entfernt.
  - Shebang-Rewrite (`sed`-Loop ueber `/app/.venv/bin/*` und
    `pyvenv.cfg`) — `uvicorn`/`alembic` laufen als direkte
    Binaries.
  - Dockerfile-`ENTRYPOINT` umgestellt auf direkten `uvicorn`-
    Aufruf; `deploy/compose.yml::api` braucht kein
    `entrypoint: []` und kein `python -m`-Indirection mehr.
  - Neues `make rebase-base`-Target zieht
    `python:$(PYTHON_VERSION)-slim` + uv-Image explizit aus
    der Registry.
  - **Base-Image-Patch-Strategie:** Welle 0b waehlt
    Trigger-015-Option-A (in-image `apt-get upgrade -y`)
    bewusst und dokumentiert das im Dockerfile. Trivy-Lauf zeigt,
    dass `python:3.14-slim` Debian-Patches hinterherlaeuft —
    `make rebase-base` alleine reicht nicht. Option B (eigenes
    `grid-gym-base:debian-13-patched`) eskaliert auf M6, falls
    persistente HIGHs/CRITICALs auftauchen.
  - `make fullbuild` cache-frei gruen ohne Pragma-Hacks; 268
    Unit-Tests gruen.
  - Closure-Notiz: [`done/015-runtime-image-hardening.md`](../done/015-runtime-image-hardening.md).

#### Welle 0c — S-6 / Lastenheft-Sweep (`Done` 2026-05-18)

- **S-6 / Lastenheft-Sweep** geschlossen:
  - `spec/lastenheft.md §27.2` (`GG-TRACE-001`-Implementierungs-
    Matrix) erstmalig befuellt — vorher nur Placeholder
    `_(offen)_ 🔲`.
  - Alle `GG-*`-IDs aus §6..§25 mit Implementierungs-Charakter
    sind als Gruppen-Eintraege abgebildet (M1-Lieferungen mit
    konkretem Modul-Pfad, M2..M6-Items mit Meilenstein-Marker,
    SOLLTE-/Post-MVP-Items explizit als `Post-MVP` gekennzeichnet).
    Einzige Ausnahme ist `GG-TERM-003` (§2 Glossar, „kanonisches
    Ergebnis") — Glossar-Eintrag ohne Implementierungs-Charakter,
    behandelt in §27.1.1 als `GG-TERM-001..006 — n/a`.
  - **Range-Konvention** in §27.2 ist `001..005` (zusammenhaengend)
    bzw. `001..005, 008` (mit Loch); reine `/`-Trennung ist
    nicht zugelassen (Review-Befund M-8).
  - **Kein neuer Trigger 016 noetig** — der Sweep hat keine
    echten Implementations-Luecken gefunden, die nicht bereits
    ueber eine Roadmap-Meilenstein-Zuordnung getragen waeren.
    Jeder Eintrag haengt entweder an einer M1-Closure-Notiz,
    am M2-Slice-Plan oder an einer M3..M6-Roadmap-Sektion.
  - `make docs-check` cache-frei gruen.

#### Welle-0-Gate-Erwartung

- Tests: Welle-0a-Tests sind reine Refactor-Tests; Welle-0b
  haengt am Dockerfile/Compose; Welle-0c ist reine Doku
  (`spec/lastenheft.md §27.2`-Befuellung).
- **Gate-Status nach Welle 0a/0b/0c**: `make fullbuild`
  cache-frei gruen mit M1-Override-Liste + `core/serialization`
  und **ohne Welle-6d-Pragma-Hacks am api-Service** (`PYTHONPATH`,
  `entrypoint: []` und `python -m uvicorn` aus `deploy/compose.yml
  ::api` entfernt). Der `simulation`-Stub behaelt `entrypoint:
  []` + `sleep infinity` als bewusster Welle-6c-Stub-Override.
  Default-Critical-Gate bleibt rot, weil `devices/battery`
  weiter leer ist (Welle-2-
  Lieferung). 268 Unit-Tests gruen. Triggers 014/015 nach
  `done/`.

### Welle 1 — `DeviceModel`-Protocol + Device-Domain (`Done` 2026-05-18)

Welle 1 ist abgeschlossen — `DeviceModel`-Protocol + Domain-
Dataclasses liegen, ADR 0013 ist `Accepted`. Die drei
Slice-Plan-§5-Risiken (Placement, Context-Felder, Command-Flow)
sind in ADR 0013 §2 entschieden:

- **Placement** — `DeviceModel` lebt als `typing.Protocol` unter
  `src/grid_gym/hexagon/core/devices/_protocol.py` (Core-internes
  Protocol, kein Driving-Port). Begruendung: AC-PORTS-NO-OUT
  verbietet `ports → core.domain.scenario`-Importe; AC-HEXAGON-PURE
  erlaubt `core/devices → ports.driven` (RandomPort). Siehe
  ADR 0013 §2.1.
- **Context-Felder** — `DeviceTickContext`
  (`hexagon/core/domain/device.py`) traegt nur `tick`,
  `simulation_time`, `tick_ms`. **Kein** `random_sub_port`-Field
  (Domain bleibt port-frei, M1-Pattern erhalten). **Kein**
  `pending_commands`-Field. Siehe ADR 0013 §2.2.
- **Command-Flow** — TickLoop ruft `apply_command(cmd)` pro
  Pending-Command vor `tick(context)`. `apply_command` gibt
  `CommandResult` zurueck; `tick` liefert
  `DeviceTickOutcome(telemetry=...)`. Siehe ADR 0013 §2.3 +
  Architecture §6 Datenfluss-Schritt 5.

**Lieferung im Repo:**

- `src/grid_gym/hexagon/core/domain/device.py` —
  `DeviceTickContext` + `DeviceTickOutcome` Frozen-Dataclasses,
  port-frei (kein `RandomPort`-Field).
- `src/grid_gym/hexagon/core/devices/_protocol.py` —
  `@runtime_checkable` `DeviceModel`-Protocol mit den fuenf
  Pflicht-Methoden.
- `src/grid_gym/hexagon/core/devices/__init__.py` — Re-Export
  von `DeviceModel`.
- `docs/plan/adr/0013-device-model-protocol.md` — ADR
  `Accepted` (direkt `Proposed → Accepted` per `ADR 0006 §2`,
  kein Validierungs-Spike noetig; Adherence im Unit-Test).
- `tests/unit/hexagon/core/devices/_fakes.py` — `NullDevice`
  als Protocol-satisfies-Test-Double; M2 Welle 2..5
  importieren das fuer Tick-Loop-Integration.
- `tests/unit/hexagon/core/devices/test_protocol_contract.py` —
  Adherence-Tests (Protocol-isinstance, Methoden-Surface,
  `version: int`-Erstfeld, `SnapshotEnvelope`-Composition,
  Frozen-Dataclass-Pflicht, Decimal-Payload-Canonical-OK).

**Was Welle 1 NICHT liefert** (Welle-1-Review-Folge N-1):

- **Keine TickLoop-Integration.** `hexagon/core/simulation/
  tick_loop.py` zeigt weiterhin den M1-Scheduler-basierten
  Event-Pfad ohne `device.tick()`-Aufruf. Die produktive
  Verdrahtung (TickLoop iteriert ueber Geraete, ruft
  `apply_command(cmd)` pro Pending-Command + `tick(context)` +
  sammelt `DeviceTickOutcome.telemetry` in
  `TickResult.emitted_telemetry`) ist Welle-6-Pflichtweg
  (siehe §3 Welle 6 unten). Welle 1 liefert nur den **Vertrag**,
  nicht die Laufzeit.
- **Keine konkreten Geraete-Implementationen.** Battery (Welle 2),
  PV/Load (Welle 3), GridConnection (Welle 4a),
  SmartMeter (Welle 4b), Grid-Bilanz-Modell (Welle 5) folgen
  sequenziell.

**Konvention fuer Welle 2..5** (ADR 0013 §5):

- Jede konkrete Geraete-Implementation wiederholt die Adherence-
  Pruefung mit ihrer eigenen Klasse als Parameter.
- Snapshot-Roundtrip `from_snapshot(snapshot()) == device` ist
  byte-stabil je Geraet (Welle-N-DoD-Item, kein Welle-7-Restposten).
- `from_snapshot` ist nach Welle-1-Review-Schaerfung
  Pflicht-Bestandteil des Protocols (`@classmethod`, ADR 0013
  §2.4); isinstance-Check faengt fehlende Implementationen
  mechanisch ab.

**Verifikation:** 303 Unit-Tests gruen nach Welle-1-Review-Folge
(277 M1+Welle-0-Stand → 290 nach Welle-1-Erstwurf → 303 nach
Welle-1-Review-Schaerfungen: +13 Protocol-/Domain-/Frozen-/
Decimal-Tests im Erstwurf, +14 Review-Tests fuer Wrong-Signature/
Lifecycle-Raises/from_snapshot-Roundtrip/Decimal-Boundary).
`make gates` gruen mit erweitertem `CRITICAL_COV_TARGETS`
(Welle-0-Liste + `hexagon/core/devices`).

### Welle 2 — Battery (`GG-DEV-010` + `GG-BESS-001..005, 008`) (`Done` 2026-05-18)

**Kritische Welle abgeschlossen.** Default-`make gates` cache-frei
gruen ohne `CRITICAL_COV_TARGETS`-Override — Erfolgskriterium 1
(S-3 aus M1-Welle-7-Sweep) erreicht. ADR 0014 `Accepted` in der
Welle-2-Closure. Commits: `6247228` (Battery-Module + ADR 0014
Provisional), `48f0106` (Determinismus + Trigger 013),
`5866117` (Trigger 013 nach `done/`), folgender Closure-Commit.

**Belege:**

- 380 Unit-Tests gruen (vorher 303 → +69 Welle-2-Erstwurf +
  +8 Determinismus/Trigger-013 = 380).
- `make coverage-gate-critical` (Default-Liste) liefert
  **92.50 % Branch-Coverage** gegen 90 %-Schwelle.
- `make gates` cache-frei gruen.
- Trigger 013 (`replay-diff-tick-ms-parameter`) nach `done/`
  gewandert (Commit `5866117`).
- ADR 0014 `Proposed → Accepted` (Welle-2-Closure-Commit).

- `src/grid_gym/hexagon/core/devices/battery/`:
  - `config.py` — `BatteryConfig` Frozen-Dataclass: `capacity_
    kwh`, `initial_soc_pct`, `min_soc_pct`, `max_soc_pct`,
    `max_charge_kw`, `max_discharge_kw`, `charge_efficiency`,
    `discharge_efficiency`, `ramp_kw_per_s`. Initial-Validator
    nach `GG-BESS-008`.
  - `model.py` — `BatteryDevice` implementiert `DeviceModel`-
    Protocol. SOC-Fortschreibung aus Leistung × Tick-Dauer ×
    Wirkungsgrad (`GG-BESS-001`/`003`). Ramp-Limits
    (`GG-BESS-004`). Sicherheitsgrenzen-Validierung
    (`GG-BESS-005`): unzulaessige SOC-/Leistung-/Temperatur-/
    Spannungswerte werden nicht in den naechsten Tick
    uebernommen.
  - `commands.py` — Command-Validator. Innerhalb-Grenzen-
    Power-Befehle bekommen `CommandResult.LIMITED` + Alarm
    (`GG-BESS-002`), Grenzwert-verletzende Befehle bekommen
    `CommandResult.REJECTED` + Alarm.
  - `snapshot.py` — `BatterySnapshot` Frozen-Dataclass +
    `from_snapshot` als classmethod, konsumiert generische
    `SnapshotFormatError`-Codec aus Welle 0.
- `BatteryDevice.telemetry()` liefert mindestens `soc_pct`,
  `soc_kwh`, `power_kw`, `command_status` als
  `TelemetryPoint`-Tupel (deterministisch nach Metrikname
  sortiert).
- **`tick_ms`-Konvention fuer Welle 2** (loest §1 / Trigger 013
  konkret aus):
  - Demo-Szenario `mvp_demo.yaml` (in Welle 6) faehrt mit
    `tick_ms=1000` (M1-Konsistenz, lesbar in CI).
  - **Welle-2-Pflicht-Test**:
    `tests/unit/hexagon/core/devices/battery/test_replay_diff_tick_ms.py`
    laeuft eine SOC-Spur mit `tick_ms=100` (10x feiner als M1-
    Default), exportiert die `TelemetryPoint`-Folge und
    vergleicht sie via `diff_replay(expected, actual,
    tick_ms=100)` byte-stabil — schliesst Trigger 013
    (`replay-diff-tick-ms-parameter`) mechanisch und ist
    Welle-2-DoD-Item.
- Tests:
  - Unit-Tests pro Akzeptanz-Kriterium `GG-BESS-001..005`/
    `008`. Determinismus-Property via
    `hypothesis @given(seed=integers(min_value=0))`: gleicher
    Seed + identische Command-Sequenz → byte-identische SOC-Spur
    ueber ≥ 100 Ticks.
  - Snapshot-Roundtrip-Test (Welle-1-Konvention):
    `BatteryDevice.snapshot()` → `BatteryDevice.from_snapshot()`
    produziert byte-identische Folge-Ticks; Snapshot-Mapping
    fuehrt `version: int` als Erst-Feld.
  - Trigger-013-Pflicht-Test (siehe `tick_ms`-Konvention oben).
  - Integration-Test fuegt `BatteryDevice` an den `TickLoop`
    an und fuellt `TickResult.emitted_telemetry` ueber 10 Ticks.
  - Negativ-Tests: ungueltige Config (`GG-BESS-008`),
    Command-Out-of-Range (`GG-BESS-002`), Safety-Limit-Verstoss
    (`GG-BESS-005`).
- **Gate-Status nach Welle 2**: **Default `make gates` ohne
  `CRITICAL_COV_TARGETS`-Override gruen** — `devices/battery` ≥
  90 % Line + Branch. Welle 2 ist der Punkt, ab dem M2-
  Erfolgskriterium 1 erreicht ist. Folgewellen duerfen den
  Default nicht wieder rot machen.

### Welle 3 — PV + Load (`GG-DEV-011`/`013`) (`Done` 2026-05-18)

Welle 3a (PV, Commit `2abbd12`) und Welle 3b (Load + Closure,
folgender Commit) abgeschlossen. ADR 0016 `Accepted` —
gemeinsames Generation/Consumption-Pattern fuer beide
Geraete. Sub-Slicing nach Empfehlung der Welle-3-Praeambel:
PV+Load in separaten Commits, aber **eine ADR**.

**Lieferung im Repo:**

- `hexagon/core/devices/pv/` (5 Module): `PvConfig`/`PvAlarm`/
  `PvSnapshot`/`PvDevice` mit konstantem `rated_power_kw`-
  Erzeugungsmodell + `set_power_kw`-Override.
- `hexagon/core/devices/load/` (5 Module): Spiegel mit
  Sign-Konvention „Load verbraucht nicht-negativ" (ADR 0016
  §2.2).
- Welle-3-Minimum: kein Generationsprofil, kein Replay-Source-
  Pfad. Zeitreihen kommen mit Welle 5 (Netzbilanzmodell-
  Integration) bzw. M3 (Replay-Verkabelung).
- Beide Geraete emittieren 1 `TelemetryPoint` mit Metric
  `power_kw` pro Tick (Quantisierung 6 Nachkommastellen).
- Tests:
  - 44 PV-Tests (`tests/unit/hexagon/core/devices/pv/
    test_pv_device.py`) — Config, Protocol-Adherence, Lifecycle,
    Param-Parsing, Command-Surface, Telemetry, Snapshot-
    Roundtrip + Codec-Errors, Alarms + Drain, Multi-Command-
    last-wins, Determinismus-Property ueber 100 Ticks.
  - 37 Load-Tests (analog).
- Welle-2-Review-Patterns mechanisch gespiegelt: self-sufficient
  `from_snapshot` (C-1), `drain_alarms()` (M-3),
  `set_run_id`-Hook (H-2), `limit_unit` (L-3), payload-None-
  defensive (M-7), Sign-Vertrag-vor-Clamp (M-8-Analogie).

**Belege:**

- 478 Unit-Tests gruen (vorher 397 → +44 PV + +37 Load = +81).
- `make gates` cache-frei gruen **ohne**
  `CRITICAL_COV_TARGETS`-Override (Welle-2-Erfolgskriterium 1
  bleibt erhalten).
- ADR 0016 `Proposed → Accepted` mit Welle-3-Closure-Commit.

**Welle-3-Review-Folge (`Done` 2026-05-18, 5 Commits):**

Independent code-reviewer fand 1 Crit + 3 High + 6 Med + 7 Low
+ 5 Info. Alle Findings adressiert ueber 5 Folge-Commits:

- `6cad963` — C-1 (Dockerfile-Default `CRITICAL_COV_TARGETS` um
  PV/Load erweitert) + H-1 (Lastenheft §12.1 `power_kw` →
  `rated_power_kw` Drift-Fix) + L-5 (PLR0904 per-file-ignore in
  pyproject.toml fuer `devices/*/model.py`).
- `ea875c3` — ADR 0016 + 0014 Schaerfung: H-2 Sign-Worked-
  Example, H-3 Pre-init-Snapshot-Asymmetry, M-3 Decimal-Context-
  Forward-Looking-Defense, L-3 set_mode-Cross-Reference, L-4
  Load-Default-Begruendung.
- `60582e7` — L-1 generischer Codec: `assert_str` + `assert_decimal`
  als Free-Functions; `battery/pv/load/snapshot.py` migriert.
- `45a9be6` — M-4 `_RUN_ID_UNSET`-Konstante + M-5 `_random`-
  Forward-Looking-Defense-Doku + M-6 `attach_random`-Methode auf
  allen drei Geraeten + 6 neue Tests (L-2/I-3).
- `b4e3ce7` — M-1 PV/Load-Duplikations-Begruendung (Welle-5-
  Divergenz-Vorgriff) + M-2 Alarm-`(result, limit)`-Tupel-
  Disambiguation in Docstrings.

`make gates` und `make docs-check` cache-frei gruen nach jedem
Commit; Test-Anzahl 478 → 484 (+6 Tests fuer attach_random/
run_id-Defaults).

### Welle 4 — SmartMeter + GridConnection (`GG-DEV-012`/`014`)

**Sub-Slicing-Entscheidung (Pre-Start, 2026-05-19):** Welle 4
ist vor dem Start in **4a (GridConnection) + 4b (SmartMeter +
Closure)** geteilt. Die §3-Sub-Slicing-Schwellen greifen
nicht strikt — beide Geraete laufen auf demselben `make`-Gate
(`test-unit` + Default-`coverage-gate-critical`) und der
generische Codec aus Welle 0a + Welle-3-Review-L-1 traegt
fuer beide (kein zweites `*SnapshotFormatError`-Subsystem
einzufuehren). Die Spaltung ist eine **Judgment-Call-
Vorsorge** wie Welle 3a/3b: zwei verschiedene Device-Patterns
(stateful Anschlusspunkt mit kumulativem Import/Export-Sums
vs. stateless Aggregator ueber Geraete-Telemetry) in einem
Commit waeren ein groesseres Review-Paket als noetig. Folge:
**zwei separate ADRs 0017 + 0018**, nicht eine geteilte (wie
ADR 0016 fuer PV+Load) — die State-Modelle (kumulativ vs.
stateless) und die Command-Surfaces sind zu verschieden, um
eine ehrliche Abstraktion zu rechtfertigen.

#### Welle 4a — GridConnection (`GG-DEV-012`) + ADR 0017 (Provisional) (`Done` 2026-05-19)

**Abgeschlossen.** Commits: `b73b44a` (Welle-4a-Erstwurf
+ ADR 0017 Provisional) plus Welle-4a-Review-Folge `579cd5a`
(H-1 + M-2 Doku-Drift), `1ed976a` (M-1 + M-3 ADR-Schaerfung),
`7ad78e4` (M-4 + M-5 + L-4 Test-Pflicht), `bdce682` (L-3
Single-Source-of-Truth).

**Belege:**

- 545 Unit-Tests gruen (vorher 484 → +59 GridConnection-
  Erstwurf, dann +2 Pre-Init-Hook-Tests = 545).
- `make gates` cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override (Default-Liste enthaelt
  jetzt `devices/grid_connection`).
- ADR 0017 `Proposed → Provisional` (Schaerfung auf
  `Accepted` mit Welle-4b-Closure).
- Welle-4a-Review-Befund: 0 Crit / 1 High / 5 Med / 4 Low /
  3 Info; alle Crit/High/Med + 2 Low adressiert, L-1/L-2 als
  Forward-Looking offen gelassen (Welle-5+-Material bzw.
  Konvention bereits projektweit), Info-only nicht
  adressiert.

**Lieferung im Repo:**

- `hexagon/core/devices/grid_connection/` (Struktur analog
  Welle 2 Battery + Welle 3 PV/Load):
  - `config.py` — `GridConnectionConfig` Frozen-Dataclass mit
    Anschlusspunkt-Parametern (Vorschlag: `nominal_voltage_v`,
    `max_import_kw`, `max_export_kw`). Initial-Validator nach
    Welle-2/3-Pattern (positive Grenzwerte, konsistente
    Sign-Konvention).
  - `model.py` — `GridConnectionDevice` implementiert
    `DeviceModel`-Protocol. **Stateful:** kumulative
    `import_kwh`/`export_kwh`-Summen werden tick-weise aus
    `power_kw × tick_dauer` fortgeschrieben. Sign-Konvention
    in ADR 0017 §2 fixiert (Vorschlag: Bezug = Netzanschluss,
    Import positiv = Energie ins lokale System, Export
    negativ = Energie aus dem lokalen System ins Netz —
    spiegelt PV/Load-Sign-Konvention aus ADR 0016 §2.2
    mechanisch).
  - `commands.py` — Command-Validator. Welle-4a-Minimum: nur
    `set_power_kw`-Override (analog PV/Load aus Welle 3); der
    typische Set-Point kommt aus Scenario-Events, nicht aus
    Operator-Commands. Grenzwert-verletzende Befehle →
    `CommandResult.REJECTED` + Alarm; innerhalb-Grenzen-
    Power-Befehle ueber `max_import_kw`/`max_export_kw` →
    `LIMITED` + Alarm mit `(result, limit, limit_unit)`-Tupel
    (Welle-3-Review-M-2-Disambiguation + L-3-`limit_unit`).
  - `snapshot.py` — `GridConnectionSnapshot` Frozen-Dataclass
    mit `version: int`-Erst-Feld + `from_snapshot` als
    classmethod. Konsumiert generische Codec-Free-Functions
    aus Welle 0a + Welle-3-Review-L-1 (`assert_str`,
    `assert_decimal`, `assert_required_keys`,
    `assert_payload_canonical_compatible`). Kumulative
    `import_kwh`/`export_kwh`-Felder sind im Snapshot
    **explizit** persistiert (Unterschied zum stateless
    SmartMeter in 4b); Self-Sufficient-`from_snapshot`
    (Welle-2-Review-C-1) verifiziert, dass kein
    Re-Initialisierungs-Schritt die Summen zurueckschiebt.
- `GridConnectionDevice.telemetry()` liefert genau drei
  `TelemetryPoint`s (sortiert nach Metrikname: `export_kwh`,
  `import_kwh`, `power_kw`). **Kein `command_status`-Telemetry-
  Point** — `TelemetryPoint.value` ist `Decimal`, ein String-
  Tag ist strukturell nicht emittierbar; Command-Status laeuft
  ueber `drain_alarms()` + `GridConnectionAlarm` (analog
  Battery / PV / Load; ADR 0017 §2.5).
- **Welle-2/3-Review-Patterns mechanisch gespiegelt** (gleiche
  Liste wie PV/Load in Welle 3b):
  - C-1: self-sufficient `from_snapshot` ohne `__init__`-
    Re-Run.
  - C-2: Sign-Vertrag-vor-Clamp (Welle-2/3-Reihenfolge).
  - M-2: Alarm-`(result, limit, limit_unit)`-Tupel-
    Disambiguation in Docstrings.
  - M-3: `drain_alarms()`-Methode.
  - M-4: `_RUN_ID_UNSET`-Konstante (kein magisches `None`).
  - M-5/M-6: `attach_random`-Methode mit Forward-Looking-
    Defense-Doku.
  - M-7: payload-None-defensive in `apply_command`.
  - H-2: `set_run_id`-Hook (Welle-3-Pattern, fuer M3-Fault-
    Streams vorbereitend).
  - L-3: `limit_unit`-Field auf Alarm-Tupel.
- ADR 0017 (`grid-connection-device-pattern`) `Proposed →
  Provisional` mit Welle-4a-Commit. ADR-Erweiterungs-Pattern
  ohne Supersedes (ADR 0011 §2); Schaerfung auf `Accepted`
  mit Welle-4b-Closure-Commit (oder spaetestens mit Welle 7,
  falls Welle-4a-Review-Folge offene Punkte vererbt).
- **Lastenheft §12 `grid_connection`**-Drift-Check (Welle-3-
  Review-H-1-Pattern): Welle 4a verifiziert mechanisch, dass
  die `power_kw`/`import_kwh`/`export_kwh`-Metriknamen im
  Lastenheft mit dem Code uebereinstimmen — bei Drift Doku
  nachziehen, nicht Code (Code ist authoritative ab M2).
- Tests:
  - Unit-Tests pro Akzeptanz-Kriterium `GG-DEV-012`
    (Minimalmodell + deterministischer Smoke-Test).
  - Protocol-Adherence-Test (Welle-1-Konvention) gegen
    `DeviceModel`-Protocol mit `GridConnectionDevice` als
    Parameter.
  - Snapshot-Roundtrip-Contract-Test:
    `GridConnectionDevice.snapshot()` →
    `GridConnectionDevice.from_snapshot()` produziert
    byte-identische Folge-Ticks; `version: int` als Erst-Feld;
    `import_kwh`/`export_kwh`-Kontinuitaet ueber den
    Roundtrip verifiziert.
  - Determinismus-Property via
    `hypothesis @given(seed=integers(min_value=0))`: gleicher
    Seed + identische Command-Sequenz → byte-identische
    Telemetry-Folge ueber ≥ 100 Ticks (einheitlich mit
    Erfolgskriterium 4).
  - Negativ-Tests: ungueltige Config, Command-Out-of-Range
    (Sign-Konvention + Limit-Tupel).
- **Welle-4a-Gate-Status**: Default `make gates` cache-frei
  gruen — `devices/grid_connection` ≥ 90 % Line + Branch.
  Default-`CRITICAL_COV_TARGETS` aus Dockerfile-`coverage-
  gate-critical`-Stage wird in Welle 4a um
  `devices/grid_connection` erweitert (Welle-3-Review-C-1-
  Pattern). 484 → ~540 Unit-Tests (analog Welle 3b: +40..+60
  Tests).

#### Welle 4b — SmartMeter (`GG-DEV-014`) + ADR 0018 (Accepted) + Welle-4-Closure (`Done` 2026-05-19)

**Abgeschlossen.** Commits: `94efb2a` (Welle-4b-Erstwurf +
ADR 0018 Proposed) plus Welle-4b-Review-Folge `1093b2c`
(H-1 power_kw-Pflicht), `bc94a8c` (M-1 + M-3 Doku), `d3769dc`
(M-2 typed-Error-Wrap), `85dced7` (L-1 + L-2 + L-4 Style),
plus Welle-4-Closure-Commit (ADR 0017 → Accepted, ADR 0018
→ Accepted, §1 Status-Sync auf Welle 5).

**Belege:**

- 605 Unit-Tests gruen (vorher 545 → +58 SmartMeter-Erstwurf
  → +2 Welle-4b-Review-Tests = 605).
- `make gates` cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override (Default-Liste enthaelt
  jetzt alle fuenf MVP-Geraete: `battery`, `pv`, `load`,
  `grid_connection`, `smart_meter`).
- ADR 0018 `Proposed → Accepted` (direkt; ADR 0017 parallel
  `Provisional → Accepted`).
- Welle-4b-Review-Befund: 0 Crit / 1 High / 4 Med / 4 Low /
  3 Info; alle Crit/High/Med + 3 Low adressiert, M-4/L-3 als
  Reviewer-empfohlene Skips offen (Pattern-Konsistenz mit
  Welle 4a bzw. Folge-Welle), Info-only nicht adressiert.

**Lieferung im Repo:**

- `hexagon/core/devices/smart_meter/` (Struktur analog 4a):
  - `config.py` — `SmartMeterConfig` Frozen-Dataclass mit
    Aggregations-Scope (Vorschlag: `aggregate_device_ids:
    tuple[str, ...]` — kanonisch sortiert nach Welle-1-
    Konvention; Initial-Validator prueft Format).
  - `model.py` — `SmartMeterDevice` implementiert
    `DeviceModel`-Protocol. **Stateless aggregator:**
    Aggregation laeuft je Tick neu ueber die in
    `aggregate_device_ids` referenzierten Geraete
    (PV/Load/Battery/optional GridConnection); kein interner
    Speicher ausser Pending-Commands + RNG-Stand.
    Aggregations-Funktion: Summe von `power_kw` der Quellen
    (Welle-4b-MVP — Erweiterungen wie energy-Aggregat sind
    Forward-Looking, in ADR 0018 dokumentiert). ADR 0018 §2
    fixiert das Aggregat-Vertrag-Detail (Decimal-Konvention,
    Tupel-Ordnung, **fehlende-Device-Verhalten** = typisierter
    Fehler, kein Silent-Skip).
  - `commands.py` — Welle-4b-Minimum: keine produktiven
    Commands ausser dem Drain-Pfad (analog PV/Load-Pattern).
    Pending-Commands werden defensiv akzeptiert; `apply_
    command` mit unbekanntem Typ wirft `CommandResult.
    REJECTED` + Alarm.
  - `snapshot.py` — `SmartMeterSnapshot` Frozen-Dataclass mit
    `version: int`-Erst-Feld + `from_snapshot` als
    classmethod. **Wichtig:** der Snapshot enthaelt NUR
    SmartMeter-eigene Felder (Config-Hash + Pending-
    Commands + RNG-Stand + `_run_id`); die aggregierten Werte
    sind derived und werden zur Snapshot-Zeit **nicht**
    persistiert. Roundtrip-Test prueft genau das (negative
    Assertion: kein `aggregated_*`-Feld im Mapping).
- `SmartMeterDevice.telemetry()` liefert mindestens
  `aggregated_power_kw` und `command_status` als
  `TelemetryPoint`-Tupel; weitere Metriken (z. B.
  `aggregated_energy_kwh`) sind Welle-4b-Optional
  (Forward-Looking, in ADR 0018 dokumentiert, aber kein DoD).
- **Welle-2/3-Review-Patterns mechanisch gespiegelt** —
  gleiche Liste wie Welle 4a (C-1/C-2/M-2/M-3/M-4/M-5/M-6/
  M-7/H-2/L-3). **Plus** Welle-4b-spezifisch:
  - **Aggregator-Reference-Lookup-Defense**: wenn eine
    referenzierte `aggregate_device_ids`-ID im aktuellen
    Tick-Context fehlt (z. B. nach Snapshot-Resume mit
    geaenderter Scenario-Struktur), wirft
    `SmartMeterDevice.tick()` einen typisierten Fehler — kein
    Silent-Skip. Dokumentation in ADR 0018 §2.
  - **Decimal-Aggregations-Kontext**: Summe ueber
    `Decimal`-Werte muss byte-stabil sein (Welle-2-Review-
    M-2 / Welle-3-Review-M-3-Pattern); Quantisierung 6
    Nachkommastellen nach Aggregation.
- ADR 0018 (`smart-meter-device-pattern`) `Proposed →
  Provisional` mit Welle-4b-Commit; Schaerfung auf `Accepted`
  mit Welle-4-Closure-Commit. ADR-Erweiterungs-Pattern ohne
  Supersedes.
- **Lastenheft §12 `smart_meter`**-Drift-Check (Welle-3-
  Review-H-1-Pattern): analog Welle 4a, Metriknamen
  abgleichen.
- Tests:
  - Unit-Tests pro Akzeptanz-Kriterium `GG-DEV-014`
    (Minimalmodell + deterministischer Smoke-Test).
  - Protocol-Adherence-Test (Welle-1-Konvention) gegen
    `DeviceModel`-Protocol mit `SmartMeterDevice` als
    Parameter.
  - Snapshot-Roundtrip-Contract-Test (`version: int` als
    Erst-Feld; **negative Assertion**: `aggregated_*`-Felder
    explizit NICHT im Snapshot, durch Test verifiziert).
  - Determinismus-Property ueber ≥ 100 Ticks (einheitlich
    mit Erfolgskriterium 4); SmartMeter-Determinismus ist
    bedingt deterministisch — gleicher Seed + identische
    Quellen-Telemetry → identische Aggregat-Telemetry.
  - Aggregator-Smoke-Test: SmartMeter aggregiert ueber
    `(PvDevice, LoadDevice, BatteryDevice,
    GridConnectionDevice)` und reproduziert die Summe
    byte-stabil ueber 10 Ticks.
  - Negativ-Test: Aggregator-Reference-Lookup-Defense
    (fehlende Device-ID nach Resume → typisierter Fehler).
- **Welle-4-Closure-Bestandteile** (zusaetzlich zu 4b-Code):
  - ADR 0017 + ADR 0018 auf `Accepted` heben.
  - `Status:`-Header im Slice-Plan auf "Welle 4
    abgeschlossen" ziehen.
  - `Naechster Schritt`: Welle 5 (Netzbilanzmodell).
- **Welle-4b-Gate-Status**: Default `make gates` cache-frei
  gruen — `devices/smart_meter` ≥ 90 % Line + Branch.
  Default-`CRITICAL_COV_TARGETS` um `devices/smart_meter`
  erweitert. ~540 → ~600 Unit-Tests (analog Welle 3a/3b-
  Volumen).

#### Welle-4-Gate-Erwartung (Sub-Welle-uebergreifend)

- Default-`CRITICAL_COV_TARGETS` aus Dockerfile-Stage
  enthaelt nach Welle 4b: `hexagon/core/simulation
  devices/battery devices/pv devices/load
  devices/grid_connection devices/smart_meter scenario
  replay` — fuenf MVP-Geraete plus M1-Spine + Scenario +
  Replay. Erfolgskriterium 1 bleibt unverletzt.
- ADR 0017 + ADR 0018 sind nach Welle 4b `Accepted` (oder
  spaetestens mit Welle-7-Closure, falls Welle-4-Review-
  Folge offene Punkte vererbt — Pattern aus Welle 3a/3b).

### Welle 5 — Netzbilanzmodell (`GG-GRID-001..004`)

**Abgrenzung gegenueber Welle 4a:** `grid_connection` aus
Welle 4a ist ein **Geraetetyp** (`GG-DEV-012`,
`hexagon/core/devices/grid_connection/`). Das **Netzbilanzmodell**
hier ist *kein* Geraet — Bezeichnung und Pfad sind bewusst
verschieden, weil `GG-AR-COMP-DEVICES` §5 das Modell nicht als
Device listet und die Bilanz aggregiert ueber alle
Connection-Points laeuft. Welle 6 verdrahtet die zwei Schichten
ueber den TickLoop.

**Sub-Slicing-Entscheidung (Pre-Start, 2026-05-19):** Welle 5
ist vor dem Start in **5a (Bilanz + GridModelSnapshot) + 5b
(Loads + CSV/JSON-Parser + Closure)** geteilt. Die
§3-Sub-Slicing-Schwellen greifen weich — beide Sub-Wellen
laufen auf demselben `make`-Gate (`test-unit` + Default-
`coverage-gate-critical`), aber:

- **Zwei verschiedene Concerns**: 5a ist reines **Physik-Modell**
  (Frequenz/Spannungs-Formel + Snapshot), 5b ist eine
  **Daten-/I/O-Integration** (CSV/JSON-Parser + Scenario-Event-
  Erweiterung). Vertraege, Test-Stile und Reviewer-Aufmerksamkeit
  divergieren deutlich.
- **Driftrisiko gegen M3-Replay-Verkabelung**: 5b nimmt eine
  Aufgabe vor, die im urspruenglichen Plan urspruenglich auch
  als M3-Replay-Source-Pfad gelistet war. Bewusste Doppel-
  Implementierung wird in ADR 0020 dokumentiert; M3 baut auf
  5b auf, statt parallel zu replizieren.
- **Zwei separate ADRs 0019 + 0020** statt einer geteilten
  (wie ADR 0017 + 0018 fuer GridConnection/SmartMeter) — die
  Concerns sind zu verschieden fuer eine ehrliche Abstraktion.

#### Welle 5a — Bilanz + GridModelSnapshot + ADR 0019 (Provisional) (`Done` 2026-05-19)

**Abgeschlossen.** Commits: `268a1c0` (Welle-5a-Erstwurf +
ADR 0019 Proposed, +1075/-1) plus Welle-5a-Review-Folge
`676f684` (M-4 Decimal-Type + L-1 Re-Export), `16f8b9b`
(M-1 model_kind semantisch), `91e0118` (M-3 Lastenheft-Marker
+ L-3 Single-Source + L-5 bool-Negativ), `1af57b8` (M-2 + L-2
ADR-Doku-Sync). ADR 0019 ist `Provisional`; Schaerfung auf
`Accepted` mit Welle-5-Closure.

**Belege:**

- 642 Unit-Tests gruen (vorher 605 → +34 grid_model-Erstwurf,
  +3 Welle-5a-Review-Tests = 642).
- `make gates` cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override (Default-Liste enthaelt
  jetzt `core/grid_model`).
- ADR 0019 `Proposed → Provisional` (nach 3 Pre-
  Implementation-Schaerfungs-Runden + 1 Review-Folge-
  Schaerfung).
- Welle-5a-Review-Befund: 0 Crit / 0 High / 4 Med / 5 Low /
  4 Info; alle Crit/High/Med + 4 Low adressiert (L-4 als
  Reviewer-empfohlener Skip, I-1..I-4 Forward-Looking).

**Lieferung im Repo:**

- `hexagon/core/grid_model/` (Top-Level neben `devices/`,
  `scenario/`, `replay/`):
  - `bilanz.py` — vereinfachtes Leistungsbilanzmodell
    (`GG-GRID-001`/`002`) leitet Frequenz-/Spannungsabweichungen
    aus Erzeugung, Last, Speicherleistung ab. Vorschlag
    (in ADR 0019 §2 zu fixieren): einfache proportionale Formel
    `f = f_nom + k_f * imbalance_kw`, `v = v_nom + k_v *
    imbalance_kw`, mit Safety-Clamps gegen Runaway.
  - `snapshot.py` — `GridModelSnapshot` Frozen-Dataclass mit
    `version: int`-Erst-Feld + `from_snapshot` als classmethod,
    konsumiert generischen `SnapshotFormatError`-Codec aus
    Welle 0. Snapshot-Sub-Key in `SnapshotEnvelope.sub_snapshots`
    ist `grid_model` (Single-Instance, kein
    `devices.<device_type>.<device_id>`).
- ADR 0019 (`grid-model-bilanz-pattern`) `Proposed → Provisional`
  mit Welle-5a-Commit; Schaerfung auf `Accepted` mit
  Welle-5b-Closure-Commit (oder spaetestens Welle 7).
- Tests:
  - Property-Tests fuer Leistungsbilanz via
    `hypothesis @given(seed=integers())`: Summe (Erzeugung −
    Last − Speicherleistung) ist deterministisch konsistent mit
    Frequenzabweichung und seed-stabil.
  - **Snapshot-Roundtrip-Contract-Test** (Welle-1-Konvention,
    auf das Bilanzmodell uebertragen, **ohne** `DeviceModel`-
    Protocol-Adherence-Test — das Bilanzmodell ist kein
    `DeviceModel`): `version: int` als Erst-Feld + byte-stabiler
    `from_snapshot(snapshot())`-Roundtrip ist Welle-5a-DoD-Item.
  - Safety-Clamp-Tests: Frequenz/Spannung verlassen ihre
    Wertebereiche nicht (z. B. `45 Hz ≤ f ≤ 55 Hz`,
    `0.7 * v_nom ≤ v ≤ 1.3 * v_nom`); ungueltige Imbalance-
    Inputs werden defensiv geclamped.
- **Welle-5a-Gate-Status**: Default `make gates` cache-frei
  gruen — `core/grid_model` ≥ 90 % Line + Branch
  (Default-`CRITICAL_COV_TARGETS` um `core/grid_model`
  erweitert).

#### Welle 5b — Loads + LoadProfile + CSV/JSON-Parser + ADR 0020 (Accepted) + Welle-5-Closure (`Done` 2026-05-19)

**Abgeschlossen.** Commits: `fa02c0b` (Welle-5b-Erstwurf +
ADR 0020 Provisional, +1200/-19) plus Welle-5b-Review-Folge
`5f64f78` (H-1+M-2 CSV-Haertung), `47c054a` (M-1 ADR-Naming),
`12ad8f9` (M-3+M-4+L-5 Mapping+Doku+tick_ms), `e5f8f86`
(M-5+M-6 Test-Luecken), `29d23bb` (L-1+L-3+L-4+L-6+L-7 Style/
Pattern), plus Welle-5-Closure-Commit (ADR 0019 + ADR 0020
→ Accepted, §1 Status-Sync auf Welle 6).

**Belege:**

- 705 Unit-Tests gruen (vorher 642 → +52 SmartMeter-Erstwurf
  → +11 Welle-5b-Review-Tests = 705).
- `make gates` cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override (Default-Liste enthaelt
  jetzt alle 5 MVP-Geraete + `core/grid_model`).
- ADR 0019 `Provisional → Accepted`; ADR 0020 `Proposed →
  Accepted` (direkt; Welle-5b-Review-Folge hat den
  Validierungs-Spike geleistet).
- Welle-5b-Review-Befund: 0 Crit / 1 High / 6 Med / 7 Low /
  4 Info; alle Crit/High/Med + 6 Low adressiert (L-2 als
  Reviewer-empfohlener Skip — Code-Duplikation
  `_parse_load_events`/`_parse_load_profiles` akzeptabel),
  I-1..I-4 Forward-Looking.

**Lieferung im Repo:**

- `hexagon/core/grid_model/loads.py` (Welle-5b-Hauptarbeit):
  - `LoadEvent` Frozen-Dataclass (`GG-GRID-004`): `start_s`,
    `duration_s`, `target_device_id`, `power_kw`. Scenario-
    Event-Pfad — wird im Welle-6-TickLoop in `set_power_kw`-
    Commands an `LoadDevice` uebersetzt.
  - `LoadProfile` Frozen-Dataclass (`GG-GRID-003` „Zeitreihen"):
    `tick_values: tuple[Decimal, ...]` plus `target_device_id`.
    Profile-Daten kommen aus bereits eingelesenem CSV/JSON-Text
    oder Scenario-YAML inline; Datei-I/O bleibt Adapter-
    Verantwortung.
  - `parse_csv_profile(text: str) -> LoadProfile` und
    `parse_json_profile(payload: str | Mapping[str, object]) ->
    LoadProfile` als pure Free-Functions. Fehlerfaelle
    (kaputtes Format, fehlende Felder, falsche Typen) geben
    typed `LoadProfileFormatError`-Subklassen aus
    Welle-0a-Codec-Pattern.
  - Annahmen, Grenzen und Parametrisierung in Docstrings +
    Lastenheft-Verweis (analog Welle 5a).
- `hexagon/core/grid_model/snapshot.py` (Welle-5b-Erweiterung):
  - `GridModelSnapshot` traegt zusaetzlich `active_load_events:
    tuple[LoadEvent, ...]` und `active_load_profiles:
    tuple[LoadProfile, ...]`, damit Resume die Scenario-Events
    weiterfuehrt. ADR 0020 §2.x fixiert das Schema.
  - Snapshot-Version bumpt von `1` (Welle 5a) auf `2` (Welle 5b)
    mit Backward-Compat-Lesepfad (v1-Snapshot ohne
    LoadEvents/LoadProfiles ist roundtrip-faehig, LoadEvents
    laden als leeres Tupel).
- `GG-GRID-005..007` (SOLLTE: Inselnetz / Transformatorgrenzen /
  Blindleistung) bleiben **out-of-scope** fuer M2 (siehe §4),
  werden als eigene Open-Triggers angelegt.
- ADR 0020 (`load-profile-and-event-pattern`) `Proposed →
  Provisional` mit Welle-5b-Commit; Schaerfung auf `Accepted`
  mit Welle-5-Closure-Commit.
- Tests:
  - LoadEvent-Roundtrip-Tests (Snapshot-Persistierung).
  - LoadProfile-Roundtrip-Tests + CSV/JSON-Parsing inkl.
    Negativ-Tests (kaputte Datei, falsche Encoding,
    nicht-numerische Werte → typisierter Fehler).
  - Snapshot-Versions-Bump v1→v2 Backward-Compat-Test
    (`from_dict({"version": 1, ...})` produziert ein
    GridModelSnapshot mit leeren LoadEvent/Profile-Tupeln).
  - Integration-Test: Bilanz konsumiert eine LoadProfile-
    Quelle und reproduziert deterministische Frequenz-/
    Spannungsverlaeufe.
- **Welle-5-Closure-Bestandteile** (zusaetzlich zu 5b-Code):
  - ADR 0019 + ADR 0020 auf `Accepted` heben.
  - `Status:`-Header im Slice-Plan auf "Welle 5
    abgeschlossen" ziehen.
  - `Naechster Schritt`: Welle 6 (TickLoop-Integration +
    Demo-Szenario).
- **Welle-5b-Gate-Status**: Default `make gates` cache-frei
  gruen — `core/grid_model` weiterhin ≥ 90 %, plus Test-
  Inkrement (~30..60 neue Tests fuer LoadEvent/LoadProfile/
  CSV-JSON-Parser).

### Welle 6 — TickLoop-Integration + Scenario + MVP-Demo

**Sub-Slicing-Entscheidung (Pre-Start, 2026-05-19):** Welle 6
ist vor dem Start in **6a (TickLoop-Device-Iteration + grid_model
+ TickLoop-Snapshot v1→v2) + 6b (Scenario-Loader-Device-Factory
+ LoadEvent/LoadProfile-Wiring + GridConnection-Auto-Schluss)
+ 6c (MVP-Demo-Szenario + E2E-Tests + Welle-7-Closure-
Vorbereitung)** geteilt. Die §3-Sub-Slicing-Schwellen greifen
**klar**:

- **Drei verschiedene Concerns**: 6a ist Simulation-Core-
  Verdrahtung (TickLoop + Snapshot-Envelope), 6b ist Scenario-
  Adapter-Erweiterung (Device-Factory + Event-/Profile-
  Wiring), 6c ist E2E-Demo (`make test-integration` +
  `mvp_demo.yaml`).
- **Drei verschiedene `make`-Gates**: 6a + 6b nutzen
  `test-unit` + `coverage-gate-critical`; 6c laeuft zusaetzlich
  ueber `test-integration` mit Postgres-Roundtrip — anderer
  Gate-Stack, anderer Review-Fokus.
- **Drei verschiedene ADRs/Schema-Brueche**: 6a fuehrt
  `ADR 0015` (Envelope v1→v2 mit typisiertem Reject) ein; 6b
  erweitert ggf. `ADR 0014` (Battery-Snapshot) implizit ueber
  die TickLoop-Verdrahtung; 6c ist `ADR-frei`, aber bringt
  Lastenheft-`GG-MVP-002`-Akzeptanz mechanisch.
- **Sub-Wellen sind aufeinander aufbauend**: 6a liefert die
  TickLoop-Surface, die 6b mit Scenario-Daten fuettert; 6c
  konsumiert die kombinierte 6a+6b-Surface. Sequenzieller
  Pfad, kein paralleler.

#### Welle 6a — TickLoop-Device-Iteration + grid_model-Update + TickLoop-Snapshot v1→v2 + ADR 0015 (Provisional) (`Done` 2026-05-19)

**Abgeschlossen.** Commits: `27a441f` (Welle-6a-Erstwurf + ADR
0015 Proposed; 716 Unit-Tests) plus Welle-6a-Review-Folge
`ff45c11` (C-1+M-2 set_run_id-Lifecycle + DeviceModel-Protocol-
Erweiterung), `e3909f0` (M-1 Exception-Message + Pflicht-Text),
`f7f21a6` (M-3+M-4 unknown_source-Counter + Decimal-
Localcontext), `da8deef` (M-5+M-6+M-7 from_snapshot-Test +
TickLoopUnknownDeviceTypeError + Import-Pfad), `779fcea` (H-1+
L-3+L-4+L-5 ADR-Forward-Pointer + Style).

**Belege:**

- 719 Unit-Tests gruen (vorher 705 → +11 Welle-6a-Erstwurf
  → +3 Welle-6a-Review-Tests = 719).
- `make gates` cache-frei gruen ohne
  `CRITICAL_COV_TARGETS`-Override.
- ADR 0015 `Proposed → Provisional`. User-Schaerfung in der
  Vor-Implementierung verlagerte den Versions-Bump von
  SnapshotEnvelope auf TickLoop-Snapshot (Schwester-Schemata,
  unterschiedliche Verantwortlichkeiten); Welle-6a-Review-
  Folge ergaenzte zusaetzlich §4-Forward-Pointer fuer
  `device_type`-Protocol-Property.
- Welle-6a-Review-Befund: 1 Crit / 1 High / 7 Med / 6 Low /
  4 Info; alle Crit/High/Med + 4 Low adressiert (L-1, L-2,
  L-6 als Cleanup-Welle deferred — wuerden 5+ Module touchen;
  I-1..I-4 Forward-Looking).

**Lieferung im Repo:**

- `hexagon/core/simulation/tick_loop.py` erweitert:

- **`TickLoop.tick()`-Erweiterung** (`hexagon/core/simulation/
  tick_loop.py`):
  - Geraete werden in stabiler Reihenfolge aufgerufen
    (Scenario-Device-Definitionsreihenfolge ⇒ kanonische
    Liste). Tie-Breaking-Vertrag dokumentiert; Property-Test
    gegen Permutation der `ScenarioDevice`-Eingabereihenfolge
    (analog Welle-3-Scheduler-Property aus M1).
  - `TickResult.emitted_telemetry` ist befuellt mit
    deterministisch nach `(device_id, metric, sequence)`
    sortierten Tupeln.
  - `grid_model.update(...)`-Aufruf nach allen Device-Ticks
    mit aggregierten Power-Werten. Pre-Grid-Restbilanz +
    `grid_connection.power_kw`-Input gehen in
    `imbalance_kw`-Berechnung (ADR 0019 §2.2).
- **`TickLoop.snapshot()`-Erweiterung**:
  - Sub-Snapshots in `SnapshotEnvelope.sub_snapshots`
    zusammengefuehrt:
    - `devices.<device_type>.<device_id>` je Geraete-Instanz
      (5 MVP-Geraete: battery, pv, load, grid_connection,
      smart_meter). Das Typsegment ist Pflicht fuer
      `from_snapshot`-Dispatch, weil die Per-Device-Snapshots
      selbst keinen Device-Typ tragen.
    - `grid_model` (Single-Instance) aus Welle 5 — Schluessel
      ohne `devices.`-Praefix, weil `grid_model` kein Device
      ist.
  - Welle 6a verifiziert, dass alle sechs Snapshot-Quellen aus
    Erfolgskriterium 6 zusammengefuehrt werden (5 Geraete +
    Bilanzmodell).
- **TickLoop-Snapshot-Versionsschritt v1 → v2** (loest F-2
  aus Review-3): das Welle-6a-TickLoop-Snapshot-Mapping
  bekommt sechs neue Sub-Snapshot-Keys; das ist ein
  strukturierender Bruch zum M1-Welle-4-Snapshot.
  `TickLoop.snapshot()["version"]` wird von `1` auf `2`
  gehoben.
  - **Pflicht-Verhalten:** `TickLoop.from_snapshot(state)` auf
    einem v1-TickLoop-Snapshot wirft einen typisierten
    `TickLoopSnapshotVersionError` mit Klartext „TickLoop
    snapshot version=1 wird in M2-Welle-6a nicht mehr gelesen;
    Lauf in M1 abgeschlossen oder Snapshot-Migrations-Slice
    abwarten (M6, `GG-PERSIST-*`)".
  - **Pflicht-Test:** `tests/unit/hexagon/core/simulation/
    test_snapshot_envelope_v1_to_v2.py` baut einen
    v1-TickLoop-Snapshot und erwartet den typisierten Fehler.
    Backward-Compat-Reader ist out-of-scope (M6
    `GG-PERSIST-*`-Migrations-Slice).
- ADR 0015 `TickLoop-Snapshot-v2 im SnapshotEnvelope-Pattern`
  (`Proposed` → `Provisional` mit Welle-6a-Commit; →
  `Accepted` mit Welle-6c-Closure-Commit). Dokumentiert den
  Bruch, fixiert den typisierten Fehler-Vertrag, verweist auf
  M6 fuer Lese-Migrations-Pfade. Strikt nach ADR-Erweiterungs-
  Pattern, kein Supersedes.
- **Bypass-Strategie fuer Trusted-Source-Pfade** (Welle-0b-
  Review M-5): die Welle-0a-Pflicht-Check
  `assert_payload_canonical_compatible` in
  `SnapshotEnvelope.__post_init__` walked rekursiv jeden
  Sub-Snapshot. Bei tiefen Geraete-Snapshots (z. B. Battery
  mit langer Command-Historie) summiert sich das auf O(N) je
  Konstruktor-Aufruf, dazu noch O(N) beim spaeteren
  `canonical_json`-Encoding. Fuer Trusted-Source-Pfade
  (Resume aus einem zuvor byte-validierten Snapshot) ist die
  Pruefung redundant. Welle 6a plant entweder einen optionalen
  `_skip_payload_check=False`-Kwarg am Konstruktor oder einen
  separaten `from_validated_mapping`-Classmethod-Pfad.
  Entscheidung faellt mit ADR 0015; bis dahin bleibt der
  eager-Check unkonditional.
- **Welle-6a-Gate-Status**: `make gates` cache-frei gruen
  ohne `CRITICAL_COV_TARGETS`-Override (Default-Liste
  unveraendert; TickLoop ist Default-Coverage seit M1).

#### Welle 6b — Scenario-Loader-Device-Factory + LoadEvent/LoadProfile-Wiring + GridConnection-Auto-Schluss (`Done` 2026-05-19)

**Abgeschlossen.** Commit `0f1c597` (kombiniert
Welle-6b-Implementation + Welle-6b-Review-Folge: 14 Findings
abgearbeitet ohne Supersede-ADR, Schaerfung-Pattern). Stand:
761 Unit-Tests gruen (vorher 731 → +30 Welle-6b-Tests),
critical-domain branch coverage 91.35% (`coverage-gate-critical`).
ADR 0021 `Proposed → Provisional`.

- **Scenario-Loader-Device-Factory** (`hexagon/core/scenario/
  loader.py`-Erweiterung):
  - Bisher hielt der Scenario-Loader `ScenarioDevice`-Mappings
    als Daten; Welle 6b instantiiert daraus konkrete
    `DeviceModel`-Implementationen (`BatteryDevice`, `PvDevice`,
    `LoadDevice`, `SmartMeterDevice`, `GridConnectionDevice`).
  - Factory-Dispatch nach `ScenarioDevice.type` — fehlende
    Types liefern typisierten Fehler (Welle-2/3/4-Review-
    Pattern).
  - `GG-SCN-001`-Akzeptanz.
- **LoadEvent/LoadProfile-Wiring zum TickLoop**:
  - Scenario-YAML-Format-Erweiterung um `events:` und
    `load_profiles:` Sektionen (`GG-GRID-003`/`004`-Pfade
    aus Welle 5b).
  - Scenario-Loader parst `events` zu `LoadEvent`-Tupel und
    `load_profiles` zu `LoadProfile`-Tupel (via
    `parse_csv_profile`/`parse_json_profile` aus
    `grid_model/loads.py` — die Datei-I/O-Adapter-Schicht
    liest die Profil-Dateien und reicht Text/Mapping durch).
  - TickLoop konsumiert pro Tick aktive Events/Profiles und
    uebersetzt sie in `LoadDevice.apply_command(set_power_kw,
    value=...)`-Aufrufe (ADR 0020 §2.2 / §2.3).
  - Restore nach Event-Ablauf: `set_power_kw(rated_power_kw)`
    (ADR 0020 §2.2).
- **GridConnection-Auto-Schluss** (ADR 0019 §6 / ADR 0017
  §2.2):
  - TickLoop berechnet `pre_grid_residual_kw = pv - load -
    battery` und setzt `grid_connection.power_kw :=
    -pre_grid_residual_kw` (Ideal-Schluss).
  - Falls Scenario-Event den `grid_connection`-Wert manuell
    setzt (z. B. `set_power_kw`-Command aus YAML-Event):
    Manual-Path nimmt Vorrang; Auto-Schluss-Pfad wird
    uebersprungen.
  - Cap-Limit (`max_import_kw`/`max_export_kw`) bleibt durch
    ADR 0017 §2.4 enforced — wenn der Auto-Schluss den Cap
    sprengt, wird der Wert clamped und der Restposten geht
    in die `imbalance_kw`-Berechnung (Frequenz/Spannungs-
    Drift).
- ADR 0014 `Battery`-Snapshot-Schema-Verweise im TickLoop-
  Code (Welle-2-Closure hat ADR 0014 bereits `Accepted`
  gemacht; Welle 6b ergaenzt nur die TickLoop-Verdrahtung).
- **Welle-6b-Gate-Status**: `make gates` cache-frei gruen
  (Stand 2026-05-19: 761 Unit-Tests, branch coverage 91.35%
  ueber `coverage-gate-critical`). Test-Anzahl-Inkrement
  Welle 6a→6b: +29 Tests (12 TickLoop-6b + 12 Loader-6b +
  3 LoadDevice-rated_power_kw + 2 Factory-Sync).
- **Welle-6b-Review-Folge** (2026-05-19): 14 Findings (4 High,
  7 Medium, 3 Low, 1 Niedrig) abgearbeitet ohne Supersede-ADR
  (Schaerfung-Pattern). Kern-Inkremente:
  - **H-1 Cap-Limit/Auto-Schluss**: Test pinnt
    `imbalance_kw`-Restposten bei `max_export_kw`-Clamp
    (ADR 0021 §2.7 Klausel „Cap-Limit-Respekt").
  - **H-2 Baseline-Force-Reset**: TickLoop besitzt
    `set_power_kw` an LoadDevices exklusiv. Externe
    `apply_command` zwischen Ticks wird im Folge-Tick durch
    `rated_power_kw` ueberschrieben — Pflicht-Test +
    Code-Kommentar im Helper.
  - **H-3 Profile/Event-Clock-Desync**: Event-Window-Check
    nutzt jetzt `tick_start_ms = now - tick_ms`, nicht
    `now`. Pflicht-Tests fuer beide Half-Open-Boundaries
    (`start_s=0, duration_s=1` aktiv im ersten Tick;
    abgelaufen im zweiten).
  - **H-4 Validator + parse_*-Helfer**: `validator.py` prueft
    optionale `grid_model`-/`load_events`-/`load_profiles`-
    Top-Level-Sektionen typisiert; `loader.py` erweitert um
    `parse_load_events`, `parse_load_profiles`, internem
    `_parse_grid_model_config`. `_build_scenario` reicht die
    drei neuen Felder durch.
  - **M-1 Set→List-Determinismus**: `manual_override_grid_ids`
    ist jetzt `list[str]` mit Dedup-Append (verhindert
    Hash-basierte Iteration-Drift).
  - **M-2 Baseline-Cache**: `_load_baseline_by_id` einmal in
    `__init__` materialisiert.
  - **M-6 Overlay-Target-Validierung**: neue
    `ScenarioInvalidLoadTargetError` blockt LoadEvent/Profile
    auf PV/Battery/SmartMeter-Targets im Builder.

#### Welle 6c — MVP-Demo-Szenario + E2E-Tests + Welle-6-Closure (`Done` 2026-05-20, Commits `8a3aa2f` + `c31052c`)

- **`tests/integration/scenarios/mvp_demo.yaml`** als
  End-to-End-Szenario (`GG-MVP-002`-Pflicht):
  - `tick_ms=1000` (M1-Konsistenz, lesbar in CI).
  - Eingefrorene Seed-Konstante in den Test-Helfern
    (`M2_DEMO_SEED` in `tests/integration/_constants.py`
    oder Conftest, Wert z. B. `0xC0FFEE`).
  - 5 MVP-Geraete + `grid_model`-Bilanz + 1 Beispiel-
    `LoadEvent` + 1 Beispiel-`LoadProfile`-Profil-Datei.
- **`make test-integration`** startet das Szenario
  **zweimal** mit der gleichen Konstante und verifiziert
  byte-identische `TickResult.emitted_telemetry`-Folge ueber
  **mindestens 100 Ticks** (einheitlich mit
  Erfolgskriterium 4) plus persistierte `runs`-Zeile.
  Zweite-Lauf-Pflicht schliesst die Reproduzierbarkeits-
  Spalte fuer CI-Audits.
- **TickLoop-Property-Test**: Permutation der
  `ScenarioDevice`-Eingabereihenfolge erzeugt byte-identische
  Telemetry (Welle-3-Scheduler-Property-Pattern).
- **Welle-6-Closure-Bestandteile** (zusaetzlich zu 6c-Code):
  - ADR 0015 (Envelope v1→v2) auf `Accepted` heben.
  - `Status:`-Header im Slice-Plan auf "Welle 6
    abgeschlossen" ziehen.
  - `Naechster Schritt`: Welle 7 (Closure).
- **Welle-6c-Gate-Status**: `make fullbuild` gruen ohne
  jeden Override (M2-Erfolgskriterium 2).

#### Welle-6-Gate-Erwartung (Sub-Welle-uebergreifend) — `Done` 2026-05-20

- Default-`CRITICAL_COV_TARGETS` blieb unveraendert (alle
  5 MVP-Geraete + `core/grid_model` + M1-Spine sind seit
  Welle 5b drin); `core/scenario` ist seit Welle 6a Bestandteil.
- ADR 0015 (Snapshot-Envelope v2) und ADR 0021 (Scenario-Loader
  + TickLoop-Event-Wiring) sind mit Welle-6c-Closure (`c31052c`)
  auf `Accepted` gehoben — keine vererbten Review-Punkte
  (Welle-6c-Run war in einem `feat`-Commit, ohne separate
  Review-Folge).
- `make fullbuild` cache-frei gruen ohne Override am
  2026-05-20 (`c31052c`).

### Welle 7 — Closure (1/2 Tag)

- ADR 0013 + ADR 0014 + ADR 0015 + ADR 0016 + ADR 0017 +
  ADR 0018 `Accepted` (wenn noch `Provisional`). ADR 0013/
  0014/0016 sind bereits in Welle 1/2/3 `Accepted`; ADR 0015
  schliesst mit Welle 6 (Envelope v1→v2); ADR 0017/0018
  schliessen mit Welle 4b-Closure und werden in Welle 7 nur
  verifiziert.
- Trigger 013 (`replay-diff-tick-ms-parameter`) ist bereits in
  Welle 2 mechanisch geschlossen (siehe Battery-Pflicht-Test
  `test_replay_diff_tick_ms.py`). Welle 7 verifiziert nur, dass
  die Closure-Notiz in `done/013-…md` liegt; faellt sonst aus.
- `done/M2-devices.md` Closure-Notiz + `done/M2-devices-results.md`
  Welle-Tabelle analog `done/M1-tick-loop-results.md`.
- `roadmap.md`: M2 auf `Done`, M2-DoD-Checkboxen
  aktivieren, `Naechster aktiver Slice: M3` setzen.
- Out-of-Scope-Restposten als Open-Triggers vermerkt:
  `GG-DEV-015..018` (SOLLTE-Geraete: EV-Charger,
  Transformer, Wind, Diesel), `GG-GRID-005..007`
  (SOLLTE-Netz: Inselnetz, Transformatorgrenzen, Blindleistung),
  `GG-BESS-006`/`007` (SOLLTE-Battery: Temperatur, Zellspannung).
- M2-Welle-7-End-to-End-Sweep (analog M1-Welle-7 §7): Reviewer-
  Stempel je Welle, S-1..S-6-Verification ist Pflicht-Punkt.

## 4. Out-of-Scope (bleibt fuer M3+ oder eigene Triggers)

- **Fault Injection** (`GG-FAULT-001..010`) — M3. Geraete-
  Schnittstelle (z. B. `BatteryDevice.inject_fault(...)`) wird
  in M2 *nicht* praeventiv vorgesehen; `RandomPort.sub_port`-
  Konvention reicht fuer M3-Aktivierung.
- **Multi-Agent-Subsystem** (`GG-AGENT-001..008`) — M3.
- **OpenTelemetry-Tracing** (`GG-OTEL-001..004`) — M3.
- **Protokolladapter** (MQTT/Modbus/OPC-UA/DNP3/IEC) — M4.
- **UI / Demo-Seite** (`GG-UI-001..009`, Demo-System aus §24) —
  M5. M2 liefert nur das Demo-*Szenario* (`mvp_demo.yaml`), nicht
  die Demo-Seite.
- **SOLLTE-Geraete** `GG-DEV-015..018` (EV-Charger, Transformer,
  Wind, Diesel) — eigene Slices nach M2-Closure.
- **SOLLTE-Netz** `GG-GRID-005..007` (Inselnetz,
  Transformatorgrenzen, Blindleistung) — eigene Slices.
- **SOLLTE-Battery** `GG-BESS-006`/`007` (Temperatur,
  Zellspannung) — Trigger nach M2-Closure (Telemetry-Metriken-
  Erweiterung ist additiv und kann jederzeit folgen).
- **Performance-Benchmarks** (`GG-RT-004`/`005`) — M6.
- **SBOM-Generierung** (Trigger 008) — M6.

## 5. Risiken und Fallback

- **Trigger-014-Refactor brennt Welle-0**: die Generalisierung
  von fuenf `*SnapshotFormatError`-Hierarchien gleichzeitig kann
  Welle-1..5-Tests rot machen, wenn ein Alias falsch
  weiter-verdrahtet ist. *Fallback:* Welle 0 in 0a (Codec-Basis +
  Aliase) und 0b (Free-Function-Migration) teilen — siehe
  Sub-Slicing-Schwelle in §3.
- **Trigger-015-Image-Refactor verlangsamt CI**: `uv sync
  --no-editable` baut Wheels statt Editable-Links — moeglicher-
  weise spuerbar laenger. *Fallback:* Build-Cache-Layer im
  Dockerfile-Stage einziehen, ggf. `--mount=type=cache`. Falls
  zu invasiv: Trigger 015 in 0b (Shebang-Rewrite only) und 0c
  (Base-Image-Strategie) teilen.
- **Default-Gate-Sprung in Welle 2 verfehlt**: wenn `devices/
  battery` < 90 % Coverage erreicht, M2-Welle-2-Closure muss in
  2a/2b/2c aufgespalten werden bis Default-Gate gruen. Niemals
  M1-Override-Pattern wiederholen (S-3-Direktive).
- **`DeviceModel`-Protocol vs. Driving-Port-Wahl unklar**:
  Welle 1 muss entscheiden, ob `DeviceModel` als
  `hexagon/core/devices/_protocol.py` (Core-internes Protocol)
  oder als `hexagon/ports/driving/device.py` (Driving-Port)
  liegt. *Fallback:* die Welle-1-PR entscheidet via ADR 0013;
  `AC-HEXAGON-PURE` und `AC-PORTS-NO-OUT` schliessen Driven-
  Port aus.
- **Demo-Szenario hat keinen UI-Konsumenten in M2**: `GG-MVP-002`
  verlangt Live-Telemetrie ueber API. *Fallback:* M2-Demo-
  Verifikation reicht ueber `make test-integration` + Postgres-
  Roundtrip; UI-Konsum kommt mit M5.
- **`SnapshotEnvelope`-Sub-Snapshots brechen Welle-4-M1-Format**:
  Welle 6 erweitert das TickLoop-Snapshot-Mapping um sechs
  neue Keys — fuenf unter
  `devices.<device_type>.<device_id>` plus einen
  `grid_model`-Single-Instance-Key. *Fallback:* der Bruch ist
  im Plan bereits als Pflicht-Schritt verankert (siehe Welle 6
  „TickLoop-Snapshot-Versionsschritt v1 → v2") —
  `TickLoop.snapshot()["version"]` zaehlt auf `2` hoch,
  v1-Snapshots werfen typisierten
  `TickLoopSnapshotVersionError` (Fail-Fast, kein
  Backward-Read). ADR 0015 fixiert den Vertrag; ein Lese-
  Migrations-Pfad ist explizit M6 (`GG-PERSIST-*`).
- **`grid_model` vs. `grid_connection` Naming-Drift**: das
  Bilanzmodell (Welle 5, `hexagon/core/grid_model/`) und der
  Geraetetyp `grid_connection` (Welle 4a,
  `hexagon/core/devices/grid_connection/`) sind sprachlich nah,
  aber strukturell verschieden — Geraet vs. Systemmodell. Risiko:
  Code-Review mischt die beiden in Welle 4a/5 versehentlich.
  *Fallback:* Welle 4a Code-Review-Checkliste enthaelt einen
  expliziten Punkt „`grid_connection` ist Device, `grid_model`
  ist Systemmodell — keine Cross-Imports". `AC-HEXAGON-PURE`
  faengt das nicht ab; nur Review/Naming-Disziplin schuetzt.

## 6. Wandert nach

- ✓ `in-progress/M2-devices.md` — vollzogen 2026-05-18 mit
  Welle-0a-Start (Trigger 014, generic snapshot codec).
- `done/M2-devices.md` mit Closure-Notiz nach Welle 7.
- Eventueller `archive/`-Pfad, falls M2 umgeplant wird (z. B.
  vorgezogenes M3 wegen Audit-Befund).

Forwarder-Stubs bleiben nur dann liegen, wenn `Accepted`-ADRs
auf den `next/`- oder `in-progress/`-Pfad zeigen (Immutability
nach ADR 0006 §3).

## 7. Verifikationspfad

| Erfolg                                                                       | Verifikation (Dockerfile-Stage via `make <target>`)                                                                                  |
| ---------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------ |
| Generischer Snapshot-Codec + Alias-Migration                                 | `make test-unit` mit bestehenden M1-`*SnapshotFormatError`-Tests gruen + neue Codec-Tests                                              |
| Trigger-015-Image-Hardening                                                  | `make fullbuild` ohne `PYTHONPATH`/`python -m`-Indirection am api-Service; `apt-get upgrade -y` bleibt als Trigger-015-Option-A; `entrypoint: []` ist nur am `simulation`-Stub-Service zulaessig (Welle-6c-Erbe). |
| `DeviceModel`-Protocol-Contract                                              | `make test-unit` mit Protocol-Adherence-Test (`NullDevice`)                                                                          |
| Battery-Akzeptanz (`GG-BESS-001..005`/`008`)                                  | `make test-unit` + `hypothesis @given(seed=integers())`-Property (seed-stabile SOC-Spur ueber ≥ 100 Ticks)                            |
| **Default `make gates` ohne `CRITICAL_COV_TARGETS`-Override gruen**          | `make gates` (Default-Liste aus Dockerfile-Default; `devices/battery` ≥ 90 %)                                                         |
| PV/Load/SmartMeter/GridConnection-Smoke-Tests                                | `make test-unit` (`GG-DEV-011..014` Akzeptanz)                                                                                       |
| `DeviceModel`-Snapshot-Versionierung pro Geraet (5 Stueck)                    | `make test-unit` Protocol-Adherence-Test je Geraet (`BatteryDevice`, `PvDevice`, `LoadDevice`, `SmartMeterDevice`, `GridConnectionDevice` — jeweils `version: int`-Erst-Feld + `from_snapshot(snapshot()) == device` byte-stabil) |
| `grid_model`-Snapshot-Versionierung                                          | `make test-unit` Snapshot-Roundtrip-Test `GridModelSnapshot` (`version: int`-Erst-Feld + byte-stabiler Roundtrip; **kein** Protocol-Adherence-Test, da kein `DeviceModel`) |
| Netzbilanz-Determinismus                                                     | `make test-unit` Property-Test via `hypothesis @given(seed=integers())` (seed-stabile Leistungsbilanz vs. Frequenz)                  |
| Demo-Szenario `mvp_demo.yaml` deterministisch                                | `make test-integration` mit `mvp_demo.yaml` (`tick_ms=1000`, Seed-Konstante `M2_DEMO_SEED`); zweifacher Lauf → byte-identische `emitted_telemetry` **ueber ≥ 100 Ticks**; Postgres-Roundtrip |
| TickLoop-Snapshot v1 → v2 Schema-Bump (Fail-Fast)                             | `make test-unit` mit `test_snapshot_envelope_v1_to_v2.py` — v1-TickLoop-Snapshot wirft typisierten `TickLoopSnapshotVersionError`      |
| `make fullbuild` gruen ohne Override                                         | `make fullbuild` — **M2-Abschluss-Gate**                                                                                              |
| Trigger 013 (`replay-diff-tick-ms-parameter`) geschlossen                    | `make test-unit` mit Battery-Pflicht-Test `test_replay_diff_tick_ms.py` (`tick_ms=100`, `diff_replay(..., tick_ms=100)`)             |
| Trigger 014 + 015 nach `done/`                                                | `docs/plan/planning/done/014-…md`, `015-…md` mit Closure-Notiz                                                                       |
| Trigger 013 nach `done/`                                                      | `docs/plan/planning/done/013-…md` mit Closure-Notiz (synchron mit Battery-Welle-2-Test oben)                                          |
| ADR 0013 (`DeviceModel`) + ADR 0014 (`Battery`-Snapshot-Schema) + ADR 0015 (Envelope v1→v2) + ADR 0016 (PV+Load) + ADR 0017 (GridConnection) + ADR 0018 (SmartMeter) + ADR 0019 (Grid-Model-Bilanz) + ADR 0020 (Load-Profile + Event) `Accepted` | `docs/plan/adr/0013-device-model-protocol.md`, `0014-battery-snapshot-schema.md`, `0015-snapshot-envelope-v2.md`, `0016-pv-load-device-pattern.md`, `0017-grid-connection-device-pattern.md`, `0018-smart-meter-device-pattern.md`, `0019-grid-model-bilanz-pattern.md`, `0020-load-profile-and-event-pattern.md` jeweils mit `Accepted`-Status |
