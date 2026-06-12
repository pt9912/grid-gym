# ADR 0015 — TickLoop-Snapshot-v2 im SnapshotEnvelope-Pattern (M2 Welle 6a)

**Status:** Accepted — Welle-6c-Closure (`c31052c`) liefert das
End-to-End-MVP-Demo (`tests/integration/scenarios/mvp_demo.yaml`
+ `test_mvp_demo_scenario.py`): zwei TickLoop-Laeufe mit
`tick_ms=1000` und Seed `0xC0FFEE` produzieren byte-identische
`TickResult.emitted_telemetry` ueber 100 Ticks; der
v1-→-v2-Schema-Bump und der typisierte
`TickLoopSnapshotVersionError` sind damit produktiv exerziert.
`make fullbuild` gruen ohne Override (M2-Welle-6c-Abschluss-
Gate). Welle-6a-Validierung (`27a441f`, 716 Unit-Tests) + Welle-
6a-Review-Folge (`ff45c11` / `e3909f0` / `f7f21a6` / `da8deef` /
`779fcea`, 719 Unit-Tests, C-1/M-1..M-7/L-3..L-5/H-1)
unveraendert; Welle 6c hebt nur den Status.
**Datum:** 2026-05-19
**Status geaendert am:** 2026-05-19 — `Proposed → Provisional`;
2026-05-20 — `Provisional → Accepted` (Welle-6c-Closure
`c31052c`).
**Geschaerft am:** 2026-05-19 (User-Review Pre-
Implementation, Commit `9e55940`) — Title + Inhalt auf
TickLoop-Snapshot-Version statt SnapshotEnvelope-Schema
korrigiert; bestehende `TickLoopSnapshotVersionError` wird
wiederverwendet statt neuer Klasse.
**Erneut geschaerft am:** 2026-05-19 (Welle-6a-Review-Folge,
Commit `779fcea`) — §4-Forward-Pointer fuer `device_type`-
Protocol-Property als Welle-7+/M3-Plan; Welle-6a-Hartzweig
`_DEVICE_TYPE_BY_CLASS_NAME` bleibt brittle-aber-funktionierend.
Schaerfung folgt `ADR 0011`-Pattern (parallele Schaerfung ohne
Supersedes — der Entscheidungs-Kern in §§2.2/2.3/2.4/2.5/2.6
ist unveraendert).
**Bezug:**
[`ADR 0013`](0013-device-model-protocol.md) (DeviceModel —
Welle-6a-TickLoop iteriert ueber die DeviceModel-Liste und
sammelt Per-Device-Snapshots),
[`ADR 0014`](0014-battery-snapshot-schema.md) (Battery-
Sub-Snapshot — wird ab v2 unter
`devices.battery.<battery-id>` im TickLoop-Snapshot
eingebettet),
[`ADR 0016`](0016-pv-load-device-pattern.md),
[`ADR 0017`](0017-grid-connection-device-pattern.md),
[`ADR 0018`](0018-smart-meter-device-pattern.md) (analog —
PV/Load/GridConnection/SmartMeter-Sub-Snapshots),
[`ADR 0019`](0019-grid-model-bilanz-pattern.md) §6
(Forward-Pointer: der TickLoop-Snapshot bekommt unter
`sub_snapshots` einen `grid_model`-Single-Instance-Eintrag ab
Welle 6a — diese ADR fixiert den Bruch),
[`ADR 0020`](0020-load-profile-and-event-pattern.md) (das
`grid_model`-Sub-Snapshot traegt v2-LoadEvents/Profiles —
ADR 0020-§2.5-Snapshot-v2 ist Welle-5b-Stand und unabhaengig
von dieser TickLoop-Snapshot-Versions-Welle),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Erweiterungs-
ADR-Pattern — diese ADR erweitert die M1-Welle-4-
TickLoop-Snapshot-Konvention ohne Supersedes; M1-Snapshots
werden im M2-Code-Pfad NICHT mehr gelesen, aber die M1-ADR
bleibt historisch intakt).
M2-Slice-Plan
[`done/M2-devices.md`](../planning/done-archive/M2-devices.md)
§3 Welle 6a. Lastenheft §3 (`GG-MVP-002` End-to-End-Szenario),
`GG-PERSIST-*` (M6-Lese-Migrations-Pfad).

---

