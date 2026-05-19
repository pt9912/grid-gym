# ADR 0020 — Load-Profile + Load-Event Pattern (M2 Welle 5b)

**Status:** Proposed
**Datum:** 2026-05-19
**Bezug:**
[`ADR 0019`](0019-grid-model-bilanz-pattern.md) (Schwester-ADR
fuer Welle 5a; ADR 0020 erweitert `GridModelSnapshot` um
`active_load_events` + `active_load_profiles` und nutzt den
Versionssprung v1→v2 mit Backward-Compat-Lesepfad),
[`ADR 0014`](0014-battery-snapshot-schema.md) (Snapshot-Codec-
Pattern fuer typed `*FormatError`-Hierarchie),
[`ADR 0013`](0013-device-model-protocol.md) (LoadDevice ist die
Konsum-Seite — LoadEvents werden in Welle 6 in
`set_power_kw`-Commands an `LoadDevice` uebersetzt),
[`ADR 0016`](0016-pv-load-device-pattern.md) §2.4 (LoadDevice-
Command-Surface),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-
ADR-Pattern — diese ADR erweitert ADR 0019 §2.5 fuer das
Load-Repraesentations-Schema, kein Supersedes).
M2-Slice-Plan
[`in-progress/M2-devices.md`](../planning/in-progress/M2-devices.md)
§3 Welle 5b. Lastenheft §11 (`GG-GRID-003`/`004`).

---

## 1. Kontext

Welle 5b ergaenzt das Welle-5a-Netzbilanzmodell um die
Lastenheft-Akzeptanz fuer `GG-GRID-003` und `GG-GRID-004`:

- **`GG-GRID-003`** verlangt, dass Lasten als **konstante
  Werte, Zeitreihen oder Szenario-Events** definiert werden
  koennen.
- **`GG-GRID-004`** verlangt, dass Szenarien **Lastspruenge
  mit Startzeit, Dauer und Leistung** definieren koennen.

Der **konstante** Pfad ist bereits ueber `LoadDevice` (Welle 3)
abgedeckt: `LoadDevice.rated_power_kw` ist der Default-Verbrauch
ohne Scenario-Events. Welle 5b fuegt:

- **`LoadEvent`-Dataclass** (`GG-GRID-004`): Scenario-Event mit
  `start_s`, `duration_s`, `target_device_id`, `power_kw`. Wird
  in Welle 6 vom TickLoop konsumiert und in
  `LoadDevice.apply_command(Command.type="set_power_kw")`
  uebersetzt; nach `start_s + duration_s` wird der Vor-Event-
  Wert (z. B. `rated_power_kw`) wiederhergestellt.
