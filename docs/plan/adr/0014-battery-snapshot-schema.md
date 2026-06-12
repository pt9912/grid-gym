# ADR 0014 — Battery-Snapshot-Schema + Command-Surface (M2 Welle 2)

**Status:** Accepted — Validierung erfolgt mit M2-Welle-2-PR-
Merge (Commits `6247228`/`48f0106`): Snapshot-Roundtrip
byte-stabil, `hypothesis @given(seed=...)`-Property gruen ueber
100 Ticks, Trigger-013-Pflicht-Test gruen mit Battery-Trace bei
`tick_ms=100`. `make gates` cache-frei gruen ohne
`CRITICAL_COV_TARGETS`-Override (Default-Branch-Coverage 92.50%).
**Datum:** 2026-05-18
**Status geaendert am:** 2026-05-18 — `Proposed → Accepted`.
**Geschaerft am:** 2026-05-18 (Welle-2-Review-Folge-Commits) —
§§2.2/2.3/2.4 ergaenzt um Snapshot-Vollstaendigkeit (device_id +
run_id + sequence), Clamp-Power-Reset-Verhalten,
Saturation-Alarm, und last-wins-Test-Pflicht. Schaerfung folgt
`ADR 0011`-Pattern (parallele Schaerfung ohne Supersedes — der
Entscheidungs-Kern in §§2.1/2.5/2.6 ist unveraendert; §§2.2-2.4
schliessen zuvor implizite Luecken).
**Erneut geschaerft am:** 2026-05-18 (Welle-3-Review-Folge —
ADR 0016 Cross-Reference) — §§3/7 klargestellt, dass `set_mode`
projektweit Welle-5-Material ist (nicht Welle-3-Material), spie-
gelnd zu ADR 0016 §7.
**Bezug:**
[`ADR 0013`](0013-device-model-protocol.md) (`DeviceModel`-Protocol,
das Battery implementiert),
[`ADR 0007`](0007-random-port.md) §5 (`RandomPort.sub_port`-
Konvention),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-ADR-
Pattern — diese ADR ist Schaerfung von ADR 0013 §2.4 fuer den
Battery-spezifischen Snapshot-Vertrag, kein Supersedes).
M2-Slice-Plan
[`done/M2-devices.md`](../planning/done-archive/M2-devices.md)
§3 Welle 2. Lastenheft §10 (`GG-BESS-001..008`),
§9.1 (`GG-DEV-010`).

---

## 1. Kontext

`BatteryDevice` ist die erste konkrete Implementation des
`DeviceModel`-Protocols (ADR 0013, Welle 1). Welle 2 muss vier
Welle-uebergreifend wirkende Entscheidungen treffen, die als
Vorlage fuer PV/Load/SmartMeter/GridConnection (Welle 3/4) dienen:

1. **Modul-Struktur** unterhalb `hexagon/core/devices/battery/`.
2. **Snapshot-Layout** (welche Felder, wie versioniert, wie zu
   `dict[str, object]` mappen, wie aus `Mapping[str, object]`
   rekonstruieren).
3. **Command-Surface** (welche `Command.type`-Werte akzeptiert
   das Geraet, wie validiert es Payloads, wann gibt es
   `ACCEPTED`/`LIMITED`/`REJECTED`/`IGNORED`).
4. **Alarm-Pfad** (`GG-BESS-002` fordert Alarme; voller
   `AlarmSinkPort` ist M3).

Diese ADR fixiert die Wahl explizit; M2 Welle 3/4 Geraete erben
das Pattern mit jeweils eigenen Folge-ADRs (`ADR 0016/0017/...`
oder analog), nicht durch Supersedes von ADR 0014.

---

## 2. Entscheidung

### 2.1 Modul-Struktur

`hexagon/core/devices/battery/`:

- `__init__.py` — Re-Export `BatteryDevice` als Paket-Symbol.
- `config.py` — `BatteryConfig` Frozen-Dataclass mit Validierung
  (`GG-BESS-008`).
