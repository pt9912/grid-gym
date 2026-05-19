# ADR 0017 — GridConnection-Anschlusspunkt-Pattern (M2 Welle 4a)

**Status:** Proposed
**Datum:** 2026-05-19
**Bezug:**
[`ADR 0013`](0013-device-model-protocol.md) (`DeviceModel`-Protocol,
das `GridConnectionDevice` implementiert),
[`ADR 0014`](0014-battery-snapshot-schema.md) (Vorlage fuer das
Snapshot-/Command-Pattern — `GridConnectionDevice` ist die zweite
stateful Geraete-Implementation nach Battery, ohne SOC- / Ramp-
Komplexitaet, aber mit kumulativen Energie-Summen),
[`ADR 0016`](0016-pv-load-device-pattern.md) §2.2 (Sign-Konvention
fuer die Welle-5-Netzbilanz; `GridConnectionDevice.power_kw`
faedelt sich in dieselbe Formel ein, siehe §2.2 unten),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-ADR-
Pattern — diese ADR erweitert ADR 0013 §2.4 fuer den
GridConnection-spezifischen Snapshot-Vertrag, kein Supersedes).
M2-Slice-Plan
[`in-progress/M2-devices.md`](../planning/in-progress/M2-devices.md)
§3 Welle 4a. Lastenheft §9.1 (`GG-DEV-012`).

---

## 1. Kontext

`GridConnectionDevice` (`GG-DEV-012`) ist die vierte konkrete
`DeviceModel`-Implementation nach `BatteryDevice` (ADR 0014),
`PvDevice` und `LoadDevice` (ADR 0016). Strukturell sitzt es
zwischen Battery (stateful, mit innerem Akkumulator) und
PV/Load (stateless, nur Power):

- **Stateful** wie Battery, aber der akkumulierte Zustand ist
  **kumulative Energie ueber den Anschlusspunkt** (`import_kwh`,
  `export_kwh`), nicht SOC. Es gibt keinen Wirkungsgrad, keinen
  Ramp-Limit, keinen Safety-Hard-Clamp.
- **Power-Eingangsseite analog PV/Load** — `set_power_kw`-
  Override mit `max_import_kw`/`max_export_kw`-Grenzen.

`GridConnectionDevice` ist der **Netzanschlusspunkt** des
simulierten Systems. Welle-4a-Minimum modelliert die Bilanzierung
am Anschlusspunkt: alles, was nicht durch lokale Erzeugung
(PV) oder Speicher (Battery) gedeckt wird, fliesst aus dem
Netz hinein (Import) oder zurueck (Export). Die spaetere
Welle-5-Netzbilanz koppelt das mit dem Frequenzmodell ueber
`hexagon/core/grid_model/bilanz.py`.

Eine **separate ADR** (statt einer geteilten mit SmartMeter
Welle 4b, wie ADR 0016 fuer PV+Load) ist gerechtfertigt, weil:

- GridConnection ist **stateful** (kumulative Energie-Summen
  ueberleben den Tick); SmartMeter ist **stateless**
  (Aggregations-Ergebnisse sind derived, nicht persistiert).
- Snapshot-Layouts unterscheiden sich strukturell: GridConnection
  persistiert `import_kwh`/`export_kwh`; SmartMeter persistiert
  **nichts** Aggregat-bezogenes.
- Command-Surfaces sind nominell aehnlich (`set_power_kw` bei
  GridConnection, kein produktiver Command-Surface bei
  SmartMeter), aber die Limit-Semantik bei GridConnection
  (Import-/Export-Caps) ist Welle-4a-spezifisch.

Welle-4a-Minimum liefert die `GG-DEV-012`-Akzeptanz „Minimal-
modell + Beispiel + deterministischer Smoke-Test" vollstaendig;
weitere Felder (z. B. `apparent_power_kva`, Leistungsfaktor,
Blindleistung `GG-GRID-007`) sind Post-MVP.

---

## 2. Entscheidung

### 2.1 Modul-Struktur

Spiegel zu ADR 0014 §2.1 und ADR 0016 §2.1 — eigenes
Unterpaket unter `hexagon/core/devices/`:

```
hexagon/core/devices/grid_connection/
    __init__.py        # Re-Export GridConnectionDevice
    config.py          # GridConnectionConfig + Validator
    commands.py        # set_power_kw-Validator, GridConnectionAlarm
    snapshot.py        # GridConnectionSnapshot (Frozen-Dataclass)
    model.py           # GridConnectionDevice (DeviceModel-Implementation)
```

Pattern-Spiegelung mit Battery / PV / Load: dieselbe Datei-
Aufteilung (`config/commands/snapshot/model`). Welle 4b
SmartMeter und alle Post-MVP-Geraete folgen demselben Layout.

### 2.2 Sign-Konvention

Anschlusspunkt-Bezugssystem: **lokales System**, nicht Netz.
Damit:

- `power_kw > 0` = **Import** (Energie aus dem Netz ins lokale
  System; `grid → bus`).
- `power_kw < 0` = **Export** (Energie aus dem lokalen System
  ins Netz; `bus → grid`).
- `power_kw == 0` = Balanced (lokal autark in diesem Tick).

Damit faedelt sich `GridConnectionDevice` in die Welle-5-
Netzbilanz aus ADR 0016 §2.2 ein:

```
grid_balance_kw = sum(pv.power_kw)
                - sum(load.power_kw)
                - sum(battery.power_kw)
                + sum(grid_connection.power_kw)  # GridConnection schliesst die Bilanz
```

`grid_connection.power_kw` ist die **Schluss-Variable** der
Bilanz. In einem idealen Modell ohne Verluste gilt
`grid_balance_kw = 0`; jede Abweichung wird ueber den
Anschlusspunkt ausgeglichen.

**Worked Example:** ein Verbrauchsnetz mit PV-Erzeugung,
entladender Battery und Importbedarf:

| Geraet           | `power_kw` | Bedeutung                       |
| ---------------- | ---------- | ------------------------------- |
| pv-1             | `+2.0`     | PV erzeugt 2.0 kW.              |
| load-1           | `+3.0`     | Load verbraucht 3.0 kW.         |
| battery-1        | `-0.5`     | Battery entlaedt 0.5 kW.        |
| grid-connection  | `+0.5`     | GridConnection importiert 0.5 kW (deckt Restbedarf). |

`grid_balance_kw = 2.0 - 3.0 - (-0.5) + 0.5 = 0`. Bilanz
geht auf, Import-Pfad aktiv.

Spiegel-Beispiel mit Export-Ueberschuss: `pv=+3.0`,
`load=+1.0`, `battery=+1.0` (Laden):

| Geraet           | `power_kw` | Bedeutung                       |
| ---------------- | ---------- | ------------------------------- |
| pv-1             | `+3.0`     | PV erzeugt 3.0 kW.              |
| load-1           | `+1.0`     | Load verbraucht 1.0 kW.         |
| battery-1        | `+1.0`     | Battery laedt 1.0 kW.           |
| grid-connection  | `-1.0`     | GridConnection exportiert 1.0 kW (Ueberschuss ans Netz). |

`grid_balance_kw = 3.0 - 1.0 - 1.0 + (-1.0) = 0`. Bilanz
geht auf, Export-Pfad aktiv.

Welle 5 implementiert die Netzbilanz mit exakt dieser Formel;
Welle 6 verdrahtet den TickLoop so, dass `grid_connection.
power_kw` aus der Restbilanz berechnet wird (oder per Scenario-
Event explizit gesetzt — dann ist die Bilanz nicht garantiert
geschlossen und der Restposten geht in die Frequenz-/Spannungs-
Abweichung).

**Welle-4a-Minimum:** der Set-Point kommt ueber `set_power_kw`-
Commands (Scenario-Event oder Test-Helper); die automatische
Restbilanz-Berechnung ist Welle 5/6-Material.

### 2.3 Snapshot-Layout

`GridConnectionSnapshot` ist eine Frozen-Dataclass mit
folgenden Feldern (ADR-0014-§2.2-Spiegel + ADR-0016-§2.3-
Spiegel):

- `version: int` — Schema-Version (`1` in Welle 4a). Bumps
  kommen ueber Folge-ADRs (z. B. wenn Welle 4b oder M3
  Blindleistung `GG-GRID-007` ergaenzt).
