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

Imbalance ist der vorzeichenbehaftete Saldo aus Erzeugung,
Last und Speicherleistung **am Bilanz-Punkt** (vor
GridConnection-Ausgleich):

```
imbalance_kw = sum(pv.power_kw)
             - sum(load.power_kw)
             - sum(battery.power_kw)
```

Dieses Vorzeichen folgt **ADR 0016 §2.2**:

- `imbalance_kw > 0`: Erzeugungs-Ueberschuss (PV liefert mehr
  als Load + Battery-Laden verbraucht) → System will
  exportieren oder Frequenz steigt.
- `imbalance_kw < 0`: Verbrauchs-Ueberschuss → System will
  importieren oder Frequenz faellt.
- `imbalance_kw == 0`: Balanced (idealer Zustand).

**Wichtig:** Der `GridConnection.power_kw` (ADR 0017 §2.2)
ist die **Schluss-Variable** der Bilanz und wird NICHT in
`imbalance_kw` einbezogen. Welle 6 setzt
`grid_connection.power_kw = -imbalance_kw` (Ideal-Schluss),
sodass die Anschlusspunkt-Telemetrie die Restgroesse traegt.
Welle 5a definiert nur die Imbalance-Berechnung; der
Bilanz-Schluss ist Welle-6-TickLoop-Arbeit.

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
ausserhalb werden auf den naechsten Grenzwert geclamped; ein
Clamp-Event setzt ein internes `_clamp_flag`, das vom
Snapshot getragen wird (Forward-Looking fuer M3-Alarm-Pfad).

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

### 2.5 Snapshot-Layout

`GridModelSnapshot` ist eine Frozen-Dataclass (Spiegel zu
ADR 0014 §2.2):

- `version: int` — Schema-Version (`1` in Welle 5a). Bumps
  mit Folge-ADRs (Welle 5b ergaenzt LoadEvents/Profiles und
  bumpt auf `2`).
- `config: GridModelConfig` — Sollwerte + Sensitivitaeten +
  Clamp-Grenzen; embedded fuer self-sufficient-`from_snapshot`.
- `model_kind: str` — Selbstkennzeichnung des Modells
  (`"simplified-proportional"` in Welle 5a).
- `current_frequency_hz: Decimal`.
- `current_voltage_v: Decimal`.
- `last_imbalance_kw: Decimal` — letzter Imbalance-Input, der
  zum aktuellen Frequenz-/Spannungs-Wert gefuehrt hat.
  Persistiert, damit Resume die Forward-History nicht
  rekonstruieren muss.
- `clamp_event_count: int` — Zaehler, wie oft eine Safety-
  Clamp zugeschnappt hat. Forward-Looking fuer M3-Alarme.

`snapshot()` mapped auf `Mapping[str, object]` mit `version`
als Erst-Feld (ADR 0013 §2.4 Konvention).
`from_snapshot(state) -> Self` rekonstruiert self-sufficient
via Welle-0a-Codec-Free-Functions.

### 2.6 Lifecycle (kein DeviceModel)

`GridModelBilanz` exposiert **keine** DeviceModel-Protocol-
Methoden. Stattdessen:

- `__init__(config: GridModelConfig)` — direkt, kein
  separates `initialize(scenario_device, random)` (keine
  ScenarioDevice-Identitaet, keine RandomPort-Abhaengigkeit
  in Welle 5a).
- `update(generation_kw, load_kw, storage_kw)` — Tick-Methode.
  Berechnet Imbalance + Frequenz + Spannung, schreibt
  interne Felder fort. Kein Telemetry-Tupel als Return —
  Welle 6 liest `frequency_hz`/`voltage_v` direkt ueber
  Getter und integriert sie ggf. in
  `TickResult.emitted_telemetry`.
- `frequency_hz` / `voltage_v` / `last_imbalance_kw` —
  Properties.
- `snapshot()` / `from_snapshot(state)` — analog DeviceModel,
  aber **ohne** Pre-init-Asymmetrie (kein
  `DeviceNotInitializedError`; `GridModelBilanz` ist nach
  `__init__` immer initialisiert).

### 2.7 Determinismus

Welle-5a-Property:

- Gleicher `GridModelConfig` + identische
  `(generation_kw, load_kw, storage_kw)`-Sequenz →
  byte-identische `(frequency_hz, voltage_v)`-Spur ueber
  ≥ 100 Updates.

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
- `tests/unit/hexagon/core/grid_model/` (4 Test-Module:
  `config`, `bilanz`, `snapshot`, `determinism`).
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
  Version v1→v2 (separat in ADR 0015 zu fixieren).
- `GridConnection.power_kw` wird in Welle 6 aus
  `-imbalance_kw` abgeleitet, sodass die Bilanz mechanisch
  geschlossen wird. Die Welle-4a-Sign-Konvention bleibt
  unveraendert (ADR 0017 §2.2).

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