- **`LoadProfile`-Dataclass** (`GG-GRID-003` „Zeitreihen"):
  Tick-indizierte `Decimal`-Folge fuer einen `target_device_id`.
- **CSV/JSON-Loader** als Free-Functions:
  `load_csv_profile(path)` und `load_json_profile(path)` →
  `LoadProfile`. Format-Fehler werden als typed
  `LoadProfileFormatError`-Subklassen gemeldet (Welle-0a-Codec-
  Pattern).
- **`GridModelSnapshot v2`**: erweitert um
  `active_load_events: tuple[LoadEvent, ...]` und
  `active_load_profiles: tuple[LoadProfile, ...]`. v1-Snapshots
  (Welle-5a-Stand) bleiben **roundtrip-faehig** ueber einen
  Backward-Compat-Lesepfad.

**Welle-5b-Driftrisiko gegen M3:** Der M2-Slice-Plan §4
markiert „Replay-Source-Pfade" als M3-Material. Welle 5b
nimmt einen Teil davon vorweg, weil `GG-GRID-003` und
`GG-GRID-004` MUSS-Akzeptanz sind und Lastenheft-Lieferung in
M2 erforderlich ist. M3 baut auf Welle 5b auf: dieselbe
`LoadProfile`-Repraesentation wird in M3 fuer komplexere
Replay-Quellen (z. B. PV-Solarprofile, Stochastik) wieder-
verwendet. Welle 5b implementiert den **Loader** aktiv (kein
Stub), aber haelt das Anwendungs-Pattern bewusst klein:
keine Profil-Generatoren, kein Loop-Modus, keine
Interpolation zwischen Tick-Werten.

---

## 2. Entscheidung

### 2.1 Modul-Struktur

Welle 5b ergaenzt `hexagon/core/grid_model/loads.py` neben den
Welle-5a-Modulen:

```
hexagon/core/grid_model/
    __init__.py        # Re-Export erweitert um LoadEvent + LoadProfile +
                       #   Loader + LoadProfileFormatError
    config.py          # (Welle 5a)
    bilanz.py          # (Welle 5a)
    snapshot.py        # (Welle 5a, erweitert in Welle 5b um v2)
    loads.py           # Welle 5b: LoadEvent + LoadProfile + Loader
```

`tests/unit/hexagon/core/grid_model/` ergaenzt ein separates
`test_loads.py` (siehe ADR 0019 §5 / Welle-5a-Review L-2 —
zweites Modul fuer separaten Concern, nicht weitere
Aufspaltung der bilanz-Tests).

### 2.2 `LoadEvent` (`GG-GRID-004`)

```python
@dataclass(frozen=True, slots=True)
class LoadEvent:
    start_s: Decimal           # Welt-Zeit-Start, > 0
    duration_s: Decimal        # > 0
    target_device_id: str      # nicht-leer; Welle 6 validiert ScenarioDevice-Existenz
    power_kw: Decimal          # >= 0 (Welle 5b: Last-Pfad; negative Werte sind
                               #   GG-DEV-013-Sign-Vertrag-Verletzung)
```

**Pflicht-Invarianten** (`__post_init__`):

- Alle `Decimal`-Felder als `Decimal` typisiert
  (GG-DATA-005-Spiegel; Welle-5a-Review-M-4-Pattern).
- `start_s >= 0`, `duration_s > 0`, `power_kw >= 0`.
- `target_device_id != ""`.
- Optional Welle-5b-Pflicht: `target_device_id`-Existenz im
  Scenario wird erst in Welle 6 (TickLoop-Verdrahtung)
  validiert.

**Vertrag in Welle 6:** TickLoop iteriert pro Tick durch alle
aktiven `LoadEvent`s:

- Wenn `simulation_time_s >= start_s and simulation_time_s <
  start_s + duration_s`: das Event ist „aktiv". TickLoop
  setzt im LoadDevice via `apply_command(Command.type=
  "set_power_kw", payload={"value": power_kw})` den
  Event-Wert.
- Wenn `simulation_time_s >= start_s + duration_s`: das Event
  ist „abgelaufen". TickLoop stellt den **Vor-Event-Wert**
  wieder her (z. B. `LoadDevice._config.rated_power_kw` oder
  den vorherigen `set_power_kw`-Wert).

Welle 5b liefert die Datenstruktur, nicht die TickLoop-
Verdrahtung — das ist Welle 6.

### 2.3 `LoadProfile` (`GG-GRID-003` „Zeitreihen")

```python
@dataclass(frozen=True, slots=True)
class LoadProfile:
    target_device_id: str               # nicht-leer
    tick_values: tuple[Decimal, ...]    # Tick-indizierte Werte; alle >= 0
    tick_ms: int                        # Tick-Aufloesung des Profils, > 0
```

**Pflicht-Invarianten** (`__post_init__`):

- `target_device_id != ""`.
- `tick_values` ist Tuple mit mindestens einem Element.
- Alle `tick_values[i]` sind `Decimal` und `>= 0`.
- `tick_ms > 0`.

**Vertrag in Welle 6:** TickLoop berechnet pro Tick den
Profil-Index aus `simulation_time_ms // tick_ms`. Wenn der
Index ueber `len(tick_values)` hinausgeht, wird der **letzte
Wert** wiederholt (Welle-5b-Konvention; M3 kann Loop-/Periodisch-
Modus aktivieren). Profile-Wert wird via
`apply_command(set_power_kw, value=tick_values[index])` an den
LoadDevice gegeben.

**Tick-Resolution-Mismatch:** wenn Profil-`tick_ms` (z. B.
`100`) nicht mit Scenario-`tick_ms` (z. B. `1000`)
uebereinstimmt, wird der Profil-Wert **nicht interpoliert**;
TickLoop nutzt den Wert bei `floor(sim_time_ms /
profile.tick_ms)`. Welle 5b ist explizit gegen Interpolation
(M3-Material).

### 2.4 CSV/JSON-Loader (Free-Functions)

```python
def load_csv_profile(path: Path) -> LoadProfile: ...
def load_json_profile(path: Path) -> LoadProfile: ...
```

**CSV-Format** (`load_csv_profile`):

```csv
target_device_id,tick_ms,tick_values
load-1,1000,1.5;2.0;1.8;1.2
```

- Einzeilige Header + einzeilige Daten.
- Pflicht-Spalten: `target_device_id`, `tick_ms`, `tick_values`.
- `tick_values` als `;`-separated `Decimal`-Liste.

**JSON-Format** (`load_json_profile`):

```json
{
  "target_device_id": "load-1",
  "tick_ms": 1000,
  "tick_values": [1.5, 2.0, 1.8, 1.2]
}
```

- Pflicht-Keys: `target_device_id`, `tick_ms`, `tick_values`.
- `tick_values` als JSON-Array; numerische Werte werden als
  `Decimal` geparst (kein float-Round-Trip).

**Fehlerbehandlung** (typisiert, Welle-0a-Codec-Spiegel):

```python
class LoadProfileFormatError(GridGymError): ...
class LoadProfileFileNotFoundError(LoadProfileFormatError): ...
class LoadProfileMissingFieldError(LoadProfileFormatError): ...
class LoadProfileTypeError(LoadProfileFormatError): ...
class LoadProfileEmptyError(LoadProfileFormatError): ...
```

**Out-of-Scope (M3 oder Post-MVP):**

- Glob-/Wildcard-Pfade.
- Stochastische Profile (Welle-5a-`RandomPort` ist bewusst
  ausserhalb).
- Profil-Interpolation / Resampling.
- Streaming-Loader fuer grosse Profile (`tick_values` haelt das
  ganze Profil im Speicher).

### 2.5 `GridModelSnapshot` v1 → v2

`GridModelSnapshot` (ADR 0019 §2.5) wird in Welle 5b um zwei
Felder erweitert:

```python
@dataclass(frozen=True, slots=True)
class GridModelSnapshot:
    # ... Welle-5a-Felder ...
    active_load_events: tuple[LoadEvent, ...]      # neu
    active_load_profiles: tuple[LoadProfile, ...]  # neu
```

`to_dict()`-Mapping (Welle 5b, `version=2`):

```
{
  "version": 2,
  "config": { ... },                       # unveraendert von v1
  "model_kind": "simplified-proportional",  # unveraendert
  "current_frequency_hz": Decimal,
  "current_voltage_v": Decimal,
  "last_imbalance_kw": Decimal,
  "clamp_event_count": int,
  "active_load_events": [                  # neu: Liste von Mappings
    {
      "start_s": Decimal,
      "duration_s": Decimal,
      "target_device_id": str,
      "power_kw": Decimal,
    },
    ...
  ],
  "active_load_profiles": [                # neu: Liste von Mappings
    {
      "target_device_id": str,
      "tick_ms": int,
      "tick_values": [Decimal, ...],
    },
    ...
  ],
}
```

**`active_load_events` / `active_load_profiles` als Tuple
serialisiert zu Liste:** SnapshotEnvelope-canonical-
Kompatibilitaet (Listen sind erlaubt, Tuple in der Dataclass-
Form bleiben unveraendert).

### 2.6 Backward-Compat-Lesepfad v1 → v2

`GridModelSnapshot.from_dict` wird von einem Hartzweig
(`if version != SNAPSHOT_VERSION: raise VersionError(...)`)
auf eine **`version in {1, 2}`-Verzweigung** umgestellt:

- **v1-Read** (Welle-5a-Snapshot, ohne LoadEvents/Profiles):
  `active_load_events = ()`, `active_load_profiles = ()` als
  Defaults. Snapshot ist roundtrip-faehig (v1-Read → v2-
  Write — der Snapshot wird beim naechsten `to_dict()`
  automatisch als v2 emittiert).
- **v2-Read** (Welle-5b-Snapshot): Pflicht-Lesen der beiden
  neuen Felder; jeder LoadEvent/LoadProfile geht durch den
  Welle-0a-Codec.

`SNAPSHOT_VERSION` wird auf `2` gehoben; Welle 5b verifiziert
mit einem Pflicht-Test, dass ein v1-Snapshot ohne
LoadEvents/Profiles → v2-`GridModelBilanz` mit leeren
LoadEvent-/LoadProfile-Tupeln rekonstruiert wird.

### 2.7 Determinismus

LoadEvent + LoadProfile sind funktional pure (kein Zufall,
kein interner State). Welle-5b-Determinismus-Property:

- Gleicher LoadEvent-Set + gleicher LoadProfile-Set → byte-
  identische `LoadDevice.apply_command`-Sequenz und damit
  byte-identische Frequenz-/Spannungs-Spur (in Verbindung mit
  Welle-5a-Bilanz).
- CSV-/JSON-Loader sind deterministisch (gleiche Eingabe-
  Datei → gleicher `LoadProfile`).

`RandomPort` wird **nicht** konsumiert (analog Welle 5a).
M3-Fault-Injection in Profilen (z. B. „Mess-Ausfall in einem
Tick") wird stochastisch — separate Open-Triggers.

---

## 3. Begruendung

**Welle-5b-Lieferung statt M3-Verschiebung:** `GG-GRID-003`/
`004` sind MUSS-Akzeptanz im Lastenheft §11; M2 muss sie
liefern. Eine Verschiebung auf M3 wuerde den MVP-Anspruch
brechen. Der M3-Driftrisiko-Hinweis im M2-Slice-Plan §3
Welle 5 ist explizit: M3 baut auf der Welle-5b-Loader-
Infrastruktur auf, repliziert sie nicht.

**Separate ADR statt geteilt mit ADR 0019:** Welle 5a ist
**Physik-Modell** (Frequenz/Spannungs-Formel + Snapshot);
Welle 5b ist **Daten-/I/O-Integration** (CSV/JSON-Parser +
LoadEvent/Profile-Datenstrukturen). Vertraege, Test-Stile und
Fehler-Hierarchien divergieren — eine geteilte ADR muesste
viele Klauseln getrennt aufrufen. Separate ADRs sind
ehrlicher (Pattern-Spiegel zu Welle 4a/4b mit ADRs 0017 +
0018).

**Snapshot-Versionssprung v1 → v2 mit Backward-Compat:** ohne
Backward-Compat-Lesepfad waere jeder Welle-5a-Snapshot ein
Migrations-Risiko. Mit Backward-Compat bleibt die M2-
Welle-Migration mechanisch unkritisch. Der Lese-Pfad ist
explizit symmetrisch (v1-Read → leere LoadEvent/Profile-
Tupel; v2-Read mit Pflicht-Felder). Welle 6 erbt diese
Konvention fuer den `SnapshotEnvelope`-Versions-Bump (ADR
0015, geplant).

**Keine Profil-Interpolation:** das vereinfacht den Loader
und macht die Determinismus-Property trivial. Profile-Loop-
Modus, periodische Wiederholung, Interpolation zwischen Tick-
Werten — alles M3-Erweiterungen. Welle 5b liefert nur den
direkten `tick_values[index]`-Pfad mit Repeat-Last-Value bei
out-of-bounds.

**CSV + JSON statt nur einer Variante:** beide Formate sind
fuer unterschiedliche Datenquellen praktisch — CSV fuer
manuelle Test-Szenarien (Spreadsheet-export), JSON fuer
programmatisch generierte Profile. Der Loader-Aufwand ist
klein (zwei Free-Functions, identisches `LoadProfile`-
Ergebnis), die Akzeptanz-Verbreiterung gross.

---

## 4. Reichweite

Diese ADR gilt fuer:

- `hexagon/core/grid_model/loads.py` (vollstaendig, neu).
- `hexagon/core/grid_model/snapshot.py` (Welle-5b-Erweiterung
  v1→v2; ADR 0019 §2.5 wird durch §2.5/§2.6 hier geschaerft).
- `hexagon/core/grid_model/__init__.py` (Re-Export-Erweiterung).
- `tests/unit/hexagon/core/grid_model/test_loads.py` (neu).
- `tests/unit/hexagon/core/grid_model/test_grid_model_bilanz.py`
  (Welle-5b-Zusatz-Tests fuer v1-Backward-Compat).

Diese ADR gilt NICHT fuer:

- LoadDevice (`hexagon/core/devices/load/`; ADR 0016, Welle 3).
  Welle 5b veraendert das LoadDevice-Modul **nicht** — der
  TickLoop in Welle 6 ist die Vermittler-Schicht.
- TickLoop-Verdrahtung (Welle 6).
- Stochastische Profile (`RandomPort`-Konsum; M3).
- Profil-Interpolation / Resampling (M3).
- Multi-Profil-Strategien (mehrere Profile pro Geraet,
  Switching). Post-MVP.
- Generischer Replay-Source-Pfad fuer Telemetrie-Replay (M3 —
  `LoadProfile` ist Geraete-spezifisch, nicht der
  generische Replay-Pfad).

---

## 5. Operative Artefakte

Mit Acceptance dieser ADR (synchron mit M2-Welle-5b-PR-Merge)
liegen folgende Module:

- `src/grid_gym/hexagon/core/grid_model/loads.py` (neu):
  `LoadEvent`, `LoadProfile`, `LoadProfileFormatError`-
  Hierarchie, `load_csv_profile`, `load_json_profile`.
- `src/grid_gym/hexagon/core/grid_model/snapshot.py` erweitert
  auf `SNAPSHOT_VERSION = 2` mit Backward-Compat-Lesepfad.
- `src/grid_gym/hexagon/core/grid_model/__init__.py` Re-Export
  erweitert.
- `tests/unit/hexagon/core/grid_model/test_loads.py` neu.
- `tests/unit/hexagon/core/grid_model/test_grid_model_bilanz.py`
  ergaenzt um Snapshot-v1→v2-Backward-Compat-Pflicht-Test.

Test-Anzahl-Inkrement gegen Welle 5a wird in der Welle-5b-
Closure-Notiz verzeichnet (Erwartung: ~30..50 neue Tests).

---

## 6. Konsequenzen

**Was sich aendert:**

- `GridModelSnapshot.SNAPSHOT_VERSION` bumpt auf `2`.
- Welle 6 TickLoop konsumiert `active_load_events` und
  `active_load_profiles` pro Tick und uebersetzt sie in
  `LoadDevice.apply_command`-Aufrufe.
- Scenario-YAML-Spec (Welle 5b oder Welle 6) erweitert um
  `events:` und `load_profile:` Sektionen — fuer Welle 5b
  reicht es, dass Datenstrukturen + Loader stehen; der
  YAML-Adapter ist Welle-6-Material.

**Was load-bearing bleibt:**

- ADR 0019 (Welle-5a-Bilanz).
- ADR 0016 §2.4 (LoadDevice-Command-Surface).
- Welle-0a-Codec (`*FormatError`-Hierarchie + assert-
  Free-Functions).

**Was offen bleibt (Welle 6+):**

- TickLoop-Verdrahtung der LoadEvent/Profile.
- Scenario-YAML-Adapter fuer LoadEvents/Profiles.
- M3-Fault-Injection in Profilen.
- M3-Stochastische Profile (Solarkurven, Wolken-Modell).

---

## 7. Nicht Gegenstand dieser ADR

- **Profil-Interpolation / Resampling** zwischen Tick-Werten.
  M3.
- **Loop-/Periodisch-Modus** fuer Profile (Wert bei out-of-
  bounds = letzter Wert; kein wrap-around).
- **Stochastische Profile** (Mess-Stoerungen, fehlende
  Ablesungen). M3 Fault-Injection.
- **Generischer Replay-Source-Pfad** fuer Telemetrie-Replay
  (M3). `LoadProfile` ist Geraete-spezifisch, nicht der
  generische Pfad.
- **Multi-Profil-Strategien** pro Geraet (mehrere Profile,
  Switching). Post-MVP.
- **Streaming-Loader** fuer grosse Profile. Welle 5b haelt
  das ganze Profil im Speicher.
- **TickLoop-Verdrahtung**. Welle 6.
- **Scenario-YAML-Format-Erweiterung**. Welle 6 — Welle 5b
  liefert nur die Datenstrukturen + Loader.
- **`PV`-Profile / Solarkurven**. `LoadProfile` ist **load-
  spezifisch** (target_device_id zeigt auf LoadDevice). PV-
  Profile sind Welle-5+/M3 — eigene Datenstruktur, weil
  Sign-Konvention divergiert.
