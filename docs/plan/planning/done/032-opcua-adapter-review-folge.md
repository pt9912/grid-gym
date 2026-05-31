# 032 — OPC-UA-Adapter Review-Folge

**Status:** Done — umgesetzt nach M4-Welle-4-Code-Review
2026-05-31. Dieser Slice behebt die im Welle-4-Closure-Review
gefundenen `protocol_opcua/`-Adapter-Luecken, ohne den Welle-4-
Scope rueckwirkend umzudefinieren. Pattern analog Slice 031
(Modbus-Review-Folge).
**Quelle:** Code-Review der Welle-4-Commits
`410c7f6..7ad5baf` (5 Commits: DoD-Erweiterung + Slice-Doc +
ADR 0033 Proposed + feat + C3-Doc-Sync); Reviewer hat 6 HIGH +
11 MEDIUM-Findings identifiziert.

---

## Lieferung

**6 HIGH-Findings (Blocker fuer Welle-4-Provisional-Closure):**

1. **`OpcuaLoopThread.stop()` State-Race (Finding 1.1)** —
   State-Nulling (`_loop=None, _thread=None, _started=False`)
   erfolgte **vor** Cancel/Join. Parallel-`start()` haette
   einen Zombie-Loop spawnen koennen. Fix: State-Nulling
   **nach** erfolgreichem Cancel/Join.

2. **`_cancel_pending` `RuntimeError`-Suppress (Finding 1.2)** —
   `asyncio.run_coroutine_threadsafe` kann `RuntimeError`
   ("Event loop is closed" / "loop is not running") werfen,
   wenn der Loop intern bereits gestoppt hat. `contextlib.
   suppress` fing nur `TimeoutError`/`CancelledError`.
   Fix: `RuntimeError` in beiden Suppress-Bloecken ergaenzt.

3. **`ready.wait()` ohne Timeout (Finding 1.3)** —
   `OpcuaLoopThread.start()` haette ewig blockiert, wenn der
   Daemon-Thread nie `ready.set()` aufruft. Fix: neuer
   `start(timeout_s=5.0)`-Kwarg + typed
   `OpcuaLoopThreadStartTimeoutError`, falls Timeout reisst.

4. **Fehlende Lifecycle-Locks (Finding 1.4)** — Concurrent
   `start()`/`stop()` aus verschiedenen Threads waren
   race-anfaellig. Fix: `threading.Lock()` als
   `_lifecycle_lock`; beide Methoden serialisieren ihren
   State-Zugriff.

5. **Port-Exception-Filter inkomplett (Finding 2.3)** —
   `(OSError, TimeoutError, uaerrors.UaError, OpcuaLoopThreadError)`
   fing `RuntimeError` (Loop-Crash) und `asyncio.CancelledError`
   (Coroutine-Cancel) nicht. Fix: neue Konstante
   `_LOOP_EXCEPTIONS` mit erweitertem Tupel; alle vier
   `except`-Stellen in `_port.py` benutzen die Konstante.

6. **String-Read Telemetrie-Verlust (Finding 3.1)** —
   `_to_decimal`-String-Pfad lieferte `Decimal(0)` als
   Platzhalter, ohne den Original-String mitzugeben.
   Docstring versprach Original-String-Erhalt in `source`-
   Feld, tat es aber nicht. Fix: neue `_telemetry_payload`-
   Funktion liefert `(Decimal(0), Quality.INVALID,
   "protocol_opcua.<target>#string=<value>")` fuer
   String-Targets — Downstream-Konsumenten sehen
   `Quality.INVALID` als Sentinel-Marker.

**11 MEDIUM-Findings (vor Provisional-Closure adressiert):**

7. **`is_running` lügt bei Loop-Crash (Finding 1.5)** —
   Property reflektierte nur `_started`. Fix: zusaetzlich
   `self._loop.is_running()` pruefen.

8. **Doku-Drift `loop.close()` (Finding 1.8)** — Klassen-
   Docstring versprach unconditional `loop.close()`. Fix:
   Modul-Docstring + Klassen-Docstring beschreiben jetzt
   konditionales Close (nur wenn `thread.join` greift).

9. **`_require_client` String-Typing (Finding 2.6)** —
   `operation: str` war kein Literal-Type. Fix:
   `Literal["read", "write"]` als Parameter-Type.