## 1. Kontext

`SnapshotEnvelope` (`hexagon/core/domain/snapshot.py`) ist der
generische Wrapper um benannte Sub-Snapshots:

```python
@dataclass(frozen=True, slots=True)
class SnapshotEnvelope:
    version: int
    run_id: str
    simulation_time: int
    sub_snapshots: Mapping[str, Mapping[str, object]]
```

Der produktive Welle-4-Pfad nutzt derzeit kein
`SnapshotEnvelope`-Objekt als Rueckgabetyp, sondern ein
**envelope-foermiges TickLoop-Snapshot-Mapping** aus
`TickLoop.snapshot()`:

```python
{
  "version": int,              # TickLoop-Snapshot-Version
  "run_id": str,
  "simulation_time": int,
  "tick_count": int,
  "tick_ms": int,
  "sub_snapshots": {
    "scheduler": Mapping[str, object],
    "random_root": Mapping[str, object],
  },
}
```

**Welle-4-M1-Stand (`TickLoop.snapshot()["version"] == 1`):**
Sub-Snapshots umfassen genau `scheduler` und `random_root`.
`tick_count` und `tick_ms` sind **Top-Level-Felder** des
TickLoop-Snapshots, keine Sub-Snapshots. Die Per-Device-
Snapshots und das `grid_model` existierten in M1 nicht.

**Welle-6a-M2-Stand (`TickLoop.snapshot()["version"] == 2`):**
TickLoop hat in Welle 1-5 fuenf DeviceModel-Implementationen
und das `grid_model`-Bilanzmodell als Konsumenten bekommen.
`TickLoop.snapshot()` sammelt ab Welle 6a folgende
**zusaetzlichen** Sub-Snapshots:

- `devices.<device_type>.<device_id>` je Geraete-Instanz
  (5 MVP-Geraete: battery, pv, load, grid_connection,
  smart_meter). Der `device_type`-Segment ist Pflicht, weil
  die heutigen Per-Device-Snapshots keinen Typ tragen und
  `from_snapshot` sonst nicht dispatchen kann.
- `grid_model` (Single-Instance) — Schluessel ohne
  `devices.`-Praefix, weil `grid_model` kein Device ist
  (ADR 0019 §1).

Damit hat ein v2-TickLoop-Snapshot **sechs neue
Sub-Snapshot-Keys**, die in einem v1-Snapshot fehlen. Resume
eines v1-Snapshots im M2-Code-Pfad wuerde fehlschlagen, weil
die Devices/Bilanzmodell nicht rekonstruierbar sind.

**Strukturierender Bruch — kein additive Erweiterung:** Der
generische `SnapshotEnvelope`-Datentyp selbst aendert sich
nicht (`version: int`, `run_id: str`, `simulation_time: int`,
`sub_snapshots: Mapping[...]`). Was sich aendert, ist der
**TickLoop-Snapshot-Inhaltsvertrag**: die erwartete
`sub_snapshots`-Liste und der Resume-Dispatch. Da M2-Aufrufer
sich auf die Anwesenheit der
`devices.<device_type>.<device_id>`- und `grid_model`-
Sub-Snapshots verlassen, ist das ein nicht-rueckwaerts-
kompatibler Vertrags-Bruch — Versions-Bump ist die saubere
Signalisierung.

---

## 2. Entscheidung

### 2.1 Modul-Struktur

Welle 6a erweitert die bestehenden Module:

```
hexagon/core/domain/snapshot.py
    SnapshotEnvelope  # generischer Wrapper; Konstruktor bleibt unveraendert
hexagon/core/errors.py
    TickLoopSnapshotVersionError  # wird fuer v1-Reject weiter genutzt
hexagon/core/simulation/tick_loop.py
    TickLoop.snapshot()    # erweitert um devices.<type>.* + grid_model
    TickLoop.from_snapshot()  # Pflicht-Reject fuer v1
```

Kein neues Modul; alle Aenderungen sind Erweiterungen
bestehender Welle-1-/M1-Module.

### 2.2 Version-Bump v1 → v2

Die **TickLoop-Snapshot-Version** (`TickLoop.snapshot()
["version"]`, intern `_SNAPSHOT_VERSION`) wird in Welle 6a
von `1` auf `2` gehoben. `TickLoop.snapshot()` emittiert ab
Welle 6a ausschliesslich v2-Snapshot-Mappings; v1-Emission ist
nicht mehr moeglich.

