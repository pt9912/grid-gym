# Welle 5c — M6 SOLLTE-Items + IP/Netz-Beschraenkung (`GG-SAFE-005/006` + Demo-Compose)

**Status:** In Progress — C0 (Slice-Doc-Anlage; dieser Commit).
Welle 5 wird gemaess Welle-5a-D-1 in **5a (Quality-Pipeline-
Audit; `GG-SAFE-001..004` MUSS) + 5b (Sim/Prod-Marker + Input-
Validation; `GG-SAFE-007/008` MUSS) + 5c (SOLLTE-Items + IP/
Netz-Beschraenkung; `GG-SAFE-005` + `GG-SAFE-006` + Demo-
Compose-Hardening)** sub-geslict. Welle 5c ist die **dritte
und letzte Sub-Welle** und schliesst Welle 5 (alle `GG-SAFE-*`
+ Demo-Compose-IP/Netz-Auflage).

**Pre-C0 abgeschlossen (M6-Welle-5b-Closure-Folge):**

- C4a `33c238c` — `git mv M6-welle-5b.md → done/` (Self-
  Close-Move, rename-only).
- C4b `06a20c3` — Cross-Doc-Refs-Sync nach Move + Hash-Slot-
  Fills. **Welle 5b komplett**: 6 Inline-Fixes + `_BaseRequest`-
  Mixin + 11 Smokes + Audit-Doku + NEU ADR 0045
  `Provisional`; Stack `0d3bb61..06a20c3`.

**Pre-C0-Audit-Korrektur (C0-Review-Folge 4 Findings 2 MEDIUM
+ 2 LOW):** der ursprueng­liche Pre-C0-Audit hatte falsch
behauptet, `GG-SAFE-005/006` seien nicht bzw. nur partiell
implementiert. Tatsache (per Code-Verifikation):

- `GG-SAFE-005` ist per Lastenheft-Traceability Z. 2291
  ausdruecklich auf **M2 `BatteryDevice.apply_command` /
  Sicherheitsgrenzen-Validierung** gemapped — produktiv.
- `GG-SAFE-006` Substanz lebt in
  `src/grid_gym/hexagon/core/replay/diff.py::diff_replay()`
  mit `volatile_fields`, `ReplayDelta.tick`/`path`/
  `classification` (M5-Welle-5-Review SC-1) — produktiv.

Damit dreht die Welle-5c-Lieferform von „Audit-Doku
nicht/partial implementiert + NEU Trigger 036" auf „Audit-
Doku **produktiv** mit Substanz-Pfaden + Test-Pfaden", analog
Welle 5a/5b. Trigger 036 entfaellt; Decisions D-2/D-3
entsprechend umgeschrieben.

**Spec-Reife:** Inhaltlich final fuer Welle 5c. Welle-5c-
Decision-Liste (§3) schliesst Welle-5c-D-1..D-6: Audit-Form,
`GG-SAFE-005`-Audit-Form, `GG-SAFE-006`-Audit-Form, Demo-
Compose-Port-Bind-Form, Hardening-Scope, ADR-Bedarf.

---

## 1. Context

`GG-SAFE-005/006` SOLLTE (Lastenheft Z. 1380-1393) plus IP-/
Netz-Beschraenkung im Demo-Compose (`GG-DEPLOY-011` Lastenheft
Z. 1913-1920):

- **`GG-SAFE-005`**: Die Plattform SOLLTE sichere Fallback-
  Zustaende unterstuetzen. **Akzeptanz:** Wenn Fallback-
  Zustaende implementiert sind, dokumentiert jeder betroffene
  Geraetetyp Ausloeser, Zielzustand, Telemetrie und Recovery-
  Verhalten. **Lastenheft-Traceability** (Z. 2291): Realisiert
  ueber **`BatteryDevice.apply_command` / Sicherheitsgrenzen-
  Validierung**.
- **`GG-SAFE-006`**: Nichtdeterministische Simulationslaeufe
  SOLLTEN erkannt werden. **Akzeptanz:** Wenn Erkennung
  nichtdeterministischer Laeufe implementiert ist, meldet die
  Plattform Replay-Diff, volatile Felder, betroffene Ticks
  und Abweichungsklassifikation maschinenlesbar.
  **Lastenheft-Traceability** (Z. 2292): Realisiert ueber
  **Replay-Diff-Status-Markierung mit Replay-Source-
  Integration**.
- **`GG-DEPLOY-011`** (Lastenheft Z. 1913-1920): Simulations-
  und Abnahmelaeufe MUESSEN ohne externe Netzwerkverbindungen
  ausfuehrbar sein. **Akzeptanz:** ein vollstaendiger Demo-/
  Abnahmelauf inkl. Replay, Fault-Injection und Persistenz
  laeuft ohne aktive Netzwerkverbindungen ausserhalb des
  lokalen Host-/Container-Netzwerks.

