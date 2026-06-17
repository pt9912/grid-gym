# ADR 0053 — Comm-Failure-Wrapper: Read-Fehler → `MISSING`-Quality + `adapter_communication_lost`-Alarm (M7 Welle 3b)

**Status:** Accepted — gezogen 2026-06-12 mit M7-Welle-X-C1
(M7-Closure-Welle). Provisional-Schritt 2026-06-11 (direkter
`Proposed → Provisional`-Sprung mit M7-Welle-3b-C1).
**Datum:** 2026-06-11
**Status geaendert am:** 2026-06-11 — `Proposed → Provisional`;
2026-06-12 — `Provisional → Accepted` (M7-Welle-X-Closure).
**Bezug:**

- [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
  — Lifecycle-/Status-Pfad.
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) — Schaerfung-
  ohne-Supersedes-Pattern (Form-Anker; ADR 0053 schaerft
  ADR 0030 + ADR 0040 additiv, kein bestehender Vertrag wird
  abgeloest).
- [`ADR 0030`](0030-device-protocol-port-surface.md) §2.1/§2.2 —
  `DeviceProtocolPort`-Surface (`start`/`stop`/`read`/`write`,
  typisierte Error-Hierarchie, Caller-getriebener Lifecycle);
  der Wrapper implementiert dieselbe Surface (Composition).
- [`ADR 0040`](0040-alarm-aggregation-and-stream-port.md) —
  `Alarm`-Domain (9 Felder) + Severity-Konvention (§2.1-Tabelle)
  + `alarm_id_source`-Injection (Decision 16) +
  `AlarmStreamPort` (Decision 17); ADR 0053 ergaenzt einen
  vierten Alarm-Code ohne Schema-Change.
- [`ADR 0024`](0024-observability-port-trio.md) §4.5 —
  `OtelSpanWrappedDeviceProtocolPort`-Praezedenz
  (`_protocol_otel_wrap.py`; Composition-Wrapper um
  `DeviceProtocolPort`, Best-Effort-Robustheit).
- [`M7-welle-3b.md`](../planning/done-archive/M7-welle-3b.md) —
  Slice-Doc (Decisions 3b-D-1..D-8); ADR 0053 fixiert D-1..D-6.
- [`M7-welle-3.md`](../planning/done-archive/M7-welle-3.md) —
  Welle-3-Gruppenplan (D-4-Scope-Schalter → §2.1; ADR-Numbering
  D-3).