10. **`Float`-32bit-Praezision (Finding 3.2)** — `Decimal
    (repr(float))` traegt 17 Stellen, obwohl `Float`
    (32-bit) nur ~7 Stellen Wire-Praezision hat. Fix:
    `struct.unpack('!f', struct.pack('!f', x))[0]`-
    Quantisierung im `_decode_float`-Pfad fuer `FLOAT`-
    Datatype; `DOUBLE` bleibt 64-bit-genau.

11. **`OverflowError`-Catch im Float-Decode (Finding 3.3)** —
    Server-seitige `Int64`-Werte jenseits der `float`-Range
    haetten `OverflowError` durch die Port-Surface
    propagiert. Fix: typed `OpcuaCodecDecodeError`-Wrap.

12. **Marshal-Pfad-Test (Finding 4.1)** — Kein Test
    pruefte, dass `read()`/`write()` die Coroutine ueber
    den Loop-Thread marshalen (vs. im Caller-Thread
    auszufuehren). Fix:
    `test_read_marshals_coroutine_through_loop_thread`-
    Test mit `threading.get_ident()`-Vergleich.

13. **Hypothesis-Surrogate-Blacklist (Finding 4.2)** —
    `st.text(max_size=64)` produzierte UTF-16-Surrogates,
    die UTF-8-Wire-Format nicht abbildet. Fix:
    `alphabet=st.characters(blacklist_categories=("Cs",))`.

14. **Double-Toleranz (Finding 4.3)** — `rel_tol=1e-9` war
    zu locker fuer IEEE-754-double (~15 signifikante
    Stellen). Fix: `rel_tol=1e-15`.

15. **Pin-Strategie (Finding 5.1)** — `asyncua==1.2b2`
    war exakt-pinning, kein Auto-Upgrade-Pfad. Fix:
    `asyncua>=1.2b2,<2.0` (erlaubt 1.2b3 / 1.2-final
    ohne `pyproject.toml`-Edit, sperrt 2.x-Major-Drift).

16. **Smoke-Server-Loop-Idiom (Finding 7.1)** — `while
    True: await asyncio.sleep(0.5)` als Stop-Wait war
    Polling. Fix: `asyncio.Event` als Stop-Signal; Server-
    Coroutine wartet effizient via `await event.wait()`.

17. **Smoke-Server-Init-Exception-Capture (Finding 7.3)** —
    `contextlib.suppress(Exception)` im Thread-Target
    schluckte Setup-Fehler stillschweigend; Caller sah
    nur `ready.wait()`-Timeout. Fix: Init-Errors werden
    im Thread gecaped (`self._init_error`), und in
    `start()` reraised, falls `ready.wait()` reisst oder
    der Thread mit Error endet.

**ADR-0033-Schaerfungen (Body-Edits ohne Status-Wechsel):**

- §2.1 Konsequenz: Optional-Felder
  `namespace_index`/`identifier_type` aus dem
  Welle-4-Schema entfernt (YAGNI; Welle-6-Schaerfungspfad
  bleibt offen). YAML-Beispiel angepasst (kein
  `namespace_index`-Override-Block mehr).
- §2.5 Setup-Skizze: Test-Server-Loop ist bewusst getrennt
  von der produktiven `OpcuaLoopThread`-Klasse (Server-
  Lifecycle braucht andere Signal-Semantik als Client).
- §5 Status-Pfad: Slice-032-Eintrag mit Begruendung.

## Verifikation

- `make gates` — gruen; 1401 Unit-Tests (1395 → 1401 = +6
  neue Tests: 4 Loop-Thread-Schaerfungen + 1
  Marshal-Pfad-Test + 1 String-Read-Quality.INVALID-Test
  + Codec-Edge-Cases); 95.x % Total-Coverage,
  Branch-Critical-Coverage > 90 %.
- `make test-integration` — gruen; 31 Tests inkl. 8
  OPC-UA-In-Process-Smokes mit neuem
  `asyncio.Event`-Stop-Signal.
- `make arch-check` — 19/19 Contracts KEPT.
- `make docs-check` — gruen (alle Link-Targets, inkl.
  Slice-032-Doc-Pfad).
- `mypy --strict-bytes` — gruen.

## Wandert Nach

- `done/032-opcua-adapter-review-folge.md` (dieses Dokument).
