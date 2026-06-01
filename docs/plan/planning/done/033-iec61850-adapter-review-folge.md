# 033 — IEC-61850-Adapter Review-Folge

**Status:** Done — umgesetzt nach M4-Welle-5b-Code-Review
2026-06-01. Dieser Slice behebt die im Welle-5b-Closure-Review
gefundenen `protocol_iec61850/`-Adapter-Luecken sowie die
Lizenz-Boundary- und Build-Setup-Findings, ohne den Welle-5b-
Scope rueckwirkend umzudefinieren. Pattern analog Slice 031
(Modbus-Review-Folge) und Slice 032 (OPC-UA-Review-Folge).

**Quelle:** Code-Review der Welle-5b-Commits `9fea2be..ca96bca`
(7 Commits: Pre-C0a + Pre-C0b + C0 + C1 + C1-Review-Folge +
C2 + C3); 5-Angle-Finder hat 15 Findings identifiziert
(10 HIGH + 5 MEDIUM), Phase-3-Sweep hat keine weiteren
Defekte ergaenzt.

---

## Lieferung

**10 HIGH-Findings (Korrektheits-Bugs):**

1. **Except-Chain-Collapse im Optional-Extra-Off-Pfad
   (Finding 1)** — `_port.py:84-90` aliased alle `_PyIec*Error`
   auf `Exception`. Die except-Chain `except _PyIecNotConnectedError`
   → `except _PyIecReadError` → `except _PyIecMMSError` kollabierte
   zu drei identischen `except Exception`, nur die erste feuerte.
   Read-Errors wurden mis-translatiert auf
   `Iec61850PortReadNotStartedError`. Fix: **private Sentinel-
   Exception-Klasse** `_IecExtraOffSentinelError` statt `Exception`
   — die except-Klauseln im Off-Pfad fangen **nichts** statt
   **alles**.

2. **`TelemetryPoint.value`-Contract-Drift (Finding 2)** —
   `_build_telemetry_point` schrieb `bool/int/str` direkt in
   `TelemetryPoint.value`, aber das Domain-Modell garantiert
   `value: Decimal` (`telemetry.py:43`). Welle-3-Modbus + Welle-
   5a-DNP3 wandeln zu `Decimal`; Welle-4-OPC-UA-Slice-032
   Finding 3.1 hat den String-Pfad als `Decimal(0)` + `Quality.
   INVALID` + Original-String im `source` etabliert. Fix:
   `_telemetry_payload()` + `_to_decimal()`-Helfer analog
   Welle-4-Pattern.

3. **`_decode_float` akzeptiert NaN/Infinity (Finding 3)** —
   `Decimal(repr(float('nan')))` → `Decimal('NaN')` ohne
   Exception. Tick-Loop-Math wurde NaN-poisoned. Fix: `math.
   isnan(...)/isinf(...)` mit typed `Iec61850CodecOverflowError`.

4. **`stop()` mutiert State VOR `disconnect()` (Finding 4)** —
   `self._client = None; self._started = False` lief VOR
   `client.disconnect()`. Bei nicht-gefangener Disconnect-
   Exception ging der Client-Handle verloren, libiec61850-
   native Threads liefen weiter. Fix: State-Mutation **nach**
   erfolgreichem `disconnect()`; bei Exception bleibt Adapter
   im `started`-Status fuer Retry/Cleanup.

5. **`start()` Factory-Call OUTSIDE try-Block (Finding 5)** —
   `client = self._client_factory(self._config)` lief vor dem
   try-Block. Factory-Exceptions (Constructor-Fehler,
   `ValueError` bei bad config) propagierten raw statt
   `Iec61850PortConnectError`. Fix: Factory + connect zusammen
   im try-Block.

6. **`start()` except omits `_PyIecMMSError` (Finding 6)** —
   Catch-Tupel `(ConnectionFailedError, ConnectionTimeoutError,
   ConnectionError, OSError)` fing nur Connection-Subklassen.
   Library-`MMSError` (z. B. handshake-MMS-Protocol-Error,
   `OperationError`) propagierte raw. Fix: `_PyIecMMSError`
   als Catch-All-Basis-Klausel ergaenzt (deckt alle Sub-
   klassen ab; spezifischere Klauseln bleiben fuer Lesbarkeit).

7. **`_is_container_repr` false-positive fuer legit Strings
   (Finding 7)** — `raw_value.startswith('<MmsValue')`
   blockierte ALLE Datatypes inkl. `string`. Ein legitimer
   `NamPlt.d`-Label-Wert mit Praefix `<MmsValue is cool>`
   wurde faelschlich verworfen. Fix: Container-Check ist nur
   bei `datatype != "string"` aktiv.

