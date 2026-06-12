# Welle 3b — M7 Safety-Closure: Adapter-Comm-Failure → `MISSING` + Alarm (`GG-SAFE-003`)

**Status:** Done (2026-06-12) — C0 `6324042` (Slice-Doc +
Decisions 3b-D-1..D-8) + C1 `caae16e` (NEU ADR 0053
`Provisional`) + C2 `3f28be1`
(`CommFailureGuardedDeviceProtocolPort` + 8 Unit-Tests +
Smoke-Reaktivierung `test_safe_003_*` + Doku-Flip `GG-SAFE-003`
⚠ → ✓) + C2-Review-Folge `82704b1` (F1 Alarm-Nebenkanal-Vorrang
komplett Best-Effort + F2 ein `clock.now()` pro Fehler — Point
und Alarm teilen den Zeitstempel + F3 Shared-`RecordingTracePort`-
Fake in `_fakes.py` + F4 geteiltes Catch-Tupel NEU
`_protocol_wrap_common.py`; 2 neue Unit-Test-Pins; ADR 0053
§2.4/§2.6/§4 geschaerft) + C3 (dieser Commit; DoD §9 abgehakt,
Trigger 035 → Closed). **Alle vier `GG-SAFE-001..004`
produktiv.** Alle Gates (`gates`/`test-integration` 139 passed /
4 skipped/`fullbuild` inkl. `accept-pin-check`/`docs-check`)
cache-frei gruen 2026-06-12. **Offen:** C4a/C4b (Self-Close-Move
+ Trigger 035 + Gruppenplan → `done/` — **M7-Welle-3 komplett**;
aktiver Slice danach → M7-Welle-X).

Zweites (letztes) Sub-Slice von **M7-Welle-3** (Safety-Closure;
Gruppenplan [`M7-welle-3.md`](M7-welle-3.md)): schliesst die
`GG-SAFE-003`-partial-Lücke
([Trigger 035](035-safe-003-comm-failure-missing-quality.md),
M6-Welle-5a-Audit ⚠). **Monolithisch** (ein Code-Commit C2): ein
geteilter Wrapper + Alarm-Vertrag + Tests + Doku-Flip sind eng
gekoppelt; die fuenf Adapter werden nicht einzeln angefasst
(3b-D-2). Mit 3b-Closure ist **M7-Welle-3 komplett** — danach
verbleibt nur M7-Welle-X (M7-Closure).
**Datum:** 2026-06-11 (Welle-3b-C0) · Done 2026-06-12
(Review-Folge + C3).
**Quelle:** [Trigger 035](035-safe-003-comm-failure-missing-quality.md)
+ Lastenheft §20 Z. 1365-1371 +
[`M7-welle-3.md`](M7-welle-3.md) (D-4-Scope-Schalter +
F4-Erbschaft).

Liefer-Reihenfolge C0 → C1 (NEU ADR 0053 `Provisional`) → C2
(Code) → C3 (Status/DoD-Sync + Flip) → C4a/C4b (Self-Close-Move;
**Gruppenplan wandert mit** nach `done/`, Welle 3 komplett).

---

## 1. Context

**Lastenheft-Akzeptanz (Z. 1365-1371, `GG-SAFE-003` MUSS):**

> Kommunikationsausfaelle MUESSEN erkannt werden.
>
> Akzeptanz: Kommunikationsausfaelle erzeugen einen
> dokumentierten Fehlerstatus, betroffene Telemetrie wird als
> `missing` oder `stale` markiert und ein Alarm mit Ziel,
> Startzeit und Ursache wird erzeugt.

### 1.1 Ist-Zustand (Code-verifiziert, Welle-3-C0-Audit + 3b-C0)

**Teil-produktiv (Welle-5a-Audit):** SmartMeter-pre-attach →
`Quality.MISSING` (`smart_meter/model.py:202`, ADR 0018 §2.3;
Sub-Smoke aktiv) + Adapter-String-Read → `Quality.INVALID`
(opcua/iec61850; SAFE-001-Substanz).

