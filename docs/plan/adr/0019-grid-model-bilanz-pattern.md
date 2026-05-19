# ADR 0019 — Grid-Model-Bilanz-Pattern (M2 Welle 5a)

**Status:** Proposed
**Datum:** 2026-05-19
**Bezug:**
[`ADR 0013`](0013-device-model-protocol.md) (`DeviceModel`-Protocol —
`GridModelBilanz` ist **explizit kein** Device; siehe §1 + §3),
[`ADR 0014`](0014-battery-snapshot-schema.md) (Snapshot-Pattern;
`GridModelSnapshot` spiegelt das self-sufficient-Layout, aber ohne
`DeviceModel`-Lifecycle),
[`ADR 0016`](0016-pv-load-device-pattern.md) §2.2 (Sign-
Konvention der Geraete-Telemetrie; Bilanz konsumiert die emittierten
`power_kw`-Werte direkt),
[`ADR 0017`](0017-grid-connection-device-pattern.md) §2.2 (das
GridConnection-Vorzeichen schliesst die Bilanz-Formel; die hier
fixierte Imbalance-Berechnung ist die Inverse dazu),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-ADR-
Pattern — diese ADR baut auf ADR 0014 §2.2 auf, ohne Supersedes).
M2-Slice-Plan
[`in-progress/M2-devices.md`](../planning/in-progress/M2-devices.md)
§3 Welle 5a. Lastenheft §11 (`GG-GRID-001`/`002`),
§5 `GG-AR-COMP-DEVICES` (System-Modell, nicht Device-Liste).

---

## 1. Kontext

`GridModelBilanz` ist das **vereinfachte Netzbilanzmodell** des
MVP. Es konsumiert die `power_kw`-Telemetrie aller `PvDevice`/
`LoadDevice`/`BatteryDevice`/`GridConnectionDevice`-Instanzen
und leitet daraus zwei System-Groessen ab:

- **Frequenz** (`frequency_hz`, `GG-GRID-001`).
- **Spannung** je Anschlusspunkt (`voltage_v`, `GG-GRID-002`).

Welle-5a-Minimum ist ein **proportionales Modell** ohne
Tragheits-/Daempfungs-Terme (keine Swing-Equation, kein
Power-Flow). Die Modell-Wahl ist bewusst klein:

- **Keine inertia** — `df/dt` wird nicht modelliert; nach jeder
  Imbalance-Aktualisierung springt `frequency_hz` direkt auf
  den neuen Wert.
- **Keine reactive-power** — `Q` ist explizit out-of-scope
  (`GG-GRID-007` SOLLTE, Post-MVP).
- **Single-Bus-Approximation** — alle Anschlusspunkte liegen
  auf demselben Spannungsband; keine Transformer-Topologie.
- **Safety-Clamps** — Frequenz/Spannung werden in
  Welle-5a-Wertebereichen gehalten (siehe §2.5), damit
  numerische Drift in Property-Tests nicht entgleist.

`GridModelBilanz` ist **kein** `DeviceModel`:

- Es satisfiziert nicht das `DeviceModel`-Protocol (kein
  `device_id`, kein `apply_command`, kein Per-Device-Tick).
- Es ist **single-instance pro Simulation** (vergleiche
  ADR 0013 §2.1: Devices sind mehrfach instanziierbar).
- Es liegt unter `hexagon/core/grid_model/`, **nicht** unter
  `devices/` (per `GG-AR-COMP-DEVICES` §5: Modell ist kein
  Geraet).
- Snapshot-Sub-Key in `SnapshotEnvelope.sub_snapshots` ist
  `grid_model` (kein `devices.<id>`-Praefix).

Welle 6 verdrahtet `GridModelBilanz` in den `TickLoop`, indem
sie nach jedem Geraete-Tick die aggregierten Power-Werte in
`bilanz.update(...)` einspeist.

---

## 2. Entscheidung

### 2.1 Modul-Struktur

