# ADR 0034 — DNP3-Adapter-Profile (M4 Welle 5a)

**Status:** Accepted — gezogen 2026-06-01 mit M4-Welle-7-C1
(dieser Commit; M4-Closure-Welle). Provisional-Schritt
2026-05-31 mit M4-Welle-5a-C3 (`docs(plan|adr)` Doc-Sync).
Initial-Entwurf (`Proposed`) 2026-05-31 mit M4-Welle-5a-C1
`b0fea7e`; C2-Merge `224b370` (feat `protocol_dnp3/`-5-Modul-
Paket + 56 neue Unit-Tests + 4 in-process `dnp3-outstation`-
Integration-Smoke-Tests + `pyproject.toml`/`uv.lock`/
`Dockerfile`/`compose.yml`-Edits; `make test-unit` 1462 gruen,
`make test-integration` 35 gruen, `make arch-check` 19/19
KEPT, `make gates` cache-frei gruen ohne
`CRITICAL_COV_TARGETS`-Override) belegt die Decisions
D-a/D-b/D-c/D-d/D-e produktiv. Cross-Adapter-OTel-Span-Wrap
aus Welle 6a wrappt auch den DNP3-Adapter ohne Adapter-
Code-Diff.

**Library-Bug-Find waehrend C2:** `nfm-dnp3.AnalogInput`-
`__repr__` zeigt `AnalogInput(idx=0, ...)` als Kurzform, aber
das tatsaechliche Field heisst `index`. C1-Probe-Output hat
das verschleiert (`print(ai)` zeigte das `repr()`). C2-Code
hatte initial `getattr(point, "idx", None)`, was zu
`Dnp3PortPointNotInPollResultError` bei jedem Read fuehrte.
Fix: `getattr(point, "index", None)` (Adapter) +
`_MockPoint.index` (Tests). Welle-5a-Closure-Sync zementiert
das Feld-Name-Mapping in `_port._find_point` als
Kommentar — Welle-6-Verallgemeinerung kann ein typed
Protocol fuer Point-Wire-Repr einfuehren, falls
weitere Libraries andere Field-Namen nutzen.