- `device_id: str` — Identitaet (`ScenarioDevice.id` aus
  `initialize()`).
- `run_id: str` — `TelemetryPoint.run_id`-Wert (`GG-DATA-001`),
  Pre-init `""` bis `set_run_id(...)`. Spiegelt ADR 0014 §2.2 /
  ADR 0016 §2.3.
- `sequence: int` — monoton wachsender Telemetrie-Sequence-
  Counter (`GG-ARCH-006`-Tie-Breaking). Persistiert, damit
  Resume nicht bei `0` neu startet.
- `config: GridConnectionConfig` — vollstaendige Konfiguration
  eingebettet (`max_import_kw`, `max_export_kw`,
  `nominal_voltage_v`), damit `from_snapshot(state)` self-
  contained ist.
- `current_power_kw: Decimal` — aktueller Power-Wert am
  Anschlusspunkt, Sign-Konvention §2.2.
- `pending_power_kw: Decimal` — letzter vom `apply_command`
  akzeptierter Soll-Wert (vor Limit-Clamp). Mehrfach-Commands
  im selben Tick: last-wins (ADR 0014 §2.3 / ADR 0016 §2.4
  Konvention).
- `import_kwh: Decimal` — kumulative importierte Energie seit
  `initialize(...)`. Nicht-negativ (durch Tick-Mechanik
  garantiert, §2.5).
- `export_kwh: Decimal` — kumulative exportierte Energie seit
  `initialize(...)`. Nicht-negativ.

`snapshot()` mapped diese Felder auf `Mapping[str, object]`
mit `version` als Erst-Feld (ADR 0013 §2.4 Konvention).
`from_dict(...)` nutzt die Welle-0a-Codec-Free-Functions
(`assert_required_keys`, `assert_str`, `assert_decimal`,
`assert_payload_canonical_compatible` — Welle-3-Review-L-1-
Migration).

**Self-Sufficient-from_snapshot (Welle-2-Review C-1):**
`GridConnectionDevice.from_snapshot(state)` rekonstruiert das
Geraet **ohne** Re-Run von `initialize(...)`. Die kumulativen
Summen `import_kwh`/`export_kwh` werden direkt aus dem
Snapshot uebernommen — kein impliziter Reset auf `0`. Test
(Welle-4a-DoD): nach `Roundtrip = from_snapshot(snapshot())`
ist `Roundtrip.import_kwh == device.import_kwh` byte-stabil.

**Pre-init-Snapshot-Asymmetry (Welle-3-Review H-3):** Pre-init
`snapshot()` (vor `initialize(...)`) liefert
`{"version": SNAPSHOT_VERSION}` — die Pflichtfelder fehlen.
Pre-init-Snapshot ist NICHT roundtrippable; `from_snapshot(
{"version": 1})` wirft `MissingKeysError`. Der
`from_snapshot(device.snapshot()) == device`-Vertrag gilt nur
post-init.

### 2.4 Command-Surface

`GridConnectionDevice` akzeptiert ausschliesslich
`Command.type == "set_power_kw"`. Andere Typen → `IGNORED`
(Protocol-konformer No-Op, ADR 0013 §2.3 / ADR 0016 §2.4).

Payload: `{"value": Decimal}`. Welle-2-Review M-7
(payload-None-Defensive) und Welle-3-Review M-2
(Alarm-`(result, limit, limit_unit)`-Tupel) werden
gespiegelt:

- `value > max_import_kw`: clamp auf `max_import_kw` →
  `LIMITED` + Alarm mit
  `limit=max_import_kw`, `limit_unit="kW"`, Begruendung:
  „Import-Cap erreicht".
- `value < -max_export_kw`: clamp auf `-max_export_kw` →
  `LIMITED` + Alarm mit
  `limit=-max_export_kw`, `limit_unit="kW"`, Begruendung:
  „Export-Cap erreicht".
- Sonst: `ACCEPTED`, `pending_power_kw = value`.

