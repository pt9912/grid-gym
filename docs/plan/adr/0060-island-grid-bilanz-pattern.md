# ADR 0060 — Inselnetz-Bilanzmodell (M8 Welle 3a)

**Status:** Accepted — Validierung mit M8-Welle-3a-Lieferung
(lint/format/typecheck/arch-check/test-unit/`coverage-gate-critical`
≥ 90 % auf `grid_model` ohne neuen Target/`docs-check`/`accept-pin-check`
gruen; Determinismus-Property + Connected-Regressions-Pin. `dep-audit`
flaggt **Bestands-CVEs** in `cryptography`/`starlette` — von 3a unberuehrt,
separater Dep-Bump). Schaerfung von
[`ADR 0019`](0019-grid-model-bilanz-pattern.md) ohne Supersedes
(Erweiterungs-Pattern [`ADR 0011`](0011-schaerfung-ohne-abloesung.md);
gleicher Mechanismus wie [`ADR 0020`](0020-load-profile-and-event-pattern.md)
zu 0019).
**Datum:** 2026-06-16
**Bezug:**
[`ADR 0019`](0019-grid-model-bilanz-pattern.md) §2.2/§2.6/§2.7 (Imbalance-
Formel, Lifecycle, Determinismus — diese ADR forkt ausschliesslich den
Slack-Pfad),
[`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md) §2.7
(GridConnection-Auto-Schluss — der Insel-Pfad ist dessen Spiegel mit dem
Forming-Geraet als Slack),
[`ADR 0017`](0017-grid-connection-device-pattern.md) §2.2 (Sign-
Konvention; das Forming-Geraet absorbiert das Residual analog zum
Netzanschluss),
[`ADR 0058`](0058-diesel-generator-device-pattern.md) §2.6 +
[`ADR 0014`](0014-battery-snapshot-schema.md) §2.2 (Diesel-/Battery-
`set_power_kw`-Clamp — die Forming-Ueberlast nutzt den Geraete-eigenen
Clamp, kein neuer Constraint-Pfad in 3a),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-ADR-
Pattern). Slice-Plan
[`M8-welle-3a.md`](../planning/done/M8-welle-3a.md); Container
[`M8-welle-3.md`](../planning/done/M8-welle-3.md). Trigger
[`020`](../planning/open/020-sollte-island-grid.md) ([`GG-GRID-005`](../../../spec/lastenheft.md#gg-grid-005),
Lastenheft §11.5).

---

## 1. Kontext

[`ADR 0019`](0019-grid-model-bilanz-pattern.md) modelliert das Netz als
**Single-Bus** mit einem externen Slack: der TickLoop injiziert in jedem
Tick das Pre-Grid-Residual `generation - load - storage` als
`set_power_kw` in den `GridConnectionDevice`, sodass `imbalance_kw` per
Konstruktion `0` wird ([`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md)
§2.7). Das ist das Verhalten eines **netzgekoppelten** Systems: das
uebergeordnete Netz faengt jeden Mismatch perfekt auf.