**Erkennungs-Substanz existiert, Folge-Substanz fehlt:**

- Alle fuenf Protocol-Adapter (`protocol_mqtt`/`_modbus`/
  `_opcua`/`_dnp3`/`_iec61850`) implementieren
  `DeviceProtocolPort` (`hexagon/ports/driven/device_protocol.py:43`)
  mit **typisierter Error-Hierarchie**: Read-Fehler (inkl.
  Verbindungsverlust mid-flight) werfen
  `DeviceProtocolPortReadError`-Subklassen — am praezisesten
  IEC 61850 mit dediziertem
  `Iec61850PortReadConnectionLostError`
  (`protocol_iec61850/_port.py:265`, Session-Drop post-start).
  **Kein** Adapter mappt diese Fehler auf `Quality.MISSING`
  oder einen Alarm.
- **Adapter sind bewusst kontext-frei:** die Read-Pfade bauen
  `TelemetryPoint`s mit Platzhaltern (`run_id=""`, `tick=0`,
  `simulation_time=0`, `sequence=0` — „Caller-Verantwortung",
  z. B. `protocol_modbus/_port.py:306-325`). Ein Alarm braucht
  aber `run_id` + `simulation_time_ms` (Startzeit) → der
  Comm-Failure-Pfad braucht **injizierten Lauf-Kontext** (3b-D-5).
- **MQTT-Sonderfall:** `read()` liefert `None` bei leerer Queue
  (kein Fehler, normaler Non-Blocking-Poll) — `None` ist KEIN
  Kommunikationsausfall (3b-D-3-Abgrenzung).
- **Composition-Wrapper-Praezedenz:**
  `OtelSpanWrappedDeviceProtocolPort`
  (`adapters/driven/_protocol_otel_wrap.py:145`) wrappt alle
  fuenf Adapter einheitlich (read/write gewrappt, start/stop
  pass-through, operation-spezifischer Catch, Best-Effort-
  Robustheit) — exaktes Vorbild fuer den Comm-Failure-Wrapper.
- **Alarm-Bestand (ADR 0040):** `Alarm` (frozen, 9 Felder:
  `alarm_id`/`run_id`/`simulation_time_ms`/`target`/`code`/
  `severity`/`message`/`status`/`fault_id`); Severity-Literale
  `info`/`warning`/`critical`; Emission heute ausschliesslich
  Device-seitig (`TickResult.emitted_alarms` → Driver →
  `AlarmStreamPort.publish`); Alarm-Codes heute
  `power_clamp_limited`/`command_rejected`/`smart_meter_rejected`
  (`alarm_mappers.py`). `alarm_id_source`-Injection-Praezedenz:
  ADR 0040 Decision 16 (uuid4-Default, Test-Stub).
  Late-Binding-Provider-Praezedenz: `_demo_setup.py:176`.
- **Kein produktiver `read()`-Pfad:** der `TickLoop` haelt
  `protocol_ports` nur fuer Start/Stop-Lifecycle
  (`tick_loop.py:900/954`); `read()` rufen ausschliesslich
  Test-Siblings. Demo-Wiring uebergibt keine `protocol_ports`.
  → praegt die Scope-Lesart (3b-D-1).
- **Skipped Smoke:** `test_safe_003_comm_failure_emits_missing_
  or_stale` (`tests/integration/test_m6_welle_5a_safe_001_004_
  smoke.py`, `pytest.skip` mit Trigger-035-Pointer) — wird in
  3b-C2 reaktiviert.

---

## 2. Lieferziel (Welle-3b-C2)

1. **NEU Comm-Failure-Wrapper**
   `CommFailureGuardedDeviceProtocolPort`
   (`adapters/driven/_protocol_comm_failure_wrap.py`; Pattern-
   Sibling zu `_protocol_otel_wrap.py`): Composition-Wrapper um
   einen konkreten `DeviceProtocolPort` (alle fuenf
   Adapter-Typen), keyword-only konstruiert mit `run_id: str`,
   `clock: ClockPort`, `on_alarm: Callable[[Alarm], None]`,
   `alarm_id_source: Callable[[], str] | None = None`
   (uuid4-Default; 3b-D-2/D-5).