### 1.1 Existierende Substanz (Pre-C0-Audit, Code-verifiziert)

**`GG-SAFE-005` — Geraete-Fallback-Verhalten via Sicherheits-
grenzen-Validierung** (✓ produktiv):

- `BatteryDevice.apply_command` mit Pure-Function
  `validate_command` in `hexagon/core/devices/battery/
  commands.py`: bei Wert ausserhalb `[-max_discharge_kw,
  max_charge_kw]` → Power-Clamp + Alarm
  `(result=LIMITED, limit=clamped_value, limit_unit="kW")`;
  bei SOC-Boden + Wert < 0 oder SOC-Decke + Wert > 0 → Alarm
  `(result=REJECTED, limit=min_soc_pct/max_soc_pct,
  limit_unit="%")`, Soll-Wert unveraendert. Geraet faellt auf
  den letzten gueltigen Soll-Zustand (= sicherer Default-
  Zustand) zurueck.
- Analoge Sicherheitsgrenzen + Power-Clamp-Substanz in
  `hexagon/core/devices/load/commands.py` (Load) und
  `hexagon/core/devices/grid_connection/commands.py`
  (GridConnection): pro Geraetetyp eigene Bounds + Alarm-
  Emission.
- Telemetrie + Alarm-Emission-Pfad ist `M3` Welle-2-Substanz
  (ADR 0022/0025): `LIMITED`/`REJECTED`-Outcomes traversieren
  den Alarm-Pipeline-Pfad bis zum `AlarmStreamPort`.
- Recovery-Verhalten: bei naechstem `apply_command` innerhalb
  der Bounds → `result=ACCEPTED`, Geraet uebernimmt den neuen
  Soll-Wert.

**`GG-SAFE-006` — Replay-Diff-Klassifikation mit Volatile-
Field-Vokabular und Tick-Skala** (✓ produktiv):

- `src/grid_gym/hexagon/core/replay/diff.py::diff_replay(
  expected, actual, *, tick_ms, volatile_fields)` vergleicht
  zwei `ReplaySample`-Sequenzen feldweise und liefert eine
  `tuple[ReplayDelta, ...]` mit:
  - **`ReplayDelta.path`** (z. B. `"sample[i].timestamp"`) —
    welches Feld differiert.
  - **`ReplayDelta.tick`** (`int = simulation_time // tick_ms`)
    — auf welchem Tick die Divergenz auftritt.
  - **`ReplayDelta.classification`**
    (`ReplayDeltaClassification` StrEnum mit `FACHLICH` /
    `VOLATIL`) — semantische Klassifikation.
  - **`volatile_fields`-Konfiguration** als
    `frozenset[str]`-Parameter; Default
    `_VOLATILE_FIELDS_DEFAULT = frozenset({"import_sequence"})`
    (M5-Welle-5-Review SC-1 verankert), pro Aufrufer
    override-bar.
- Test-Coverage `tests/unit/hexagon/core/replay/test_diff.py`
  verriegelt das Verhalten: Klassifikation-Equality,
  Tick-Berechnung, Volatile-Field-Aufweichung, Custom-Override.
- Lastenheft-Akzeptanz „Replay-Diff, volatile Felder,
  betroffene Ticks und Abweichungsklassifikation maschinen-
  lesbar" → alle vier Komponenten ✓ produktiv.

**`GG-DEPLOY-011` Demo-Compose IP-/Netz-Beschraenkung:**

- `deploy/compose.yml` Z. 104 `api`-Service: `ports: -
  "8000:8080"` (Short-Form ohne IP-Praefix) → laut Docker-
  Compose-Konvention bindet auf **alle Host-Interfaces
  (0.0.0.0)**. Restriktive Form waere `"127.0.0.1:8000:8080"`.
- Anmerkung zu `GRID_GYM_HOST: 0.0.0.0` im `api`-Service
  (Z. 84): das ist die **container-interne** uvicorn-Binding-
  Konfig, damit das Docker-Compose-Network den `api`-Container
  ueber den Sibling-Hostname erreichen kann. Standard-Pattern,
  **keine** Security-Lücke; die externe Sichtbarkeit wird
  ausschliesslich ueber die `ports:`-Klausel kontrolliert.
- `GG-DEPLOY-011`-Akzeptanz „Demo laeuft ohne externe
  Netzwerkverbindungen ausserhalb des lokalen Host-/Container-
  Netzwerks": aktuell faktisch erfuellbar (lokal-only-Lauf
  funktioniert), aber das `0.0.0.0`-Bind ist die Lastenheft-
  Auflage-Verletzung im engeren Sinn.

