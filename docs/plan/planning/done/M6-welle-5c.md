# Welle 5c — M6 SOLLTE-Items + IP/Netz-Beschraenkung (`GG-SAFE-005/006` + Demo-Compose)

**Status:** Done 2026-06-07 — Liefer-Hash-Stack
`4b76ff7..C3 dieser Commit` (C0 `4b76ff7` Slice-Doc-Anlage
inkl. zweier Review-Runden mit 8 Findings vor Push +
C0-Review-Folge-2 `4a80f46` 4 weitere Findings F1..F4
adressiert + open/README-Trigger-036-Eintrag `807ef9b`
parallel + in-progress/README-Aktive-Welle-/Aktiver-
Meilenstein-Cleanup `db4729e` parallel + C2 `f03c4c7`
Code-/Doku-Substanz (3 Doks + 1 Trigger + 1 Compose-Edit +
6 Smokes) + C3 dieser Commit Status/DoD-Sync). C1 entfaellt
per Welle-5c-D-6.

Welle 5 wird gemaess Welle-5a-D-1 in **5a (Quality-Pipeline-
Audit; `GG-SAFE-001..004` MUSS) + 5b (Sim/Prod-Marker + Input-
Validation; `GG-SAFE-007/008` MUSS) + 5c (SOLLTE-Items + IP/
Netz-Beschraenkung; `GG-SAFE-005` + `GG-SAFE-006` + Demo-
Compose-Hardening)** sub-geslict. Welle 5c ist die **dritte
und letzte Sub-Welle** und schliesst die **Welle-5-Subdivision
komplett** (alle `GG-SAFE-*` MUSS+SOLLTE + Demo-Compose-IP/
Netz-Auflage).

**Pre-C0 abgeschlossen (M6-Welle-5b-Closure-Folge):**

- C4a `33c238c` — `git mv M6-welle-5b.md → done/` (Self-
  Close-Move, rename-only).
- C4b `06a20c3` — Cross-Doc-Refs-Sync nach Move + Hash-Slot-
  Fills. **Welle 5b komplett**: 6 Inline-Fixes + `_BaseRequest`-
  Mixin + 11 Smokes + Audit-Doku + NEU ADR 0045
  `Provisional`; Stack `0d3bb61..06a20c3`.

**C0-Review-Folge 1+2 (Slice-Doc-Iteration vor Push):** der
ursprueng­liche Pre-C0-Audit hatte zwei substantielle
Fehler-Schichten — der vorliegende Stand integriert beide
Review-Folgen in einen einzigen C0-Commit:

- **Runde 1 (4 Findings 2 MEDIUM + 2 LOW)**: ursprueng­licher
  Audit-Schluss „nicht/binaer implementiert" war falsch.
  Tatsache: `BatteryDevice.apply_command` + Sicherheits-
  grenzen + Power-Clamp sind die Lastenheft-Z. 2291-
  Realisierung fuer SAFE-005; `diff_replay()` ist die
  Lastenheft-Z. 2292-Realisierung fuer SAFE-006-Core-
  Algorithm. Plus IP/Netz-Lastenheft-Zeile + `GRID_GYM_HOST`-
  Service-Pfad korrigiert.
- **Runde 2 (4 weitere Findings: 3 MEDIUM + 1 LOW)**: die
  Korrektur von Runde 1 hat zu weit gedreht. SAFE-006 ist
  doch ⚠ partial (Core-Algorithm ✓, aber Per-Lauf-Status-
  Marker `replay_diff_status` aus Architektur §15-Metrik-
  Liste + Lastenheft-Z. 2292-ReplaySource-Integration
  fehlen). SAFE-005-Geraete-Liste war unvollstaendig (PV
  fehlte). IP/Netz-Anker auf `GG-DEPLOY-011` war falsch —
  die Beschraenkung ist per `carveouts.md §2.7` eine
  **separate Auflagen-Schicht ohne einzelnen Lastenheft-
  ID**. Plus 2 LOW Code-Detail-Drifts
  (`validate_set_power_command` statt `validate_command`;
  `limit_unit="pct"` statt `"%"`).

Damit ist die Welle-5c-Lieferform: Audit-Doku mit ehrlichem
Status (✓ produktiv fuer SAFE-005 + Core-Diff-Algorithm;
⚠ partial fuer SAFE-006 Per-Lauf-Status-Marker +
ReplaySource-Integration) **plus NEU `open/`-Trigger 036**
fuer die partielle Lücke. Pattern-konsistent mit Welle 5a
(Triggers 034/035 fuer partielle SAFE-001..004-Lücken).

**Spec-Reife:** Inhaltlich final fuer Welle 5c. Welle-5c-
Decision-Liste (§3) schliesst Welle-5c-D-1..D-6: Audit-Form,
`GG-SAFE-005`-Audit-Form, `GG-SAFE-006`-Audit-Form + Trigger-
Anlage, Demo-Compose-Port-Bind-Form, Hardening-Scope, ADR-
Bedarf.

---

## 1. Context

`GG-SAFE-005/006` SOLLTE (Lastenheft Z. 1380-1393) plus IP-/
Netz-Beschraenkung im Demo-Compose (separate Auflagen-Schicht
per `carveouts.md §2.7`, **kein einzelner Lastenheft-ID**):