```
hexagon/core/grid_model/
    __init__.py        # Re-Export GridModelBilanz + GridModelConfig + Sentinel-Konstanten
    bilanz.py          # GridModelBilanz (Frequenz/Spannungs-Formel)
    config.py          # GridModelConfig (Sollwerte + Sensitivitaeten + Clamps)
    snapshot.py        # GridModelSnapshot (Frozen-Dataclass)
```

`loads.py` ist Welle-5b-Lieferung (ADR 0020); Welle 5a haelt
das Verzeichnis ohne `loads.py`.

### 2.2 Imbalance-Definition

Imbalance ist die **Residualgroesse** der vollstaendigen
Netzbilanz, mechanisch identisch zur Formel aus
ADR 0017 §2.2:

```
imbalance_kw = sum(pv.power_kw)
             - sum(load.power_kw)
             - sum(battery.power_kw)
             + sum(grid_connection.power_kw)
```

Dieses Vorzeichen folgt **ADR 0016 §2.2** und **ADR 0017
§2.2** (`grid_connection.power_kw > 0` = Import = positives
Vorzeichen in der Summe):

- `imbalance_kw == 0`: Bilanz schliesst ideal (Soll-Zustand
  unter Welle-6-Auto-Schluss; Frequenz/Spannung bleiben auf
  Nennwert).
- `imbalance_kw > 0`: Erzeugungs- bzw. Import-Ueberschuss →
  Frequenz steigt, Spannung steigt.
- `imbalance_kw < 0`: Verbrauchs-Ueberschuss → Frequenz
  faellt, Spannung faellt.

**Worked Example (Spiegel zu ADR 0017 §2.2):**

| Geraet           | `power_kw` | Beitrag zur Bilanz |
| ---------------- | ---------- | ------------------ |
| pv-1             | `+2.0`     | +2.0 (Erzeugung)   |
| load-1           | `+1.0`     | -1.0 (Verbrauch)   |
| battery-1        | `+1.0`     | -1.0 (Laden)       |
| grid-connection  | `-0.0`     | +0.0 (Balanced)    |

`imbalance_kw = 2.0 - 1.0 - 1.0 + 0.0 = 0` → balanced.

Spiegel mit nicht-geschlossener Bilanz (Welle-6-Auto-Schluss
NICHT aktiv): `pv=+2`, `load=+1`, `battery=+0.5`,
`grid_connection=+1` (manuell per Scenario-Event gesetzt):

`imbalance_kw = 2.0 - 1.0 - 0.5 + 1.0 = +1.5` →
Erzeugungs-/Importueberschuss, Frequenz steigt um
`+1.5 * k_f`.

**Beziehung zu Welle-6-Auto-Schluss:** Wenn Welle 6 die
GridConnection automatisch als Bilanz-Schluss setzt
(`grid_connection.power_kw = -(pv - load - battery)`),
wird `imbalance_kw` per Konstruktion `0`. Die Frequenz/
Spannungs-Aenderung tritt also nur bei **manuell** gesetzten
GridConnection-Werten (z. B. Szenario-Events, Kapazitaets-
Begrenzungen via `max_import_kw`/`max_export_kw`-Clamp) auf —
das spiegelt die reale Netzdynamik (Frequenz folgt der
Restbilanz, nicht der Summe einzelner Anteile).

### 2.3 Frequenz-Formel (`GG-GRID-001`)

Proportionales Modell mit Equilibrium bei Nennwert:

```
frequency_hz = nominal_frequency_hz + k_f * imbalance_kw
```

mit `nominal_frequency_hz = 50.0` (Default; konfigurierbar in
`GridModelConfig`) und `k_f` als **Sensitivitaets-Konstante**
mit Einheit `Hz/kW`.

**Welle-5a-Default fuer `k_f`:** `Decimal("0.001")` (entspricht
`1 Hz / 1000 kW = 1 Hz / MW`). Das ist eine konservative
Skalierung — eine 1-MW-Imbalance treibt die Frequenz um
`±1 Hz`, ohne die Safety-Clamps zu verletzen, solange die
Imbalance unter `±5 MW` bleibt. Welle-5a-MVP-Demo-Szenarien
liegen erwartet unter `1 MW`.