**Konkrete Konsequenz fuer das Modul:** im
`SnapshotEnvelope`-Konstruktor selbst aendert sich **nichts**;
der `version`-Wert ist ein Daten-Feld ohne strukturelle
Wirkung und wird von `__post_init__` weiterhin nicht auf einen
konkreten Wert validiert. Der TickLoop setzt seine eigene
Top-Level-Version auf `2`; falls ein Aufrufer das Mapping in
ein `SnapshotEnvelope`-Objekt hebt, spiegelt dessen `version`
ebenfalls `2`.

### 2.3 Erwartete Sub-Snapshot-Keys in v2

Ein v2-TickLoop-Snapshot MUSS die Vereinigung der
M1-Welle-4-Sub-Snapshots **plus** der Welle-6a-Erweiterung
enthalten:

**M1-Welle-4-Sub-Snapshots (unveraendert):**
- `scheduler` — TickLoop-Scheduler-State.
- `random_root` — `RandomPort`-State (per ADR 0009/0010).

**M1-Welle-4-Top-Level-Felder (unveraendert, keine
Sub-Snapshots):**
- `run_id`.
- `simulation_time`.
- `tick_count`.
- `tick_ms`.

**Welle-6a-Erweiterung:**
- `devices.<device_type>.<device_id>` je Geraete-Instanz
  (genau 5 in einem Vollszenario; weniger in Teil-Szenarien).
  Erlaubte Welle-6a-`device_type`-Segmente:
  `battery`, `pv`, `load`, `grid_connection`, `smart_meter`.
- `grid_model` (genau 1; Single-Instance per ADR 0019 §1).

**Welle-6a-Validierungs-Vertrag (M-1-Spiegel zu ADR 0019):**
Der `SnapshotEnvelope`-Konstruktor prueft die Anwesenheit der
Pflicht-Sub-Snapshots **nicht**. Das ist Aufrufer-Pflicht
(TickLoop-`from_snapshot`-Implementierung). Begruendung:
`SnapshotEnvelope` ist generisch (M1-Layer) und kennt die
M2-Sub-Snapshot-Namen nicht; eine harte Kopplung wuerde die
Hexagon-Layer brechen.

### 2.4 v1-Reject — typisierter Fehler-Pfad

`TickLoop.from_snapshot(state)` auf einem v1-TickLoop-
Snapshot wirft den bestehenden **typisierten**
`TickLoopSnapshotVersionError`.

**Fehler-Hierarchie:** Welle 6a fuehrt **keinen** neuen
`SnapshotEnvelopeSchemaVersionError` ein. Die bestehende
Taxonomie bleibt tragend:

- `SnapshotEnvelopeError` bleibt fuer generische
  Envelope-Konstruktionsverletzungen (`MissingSubSnapshotVersionError`,
  `NonIntegerSubSnapshotVersionError`).
- `TickLoopSnapshotVersionError` bleibt fuer unbekannte
  `TickLoop.snapshot()["version"]`-Werte.

Eine Multi-Inheritance-Aenderung auf `SnapshotFormatError` ist
out-of-scope fuer diese ADR; sie waere eine eigene
Fehlerhierarchie-Schaerfung.

**Fehler-Message (Pflicht-Text):**

```
TickLoop snapshot version=1 wird in M2-Welle-6a nicht mehr
gelesen. Quellen: Lauf in M1 abgeschlossen oder Snapshot-
Migrations-Slice abwarten (M6, GG-PERSIST-*).
```

**Pflicht-Test (Welle-6a-DoD):**

`tests/unit/hexagon/core/simulation/test_snapshot_envelope_
v1_to_v2.py` baut ein v1-TickLoop-Snapshot-Mapping und
erwartet `TickLoopSnapshotVersionError`. Backward-Compat-Reader ist
**out-of-scope** fuer M2 — der M6-`GG-PERSIST-*`-Migrations-
Slice darf das nachruesten, wenn dort ein Lese-Pfad gebraucht
wird.

### 2.5 Bypass-Strategie fuer Trusted-Source-Pfade