**Kein `REJECTED`-Pfad fuer Vorzeichen.** Im Gegensatz zu
PV/Load (ADR 0016 §2.4) hat GridConnection keinen Sign-Vertrag,
der Negative ausschliesst — beide Vorzeichen sind valide
(Import/Export). `REJECTED` greift nur bei strukturell
ungueltigen Payloads (z. B. fehlender `value`-Key, nicht-
numerisches `value`).

Mehrfach-Commands im selben Tick: last-wins (Konvention aus
ADR 0014 §2.3 / ADR 0016 §2.4 spiegeln).

### 2.5 Tick-Mechanik

Welle-4a-Minimum:

1. **Power-Aufschreibung:** `new_power_kw = self._pending_power_kw`
   nach Limit-Clamp. Kein Ramp-Limit, kein Wirkungsgrad — der
   Anschlusspunkt ist ideal.
2. **Energie-Akkumulation:** `tick_dauer_s = tick_ms / 1000`,
   `delta_kwh = abs(new_power_kw) * (tick_dauer_s / 3600)`.
   - Wenn `new_power_kw > 0`: `self._import_kwh += delta_kwh`.
   - Wenn `new_power_kw < 0`: `self._export_kwh += delta_kwh`.
   - Wenn `new_power_kw == 0`: keine Aenderung.
   Damit sind beide Summen monoton nicht-fallend (Welle-4a-
   Invariante; durch Test verifiziert).
3. **Telemetrie-Emission:** drei `TelemetryPoint`-Eintraege je
   Tick (deterministisch nach Metrikname sortiert; spiegelt das
   Battery-Pattern aus ADR 0014 §2.4, das ebenfalls drei numerische
   Metriken emittiert):
   - `export_kwh` (kumulativ, Quantisierung 6 NK-Stellen, Unit `kWh`),
   - `import_kwh` (kumulativ, Quantisierung 6 NK-Stellen, Unit `kWh`),
   - `power_kw` (aktueller Wert, Quantisierung 6 NK-Stellen, Unit `kW`).

   **Kein `command_status`-TelemetryPoint:** `TelemetryPoint.value`
   ist `Decimal` (siehe `hexagon/core/domain/telemetry.py`),
   ein String-Tag ist also strukturell nicht emittierbar.
   Command-Status laeuft analog Battery / PV / Load ueber den
   Alarm-Pfad (`drain_alarms()`-Methode + `GridConnectionAlarm`-
   Domain-Klasse).

Quantisierung wie Battery / PV / Load:
`value.quantize(Decimal("0.000001"), ROUND_HALF_EVEN)`.
Decimal-Localcontext-Wrapper (Welle-2-Review M-2 / Welle-3-
Review M-3) spiegelt — Tick-Body in
`with _device_decimal_context()`.

**Forward-Looking-Defense (Welle-3-Review M-3-Pattern):**
Welle 4a rechnet bereits `delta_kwh = abs(new_power_kw) *
(tick_ms / 3600000)` — eine echte Decimal-Multiplikation, im
Gegensatz zum trivialen PV/Load-Tick. Der Localcontext-Wrapper
hat hier also bereits einen sichtbaren Effekt (anders als bei
PV/Load Welle 3, wo er reine Vorsorge war).

### 2.6 Initialisierung

Bei `initialize(scenario_device, random)` startet das Geraet
mit:

- `pending_power_kw = Decimal("0")` (Default-Balanced, kein
  Import, kein Export).
- `current_power_kw = Decimal("0")`.
- `import_kwh = Decimal("0")`.
- `export_kwh = Decimal("0")`.

Damit liefert der erste Tick `power_kw = 0`,
`import_kwh = 0`, `export_kwh = 0` ohne dass der Aufrufer
einen Command absetzen muss. Aenderung folgt per
`apply_command` (Scenario-Event oder Test-Helper).

**Default-Begruendung:** Anders als PV/Load (Default
`rated_power_kw`, ADR 0016 §2.6) hat GridConnection keinen
naturgemaess „aktiven" Default — der Anschlusspunkt soll
nicht spontan importieren oder exportieren, sondern nur das,
was die Bilanz vorgibt. Welle 6 / M3 koppelt das spaeter an
die Netzbilanz (siehe §2.2 oben).