Ein **Inselnetz** ([`GG-GRID-005`](../../../spec/lastenheft.md#gg-grid-005), Lastenheft §11.5, Trigger
[`020`](../planning/open/020-sollte-island-grid.md)) hat **keinen
externen Slack-Bus**. Stattdessen haelt ein internes **Grid-Forming-
Geraet** — typisch ein Diesel-Generator
([`ADR 0058`](0058-diesel-generator-device-pattern.md)) oder ein
Battery-Inverter ([`ADR 0014`](0014-battery-snapshot-schema.md)) — die
Bilanz und damit Frequenz/Spannung. Der Residual wird **nicht** in einen
Netzanschluss exportiert/importiert, sondern vom Forming-Geraet absorbiert
(es regelt seine eigene Leistung hoch/runter).

Welle 3a ist eine **reine Bilanz-Schaerfung im Core** — kein neues Geraet,
kein neuer Port/Adapter-Typ. Sie forkt ausschliesslich den Slack-Pfad des
TickLoop und ergaenzt zwei additive `GridModelConfig`-Felder. Der
**Connected-Default-Pfad (`is_islanded=False`) bleibt bit-genau** wie unter
[`ADR 0019`](0019-grid-model-bilanz-pattern.md)/[`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md).

---

## 2. Entscheidung

### 2.1 GridModelConfig-Erweiterung (additiv)

`GridModelConfig` (`hexagon/core/grid_model/config.py`) bekommt **zwei
additive Felder** mit backward-compat-Defaults:

- `is_islanded: bool = False` — Modus-Schalter. Default `False` =
  netzgekoppelt = heutiges Verhalten.
- `forming_device_id: str | None = None` — die ID des Grid-Forming-
  Geraets, das im Inselnetz den Slack haelt.

`__post_init__` validiert ausschliesslich **Presence** (Config-Rand,
Pattern-Spiegel zu den `*ConfigInvalidValueError`-Invarianten in
[`ADR 0019`](0019-grid-model-bilanz-pattern.md) §2.4a) und wirft
`GridModelConfigInvalidValueError`:

- `is_islanded` muss `bool` sein (kein int-Subclass-Schmuggel).
- `forming_device_id` muss `None` **oder** ein nicht-leerer `str` sein.
- **Biconditional:** `forming_device_id is not None` **genau dann wenn**
  `is_islanded`. Inselnetz ohne Forming-ID ist ein Konfigurationsfehler;
  eine Forming-ID im netzgekoppelten Modus ebenfalls (Tippfehler-Defense).

`GridModelConfig` kennt **keine Device-Registry** — die Existenz des
referenzierten Geraets wird hier **nicht** geprueft (siehe §2.3). Die
Trennung ist bewusst: die Config ist self-contained und
Snapshot-serialisierbar, ohne Geraete-Referenzen aufloesen zu muessen.

### 2.2 Forming-Geraet als Slack (TickLoop-Fork)

Heute partitioniert `_run_tick_body`
([`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md) §2.7) die
Geraete in `grid_devices` (`GridConnectionDevice`) und `non_grid_devices`,
tickt die Nicht-Grid-Geraete (erste Iteration), berechnet das Residual,
schliesst den Netzanschluss und tickt ihn (zweite Iteration).

Der **Insel-Fork** spiegelt diese Zwei-Pass-Struktur mit dem
**Forming-Geraet** in der Slack-Rolle:

1. **Erste Iteration** ueber **alle Geraete ausser dem Forming-Geraet**
   (per `device_id`-Gleichheit ausgeschlossen; ein evtl. vorhandener
   `GridConnectionDevice` tickt hier mit seiner eigenen kommandierten
   Leistung — er ist im Inselnetz **nicht** Slack). Fuellt die vier
   Bilanz-Buckets `generation`/`load`/`storage`/`grid_connection`.
2. **Residual** = `generation - load - storage + grid_connection`
   (identische Bilanz-Formel wie
   [`ADR 0019`](0019-grid-model-bilanz-pattern.md) §2.2, nur ohne den
   noch nicht getickten Forming-Anteil).
3. **Forming-Setpoint**: das Forming-Geraet muss `-residual` zur Imbalance
   beitragen. Sein Bilanz-Vorzeichen haengt vom **Bucket** ab
   (`_BILANZ_SOURCE_BUCKETS`):
   - **Generation-Bucket** (Diesel/Wind; Beitrag `+power`):
     `set_power_kw := -residual`.
   - **Storage-Bucket** (Battery/EV; Beitrag `-power`):
     `set_power_kw := +residual`.

   Formal: `setpoint = -residual` fuer Generation/GridConnection-Bucket,
   `setpoint = +residual` fuer Storage-Bucket (der einzige Bucket mit
   invertiertem Bilanz-Vorzeichen).
4. **Zweite Iteration** ueber `[forming_device]` — es tickt mit dem
   gesetzten Sollwert und fuellt seinen Bucket. `grid_model.update(...)`
   sieht dann eine geschlossene Bilanz (`imbalance_kw == 0`), **sofern das
   Forming-Geraet den Sollwert nicht clampt** (§2.6).

