# ADR 0016 — PV + Load Generation/Consumption-Device-Pattern (M2 Welle 3)

**Status:** Provisional — Validierung erfolgt mit M2-Welle-3-PR-
Merge (Smoke-Tests ueber 100 Ticks fuer beide Geraete, Snapshot-
Roundtrip, Protocol-Adherence). `Provisional → Accepted` synchron
mit Welle-3-Closure.
**Datum:** 2026-05-18
**Bezug:**
[`ADR 0013`](0013-device-model-protocol.md) (`DeviceModel`-Protocol),
[`ADR 0014`](0014-battery-snapshot-schema.md) (Vorlage fuer das
Snapshot-/Command-Pattern — ADR 0016 ist die einfachere Variante
ohne SOC-/Ramp-/Safety-Komplexitaet),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-ADR-
Pattern — diese ADR ist Erweiterung von ADR 0013 §2.4 fuer den
PV/Load-Snapshot-Vertrag, kein Supersedes).
M2-Slice-Plan
[`in-progress/M2-devices.md`](../planning/in-progress/M2-devices.md)
§3 Welle 3. Lastenheft §9.1 (`GG-DEV-011` PV, `GG-DEV-013` Load).

---

## 1. Kontext

`PvDevice` (`GG-DEV-011`) und `LoadDevice` (`GG-DEV-013`) sind die
zweiten und dritten konkreten `DeviceModel`-Implementationen nach
`BatteryDevice` (ADR 0014, Welle 2). Beide sind strukturell
deutlich einfacher als die Battery:

- **Kein SOC-State** — sie sammeln nichts an.
- **Kein Wirkungsgrad** — was sie melden, ist die direkte Power.
- **Kein Ramp-Limit** — Power-Aenderungen sind tickweise instant.
- **Kein Safety-Hard-Clamp** — Power-Grenzen kommen ueber die
  `apply_command`-Validierung, nicht via Tick-Mechanik.

Damit haben PV und Load eine fast identische Struktur. Eine
gemeinsame ADR ist effizienter als zwei separate; die wenigen
Unterschiede (Sign-Konvention, Metric-Name) sind in §2.2 / §2.3
explizit ausgezeichnet.

Welle 3 liefert das **konstante Modell**: PV emittiert konstant
`rated_power_kw`, Load emittiert konstant `rated_power_kw`.
Override via `set_power_kw`-Command. Zeitreihen-Profile
(Tages-Solarkurve, Lastprofile) und Replay-Pfade (CSV/JSON-
Lines) kommen mit Welle 5 (Netzbilanzmodell-Integration) bzw.
M3 (Replay-Source-Verkabelung). Die Lastenheft-Akzeptanz
„Minimalmodell + Beispiel + deterministischer Smoke-Test"
(`GG-DEV-011`/`013`) ist mit der Welle-3-Lieferung erfuellt.

---

## 2. Entscheidung

### 2.1 Modul-Struktur

Spiegel zu ADR 0014 §2.1 — fuer jedes Geraet ein eigenes
Unterpaket unter `hexagon/core/devices/`:

```
hexagon/core/devices/pv/
    __init__.py        # Re-Export PvDevice
    config.py          # PvConfig + Validator (GG-BESS-008-Analogie)
    commands.py        # set_power_kw-Validator, PvAlarm
    snapshot.py        # PvSnapshot (Frozen-Dataclass)
    model.py           # PvDevice (DeviceModel-Implementation)

hexagon/core/devices/load/
    __init__.py        # Re-Export LoadDevice
    config.py          # LoadConfig
    commands.py        # set_power_kw-Validator, LoadAlarm
    snapshot.py        # LoadSnapshot
    model.py           # LoadDevice
```

Pattern-Spiegelung gegenueber Battery: dieselbe Datei-Aufteilung
(config/commands/snapshot/model). Welle 3+ Welle 4-Geraete
folgen demselben Layout.

### 2.2 Sign-Konvention

- **PV** emittiert positive `power_kw` (Erzeugung; `>= 0`).
  PV verbraucht NICHT — eine negative Power-Anforderung ist
  semantisch ungueltig und wird mit `REJECTED` beantwortet.
- **Load** emittiert positive `power_kw` (Verbrauch; `>= 0`).
  Load erzeugt NICHT — eine negative Power-Anforderung ist
  ungueltig und wird mit `REJECTED` beantwortet.