**Safety-Clamp:** `45.0 Hz ≤ frequency_hz ≤ 55.0 Hz`. Werte
ausserhalb werden auf den naechsten Grenzwert geclamped;
jedes Clamp-Event inkrementiert `clamp_event_count` (siehe
§2.5; monoton nicht-fallend ueber den Lauf, Forward-Looking
fuer M3-Alarm-Pfad). Welle 5a fuehrt **keinen** separaten
`last_clamped: bool`-Flag mit Reset-Semantik — der Zaehler
allein traegt die Welle-5a-Information, und die Differenz
zwischen zwei aufeinanderfolgenden Snapshots zeigt, ob ein
Clamp seitdem zugeschnappt hat.

### 2.4 Spannungs-Formel (`GG-GRID-002`)

Analog Frequenz, single-bus-Approximation:

```
voltage_v = nominal_voltage_v + k_v * imbalance_kw
```

mit `nominal_voltage_v` aus `GridModelConfig` (Default
`400.0`, spiegelt typischen Niederspannungs-Anschluss).
`k_v` mit Einheit `V/kW`.

**Welle-5a-Default fuer `k_v`:** `Decimal("0.1")` (entspricht
`10 V / 100 kW`). 100-kW-Imbalance treibt die Spannung um
`±10 V`. Lastenheft §11.2 spezifiziert keinen festen Wert;
die Wahl ist eine konservative Vorbelegung.

**Safety-Clamp:** `0.7 * nominal_voltage_v ≤ voltage_v ≤ 1.3
* nominal_voltage_v`. Analog zur Frequenz-Clamp.

**Modell-Selbstkennzeichnung (`GG-GRID-002` Akzeptanz):**
`GridModelSnapshot.model_kind: str` traegt den Wert
`"simplified-proportional"`. Welle-5+/M3 koennte das auf
`"power-flow-adapter"` umstellen; Welle 5a haelt es als
Konstante.

### 2.4a GridModelConfig-Invarianten (Welle-4a-Review-Round-3-Medium-1)

`GridModelConfig` ist Frozen-Dataclass; `__post_init__` validiert
und wirft `GridModelConfigInvalidValueError` bei Verstoss:

- **Sollwerte positiv:**
  - `nominal_frequency_hz > 0`.
  - `nominal_voltage_v > 0`.
- **Sensitivitaeten positiv** (Sign-Konvention: `imbalance > 0`
  → `f`/`v` steigt; ein negativer Sensitivitaets-Wert wuerde
  die Semantik invertieren):
  - `frequency_sensitivity_hz_per_kw > 0`.
  - `voltage_sensitivity_v_per_kw > 0`.
- **Clamp-Reihenfolge:**
  - `frequency_clamp_min_hz < nominal_frequency_hz <
    frequency_clamp_max_hz`.
  - `voltage_clamp_min_v < nominal_voltage_v <
    voltage_clamp_max_v`.
  - Strikt kleiner/groesser (kein Equal), damit der
    Equilibrium-Zustand (imbalance == 0) garantiert
    nicht-clampend ist.

Diese Invarianten sind Welle-5a-Pflicht und durch Unit-Tests
(jedes Verstoss-Szenario einzeln) gepinnt. `from_dict`
ueberfuehrt `GridModelConfigInvalidValueError` zu
`WrongTypeError(subsystem="grid_model", field="config",
expected="valid", actual=<config-error-text>)` —
Pattern-Spiegel zu Welle-3-Review-L-1 / Welle-4b-Review-M-2.

### 2.5 Snapshot-Layout

`GridModelSnapshot` ist eine Frozen-Dataclass (Spiegel zu
ADR 0014 §2.2). Im Code traegt sie ein `GridModelConfig`-
Objekt als Feld; in der `to_dict()`-Serialisierung wird der
Config in ein **nested Mapping mit explizit benannten Keys**
zerlegt (Pattern-Spiegel zu PV/Load/Battery/GridConnection-
Snapshots: SnapshotEnvelope akzeptiert rekursiv nur
canonical-kompatible Payloads, keine Dataclass-Objekte —
siehe `hexagon/core/domain/snapshot.py::SnapshotEnvelope.
__post_init__`).