**Worked Example (Diesel-Insel, nur Last):** `forming = diesel-1`
(Generation), `load-1.power_kw = 10`, sonst nichts. Erste Iteration
(ohne Diesel): `generation=0, load=10, storage=0, grid_connection=0` →
`residual = 0 - 10 - 0 + 0 = -10`. Generation-Bucket →
`setpoint = -(-10) = +10`. Diesel tickt mit `+10` → `generation=10` →
`imbalance = 10 - 10 = 0`. ✓ Frequenz bleibt auf Nennwert.

**Worked Example (Battery-Insel):** `forming = battery-1` (Storage),
`load-1.power_kw = 10`. `residual = -10`. Storage-Bucket →
`setpoint = +(-10) = -10`. Battery tickt mit `-10` (Entladen;
[`ADR 0014`](0014-battery-snapshot-schema.md) §2.2 negatives `power_kw`)
→ `storage=-10` → `imbalance = 0 - 10 - (-10) = 0`. ✓

**Election:** ausschliesslich per `forming_device_id` — **kein** impliziter
„erstes Geraet"-Tie-Break (Determinismus-Vertrag, §2.5). Mehrere Forming-
Geraete / Multi-Insel-Synchronisation sind out-of-scope (§7).

### 2.3 Existenz-Validierung im TickLoop-Wiring (nicht in der Config)

Die Pruefung, dass `forming_device_id` auf ein **real registriertes**
Geraet zeigt, passiert im **TickLoop-Konstruktor** — dort, wo
`_device_by_id` aufgebaut wird (das ist die „Wiring"-Schicht, die
Config + Geraete-Liste zusammenfuehrt). Bei `is_islanded=True` und einer
unbekannten ID wirft der Konstruktor `TickLoopUnknownFormingDeviceError`
(Fail-Fast, deterministisch, einmal beim Bau statt pro Tick).

Begruendung der Schichtung: `GridModelConfig` (§2.1) ist Geraete-agnostisch
und Snapshot-serialisierbar; eine Existenz-Pruefung dort wuerde eine
Device-Registry in die Config zwingen. Die Wiring-Schicht hat die Registry
ohnehin — sie ist der natuerliche Ort fuer den Referenz-Integritaets-Check
(Pattern-Spiegel zu `AgentInvalidCommandTargetError`, das
`target_device_id` ebenfalls im TickLoop-Wiring gegen `_device_by_id`
prueft).

### 2.4 Snapshot — opt-in, kein Versions-Bump

`GridModelSnapshot` bleibt auf **Schema-Version 2**. Die zwei neuen
Config-Felder werden **opt-in** serialisiert:

- `to_dict()`: das `config`-Sub-Mapping traegt die acht Decimal-Keys
  unveraendert; `is_islanded` + `forming_device_id` werden **nur dann**
  ergaenzt, wenn `is_islanded` `True` ist. Im Default (netzgekoppelt) ist
  das `config`-Sub-Mapping **byte-identisch** zu
  [`ADR 0019`](0019-grid-model-bilanz-pattern.md) §2.5 → `EXPECTED_DEMO_*`-
  Hash-Pins unberuehrt, kein Schema-Bump noetig.
- `from_dict()`: liest `is_islanded` (Default `False`) + `forming_device_id`
  (Default `None`) **optional** aus dem `config`-Sub-Mapping. Alt-Snapshots
  (v1 wie v2) ohne die Keys lesen als netzgekoppelt — backward-compat-
  Lesepfad analog dem v1→v2-Bump
  ([`ADR 0020`](0020-load-profile-and-event-pattern.md) §2.6). Die
  Config-Presence-Invariante (§2.1) wird beim Rekonstruieren erzwungen und
  via `WrongTypeError(subsystem="grid_model", field="config")` ueberfuehrt
  (Pattern-Spiegel zu §2.4a-Reraise).

Damit ist ein Inselnetz-Snapshot self-sufficient roundtrip-faehig, ohne den
Connected-Default oder den `SnapshotEnvelope`
([`ADR 0015`](0015-snapshot-envelope-v2.md)) anzufassen. Der
`CONFIG_FIELD_NAMES`-Pflicht-Key-Block (acht Decimals) bleibt unveraendert;
die Insel-Keys sind optionale Zusatz-Keys, kein Pflicht-Set.