### 1.2 Welle-5c-Lieferziel

**Audit + Hardening-Welle** (Pattern analog Welle 5a/5b):

1. **NEU `docs/user/safe-005-006-fallback-determinism.md`**
   (Welle-5c-C2) — Audit-Tabelle:
   - **`GG-SAFE-005`**: ✓ **Produktiv** ueber Sicherheits-
     grenzen-Validierung + Power-Clamp in Battery/Load/
     GridConnection `apply_command` mit Alarm-Emission;
     Lastenheft-Traceability Z. 2291.
   - **`GG-SAFE-006`**: ✓ **Produktiv** ueber `diff_replay()`
     mit `volatile_fields`/`tick`/`path`/`classification`;
     Lastenheft-Traceability Z. 2292; Test-Pfad
     `tests/unit/hexagon/core/replay/test_diff.py`.

2. **`deploy/compose.yml` Port-Bind-Hardening** (Welle-5c-C2)
   — `api`-Service `ports`-Klausel umstellen auf
   `"${GRID_GYM_DEMO_HOST_BIND:-127.0.0.1}:8000:8080"`;
   `GRID_GYM_DEMO_HOST_BIND`-ENV-Variable als Override-Pattern
   fuer Maintainer-Bedarf „externe Sichtbarkeit explizit
   aktivieren". Default bleibt strikt loopback-only und
   befriedigt `GG-DEPLOY-011` formal.

3. **NEU `docs/user/demo-compose-hardening.md`** (Welle-5c-
   C2) — Maintainer-Doku, wie der Demo-Compose ge-hardened
   ist + wie der ENV-Override-Pfad genutzt wird.

4. **NEU 4-5 Integration-Smokes** (Welle-5c-C2):
   - `test_safe_005_battery_safety_bounds_emit_limited`:
     End-to-End-Smoke gegen `BatteryDevice.apply_command` mit
     Wert ausserhalb Bounds → `result=LIMITED` + Alarm.
   - `test_safe_005_battery_soc_floor_rejects`:
     Schwester-Smoke fuer SOC-Boden-Reject.
   - `test_safe_006_diff_replay_classifies_volatile_and_
     fachlich`: End-to-End-Smoke gegen `diff_replay` mit
     Mismatch in `import_sequence` (`VOLATIL`) + Mismatch
     in `timestamp` (`FACHLICH`); pinnt die Klassifikation.
   - `test_safe_006_diff_replay_pins_tick_and_path`:
     Schwester-Smoke fuer `tick`-Berechnung +
     `path`-Format.
   - `test_compose_ports_loopback_bound_by_default`:
     `deploy/compose.yml` `api`-Service `ports`-Klausel
     enthaelt `127.0.0.1`-Default oder
     `GRID_GYM_DEMO_HOST_BIND`-Override-Pattern (Quell-
     Datei-Inspektion; analog Welle-5b-WS-Subscribe-only-
     Pattern).

### 1.3 Welle-5c-Anti-Scope

- **Keine NEU Fallback-Implementation** an Geraeten — Welle
  5c verifiziert + dokumentiert die bestehende Sicherheits-
  grenzen-Substanz, sie wird **nicht** erweitert.
- **Keine NEU `diff_replay`-Erweiterung** — die existierende
  Substanz (M5-Welle-5-Review SC-1) erfuellt die Lastenheft-
  Akzeptanz; keine zusaetzlichen Felder oder
  Klassifikations-Kategorien.
- **Kein Container-Hardening jenseits Port-Bind** (Read-only-
  Filesystem, User-Capabilities, Healthcheck-Pollung-Pattern,
  ...) — `GG-DEPLOY-*`-Substanz ist M6-Welle-6-Scope.
- **Keine Multi-User-/Auth-Implementation** — strukturell
  ausgeschlossen per Lastenheft Z. 1161-1163 +
  `carveouts.md §2.7`.
- **Kein NEU `open/`-Trigger** — beide SAFE-Items sind voll
  abgedeckt; kein Folge-Pfad anzulegen (Pattern-Drift gegenueber
  Welle 5a/5b waere Anti-Scope, wenn keine Lücke vorliegt).
- **Kein NEU ADR** — D-6 schliesst Schaerfungs-Bedarf negativ
  aus.
- **Kein NEU Code im Core** — Audit-Doku + Compose-Edit +
  Smokes.

---

## 2. Scope

Welle 5c liefert **vier Items** ueber 3 Commits (C0..C3),
plus Self-Close-Folge C4a/C4b.