- `commands.py` — Command-Typen-Parser, `BatteryAlarm`-Domain-
  Klasse, Power-/SOC-Grenz-Validierung.
- `snapshot.py` — `BatterySnapshot` Frozen-Dataclass + dict-
  Konversion (`to_dict`/`from_dict`).
- `model.py` — `BatteryDevice` (die DeviceModel-Implementation).

### 2.2 Snapshot-Layout

`BatterySnapshot` ist eine Frozen-Dataclass mit folgenden
Feldern (Welle-2-Review-Schaerfung C-1/H-1/H-2):

- `version: int` — Schema-Version (`1` in Welle 2). Bumps
  kommen ueber Folge-ADRs (z. B. wenn Welle 3 einen
  Temperatur-Zustand `GG-BESS-006` ergaenzt).
- `device_id: str` — Identitaet (`ScenarioDevice.id` aus
  `initialize()`); damit `from_snapshot(state)` einen
  funktionsfaehigen Device-Vertrag (`device.device_id`,
  `device.apply_command()`, `device.tick()`) wiederherstellen
  kann **ohne** Aufrufer-Pflicht zur erneuten `initialize()`-
  Invokation.
- `run_id: str` — `TelemetryPoint.run_id`-Wert (`GG-DATA-001`).
  Pre-init `""`; wird durch einen separaten Lifecycle-Hook
  gesetzt (siehe §2.6 unten). Persistiert in Snapshot, damit
  Resume die gleiche `run_id` weiterfuehrt.
- `sequence: int` — Monoton wachsender `TelemetryPoint.sequence`-
  Counter (`GG-ARCH-006`-Tie-Breaking). Persistiert in
  Snapshot, damit Resume nicht bei `0` neu startet und mit
  bestehenden Sequenzen kollidiert.
- `config: BatteryConfig` — vollstaendige Konfiguration eingebettet,
  damit `from_snapshot(state)` self-contained ist und keinen
  externen `ScenarioDevice` braucht.
- `soc_kwh: Decimal` — aktueller Energieinhalt (`GG-BESS-001`).
- `current_power_kw: Decimal` — aktueller Lade-/Entladestrom
  nach Ramp-Limiting (`GG-BESS-004`); negativ = Entladen,
  positiv = Laden.
- `pending_power_kw: Decimal` — letzter vom `apply_command`
  akzeptierter Soll-Wert (vor Ramp). Mehrfach-Commands im selben
  Tick: last-wins (siehe §2.3).

`snapshot()` mapped diese Felder auf `Mapping[str, object]` mit
`version` als Erst-Feld (ADR 0013 §2.4 Konvention). `from_dict`
verwendet die Welle-0a-Codec-Free-Functions
(`assert_required_keys`, `assert_int`, `assert_mapping`) und wirft
`MissingKeysError`/`WrongTypeError`/`VersionError` aus dem
generischen `SnapshotFormatError`-Baum mit
`subsystem="battery"`. Welle-2-Review-Schaerfung M-5: wenn die
in `config` eingebetteten Werte beim Reload die `BatteryConfig`-
Validierung (`__post_init__`) verletzen, wirft `from_dict`
nicht den `BatteryConfigError`-Subtyp durch, sondern fangt ihn
und reraised als `WrongTypeError("battery", "config.<feld>",
"valid", "invalid")` — Welle-6-Aufrufer fangen typisiert auf
der `SnapshotFormatError`-Ebene.

**Self-sufficient `from_snapshot`-Vertrag** (Welle-2-Review C-1):
`BatteryDevice.from_snapshot(state)` liefert eine fertig nutzbare
Device-Instanz: alle Lifecycle-Pre-init-Raises (ADR 0013 §2.6)
sind nach `from_snapshot` aufgeloest. Devices, die `RandomPort`
in `tick()` konsumieren wollen (Welle 3+ Fault-Injection), brauchen
einen zusaetzlichen `set_random(random: RandomPort)`-Hook *oder*
fragen `RandomPort` ueber den `DeviceTickContext` ab (offen fuer
M3-Slice-Diskussion). Welle 2 Battery konsumiert `RandomPort`
nicht; `_random` bleibt nach `from_snapshot` `None`.