Welle-0a hat in `SnapshotEnvelope.__post_init__` eine
**rekursive** `assert_payload_canonical_compatible`-Pruefung
fuer jeden Sub-Snapshot eingebaut (M2-Welle-0a, Trigger 014
Item 5). Bei tiefen Geraete-Snapshots (z. B. Battery mit
langer Command-Historie) summiert sich das auf O(N) je
Konstruktor-Aufruf, plus O(N) beim spaeteren
`canonical_json`-Encoding.

Fuer **Trusted-Source-Pfade** (Resume aus einem zuvor
byte-validierten Snapshot) ist die Pruefung redundant. Welle
6a entscheidet:

**Welle-6a-Variante (Default):** der eager-Check bleibt
**unkonditional**. Performance-Messung in Welle 6a/6b zeigt,
ob der O(N)-Overhead in der MVP-Demo-Szenario-Laufzeit
spuerbar wird. Wenn ja: M3 oder ein dedizierter Performance-
Slice fuehrt die Bypass-Klausel ein.

**Welle-6+-Bypass-Optionen** (out-of-scope fuer Welle 6a, in
ADR 0015 nur dokumentiert):

1. **Opt-in Kwarg:** `SnapshotEnvelope(_skip_payload_check=
   True, ...)` — Trusted-Source-Aufrufer setzen das Flag
   explizit. Default bleibt `False`.
2. **Separater Classmethod-Pfad:** `SnapshotEnvelope.
   from_validated_mapping(...)` — bypassed den eager-Check
   und vertraut dem Aufrufer, dass die Daten bereits geprueft
   sind.

Welle 6a haelt den eager-Check und fixiert die Entscheidung
fuer M3/Performance-Slice. Pattern-Spiegel zur Welle-3-Review
M-3 (Forward-Looking-Defense, die im aktuellen Welle-Minimum
unkonditional greift).

### 2.6 Unbekannte Sub-Snapshot-Keys

`SnapshotEnvelope.__post_init__` validiert pro Sub-Snapshot
nur die Welle-0a-Konvention (`version: int` als erster Key,
canonical-kompatible Payloads). Unbekannte Sub-Snapshot-
Keys werden **toleriert** — der Aufrufer (TickLoop oder
Test) entscheidet, was er mit ihnen macht.

**Begruendung:** der `SnapshotEnvelope` ist generisch; harte
Schlussel-Whitelist wuerde Forward-Compatibility brechen.
Welle 7+ koennte z. B. `agents.<id>`-Sub-Snapshots fuer
Multi-Agent (`GG-AGENT-*`) hinzufuegen, ohne dass das den
Envelope-Schema-Bruch triggert.