**Scenario-Hash opt-in (gleiche Regel):** der `scenario_hash`
(`sha256(canonical_json(asdict(scenario)))`,
`hexagon/core/scenario/loader.py`) serialisiert die volle
`GridModelConfig`-Dataclass und wuerde die zwei additiven Felder sonst
**auch im netzgekoppelten Default** aufnehmen — und damit den Hash jedes
Bestands-Szenarios (inkl. der `EXPECTED_DEMO_SCENARIO_HASH`-Pin und aller
Replay-Baselines) verschieben. Der Loader entfernt die Insel-Keys daher im
Default (`is_islanded=False`) aus der Hash-`asdict`-Form
(`_scenario_hash_payload`), **bit-genau** zur opt-in Snapshot-Regel. Nur ein
explizit islandetes Szenario traegt die Keys im Hash. So bleibt
„config-additiv ohne Schema-Bump" auch fuer den Scenario-Hash erfuellt
(der behaviorale `EXPECTED_DEMO_TELEMETRY_STREAM_HASH` ist ohnehin
unberuehrt, da `is_islanded=False` bit-genaues Verhalten liefert).

### 2.5 Determinismus + Default-Stabilitaet

- **Connected bit-genau:** der Fork aktiviert sich ausschliesslich bei
  `is_islanded=True`. Der Connected-Pfad-Code (Geraete-Partition,
  `_apply_grid_connection_auto_close`) bleibt **textlich unveraendert**;
  `is_islanded=False` liefert byte-identische Tick-Spuren und Snapshots
  (Regressions-Pin Pflicht).
- **Insel-Determinismus:** gleicher Config + identische Geraete-/Input-
  Sequenz → byte-identische `(frequency_hz, voltage_v, last_imbalance_kw,
  clamp_event_count)`-Spur ueber ≥ 100 Ticks (Hypothesis-Property,
  Spiegel zu [`ADR 0019`](0019-grid-model-bilanz-pattern.md) §2.7). Die
  Forming-Election ist deterministisch (explizite ID); die Geraete-
  Partition nutzt `device_id`-Gleichheit (Konstruktor-Reihenfolge,
  stabil).
- **Decimal-Disziplin:** der Setpoint laeuft im bestehenden
  `_tick_loop_decimal_context()` (`prec=28`, `ROUND_HALF_EVEN`) — keine
  neue Rundungsquelle.

### 2.6 Forming-Ueberlast — Geraete-Clamp, Constraint-Event deferred (3b)

Ist `|setpoint|` groesser als die Kapazitaet des Forming-Geraets, **clampt
das Geraet selbst** ueber seinen bestehenden `set_power_kw`-Validator:

- Diesel ([`ADR 0058`](0058-diesel-generator-device-pattern.md) §2.6):
  `setpoint < 0 → 0 + LIMITED`-Alarm; `setpoint > max_power_kw →
  max_power_kw + LIMITED`-Alarm.
- Battery ([`ADR 0014`](0014-battery-snapshot-schema.md)): Lade-/Entlade-
  Grenzen clampen analog.

Folge: das Residual wird **nicht vollstaendig** absorbiert, `imbalance_kw`
bleibt ungleich `0`, Frequenz/Spannung deviieren und treffen — bei
extremer Ueberlast — die bestehenden Safety-Clamps
([`ADR 0019`](0019-grid-model-bilanz-pattern.md) §2.3). Das ist **ehrlich
vereinfachtes** Inselnetz-Verhalten (eine Insel ohne ausreichende Forming-
Reserve faellt aus dem Frequenzband) und der Geraete-`LIMITED`-Alarm macht
die Ueberlast sichtbar.