8. **`_decode_float` silent int→float-Praezisionsverlust
   (Finding 8)** — `isinstance(raw_value, (float, int))`
   akzeptierte `int`; `float(2**60)` verlor 6 Bits. Fix:
   nur `float` akzeptieren; `int` triggert
   `Iec61850CodecValueTypeError`.

9. **Dockerfile `build-app`-Stage ohne `--extra iec61850`
   (Finding 9)** — `deps`+`source`-Stages installierten das
   Extra, aber `build-app` (Z. 353) lief `uv sync --frozen
   --no-dev --no-editable` ohne den Flag. Runtime-Image hatte
   kein `pyiec61850-ng`; Production-Scenarios mit
   `type: iec61850` crashten erst zur Laufzeit. Fix: `--extra
   iec61850` zum build-app-Stage. Distribution-Implikation
   ueber GPLv3 ist im Dockerfile-Kommentar dokumentiert.

10. **`simpleIO.cfg` ohne SPDX-Header + Attribution
    (Finding 10)** — Fixture-Struktur ist von
    `mz-automation/libiec61850/examples/server_example_config_file/
    model.cfg` (GPL-3.0) abgeleitet, hatte aber weder SPDX-
    Header noch Upstream-Attribution. Fix: `#`-prefixed
    Kommentar-Block mit `SPDX-License-Identifier: GPL-3.0-only`
    und Hinweis auf die Derivative-Work-Beziehung zu
    libiec61850 / MZ Automation.

**5 MEDIUM-Findings (Edge-Cases + Metadata):**

11. **Anti-Scope-Write-Leak in Config (Finding 11)** —
    `_validate_single_ln_config` akzeptierte `access in
    ("read", "write")`. Welle-5b ist Read-only;
    `access="write"`-Targets crashten erst zur Laufzeit in
    `port.write()` mit `Iec61850PortWriteNotImplementedError`.
    Fix: Config-Validation rejected `access != "read"` mit
    geschaerfter `Iec61850ConfigInvalidAccessError`-Message.

12. **Sub-Millisekunden-Timeout-Floor (Finding 12)** —
    `int(response_timeout_s * 1000)` floort auf 0 fuer
    `response_timeout_s < 0.001`. libiec61850 interpretiert
    0ms uneinheitlich. Fix: `max(1, int(...))` im
    `_default_client_factory`.

13. **`NotConnectedError` mid-flight-vs-pre-start-Konflation
    (Finding 13)** — `read()` mappte `_PyIecNotConnectedError`
    immer auf `Iec61850PortReadNotStartedError`. Aber
    `_require_client` garantiert oben, dass `self._client is
    not None`; jedes NotConnected hier ist mid-flight Session-
    Drop. Fix: NEU `Iec61850PortReadConnectionLostError`
    (Subclass von `Iec61850PortReadFailedError`); `read()`
    mappt auf den neuen Error.

14. **Test-Fixture Setup outside try-Block (Finding 14)** —
    `IedServer(model_path=...)` + `server.start(port)` liefen
    VOR dem try-Block der Smoke-Fixture. Bei start-Exception
    lief `finally: server.stop()` nicht. Fix: Server-
    Construction + start im try-Block; `server: IedServer |
    None = None`-Sentinel; `finally`-Block gated auf
    `server is not None`.

15. **`pyproject.toml`-Classifier ohne GPL (Finding 15)** —
    Klassifizier-Liste fuehrte nur MIT auf. SBOM-Tools
    (FOSSA/ScanCode/Debian cme) klassifizierten
    `grid-gym[iec61850]` als reines MIT — false-clean.
    Fix: zweiter Klassifizier `License :: OSI Approved ::
    GNU General Public License v3 (GPLv3)` ergaenzt; PEP-621
    erlaubt mehrere License-Classifier explizit.

**Zusaetzliche Aufraeumarbeiten:**

