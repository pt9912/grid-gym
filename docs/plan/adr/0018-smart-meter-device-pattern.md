# ADR 0018 — SmartMeter-Aggregator-Pattern (M2 Welle 4b)

**Status:** Accepted — Validierung mit M2-Welle-4b-PR-Merge
(Commit `94efb2a`): 603 Unit-Tests gruen (vorher 545, +58
SmartMeter-Tests), `make gates` cache-frei gruen ohne
`CRITICAL_COV_TARGETS`-Override; Welle-4b-Review-Folge
(`1093b2c` / `bc94a8c` / `d3769dc` / `85dced7`) hat
H-1/M-1..M-3/L-1/L-2/L-4 adressiert (605 Unit-Tests Endstand).
Welle-4-Closure synchron mit folgendem Plan-Sync-Commit.
**Datum:** 2026-05-19
**Status geaendert am:** 2026-05-19 — `Proposed → Accepted`
(direkt, kein Provisional-Zwischenschritt; ADR 0006 §2 erlaubt
Sprung wenn der Validierungs-Spike Pflicht-Bestandteil des
Welle-PR-Merges ist).
**Geschaerft am:** 2026-05-19 (Pre-Implementation, Commit
`3cabe83` zusammen mit ADR 0017) — §§2.3/2.4 `Quality.UNKNOWN`
→ `Quality.MISSING` (UNKNOWN existiert nicht im `Quality`-Enum;
MISSING traegt die „Daten fehlen"-Semantik); §2.4 Punkt 5
Telemetrie-Liste von 2 auf 1 Punkt reduziert (`command_status`
ist String, `TelemetryPoint.value` ist `Decimal`).
**Erneut geschaerft am:** 2026-05-19 (Welle-4b-Review-Folge,
Commit `1093b2c`) — §2.2 `aggregate_metric_name`-Pflicht in
Welle 4b auf `"power_kw"` ausgeschaerft (Telemetrie-Hardcoding
in `model.py`; Welle 5+ aktiviert die Forward-Looking-
Erweiterung mit dynamischer Emission). Schaerfung folgt
`ADR 0011`-Pattern (parallele Schaerfung ohne Supersedes — der
Entscheidungs-Kern in §§2.1/2.3/2.4/2.6/2.7/2.8 ist
unveraendert).
**Bezug:**
[`ADR 0013`](0013-device-model-protocol.md) (`DeviceModel`-Protocol,
das `SmartMeterDevice` implementiert — diese ADR aendert das
Protocol NICHT, sondern fuegt eine Geraete-spezifische
Lifecycle-Methode `attach_sources(...)` hinzu, analog zur
Welle-3-Review-M-6-`attach_random(...)`-Erweiterung von
PV/Load/Battery),
[`ADR 0014`](0014-battery-snapshot-schema.md) (Vorlage fuer das
Snapshot-/Command-Pattern — SmartMeter ist die fuenfte
DeviceModel-Implementation, aber **stateless** und damit der
strukturell kleinste Snapshot der MVP-Geraete),
[`ADR 0016`](0016-pv-load-device-pattern.md) §2.2 (Sign-
Konvention, an die sich die Aggregations-Formel haengt),
[`ADR 0017`](0017-grid-connection-device-pattern.md) (parallele
Schwester-ADR fuer Welle 4a; gemeinsam liefern 0017 + 0018 die
beiden Reporting/Anschluss-Geraete, ohne erzwungene
Abstraktion),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-
ADR-Pattern — diese ADR erweitert ADR 0013 §2.4 fuer den
SmartMeter-spezifischen Snapshot-Vertrag und das
`attach_sources`-Hook, kein Supersedes).
M2-Slice-Plan
[`done/M2-devices.md`](../planning/done-archive/M2-devices.md)
§3 Welle 4b. Lastenheft §9.1 ([`GG-DEV-014`](../../../spec/lastenheft.md#gg-dev-014)).

---

## 1. Kontext

`SmartMeterDevice` ([`GG-DEV-014`](../../../spec/lastenheft.md#gg-dev-014)) ist die fuenfte und letzte
konkrete `DeviceModel`-Implementation des MVP. Strukturell ist
es das einfachste Geraet:

- **Stateless** (im Gegensatz zu Battery / GridConnection):
  kein SOC, keine kumulative Energie, kein Power-State.
  SmartMeter berechnet seine Telemetrie je Tick aus den
  Quellen neu.
- **Derived** (im Gegensatz zu PV/Load): SmartMeter erzeugt
  keine physikalische Groesse, sondern aggregiert vorhandene
  Telemetrie anderer Geraete.
- **Konfigurations-driven**: die Aggregations-Quellen kommen
  aus `aggregate_device_ids: tuple[str, ...]` und werden
  ueber das neue `attach_sources(...)`-Lifecycle-Hook
  verdrahtet.

Welle-4b-Minimum aggregiert ausschliesslich **`power_kw`** als
Summe ueber die Quell-Telemetrie. Energie-Aggregate
(`aggregated_energy_kwh` als Summe von `import_kwh`/`export_kwh`
einzelner Anschlusspunkte) sind Welle-4b-Optional / Forward-
Looking; sie werden in §2 ausdruecklich nicht festgeschrieben,
damit die Welle-4b-DoD-Liste schmal bleibt.

Eine **separate ADR** (statt einer geteilten mit GridConnection
in ADR 0017, wie ADR 0016 fuer PV+Load) ist gerechtfertigt,
weil:

- SmartMeter ist **stateless**; GridConnection ist
  **stateful** (kumulative Energie). Snapshot-Vertraege
  divergieren strukturell.
- SmartMeter braucht ein Aggregations-Quellen-Hook
  (`attach_sources`), das GridConnection nicht braucht.
- Command-Surface ist **leer** (kein produktiver Command),
  waehrend GridConnection eine `set_power_kw`-Surface hat.

Welle-4b-Minimum liefert die [`GG-DEV-014`](../../../spec/lastenheft.md#gg-dev-014)-Akzeptanz
„Minimalmodell + Beispiel + deterministischer Smoke-Test"
vollstaendig.

---

## 2. Entscheidung

### 2.1 Modul-Struktur

Spiegel zu ADR 0014 §2.1 / ADR 0016 §2.1 / ADR 0017 §2.1 —
eigenes Unterpaket unter `hexagon/core/devices/`:

```
hexagon/core/devices/smart_meter/
    __init__.py        # Re-Export SmartMeterDevice
    config.py          # SmartMeterConfig + Validator
    commands.py        # SmartMeterAlarm (minimal — kein set_*-Command)
    snapshot.py        # SmartMeterSnapshot (Frozen-Dataclass)
    model.py           # SmartMeterDevice (DeviceModel-Implementation
                       # + attach_sources-Hook)
```

Pattern-Spiegelung mit Battery / PV / Load / GridConnection.
`commands.py` traegt nur `SmartMeterAlarm` (Domain-Klasse fuer
Drain-Pfad), keinen Command-Validator-Body — es gibt keinen
produktiven Command-Surface in Welle 4b.

### 2.2 Aggregations-Scope

`SmartMeterConfig` (Frozen-Dataclass) traegt:

- `aggregate_device_ids: tuple[str, ...]` — kanonisch
  sortiert (Welle-1-Konvention; Initial-Validator pruft
  Sortierung und Eindeutigkeit, wirft `ValueError` bei
  Verstoss).
- Optional: `aggregate_metric_name: str = "power_kw"` —
  bleibt in Welle 4b auf Default; Forward-Looking-Hook fuer
  Welle 5 / Post-MVP, wenn auch `import_kwh`/`export_kwh`/
  `soc_kwh` aggregierbar werden sollen. **Welle-4b-Pflicht
  (Review-H-1, Commit folgt):** der Config-Validator lehnt
  Werte ungleich `"power_kw"` ab, weil die Telemetrie-Emission
  in `model.py` auf `aggregated_power_kw` + Unit `kW` hardcoded
  ist (siehe §2.4 Punkt 5). Ohne diese Sperre wuerde ein
  abweichender `aggregate_metric_name` zwar die korrekte
  Quell-Metric summieren, aber unter dem falschen Telemetrie-
  Label emittieren (still-falscher Drift). Welle 5+ aktiviert
  die Forward-Looking-Erweiterung zusammen mit einer
  dynamischen `_emit_telemetry`-Emission, die Metric/Unit aus
  dem Config liest.

`aggregate_device_ids` darf leer sein (`()`); leeres
Aggregat liefert `aggregated_power_kw = Decimal("0")` (kein
Fehler).

### 2.3 Quellen-Anbindung — `attach_sources`-Hook

`SmartMeterDevice` exposiert eine **post-init Lifecycle-Methode**
(nicht Teil des `DeviceModel`-Protocols):

```python
def attach_sources(self, sources_by_id: Mapping[str, DeviceModel]) -> None
```

Vertrag:

- Aufrufer-Pflicht (TickLoop / Scenario-Loader): nach
  `initialize(...)`, vor dem ersten `tick(...)`. Mapping
  enthaelt fuer jede ID aus `config.aggregate_device_ids`
  genau eine `DeviceModel`-Referenz.
- Mehrfach-Aufruf ueberschreibt; das ist erlaubt, weil
  TickLoop-Reload-Pfade (Welle 6 / M3) ggf. neu verdrahten.
- Pre-`attach_sources`-`tick(...)`-Aufruf: SmartMeter
  emittiert `aggregated_power_kw = Decimal("0")` mit
  `quality=Quality.MISSING` (statt `VALID`). Damit bleibt der
  Pre-attach-Zustand maschinell unterscheidbar, ohne einen
  separaten String-Tag-`TelemetryPoint` zu brauchen (siehe
  §2.4 Punkt 5). **Kein** Fehler — das macht den Smoke-Test
  einfacher und schliesst nicht das Welle-6-Verdrahtungsfenster.

Pattern-Analogie: `attach_random(random)` aus Welle-3-Review
M-6 — ein post-init Hook, der Implementations-spezifisch ist
und nicht zur Protocol-Surface gehoert.

**Begruendung (gegen Alternativen):**

- **Nicht via `DeviceTickContext`:** ADR 0013 §2.2 haelt den
  Context port-frei und narrow (`tick`, `simulation_time`,
  `tick_ms`). Ein `neighbor_telemetry`-Feld zu schmuggeln
  wuerde den Vertrag brechen und das DeviceModel-Protocol
  fuer ein einzelnes Geraet ueberdehnen.
- **Nicht via `initialize(scenario_device, random)`:** die
  Quell-Devices sind zur `initialize`-Zeit moeglicherweise
  noch nicht alle konstruiert (Scenario-Loader iteriert
  ueber Devices in Definitionsreihenfolge; SmartMeter koennte
  vor seinen Quellen kommen). Ein separater Hook **nach**
  allen `initialize`-Aufrufen ist sauberer.
- **Nicht via TickLoop-Lookup-Callable:** waere flexibler,
  aber Welle-4b-Minimum braucht kein Callable; die direkte
  Mapping-Referenz reicht und ist test-freundlicher.

### 2.4 Tick-Mechanik

Welle-4b-Minimum:

1. **Sources-Resolution:** fuer jede ID in
   `config.aggregate_device_ids` schlage im post-`attach_
   sources`-Mapping nach. Wenn das Mapping leer ist
   (`attach_sources` wurde nie aufgerufen) → siehe §2.3
   Default-Fallback.
2. **Reference-Lookup-Defense:** wenn `attach_sources` zwar
   aufgerufen war, aber das Mapping eine ID aus
   `aggregate_device_ids` **nicht** enthaelt → werfe
   `SmartMeterSourceMissingError` mit Klartext „Quell-Device
   `<id>` ist im Aggregations-Scope, aber nicht in
   `attach_sources(...)`-Mapping. Wahrscheinlichste Ursache:
   Scenario-Drift nach Snapshot-Resume." Kein Silent-Skip,
   kein Default-`0`-Werthandel.
3. **Aggregation:** je Quelle ueber `source.telemetry()`
   iterieren, den ersten `TelemetryPoint` mit
   `metric == config.aggregate_metric_name` aufsummieren.
   Wenn eine Quelle die Metric nicht emittiert (`telemetry()`
   ist `()` oder enthaelt keinen passenden Eintrag), wird sie
   als Beitrag `Decimal("0")` gewertet — **Silent-Skip auf
   Metric-Ebene**, **kein** Fehler. Begruendung: Pre-init-
   Quellen liefern `()` (ADR 0013 §2.6); SmartMeter darf in
   diesem Fall nicht durchstuerzen.
4. **Decimal-Aggregation:** Summen-Operation in einem
   Decimal-Localcontext-Wrapper (Welle-2-Review-M-2 / Welle-3-
   Review-M-3-Pattern), damit Praezisions-Drift zwischen
   Replay-Laeufen ausgeschlossen ist. Quantisierung des
   End-Ergebnisses: 6 NK-Stellen mit `ROUND_HALF_EVEN`.
5. **Telemetrie-Emission:** ein `TelemetryPoint`-Eintrag je
   Tick:
   - `aggregated_power_kw` (Summe, quantisiert auf 6 NK-Stellen
     mit `ROUND_HALF_EVEN`, Unit `kW`).

   Im Pre-attach-Fall (§2.3) wird derselbe `TelemetryPoint`
   mit `value=Decimal("0")` und `quality=Quality.MISSING`
   emittiert — die Pre-attach-Situation laeuft ueber das
   `Quality`-Enum (`MISSING` statt `VALID`; `MISSING` ist der
   spec-Wert aus `Quality`-Enum, der „Daten fehlen" semantisch
   am praezisesten traegt — siehe `hexagon/core/domain/quality.py`),
   nicht ueber einen
   separaten String-Tag-`TelemetryPoint` (`TelemetryPoint.value`
   ist `Decimal`, String-Tag ist strukturell nicht emittierbar).
   Reference-Lookup-Defense bleibt ein typisierter Fehler-Pfad,
   kein Telemetrie-Tag.

**Forward-Looking-Defense:** die Aggregations-Formel
behandelt jede Quelle gleich (Summe ueber `power_kw`).
Sign-Konvention der Quellen ist Quellen-Verantwortung
(ADR 0016 §2.2 / ADR 0017 §2.2); SmartMeter macht **keine**
Sign-Anpassung. Wer die SmartMeter-Summe als „Netto-Verbrauch"
interpretiert, muss die Quellen passend waehlen
(z. B. nur Load + GridConnection).

### 2.5 Snapshot-Layout

`SmartMeterSnapshot` (Frozen-Dataclass) ist der **strukturell
kleinste** Geraete-Snapshot der MVP-Geraete (Welle-2-Review
C-1-Konvention):

- `version: int` — Schema-Version (`1` in Welle 4b).
- `device_id: str` — Identitaet aus `initialize()`.
- `run_id: str` — `TelemetryPoint.run_id`, Pre-init `""`.
- `sequence: int` — monoton wachsender Telemetrie-Sequence-
  Counter (persistiert, damit Resume nicht bei `0` neu
  startet).
- `config: SmartMeterConfig` — vollstaendige Konfiguration
  inkl. `aggregate_device_ids` (damit `from_snapshot(state)`
  self-contained ist und der naechste `attach_sources`-Aufruf
  weiss, welche IDs erwartet sind).

**Was explizit NICHT im Snapshot ist** (negative Assertion,
Welle-4b-DoD-Item):

- Keine `aggregated_power_kw`-Felder. Die aggregierten Werte
  sind **derived**; sie werden zur Snapshot-Zeit nicht
  persistiert. Nach `from_snapshot(...)` wartet das Geraet
  auf den naechsten `attach_sources(...)`+`tick(...)`-Zyklus
  und berechnet die Aggregate neu.
- Kein `sources_by_id`-Mapping. Der Mapping-Inhalt ist nur
  zur Laufzeit gueltig — die referenzierten `DeviceModel`-
  Instanzen sind nicht serialisierbar.
- Kein `pending_commands`-Feld (SmartMeter hat keinen
  produktiven Command-Surface).

`snapshot()` mapped die Felder auf `Mapping[str, object]`
mit `version` als Erst-Feld (ADR 0013 §2.4 Konvention).
`from_dict(...)` nutzt die Welle-0a-Codec-Free-Functions
(`assert_required_keys`, `assert_str`, `assert_decimal`).

**Self-Sufficient-from_snapshot (Welle-2-Review C-1):**
`SmartMeterDevice.from_snapshot(state)` rekonstruiert das
Geraet ohne `initialize(...)`-Re-Run. Der naechste
`attach_sources(...)`-Aufruf muss vom TickLoop / Scenario-
Loader erfolgen, bevor `tick(...)` aufgerufen wird; ansonsten
greift der Default-Fallback aus §2.3.

**Pre-init-Snapshot-Asymmetry (Welle-3-Review H-3):** Pre-init
`snapshot()` liefert `{"version": SNAPSHOT_VERSION}` — die
Pflichtfelder fehlen. Pre-init-Snapshot ist NICHT
roundtrippable; `from_snapshot({"version": 1})` wirft
`MissingKeysError`.

### 2.6 Command-Surface

`SmartMeterDevice` hat in Welle-4b-Minimum **keinen
produktiven Command-Surface**:

- Beliebiger `Command.type` → `IGNORED` (Protocol-konformer
  No-Op, ADR 0013 §2.3).
- Drain-Pfad (`drain_alarms()` aus Welle-2-Review M-3) ist
  vorhanden, liefert aber ueblicherweise leere Listen, weil
  SmartMeter selten Alarme generiert.
- `_run_id`-Setter (`set_run_id(...)`) und `attach_random(...)`
  (Welle-3-Review-M-6-Pattern) bleiben erhalten — auch
  SmartMeter hat einen `RandomPort.sub_port` reserviert fuer
  M3-Fault-Injection.

**Mehrfach-Commands im selben Tick:** alle werden `IGNORED`;
last-wins-Semantik ist nicht relevant.

Forward-Looking: Post-MVP kann ein `set_aggregate_scope`-
Command sinnvoll werden (z. B. dynamisches Hinzufuegen/
Entfernen von `aggregate_device_ids` waehrend des Laufs).
Welle 4b sieht das nicht vor.

### 2.7 Initialisierung

Bei `initialize(scenario_device, random)` startet das Geraet
mit:

- `aggregate_device_ids = scenario_device.params["aggregate_device_ids"]`
  (kanonisch sortiert validiert; siehe §2.2).
- `_sources_by_id = {}` (leer; wird per `attach_sources(...)`
  spaeter gefuellt).

`SmartMeterDevice` hat **keinen** Power-State, daher kein
„aktiver" Default wie PV/Load (`rated_power_kw`) oder
GridConnection (`0` per §2.6). Die erste Telemetrie kommt aus
dem ersten Tick **nach** `attach_sources(...)`.

`RandomPort.sub_port("smart_meter.<device_id>")` wird in
Welle 4b-Minimum nicht konsumiert; ist via
`attach_random(...)`-Hook vorbereitet (Welle-3-Review M-6).

### 2.8 Determinismus

SmartMeter ist **bedingt deterministisch**: gleicher
`aggregate_device_ids`-Scope + gleiche Quellen-Telemetrie →
byte-identische Aggregat-Telemetrie. Welle-4b-Property-Test
(`hypothesis @given(seed=integers())`) prueft das ueber
≥ 100 Ticks mit einer Suite aus `(PvDevice, LoadDevice,
BatteryDevice, GridConnectionDevice)` als Quellen.

Da SmartMeter `RandomPort` nicht konsumiert, ist die
Determinismus-Garantie eine reine Funktion der Quellen-
Determinismus-Garantien. Welle-4b-Smoke-Test verifiziert,
dass die SmartMeter-Telemetrie keine `RandomPort`-Calls
mehr triggert als die Summe der Quellen — d.h. SmartMeter
fuegt keine eigene Entropie hinzu.

---

## 3. Begruendung

**Separate ADR statt geteilt mit GridConnection (ADR 0017):**
GridConnection ist stateful (`import_kwh`/`export_kwh`-
Akkumulation); SmartMeter ist stateless (derived
aggregation). Snapshot-Vertraege sind strukturell verschieden
(GridConnection persistiert Energie-Summen; SmartMeter
persistiert nur Config). Command-Surfaces sind ebenfalls
verschieden (GridConnection hat `set_power_kw`; SmartMeter
hat keine produktive Surface). Eine gemeinsame ADR muesste
diese Unterschiede in vielen Klauseln getrennt aufrufen —
zwei separate ADRs sind ehrlicher.

**`attach_sources`-Hook statt `DeviceTickContext`-Erweiterung:**
ADR 0013 §2.2 haelt `DeviceTickContext` bewusst narrow
(`tick`, `simulation_time`, `tick_ms`). Ein
`neighbor_telemetry: Mapping[str, ...]`-Feld wuerde den
Vertrag fuer **ein einzelnes Geraet** ueberdehnen. Das
`attach_sources`-Hook bleibt SmartMeter-spezifisch, das
DeviceModel-Protocol unveraendert.

**Stateless aggregator statt cached snapshot:** Welle-4b
koennte das letzte Aggregat im Snapshot persistieren und bei
`from_snapshot()` direkt zurueckgeben. Das waere
„konsistenter mit Battery/GridConnection", aber **falsch**:
das Aggregat ist derived; es soll bei jeder Welle-N-
Scenario-Variation neu berechnet werden, und ein
persistiertes Aggregat koennte still-divergieren, wenn die
Quellen-IDs sich aendern. Stateless ist die ehrlichere Form.

**Reference-Lookup-Defense vs. Silent-Skip:** wenn eine
`aggregate_device_ids`-Quelle nach `attach_sources(...)`-
Aufruf fehlt, ist das ein **Scenario-Drift** (z. B. nach
Snapshot-Resume mit veraendertem Szenario). Silent-Skip
wuerde die Aggregat-Telemetrie still falsch machen
(SmartMeter meldet `aggregated_power_kw = 1.5 kW` statt
`2.0 kW`, weil eine Quelle „verschwunden" ist). Ein
typisierter Fehler (`SmartMeterSourceMissingError`) zwingt
den Aufrufer zur expliziten Aufmerksamkeit.

**Pre-attach Silent-Default (statt Fehler):** im **Pre-
attach**-Fall (TickLoop hat `attach_sources` noch nicht
aufgerufen) ist ein Default-`0` mit Quality-Tag
`"sources-not-attached"` sinnvoller als ein Fehler — der
Smoke-Test soll auch ohne explizite Verdrahtung etwas
Brauchbares liefern, und das Welle-6-TickLoop-Verdrahtungs-
fenster bleibt offen. Der Unterschied zur Reference-Lookup-
Defense: dort wurde verdrahtet, aber falsch; hier wurde noch
nicht verdrahtet.

---

## 4. Reichweite

Diese ADR gilt fuer:

- `hexagon/core/devices/smart_meter/` (vollstaendig).
- `tests/unit/hexagon/core/devices/smart_meter/`.

Diese ADR gilt NICHT fuer:

- GridConnection (Welle 4a — eigene ADR 0017).
- Netzbilanzmodell (Welle 5 — `grid_model`-Pfad, kein Device).
- Energie-Aggregate (Summe von `import_kwh`/`export_kwh`).
  Forward-Looking via `aggregate_metric_name`-Config-Feld
  vorbereitet, in Welle 4b aber nicht aktiviert.
- Sub-Meter-Hierarchien (SmartMeter aggregiert SmartMeter
  aggregiert ...). Welle-4b-Minimum hat eine flache
  Aggregations-Liste; rekursive Aggregation ist Post-MVP.

---

## 5. Operative Artefakte

Mit Acceptance dieser ADR (synchron mit M2-Welle-4b-PR-Merge)
liegen folgende Module:

- `src/grid_gym/hexagon/core/devices/smart_meter/`
  (5 Module: `__init__`, `config`, `commands`, `snapshot`,
  `model`).
- `tests/unit/hexagon/core/devices/smart_meter/`
  (Welle-4b-Konvention: 5..6 Test-Module — `config`,
  `commands`, `snapshot`, `model`, `determinism`, plus
  `test_attach_sources.py` fuer den neuen Lifecycle-Hook).
- Default-`CRITICAL_COV_TARGETS` aus Dockerfile-`coverage-
  gate-critical`-Stage um `devices/smart_meter` erweitert.
- Volle Test-Anzahl-Inkrement gegen Welle 4a wird in der
  Welle-4b-Closure-Notiz verzeichnet (Erwartung: ~40..60
  neue Tests analog Welle 3a/3b/4a).

---

## 6. Konsequenzen

**Was sich aendert:**

- M2-Welle-6 TickLoop-Integration ruft `attach_sources(...)`
  fuer jede SmartMeter-Instanz nach der `initialize`-Phase
  und vor dem ersten `tick(...)`-Aufruf. TickLoop ordnet
  SmartMeter-Devices als letzte in der Tick-Reihenfolge ein,
  damit ihre Quellen pro Tick aktuelle `telemetry()` liefern.
- `SnapshotEnvelope.sub_snapshots` enthaelt ab Welle 6 einen
  fuenften `devices.<id>`-Eintrag fuer SmartMeter (Pattern
  aus ADR 0014 §2.2 / ADR 0016 §2.3 / ADR 0017 §2.3).
- Welle 5 Netzbilanzmodell kann SmartMeter-Telemetrie
  konsumieren (z. B. fuer Visualisierungs-Demos), muss aber
  nicht — die Bilanz haengt an den Roh-Geraeten, nicht am
  abgeleiteten Aggregat.

**Was load-bearing bleibt:**

- ADR 0013 DeviceModel-Protocol-Vertrag (unveraendert).
- ADR 0014 §2.2-Schaerfung (Snapshot self-sufficient).
- ADR 0016 §2.2 Sign-Konvention (SmartMeter macht keine
  eigene Sign-Anpassung; Quellen-Sign zaehlt 1:1).
- ADR 0017 (parallele Schwester-ADR).
- Welle-0a-Codec (`SnapshotFormatError`-Hierarchie).

**Was offen bleibt (Welle 5+ / Post-MVP):**

- Energie-Aggregate
  (`aggregate_metric_name = "import_kwh"`/`"export_kwh"`).
  Forward-Looking-Field bereits in Config, aber Welle 4b
  hat nur den `power_kw`-Pfad validiert.
- Rekursive Aggregation (SmartMeter aggregiert andere
  SmartMeter). Post-MVP — Welle 4b lehnt das nicht aus,
  aber testet es auch nicht.
- Tarifierung / Abrechnungs-Logik. Out-of-Scope, M6 oder
  Post-MVP.
- Fault-Injection ueber `RandomPort.sub_port` (z. B.
  Mess-Stoerungen, fehlende Ablesungen). M3.

---

## 7. Nicht Gegenstand dieser ADR

- **Dynamische Aenderung des Aggregations-Scope** waehrend
  des Laufs (`set_aggregate_scope`-Command). Welle 4b hat
  `aggregate_device_ids` als Config-Konstante; Aenderung
  erfordert neuen Lauf.
- **Sub-Meter-Hierarchien** (SmartMeter aggregiert SmartMeter
  aggregiert PV). Welle-4b-Minimum hat eine flache Liste;
  rekursive Aggregation ist nicht ausgeschlossen, aber auch
  nicht validiert.
- **Tarifierung / Energiepreis-Anbindung**
  (`aggregated_cost_eur`-Telemetrie). Out-of-Scope, Post-MVP.
- **Mess-Praezisions-Modellierung** (z. B. Class-2 vs.
  Class-A-Genauigkeit, Quantisierung auf Geraete-Ebene).
  Welle 4b hat die generische 6-NK-Stellen-Quantisierung
  aus ADR 0014 §2.5; physikalische Mess-Praezision ist
  M3-Material.
- **`set_mode`-Command** (Lade-/Liefer-Modus). Konsistent
  mit ADR 0014 §7 / ADR 0016 §7 / ADR 0017 §7: `set_mode`
  ist projektweit Welle-5+ / M3-Material.
- **OTEL-Spans pro Aggregation** ([`GG-OTEL-002`](../../../spec/lastenheft.md#gg-otel-002)). Welle 4b
  konsumiert keine OTEL-Hooks; M3.