- **`GG-SAFE-005`**: Die Plattform SOLLTE sichere Fallback-
  Zustaende unterstuetzen. **Akzeptanz:** Wenn Fallback-
  Zustaende implementiert sind, dokumentiert jeder betroffene
  Geraetetyp Ausloeser, Zielzustand, Telemetrie und Recovery-
  Verhalten. **Lastenheft-Traceability** (Z. 2291): Realisiert
  ueber **Geraete-Fallback-Verhalten via `BatteryDevice.
  apply_command` / Sicherheitsgrenzen-Validierung** —
  Sub-Substanz lebt auf vier produktiven Geraetetypen
  (Battery, Load, GridConnection, PV; siehe §1.1).
- **`GG-SAFE-006`**: Nichtdeterministische Simulationslaeufe
  SOLLTEN erkannt werden. **Akzeptanz:** Wenn Erkennung
  nichtdeterministischer Laeufe implementiert ist, meldet die
  Plattform Replay-Diff, volatile Felder, betroffene Ticks
  und Abweichungsklassifikation maschinenlesbar. **Lastenheft-
  Traceability** (Z. 2292): Realisiert ueber **Replay-Diff-
  Status-Markierung — M3 mit Replay-Source-Integration**.
  Architektur §15 (Z. 820 + 823) verlangt zusaetzlich eine
  per-Lauf-Metrik `replay_diff_status` und einen
  maschinenlesbaren Replay-Diff-Statuswert.