`RandomPort.sub_port("grid_connection.<device_id>")` wird in
Welle 4a-Minimum nicht konsumiert; bleibt fuer M3-Fault-
Injection reserviert (Spannungs-Drops, Frequenz-Spikes —
`GG-FAULT-005`/`007`).

### 2.7 Determinismus

`GridConnectionDevice` ist funktional pure ueber `_pending_
power_kw` + Tick-Mechanik. Welle-4a-Smoke-Test prueft das per
Property (Welle-1-Konvention):

- Identische Command-Sequenz + identische Tick-Folge →
  byte-identische Telemetrie ueber ≥ 100 Ticks.
- `import_kwh`/`export_kwh`-Monotonie ueber ≥ 100 Ticks
  (Hypothesis-Property).

`RandomPort` wird nicht konsumiert; ist aber per
`attach_random(...)`-Hook (Welle-3-Review M-6) vorbereitet,
falls M3-Fault-Injection Spannungs-/Frequenz-Streams
braucht.

---

## 3. Begruendung

**Separate ADR statt Erweiterung von ADR 0016:** PV/Load und
GridConnection teilen oberflaechlich die Struktur (Power +
`set_power_kw`), aber semantisch sind sie verschieden —
GridConnection ist **stateful** (kumulative Energie-Summen),
PV/Load sind **stateless**. Der Snapshot-Vertrag weicht ab
(zwei zusaetzliche `_kwh`-Felder; Pre-init-Defaults sind
`0` statt `rated_power_kw`). Eine geteilte ADR muesste diese
Unterschiede in vielen Klauseln getrennt aufrufen — separate
ADRs sind ehrlicher.

**Pattern-Stabilitaet mit Battery:** GridConnection ist
strukturell „Battery ohne SOC / Ramp / Wirkungsgrad" — die
kumulative Energie-Aufschreibung am Anschlusspunkt ersetzt
die SOC-Fortschreibung im Battery-Modell. Die identische
Datei-Struktur, identisches Snapshot-Layout (mit den
Welle-2-Review-Erweiterungen) und identische `set_power_kw`-
Command-Form macht das Pattern fuer Welle 4b SmartMeter und
Welle 6 TickLoop-Integration mechanisch nutzbar.

**Welle-4a-Minimum bewusst klein:** kein automatischer
Bilanz-Schluss (das ist Welle 5/6), keine Blindleistung, kein
Leistungsfaktor. Welle 4a erfuellt `GG-DEV-012` als
„Minimalmodell + Beispiel + deterministischer Smoke-Test"
vollstaendig; SOLLTE-Erweiterungen aus §11 (`GG-GRID-005..
007`) sind Post-MVP.

**Sign-Konvention bewusst „Bezug = lokales System" (nicht
„Bezug = Netz"):** Damit ist `power_kw > 0` aus Sicht des
Anschlusspunkts „Energie kommt rein". Das spiegelt die
typische Konvention in Energiemanagement-Systemen (Zaehler
zeigt positive Werte bei Bezug, negative bei Einspeisung)
und vereinfacht die Welle-5-Bilanz (Vorzeichen-Vertrag in
ADR 0016 §2.2 spiegelt 1:1).

---

## 4. Reichweite

Diese ADR gilt fuer:

- `hexagon/core/devices/grid_connection/` (vollstaendig).
- `tests/unit/hexagon/core/devices/grid_connection/`.

Diese ADR gilt NICHT fuer:

- SmartMeter (Welle 4b — eigene ADR 0018).
- Netzbilanzmodell (Welle 5 — `grid_model`-Pfad, kein Device).
- Frequenz-/Spannungs-Modell (Welle 5 — `GG-GRID-001..004`).
- Inselnetz-Faehigkeit (`GG-GRID-005` SOLLTE, Post-MVP).
- Transformatorgrenzen (`GG-GRID-006` SOLLTE, Post-MVP).
- Blindleistung / Leistungsfaktor (`GG-GRID-007` SOLLTE,
  Post-MVP).

---

## 5. Operative Artefakte

Mit Acceptance dieser ADR (synchron mit M2-Welle-4a-PR-Merge)
liegen folgende Module:

- `src/grid_gym/hexagon/core/devices/grid_connection/`
  (5 Module: `__init__`, `config`, `commands`, `snapshot`,
  `model`).