Ein **dedizierter** `GridConstraintViolationEvent` fuer die Forming-
Ueberlast ist **bewusst deferred** auf
[`M8-welle-3b.md`](../planning/done/M8-welle-3b.md) (Transformator-
/Netz-Grenzen) — dort entsteht der Event-Domaintyp, den 3a dann
wiederverwenden kann. Welle 3a bleibt eine reine Slack-Umleitung
(Slice-Plan [`M8-welle-3a.md`](../planning/done/M8-welle-3a.md) §4:
„C1-Entscheidung … Moegliche Wiederverwendung des
`GridConstraintViolationEvent` aus 3b").

---

## 3. Begruendung

**Forming-als-Slack statt eigenem Inselnetz-Solver:** Der TickLoop hat mit
dem GridConnection-Auto-Schluss
([`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md) §2.7)
bereits einen Zwei-Pass-Slack-Mechanismus. Das Inselnetz ist mechanisch
dasselbe Muster mit einem **internen** statt externen Slack — das
Forming-Geraet uebernimmt die Rolle, die im netzgekoppelten Fall der
Netzanschluss spielt. Eine separate Inselnetz-Bilanzklasse waere
Duplikation; der Fork ist minimal und haelt den
[`ADR 0019`](0019-grid-model-bilanz-pattern.md)-Bilanz-Kern (§2.2-Formel)
unangetastet.

**Vorzeichen pro Bucket statt Geraete-Typ-Sonderfall:** Der einzige
Unterschied zwischen einem Generation- und einem Storage-Forming-Geraet ist
das Bilanz-Vorzeichen — und das steht bereits in `_BILANZ_SOURCE_BUCKETS`.
Den Setpoint ueber den Bucket abzuleiten (statt ueber den Geraete-Klassen-
Namen) haelt die Logik datengetrieben und automatisch konsistent mit
kuenftigen Forming-faehigen Geraeten, die sich dort registrieren.

**Existenz-Check im Wiring, Presence-Check in der Config:** Das spiegelt
die etablierte Schichtung — Format-/Presence-Invarianten am Config-Rand
(self-contained, Snapshot-fest), Referenz-Integritaet im TickLoop-Wiring
(wo die Registry liegt). Genau so trennt der TickLoop heute
`Command`-Format (Geraete-Validator) von Target-Existenz
(`AgentInvalidCommandTargetError` gegen `_device_by_id`).

**Opt-in-Serialisierung statt Schema-Bump:** Ein Versions-Bump v2→v3 wuerde
jeden Bestands-Snapshot und die `EXPECTED_DEMO_*`-Pins beruehren, obwohl
sich am netzgekoppelten Default **nichts** aendert. Die opt-in-Emission
haelt den Default byte-identisch und traegt die Insel-Information nur dort,
wo sie semantisch existiert. Der Schema-Bump bleibt 3c vorbehalten
([`M8-welle-3.md`](../planning/done/M8-welle-3.md) §6), wo die
Q-Felder mehrere Snapshots additiv erweitern.

**Forming-Ueberlast ueber Geraete-Clamp:** Die Geraete tragen ihre
Kapazitaetsgrenzen bereits als `set_power_kw`-Clamp + `LIMITED`-Alarm. Diese
Grenze im Slack-Pfad zu respektieren ist kostenlos und korrekt — ein
zusaetzlicher Netz-Constraint-Event waere 3b-Material und wuerde 3a
ueber den Slice-Schnitt hinaus aufblaehen.

---

## 4. Reichweite

Diese ADR gilt fuer:

- `hexagon/core/grid_model/config.py` (zwei additive Felder + Presence-
  Validierung).
- `hexagon/core/grid_model/snapshot.py` (opt-in Config-Serialisierung +
  backward-compat-Lesepfad).
- `hexagon/core/simulation/tick_loop.py` (Insel-Fork + Existenz-Check;
  Connected-Pfad unveraendert).
- `hexagon/core/errors.py` (`TickLoopUnknownFormingDeviceError`).
- `hexagon/core/scenario/loader.py` (`grid_model`-YAML-Sektion liest die
  optionalen Insel-Felder; `scenario_hash` opt-in via
  `_scenario_hash_payload`).
- `tests/unit/hexagon/core/grid_model/` +
  `tests/unit/hexagon/core/simulation/` +
  `tests/unit/hexagon/core/scenario/` (3a-Tests).

Diese ADR gilt NICHT fuer:

- Transformator-/Netz-Grenzen + `GridConstraintViolationEvent`
  ([`M8-welle-3b.md`](../planning/done/M8-welle-3b.md), [`GG-GRID-006`](../../../spec/lastenheft.md#gg-grid-006)).
- Blindleistung / Q + Snapshot-Schema-Bump
  ([`M8-welle-3c.md`](../planning/done/M8-welle-3c.md), [`GG-GRID-007`](../../../spec/lastenheft.md#gg-grid-007)).
- Droop-/Detail-Frequenzregelung, Schwarzstart-Synchronisation,
  Lastabwurf (§7).

---

## 5. Konsequenzen

**Was sich aendert:**

- `GridModelConfig` traegt zwei additive Felder; Bestands-Konstruktoren
  und -Snapshots bleiben gueltig (Defaults).
- Der TickLoop hat zwei Slack-Pfade (netzgekoppelt / Inselnetz), per
  `is_islanded` verzweigt. Der netzgekoppelte Pfad ist unveraendert.
- Inselnetz-Snapshots tragen die Insel-Keys im `config`-Sub-Mapping;
  Connected-Snapshots nicht (byte-identisch zu heute).

**Was load-bearing bleibt:**

- [`ADR 0019`](0019-grid-model-bilanz-pattern.md) §2.2 Bilanz-Formel
  (unveraendert; der Fork berechnet nur, **welches** Geraet den Residual
  absorbiert).
- [`ADR 0021`](0021-scenario-loader-and-tick-loop-event-wiring.md) §2.7
  Zwei-Pass-Slack-Struktur (der Insel-Pfad ist ihr Spiegel).
- [`ADR 0015`](0015-snapshot-envelope-v2.md) `SnapshotEnvelope`
  (unberuehrt).
- `_BILANZ_SOURCE_BUCKETS` (Single-Source-of-Truth fuer das Bucket-
  Vorzeichen; das Forming-Setpoint-Vorzeichen haengt daran).

**Was offen bleibt (3b/3c+):**

- `GridConstraintViolationEvent` (Forming-Ueberlast-Signal) — 3b.
- Q / Blindleistung im Inselnetz — 3c.
- Droop-/Detail-Regelung, Multi-Insel-Synchronisation, Black-Start-
  Sequenz mit Hochlauf — Post-3a-Trigger (§7).

---

## 6. Akzeptanzkriterien (Trigger 020)

- [x] `GridModelConfig` um `is_islanded`/`forming_device_id` erweitert,
      Presence-Biconditional gepinnt; YAML-`grid_model`-Sektion liest die
      optionalen Felder.
- [x] Forming-Election deterministisch (explizite ID; kein impliziter
      Tie-Break).
- [x] Frequenz-/Spannungs-Toleranzen ohne externen Slack (bestehende
      Safety-Clamps greifen).
- [x] Black-Start minimal (Init ohne `GridConnectionDevice` laeuft —
      Forming-Geraet schliesst die Bilanz).
- [x] Inselnetz-Determinismus-Property (≥ 100 Ticks byte-identisch).
- [x] `is_islanded=False` bit-genau wie heute (Connected-Pfad textlich
      unveraendert; volle Bestands-Test-Suite gruen).
- [x] 3a-Gates gruen (lint/typecheck/arch/test-unit/coverage-critical/
      docs-check/accept-pin); `EXPECTED_DEMO_*` unberuehrt (Scenario-Hash
      opt-in, §2.4; behavioraler Telemetry-Stream-Hash ohnehin stabil).
      `dep-audit`-Bestands-CVEs sind ein separater Dep-Bump.

---

## 7. Nicht Gegenstand dieser ADR

- **Schwarzstart-Synchronisation** zwischen mehreren Inselnetzen — eigener
  Trigger ([`020`](../planning/open/020-sollte-island-grid.md) Out-of-scope).
- **Droop-/Detail-Regelung** der Frequenzhaltung (Polradwinkel,
  Sekundaerregelung) — die vereinfachte proportionale Bilanz
  ([`ADR 0019`](0019-grid-model-bilanz-pattern.md) §3) bleibt.
- **Lastabwurf / Load-Shedding** bei Forming-Ueberlast — Multi-Agent-
  Kontext, separater Trigger.
- **Dedizierter Forming-Ueberlast-Constraint-Event** — deferred auf
  [`M8-welle-3b.md`](../planning/done/M8-welle-3b.md) (§2.6).
- **Blindleistung im Inselbetrieb** — [`M8-welle-3c.md`](../planning/done/M8-welle-3c.md).