1. **Slice-Doc-Anlage** (C0, dieser Commit) — dieses Dokument;
   `in-progress/README.md` Aktive-Welle-Block auf 5c;
   `M6-perf-security-cicd.md §3.1` Welle-5c-Zeile
   `Pending → In Progress 2026-06-07`;
   `roadmap.md §3 M6` aktive Welle auf 5c.
2. **C1 entfaellt** — Welle-5c-D-6 schliesst ADR-Bedarf
   negativ aus (Pattern analog Welle 5a / M5-Welle-2).
3. **Code-/Doku-Substanz** (C2) — NEU `docs/user/safe-005-
   006-fallback-determinism.md` + NEU `docs/user/demo-
   compose-hardening.md` + `deploy/compose.yml`-Port-Bind-
   Hardening + NEU `tests/integration/test_m6_welle_5c_safe_
   005_006_compose_smoke.py` (5 Smokes). Lokal-Verifikation
   alle Gates gruen.
4. **Status/DoD-Sync** (C3) — Status-Flip + Welle-5-
   Subdivision-komplett-Notiz; aktive Welle auf Welle 6.

Self-Close-Folge C4a/C4b laufen nach C3 als M6-Welle-6-Pre-
C0a/Pre-C0b.

---

## 3. Architektur-Entscheidungen (Welle-5c-Decision-Liste)

### Welle-5c-D-1 — Audit-Form

**Frage:** Wie wird die GG-SAFE-005/006-SOLLTE-Akzeptanz
audited?

**Welle-5c-Final: Option C (Doku + Smoke-Tests).** Pattern-
Konsistenz mit Welle 5a + 5b; Smoke-Tests sind CI-Sensor
gegen Drift, Doku ist Audit-Trail fuer Reviewer.

### Welle-5c-D-2 — `GG-SAFE-005`-Audit-Form

**Frage:** Wie wird die produktive Sicherheitsgrenzen-Substanz
in der Audit-Doku verankert?

**Welle-5c-Final: Audit-Doku „✓ produktiv per Lastenheft-
Traceability Z. 2291" mit Substanz-Pfad + Test-Pfad + Pro-
Geraet-Pflicht-Felder (Ausloeser, Zielzustand, Telemetrie,
Recovery-Verhalten) tabellarisch dokumentiert.**

Begruendung:

- Lastenheft Z. 2291 mapped GG-SAFE-005 ausdruecklich auf
  `BatteryDevice.apply_command` + Sicherheitsgrenzen.
- Lastenheft-Akzeptanz fordert „dokumentiert jeder
  betroffene Geraetetyp Ausloeser, Zielzustand, Telemetrie,
  Recovery-Verhalten" — Welle-5c-C2-Audit-Doku liefert genau
  dieses Mapping pro Geraet (Battery, Load, GridConnection).
- Analoge Substanz an Load/GridConnection wird mit-erfasst,
  damit der Audit nicht Battery-eng wird.

### Welle-5c-D-3 — `GG-SAFE-006`-Audit-Form

**Frage:** Wie wird die produktive `diff_replay`-Substanz in
der Audit-Doku verankert?

**Welle-5c-Final: Audit-Doku „✓ produktiv per Lastenheft-
Traceability Z. 2292" mit Substanz-Pfad
(`hexagon/core/replay/diff.py`) + Domain-Type-Pfad
(`hexagon/core/domain/replay.py`) + Test-Pfad
(`tests/unit/hexagon/core/replay/test_diff.py`) +
Akzeptanz-Komponenten-Mapping (Replay-Diff →
`tuple[ReplayDelta,...]`; volatile Felder → `volatile_fields`;
betroffene Ticks → `ReplayDelta.tick`; Klassifikation →
`ReplayDeltaClassification`).**

Begruendung:

- Substanz lebt seit M5-Welle-5-Review SC-1; M6-Welle-5c
  liefert nur die Audit-Trail-Verankerung.
- Alle vier Lastenheft-Akzeptanz-Komponenten haben eine
  konkrete Code-Stelle — Audit-Doku zeigt das Mapping
  explizit.
- **Kein NEU Trigger 036**: die ursprueng­liche C0-Audit-
  Annahme „binaer/partial" war falsch; die Substanz ist
  voll, also gibt es nichts zu vertagen.

### Welle-5c-D-4 — Demo-Compose-Port-Bind-Form

**Frage:** Wie wird die `ports`-Klausel ge-hardened?

Optionen:

- **A — Strikt `"127.0.0.1:8000:8080"`** ohne Override-
  Mechanismus. Maintainer-Workflows brauchen Compose-
  Override-File.
- **B — `"${GRID_GYM_DEMO_HOST_BIND:-127.0.0.1}:8000:8080"`
  ENV-Override-Pattern**: Default loopback-only, Override
  per ENV-Export.