**Dataclass-Felder (`GridModelSnapshot`):**

- `version: int` — Schema-Version (`1` in Welle 5a). Bumps
  mit Folge-ADRs (Welle 5b ergaenzt LoadEvents/Profiles und
  bumpt auf `2`).
- `config: GridModelConfig` — Sollwerte + Sensitivitaeten +
  Clamp-Grenzen; embedded fuer self-sufficient-
  `from_snapshot`.
- `model_kind: str` — Selbstkennzeichnung des Modells
  (`"simplified-proportional"` in Welle 5a).
- `current_frequency_hz: Decimal`.
- `current_voltage_v: Decimal`.
- `last_imbalance_kw: Decimal` — letzter Imbalance-Input, der
  zum aktuellen Frequenz-/Spannungs-Wert gefuehrt hat.
  Persistiert, damit Resume die Forward-History nicht
  rekonstruieren muss.
- `clamp_event_count: int` — Zaehler, wie oft eine Safety-
  Clamp zugeschnappt hat (Welle-5a-Monotonie-Invariante:
  monoton nicht-fallend; nur durch `from_snapshot(...)`-
  Resume kann der Wert von 0 wieder hoch erscheinen).
  Forward-Looking fuer M3-Alarme.

  **Clamp-Counting-Semantik (Welle-4a-Review-Round-3-
  Medium-2):** Jeder `update(...)`-Aufruf inkrementiert den
  Zaehler um **die Anzahl der unabhaengig zuschnappenden
  Clamps** in diesem Aufruf:
  - Frequenz UND Spannung clampen gleichzeitig → `count +=
    2`.
  - Nur Frequenz clampt → `count += 1`.
  - Nur Spannung clampt → `count += 1`.
  - Keine Clamps → `count += 0`.

  Aufeinanderfolgende `update(...)`-Aufrufe mit identischem
  Input, die jeweils clampen, zaehlen jeweils einzeln —
  **keine Deduplizierung**. Damit gibt der Differenz-
  Zaehler zwischen zwei Snapshots die Anzahl der
  Clamp-Vorfaelle wieder, nicht die Anzahl der „Uebergangs"-
  Ereignisse. Welle-5a-Property pinnt: bei 100 identischen
  clampenden Inputs erwartet der Test `count == 100` (bzw.
  `200` wenn beide Clamps gleichzeitig schnappen).

**`to_dict()`-Mapping (Top-Level, `version` als Erst-Feld):**

```
{
  "version": 1,
  "config": {                                  # nested dict, kein Dataclass
    "nominal_frequency_hz": Decimal,           # Default 50.0
    "frequency_sensitivity_hz_per_kw": Decimal, # Default 0.001
    "frequency_clamp_min_hz": Decimal,         # Default 45.0
    "frequency_clamp_max_hz": Decimal,         # Default 55.0
    "nominal_voltage_v": Decimal,              # Default 400.0
    "voltage_sensitivity_v_per_kw": Decimal,   # Default 0.1
    "voltage_clamp_min_v": Decimal,            # = 0.7 * nominal_voltage_v
    "voltage_clamp_max_v": Decimal,            # = 1.3 * nominal_voltage_v
  },
  "model_kind": "simplified-proportional",
  "current_frequency_hz": Decimal,
  "current_voltage_v": Decimal,
  "last_imbalance_kw": Decimal,
  "clamp_event_count": int,
}
```

Voltage-Clamps werden im Snapshot **absolut** persistiert
(nicht als `0.7 * nominal_voltage_v`-Faktor); Resume nutzt
exakt die persistierten Werte und ist gegen
Sensitivitaets-Konvention-Drift unempfindlich.