2. **`read()`-Fehler → `MISSING`-Point + Alarm:** faengt
   `DeviceProtocolPortReadError`-Subklassen; pro gefangenem
   Fehler:
   - liefert einen synthetisierten `TelemetryPoint` mit
     `quality=Quality.MISSING` (Feld-Vertrag siehe 3b-D-6),
   - ruft `on_alarm(Alarm(code="adapter_communication_lost",
     severity="warning", target=<target>,
     simulation_time_ms=clock.now(), message=<Ursache:
     Exception-Klassenname + str(exc)>, status="active",
     fault_id=None))` (3b-D-4).
   `read()`-Rueckgabe `None` (MQTT-leer) bleibt `None` — kein
   Ausfall. `start()`/`stop()`/`write()` bleiben Pass-Through
   (3b-D-3).
3. **NEU Unit-Tests**
   (`tests/unit/adapters/driven/test_protocol_comm_failure_wrap.py`,
   Sibling zu `test_protocol_otel_wrap.py`): pro Adapter-Familie
   ein Mock-Read-Fehler-Fall (fuenf typisierte
   `ReadError`-Subklassen inkl.
   `Iec61850PortReadConnectionLostError`) → `MISSING`-Point +
   Alarm-Felder gepinnt (Ziel/Startzeit/Ursache); `None`-
   Pass-Through (MQTT-leer ≠ Ausfall); Nicht-Read-Fehler
   (`write`/`start`) NICHT gefangen; Alarm-ID via Test-Stub
   deterministisch.
4. **Smoke-Reaktivierung:** `test_safe_003_comm_failure_emits_
   missing_or_stale` (Skip-Marker raus): End-to-End ueber
   Wrapper + Mock-Adapter, der nach erfolgreichem Read einen
   Verbindungsverlust wirft → `Quality.MISSING` + Alarm mit
   `code="adapter_communication_lost"` + Ziel + Startzeit +
   Ursache. Der SmartMeter-pre-attach-Sub-Smoke bleibt
   unveraendert.
5. **Doku-Flip** `docs/user/safe-001-004-quality-pipeline.md`:
   `GG-SAFE-003`-Zeile ⚠ partial → ✓ produktiv (Substanz- +
   Test-Pfad + Detail-Sektion; Scope-Lesart aus 3b-D-1
   transparent dokumentiert).
6. **NEU ADR 0053 `Provisional`** (C1): Wrapper-Standort +
   Fehler-→-Quality-Mapping + Alarm-Vertrag + Kontext-Injection
   + Scope-Lesart.
7. **C3:** Trigger 035 → Closed; `GG-SAFE-003`-Flip;
   Gruppenplan-/roadmap-/carveouts-Sync. **C4a/C4b:**
   `M7-welle-3b.md` + Trigger 035 + **Gruppenplan
   `M7-welle-3.md`** → `done/` (Welle 3 komplett).

**Anti-Scope (3b NICHT):** produktive Protocol-Adapter-Demo-
Aktivierung / produktiver `read()`-Pfad im TickLoop (kein
Lastenheft-Lieferpunkt; siehe D-1); `start()`-Fail-Mapping
(Fail-Fast-Bestand ist korrekt: ein Lauf ohne Verbindung
startet nicht still mit MISSING, `start_protocol_ports`
propagiert mit LIFO-Cleanup); `write()`-Fehler-Alarme
(Command-Pfad ist `CommandResult`-/Device-Domaene);
Retry-/Reconnect-Logik (eigener Ops-Scope); `STALE` fuer
Comm-Failure (D-3); per-Adapter-Quality-Differenzierung (D-3).

---

## 3. Architektur-Entscheidungen (Welle-3b)

### 3b-D-1 — Scope-Lesart (finalisiert Welle-3-D-4)