- **C — Conditional via Compose-Profile** (`hardened`-
  Profile mit loopback-only, Default unverandert).

**Welle-5c-Final: Option B (ENV-Override-Pattern).**
Begruendung:

- Default ist sicher (loopback-only) → erfuellt
  `GG-DEPLOY-011`-Akzeptanz formal.
- Override-Pfad ist explizit und dokumentiert (Maintainer
  setzt `GRID_GYM_DEMO_HOST_BIND=0.0.0.0` bewusst, Audit-Trail
  ueber den ENV-Export).
- Vermeidet das Pattern „verstecktes Override per Compose-
  Override-File" (Drift-anfaellig).
- Compose-Profile (Option C) waere fuer zwei Modi (default vs
  hardened) overkill — ein ENV-Override ist die kleinste
  ausreichende Substanz.

### Welle-5c-D-5 — Demo-Compose-Hardening-Scope

**Frage:** Welche weiteren Compose-Hardening-Items kommen mit
in Welle 5c?

**Welle-5c-Final: Nur Port-Bind.** Begruendung:

- `GG-DEPLOY-011`-Akzeptanz ist ausschliesslich Netzwerk-
  Beschraenkung; keine Read-only-Filesystem-Pflicht.
- Read-only + Cap-Drop sind `GG-DEPLOY-*`-Vollausbau-Substanz
  und M6-Welle-6-Scope (Deploy-Hardening); Welle 5c wuerde
  da vorgreifen und Welle-6-Decisions praejudizieren.
- Sub-Slicing-Disziplin: jede Welle haelt ihren Scope eng.

### Welle-5c-D-6 — ADR-Schaerfungs-Bedarf

**Frage:** Erfordert Welle 5c eine NEU ADR oder Schaerfung
einer bestehenden?

**Welle-5c-Final: Keine ADR.** Begruendung:

- Audit-Doku verankert nur bestehende Substanz; kein neuer
  Architektur-Vertrag.
- Compose-`ports`-Klausel-Edit ist Operations-Detail, kein
  ADR-Material.
- ENV-Override-Pattern ist Konvention, kein neuer Decision-
  Punkt fuer ADR 0012 (API + Simulation als zwei Prozesse).
- Pattern-Konsistenz mit Welle 5a (kein C1 per Welle-5a-D-5);
  Welle 5c folgt derselben Linie.

---

## 4. Liefer-Reihenfolge (3 Commits)

### Pre-C0 — bereits erledigt (M6-Welle-5b-Closure-Folge)

- `33c238c` (Pre-C0a: `git mv M6-welle-5b.md → done/`).
- `06a20c3` (Pre-C0b: Cross-Doc-Refs-Sync + Hash-Slot-Fills).

### C0 — `docs(plan)`: M6-welle-5c Slice-Doc

**Dieser Commit.** Enthaelt:

- NEU `M6-welle-5c.md` (dieses Dokument; nach C0-Review-Folge
  rewrite gegen 4 Findings).
- `in-progress/README.md` Aktive-Welle-Block auf M6-Welle-5c.
- `M6-perf-security-cicd.md §3.1` Welle-5c-Zeile
  `Pending → In Progress 2026-06-07`; Status-Header-Block
  aktive Welle auf 5c.
- `roadmap.md §3 M6` aktive Welle auf 5c.

### C1 entfaellt (Welle-5c-D-6)

### C2 — `feat(security)` + `docs(user)`: SAFE-005/006-Audit + Demo-Compose-Hardening + Smokes

Code- + Doku-Merge mit:

- NEU `docs/user/safe-005-006-fallback-determinism.md` Audit-
  Tabelle:
  - `GG-SAFE-005`: ✓ produktiv per Sicherheitsgrenzen-
    Validierung; Pro-Geraet-Tabelle Battery/Load/
    GridConnection.
  - `GG-SAFE-006`: ✓ produktiv per `diff_replay`; Akzeptanz-
    Komponenten-Mapping.
- NEU `docs/user/demo-compose-hardening.md` Maintainer-Doku
  fuer Port-Bind + ENV-Override-Pfad.
- `deploy/compose.yml` Port-Bind-Hardening (`api`-Service
  `ports`-Klausel auf
  `"${GRID_GYM_DEMO_HOST_BIND:-127.0.0.1}:8000:8080"`).
- NEU `tests/integration/test_m6_welle_5c_safe_005_006_
  compose_smoke.py` mit 5 Smoke-Tests (siehe §1.2).