- [Trigger 035](../planning/done-archive/035-safe-003-comm-failure-missing-quality.md)
  — [`GG-SAFE-003`](../../../spec/lastenheft.md#gg-safe-003)-partial-Lücken-Verankerung; wird mit 3b-C3
  aufgeloest (`done/`).
- [`../../user/safe-001-004-quality-pipeline.md`](../../user/safe-001-004-quality-pipeline.md)
  — Quality-Pipeline-Audit (Flip-Ziel ⚠ → ✓).

---

## 1. Kontext

[`GG-SAFE-003`](../../../spec/lastenheft.md#gg-safe-003) (Lastenheft §20 Z. 1365-1371, MUSS) verlangt:
Kommunikationsausfaelle werden erkannt — dokumentierter
Fehlerstatus, betroffene Telemetrie `missing` oder `stale`,
Alarm mit Ziel, Startzeit und Ursache. Das M6-Welle-5a-Audit
stufte die ID als ⚠ partial ein (SmartMeter-pre-attach-`MISSING`
+ Adapter-String-Read-`INVALID` vorhanden; Verbindungsverlust-
Quality + Alarm fehlen).

**Code-Ist-Stand (verifiziert, Welle-3-C0-/3b-C0-Audit):**

- **Erkennung existiert, Folge fehlt:** alle fuenf
  Protocol-Adapter werfen bei Read-Fehlern typisierte
  `DeviceProtocolPortReadError`-Subklassen — am praezisesten
  IEC 61850 mit `Iec61850PortReadConnectionLostError`
  (mid-flight-Session-Drop, `protocol_iec61850/_port.py:265`).
  Kein Adapter mappt sie auf `Quality.MISSING` oder einen Alarm.
- **Adapter sind bewusst lauf-kontext-frei:** die Read-Pfade
  bauen `TelemetryPoint`s mit Platzhaltern (`run_id=""`,
  `tick=0`, `simulation_time=0`, `sequence=0` —
  „Caller-Verantwortung", z. B. `protocol_modbus/_port.py:
  306-325`). Ein `Alarm` braucht aber `run_id` +
  `simulation_time_ms`.
- **MQTT-`read() → None`** bei leerer Queue ist regulaerer
  Non-Blocking-Poll, kein Ausfall.
- **Kein produktiver `read()`-Pfad:** der `TickLoop` haelt
  `protocol_ports` nur fuer Start/Stop-Lifecycle; `read()`
  rufen ausschliesslich Test-Siblings; das Demo-Wiring
  uebergibt keine `protocol_ports`.
- **Wrapper-Praezedenz:** `OtelSpanWrappedDeviceProtocolPort`
  wrappt alle fuenf Adapter einheitlich; Alarm-Emission laeuft
  heute ausschliesslich Device-seitig
  (`TickResult.emitted_alarms` → Driver →
  `AlarmStreamPort.publish`).

---

## 2. Entscheidung

ADR 0053 fixiert sechs Punkte fuer den Welle-3b-Comm-Failure-
Pfad.

### §2.1 Scope-Lesart: Adapter-Substanz + Test-Sibling-E2E (3b-D-1)

Der [`GG-SAFE-003`](../../../spec/lastenheft.md#gg-safe-003)-Flip bindet an die **Erkennungs-/Markierungs-/
Alarm-Substanz des Adapter-Rings**, belegt per Unit-Tests ueber
alle fuenf Adapter-Familien + reaktiviertem Integration-Smoke —
**nicht** an einen produktiven Demo-Lauf mit echtem
Protokoll-Verkehr.

- **Praezedenz:** die SAFE-001-`INVALID`-Emission derselben
  Adapter zaehlt seit Welle 5a als produktiv, ohne dass ein
  Demo-Pfad sie exerziert.
- Der fehlende produktive `read()`-Pfad ist eine
  **dokumentierte Bestand-Grenze** (kein Requirement verlangt
  ihn; kein Trigger). Etabliert ihn ein kuenftiger Slice, ist
  der Wrapper die fertige Comm-Failure-Schicht.
- Der M7-Erfolgskriteriums-Fallback („bewusste Carveout-Notiz")
  wird **nicht** gezogen.

### §2.2 Mechanik: ein geteilter Composition-Wrapper (3b-D-2)

NEU **`CommFailureGuardedDeviceProtocolPort`**
(`adapters/driven/_protocol_comm_failure_wrap.py`) —
Composition-Wrapper um einen konkreten `DeviceProtocolPort`,
Pattern exakt `_protocol_otel_wrap.py`.

- **NICHT** fuenf per-Adapter-Edits (fuenffache Mapping-Kopie;
  die Adapter bleiben kontext-frei und unangetastet).
- **NICHT** Core-/Spine-Stage (es gibt keinen produktiven
  `read()`-Pfad im Spine; die Fehler sind am Adapter-Rand
  typisiert greifbar).
- **Komposition mit dem OTel-Wrapper:** Comm-Failure **aussen**,
  OTel innen — der OTel-Span sieht den Original-Fehler als
  Error-Event, bevor der aeussere Wrapper ihn in Daten wandelt.
  C2 pinnt die Reihenfolge per Unit-Test.
- Der Wrapper ist **opt-in** (Verdrahter-Entscheidung):
  ungewrappte Adapter verhalten sich unveraendert fail-fast —
  kein stiller Fehler-Verschluck im Bestand.

### §2.3 Quality-Wahl: einheitlich `MISSING` (3b-D-3)

`read()`-Fehler (alle `DeviceProtocolPortReadError`-Subklassen)
→ synthetisierter Point mit **`Quality.MISSING`** — fuer alle
fuenf Adapter-Typen einheitlich.

- **NICHT `STALE`:** Verbindungsverlust heisst „Wert fehlt"
  (`MISSING`, Severity 7); `STALE` (Severity 3) ist die
  ADR-0052-Semantik fuer vorhanden-aber-veraltet und braeuchte
  einen Last-Value-Cache, den der Wrapper bewusst nicht fuehrt
  (kein versteckter Zustand, kein Drift-Risiko).
- **Abgrenzungen:** MQTT-`read() → None` (leere Queue) bleibt
  `None` (kein Ausfall, kein Point, kein Alarm); String-Read-
  `INVALID` (SAFE-001-Bestand) bleibt unberuehrt (kein
  Read-Error, kein Wrapper-Eingriff); `start()`/`stop()`/
  `write()` bleiben Pass-Through fail-fast (§7).

### §2.4 Alarm-Vertrag (3b-D-4)

Pro gefangenem Read-Fehler genau ein `Alarm`:

| Feld | Wert |
| --- | --- |
| `code` | `"adapter_communication_lost"` (NEU vierter stabiler Code neben `power_clamp_limited`/`command_rejected`/`smart_meter_rejected`) |
| `severity` | `"warning"` (einheitlich; `critical` bleibt der Command-Reject-Semantik vorbehalten, ADR 0040 §2.1) |
| `target` | `<read-target>` (Ziel) |
| `simulation_time_ms` | `clock.now()` (Startzeit; Sim-Zeit, [`AC-NO-TIME`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)) |
| `message` | `"<ExceptionKlassenname>: <str(exc)>"` (Ursache, maschinenlesbar praefixt) |
| `status` / `fault_id` | `"active"` / `None` |
| `alarm_id` | `alarm_id_source()` (uuid4-Default, Test-Stub — ADR 0040 Decision 16) |

**Emissions-Pfad:** injizierter `on_alarm: Callable[[Alarm],
None]`-Callback — der Verdrahter entscheidet das Ziel
(`AlarmStreamPort.publish` + History-Buffer im API-Kontext;
Listen-Collector im Test). Kein Driving-Port-Halt im
Driven-Ring; Late-Binding-Praezedenz `_demo_setup.py:176`.
**Best-Effort (geschaerft per C2-Review-Folge F1):** der
GESAMTE Alarm-Nebenkanal — Alarm-Konstruktion inkl. werfendem
`alarm_id_source` UND `on_alarm`-Callback — wird am
`read()`-Call-Site Best-Effort gefangen (geteiltes Catch-Tupel
`BEST_EFFORT_CALLBACK_EXCEPTIONS` aus
`_protocol_wrap_common.py`, Single-Source mit dem
OTel-Wrapper, Review-Folge F4) — der `MISSING`-Point hat
Vorrang vor dem Alarm-Nebenkanal. **Zeitstempel (Review-Folge
F2):** die Sim-Zeit wird genau einmal pro gefangenem Fehler
gelesen — `Alarm.simulation_time_ms` und
`Point.simulation_time` sind identisch.

### §2.5 Kontext-Injection (3b-D-5)

Der Wrapper wird keyword-only konstruiert mit `run_id: str` +
`clock: ClockPort` + `on_alarm` + `alarm_id_source:
Callable[[], str] | None = None`. Die gewrappten Adapter bleiben
kontext-frei (Platzhalter-Konvention unveraendert). `ClockPort`
ist die Sim-Zeit-Abstraktion (`AC-NO-TIME` gewahrt); der Wrapper
wird **pro Lauf** konstruiert (`run_id` Konstruktor-fix —
Praezedenz `TickLoop`).

### §2.6 Synthetisierter `MISSING`-Point (3b-D-6)

```python
TelemetryPoint(
    run_id=self._run_id,             # Wrapper-Kontext (§2.5)
    tick=0,                           # Platzhalter-Konvention (§1)
    simulation_time=now_ms,           # EIN clock.now() pro Fehler (F2)
    device_id=target,
    metric="",                        # unbekannt ohne Codec-Config
    value=Decimal("0"),               # Praezedenz SmartMeter-MISSING
    unit="",
    quality=Quality.MISSING,
    source=f"comm_failure.{target}",
    sequence=0,
)
```

`metric`/`unit` bleiben leer — die Codec-Konfiguration des
Targets ist bewusst Adapter-intern; ein „alle Metriken des
Targets"-Faecher braeuchte Codec-Introspektion (Scope-Sprung).
Der `source`-Praefix `comm_failure.` macht synthetisierte
Punkte maschinell unterscheidbar. C2 pinnt den Feld-Vertrag.

---

## 3. Begruendung

- **[`GG-SAFE-003`](../../../spec/lastenheft.md#gg-safe-003) schliessen.** Die typisierte Erkennungs-
  Substanz existiert seit M4/M5 — ADR 0053 liefert die fehlende
  Quality-/Alarm-Folge in genau einer Schicht; alle drei
  Alarm-Pflichtfelder der Akzeptanz (Ziel/Startzeit/Ursache)
  sind strukturiert belegt.
- **Composition statt Modifikation.** Fuenf gewachsene
  Read-Pfade bleiben unangetastet; das Mapping lebt
  Single-Source im Wrapper (Praezedenz ADR 0024 §4.5).
- **Kontext gehoert an die Naht, nicht in die Adapter.** Die
  Adapter bleiben sim-zeit-/lauf-frei (ADR-0030-Linie); der
  Wrapper traegt den injizierten Lauf-Kontext.
- **Schaerfung ohne Supersedes (ADR 0011).** ADR 0030
  (Port-Surface) + ADR 0040 (Alarm-Domain) bleiben textlich
  unveraendert; neuer Alarm-Code ist Daten-, kein Schema-Change.

---

## 4. Reichweite

- NEU `adapters/driven/_protocol_comm_failure_wrap.py`
  (`CommFailureGuardedDeviceProtocolPort`) (C2).
- NEU `tests/unit/adapters/driven/test_protocol_comm_failure_
  wrap.py` (5 Adapter-Familien-Fehlerfaelle + Alarm-Felder +
  None-Pass-Through + Nicht-Read-Fehler ungefangen +
  OTel-Komposition + on_alarm-Robustheit) (C2).
- Reaktivierung `test_safe_003_comm_failure_emits_missing_or_
  stale` + Flip `docs/user/safe-001-004-quality-pipeline.md`
  [`GG-SAFE-003`](../../../spec/lastenheft.md#gg-safe-003) ⚠ → ✓ (C2).
- ADR-Index NEU ADR-0053-Zeile (C1).
- NEU `adapters/driven/_protocol_wrap_common.py` —
  geteiltes Best-Effort-Catch-Tupel beider Wrapper
  (C2-Review-Folge F4); `_protocol_otel_wrap.py` bezieht sein
  Tupel seither von dort (einzige Bestand-Beruehrung, reines
  Konstanten-Hoisting). Geteilter `RecordingTracePort`-Test-
  Fake in `tests/unit/hexagon/ports/driven/_fakes.py`
  (Review-Folge F3, Dedup-Praezedenz 3a-F3).
- **Unberuehrt:** die fuenf Protocol-Adapter (nur gewrappt),
  `DeviceProtocolPort`-Vertrag, `Alarm`-Domain +
  `alarm_mappers.py`, `AlarmStreamPort`, TickLoop +
  ADR-0052-Stage, Demo-Wiring (keine `protocol_ports` —
  `make accept`-Pins unberuehrt).

---

## 5. Lieferung

Lieferplan, Commit-Hashes + Verifikations-Gates leben in der
Slice-Doc [`M7-welle-3b.md`](../planning/done-archive/M7-welle-3b.md).
Status-Pfad (`Proposed → Provisional → Accepted`): `Accepted`
gezogen 2026-06-12 mit M7-Welle-X-C1 (gebuendelt mit
ADR 0047..0052).

---

## 6. Konsequenzen

- **Positiv:** [`GG-SAFE-003`](../../../spec/lastenheft.md#gg-safe-003) flippt ⚠ → ✓; Trigger 035
  schliesst; **M7-Welle-3 komplett** — alle acht
  `GG-SAFE-*`-IDs sind damit produktiv oder bewusst verankert.
- **Positiv:** der Wrapper ist die fertige Comm-Failure-Schicht
  fuer einen kuenftigen produktiven `read()`-Pfad (eine
  Verdrahtungs-Zeile statt neuer Substanz).
- **Neutral:** synthetisierte `MISSING`-Points tragen leere
  `metric`/`unit` + Platzhalter-`tick` — Konsumenten, die per
  Metric filtern, sehen sie nicht (bewusst: der `source`-Praefix
  ist der Erkennungs-Kanal).
- **Neutral (Bestand):** ungewrappte Adapter bleiben fail-fast;
  der Wrapper ist opt-in und heute nur Test-seitig verdrahtet
  (§2.1-Lesart).
- **Bewusste Grenze:** kein Retry/Reconnect, kein
  Last-Value-`STALE`, keine per-Adapter-Severity — additive
  Schaerfungen bei konkretem Bedarf (§7).

---

## 7. Nicht Gegenstand dieser ADR

- **Produktiver `read()`-Pfad / Demo-Aktivierung der
  Protocol-Adapter** — kein Lastenheft-Lieferpunkt;
  dokumentierte Bestand-Grenze (§2.1).
- **`start()`-Fail-Mapping** — Fail-Fast-Bestand ist korrekt
  (ein Lauf ohne Verbindung startet nicht still mit `MISSING`;
  `start_protocol_ports` propagiert mit LIFO-Cleanup).
- **`write()`-Fehler-Alarme** — Command-Pfad ist
  `CommandResult`-/Device-Domaene (ADR 0040 §2.1).
- **Retry-/Reconnect-Logik** — eigener Ops-Scope.
- **`STALE`-Variante mit Last-Value-Cache** — additive
  Schaerfung bei konkretem Bedarf (§2.3).
- **Per-Adapter-Quality-/Severity-Differenzierung** — additive
  Schaerfung (§2.3/§2.4).
- **Severity-Override-Helper-Lift nach `quality.py`**
  (3a-Review-F4) — 3b synthetisiert Punkte statt Qualities zu
  upgraden; Lift erst bei dritter Nutzungsstelle (3b-D-7).