- **IP-/Netz-Beschraenkung im Demo-Compose**: per
  [`carveouts.md §2.7`](../in-progress/carveouts.md) (Permanent-Out-of-
  Scope-Block „Multi-User + Auth im UI-Layer"): **separate
  Auflagen-Schicht, kein einzelner Lastenheft-ID**. Die
  Auflage steht orthogonal zu `GG-DEPLOY-011` (Lastenheft Z.
  1913-1920) — `GG-DEPLOY-011` fordert Offline-Laeufe ohne
  externe Netzwerkverbindungen, nicht restriktive Host-Port-
  Bindings; die beiden Anforderungen ueberschneiden sich
  nicht.

### 1.1 Existierende Substanz (Pre-C0-Audit, Code-verifiziert)

**`GG-SAFE-005` — Geraete-Fallback-Verhalten via Sicherheits-
grenzen-Validierung** (✓ produktiv an vier Geraetetypen):

- `BatteryDevice.apply_command` mit Pure-Function
  `validate_set_power_command` in `hexagon/core/devices/
  battery/commands.py:77`: bei Wert ausserhalb
  `[-max_discharge_kw, max_charge_kw]` → Power-Clamp + Alarm
  `(result=LIMITED, limit=clamped_value, limit_unit="kW")`;
  bei SOC-Boden + Wert < 0 oder SOC-Decke + Wert > 0 → Alarm
  `(result=REJECTED, limit=min_soc_pct/max_soc_pct,
  limit_unit="pct")`, Soll-Wert unveraendert. Geraet faellt
  auf den letzten gueltigen Soll-Zustand (= sicherer
  Default-Zustand) zurueck.
- Analoge Sicherheitsgrenzen + Power-Clamp-Substanz in:
  - `hexagon/core/devices/load/commands.py` (Load):
    `value < 0` → REJECTED, `value > rated_power_kw` →
    LIMITED + Alarm.
  - `hexagon/core/devices/grid_connection/commands.py`
    (GridConnection): `value > max_import_kw` → LIMITED,
    `value < -max_export_kw` → LIMITED + Alarm; kein
    REJECTED-Pfad fuer Vorzeichen (ADR 0017 §2.4).
  - `hexagon/core/devices/pv/commands.py` (PV):
    `value < 0` → REJECTED + Alarm (`limit=0,
    limit_unit="kW"`); `value > rated_power_kw` →
    LIMITED + Alarm (Power-Clamp).
- Telemetrie + Alarm-Emission-Pfad ist `M3` Welle-2-Substanz
  (ADR 0022/0025): `LIMITED`/`REJECTED`-Outcomes traversieren
  den Alarm-Pipeline-Pfad bis zum `AlarmStreamPort`.
- Recovery-Verhalten: bei naechstem `apply_command` innerhalb
  der Bounds → `result=ACCEPTED`, Geraet uebernimmt den neuen
  Soll-Wert.
- Test-Coverage: `tests/unit/hexagon/core/devices/battery/`
  + `.../load/` + `.../grid_connection/` + `.../pv/`-Suiten
  pinnen die Bounds- und Reject-Pfade pro Geraet.

**`GG-SAFE-006` — Replay-Diff-Klassifikation** (⚠ partial —
Core-Algorithm produktiv; Per-Lauf-Status-Marker +
ReplaySource-Integration fehlen):

- ✓ **Core-Diff-Algorithm produktiv** in
  `src/grid_gym/hexagon/core/replay/diff.py::diff_replay(
  expected, actual, *, tick_ms, volatile_fields)` mit
  `tuple[ReplayDelta, ...]`:
  - **`ReplayDelta.path`** (z. B. `"sample[i].timestamp"`) —
    welches Feld differiert.
  - **`ReplayDelta.tick`** (`int = simulation_time //
    tick_ms`) — auf welchem Tick die Divergenz auftritt.
  - **`ReplayDelta.classification`** (`ReplayDeltaClassification`
    StrEnum mit `FACHLICH` / `VOLATIL`) — semantische
    Klassifikation.
  - **`volatile_fields`-Konfiguration** als
    `frozenset[str]`-Parameter; Default
    `_VOLATILE_FIELDS_DEFAULT = frozenset({"import_sequence"})`
    (M5-Welle-5-Review SC-1 verankert).
  - Test-Coverage `tests/unit/hexagon/core/replay/
    test_diff.py` verriegelt Klassifikation-Equality,
    Tick-Berechnung, Volatile-Field-Aufweichung.
- ✗ **Per-Lauf-Status-Marker `replay_diff_status` fehlt**:
  Architektur §15 (Z. 820 + 823) listet
  `replay_diff_status` als Pflicht-Metrik („maschinenlesbarer
  Statuswert pro Lauf"). Grep ueber `src/grid_gym/` nach
  `replay_diff_status` liefert null Treffer; die Metrik wird
  weder emittiert noch ueber `MetricsPort` exponiert.
- ✗ **ReplaySource-Integration fehlt**: Lastenheft Z. 2292
  nennt explizit „Replay-Diff-Status-Markierung — M3 mit
  Replay-Source-Integration". Grep nach `ReplaySource` in
  `src/grid_gym/` liefert null Treffer; der Diff-Algorithm
  ist standalone-Funktion ohne Anbindung an einen Lauf-
  Lifecycle.
- Konsequenz: die binaeren vier Akzeptanz-Komponenten
  (Replay-Diff, volatile Felder, betroffene Ticks,
  Klassifikation maschinenlesbar) sind algorithmisch
  abgedeckt, aber die operative Verankerung an einen Lauf
  (Per-Lauf-Status + ReplaySource-Lifecycle-Hook) fehlt.
  Welle 5c verankert das partielle Bild in der Audit-Doku
  und legt NEU [Trigger 036](../open/036-safe-006-replay-
  diff-status-replay-source-integration.md) an (Pattern
  analog Welle-5a-Triggers 034/035 fuer fehlende SAFE-001..
  004-Substanz).

**Demo-Compose IP-/Netz-Beschraenkung** (separate Auflagen-
Schicht ohne Lastenheft-ID):

- `deploy/compose.yml` Z. 104 `api`-Service: `ports: -
  "8000:8080"` (Short-Form ohne IP-Praefix) → laut Docker-
  Compose-Konvention bindet auf **alle Host-Interfaces
  (0.0.0.0)**. Restriktive Form waere `"127.0.0.1:8000:
  8080"`.
- Anmerkung zu `GRID_GYM_HOST: 0.0.0.0` im `api`-Service
  (Z. 84): das ist die **container-interne** uvicorn-
  Binding-Konfig, damit das Docker-Compose-Network den
  `api`-Container ueber den Sibling-Hostname erreichen kann.
  Standard-Pattern, **keine** Security-Lücke; die externe
  Sichtbarkeit wird ausschliesslich ueber die `ports:`-
  Klausel kontrolliert.
- Auflagen-Quelle: `carveouts.md §2.7`-Permanent-Out-of-
  Scope-Eintrag „Multi-User + Auth im UI-Layer" enthaelt
  den expliziten Hinweis „IP-/Netz-Beschraenkung ist im
  Demo-Compose verankert (separate Auflagen-Schicht, kein
  einzelner Lastenheft-ID)" — Welle 5c implementiert diese
  Auflage.

### 1.2 Welle-5c-Lieferziel

**Audit + Hardening-Welle** (Pattern analog Welle 5a/5b):

1. **NEU `docs/user/safe-005-006-fallback-determinism.md`**
   (Welle-5c-C2) — Audit-Tabelle:
   - **`GG-SAFE-005`**: ✓ **Produktiv** ueber Sicherheits-
     grenzen-Validierung + Power-Clamp in Battery/Load/
     GridConnection/**PV** `apply_command` mit Alarm-
     Emission; Lastenheft-Traceability Z. 2291 + ADR
     0014/0016/0017.
   - **`GG-SAFE-006`**: ⚠ **Partial Lücke**: Core-Diff-
     Algorithm ✓ produktiv (`diff_replay()` mit allen vier
     Akzeptanz-Komponenten); Per-Lauf-Status-Marker
     `replay_diff_status` ✗ Lücke + ReplaySource-Integration
     ✗ Lücke → Trigger 036.

2. **NEU `docs/plan/planning/open/036-safe-006-replay-
   diff-status-replay-source-integration.md`** (Welle-5c-
   C2) — Trigger fuer:
   - `replay_diff_status`-Metrik auf `MetricsPort` (per-Lauf,
     maschinenlesbar) gemaess Architektur §15-Z. 820+823.
   - `ReplaySource`-Integration: Lifecycle-Hook im Lauf-
     Setup, der `diff_replay()` mit `expected`/`actual`-
     Sequenzen aus dem Lauf-Snapshot-Pfad versorgt.
   - Aktivierungs-Bedingung: Compliance-Druck oder
     Stakeholder-Bedarf an Per-Lauf-Status-Sichtbarkeit
     (heute kein konkreter Trigger).

3. **`deploy/compose.yml` Port-Bind-Hardening** (Welle-5c-C2)
   — `api`-Service `ports`-Klausel umstellen auf
   `"${GRID_GYM_DEMO_HOST_BIND:-127.0.0.1}:8000:8080"`;
   `GRID_GYM_DEMO_HOST_BIND`-ENV-Variable als Override-Pattern
   fuer Maintainer-Bedarf „externe Sichtbarkeit explizit
   aktivieren". Default bleibt strikt loopback-only.

4. **NEU `docs/user/demo-compose-hardening.md`** (Welle-5c-
   C2) — Maintainer-Doku, wie der Demo-Compose ge-hardened
   ist + wie der ENV-Override-Pfad genutzt wird.

5. **NEU 6 Integration-Smokes** (Welle-5c-C2):
   - `test_safe_005_battery_safety_bounds_emit_limited`:
     E2E-Smoke gegen `BatteryDevice.apply_command` mit Wert
     ausserhalb Bounds → `result=LIMITED` + Alarm.
   - `test_safe_005_pv_safety_bounds_emit_limited`:
     Schwester-Smoke fuer PV-Power-Clamp.
   - `test_safe_005_load_negative_value_rejected`:
     Schwester-Smoke fuer Load-Sign-Reject.
   - `test_safe_006_diff_replay_classifies_volatile_and_
     fachlich`: E2E-Smoke gegen `diff_replay` mit Mismatch
     in `import_sequence` (`VOLATIL`) + Mismatch in
     `timestamp` (`FACHLICH`); pinnt die Klassifikation.
   - `test_safe_006_diff_replay_status_deferred_via_
     trigger_036`: Skip-mit-Pointer auf Trigger 036
     (Pattern analog Welle-5a-Smoke-Skip-mit-Trigger-
     Pointer fuer Trigger 034/035).
   - `test_compose_ports_loopback_bound_by_default`:
     `deploy/compose.yml` `api`-Service `ports`-Klausel
     enthaelt `127.0.0.1`-Default oder
     `GRID_GYM_DEMO_HOST_BIND`-Override-Pattern (Quell-
     Datei-Inspektion).

### 1.3 Welle-5c-Anti-Scope

- **Keine NEU Fallback-Implementation** an Geraeten — Welle
  5c verifiziert + dokumentiert die bestehende Sicherheits-
  grenzen-Substanz, sie wird **nicht** erweitert.
- **Keine NEU `replay_diff_status`-Metrik / ReplaySource-
  Integration** — Pattern-Konsistenz mit Welle 5a-D-3:
  substantielle Lücken werden als `open/`-Trigger
  vertagt; Welle 5c liefert die Audit-Doku + Trigger 036.
- **Keine NEU `diff_replay`-Algorithm-Erweiterung** — die
  vier Akzeptanz-Komponenten sind im Core-Algorithm ✓
  vollstaendig; keine zusaetzlichen Felder oder
  Klassifikations-Kategorien.
- **Kein Container-Hardening jenseits Port-Bind** (Read-only-
  Filesystem, User-Capabilities, Healthcheck-Pollung-Pattern,
  ...) — `GG-DEPLOY-*`-Substanz ist M6-Welle-6-Scope.
- **Keine Multi-User-/Auth-Implementation** — strukturell
  ausgeschlossen per Lastenheft Z. 1161-1163 +
  `carveouts.md §2.7`.
- **Kein NEU ADR** — D-6 schliesst Schaerfungs-Bedarf
  negativ aus.
- **Kein NEU Code im Core** — Audit-Doku + Compose-Edit +
  Smokes; keine NEU Funktionalitaet in der Hexagon-Substanz.

---

## 2. Scope

Welle 5c liefert **fuenf Items** ueber 3 Commits (C0..C3),
plus Self-Close-Folge C4a/C4b.

1. **Slice-Doc-Anlage** (C0, dieser Commit) — dieses Dokument;
   `in-progress/README.md` Aktive-Welle-Block auf 5c;
   `M6-perf-security-cicd.md §3.1` Welle-5c-Zeile
   `Pending → In Progress 2026-06-07`;
   `roadmap.md §3 M6` aktive Welle auf 5c.
2. **C1 entfaellt** — Welle-5c-D-6 schliesst ADR-Bedarf
   negativ aus (Pattern analog Welle 5a / M5-Welle-2).
3. **Code-/Doku-Substanz** (C2):
   - NEU `docs/user/safe-005-006-fallback-determinism.md`
     Audit-Tabelle.
   - NEU `docs/user/demo-compose-hardening.md` Maintainer-
     Doku.
   - NEU `docs/plan/planning/open/036-safe-006-replay-
     diff-status-replay-source-integration.md` Trigger.
   - `deploy/compose.yml` `api`-Service `ports`-Klausel
     Port-Bind-Hardening.
   - NEU `tests/integration/test_m6_welle_5c_safe_005_006_
     compose_smoke.py` mit 6 Smokes.
   - `open/README.md` Trigger-036-Eintrag in der „Quality-
     Pipeline-Lücken"-Section.
4. **Status/DoD-Sync** (C3) — Status-Flip + Welle-5-
   Subdivision-komplett-Notiz; aktive Welle auf Welle 6.

Self-Close-Folge C4a/C4b laufen nach C3 als M6-Welle-6-Pre-
C0a/Pre-C0b.

---

## 3. Architektur-Entscheidungen (Welle-5c-Decision-Liste)

### Welle-5c-D-1 — Audit-Form

**Frage:** Wie wird die GG-SAFE-005/006-SOLLTE-Akzeptanz
audited?

**Welle-5c-Final: Option C (Doku + Smoke-Tests + ggf.
Trigger).** Pattern-Konsistenz mit Welle 5a + 5b; Smoke-
Tests sind CI-Sensor gegen Drift, Doku ist Audit-Trail fuer
Reviewer, Trigger verankert substantielle Lücken.

### Welle-5c-D-2 — `GG-SAFE-005`-Audit-Form

**Frage:** Wie wird die produktive Sicherheitsgrenzen-
Substanz in der Audit-Doku verankert?

**Welle-5c-Final: Audit-Doku „✓ produktiv per Lastenheft-
Traceability Z. 2291" mit Substanz-Pfad + Test-Pfad + Pro-
Geraet-Pflicht-Felder (Ausloeser, Zielzustand, Telemetrie,
Recovery-Verhalten) tabellarisch dokumentiert. Pro-Geraet-
Liste umfasst Battery, Load, GridConnection, PV (alle vier
mit produktiver Sicherheitsgrenzen-Substanz).**

Begruendung:

- Lastenheft Z. 2291 mapped GG-SAFE-005 ausdruecklich auf
  `BatteryDevice.apply_command` + Sicherheitsgrenzen.
- Lastenheft-Akzeptanz fordert „dokumentiert jeder
  betroffene Geraetetyp" — Welle-5c-C2-Audit-Doku zeigt
  das Mapping fuer alle vier Geraete mit produktiver
  Substanz.

### Welle-5c-D-3 — `GG-SAFE-006`-Audit-Form

**Frage:** Wie wird die `GG-SAFE-006`-Substanz in der Audit-
Doku verankert? Core-Diff-Algorithm ist produktiv, aber
Per-Lauf-Status-Marker und ReplaySource-Integration fehlen.

**Welle-5c-Final: Audit-Doku „⚠ partial Lücke" mit
Trigger 036 fuer die fehlende Substanz.** Begruendung:

- Pattern-Konsistenz mit Welle 5a-D-3 (Hybrid; substantielle
  Lücken → `open/`-Trigger): die zwei Lücken (`replay_diff_
  status`-Metrik + ReplaySource-Integration) sind nicht
  inline-fixbar, ohne den Lauf-Lifecycle und die `MetricsPort`-
  Surface zu beruehren.
- Core-Diff-Algorithm-Substanz wird ehrlich als produktiv
  dokumentiert; Per-Lauf-Verankerung als Lücke verankert.
- Trigger 036 macht den Folge-Pfad explizit; Aktivierung bei
  Compliance-Druck oder Stakeholder-Bedarf.
- **Anti-Pattern (verworfen)**: Audit-Doku „✓ voll
  produktiv" — wuerde die Architektur-§15-`replay_diff_
  status`-Pflicht-Metrik und die Lastenheft-Z. 2292-
  ReplaySource-Integration unterberichten.

### Welle-5c-D-4 — Demo-Compose-Port-Bind-Form

**Frage:** Wie wird die `ports`-Klausel ge-hardened?

Optionen:

- **A — Strikt `"127.0.0.1:8000:8080"`** ohne Override-
  Mechanismus.
- **B — `"${GRID_GYM_DEMO_HOST_BIND:-127.0.0.1}:8000:8080"`
  ENV-Override-Pattern**: Default loopback-only, Override
  per ENV-Export.
- **C — Conditional via Compose-Profile**.

**Welle-5c-Final: Option B (ENV-Override-Pattern).**
Begruendung:

- Default ist sicher (loopback-only) → erfuellt die
  `carveouts.md §2.7`-Auflage „IP-/Netz-Beschraenkung im
  Demo-Compose".
- Override-Pfad ist explizit und dokumentiert (Maintainer
  setzt `GRID_GYM_DEMO_HOST_BIND=0.0.0.0` bewusst, Audit-
  Trail ueber den ENV-Export).
- Vermeidet das Pattern „verstecktes Override per Compose-
  Override-File" (Drift-anfaellig).

### Welle-5c-D-5 — Demo-Compose-Hardening-Scope

**Frage:** Welche weiteren Compose-Hardening-Items kommen mit
in Welle 5c?

**Welle-5c-Final: Nur Port-Bind.** Begruendung:

- Die `carveouts.md §2.7`-Auflage ist ausschliesslich
  Netzwerk-Beschraenkung; keine Read-only-Filesystem-Pflicht.
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
  Punkt.
- Trigger 036 selbst ist `open/`-Trigger-Pattern, kein
  ADR-Material; wenn die Trigger-Aktivierung spaeter ein
  ADR braucht, kommt das mit dem Folge-Slice.
- Pattern-Konsistenz mit Welle 5a (kein C1 per Welle-5a-D-5).

---

## 4. Liefer-Reihenfolge (3 Commits)

### Pre-C0 — bereits erledigt (M6-Welle-5b-Closure-Folge)

- `33c238c` (Pre-C0a: `git mv M6-welle-5b.md → done/`).
- `06a20c3` (Pre-C0b: Cross-Doc-Refs-Sync + Hash-Slot-Fills).

### C0 — `docs(plan)`: M6-welle-5c Slice-Doc

**Dieser Commit.** Enthaelt:

- NEU `M6-welle-5c.md` (dieses Dokument; integriert C0-
  Review-Runde 1 + Runde 2 vor Push).
- `in-progress/README.md` Aktive-Welle-Block auf M6-Welle-5c.
- `M6-perf-security-cicd.md §3.1` Welle-5c-Zeile
  `Pending → In Progress 2026-06-07`; Status-Header-Block
  aktive Welle auf 5c.
- `roadmap.md §3 M6` aktive Welle auf 5c.

### C1 entfaellt (Welle-5c-D-6)

### C2 — `feat(security)` + `docs(user)`: SAFE-005/006-Audit + Trigger 036 + Demo-Compose-Hardening + Smokes

Code- + Doku-Merge mit:

- NEU `docs/user/safe-005-006-fallback-determinism.md`
  Audit-Tabelle (SAFE-005 ✓ pro 4 Geraete + SAFE-006 ⚠
  partial + Trigger-Pointer).
- NEU `docs/user/demo-compose-hardening.md` Maintainer-
  Doku.
- NEU `docs/plan/planning/open/036-safe-006-replay-diff-
  status-replay-source-integration.md` Trigger.
- `docs/plan/planning/open/README.md` Trigger-036-Eintrag
  in der „Quality-Pipeline-Lücken (M6-Welle-5a-Audit-
  Folge)"-Section (umbenennen auf „Quality-Pipeline +
  Replay-Determinismus-Lücken (M6-Welle-5-Audit-Folge)").
- `deploy/compose.yml` `api`-Service `ports`-Klausel
  Port-Bind-Hardening mit ENV-Override.
- NEU `tests/integration/test_m6_welle_5c_safe_005_006_
  compose_smoke.py` mit 6 Smoke-Tests (siehe §1.2).
- **Verifikation (lokal vor C2-Commit):**
  - `make gates` cache-frei gruen (10/10 A-1-Gates).
  - `make ci` cache-frei gruen.
  - `make fullbuild` cache-frei gruen.
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
- `docs/plan/planning/open/036-safe-006-replay-diff-status-
  replay-source-integration.md` (C2).
- `tests/integration/test_m6_welle_5c_safe_005_006_compose_
  smoke.py` (C2).

**Welle-5c-MODIFY (in C0/C2/C3):**

- `docs/plan/planning/in-progress/README.md` (C0 + C3) —
  Aktive-Welle-Block.
- `docs/plan/planning/in-progress/M6-perf-security-cicd.md`
  (C0 + C3) — §3.1 Welle-5c-Zeile flippen.
- `docs/plan/planning/in-progress/roadmap.md` (C0 + C3) —
  §3 M6 aktive-Welle-Block.
- `docs/plan/planning/open/README.md` (C2) — Trigger-036-
  Eintrag.
- `deploy/compose.yml` (C2) — `api`-Service `ports`-Klausel
  Port-Bind-Hardening.

**Welle-5c-UNBERUEHRT (kein Edit):**

- Hexagon-Core (`src/grid_gym/hexagon/**`) — Welle 5c ist
  Audit-Welle; keine Code-Aenderung im Core.
- `BatteryDevice`/`Load`/`GridConnection`/`PvDevice`
  `apply_command`-Substanz und `diff_replay` bleiben
  unveraendert.
- Protocol-Adapter (`adapters/driven/protocol_*`) — Welle-5b
  hat den Sim-Marker-Disclaimer dort verankert; Welle 5c
  fasst sie nicht an.
- Welle-5a/5b-Audit-Dokus bleiben unveraendert.
- Alle ADRs (Welle 5c ohne C1-ADR; D-6).
- `pyproject.toml`/`uv.lock`/`Dockerfile`/`Makefile`.
- Alle GitHub-Actions-Workflows.

---

## 6. Verifikationspfad

**Welle-5c-Gate:**

- `make docs-check` cache-frei gruen.
- `make gates` cache-frei gruen (10/10 A-1-Gates).
- `make ci` cache-frei gruen.
- `make fullbuild` cache-frei gruen.

**DoD-Verifikation (§9):**

- C0 (dieser Commit) liefert nur Doc-Substanz.
- C2 prueft 6 NEU Smoke-Tests + 2 NEU User-Dokus + NEU
  Trigger 036 + Compose-Port-Hardening + alle bestehenden
  Gates gruen.
- C3 prueft Status-Flip + Welle-5-Subdivision-Closure-Notiz.

**Abnahme-Verifikation:**

- `GG-SAFE-005` SOLLTE konditional erfuellt: Audit-Doku
  zeigt Power-Clamp + Sicherheitsgrenzen + Alarm-Emission
  auf vier Geraeten (Battery/Load/GridConnection/PV);
  Lastenheft-Traceability Z. 2291.
- `GG-SAFE-006` SOLLTE konditional **teil-erfuellt**:
  Audit-Doku zeigt `diff_replay` Core-Algorithm ✓ produktiv
  mit allen vier Akzeptanz-Komponenten; Per-Lauf-Status-
  Marker `replay_diff_status` + ReplaySource-Integration ✗
  Lücke → Trigger 036.
- Demo-Compose IP-/Netz-Beschraenkung: `deploy/compose.yml`
  `api`-Service `ports`-Klausel default `127.0.0.1`-
  loopback-only mit `GRID_GYM_DEMO_HOST_BIND`-Override;
  Auflage per `carveouts.md §2.7`.

---

## 7. Risiken

**R1 — SAFE-006-Trigger als Pattern-Inflation.** Trigger 036
ist der dritte `open/`-Trigger aus einer Welle-5*-Audit (034
+ 035 aus Welle 5a). Pruefer koennte das als „Auslagerungs-
Inflation" lesen.
**Mitigation:** Pattern ist „Trigger nur bei echter
substantieller Lücke" — Welle-5c-Audit hat Per-Lauf-Status-
Marker + ReplaySource-Integration als substantielle Lücken
identifiziert (Architektur §15 + Lastenheft Z. 2292
explizit). Pattern-konsistent mit Welle 5a.

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

**R4 — Demo-Compose-`api`-Service-Pfad waere falsche
Annahme.** `GRID_GYM_HOST` und `ports`-Klausel liegen beide
im `api`-Service; ein Audit-Hinweis koennte das versehentlich
auf `simulation` schieben.
**Mitigation:** Slice-Doc-§1.1 nennt den `api`-Service
explizit; Welle-5c-C2-Compose-Edit greift dort.

**R5 — IP/Netz-Anker auf falsche normative Quelle.**
`GG-DEPLOY-011` (offline-Lauf, Z. 1913-1920) und die
Lastenheft-Z. 1161-1163-Sim/Prod-Trennung sind beide
**nicht** die normative Quelle fuer Demo-Compose-Host-Port-
Bind. Die korrekte Quelle ist `carveouts.md §2.7`-
„separate Auflagen-Schicht ohne Lastenheft-ID".
**Mitigation:** Slice-Doc-§1 + §1.1 + Abnahme-Verifikation
verweisen ausschliesslich auf `carveouts.md §2.7`;
`GG-DEPLOY-011` wird als orthogonale Anforderung in §1
explizit abgegrenzt.

---

## 8. Wandert nach

- **Self-Close-Move im eigenen Welle-Stack**: nach C3
  schliesst die Welle ihre eigene Commit-Sequenz mit
  `git mv M6-welle-5c.md → ../done/M6-welle-5c.md` (C4a) +
  Cross-Doc-Refs-Sync (C4b). Pattern analog M6-Welle-5b-
  C4a `33c238c`/C4b `06a20c3`.
- C4a/C4b dienen gleichzeitig als M6-Welle-6-Pre-C0a/Pre-C0b.
- `done/README.md`-Eintrag fuer `M6-welle-5c.md` ergaenzen
  (C4b oder eigener Commit; Pattern aus Welle-5b-Hygiene-
  Commit `cd8a3c3`).
- Keine NEU ADRs (Welle 5c ohne C1-ADR; D-6).

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] **C0 — NEU `M6-welle-5c.md`** mit §1..§9-Struktur
  (dieser Commit; integriert C0-Review-Runde 1 + Runde 2
  vor Push).
- [x] **C0 — `in-progress/README.md`** Aktive-Welle-Block
  auf M6-Welle-5c.
- [x] **C0 — `M6-perf-security-cicd.md §3.1`** Welle-5c-
  Zeile `Pending → In Progress 2026-06-07`.
- [x] **C0 — `roadmap.md §3 M6`** aktive Welle auf 5c.
- [x] **C1 entfaellt** — Welle-5c-D-6.
- [x] **C2 — NEU `docs/user/safe-005-006-fallback-
  determinism.md`** Audit-Tabelle (SAFE-005 ✓ pro 4
  Geraete + SAFE-006 ⚠ partial + Trigger-Pointer) —
  geliefert in C2 `f03c4c7`.
- [x] **C2 — NEU `docs/user/demo-compose-hardening.md`**
  Maintainer-Doku — geliefert in C2 `f03c4c7`.
- [x] **C2 — NEU `open/036-safe-006-replay-diff-status-
  replay-source-integration.md`** Trigger — geliefert in
  C2 `f03c4c7` (nach 2 Review-Runden vor Push: Runde 1
  4 Findings = 1 HIGH + 3 MEDIUM + Runde 2 2 LOW; alle
  adressiert, inkl. §15-Anker statt §8.2, §4.2+§8 fuer
  `ReplaySourcePort`, Statuswert-Wertedomaene als
  Folge-Slice-C0-Schaerfungs-ADR-Frage, Lifecycle-Hook
  im Core-Spine statt im HTTP-Action-Router,
  GG-TERM-002-Equality-Vorbedingung im Live-Mode).
- [x] **C2 — `open/README.md`** Trigger-036-Eintrag —
  parallel `807ef9b` (in „Quality-/Determinismus-Lücken
  (M6-Welle-5a/5c-Audit-Folge)"-Section umbenannt).
- [x] **C2 — `deploy/compose.yml`** `api`-Service `ports`-
  Klausel Port-Bind-Hardening — geliefert in C2 `f03c4c7`
  (Default `127.0.0.1` + ENV-Override `GRID_GYM_DEMO_
  HOST_BIND`).
- [x] **C2 — NEU `tests/integration/test_m6_welle_5c_safe_
  005_006_compose_smoke.py`** mit 6 Smokes — geliefert
  in C2 `f03c4c7` (4 SAFE-005 + 1 SAFE-006 Core-Diff +
  1 SAFE-006 Trigger-036-Skip + 1 Compose-Host-Bind).
- [x] **C2 — `make gates`** cache-frei gruen.
- [x] **C2 — `make ci`** cache-frei gruen (104 passed +
  7 skipped).
- [x] **C2 — `make fullbuild`** cache-frei gruen.
- [x] **C3 — `M6-welle-5c.md`** Status `In Progress → Done
  2026-06-07` mit Liefer-Hash-Stack — dieser Commit.
- [x] **C3 — `M6-perf-security-cicd.md §3.1`** Welle-5c-
  Zeile `In Progress → Done` + Aktive-Welle-Block auf
  Welle 6 + Welle-5-Subdivision-komplett-Notiz — dieser
  Commit.
- [x] **C3 — `roadmap.md §3 M6`** aktive Welle auf 6 +
  Welle-5-Abschluss-Notiz — dieser Commit.
- [x] **C3 — `in-progress/README.md`** Bestand-Tabelle
  Welle-5c-Zeile `In Progress → Done 2026-06-07` (Aktive-
  Welle-/Aktiver-Meilenstein-Bloecke sind bereits in
  `db4729e` ersatzlos gestrichen — redundant zu
  `roadmap.md §3 M6` + Z. 3) — dieser Commit.
- [x] **C3 — `make docs-check`** cache-frei gruen.

**Anti-Scope-Verifikation (Welle 5c NICHT):**

- [x] Keine NEU Fallback-Implementation an Geraeten — Audit
  gegen bestehende Substanz.
- [x] Keine NEU `replay_diff_status`-Metrik / ReplaySource-
  Integration — Trigger 036.
- [x] Keine NEU `diff_replay`-Algorithm-Erweiterung — die
  vier Akzeptanz-Komponenten sind im Core ✓ vollstaendig.
- [x] Kein Container-Hardening jenseits Port-Bind (Welle-
  5c-D-5; `GG-DEPLOY-*` ist Welle-6-Scope).
- [x] Keine Multi-User-/Auth-Implementation (Lastenheft Z.
  1161-1163 strukturell ausgeschlossen).
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
  Audit-Welle mit `open/`-Trigger-Anlage bei partiellen
  Lücken (Triggers 034/035).
- [`M6-perf-security-cicd.md §3.2 Welle 5`](M6-perf-security-cicd.md)
  — M6-Slice-Plan Welle-5c-Vorbelegung.
- [`../../../../spec/lastenheft.md §20 GG-SAFE-005/006`](../../../../spec/lastenheft.md)
  — Lastenheft-Akzeptanz fuer Fallback-Zustaende +
  Non-Determinism-Detection (Z. 1380-1393); plus
  Realisierungs-Traceability §23 (Z. 2291 fuer GG-SAFE-005,
  Z. 2292 fuer GG-SAFE-006).
- [`../../../../spec/architecture.md §15`](../../../../spec/architecture.md)
  — Observability-Metrik-Liste (Z. 820) mit
  `replay_diff_status` + Replay-Diff-Status-Tabelle (Z. 823)
  „maschinenlesbarer Statuswert pro Lauf" mit Verweis auf
  `GG-REPLAY-007` und `GG-SAFE-006`.
- [`carveouts.md §2.7`](../in-progress/carveouts.md) — Permanent-Out-of-
  Scope-Block mit der „separate Auflagen-Schicht" fuer
  Demo-Compose-IP/Netz-Beschraenkung (kein Lastenheft-ID).
- [`../../adr/0014-battery-snapshot-schema.md`](../../adr/0014-battery-snapshot-schema.md)
  + [`../../adr/0016-pv-load-device-pattern.md`](../../adr/0016-pv-load-device-pattern.md)
  + [`../../adr/0017-grid-connection-device-pattern.md`](../../adr/0017-grid-connection-device-pattern.md)
  — Device-Snapshot-/Command-Pattern (Substanz fuer
  `GG-SAFE-005`-Sicherheitsgrenzen-Validierung an Battery,
  PV, Load, GridConnection).
- [`../../../user/safe-001-004-quality-pipeline.md`](../../../user/safe-001-004-quality-pipeline.md)
  + [`../../../user/safe-007-008-sim-prod-input-validation.md`](../../../user/safe-007-008-sim-prod-input-validation.md)
  — Welle-5a/5b-Schwester-Audit-Dokus; Welle 5c liefert
  das dritte Audit-Doc `safe-005-006-fallback-
  determinism.md`.