- **Verifikation (lokal vor C2-Commit):**
  - `make gates` cache-frei gruen (10/10 A-1-Gates).
  - `make ci` cache-frei gruen.
  - `make fullbuild` cache-frei gruen (Compose-Smoke
    verifiziert den NEU `ports`-Default — `make runtime`
    probet `api:8080/health` containerintern, nicht ueber
    Host-Port).
  - `make docs-check` cache-frei gruen.

### C3 — `docs(plan)`: Status/DoD-Sync + Welle-5-Subdivision-Closure

**Welle-5c-Closure-Sync.**

- `M6-welle-5c.md` Status `In Progress → Done 2026-06-07`
  mit Liefer-Hash-Stack.
- `M6-perf-security-cicd.md §3.1` Welle-5c-Zeile `In
  Progress → Done` + Aktive-Welle-Block auf Welle 6 +
  **Welle-5-Subdivision-komplett-Notiz**.
- `roadmap.md §3 M6` aktive Welle auf Welle 6 + Welle-5-
  Abschluss-Notiz.
- `in-progress/README.md` Aktive-Welle-Block auf Welle 6.

### Welle-5c-Closure-Folge (nach C3)

- C4a `git mv M6-welle-5c.md → done/` (rename-only).
- C4b Cross-Doc-Refs-Sync nach Move + Hash-Slot-Fills +
  `done/README.md`-Eintrag fuer M6-welle-5c.md.

C4a/C4b dienen gleichzeitig als M6-Welle-6-Pre-C0a/Pre-C0b.

---

## 5. Critical Files

**Welle-5c-NEU (geschrieben in C0/C2):**

- `docs/plan/planning/in-progress/M6-welle-5c.md` (C0,
  dieser Commit).
- `docs/user/safe-005-006-fallback-determinism.md` (C2).
- `docs/user/demo-compose-hardening.md` (C2).
- `tests/integration/test_m6_welle_5c_safe_005_006_compose_
  smoke.py` (C2).

**Welle-5c-MODIFY (in C0/C2/C3):**

- `docs/plan/planning/in-progress/README.md` (C0 + C3) —
  Aktive-Welle-Block.
- `docs/plan/planning/in-progress/M6-perf-security-cicd.md`
  (C0 + C3) — §3.1 Welle-5c-Zeile flippen.
- `docs/plan/planning/in-progress/roadmap.md` (C0 + C3) —
  §3 M6 aktive-Welle-Block.
- `deploy/compose.yml` (C2) — `api`-Service `ports`-Klausel
  Port-Bind-Hardening.

**Welle-5c-UNBERUEHRT (kein Edit):**

- Hexagon-Core (`src/grid_gym/hexagon/**`) — Welle 5c ist
  Audit-Welle gegen die bereits produktive Substanz; keine
  Code-Aenderung im Core.
- `BatteryDevice`/`Load`/`GridConnection` `apply_command`-
  Substanz und `diff_replay` bleiben unveraendert.
- Protocol-Adapter (`adapters/driven/protocol_*`) — Welle-5b
  hat den Sim-Marker-Disclaimer dort verankert; Welle 5c
  fasst sie nicht an.
- Welle-5a/5b-Audit-Dokus (`safe-001-004-*` + `safe-007-
  008-*`) — bleiben unveraendert; Welle 5c liefert das
  fehlende Schwester-Audit.
- Alle ADRs (Welle 5c ohne C1-ADR; D-6).
- `open/`-Trigger — kein NEU Trigger (Audit-Substanz ist
  voll abgedeckt).
- `pyproject.toml`/`uv.lock`/`Dockerfile`/`Makefile` (kein
  neuer Dep-Bedarf).
- Alle GitHub-Actions-Workflows.

---

## 6. Verifikationspfad

**Welle-5c-Gate:**

- `make docs-check` cache-frei gruen.
- `make gates` cache-frei gruen (10/10 A-1-Gates).
- `make ci` cache-frei gruen.
- `make fullbuild` cache-frei gruen (Compose-Smoke verifiziert
  den NEU `ports`-Default — `make runtime` probet `api:8080/
  health` containerintern, nicht ueber Host-Port).

**DoD-Verifikation (§9):**

- C0 (dieser Commit) liefert nur Doc-Substanz.
- C2 prueft 5 NEU Smoke-Tests + 2 NEU User-Dokus + Compose-
  Port-Hardening + alle bestehenden Gates gruen.
- C3 prueft Status-Flip + Welle-5-Subdivision-Closure-Notiz.

**Abnahme-Verifikation:**

- `GG-SAFE-005` SOLLTE konditional erfuellt: Audit-Doku zeigt
  Power-Clamp + Sicherheitsgrenzen + Alarm-Emission pro
  Geraet; Lastenheft-Traceability Z. 2291.