Status-Pfad: `Proposed → Provisional` (2026-05-31
M4-Welle-5a-C3) → **Accepted** (2026-06-01 M4-Welle-7-C1,
dieser Commit, analog ADR 0022..0027 + 0030 + 0031 +
0032 + 0033).
**Datum:** 2026-05-31 (Erstfassung) / 2026-06-01 (Accepted, M4-Welle-7-C1)
**Bezug:**
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md)
(Schaerfungs-ohne-Supersede-Pattern — ADR 0034 schaerft
ADR 0030 §2.1 und §2.4 konkret fuer DNP3, ohne den Sync-
`DeviceProtocolPort`-Vertrag oder den Welle-1-Verzicht-
Default zu ersetzen; M4-Welle-7-Closure schaerft
ADR 0030 §2.4 dann auf „durch Welle-5a-Spike-Lieferung
aufgeloest"),
[`ADR 0030`](0030-device-protocol-port-surface.md) §2.1
(Sync-`Protocol`-Vertrag; `nfm-dnp3.DNP3Master` ist
sync-by-design — alle public Methoden sync per
C1-API-Probe — und passt damit **direkt** in die Sync-
`DeviceProtocolPort`-Surface, analog Welle-3-Modbus
**ohne** Adapter-internen Thread+Loop-Marshal) + §2.2
(Caller-Scope-Lifecycle) + §2.3 (stateless aus Replay-
Sicht — DNP3-Reconnect-State + IIN-Restart-Flag sind
volatile) + §2.4 (Welle-1-DNP3-Verzicht-Default;
Welle 5a loest ihn per Spike-Lieferung auf — Pattern
ADR 0011),
[`ADR 0031`](0031-mqtt-adapter-profile.md) §2.1
(Decision 4a inline-Profile-Pattern — ADR 0034 uebernimmt
das Pattern direkt fuer Point-Schema),
[`ADR 0032`](0032-modbus-adapter-profile.md) §2.1
(Decision M-a inline-Register-Schema — direkte Pattern-
Praezedenz fuer Decision D-a inline-Point-Schema) +
§2.3 (Decision M-c direkt-sync — direkte Pattern-
Praezedenz fuer Decision D-b: nfm-dnp3 ist sync wie
pymodbus) + §2.6 (Decision M-f in-process-Server —
direkte Pattern-Praezedenz fuer Decision D-e),
[`ADR 0033`](0033-opcua-adapter-profile.md) §2.5
(Decision O-e in-process-Server — Pattern fortgesetzt
fuer Decision D-e mit `dnp3-outstation` als
Test-Sibling).
M4-Slice-Plan
[`done/M4-protocol-adapters.md`](../planning/done-archive/M4-protocol-adapters.md)
§3 Welle 5a; M4-Welle-0-Decision-Liste
[`done/M4-welle-0.md`](../planning/done-archive/M4-welle-0.md) §3
Decision 1 (DNP3/IEC-Disposition — Welle 1 hat den
Verzicht-Default provisorisch gewaehlt; Welle 5a/5b
loesen ihn per Spike-Lieferung auf).
Lastenheft §16 (`GG-DNP3-001` SOLLTE-Cluster: Points,
Variations, Qualitaetsflags, Fehlerverhalten +
deterministischer Adapter-Smoke).
Architektur §7 (`GG-AR-PORT-DRN-007` Driven-Ports-Tabelle
— ADR 0030 hat den Slot belegt; Welle 5a liefert vierten
Implementer) + §8.2 (Adapter-Interfaces-Driven-
Beschreibung — Point-Schema konkretisiert die generische
Beschreibung fuer DNP3).

---

## 1. Kontext

`GG-DNP3-001` (Lastenheft §16) verlangt einen DNP3-
Adapter als **Simulations-/Testadapter** mit
deterministischem Adapter-Smoke-Test. M4-Welle-2 hat
MQTT (ADR 0031 `Provisional`), Welle 3 Modbus
(ADR 0032 `Provisional`), Welle 4 OPC-UA (ADR 0033
`Provisional`) produktiv geliefert; Welle 5a liefert
den vierten Implementer: `Dnp3DeviceProtocolPort` unter
`src/grid_gym/adapters/driven/protocol_dnp3/` ueber
**zwei** Pure-Python-Libraries:

- **Master/Client (produktiv-Dependency):** `nfm-dnp3`
  1.0.1 (PyPI, MIT, Pure-Python, Beta `Development
  Status :: 4`). `DNP3Master`-Klasse mit voller
  Protocol-Stack-Implementierung (Data Link / Transport
  / Application Layer), TCP/IP-Kommunikation, Class-
  0/1/2/3-Polling, CRC-16. **Sync API mit Thread-Lock-
  Schutz** (C1-Probe-Run 2026-05-31 verifiziert: alle
  public Methoden sync, keine `[async]`-Marker; vgl.
  `inspect.iscoroutinefunction`-Check). Python 3.9+.
  Import-Name: `dnp3py`. Repo `fxodell/dnp3py`.
- **Outstation/Server (nur Test-Sibling, Dev-Dependency):**
  `dnp3-outstation` 0.2.0 (PyPI, MIT, Pure-Python,
  asyncio-native, IEEE-1815-2012-Level-1-Subset, aarch64-
  compatible). `joenarvaez/dnp3-outstation`. Group 30 /
  Variation 5 (32-bit float analog inputs) als Minimum-
  Profile. **Wichtige Library-Einschraenkung:** Nur
  READ-qualifier 0x06 (class-0/integrity poll) und 0x00
  (8-bit range) sind supported — qualifier 0x01 (16-bit
  range) wird mit „dropped frame: unsupported request
  qualifier 0x1" verworfen.

ADR 0030 hat den **Sync-Vertrag** und **Caller-Scope-
Lifecycle** finalisiert; ADR 0030 §2.4 hat den
**DNP3-Verzicht-Default provisorisch** gewaehlt (Welle 1
2026-05-26). ADR 0034 schaerft die fuer den DNP3-Adapter
notwendigen Sub-Entscheidungen **konkret** und loest
damit den ADR-0030-§2.4-Verzicht per Spike-Lieferung auf
(Pattern ADR 0011; M4-Welle-7-Closure schaerft
ADR 0030 §2.4 entsprechend).

ADR 0031 hat das **inline-im-`protocol_ports`-Block**-
Profile-Pattern etabliert; ADR 0032 hat es Modbus-
spezifisch geschaerft (Register-Schema); ADR 0033 fuer
OPC-UA (Node-ID-Schema). ADR 0034 schaerft Decision-D-a..
D-e:

- **Decision D-a (Point-Schema)** — wo und wie werden
  Device-ID → Point-Mappings deklariert?
- **Decision D-b (Async-Bridge)** — wie wird der nfm-dnp3-
  Sync-Charakter gegen die sync-`DeviceProtocolPort`-
  Surface vermittelt?
- **Decision D-c (Datatype + Group/Variation-Set)** —
  welche DNP3-Object-Groups/Variations sind in Welle 5a
  unterstuetzt?
- **Decision D-d (Read-Pfad)** — wie wird die nfm-dnp3-
  API auf den `DeviceProtocolPort.read()`-Call abgebildet?
- **Decision D-e (Test-Sibling)** — wie wird der DNP3-
  Outstation-Sibling im Integration-Test bereitgestellt?

**Spannungsfeld:**

- **Zwei-Library-Setup:** anders als Welle 3 (pymodbus
  liefert Client+Server) und Welle 4 (asyncua liefert
  Client+Server) braucht Welle 5a zwei unabhaengige
  Libraries. Wire-Compat zwischen `nfm-dnp3.DNP3Master`
  und `dnp3-outstation.AsyncOutstation` ist **nicht**
  vorab garantiert — C1-Probe-Run 2026-05-31 hat sie
  fuer Class-0-Read explizit verifiziert.
- **DNP3-Polling-Idiom vs. Per-Index-Read:** DNP3 ist
  primaer Class-0-Polling-orientiert (Master fragt
  „gib mir alle Class-0-Daten", Outstation liefert alle
  konfigurierten Points). Per-Index-Range-Read existiert
  spec-seitig (FC=READ, qualifier 0x00/0x01), aber
  `dnp3-outstation` v0.2.0 supportet nur 0x00/0x06.
  Welle 5a folgt deshalb dem **idiomatischen Class-0-
  Polling-Pattern** mit Resultat-Filter-by-Index — das
  ist auch der spec-konforme Welle-Standard.
- **DNP3-IIN-Restart-Flag:** nach Outstation-Boot
  meldet die Outstation IIN1.DEVICE_RESTART=True; nfm-
  dnp3 erhaelt das im `PollResult.iin`, und
  `dnp3-outstation` self-clears das Flag nach der
  ersten Response (C1-Probe verifiziert). Welle-5a-
  Adapter hat keinen Init-Step-Bedarf, weil dnp3-
  outstation das Flag selbst clearet.

---

## 2. Entscheidung

ADR 0034 legt fuenf Profile-Decisions fest.

### 2.1 Decision D-a — Point-Schema inline im `protocol_ports`-Block (final)

Point-Profile werden **inline** im `protocol_ports`-
Scenario-YAML-Block deklariert. Pattern uebernommen
direkt von ADR 0031 §2.1 (MQTT Topic-Schema inline),
ADR 0032 §2.1 (Modbus Register-Schema inline), ADR 0033
§2.1 (OPC-UA Node-ID-Schema inline).

**Skizze (finale Signatur in Welle-5a-C2-feat):**

```yaml
protocol_ports:
  - type: dnp3
    host: "192.168.1.50"
    port: 20000
    master_address: 1
    outstation_address: 10
    response_timeout_s: 5.0
    points:
      battery1_voltage:
        group: 30
        variation: 5  # 32-bit float analog input
        index: 0
        access: "read"
      battery1_current:
        group: 30
        variation: 5
        index: 1
        access: "read"
      battery1_status:
        group: 1
        variation: 2  # binary input with flags
        index: 0
        access: "read"
      battery1_power:
        group: 30
        variation: 1  # 32-bit integer analog input
        index: 2
        access: "read"
```

**Begruendung:**

- Pattern-Konsistenz mit ADR 0031/0032/0033: ein
  einheitliches Konstrukt `protocol_ports: list[<typ-
  spezifische-Config>]` ueber alle Adapter macht
  Scenarios lesbar und reduziert Loader-Komplexitaet.
- Point-Schemas sind **per Target eindeutig** (jede
  Device-ID hat eine eigene Group/Variation/Index-
  Tripel-Adresse), genauso wie MQTT-Topics / Modbus-
  Register / OPC-UA-Node-IDs — Inline-Wachstum bleibt
  handhabbar.
- Separate Profile-Section haette dieselben Nachteile
  wie in ADR 0031 §3 A1 / ADR 0032 §3 A1 / ADR 0033 §3 A1
  verworfen.

**Konsequenz:** `Dnp3ProtocolPortConfig`-frozen-dataclass
unter
`src/grid_gym/adapters/driven/protocol_dnp3/_config.py`
mit Pflicht-Feldern `host: str`, `port: int = 20000`,
`master_address: int = 1`, `outstation_address: int = 10`,
`response_timeout_s: float = 5.0`, `points: Mapping[str,
Dnp3PointConfig]`. `Dnp3PointConfig` mit Pflicht-Feldern
`group: int`, `variation: int`, `index: int`, `access:
Literal["read", "write"]`. Welle-5a-Minimum: `access`
ist **nur** `"read"` — `"write"` wird Welle-6-Schaerfung.
Konstruktor-Validation mit `Dnp3ConfigError`-Familie
(analog `ModbusConfigError`-Familie aus Welle 3).

### 2.2 Decision D-b — Direkt-Sync (kein Adapter-interner Loop-Thread, final)

`Dnp3DeviceProtocolPort` benutzt **keinen** Adapter-
internen asyncio-Loop-Thread (anders als Welle 4 OPC-UA
mit `OpcuaLoopThread`). `start()` ruft
`DNP3Master.open()` direkt synchron; `read(target)` ruft
`DNP3Master.read_class(0)` direkt synchron gegen den
DNP3-Outstation.

`nfm-dnp3.DNP3Master` ist sync-by-design (C1-Probe-Run
2026-05-31 verifiziert: alle public Methoden sync, kein
async-Marker; Thread-Lock-Schutz fuer Concurrent-Use per
Library-Doku) und passt damit **ohne** Adapter-internen
Thread+Marshal direkt in die Sync-`DeviceProtocolPort`-
Surface aus ADR 0030 §2.1.

**Vorteil gegenueber Welle 4 (OPC-UA, Decision O-b):**

- Kein `Dnp3LoopThread` analog `OpcuaLoopThread`.
- Kein `run_coroutine_threadsafe`-Marshal-Layer.
- Kein Teardown-Race-Risiko mit pending Tasks.
- `_port.py` ist signifikant einfacher als
  `protocol_opcua/_port.py` (vergleichbar mit
  `protocol_modbus/_port.py`).

**Begruendung:**

- `nfm-dnp3`-Sync-Charakter ist der natuerliche Fit fuer
  die Sync-Surface (Pattern-Praezedenz Welle-3-Modbus-
  Decision-M-c).
- Kein produktives Async-Bridge-Pattern, wenn die
  Library es nicht braucht — YAGNI.
- Falls Welle 6+ einen Async-Pfad fuer `nfm-dnp3` zeigt
  (z. B. wenn die Library in 2.x async wird), kann eine
  Folge-ADR (ADR-0011-Pattern) eine Async-Bridge
  einfuehren, ohne den `DeviceProtocolPort`-Vertrag zu
  aendern.

**Konsequenz:** `Dnp3DeviceProtocolPort.read()` ist
blocking. `nfm-dnp3.DNP3Master`-Calls werden direkt im
TickLoop-Thread ausgefuehrt; Tick-Latenz-Implikation
analog Welle-3-Decision-M-c (typische DNP3-Read-Latenz
20-100 ms; mit konfigurierbarem
`response_timeout_s`-Default 5.0).

**Reconnect-Verhalten:** `nfm-dnp3` wirft
`DNP3CommunicationError` / `DNP3TimeoutError` /
`DNP3ProtocolError` bei Verbindungs-Verlust waehrend
`read()`. Diese werden in typed
`Dnp3PortReadFailedError`-aequivalent umgemantelt
(analog Slice-031/032-Pattern aus M4-Welle-3/4 fuer
Modbus/OPC-UA). Welle 5a macht **keinen** Auto-Reconnect-
Loop — Caller-Pflicht, falls noetig.

### 2.3 Decision D-c — Group/Variation-Set + Codec (final)

Erlaubter Group/Variation-Set in Welle 5a:

- **Group 1, Variation 1 (Binary Input, single-bit)** —
  Python `bool`.
- **Group 1, Variation 2 (Binary Input with flags)** —
  Python `bool` (+ optional flags-Inspektion).
- **Group 30, Variation 1 (32-bit Integer Analog Input)** —
  Python `int`.
- **Group 30, Variation 5 (32-bit Float Analog Input)** —
  Python `Decimal(repr(float))` analog Welle-3-Modbus-
  `float32`-Pfad (ADR 0032 §2.2).

Andere DNP3-Object-Groups bleiben **Welle-6-
Schaerfungspfad** offen via ADR 0011:

- Group 10/12 (Binary Outputs) — Welle-6 falls Write-
  Pfad eingefuehrt.
- Group 20/22 (Counters) — Welle-6.
- Group 30, Variation 2/3/4/6 (16-bit Int / 16-bit Int
  with flags / 32-bit Int with flags / 64-bit Float) —
  Welle-6.
- Group 40/41 (Analog Outputs) — Welle-6.
- Group 32 (Analog Input Events) — Welle-6
  (Event-Class-Polling).

**Konvertierung:** `nfm-dnp3`-Reads liefern typed
Python-Objekte:

- `read_class(0)` → `PollResult` mit `.analog_inputs:
  list[AnalogInput]`, `.binary_inputs: list[BinaryInput]`,
  `.counters: list[Counter]`, plus `.iin: IINFlags`,
  `.success: bool`, `.error: ...`.
- `AnalogInput(idx: int, value: int | float, ...)` —
  `value` ist Python-Native je nach Group/Variation.
- `BinaryInput(idx: int, value: bool, ...)`.

`_codec.py` macht:

- Float-Werte aus Group 30/V5 → `Decimal(repr(value))`
  (Float-Praezisions-Konvention aus ADR 0032 §2.2).
- Int-Werte aus Group 30/V1 → `Decimal(value)` direkt.
- Bool-Werte aus Group 1 → `Decimal(int(value))`
  (Welle-3-Modbus-Pattern fuer TelemetryPoint-Wert).

**Begruendung:**

- Welle-5a-Minimum reicht fuer produktive
  Wechselrichter/Energiemeter-Profile (Power in
  Group 30/V5, Status in Group 1, Energie-Counter in
  Welle-6+).
- Float-Praezisions-Konvention konsistent zu ADR 0032
  §2.2.
- typed Library-Returns reduzieren Decoder-Komplexitaet
  drastisch (kein eigenes Wire-Parsing noetig wie bei
  Modbus).

**Konsequenz:** `_codec.py`-Modul mit
`decode_point_value(point: AnalogInput | BinaryInput,
point_cfg: Dnp3PointConfig) -> Decimal`-Funktion.
Asymmetrie analog ADR 0032 §2.2:
- **Decoding ist tolerant** — wenn der Server eine
  unerwartete Group/Variation liefert (z. B. Welle-5a-
  Config wartet Group 30/V5 aber Server liefert
  Group 30/V1), wird der Wert per
  `Dnp3CodecGroupMismatchError` typed gemeldet.
- **Encoding ist Welle-6-Material** (Write-Pfad).

### 2.4 Decision D-d — Class-0-Polling-Read mit Resultat-Filter (final)

`Dnp3DeviceProtocolPort.read(target)` ruft
`DNP3Master.read_class(0)` **einmal pro `read(target)`-
Aufruf** und filtert die Resultat-Liste nach
`point_cfg.index`:

```python
def read(self, target: str) -> TelemetryPoint | None:
    point_cfg = self._resolve_point_config(target)
    if point_cfg.access != "read":
        raise Dnp3PortReadAccessMismatchError(target, point_cfg.access)
    client = self._require_client(target, "read")
    try:
        poll = client.read_class(0)
    except (DNP3CommunicationError, DNP3TimeoutError, DNP3ProtocolError) as exc:
        raise Dnp3PortReadFailedError(target, point_cfg, str(exc)) from exc
    if not poll.success:
        raise Dnp3PortReadFailedError(target, point_cfg, f"poll error: {poll.error}")
    point = _find_point(poll, point_cfg)  # per Group/Variation/Index
    if point is None:
        raise Dnp3PortReadFailedError(target, point_cfg, "point not in poll result")
    value = decode_point_value(point, point_cfg)
    return _build_telemetry_point(target, point_cfg, value)
```

**Per-Read-Class-0-Cost ist akzeptabel** fuer Welle 5a-
Sim-Scenarios (< 20 DNP3-Targets pro Tick, Polling-Cost
~50-200 ms pro `read_class(0)`-Aufruf — analog
Welle-3-Modbus-Tick-Latenz-Implikation).

**Alternative (verworfen):** `read_class(0)`-Result
cachen und mehrere `read(target)`-Calls daraus bedienen.
Verworfen, weil:
- Welle-5a-Minimum bleibt einfach (kein Cache-Lifecycle,
  keine Cache-Invalidation, keine Stale-Read-Issue).
- Welle 6 (Cross-Adapter-Hardening) kann das Pattern
  generisch fuer alle Adapter einfuehren (Tick-Caching),
  nicht DNP3-spezifisch.

**Begruendung:**

- DNP3-spec-konform: Class-0-Integrity-Poll ist der
  Standard-Read-Pfad in DNP3-Protokoll-Idiomatik.
- Wire-Compat-Robust: C1-Probe-Run 2026-05-31 hat
  `read_class(0)` gegen `dnp3-outstation` v0.2.0
  verifiziert.
- `read_analog_inputs(start, stop)`-Pfad ist **nicht**
  benutzbar (qualifier 0x01-Inkompat mit
  `dnp3-outstation` — siehe §1 Spannungsfeld).
  Welle-6-Schaerfung kann auf eine kompatiblere
  Outstation-Library umstellen, falls Per-Index-Read
  produktiv noetig wird.

**Konsequenz:** `_port.py`-`read()` ist Pfad-monolithisch
(immer `read_class(0)` + Filter). Subscription-/Event-
Class-Polling (Class 1/2/3) bleibt Welle-6-Schaerfung
offen.

**Reconnect-Verhalten:** `nfm-dnp3` haelt die TCP-
Verbindung in `DNP3Master`. Bei Verbindungs-Verlust
wirft `read_class(0)` `DNP3CommunicationError`. Welle 5a
mantelt das in `Dnp3PortReadFailedError`; Caller-Pflicht,
ggf. den Adapter neu zu starten.

**IIN-Restart-Flag-Behandlung:** nach Outstation-Reboot
liefert `read_class(0)` mit `iin.device_restart=True`;
nfm-dnp3 setzt das Flag transparent in
`PollResult.iin.device_restart`. Welle-5a-Adapter
**ignoriert** das Flag (kein Init-Step, kein Write
FC=0x02 zum Clearen) — `dnp3-outstation` v0.2.0 self-
clears das Flag nach der ersten Response (C1-Probe-Run
verifiziert). Welle-6-Schaerfung kann ein explizites
Write FC=0x02 als Welle-Init-Step einfuehren, falls
produktive Outstations das brauchen.

### 2.5 Decision D-e — In-Process `dnp3-outstation` fuer Integration-Smoke (final)

**Test-Sibling-Variante in Welle 5a:** **in-process
`dnp3_outstation.AsyncOutstation`** im Test-Code
(`tests/integration/test_dnp3_in_process_smoke.py`),
**kein** testcontainers-Container.

**Setup (C1-Probe-Run verifiziert):**

```text
1. Test setzt einen `AsyncOutstation` mit pre-konfigurierten
   Analog-Inputs (per `set_analog(idx, value)`).
2. Eigener Test-internes Loop-Thread-Konstrukt
   (`_InProcessDnp3Outstation` in
   `tests/integration/test_dnp3_in_process_smoke.py`) mit
   `asyncio.new_event_loop()` + `Thread(daemon=True)` +
   `asyncio.Event`-Stop-Signal (Pattern-Praezedenz Welle-4-
   Test-Server-Setup nach Slice-032-Schaerfung).
3. Test wartet via `_wait_for_port_open` bis Server
   bereit ist; Init-Errors werden im Thread gecaped
   und im Caller reraised.
4. End-to-End-Read-Roundtrip via
   `Dnp3DeviceProtocolPort.read(target)` durch alle
   Decision-D-c-Group/Variation-Kombinationen
   (Group 1/V1, Group 1/V2, Group 30/V1, Group 30/V5).
5. Teardown:
   `asyncio.run_coroutine_threadsafe(outstation.shutdown(), loop)`
   + `loop.call_soon_threadsafe(loop.stop)` + `thread.join`.
```

**Begruendung:**

- **Lizenz-Sicherheit:** `dnp3-outstation` ist MIT-
  Lizenz, Pure-Python, kein C-Backend-Lock-in. Anders
  als `pydnp3`-Bindings fuer OpenDNP3 (LGPL-2.1) oder
  kommerzielle DNP3-Server-Container.
- **CI-Latenz:** Kein Docker-Image-Pull, kein
  Container-Boot-Wait. AsyncOutstation kommt in der
  Test-Runtime hoch.
- **Pure-Python-Konsistenz:** Beide Welle-5a-Libraries
  sind Pure-Python — keine native-Compile-Notwendigkeit
  in CI; aarch64-Linux-Support automatisch (laut
  `dnp3-outstation`-Metadata).
- **Praezedenz:** Welle-3-Decision-M-f (pymodbus-Server)
  + Welle-4-Decision-O-e (asyncua-Server) als
  bewaehrtes Pattern.

**Wire-Compat-Beleg** (C1-Probe-Run 2026-05-31):

- `nfm-dnp3.DNP3Master.open()` ↔
  `dnp3_outstation.AsyncOutstation.start()` — TCP-
  Verbindung kommt zustande.
- `master.read_class(0)` mit `success=True` liefert
  alle vorab-konfigurierten Analog-Inputs als typed
  `AnalogInput(idx, value, online)`-Liste.
- IIN-Restart-Flag self-clears nach 1. Poll (DNP3-
  Standard).
- 2./3. Polls funktionieren stabil; Wert-Updates per
  `outstation.set_analog(idx, value)` werden vom Master
  in nachfolgenden Polls gesehen.

**Konsequenz:**

- **Keine `tests/integration/compose.yml`-Erweiterung**
  in Welle 5a. Header-Kommentar (C2 EDIT) dokumentiert
  die bewusste Entscheidung als Pattern-Fortfuehrung
  aus Welle 3/4.
- **Keine testcontainers-Fixture.**
- **`dnp3-outstation` als Dev-Dependency:**
  `[dependency-groups.dev]`-Eintrag in `pyproject.toml`
  (nicht in `[project] dependencies`), weil sie nur fuer
  den Integration-Smoke benoetigt wird. Production-
  Adapter laeuft mit `nfm-dnp3` alleine.
- **Daemon-Loop-Thread-Lifecycle:** der Test verwendet
  eigenes `asyncio.Event`-Stop-Signal + `daemon=True`-
  Thread (Pattern aus Welle-4-Slice-032-Schaerfung).
- **Port-Auswahl:** `0` (OS waehlt freien Port) per
  `socket.SOCK_STREAM`-Probe.

---

## 3. Alternativen

**A1 (verworfen) — Separate `dnp3_profiles`-Top-Level-
Section:** wuerde Decision D-a auf eine eigene Schluessel-
Section verlagern. Verworfen wegen YAGNI (siehe ADR 0031
§3 A1 / ADR 0032 §3 A1 / ADR 0033 §3 A1).

**A2 (verworfen) — Adapter-interner asyncio-Loop-
Thread:** `OpcuaLoopThread`-Reuse-Pattern. Verworfen, weil
`nfm-dnp3` sync ist (C1-Probe-Run verifiziert) — kein
Loop-Marshal noetig. Welle 4 OPC-UA hat den Pfad
(asyncua ist async); Welle 5a folgt Welle-3-Modbus-
Pattern (sync direkt).

**A3 (verworfen) — Datatype-Set inklusive
Counter/AnalogOutput/Group 32 (Events) ab Welle 5a:**
wuerde Welle-5a-Codec-Komplexitaet vervielfachen.
Verworfen wegen YAGNI; ADR-0011-Schaerfungspfad bleibt
offen.

**A4 (verworfen) — Per-Index-Range-Read via
`read_analog_inputs(start, stop)`:** spec-seitig
gueltig, aber wire-incompat mit `dnp3-outstation` v0.2.0
(qualifier 0x01-Verworfen — C1-Probe-Run verifiziert).
Welle-6-Schaerfung kann auf eine Outstation-Library
umstellen, die 0x01 supportet, oder den Master-Pfad
auf `read_analog_inputs(group, variation, qualifier=0x00,
start=i, stop=i)` umstellen (qualifier-explizit; nfm-dnp3
hat das aktuell nicht in der Public-API).

**A5 (verworfen, nach Lizenz-Check) — `pydnp3`-Bindings
fuer OpenDNP3:** waere die etablierteste Library
(OpenDNP3 ist Industrie-Referenz). Verworfen wegen:
- LGPL-2.1 statt MIT (Library-Linking-Pflicht zu LGPL-
  Source-Disclosure-Klauseln; Repo bleibt MIT, aber
  Konsumenten-Header brauchen LGPL-Notice).
- pydnp3 v0.1.0 ist 2018-Stand; kein produktiver
  Maintenance; Python 3.14-Kompat fragwuerdig.
- nfm-dnp3 + dnp3-outstation sind beide MIT, Pure-
  Python, aktiv-gepflegt (2024+).

**A6 (verworfen, nach Lizenz-Check) — `dnp3protocol`
(FreyrSCADA):** waere ein einziges Paket mit Master+
Outstation. Verworfen wegen:
- Kommerzieller Backing (FreyrSCADA verkauft DNP3-
  Stacks); MIT-Wrapper, aber Code-Quality + Maintenance-
  Modell unklar.
- Liefert `.dll`/`.so`-Binaries — kein Pure-Python, kein
  aarch64-Support automatisch.

**A7 (verworfen) — testcontainers + OpenDNP3-Server-
Image:** existiert nicht als stabiles Public-Image.
Verworfen — kein Container-Pfad verfuegbar.

**A8 (verworfen) — Read-Class-0-Caching mit
Tick-Lifecycle:** `read_class(0)` einmal pro Tick statt
einmal pro `read(target)`. Verworfen — Welle-6-Material
(Cross-Adapter-Tick-Caching ist generisches Pattern,
nicht DNP3-spezifisch).

**A9 (verworfen) — Asynchron-`AsyncDeviceProtocolPort`-
Schwester-Port:** waere konsistent mit ADR 0030 §2.1-
Folge-Pfad. Verworfen, weil `nfm-dnp3` sync ist — Welle
5a braucht keine async-Surface. Welle 6 kann den
Schwester-Port-Pfad fuer asyncua/DNP3-Async-Migration
ziehen.

---

## 4. Konsequenzen

- **Welle-5a-C2-Implementierungs-Pflicht** (`feat(welle-5a):
  protocol_dnp3 + Tests + In-Process-Smoke + Compose-
  Edit`):
  - NEU `src/grid_gym/adapters/driven/protocol_dnp3/__init__.py`
    mit `Dnp3DeviceProtocolPort` als
    `DeviceProtocolPort`-Implementer (ADR 0030 §2.1).
  - NEU `src/grid_gym/adapters/driven/protocol_dnp3/_config.py`
    (`Dnp3ProtocolPortConfig` + `Dnp3PointConfig`
    frozen-dataclasses, Decision D-a-Schema).
  - NEU `src/grid_gym/adapters/driven/protocol_dnp3/_codec.py`
    (`decode_point_value`-Funktion, Decision D-c).
  - NEU `src/grid_gym/adapters/driven/protocol_dnp3/_port.py`
    (Decision D-b direkt-sync; Decision D-d Class-0-Read-
    mit-Filter; nfm-dnp3-Exception-Translation).
  - NEU `src/grid_gym/adapters/driven/protocol_dnp3/_errors.py`
    (typed `DeviceProtocolPort*Error`-Subclasses
    inkl. Read/Write-Operation-Tax analog Slice-031/032-
    Pattern: `Dnp3PortConnectError`,
    `Dnp3PortDisconnectError`,
    `Dnp3PortReadNotStartedError`,
    `Dnp3PortReadAccessMismatchError`,
    `Dnp3PortReadFailedError`,
    `Dnp3PortWriteAccessMismatchError` etc.).
  - **Modul-Docstring** mit Lastenheft-Z. 1161–1163-
    Pflicht: „Simulations-/Testadapter; keine
    produktive Anlagensteuerung".
  - 3 Unit-Test-Module unter
    `tests/unit/adapters/driven/protocol_dnp3/`
    (Config / Codec / Protocol-Port).
  - 1 Integration-Smoke unter
    `tests/integration/test_dnp3_in_process_smoke.py`
    (Decision D-e).
- **`tests/integration/compose.yml`-Header-Kommentar-
  Sync (C2 EDIT):** dokumentiert die bewusste Decision-
  D-e-Wahl (in-process-Smoke; kein neuer Sibling-
  Service) als Pattern-Fortfuehrung aus Welle 3/4.
- **`pyproject.toml`-Erweiterung:**
  - `nfm-dnp3>=1.0,<2.0` in `[project] dependencies`
    (Produktiv-Adapter).
  - `dnp3-outstation>=0.2,<1.0` in
    `[dependency-groups.dev]` (Test-only).
  - ggf. mypy-Override fuer `dnp3py.*` und
    `dnp3_outstation.*` (Library-Reifegrad pruefen
    in C2).
  - `nfm-dnp3`/`dnp3-outstation`-Sichtbarkeit in
    [`AC-PORTS-NO-FW`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)/AC-NO-FW-Forbidden-Listen — Welle-0-
    Vorbelegung pruefen; ggf. C2-Edit.
- **`Dockerfile`-Erweiterung:** `CRITICAL_COV_TARGETS`-
  Default um `src/grid_gym/adapters/driven/protocol_dnp3`
  erweitert (Pattern analog Welle 2/3/4).
- **`AC-ADAPTER-LIGHTWEIGHT` greift unveraendert**
  (`tools/arch_check.py:1089`
  `bucket.startswith("protocol_")`).
- **Scenario-Loader bleibt DNP3-frei** (AC-HEXAGON-
  PURE): analog zur Welle-2/3/4-Konsequenz aus
  ADR 0031/0032/0033 §4 (`hexagon/core/scenario/loader.py`
  darf `Dnp3ProtocolPortConfig` nicht direkt parsen).
- **Caller-Scope-Lifecycle bleibt ADR-0030-Vertrag:**
  Caller wrappen `loop.start_protocol_ports()` /
  `loop.stop_protocol_ports()` in `try/finally`.
- **Snapshot-Vertrag bleibt v2** (ADR 0030 §2.3):
  DNP3-Adapter ist stateless aus Replay-Sicht;
  Reconnect-State (TCP-Socket + DNP3-Session) und
  IIN-Restart-Flag-Status sind volatile.
- **OTel-Span-Wrap der Adapter-Calls:** ADR 0034
  wrappt Adapter-Calls **nicht** mit OTel-Spans.
  Welle 6 ist der Zeitpunkt fuer den `TracePort`-Wrap.
- **Welle-5b-Implementer-Auflage (IEC-61850-Adapter):**
  Welle 5b folgt analog Welle 5a (separater Adapter,
  separater ADR 0035, eigene `protocol_iec61850/`-
  Modulstruktur). `iec61850`-Library ist async-first
  mit Rust-Backend — Decision-I-b muss `OpcuaLoopThread`-
  Reuse-Pattern erwaegen (Decision-D-b-direkt-sync
  ist nicht reusable). Welle-5a-Erfahrung mit der
  zwei-Library-Konstruktion (Master+Outstation als
  separate Pakete) ist auf Welle 5b uebertragbar,
  falls `iec61850` keinen integrierten Server liefert.
- **Welle-6-Schaerfungs-Pfade:**
  - DNP3-Write-Pfad (Direct-Operate / Select-Before-
    Operate / Pulse-Binary). Welle-5a-Minimum ist
    Read-only.
  - DNP3-Event-Class-Polling (Class 1/2/3) +
    Subscription-Pfad fuer Event-Streams.
  - Per-Index-Range-Read via qualifier 0x00 (8-bit
    range) — wenn Outstation-Library upgegradet wird.
  - DNP3-Security (Secure Authentication, IEEE 1815-
    2012 §10).
  - Tick-Caching von `read_class(0)`-Resultaten
    (generisch fuer alle Adapter, nicht DNP3-spezifisch).

---

## 5. Status-Pfad

- **Proposed** — 2026-05-31 (M4-Welle-5a-C1 `b0fea7e`).
  Initial-Entwurf nach C1-Probe-Runs (nfm-dnp3-API-
  Inspektion + Wire-Compat-Probe gegen dnp3-outstation),
  Decisions D-a..D-e durch Probe-Ergebnisse final-belegt.
- **Provisional** — 2026-05-31 (M4-Welle-5a-C3, dieser
  Commit) nach C2-Merge `224b370` (feat-Commit:
  `protocol_dnp3/`-5-Modul-Paket — `__init__.py` +
  `_config.py` + `_codec.py` + `_port.py` + `_errors.py`
  — mit 56 neuen Unit-Tests (17 Config-Validation + 16
  Codec-Roundtrip inkl. hypothesis-Property-Tests + 17
  Protocol-Port-Lifecycle/Read-Pfad-gegen-mocked-Master +
  4 In-Process-Integration-Smoke gegen
  `dnp3_outstation.AsyncOutstation`-Sibling);
  `pyproject.toml`-Pin `nfm-dnp3>=1.0,<2.0` in `[project]
  dependencies` + `dnp3-outstation>=0.2,<1.0` in
  `[dependency-groups.dev]` (Welle-5a-Test-Sibling-only);
  mypy-Overrides `module="dnp3py.*"` und
  `module="dnp3_outstation.*"` mit
  `ignore_missing_imports = true` (beide Libraries
  liefern kein py.typed); `uv.lock`-Refresh mit 110
  packages (+nfm-dnp3 v1.0.1, +dnp3-outstation v0.2.0;
  keine transitiven Deps); `Dockerfile`-Edit
  (`CRITICAL_COV_TARGETS` um
  `adapters/driven/protocol_dnp3` erweitert);
  `compose.yml`-Header-Kommentar-Sync zu Decision-D-e
  in-process-AsyncOutstation. Verifikation cache-frei:
  `make test-unit` 1462 gruen, `make test-integration`
  35 gruen (31 → 35, +4 DNP3-Roundtrips: 3 Class-0-Read
  + 1 Update-then-Read), `make arch-check` 19/19 KEPT,
  `make gates` 9 A-1-Gates gruen ohne
  `CRITICAL_COV_TARGETS`-Override. C2-Library-Bug-Find
  (`AnalogInput.idx` vs. `.index`, siehe Status-Header)
  in C3 dokumentiert.
- **Accepted** — 2026-06-01 mit M4-Welle-7-C1 (dieser
  Commit, M4-Closure-Welle; analog ADR 0022..0027 + 0030
  + 0031 + 0032 + 0033). Voraussetzung erfuellt: Welle 5b
  (IEC-61850, ADR 0035) ist per ADR-0011-Pattern
  dokumentiert; Welle 6 (Cross-Adapter-Hardening:
  Welle 6a OTel-Span-Wrap + Welle 6b GPL-Boundary) ist
  orthogonal zur DNP3-Zwei-Library-Konstruktion — keine
  Schaerfungs-Folge fuer DNP3-Decisions. Welle 6 prueft,
  ob die zwei-Library-Konstruktion (Master+
  Outstation als separate Pakete) Welle-6-Schaerfungs-
  Bedarf zeigt. Folge-Pflicht: M4-Welle-7-Closure
  schaerft ADR 0030 §2.4 (Welle-1-DNP3-Verzicht-
  Default) auf „durch Welle-5a-Spike-Lieferung
  aufgeloest" (Pattern ADR 0011).