- `tests/unit/hexagon/core/devices/grid_connection/`
  (Welle-4a-Konvention: 5 Test-Module — `config`, `commands`,
  `snapshot`, `model`, `determinism`).
- Default-`CRITICAL_COV_TARGETS` aus Dockerfile-`coverage-
  gate-critical`-Stage um `devices/grid_connection`
  erweitert.
- Volle Test-Anzahl-Inkrement gegen Welle 3b wird in der
  Welle-4a-Closure-Notiz verzeichnet (Erwartung: ~40..60
  neue Tests analog Welle 3a/3b).

---

## 6. Konsequenzen

**Was sich aendert:**

- M2-Welle-6 TickLoop-Integration kann `GridConnectionDevice`
  einheitlich neben `BatteryDevice`, `PvDevice`, `LoadDevice`
  konsumieren — alle vier satisfizieren das DeviceModel-
  Protocol identisch.
- Welle 5 Netzbilanzmodell kann ueber die `power_kw`-
  Telemetrie der vier Geraete aggregieren (Sign-Konvention
  §2.2 spiegelt ADR 0016 §2.2).
- `SnapshotEnvelope.sub_snapshots` enthaelt ab Welle 6 einen
  vierten `devices.<id>`-Eintrag (Pattern aus ADR 0014 §2.2
  +ADR 0016 §2.3).

**Was load-bearing bleibt:**

- ADR 0013 DeviceModel-Protocol-Vertrag.
- ADR 0014 §2.2-Schaerfung (Snapshot self-sufficient).
- ADR 0016 §2.2 Sign-Konvention (faedelt 1:1 weiter).
- Welle-0a-Codec (`SnapshotFormatError`-Hierarchie).

**Was offen bleibt (Welle 5+-Material):**

- Automatischer Bilanz-Schluss am Anschlusspunkt (Restposten
  geht in `grid_balance_kw`). Welle 5/6.
- Frequenz-/Spannungs-Abweichungs-Auswirkung auf
  `GridConnectionDevice.telemetry()` — `GG-GRID-001`/`002`
  modellieren das im Bilanzmodell, nicht im Device. Welle 5.
- Fault-Injection ueber `RandomPort.sub_port` (Spannungs-
  Drops, Frequenz-Spikes, Anschluss-Trips). M3.

---

## 7. Nicht Gegenstand dieser ADR

- **Automatische Restbilanz-Berechnung** am Anschlusspunkt
  (Welle 5/6 — das Netzbilanzmodell oder der TickLoop
  berechnen `grid_connection.power_kw = -(pv - load -
  battery)` und setzen es per `set_power_kw`-Command). Welle
  4a hat nur den manuellen Pfad ueber Scenario-Events.
- **Blindleistung / Leistungsfaktor / Apparent-Power**
  (`GG-GRID-007` SOLLTE, Post-MVP). Welle 4a hat nur
  Wirkleistung `power_kw`.
- **Spannungs-/Frequenz-Telemetrie am Anschlusspunkt**
  (`GG-GRID-001`/`002` — wird vom Netzbilanzmodell Welle 5
  berechnet und ueber `grid_model`-Snapshot persistiert, nicht
  ueber `GridConnectionDevice`).
- **Mehrere Anschlusspunkte mit unterschiedlichen
  Spannungsebenen** (Transformatorgrenzen, `GG-GRID-006`
  SOLLTE). Welle 4a unterstuetzt N `GridConnectionDevice`-
  Instanzen, aber alle auf derselben Spannungsebene
  (`nominal_voltage_v`).
- **Anschluss-Trip / Inselbildung** (`GG-GRID-005` SOLLTE).
  M3 Fault-Injection.
- **Kumulative-Energie-Reset** (z. B. taeglich, monatlich
  fuer Abrechnungszwecke). Welle 4a haelt die Summen monoton
  ueber den ganzen Lauf. Reset-Pfad ist Post-MVP.
- **`set_mode`-Command** (z. B. Inselbetrieb vs. Netz-
  parallel-Modus). Konsistent mit ADR 0014 §7 / ADR 0016 §7:
  `set_mode` ist projektweit Welle-5+/M3-Material.