### 2.3 Command-Surface

Battery akzeptiert ausschliesslich `Command.type ==
"set_power_kw"` in Welle 2. Andere `type`-Werte liefern
`CommandResult.IGNORED` (Protocol-konformer No-Op).

Payload-Vertrag: `{"value": Decimal}`. Welle-0a-`assert_int`/
`assert_payload_canonical_compatible` haben den strukturellen
Pfad schon abgesichert — Battery prueft semantisch:

- Wert ausserhalb `[-max_discharge_kw, max_charge_kw]`:
  → **clampen** auf naechste Grenze
  → **Alarm** mit `target=device_id`, `limit=clamp_value`,
    `result="limited"`
  → `pending_power_kw = clamp_value`, Rueckgabe `LIMITED`.
- SOC am Boden (`<= min_soc_pct`) UND Wert < 0 (Entladen):
  → **Alarm** mit `target=device_id`, `limit=min_soc_pct`,
    `result="rejected"`
  → `pending_power_kw` bleibt unveraendert, Rueckgabe `REJECTED`.
- SOC an der Decke (`>= max_soc_pct`) UND Wert > 0 (Laden):
  → analog, Rueckgabe `REJECTED`.
- Sonst:
  → `pending_power_kw = value`, Rueckgabe `ACCEPTED`.

Mehrfach-Commands im selben Tick (ADR 0013 §2.3 Ordering):
**last-wins** — der letzte `set_power_kw` in Scenario-Source-
Reihenfolge ueberschreibt `pending_power_kw`. Bewusste Wahl;
ADR 0013 §2.3 nennt `last-wins` als Default-Empfehlung fuer
Welle 2. Welle-2-Review-Schaerfung H-4: ein dedizierter Test
in `test_commands.py` pinnt die Semantik mechanisch — Welle 3+
Implementationen koennen die Test-Form kopieren.

**Reihenfolge der Pruefungen** (Welle-2-Review-Schaerfung M-8):
SOC-Grenz-Pruefung kommt VOR Power-Clamp. Begruendung:
ein Command mit `value=-700kW` bei SOC am Boden ist semantisch
ein doppelter Verstoss (gegen Power-Grenze UND gegen SOC-
Grenze). Der staerkere Verstoss (SOC) gewinnt — das Device
geht direkt auf `REJECTED`, nicht auf `LIMITED→-500kW→Clamp-
Drop` (was den Aufrufer im Glauben laesst, der Befehl sei
clamped akzeptiert, obwohl er in der naechsten Tick gar nicht
abgearbeitet werden kann). Welle-2-Erstwurf hatte die
Reihenfolge umgekehrt; Test-Pin
`test_clamped_command_at_soc_floor_rejects_not_limits` macht
den korrigierten Pfad mechanisch.

`apply_command` schreibt das Geraet **nicht** unmittelbar fort
— die tatsaechliche SOC- und Power-Aenderung passiert in
`tick(context)`. Damit ist `apply_command` eine Pure-State-
Transition `(SOC, current_power, command) → (SOC,
current_power, pending_power, alarms)`; `tick()` macht die
zeitabhaengige Fortschreibung.

### 2.4 Tick-Verhalten

`tick(context)` mit `context.tick_ms`:

1. **Ramp-Limit** (`GG-BESS-004`): `delta_power_kw` zwischen
   `current_power_kw` und `pending_power_kw` wird auf
   `ramp_kw_per_s * (tick_ms / 1000)` gekappt. Daraus folgt
   `new_power_kw`.