- `GG-SAFE-006` SOLLTE konditional erfuellt: Audit-Doku zeigt
  `diff_replay` mit allen vier Akzeptanz-Komponenten
  (Replay-Diff/volatile/Ticks/Klassifikation); Lastenheft-
  Traceability Z. 2292.
- `GG-DEPLOY-011`: `deploy/compose.yml` `api`-Service
  `ports`-Klausel default `127.0.0.1`-loopback-only; ENV-
  Override dokumentiert.

---

## 7. Risiken

**R1 — Smoke-Test-Coverage gegen die Welle-5a-Audit-Pattern
weicht ab.** Welle 5a hatte 2 NEU `open/`-Trigger fuer
partielle/fehlende Substanz; Welle 5c hat keine — Reviewer
koennten das als Pattern-Drift lesen.
**Mitigation:** Slice-Doc-§1.1 erklaert explizit, dass beide
SAFE-Items voll abgedeckt sind und ein Trigger Sub-Slicing-
Inflation waere; Pattern ist „Trigger nur bei echter Lücke".

**R2 — Demo-Compose-Port-Bind-Aenderung bricht Maintainer-
Workflows.** Default-Wechsel von `0.0.0.0` auf `127.0.0.1`
koennte Local-Network-Zugriff (z. B. von einem zweiten Host
im LAN) brechen.
**Mitigation:** ENV-Override-Pattern (Welle-5c-D-4 Option B);
`GRID_GYM_DEMO_HOST_BIND=0.0.0.0` reaktiviert das
Vor-Verhalten explizit. Welle-5c-C2-Doku
(`demo-compose-hardening.md`) macht den Override-Pfad
sichtbar.

**R3 — Compose-Smoke-Side-Effects.** `make runtime`/
`make fullbuild`-Compose-Smoke koennte den `ports`-Aenderung
unbemerkt brechen, wenn der Smoke ueber Host-Port testet.
**Mitigation:** `make runtime` probet bereits container-
intern (`api:8080/health` ueber Compose-Network); Host-Port-
Aenderung ist orthogonal. Pre-C2-`make fullbuild`-Lauf
verifiziert das.

**R4 — Audit-Doku praejudiziert M3-Quality-Pipeline-
Lieferung.** `GG-SAFE-001..004` (Welle 5a) hatte Trigger
034/035 fuer fehlende `max_age`/`Adapter-Comm-Failure`-
Substanz; das war historisch eine `🔲 M3`-Erbschaft. Welle
5c koennte versucht sein, GG-SAFE-005/006 ebenfalls als
„nicht-voll-erfuellt" zu rahmen.
**Mitigation:** Die Lastenheft-Traceability ist eindeutig
(Z. 2291/2292); Welle 5c bleibt bei „✓ produktiv" und
weicht nicht auf die Welle-5a-Pattern aus.

**R5 — Demo-Compose-`api`-Service-Pfad waere falsche
Annahme.** `GRID_GYM_HOST` und `ports`-Klausel liegen beide
im `api`-Service; ein Audit-Hinweis koennte das versehentlich
auf `simulation` schieben.
**Mitigation:** Slice-Doc-§1.1 nennt den `api`-Service
explizit; Welle-5c-C2-Compose-Edit greift dort.

---

## 8. Wandert nach

- **Self-Close-Move im eigenen Welle-Stack**: nach C3
  schliesst die Welle ihre eigene Commit-Sequenz mit
  `git mv M6-welle-5c.md → ../done/M6-welle-5c.md` (C4a) +
  Cross-Doc-Refs-Sync (C4b). Pattern analog M6-Welle-5b-
  C4a `33c238c`/C4b `06a20c3`.
- C4a/C4b dienen gleichzeitig als M6-Welle-6-Pre-C0a/Pre-C0b.
- `done/README.md`-Eintrag fuer `M6-welle-5c.md` ergaenzen
  (C4b oder eigener Commit; Pattern aus dem Welle-5b-
  Hygiene-Commit `cd8a3c3`).
- Keine NEU ADRs (Welle 5c ohne C1-ADR; D-6).

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] **C0 — NEU `M6-welle-5c.md`** mit §1..§9-Struktur
  (dieser Commit; C0-Review-Folge gegen 4 Findings adressiert
  ueber Slice-Doc-Rewrite vor Push).
- [x] **C0 — `in-progress/README.md`** Aktive-Welle-Block
  auf M6-Welle-5c.
- [x] **C0 — `M6-perf-security-cicd.md §3.1`** Welle-5c-Zeile
  `Pending → In Progress 2026-06-07`.
- [x] **C0 — `roadmap.md §3 M6`** aktive Welle auf 5c.
- [x] **C1 entfaellt** — Welle-5c-D-6 (keine ADR).
- [ ] **C2 — NEU `docs/user/safe-005-006-fallback-
  determinism.md`** Audit-Tabelle.