Damit gilt fuer das spaetere Welle-5-Netzbilanzmodell:

```
grid_balance_kw = sum(pv.power_kw) - sum(load.power_kw)
                  - sum(battery.power_kw)
```

(Battery ist signed; positives Battery-Power = laden = grid-
Konsum.)

### 2.3 Snapshot-Layout

`PvSnapshot` und `LoadSnapshot` haben das Welle-2-Review-Schema
(self-sufficient, ADR 0014 §2.2-Schaerfung):

- `version: int` (= `1` in Welle 3).
- `device_id: str`.
- `run_id: str`.
- `sequence: int`.
- `config: PvConfig|LoadConfig`.
- `current_power_kw: Decimal`.
- `pending_power_kw: Decimal`.

`to_dict()` mit `version` als Erst-Feld (ADR 0013 §2.4).
`from_dict(...)` nutzt die Welle-0a-Codec-Free-Functions, faengt
Config-Reload-Verletzungen als `WrongTypeError` (analog ADR 0014
§2.2-Schaerfung M-5).

`BatteryConfig` traegt 9 Felder; `PvConfig`/`LoadConfig` tragen
nur `rated_power_kw: Decimal` (positiv). Welle 4+ erweitert
ggf. um `forecast_kw`-Feld (siehe §7 Out-of-Scope).

### 2.4 Command-Surface

Beide Geraete akzeptieren ausschliesslich
`Command.type == "set_power_kw"`. Andere Typen → `IGNORED`
(Protocol-konformer No-Op, ADR 0013 §2.3).

Payload: `{"value": Decimal}`. Welle-2-Review M-7
(payload-None-Defensive) und M-8 (Reihenfolge: erst Wertebereich-
Pruefung, dann Power-Clamp) werden gespiegelt:

- `value < 0`: REJECTED + Alarm
  (`limit=Decimal("0")`, `limit_unit="kW"`, Begruendung:
  „Sign-Vertrag des Geraetes verletzt").
- `value > rated_power_kw`: clamp auf `rated_power_kw` →
  LIMITED + Alarm.
- Sonst: ACCEPTED, `pending_power_kw = value`.

Mehrfach-Commands im selben Tick: last-wins (ADR 0014 §2.3-
Konvention spiegelt).

### 2.5 Tick-Mechanik

Welle-3-Minimum (ADR 0014 §2.4-Vereinfachung):

1. Kein Ramp-Limit. `new_power_kw = self._pending_power_kw`.
2. Keine Energiebilanz, kein SOC. PV/Load haben keinen
   internen State, der sich tick-weise akkumuliert.
3. Telemetrie-Emission: ein einziger `TelemetryPoint` mit
   Metric `power_kw`, Unit `"kW"`, Quality `VALID`, Value =
   `new_power_kw.quantize(Decimal("0.000001"), ROUND_HALF_EVEN)`.

Decimal-Localcontext-Wrapper (Welle-2-Review M-2) spiegeln —
Tick-Body in `with _device_decimal_context()`.

### 2.6 Initialisierung

Bei `initialize(scenario_device, random)` startet das Geraet
mit `pending_power_kw = rated_power_kw` (Default-Output =
Nennleistung). Damit liefert der erste Tick sofort
`current_power_kw = rated_power_kw` ohne dass der Aufrufer
einen Command absetzen muss. Aenderung folgt per `apply_command`.

### 2.7 Determinismus

PV/Load sind funktional pure (kein Zufall, kein interner State
ueber Power-Werte hinaus). Welle-3-Smoke-Test prueft das per
Property: identische Command-Sequenz + identische Tick-Folge
→ byte-identische Telemetrie ueber ≥ 100 Ticks (analog ADR 0014
§2.6).

`RandomPort` wird nicht konsumiert; bleibt fuer Welle 3+ M3-
Fault-Injection reserviert (analog Welle 2 Battery).

---

## 3. Begruendung

**Eine ADR statt zwei:** PV und Load haben dieselbe Skeleton-
Struktur (rated_power + set_power_kw-Override + power_kw-
Telemetrie). Die wenigen Unterschiede (Sign-Konvention,
Metric-Name, semantische Interpretation) sind in §2.2 / §2.3
auf zwei Saetze begrenzt. Zwei separate ADRs waeren 90 %
duplizierter Inhalt.

**Pattern-Stabilitaet mit Battery:** identische Datei-
Struktur (`config/commands/snapshot/model`), identisches
Snapshot-Layout (mit den Welle-2-Review-Erweiterungen
device_id/run_id/sequence), identische `set_power_kw`-Command-
Form. Welle 4 SmartMeter/GridConnection und Welle 6 TickLoop-
Integration koennen das Pattern mechanisch ausnutzen.

**Welle-3-Minimum bewusst klein:** kein Generationsprofil, kein
Replay-Source-Pfad. Welle 5+ Netzbilanzmodell und M3
Replay-Integration erweitern; aber Welle 3 erfuellt
`GG-DEV-011`/`013` als „Minimalmodell + Beispiel +
deterministischer Smoke-Test" vollstaendig.

---

## 4. Reichweite

Diese ADR gilt fuer:

- `hexagon/core/devices/pv/` (vollstaendig).
- `hexagon/core/devices/load/` (vollstaendig).
- `tests/unit/hexagon/core/devices/pv/` und `load/`.

Diese ADR gilt NICHT fuer:

- SmartMeter / GridConnection (Welle 4 — eigene ADR 0017).
- Netzbilanzmodell (Welle 5 — `grid_model`-Pfad, kein Device).
- Zeitreihen-Profile / Replay-Source-Pfade (Welle 5 / M3).
- Forecast-Felder in Telemetrie (`GG-FUTURE-*`-Erweiterung,
  Post-MVP).

---

## 5. Operative Artefakte

Mit Acceptance dieser ADR (synchron mit M2-Welle-3-PR-Merge)
liegen folgende Module:

- `src/grid_gym/hexagon/core/devices/pv/` (5 Module).
- `src/grid_gym/hexagon/core/devices/load/` (5 Module).
- `tests/unit/hexagon/core/devices/pv/` (5 Test-Module:
  config, commands, snapshot, model, determinism).
- `tests/unit/hexagon/core/devices/load/` (analog).

Volle Test-Anzahl-Inkrement gegen Welle 2 wird in der Welle-3-
Closure-Notiz verzeichnet.

---

## 6. Konsequenzen

**Was sich aendert:**

- M2-Welle-6 TickLoop-Integration kann `PvDevice`, `LoadDevice`
  und `BatteryDevice` einheitlich konsumieren — alle drei
  satisfizieren das DeviceModel-Protocol identisch.
- Welle 5 Netzbilanzmodell kann ueber die `power_kw`-Telemetrie
  der drei Geraete aggregieren (Sign-Konvention §2.2).

**Was load-bearing bleibt:**

- ADR 0013 DeviceModel-Protocol-Vertrag.
- ADR 0014 §2.2-Schaerfung (Snapshot self-sufficient).
- Welle-0a-Codec (`SnapshotFormatError`-Hierarchie).

**Was offen bleibt (Welle 5+-Material):**

- Zeitreihen-Profile (Tages-Solarkurve fuer PV,
  Lastgang-Profil fuer Load). Welle 5 Replay-Source.
- Forecast-Telemetrie (`forecast_kw`-Metric). Post-MVP.
- Inselnetz-Verhalten von PV (Frequenz-Halten,
  `GG-GRID-005` SOLLTE). Post-MVP.

---

## 7. Nicht Gegenstand dieser ADR

- **`set_mode`-Command** (z. B. PV-Curtailment-Modi). YAML-
  Beispiel im Lastenheft §12.1 erwaehnt es; Welle 3 unterstuetzt
  es nicht.
- **PV-Wirkungsgrad-Modellierung** (DC→AC, Wechselrichter-
  Curve). Welle-3-Minimum ist „rated_power_kw direkt".
- **Lastprofil-Saettigung** (z. B. „Load springt auf 200 % bei
  Heizungs-Anschalt-Spike"). Welle 5 Szenario-Events koennen
  das ueber `set_power_kw`-Events modellieren; Welle 3 hat den
  konstanten Pfad.
- **Negative-Power-Acceptance** (PV als Schein-Last, Load als
  Schein-Erzeuger). Sign-Konvention §2.2 schliesst das aus.