2. **Energiebilanz** (`GG-BESS-001/003`):
   `delta_t_hours = tick_ms / (1000 * 3600)`.
   - Laden (`power > 0`): `energy_delta = power * delta_t_hours *
     charge_efficiency`.
   - Entladen (`power < 0`): `energy_delta = power * delta_t_hours
     / discharge_efficiency`.
   - Stillstand (`power == 0`): `energy_delta = 0`.
3. **SOC-Hard-Clamp** (`GG-BESS-005`):
   `new_soc_kwh = clamp(current_soc_kwh + energy_delta,
   min_soc_pct * capacity_kwh / 100,
   max_soc_pct * capacity_kwh / 100)`. Damit kommt das Geraet
   nie ueber die konfigurierten SOC-Grenzen, auch wenn Befehle
   sie ueberschreiten wollen.

   **Welle-2-Review-Schaerfung C-2 (Power-Reset bei Sat.):**
   Wenn das Hard-Clamp greift, war ein Teil der angeforderten
   Power physikalisch nicht moeglich (Energy-Erhaltung). Battery
   reagiert mit:

   - **`_current_power_kw = 0`** und **`_pending_power_kw = 0`**
     setzen — naechster Tick startet bei 0 kW, falls keine neue
     Befehl kommt. Damit verschwindet die in-Memory-Power-Illusion
     ("Ghost-Discharge"-Risiko aus dem Welle-2-Review).
   - **Saturation-Alarm** emittieren:
     `BatteryAlarm(target=device_id, limit=min_or_max_soc_pct,
     result=LIMITED, command_id="<saturation>")`. Der spezielle
     `command_id="<saturation>"` markiert den Alarm als
     tick-getrieben (nicht command-getrieben); Welle 6 TickLoop-
     Integration kann das per String-Match filtern.

   Die Sequenz: `Befehl → apply_command (ACCEPTED/LIMITED) →
   tick(...) → SOC-Clamp greift → Power+Pending zero → Alarm`.
   Aufrufer, die die Battery weiter laden/entladen wollen,
   muessen nach dem Saturation-Alarm einen neuen `set_power_kw`-
   Befehl absetzen (bewusst kein „auto-resume" — `GG-BESS-005`
   Akzeptanz „nicht ungeprueft uebernommen" verbietet stille
   Fortschreibung).
4. **Telemetrie** (`GG-DEV-002`, `GG-DATA-001/002`):
   `TelemetryPoint`-Tupel mit Metriken
   - `("soc_pct", new_soc_kwh / capacity_kwh * 100, "pct")`,
   - `("soc_kwh", new_soc_kwh, "kWh")`,
   - `("power_kw", new_power_kw, "kW")`.
   Sortiert nach Metrikname (deterministisch). Welle 2
   liefert genau diese drei Metriken; Folgeerweiterungen
   (Temperatur, Zellspannung) sind eigene ADRs.

Decimal-Quantisierung: alle internen Berechnungen halten
mindestens 6 Nachkommastellen (`GG-DATA-005`-Soll). Telemetrie-
Werte werden vor Emission auf 6 Nachkommastellen quantisiert
via `Decimal.quantize(Decimal("0.000001"),
rounding=ROUND_HALF_EVEN)`.

### 2.5 Alarm-Pfad

`BatteryAlarm` ist eine Frozen-Dataclass:

```python
@dataclass(frozen=True, slots=True)
class BatteryAlarm:
    target_device_id: str  # = self.device_id
    limit: Decimal
    result: CommandResult  # LIMITED oder REJECTED
    command_id: str        # Bezug zum ausloesenden Command
```

Battery haelt eine interne `_alarms: list[BatteryAlarm]`, die
ueber `@property alarms -> tuple[BatteryAlarm, ...]` lesbar ist
(unveraenderliches Tupel-Snapshot der internen Liste).

Welle 2 emittiert die Alarme NICHT durch einen Port — Welle 6
TickLoop-Integration kann sie auslesen, M3 fuehrt einen
`AlarmSinkPort` ein und macht die Persistenz produktiv.
Welle-2-Tests pruefen die Alarme direkt am Device.