- [ ] **C2 — NEU `docs/user/demo-compose-hardening.md`**
  Maintainer-Doku.
- [ ] **C2 — `deploy/compose.yml`** `api`-Service `ports`-
  Klausel Port-Bind-Hardening.
- [ ] **C2 — NEU `tests/integration/test_m6_welle_5c_safe_
  005_006_compose_smoke.py`** mit 5 Smokes.
- [ ] **C2 — `make gates`** cache-frei gruen.
- [ ] **C2 — `make ci`** cache-frei gruen.
- [ ] **C2 — `make fullbuild`** cache-frei gruen.
- [ ] **C3 — `M6-welle-5c.md`** Status `In Progress → Done
  2026-06-07` mit Liefer-Hash-Stack.
- [ ] **C3 — `M6-perf-security-cicd.md §3.1`** Welle-5c-
  Zeile `In Progress → Done` + Aktive-Welle-Block auf
  Welle 6 + Welle-5-Subdivision-komplett-Notiz.
- [ ] **C3 — `roadmap.md §3 M6`** aktive Welle auf 6 +
  Welle-5-Abschluss-Notiz.
- [ ] **C3 — `in-progress/README.md`** Aktive-Welle-Block
  auf Welle 6.
- [ ] **C3 — `make docs-check`** cache-frei gruen.

**Anti-Scope-Verifikation (Welle 5c NICHT):**

- [x] Keine NEU Fallback-Implementation an Geraeten — Audit
  gegen bestehende Substanz; Pattern ✓ produktiv.
- [x] Keine NEU `diff_replay`-Erweiterung — bestehende
  Substanz ist voll.
- [x] Kein Container-Hardening jenseits Port-Bind (Welle-
  5c-D-5; `GG-DEPLOY-*` ist Welle-6-Scope).
- [x] Keine Multi-User-/Auth-Implementation (Lastenheft Z.
  1161-1163 strukturell ausgeschlossen).
- [x] Kein NEU `open/`-Trigger (Audit-Substanz voll
  abgedeckt; kein Pattern-Drift gegenueber Welle 5a).
- [x] Kein NEU ADR (D-6).
- [x] Kein NEU Code im Core.

---

## References

- [`../done/M6-welle-5b.md`](../done/M6-welle-5b.md) —
  Welle-5b Sim/Prod-Marker + Input-Validation
  (abgeschlossen); Welle 5c ist die naechste und letzte
  Sub-Welle der Welle-5-Subdivision.
- [`../done/M6-welle-5a.md`](../done/M6-welle-5a.md) —
  Welle-5a Quality-Pipeline-Audit; Pattern-Vorbild fuer
  Audit-Welle ohne C1-ADR.
- [`M6-perf-security-cicd.md §3.2 Welle 5`](M6-perf-security-cicd.md)
  — M6-Slice-Plan Welle-5c-Vorbelegung.
- [`../../../../spec/lastenheft.md §20 GG-SAFE-005/006`](../../../../spec/lastenheft.md)
  — Lastenheft-Akzeptanz fuer Fallback-Zustaende +
  Non-Determinism-Detection (Z. 1380-1393); plus
  Realisierungs-Traceability §23 (Z. 2291 fuer GG-SAFE-005,
  Z. 2292 fuer GG-SAFE-006).
- [`../../../../spec/lastenheft.md §17 GG-DEPLOY-011`](../../../../spec/lastenheft.md)
  — Demo-Compose-IP/Netz-Beschraenkung (Z. 1913-1920).
- [`carveouts.md §2.7`](carveouts.md) — Permanent-Out-of-
  Scope-Block (Multi-User + Auth strukturell ausgeschlossen).
- [`../../adr/0014-battery-snapshot-schema.md`](../../adr/0014-battery-snapshot-schema.md)
  + [`../../adr/0016-pv-load-device-pattern.md`](../../adr/0016-pv-load-device-pattern.md)
  + [`../../adr/0017-grid-connection-device-pattern.md`](../../adr/0017-grid-connection-device-pattern.md)
  — Device-Snapshot-/Command-Pattern (Substanz fuer `GG-SAFE-005`-
  Sicherheitsgrenzen-Validierung).
- [`../../../user/safe-001-004-quality-pipeline.md`](../../../user/safe-001-004-quality-pipeline.md)
  + [`../../../user/safe-007-008-sim-prod-input-validation.md`](../../../user/safe-007-008-sim-prod-input-validation.md)
  — Welle-5a/5b-Schwester-Audit-Dokus; Welle 5c liefert
  das dritte Audit-Doc `safe-005-006-fallback-
  determinism.md`.