- Unused `Final`-Import aus `_port.py` entfernt (Sweep #5).
- Toter `if TYPE_CHECKING`-Block mit `_MmsClient`-Alias am
  Modul-Ende entfernt (Sweep #6).
- Redundanter `not isinstance(..., bool)`-Guard in
  `_decode_bool` (folgt nach `isinstance(raw_value, bool)`-
  return) entfernt (Sweep-Item).
- Inner-Decoder-Helfer (`_decode_bool`/`_decode_int32`/
  `_decode_float`) bekommen den `fc`-Parameter durchgereicht
  statt `"?"`-Placeholder zu verwenden (Sweep-Item).

---

## Tests

**Neue Unit-Tests** (`tests/unit/adapters/driven/protocol_iec61850/`):

- `test_iec61850_codec.py`:
  - NEU `test_decode_float_rejects_int` (statt vorher
    `test_decode_float_accepts_int` — Behavior gedreht,
    Finding 8).
  - NEU `test_decode_float_rejects_nan` (Finding 3).
  - NEU `test_decode_float_rejects_inf` (Finding 3).
  - NEU `test_decode_float_rejects_neg_inf` (Finding 3).
  - NEU `test_decode_accepts_mms_container_prefix_for_string`
    (statt vorher `test_decode_rejects_mms_container_repr_for_string`
    — Behavior gedreht, Finding 7).
  - NEU `test_decode_accepts_legit_string_starting_with_mms_value`
    (konkretes Beispiel-Test, Finding 7).
- `test_iec61850_config.py`:
  - NEU `test_config_rejects_write_access_welle5b_anti_scope`
    (Finding 11).
- `test_iec61850_protocol_port.py`:
  - NEU `test_read_translates_not_connected_to_connection_lost_error`
    (Finding 13).
  - `test_read_returns_telemetry_with_decoded_int32` umgestellt
    auf `Decimal(42)` (Finding 2).
  - `test_read_returns_telemetry_with_decoded_string` umgestellt
    auf `Decimal(0)` + `Quality.INVALID` + Source-`#string=...`
    (Finding 2).
  - `test_read_returns_telemetry_with_decoded_bool` umgestellt
    auf `Decimal(1)` (Finding 2).
  - `test_write_before_start_raises_typed_error` umgestellt auf
    `Iec61850PortWriteAccessMismatchError`, weil
    `access="write"` in Config nicht mehr erlaubt (Finding 11
    Folge-Effekt).
  - `test_read_on_write_target_raises_access_mismatch` und
    `test_write_with_write_target_raises_not_implemented`
    entfernt, weil sie write-target-Config voraussetzten
    (Finding 11 Folge-Effekt).

---

## Verifikation

- `make test-unit`: gruen (1537 → 1538+ Tests; +3 neue Tests
  netto: 4 neue Tests im Codec/Config + 1 neuer Port-Test —
  2 entfernte Port-Tests = +3).
- `make test-integration`: gruen mit 4 IEC-Smokes weiterhin
  via `pytest.mark.skip` (Decision I-e 2c-Mock-only-Fallback
  bleibt aktiv; Welle-6-Schaerfungspfad).
- `make arch-check`: 19/19 Contracts KEPT.
- `make gates`: 9/9 A-1-Gates gruen ohne
  `CRITICAL_COV_TARGETS`-Override.

---

## ADR 0035 Schaerfung

ADR 0035 Body wird im Doc-Sync-Commit minimal angepasst:

- §1 Kontext: `_PyIecMMSError`-Catch-All-Hinweis in der
  Exception-Famille-Liste.
- §2.2 Decision I-b: Hinweis auf Sentinel-Klassen-Pattern
  fuer Optional-Extra-Off.
- §2.3 Decision I-c: NaN/Inf-Reject + int-Reject fuer
  float-Datatype dokumentiert.
- §2.4 Decision I-d: `NotConnectedError` → `ConnectionLostError`
  mid-flight-Mapping ergaenzt.
- §2.5 Decision I-e: Test-Fixture-try-Block-Note.
- §2.6 Decision I-f: Build-app-Stage-Propagation +
  Classifier-Erweiterung dokumentiert.
- §4 Konsequenzen: Welle-6-Schaerfungs-Pfade erweitert.

Status-Pfad bleibt `Provisional` (M4-Welle-5b-C3-Stand);
Slice 033 ist Schaerfungs-Folge nach C3, kein
Status-Aenderung.

---

## Wandert nach

- `done/M4-welle-5b.md` mit M4-Welle-6-Pre-C0-Move (Pattern
  Welle 1..5a).
- ADR 0035 bleibt in `docs/plan/adr/`; finale Akzeptanz mit
  M4-Welle-7-Closure.
- M4-Welle-6 zieht die im Review identifizierten Welle-6-
  Schaerfungspfade durch (SPDX-Header-Konsistenz-Check in
  `tools/check_refs.py`, CONTRIBUTING.md-Sync mit GPL-Boundary-
  Policy, `arch_check.py`-Contract gegen GPL-Boundary-Crossing,
  IedServer-Smoke-Reaktivierung Python-3.12-Pfad).