### 2.6 Determinismus

`BatteryDevice.tick()` ist deterministisch by-construction:

- Decimal-Arithmetik ist plattformuebergreifend stabil
  (`GG-DATA-005`).
- `RandomPort` wird in Welle 2 nicht konsumiert (keine
  stochastischen Anteile). Welle 3+ Fault-Injection wird den Port
  via `random.sub_port(...)`-Konvention nutzen.
- Telemetry-Tupel-Reihenfolge ist alphabetisch nach Metrikname
  sortiert.

Welle-2-Pflicht-Test (`test_determinism.py`): gleicher Seed +
identische Command-Sequenz + identische Tick-Folge → byte-
identische SOC-Spur ueber ≥ 100 Ticks. `hypothesis @given(
seed=integers(min_value=0))` parametrisiert.

---

## 3. Begruendung

**Snapshot self-contained mit Config:** `from_snapshot(state)`
ohne externes ScenarioDevice macht Resume aus persistiertem
Snapshot moeglich (M6 `GG-PERSIST-*`-Migrations-Slice baut darauf
auf). Der Bloat (Config-Eintraege sind ~10 Felder) ist
vernachlaessigbar gegenueber dem Vorteil.

**last-wins fuer Multi-Command-Tick:** simpelste Semantik;
Test-Aufwand minimal. Alternative `accumulate` waere physikalisch
fragwuerdig (zwei `set_power_kw`-Befehle pro Tick sollten nicht
summiert werden), `reject-later` waere asymmetrisch (warum den
ersten akzeptieren, den zweiten ablehnen?).

**SOC-Floor/Ceiling-Check als "an der Grenze"**: pragmatischer
Approximator. Eine forward-looking-Pruefung "wuerde SOC in N
Ticks ueberschreiten" ist tickabhaengig und apply_command-Pre-
Tick nicht entscheidbar (Battery weiss tick_ms erst in tick()).
Die hard-clamp in §2.4 Schritt 3 stellt sicher, dass die SOC
nie ueber min/max hinauskommt — die Rejection in apply_command
ist nur ein frueher Hinweis fuer den Aufrufer.

**Alarm-Pfad in-device statt AlarmSinkPort jetzt:** Welle-2-
Scope-Disziplin (`AlarmSinkPort` ist M3 per Roadmap). In-Device-
Sammlung erfuellt `GG-BESS-002` Akzeptanz ("Alarm wird erzeugt"),
ohne M3-Port-Surface vorzuziehen. Welle 6 TickLoop kann die
Alarme bereits einsammeln; M3 fuegt nur die Persistenz hinzu.

**`set_power_kw` als einziger Command-Type in Welle 2:** YAML-
Beispiel im Lastenheft §12.1 nutzt `set_power_kw` und `set_mode`.
`set_mode` ist projektweit Welle-5-Material (ADR 0016 §7 Cross-
Reference; Welle 3 PV/Load liefert ebenfalls nur `set_power_kw`);
Battery in Welle 2 macht den minimalen Vertrag. Unknown-Type-
IGNORED ist Protocol-konformer No-Op (ADR 0013 §2.3).

---

## 4. Reichweite

Diese ADR gilt fuer:

- `hexagon/core/devices/battery/` (vollstaendig).
- `tests/unit/hexagon/core/devices/battery/` (Test-Module).

Diese ADR gilt NICHT fuer:

- PV/Load/SmartMeter/GridConnection (Welle 3/4). Sie erben das
  **Pattern** (4 Module pro Geraet, Snapshot mit Config-Embed,
  Decimal-Quantisierung, Alarm-Property, Protocol-Adherence-
  Test), aber jede eigene ADR fixiert das jeweilige Snapshot-
  und Command-Surface.
- `AlarmSinkPort` (M3).
- Fault-Injection (M3, `GG-FAULT-001..010`).
- Snapshot-v1→v2-Bump-Mechanik im Envelope-Level (Welle 6 +
  ADR 0015).