`from_dict(state) -> Self` nutzt Welle-0a-Codec-Free-Functions
(`assert_required_keys`, `assert_int`, `assert_str`,
`assert_decimal`, `assert_mapping`) und rekonstruiert
self-sufficient. `GridModelConfigError` wird zu
`WrongTypeError(subsystem="grid_model", ...)` ueberfuehrt
(Welle-3-Review-L-1- und Welle-4b-Review-M-2-Pattern).

### 2.6 Lifecycle (kein DeviceModel)

`GridModelBilanz` exposiert **keine** DeviceModel-Protocol-
Methoden. Stattdessen:

- `__init__(config: GridModelConfig)` — direkt, kein
  separates `initialize(scenario_device, random)` (keine
  ScenarioDevice-Identitaet, keine RandomPort-Abhaengigkeit
  in Welle 5a).
- `update(generation_kw, load_kw, storage_kw, grid_connection_kw)`
  — Tick-Methode mit **vier** Power-Inputs (Spiegel zur
  Bilanz-Formel §2.2). Berechnet Imbalance + Frequenz +
  Spannung, schreibt interne Felder fort. Kein Telemetry-
  Tupel als Return — Welle 6 liest `frequency_hz`/`voltage_v`
  direkt ueber Getter und integriert sie ggf. in
  `TickResult.emitted_telemetry`.
- `frequency_hz` / `voltage_v` / `last_imbalance_kw` /
  `clamp_event_count` — Properties.
- `snapshot()` / `from_snapshot(state)` — analog DeviceModel,
  aber **ohne** Pre-init-Asymmetrie (kein
  `DeviceNotInitializedError`; `GridModelBilanz` ist nach
  `__init__` immer initialisiert).

### 2.7 Determinismus

Welle-5a-Property:

- Gleicher `GridModelConfig` + identische
  `(generation_kw, load_kw, storage_kw, grid_connection_kw)`-
  Sequenz → byte-identische
  `(frequency_hz, voltage_v, last_imbalance_kw,
  clamp_event_count)`-Spur ueber ≥ 100 Updates.
- Pflicht-Hypothesis-Property (`@given(...)` ueber
  Decimal-Tupel der vier Inputs): zweimal dieselbe Sequenz →
  byte-identische Snapshot-Folge inkl. der monoton nicht-
  fallenden `clamp_event_count`-Spur. Damit ist der manuelle
  GridConnection-/Clamp-Pfad mechanisch durch die Property
  gepinnt, nicht nur durch Punkt-Tests.

`RandomPort` wird **nicht** konsumiert (Welle 5a hat kein
stochastisches Element). M3-Fault-Injection (Spannungs-
Stoerungen, Frequenz-Drift) wird `RandomPort` einbinden,
analog `attach_random`-Hook in den Geraeten.

Decimal-Localcontext-Wrapper (Welle-2-Review-M-2-Spiegel)
greift in `update(...)`, weil dort Decimal-Multiplikationen
(`k_f * imbalance_kw`, `k_v * imbalance_kw`) laufen.

---

## 3. Begruendung