**Final: voller Akzeptanz-Umfang via Adapter-Substanz +
Test-Sibling-E2E — KEIN Carveout.** Die Akzeptanz bindet an die
Erkennungs-/Markierungs-/Alarm-**Substanz** des Adapter-Rings,
nicht an einen produktiven Demo-Lauf mit echtem
Protokoll-Verkehr. **Praezedenz:** die SAFE-001-`INVALID`-
Emission derselben Adapter zaehlt seit Welle 5a als produktiv,
ohne dass ein Demo-Pfad sie exerziert. Der fehlende produktive
`read()`-Pfad ist eine **dokumentierte Bestand-Grenze** (kein
Trigger noetig — kein Requirement verlangt ihn; sobald ein
kuenftiger Slice ihn etabliert, ist der Wrapper die fertige
Comm-Failure-Schicht). Der M7-Erfolgskriteriums-Fallback
(„Carveout-Notiz") wird damit **nicht** gezogen.

### 3b-D-2 — Mechanik: ein geteilter Composition-Wrapper

**Final: NEU `CommFailureGuardedDeviceProtocolPort`** als
Composition-Wrapper (Pattern exakt
`OtelSpanWrappedDeviceProtocolPort`, `_protocol_otel_wrap.py`).

- **NICHT Option B (fuenf per-Adapter-Edits):** dupliziert das
  Mapping fuenffach, beruehrt fuenf gewachsene Read-Pfade, und
  die Adapter sollen kontext-frei bleiben (§1.1) — der Kontext
  (run_id/clock/on_alarm) gehoert in genau eine Schicht.
- **NICHT Core-/TickLoop-Stage:** es gibt keinen produktiven
  `read()`-Pfad im Spine (D-1); die Fehler entstehen am
  Adapter-Rand und sind dort typisiert greifbar.
- Komponierbar mit dem OTel-Wrapper (beide wrappen
  `DeviceProtocolPort`; Reihenfolge: Comm-Failure aussen, damit
  der OTel-Span den Original-Fehler sieht — C2 pinnt die
  dokumentierte Komposition).

### 3b-D-3 — Quality-Wahl: einheitlich `MISSING`

**Final: `Quality.MISSING` fuer alle fuenf Adapter-Typen.**
Verbindungsverlust heisst „Wert fehlt" (`MISSING`, Severity 7)
— `STALE` (Severity 3) ist die 3a-Semantik fuer
vorhanden-aber-veraltet und braeuchte einen letzten bekannten
Wert, den der Wrapper bewusst nicht cached (kein
Last-Value-Store, kein Drift-Risiko). Der Trigger erlaubt die
Wahl pro Adapter-Typ; eine Differenzierung haette heute keinen
fachlichen Traeger — einheitlich `MISSING` ist die einfachste
ehrliche Form (additive Schaerfung jederzeit moeglich).
**Abgrenzungen:** MQTT-`read() → None` (leere Queue) ist kein
Ausfall und bleibt `None`; String-Read-`INVALID`
(SAFE-001-Bestand) bleibt unberuehrt (kein Read-Error, kein
Wrapper-Eingriff).

### 3b-D-4 — Alarm-Vertrag

**Final:** pro gefangenem Read-Fehler ein `Alarm` mit:

- `code="adapter_communication_lost"` (NEU vierter
  Alarm-Code; stabile ID analog `alarm_mappers.py`-Konvention),
- `severity="warning"` (einheitlich; `critical` bleibt der
  Command-Reject-Semantik vorbehalten, ADR 0040 §2.1 —
  per-Adapter-Eskalation waere additive Schaerfung),
- `target=<read-target>` (Ziel), `simulation_time_ms=
  clock.now()` (Startzeit, Sim-Zeit — AC-NO-TIME),
- `message=<ExceptionKlassenname>: <str(exc)>` (Ursache,
  maschinenlesbar praefixt),
- `status="active"`, `fault_id=None`,
  `alarm_id=alarm_id_source()` (uuid4-Default, Test-Stub —
  ADR 0040 Decision 16).

**Emissions-Pfad:** injizierter `on_alarm: Callable[[Alarm],
None]`-Callback statt direktem `AlarmStreamPort`-Halt im
Driven-Ring — der Verdrahter entscheidet das Ziel
(`AlarmStreamPort.publish` + History-Buffer im API-Kontext;
Listen-Collector im Test). Kein Schichten-Konflikt
(Driven-Adapter haelt keinen Driving-Port), Late-Binding-
Praezedenz `_demo_setup.py:176`. **Kein fail-fast:** wirft
`on_alarm` selbst, wird das Best-Effort gefangen (Pattern
`_BEST_EFFORT_OBSERVABILITY_EXCEPTIONS` aus
`_protocol_otel_wrap.py:135`) — der `MISSING`-Point hat
Vorrang vor dem Alarm-Nebenkanal.

### 3b-D-5 — Kontext-Injection

**Final:** der Wrapper nimmt keyword-only `run_id: str` +
`clock: ClockPort` + `on_alarm` + `alarm_id_source`. Die
gewrappten Adapter bleiben kontext-frei (Platzhalter-Konvention
§1.1 unveraendert). `ClockPort` ist die Sim-Zeit-Abstraktion
(AC-NO-TIME gewahrt); der Wrapper wird pro Lauf konstruiert
(run_id ist Konstruktor-fix — Praezedenz: `TickLoop` selbst).

### 3b-D-6 — Synthetisierter `MISSING`-Point (Feld-Vertrag)

**Final:** der Wrapper liefert bei gefangenem Read-Fehler:

```python
TelemetryPoint(
    run_id=self._run_id,            # Wrapper-Kontext (D-5)
    tick=0,                          # Platzhalter-Konvention §1.1
    simulation_time=self._clock.now(),
    device_id=target,
    metric="",                       # unbekannt ohne Codec-Config
    value=Decimal("0"),              # Praezedenz SmartMeter-MISSING (_ZERO)
    unit="",
    quality=Quality.MISSING,
    source=f"comm_failure.{target}",
    sequence=0,
)
```

`metric`/`unit` bleiben leer — der Wrapper kennt die
Codec-Konfiguration des Targets bewusst nicht (sie ist
Adapter-intern); ein „alle Metriken des Targets"-Faecher
braeuchte Codec-Introspektion und waere Scope-Sprung. Der
`source`-Praefix `comm_failure.` macht synthetisierte Punkte
maschinell unterscheidbar. C2 pinnt den Feld-Vertrag im
Unit-Test.

### 3b-D-7 — F4-Erbschaft (3a-Review): Severity-Override-Helper

**Final: F4 bleibt zurueckgestellt — kein Lift nach
`quality.py`.** 3b **synthetisiert** neue Punkte mit fixer
Quality (`MISSING`), upgraded keine bestehende Quality — die
3a-Severity-Override-Regel wird nicht gebraucht; sie bleibt
Single-Use in `_apply_max_age_stage` (ADR 0052 §2.3). Ein Lift
wird erst faellig, wenn eine **dritte** Stelle die Regel
braucht.

### 3b-D-8 — ADR-Bedarf

**Final: NEU ADR 0053 `Provisional`** (C1; Nummer per
Welle-3-D-3 reserviert): Wrapper-Standort + Read-Error-→-
`MISSING`-Mapping + `adapter_communication_lost`-Alarm-Vertrag
+ Kontext-Injection + D-1-Scope-Lesart. Schaerft ADR 0030
(DeviceProtocolPort) + ADR 0040 (Alarm) additiv (ADR-0011-Form,
kein Supersedes).

---

## 4. Liefer-Reihenfolge

- **C0** (dieser Commit) — Slice-Doc + Decision-Liste
  3b-D-1..D-8 + Refs-Sync.
- **C1** — NEU ADR 0053 `Provisional`.
- **C2** — Code: Wrapper + Unit-Tests (5 Adapter-Familien) +
  Smoke-Reaktivierung + Doku-Flip.
- **C3** — Status/DoD-Sync + `GG-SAFE-003`-Flip + Trigger 035 →
  Closed.
- **C4a/C4b** — Self-Close-Move `M7-welle-3b.md` + Trigger 035 +
  **Gruppenplan `M7-welle-3.md`** → `done/` + Refs-Sync
  (Welle 3 komplett; aktiver Slice danach → M7-Welle-X).

---

## 5. Critical Files

**NEU (C0/C1/C2):** `M7-welle-3b.md` (C0);
`docs/plan/adr/0053-…md` (C1);
`src/grid_gym/adapters/driven/_protocol_comm_failure_wrap.py`
(C2);
`tests/unit/adapters/driven/test_protocol_comm_failure_wrap.py`
(C2).
**MODIFY (C2):**
`tests/integration/test_m6_welle_5a_safe_001_004_smoke.py`
(Skip-Reaktivierung `test_safe_003_comm_failure_*`);
`docs/user/safe-001-004-quality-pipeline.md` (Flip ⚠ → ✓);
`docs/plan/adr/README.md` (C1).
**MODIFY (C3):** `M7-welle-3.md` (3b → Done, Wellen-Closure) +
`M7-mvp-completion.md` + `roadmap.md` + `carveouts.md` +
`open/README.md` + `open/035-…` (→ `done/` in C4a).
**UNBERUEHRT:** die fuenf Protocol-Adapter selbst (nur
gewrappt), `_protocol_otel_wrap.py`, `DeviceProtocolPort`-
Vertrag, `Alarm`-Domain + `alarm_mappers.py` (neuer Code-Wert
ist Daten-, kein Schema-Change), `AlarmStreamPort`,
TickLoop/3a-Stage.

---

## 6. Verifikationspfad

- `make gates` cache-frei gruen (inkl. `arch-check`: Wrapper ist
  Driven-Ring-Code, Praezedenz `_protocol_otel_wrap.py`).
- `make test-integration` gruen inkl. reaktiviertem
  `test_safe_003_comm_failure_emits_missing_or_stale`.
- `make fullbuild` (inkl. `accept-pin-check` — Demo-Pfad
  unveraendert, keine `protocol_ports` im Demo) +
  `make docs-check` cache-frei gruen.

---

## 7. Risiken

- **R1 Flip-Lesart `GG-SAFE-003`.** Ein Reviewer koennte
  „Kommunikationsausfaelle MUESSEN erkannt werden" als
  produktiv-verdrahteten Pfad lesen. Mitigation: D-1-Lesart +
  SAFE-001-Praezedenz explizit in ADR 0053 + Doku-Flip; der
  Wrapper ist die fertige Schicht fuer einen kuenftigen
  produktiven `read()`-Pfad.
- **R2 Wrapper-Komposition mit OTel.** Falsche Schachtel-
  Reihenfolge wuerde den OTel-Error-Event verschlucken
  (Comm-Failure innen faengt vor dem Span). Mitigation: D-2
  pinnt Comm-Failure **aussen**; Unit-Test mit beiden Wrappern
  komponiert.
- **R3 Alarm-Nebenkanal-Robustheit.** Ein werfender `on_alarm`
  darf den `MISSING`-Point nicht verhindern. Mitigation:
  Best-Effort-Catch (D-4) + Test pinnt „Alarm-Fehler →
  Point kommt trotzdem".
- **R4 Stiller Fehler-Verschluck.** Der Wrapper wandelt
  typisierte Fehler in Daten — ein Aufrufer, der den Fehler
  brauchte, sieht ihn nicht mehr. Mitigation: Wrapper ist
  **opt-in** (Verdrahter-Entscheidung; ungewrappte Adapter
  verhalten sich unveraendert); Anti-Scope haelt `start`/
  `stop`/`write` als Pass-Through fail-fast.

---

## 8. Wandert nach

Self-Close-Move `M7-welle-3b.md → done/` (C4a) + Refs-Sync
(C4b) nach 3b-C3. **Mit 3b-Closure ist M7-Welle-3 komplett** —
der Gruppenplan [`M7-welle-3.md`](M7-welle-3.md) und Trigger 035
wandern in derselben C4-Sequenz nach `done/`; aktiver Slice
danach → **M7-Welle-X** (M7-Closure).

---

## 9. DoD-Checkliste (mit C3 abzuhaken)

- [x] C0 — Slice-Doc §1..§9 + Decision-Liste 3b-D-1..D-8 +
      Refs-Sync (`6324042`).
- [x] C1 — NEU ADR 0053 `Provisional` (Wrapper + Mapping +
      Alarm-Vertrag + Kontext-Injection + Scope-Lesart;
      `caae16e`).
- [x] C2 — `CommFailureGuardedDeviceProtocolPort` (read-Catch →
      `MISSING`-Point per D-6 + `adapter_communication_lost`-
      Alarm per D-4; start/stop/write Pass-Through; None ≠
      Ausfall; `3f28be1` + Review-Folge `82704b1`: F1
      Nebenkanal-Vorrang + F2 Ein-Zeitstempel + F3/F4 Dedup).
- [x] C2 — Unit-Tests: 5 Adapter-Familien-Fehlerfaelle +
      Alarm-Felder (Ziel/Startzeit/Ursache) + None-Pass-Through
      + Nicht-Read-Fehler ungefangen + OTel-Komposition (R2) +
      on_alarm-Robustheit (R3; per Review-Folge geschaerft um
      alarm_id_source-Robustheit + Ein-Zeitstempel-Pin — 10
      Tests).
- [x] C2 — Smoke `test_safe_003_comm_failure_emits_missing_or_
      stale` reaktiviert + gruen.
- [x] C2 — Doku-Flip `safe-001-004-quality-pipeline.md`
      `GG-SAFE-003` ⚠ → ✓ (inkl. D-1-Scope-Lesart).
- [x] `make gates` + `make test-integration` + `make fullbuild`
      (inkl. `accept-pin-check`) + `make docs-check` cache-frei
      gruen (zuletzt 2026-06-12 nach Review-Folge).
- [x] C3 — 3b `Done`; **`GG-SAFE-003` ✓ produktiv**; Trigger 035
      → Closed (Move `done/` in C4a); Wellen-Closure-Sync;
      aktiver Slice → M7-Welle-X (dieser Commit).

**Anti-Scope (3b NICHT):** produktiver `read()`-Pfad /
Demo-Aktivierung, `start()`-/`write()`-Fehler-Mapping,
Retry-/Reconnect, `STALE`-Variante, per-Adapter-Severity,
F4-Helper-Lift (D-7).

---

## References

- [`M7-welle-3.md`](M7-welle-3.md) — Welle-3-Gruppenplan
  (D-4-Scope-Schalter → 3b-D-1; F4-Erbschaft → 3b-D-7).
- [Trigger 035](035-safe-003-comm-failure-missing-quality.md)
  — Lücken-Verankerung + erwartete Lieferung (M6-Welle-5a-Audit).
- [`../../../user/safe-001-004-quality-pipeline.md`](../../../user/safe-001-004-quality-pipeline.md)
  — Audit-Tabelle (Flip-Ziel ⚠ → ✓).
- [`M7-welle-3a.md`](M7-welle-3a.md) —
  Schwester-Slice (`GG-SAFE-004`, ADR 0052; Slice-Doc-Pattern).
- [`../../adr/0030-device-protocol-port-surface.md`](../../adr/0030-device-protocol-port-surface.md)
  — `DeviceProtocolPort`-Vertrag (wird additiv geschaerft).
- [`../../adr/0040-alarm-aggregation-and-stream-port.md`](../../adr/0040-alarm-aggregation-and-stream-port.md)
  — Alarm-Domain + Severity-Konvention + `alarm_id_source`-
  Injection (Decision 16).
- [`../../adr/0024-observability-port-trio.md`](../../adr/0024-observability-port-trio.md)
  §4.5 — OTel-Wrapper-Praezedenz (`_protocol_otel_wrap.py`).
- [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md)
  §20 `GG-SAFE-003` (Z. 1365-1371).