Wenn ein TickLoop-Aufrufer eine Pflicht-Inhalt-Liste
durchsetzen will (z. B. „v2-TickLoop-Snapshot MUSS
`grid_model`-Key haben"), macht er das in seinem
`from_snapshot`-Pfad, nicht im Envelope-Konstruktor.

### 2.7 Determinismus

`SnapshotEnvelope` selbst ist eine Frozen-Dataclass; ihre
`__post_init__`-Validierung ist deterministisch (keine
Random-/Time-/IO-Anteile). Welle 6a erbt diese Garantie
direkt.

`TickLoop.snapshot()` ist deterministisch ueber die
Geraete-Liste und das `grid_model` (Welle 1-5-Garantien),
plus die alphabetische `sub_snapshots`-Sortierung
(`__post_init__:78` iteriert ueber `sorted(...)`).

---

## 3. Begruendung

**Version-Bump statt additiver Erweiterung:** Das Hinzufuegen
von Sub-Snapshot-Keys ist technisch additiv (Mapping-Erweiterung),
aber **vertraglich** nicht: M2-Code-Pfade verlassen sich auf
die Anwesenheit der `devices.<device_type>.<device_id>` /
`grid_model`-Keys. Ein v1-TickLoop-Snapshot ohne diese Keys
wuerde im `TickLoop.from_snapshot` auf nicht-rekonstruierbaren
State stossen — fail-loud ist besser als fail-silent.

**Typisierter Fehler statt Generic-Exception:**
`TickLoopSnapshotVersionError` ist bereits die lokale
Standard-Form fuer TickLoop-Snapshot-Versionen. Diese ADR
nutzt sie weiter, statt eine zweite Envelope-spezifische
Version-Exception einzufuehren, die nicht zur bestehenden
Taxonomie passt. Aufrufer koennen den Fehler typisiert fangen
und differenziert reagieren (z. B. „lade Migrations-Tool"
vs. „abbrechen").

**Keine Backward-Compat-Lese-Migration:** Welle 6a ist nicht
der richtige Ort, um v1-Snapshots zu lesen — das ist eine
M6-`GG-PERSIST-*`-Aufgabe. Welle 6a haelt M2-Lieferung schmal:
nur Forward-Schreib-Pfad + typisierter Reject. Der M6-
Migrations-Slice kann **spaeter** einen Lese-Adapter
einziehen, ohne dass Welle 6a sich selbst dafuer architektieren
muss.

**Eager-Check bleibt unkonditional:** Welle 0a hat den Check
bewusst als Defense-in-Depth gegen Float-/Bytes-Smuggler
eingefuehrt. In Welle 6a wird der O(N)-Overhead Per-Tick
relevant, aber **nur** wenn TickLoop bei jedem Tick ein
Snapshot-Mapping baut — typische Welle-6a-Laufzeit baut dieses
Mapping nur bei `snapshot()`-Aufrufen (selten). Performance-
Messung in 6c entscheidet, ob die Bypass-Klausel in einem
Folge-Slice gebraucht wird.

**Unbekannte Keys werden toleriert:** Welle 7+ ergaenzt
moeglicherweise weitere Sub-Snapshots (`agents.*`,
`scenario_state`); eine harte Whitelist wuerde jeden dieser
Schritte zu einem Envelope-Schema-Bruch zwingen. Tolerante
Iteration ist die ehrliche Form fuer ein generisches
Wrapper-Schema.

---

## 4. Reichweite

Diese ADR gilt fuer:

- `hexagon/core/domain/snapshot.py` (keine strukturelle
  Aenderung; generischer `SnapshotEnvelope` bleibt tolerant).
- `hexagon/core/errors.py` (keine neue Envelope-Version-
  Exception; `TickLoopSnapshotVersionError` bleibt tragend).
- `hexagon/core/simulation/tick_loop.py` (`TickLoop.snapshot()`
  emittiert v2; `TickLoop.from_snapshot()` rejected v1 mit
  `TickLoopSnapshotVersionError`).
- `tests/unit/hexagon/core/simulation/test_snapshot_envelope_
  v1_to_v2.py` (Pflicht-Test fuer den Reject-Pfad).

Diese ADR gilt NICHT fuer:

- M1-Welle-4-Sub-Snapshot-Schemas (TickLoop-Scheduler,
  `RandomPort`); die bleiben unveraendert.
- Per-Geraete-Snapshot-Inhalt (ADR 0014/0016/0017/0018
  unveraendert).
- `grid_model`-Sub-Snapshot-Inhalt (ADR 0019/0020 unveraendert).
- Backward-Compat-Lesepfad fuer v1-TickLoop-Snapshots (M6
  `GG-PERSIST-*`-Migrations-Slice).
- Performance-Optimierung des eager-canonical-Check
  (M3 oder Performance-Slice).
- TickLoop-Verdrahtung der Devices/grid_model selbst (Welle
  6a-Implementation; diese ADR fixiert nur den TickLoop-
  Snapshot-Schema-Vertrag).

**Welle-6a-Review H-1 — Forward-Pointer fuer `device_type`-
Protocol-Property:** Welle 6a nutzt ein Hartzweig-Mapping
`_DEVICE_TYPE_BY_CLASS_NAME` (Klassen-Name → snake_case-String)
fuer die `devices.<device_type>.<device_id>`-Sub-Snapshot-Key-
Konstruktion. Das ist Welle-7+/M3-Drift-Risiko: Umbenennung
einer DeviceModel-Klasse (`BatteryDevice` → `BatteryDeviceV2`)
oder Subklassing (`HighVoltageGridConnectionDevice`) bricht
die Dispatch mit `TickLoopUnknownDeviceTypeError`.

Welle 7+ oder M3 sollen das Mapping durch eine **explizite
Protocol-Property** ersetzen:

```python
class DeviceModel(Protocol):
    @property
    def device_type(self) -> str: ...
```

Jedes Geraet exposed seinen Type-String direkt (z. B.
`BatteryDevice.device_type → "battery"`), TickLoop liest
`device.device_type` statt eines Side-Channel-Klassen-Namens.
Welle-6a-Hartzweig bleibt bis zur Protocol-Erweiterung als
brittler-aber-funktionierender Pfad bestehen — ein Eintrag
in der Folge-Welle-Backlog.

---

## 5. Operative Artefakte

Mit Acceptance dieser ADR (synchron mit M2-Welle-6a-PR-Merge)
liegen folgende Artefakte:

- `TickLoop.snapshot()["version"]` ist `2`.
- `TickLoop.snapshot()` emittiert ein v2-Snapshot-Mapping mit
  `devices.<device_type>.<device_id>` x N + `grid_model`
  Sub-Snapshots zusaetzlich zu den M1-Welle-4-Eintraegen.
- `TickLoop.from_snapshot(state)` mit `state["version"] == 1`
  wirft `TickLoopSnapshotVersionError`.
- Pflicht-Test in `tests/unit/.../test_snapshot_envelope_v1_
  to_v2.py` pinnt den Reject-Pfad.
- Volle Test-Anzahl-Inkrement gegen Welle 5b wird in der
  Welle-6a-Closure-Notiz verzeichnet (Erwartung: ~10..20 neue
  Tests).

---

## 6. Konsequenzen

**Was sich aendert:**

- `TickLoop.snapshot()["version"] == 2` in allen
  Welle-6a-Produkten.
- M2-Tools, die ein TickLoop-Snapshot-Mapping persistieren
  (z. B. Postgres-Adapter ueber `RunRow.snapshot_envelope`),
  serialisieren ab Welle 6a v2-Strukturen.
- M2-Tools, die ein TickLoop-Snapshot-Mapping deserialisieren,
  MUESSEN das v2-Format unterstuetzen; v1-Snapshots werden hart
  rejected.

**Was load-bearing bleibt:**

- ADR 0009/0010 (`RandomPort`-Sub-Snapshot-Schema).
- ADR 0013/0014/0016/0017/0018 (Device-Sub-Snapshot-Schemas).
- ADR 0019/0020 (`grid_model`-Sub-Snapshot-Schema, v1/v2
  Backward-Compat fuer den Inhalt, **nicht** fuer den Envelope-
  Wrap).
- M2-Welle-0a-`assert_payload_canonical_compatible`-Check.

**Was offen bleibt:**

- M6-`GG-PERSIST-*`-Lese-Migrations-Slice (v1 → v2 Auto-
  Upgrade fuer alte Snapshots; out-of-scope hier).
- Performance-Slice fuer den eager-canonical-Check
  (Trusted-Source-Bypass; M3 oder Folge-Welle).
- Welle-7+-`agents.*` / `scenario_state`-Sub-Snapshots
  (tolerante Erweiterung; kein erneuter Versions-Bump
  noetig).

---

## 7. Nicht Gegenstand dieser ADR

- **v1-Lese-Migration**. M6-`GG-PERSIST-*`. Welle 6a haelt nur
  den typisierten Reject-Pfad.
- **Performance-Optimierung des eager-canonical-Check**.
  Trusted-Source-Bypass via Opt-in-Kwarg oder Classmethod —
  dokumentiert in §2.5, aber nicht in Welle 6a implementiert.
- **Per-Geraete-/grid_model-Sub-Snapshot-Inhalts-Schaerfung**.
  ADR 0014/0016/0017/0018/0019/0020 fixieren das pro
  Geraet/Modell; diese ADR fixiert nur den TickLoop-
  Snapshot-Wrap.
- **Multi-Agent-Sub-Snapshots** (`agents.*`,
  `GG-AGENT-*`). Welle-7+-Erweiterung; tolerante Iteration
  in `__post_init__` braucht keinen weiteren Versions-Bump.
- **Scenario-Sub-Snapshot** (`scenario_state` fuer Live-
  Event-Persistierung). Welle 6b liefert die Datenstruktur;
  ob es als eigener Sub-Snapshot im Envelope landet oder im
  `grid_model`-Sub-Snapshot mitschwebt, ist Welle-6b-
  Entscheidung.
- **Whitelist-Validierung der Sub-Snapshot-Keys** im
  Envelope-Konstruktor. Welle 6a setzt das bewusst NICHT —
  TickLoop-Aufrufer durfen pruefen, was sie brauchen; das
  Envelope-Schema bleibt generisch.