**Proportionales Modell statt Swing-Equation:** Die echte
Frequenz-Dynamik (`df/dt = (P_gen - P_load) / (2*H*S_base)`)
braucht Tragheit `H` und Nennleistung `S_base` als Modell-
Parameter — beides ist im MVP nicht praezise modellierbar
ohne Generatoren-Detailmodell (`GG-GEN-*` ist Post-MVP).
Welle-5a-Proportionalmodell ist trivial deterministisch und
deckt `GG-GRID-001` Akzeptanz („vereinfachtes Leistungs-
bilanzmodell, das Frequenzabweichungen aus Erzeugung, Last
und Speicherleistung ableitet") wortwoertlich.

**Auto-Schluss vs. Lastenheft-Akzeptanz (Review-Round-3-
Hoch):** Wenn Welle 6 den Auto-Schluss als Default verdrahtet
(`grid_connection.power_kw := -pre_grid_residual_kw`), wird
`imbalance_kw` per Konstruktion `0` — und Frequenz/Spannung
bleiben auf Nennwert. Lastenheft `GG-GRID-001` „aus Erzeugung,
Last und Speicherleistung ableitet" ist trotzdem **wortwoertlich
erfuellt**: die Formel verwendet diese drei Groessen als
Bausteine. Die Akzeptanz wird ueber **manuelle Welle-5a-
Test-Szenarien** demonstriert, die GridConnection bewusst
NICHT auto-schliessen (Beispiel-Test:
`scenario.events = [set_power_kw(target='grid-1', value=0)]`
zwingt `grid_connection.power_kw = 0`, sodass das
`pre_grid_residual = pv - load - battery` direkt in
`imbalance_kw` durchschlaegt und Frequenz/Spannung deviieren).
Welle-6-MVP-Demo-Scenario kann den Auto-Schluss-Pfad nutzen
(Frequenz stabil auf 50 Hz), Welle-5a-Property-Tests nutzen
den Manual-Pfad (Frequenz deviiert deterministisch).

**Physikalisch:** der Auto-Schluss-Fall entspricht dem
Idealzustand „Netz ist unendlich stark, faengt jeden
Mismatch perfekt auf". Manuelle GridConnection und Cap-
Limits (`max_import_kw`/`max_export_kw` aus ADR 0017 §2.4)
sind die realistischeren Faelle, in denen die lokale
Frequenz/Spannung deviiert. Das entspricht der MVP-
Vereinfachung, dass das Netzbilanzmodell keine
Sekundaerregelung modelliert.

**Single-Bus statt Power-Flow:** Eine echte Power-Flow-
Analyse (Newton-Raphson, Backward-Forward-Sweep) braucht
Knoten-Topologie + Leitungs-Impedanzen — keines ist in
`GG-GRID-002` MUSS-Akzeptanz spezifiziert. `GG-GRID-006`
(Transformatorgrenzen) und `GG-GRID-007` (Blindleistung)
sind SOLLTE und out-of-scope. Welle-5a-Single-Bus ist
ehrlich vereinfacht; `model_kind: "simplified-proportional"`
kennzeichnet das (Lastenheft §11.2-Akzeptanz „muss kenntlich
machen, ob es ein vereinfachtes Ersatzmodell oder einen
Power-Flow-Adapter verwendet").

**Kein DeviceModel-Protocol:** `GridModelBilanz` ist ein
**System-Modell**, kein Geraet. Es gehoert zur
TickLoop-Verantwortung (analog Scheduler/RandomPort), nicht
zur Geraete-Liste. Welle 6 ruft es **einmal pro Tick** mit
aggregierten Power-Werten auf; das passt nicht zum
DeviceModel-Lifecycle (apply_command/tick/initialize). Eine
erzwungene DeviceModel-Konformitaet wuerde die Protocol-
Surface verwaessern (was waere `apply_command` an die
Bilanz?). Pattern-Spiegel: ADR 0013 §2.2 haelt `RandomPort`
auch ausserhalb des Protocols.

**Safety-Clamps als Welle-5a-Pflicht:** Property-Tests mit
Hypothesis koennen extreme Imbalance-Werte (`±1e9 kW`)
generieren. Ohne Clamps wuerden Frequenz/Spannung in
absurde Bereiche driften und numerische Folgefehler
(Decimal-Praezision, Quantisierungs-Drift) verstaerken. Die
Clamp-Grenzen sind **Modell-Grenzen**, kein Realitaets-
Anspruch — sie pinnen den Wertebereich, in dem das
Proportional-Modell sinnvoll interpretierbar ist.

---

## 4. Reichweite

Diese ADR gilt fuer:

- `hexagon/core/grid_model/__init__.py`.
- `hexagon/core/grid_model/bilanz.py` (vollstaendig).
- `hexagon/core/grid_model/config.py` (vollstaendig).
- `hexagon/core/grid_model/snapshot.py` (Welle-5a-Stand;
  Welle-5b ergaenzt LoadEvents/Profiles in derselben Datei).
- `tests/unit/hexagon/core/grid_model/` (Welle-5a-Tests).

Diese ADR gilt NICHT fuer:

- `loads.py` und Load-Profile-Logik (Welle 5b — eigene
  ADR 0020).
- TickLoop-Integration (Welle 6).
- Power-Flow-Adapter (`GG-GRID-006`/`007` SOLLTE, Post-MVP).
- Fault-Injection-Pfade (`GG-FAULT-*`, M3).
- Generator-Detail-Modelle (Tragheit, Daempfung — Post-MVP).

---

## 5. Operative Artefakte

Mit Acceptance dieser ADR (synchron mit M2-Welle-5a-PR-Merge)
liegen folgende Module:

- `src/grid_gym/hexagon/core/grid_model/`
  (`__init__`, `config`, `bilanz`, `snapshot` — 4 Module;
  `loads.py` folgt mit Welle 5b).
- `tests/unit/hexagon/core/grid_model/test_grid_model_bilanz.py`
  — **ein** konsolidiertes Test-Modul mit Section-Kommentaren
  (Config-Invarianten, Initial-Equilibrium, Imbalance-Formel,
  Safety-Clamps + Clamp-Counting, Snapshot-Roundtrip,
  Determinismus). Spiegelt das PV/Load/GridConnection-Pattern
  (`test_pv_device.py` ist ebenfalls konsolidiert). Welle 5b
  ergaenzt `test_loads.py` separat. *(Welle-5a-Review L-2:
  ursprueglicher ADR-Text nannte 4 Test-Module — auf 1
  konsolidiertes korrigiert.)*
- Default-`CRITICAL_COV_TARGETS` aus Dockerfile-`coverage-
  gate-critical`-Stage um `core/grid_model` erweitert.
- Volle Test-Anzahl-Inkrement gegen Welle 4b wird in der
  Welle-5a-Closure-Notiz verzeichnet (Erwartung: ~30..50
  neue Tests).

---

## 6. Konsequenzen

**Was sich aendert:**

- M2-Welle-6 TickLoop-Integration kann `GridModelBilanz`
  einheitlich neben den fuenf Geraete-Modellen konsumieren —
  Wege ueber `update(...)` statt `tick(...)`-Protocol.
- `SnapshotEnvelope.sub_snapshots` bekommt ab Welle 6 einen
  `grid_model`-Single-Instance-Eintrag (vs. den fuenf
  `devices.<id>`-Eintraegen). Dadurch bumpt die Envelope-
  Version v1→v2 (separat in **ADR 0015 zu fixieren —
  geplante ADR, Datei wird mit Welle 6 angelegt; Forward-
  Reference im aktuellen Repo noch ohne ADR-File**).
- **Welle-5b-Snapshot-Versionssprung (Forward-Pointer,
  Review-M-2):** Der aktuelle `GridModelSnapshot.from_dict`-
  Hartzweig (`if version != SNAPSHOT_VERSION: raise
  VersionError(...)`) wird in Welle 5b durch eine
  `version in {1, 2}`-Verzweigung + per-Version-Parser
  ersetzt. v1-Snapshots (ohne `active_load_events` /
  `active_load_profiles`) sollen weiterhin als roundtrip-
  faehige Welle-5a-Snapshots lesbar bleiben (Backward-Compat-
  Lesepfad in ADR 0020 §2.x). Welle 5a haelt den jetzigen
  Hartzweig bewusst; Welle 5b plant den Umbau im selben
  Modul mit gleichzeitigem ADR-0020-Closure.
- `GridConnection.power_kw` wird in Welle 6 aus der
  **Pre-Grid-Restbilanz** abgeleitet:

  ```
  pre_grid_residual_kw = sum(pv.power_kw)
                       - sum(load.power_kw)
                       - sum(battery.power_kw)
  grid_connection.power_kw := -pre_grid_residual_kw   # Auto-Schluss
  ```

  Damit wird `imbalance_kw` aus §2.2 per Konstruktion `0`
  (Bilanz schliesst). **Nicht** verwechseln mit
  `-imbalance_kw` — das waere zirkulaer, weil
  `imbalance_kw` in §2.2 bereits `grid_connection.power_kw`
  enthaelt. Die Welle-4a-Sign-Konvention (ADR 0017 §2.2)
  bleibt unveraendert; der Schluss-Pfad nutzt nur die
  Pre-Grid-Subsumme.

**Was load-bearing bleibt:**

- ADR 0013 DeviceModel-Protocol (unveraendert; Bilanz ist
  bewusst ausserhalb).
- ADR 0016 §2.2 Sign-Konvention (Imbalance-Berechnung haengt
  daran).
- ADR 0017 §2.2 (GridConnection schliesst die Bilanz).
- Welle-0a-Codec (`SnapshotFormatError`-Hierarchie).

**Was offen bleibt (Welle 5b+):**

- LoadEvent/LoadProfile-Repraesentation (`GG-GRID-003`/`004`).
  ADR 0020, Welle 5b.
- Snapshot-Versionssprung v1→v2 zwischen 5a (ohne Loads) und
  5b (mit Loads). Backward-Compat-Lesepfad in ADR 0020 §2.x
  zu fixieren.
- TickLoop-Verdrahtung + GridConnection-Schluss-Variable.
  Welle 6.
- M3-Fault-Injection an Frequenz/Spannung
  (`GG-FAULT-005`/`007`).
- Generator-Detail-Modelle (Tragheit, Daempfung) —
  Post-MVP.

---

## 7. Nicht Gegenstand dieser ADR

- **Swing-Equation** (`df/dt = (P_gen - P_load) / (2*H*S_base)`)
  und damit verbundene Tragheit/Daempfung-Konstanten. Welle 5a
  benutzt die proportionale Form bewusst; Erweiterung ist
  Post-MVP (Generator-Detail-Modelle).
- **Power-Flow-Topologie** (Knoten, Leitungen, Impedanzen).
  `GG-GRID-006` SOLLTE; out-of-scope M2.
- **Blindleistung / Q** (`GG-GRID-007` SOLLTE, Post-MVP).
- **Inselnetz-Erkennung** (`GG-GRID-005` SOLLTE, Post-MVP);
  Frequenz/Spannung im Inselbetrieb haengen von
  Generator-Detail-Modellen ab.
- **Load-Profile/-Event-Repraesentation** (`GG-GRID-003`/
  `004`). Welle 5b, eigene ADR 0020.
- **TickLoop-Verdrahtung** (Welle 6).
- **Telemetry-Emission**: Welle 5a `GridModelBilanz` emittiert
  selbst keine `TelemetryPoint`s. Welle 6 entscheidet, ob
  Frequenz/Spannung in `TickResult.emitted_telemetry` als
  `grid.frequency_hz`/`grid.voltage_v` aufgenommen werden;
  diese Entscheidung ist nicht Gegenstand der vorliegenden
  ADR.

  **Open Question fuer den Welle-6-ADR (Round-3-Reviewer):**
  `TelemetryPoint` verlangt `device_id`, `source` und
  `sequence` als Pflichtfelder
  (siehe `hexagon/core/domain/telemetry.py:26`). Falls
  Welle 6 Grid-Werte als TelemetryPoints emittiert, braucht
  der Folge-ADR (Welle 6 ist ADR-Kandidat fuer 0021 oder
  inline im M2-Slice-Plan) eine Konvention fuer:
  - Pseudo-`device_id` (Vorschlag: `"grid_model"` als
    Single-Instance-Marker, parallel zur Snapshot-Sub-Key-
    Konvention),
  - `source` (Vorschlag: `"grid_model"`),
  - `sequence`-Counter (Vorschlag: dedizierter Counter
    `_grid_model_telemetry_sequence`, separat von Geraete-
    Sequence-Pools).

  Welle 5a haelt das Feld bewusst leer und gibt diese drei
  Vertraege an Welle 6 weiter. Falls Welle 6 entscheidet,
  Grid-Werte NICHT als TelemetryPoint zu emittieren (sondern
  z. B. nur ueber den Snapshot zu persistieren), entfaellt
  die Konvention.