---

## 5. Operative Artefakte

Mit Acceptance dieser ADR (synchron mit M2-Welle-2-PR-Merge)
liegen folgende Module:

- `src/grid_gym/hexagon/core/devices/battery/__init__.py` —
  Re-Export `BatteryDevice`.
- `src/grid_gym/hexagon/core/devices/battery/config.py` —
  `BatteryConfig` mit Validierung (`GG-BESS-008`).
- `src/grid_gym/hexagon/core/devices/battery/commands.py` —
  `BatteryAlarm`-Domain-Klasse + Command-Validator.
- `src/grid_gym/hexagon/core/devices/battery/snapshot.py` —
  `BatterySnapshot` + `to_dict`/`from_dict`.
- `src/grid_gym/hexagon/core/devices/battery/model.py` —
  `BatteryDevice`.
- `tests/unit/hexagon/core/devices/battery/` mit:
  - `test_config.py` — Initial-Validator + Negativ-Pfade.
  - `test_commands.py` — Command-Surface, Alarm-Emission.
  - `test_snapshot.py` — Roundtrip + Codec-Errors.
  - `test_model.py` — Protocol-Adherence + SOC-/Power-
    Fortschreibung.
  - `test_determinism.py` — Property-Test ueber ≥ 100 Ticks.
  - `test_replay_diff_tick_ms.py` — Trigger-013-Pflicht-Test
    (tick_ms=100).

Volle Test-Anzahl-Inkrement gegen Welle 1 wird in der Welle-2-
Closure-Notiz verzeichnet.

---

## 6. Konsequenzen

**Was sich aendert:**

- `make gates` ohne `CRITICAL_COV_TARGETS`-Override geht
  voraussichtlich ab Welle 2 gruen (Dockerfile-Default-Liste
  enthaelt `devices/battery`, Coverage erreicht ≥ 90 % Line +
  Branch).
- Trigger 013 (`replay-diff-tick-ms-parameter`) wird in Welle 2
  geschlossen (`test_replay_diff_tick_ms.py` mit `tick_ms=100`).

**Was load-bearing bleibt:**

- ADR 0013 Protocol-Vertrag (alle sieben Pflicht-Member,
  Lifecycle-Pre-init-Raises, Determinismus).
- Welle-0a-Codec (`SnapshotFormatError`-Hierarchie, `assert_*`-
  Free-Functions).
- M1-Domain-Modelle (`Command`, `CommandResult`, `TelemetryPoint`,
  `Quality`, `ScenarioDevice`).

**Was offen bleibt (Welle 3+-Material):**

- PV/Load-spezifische Snapshot- und Command-Schemata.
- Temperatur (`GG-BESS-006`) und Zellspannung (`GG-BESS-007`)
  — Post-MVP, eigene ADR-Erweiterung.
- TickLoop-Integration (Welle 6).
- `AlarmSinkPort` (M3).

---

## 7. Nicht Gegenstand dieser ADR

- **`set_mode`-Command** (`discharge`/`charge`/`idle`). YAML-
  Beispiel im Lastenheft erwaehnt das; Welle 2 unterstuetzt es
  nicht. Welle-3-Review-Folge-Klaerstellung: `set_mode` ist
  projektweit Welle-5-Material (Curtailment/Mode-Switching
  zusammen mit Lastprofilen) — ADR 0016 §7 spiegelt.
- **Stoechiometrische BESS-Modellierung.** Welle 2 nutzt das
  Vereinfachungsmodell aus `GG-BESS-001..005` (kein Coulomb-
  Counting, kein OCV-Lookup, keine Stromdynamik unter Ramp).
- **Tick-Loop-Integration.** Welle 6, ADR ggf. eigene.
- **Multi-Geraete-Inter-Battery-Effekte.** Welle 5 Netzbilanz
  oder M3 Multi-Agent.
