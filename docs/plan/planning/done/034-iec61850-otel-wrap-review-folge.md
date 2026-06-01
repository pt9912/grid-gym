# 034 — OTel-Span-Wrap und Planted-Violator-Test Review-Folge

**Status:** Done — umgesetzt nach M4-Welle-6a-Code-Review
2026-06-01. Dieser Slice behebt die im Welle-6a-Closure-Review
gefundenen `OtelSpanWrappedDeviceProtocolPort`- und Planted-
Violator-Test-Luecken sowie kleinere Spec-/Audit-Trail-
Findings, ohne den Welle-6a-Scope rueckwirkend umzudefinieren.
Pattern analog Slice 031 (Modbus-Review-Folge), Slice 032
(OPC-UA-Review-Folge) und Slice 033 (IEC-61850-Review-Folge).

**Quelle:** Code-Review der Welle-6a-Commits `838d904..69b37f1`
(7 Commits: Sub-Slicing-Refactor + C0 + C1 + C2 + Pre-C3 +
C3 + C4); 5-Angle-Finder + Phase-3-Sweep hat 15 Findings
identifiziert (1 HIGH + 6 MEDIUM + 4 LOW-MEDIUM + 4 LOW). 14
Findings werden in Slice 034 produktiv adressiert; Finding 13
(`AC-ADAPTER-LIGHTWEIGHT`-Coverage-Gap) ist als Welle-6b-
Vorlauf-Item in `M4-protocol-adapters.md §3 Welle 6b`
verankert (kein Code-Fix in 034 — Coverage-Schaerfung gehoert
in den Welle-6b-`arch_check.py`-Slice).

---

## Lieferung

**1 HIGH-Finding (Korrektheits-Bug):**

1. **`_safe_end_span` Span-Leak bei `record_event`-Fehler
   (F1)** — `_protocol_otel_wrap.py:238` wrappte beide Calls
   (`record_event("latency", ...)` und `end_span`) in einem
   gemeinsamen `with contextlib.suppress(Exception):`-Block.
   Wenn `record_event` raised, exitiert der `with`-Block und
   `end_span` lief NIE → Span leakt auf dem TracePort-Backend,
   die dokumentierte Garantie "Span wird im finally
   geschlossen" brach. **Fix:** zwei separate
   `with contextlib.suppress(*_BEST_EFFORT_OBSERVABILITY_EXCEPTIONS)`-
   Bloecke. Plus zwei neue Tests
   (`test_end_span_still_called_when_latency_record_event_raises`
   und `..._when_error_record_event_raises`).

**6 MEDIUM-Findings:**

2. **`reference` Span-Attribut Spec-vs-Impl-Drift (F2)** —
   `spec/architecture.md:531` listete `reference` als
   Standard-Span-Attribut, der Wrapper emittierte es nie.
   **Fix:** Constructor-arg `reference: str | None = None`
   ergaenzt; bei != None wird `attributes["reference"]` im
   Span gesetzt. Spec-Text geschaerft (latency_ms ist
   Event-encoded, nicht Span-Attribut, weil `TracePort`
   keine `set_attribute`-Surface kennt). Zwei neue Tests
   (`test_reference_attribute_emitted_when_constructor_supplies_it`
   und `..._present_on_write_span_too`).

3. **`write()`-Catch zu breit (F3)** — `_call_with_span_write`
   fing `DeviceProtocolPortError` (Base-Class), womit auch
   `DeviceProtocolPortReadError` aus einer fehlerhaften
   `write()`-Implementation als `error`-Event auf einem
   `write`-Span attribuiert wurde (falsche Operation-
   Kontext). Symmetrisch fuer `read()`-Catch. **Fix:**
   `read()` faengt nur `DeviceProtocolPortReadError`,
   `write()` faengt nur `DeviceProtocolPortWriteError`.
   Misclassified Errors propagieren raw ohne Error-Event-
   Attribution. Zwei neue Tests
   (`test_read_does_not_catch_write_error`,
   `test_write_does_not_catch_read_error`).

4. **Planted-Violator vacuous-pass-Test (F4)** —
   `test_high_complexity_outside_adapter_paths_is_ignored`
   schrieb eine Datei unter `hexagon/core/`, aber
   `_check_adapter_lightweight` startet `_iter_py_files`
   bei `adapters/`, das hexagon-Pfade niemals erreicht. Der
   Test passte vacuously und konnte keine Regression im
   Pfad-Filter erkennen. **Fix:** Test umbenannt zu
   `test_path_filter_rejects_paths_outside_adapter_boundary`
   und auf direkten Aufruf von `_is_adapter_lightweight_path`
   umgestellt mit 8 Pfad-Property-Assertions (positiv und
   negativ).

5. **Trace-Parent-Span-Propagation (F5)** — Wrapper rief
   `start_span` ohne `parent=`-Argument; jeder Adapter-Span
   war ein Root-Span, die `Tick → Phase → Adapter`-Kausal-
   Kette war im OTLP-Backend nicht sichtbar. **Fix (Anti-
   Scope-Doku):** Trace-Chain-Propagation ist OTLP-Adapter-
   Sache via OTel-ContextVars (W3C-Trace-Context-Standard);
   der Wrapper bleibt context-var-naiv. Module-Docstring
   verankert das explizit ("Trace-Parent-Span-Anti-Scope"
   Section); Welle-7-Closure prueft ob ein expliziter
   `parent_provider`-Hook noetig ist.

6. **`sys.modules`-Leak im Planted-Violator-Fixture (F6)** —
   `_arch_check_module`-Fixture schrieb
   `sys.modules["_arch_check_under_test"] = module` ohne
   Cleanup. Pytest-xdist-Workers haetten den Eintrag geteilt;
   `sys.modules` blieb nach Session-Teardown verschmutzt.
   **Fix:** Fixture auf yield-Pattern umgestellt mit
   `sys.modules.pop("_arch_check_under_test", None)` im
   finally-Block. Pytest-xdist-Race-frei.

7. **MagicMock ohne `spec=DeviceProtocolPort` (F7)** —
   `_make_mock_adapter()` benutzte `MagicMock()` ohne
   Protocol-Bindung. Versehentliche Wrapper-Aufrufe auf
   non-Protocol-Methoden (z. B. `_wrapped._private_x()`)
   waeren von MagicMock silently absorbiert worden →
   Protocol-Surface-Drift unsichtbar. **Fix:**
   `MagicMock(spec=DeviceProtocolPort)`; bei fehlenden
   Methoden wirft Mock `AttributeError`.

**4 LOW-MEDIUM-Findings:**

8. **`method: object` mit `type: ignore[operator]` (F8)** —
   `_call_with_span`-Helper typte den Bound-Method-Argument
   als `object` und unterdrueckte den `operator`-Fehler mit
   `# type: ignore`. Signature-Drift in
   `DeviceProtocolPort.read` (z. B. neue Kwarg) waere von
   mypy --strict nicht erkannt worden. **Fix:** Helper-
   Methoden ohne `method`-Parameter zusammengefuehrt;
   `Callable[[str], "TelemetryPoint | None"]`-Typ fuer den
   Bound-Method-Verweis. Kein `type: ignore` mehr im Hot-
   Path.

9. **Catch-Scope-Asymmetrie `_safe_start_span` vs
   `_safe_end_span` (F9)** — `_safe_start_span` fing ein
   eng-gefasstes 6-er-Tuple (`RuntimeError`, `AttributeError`,
   `TypeError`, `ValueError`, `KeyError`, `OSError`), waehrend
   `_safe_end_span` und `_record_exception`
   `contextlib.suppress(Exception)` benutzten. Inkonsistente
   Best-Effort-Scope. **Fix:** Module-Level-Konstante
   `_BEST_EFFORT_OBSERVABILITY_EXCEPTIONS` ueber alle drei
   Helper hinweg. Sichtbare Signale bei unbekannten
   Library-Bugs statt stiller Swallow.

10. **`latency_ms` als Event vs OTel-Standard-Span-Duration
    (F10)** — OTel-Convention encodet Latency typischerweise
    via Span-Start/End-Timestamps (Span-Duration). Spec-Text
    war zweideutig. **Fix (Spec-Schaerfung):**
    `spec/architecture.md` klargestellt: `latency_ms` ist
    Event-encoded (TracePort hat keine `set_attribute`-Surface;
    Latency ist beim `start_span`-Call noch nicht bekannt).
    Downstream-Collector kann zusaetzlich die Span-Duration
    auswerten — beide Werte sind konsistent dank F12
    (`start_ns` VOR `_safe_start_span`).

11. **`adapter_type` ohne Whitelist-Validation (F11)** —
    Constructor-arg `adapter_type: str` ohne Type-Whitelist;
    Caller-Mistakes (`"IEC61850"` vs `"iec61850"`) waren
    static-type-safe. **Fix:** `AdapterType = Literal[
    "mqtt", "modbus", "opcua", "dnp3", "iec61850"]`-Typ-
    Alias am Modul-Anfang; Constructor-Parameter darauf
    eingeengt. Mypy --strict faengt Caller-Mistakes static.

**4 LOW-Findings:**

12. **`start_ns` exkludiert `start_span`-Overhead (F12)** —
    `start_ns = time.monotonic_ns()` lief NACH
    `_safe_start_span`, sodass langsame `start_span`-Calls
    (synchroner OTLP-Exporter-Flush) NICHT in `latency_ms`
    abgebildet wurden — User-perceived Latency wurde
    systematisch unterreportiert. **Fix:** `start_ns`-
    Capture VOR `_safe_start_span` in beiden
    Operation-Helpern. Trade-off (langsamer Trace-Init
    erhoeht reported latency_ms) ist gewollt — User
    sieht das, was er wirklich erlebt.

13. **`AC-ADAPTER-LIGHTWEIGHT`-Coverage-Gap (F13)** —
    `_is_adapter_lightweight_path` (`tools/arch_check.py:
    1067-1090`) erfasst die Pfade
    `src/grid_gym/adapters/driven/_protocol_*.py` NICHT,
    weil `parts[4]` mit `protocol_`/`persistence_` starten
    muss und Underscore-Prefix-Files dieses Praefix nicht
    erfuellen. **Welle-6b-Vorlauf-Item:** als TODO in
    `M4-protocol-adapters.md §3 Welle 6b` verankert; kein
    Code-Fix in Slice 034 (Coverage-Schaerfung gehoert in
    den Welle-6b-`arch_check.py`-Slice mit dem `AC-IEC61850-
    GPL-BOUNDARY`-Contract).

14. **`Literal["read"]`-Asymmetrie (F14)** —
    `_call_with_span(operation: Literal["read"], ...)`
    over-narrow vs `_safe_start_span`'s `Literal["read",
    "write"]`. Asymmetrisch, Cargo-Cult-Risiko fuer eine
    dritte Operation. **Fix:** Operation-Argument aus den
    beiden Helpern entfernt; `_call_with_span_read` und
    `_call_with_span_write` sind dedizierte Helper, die
    `_safe_start_span` mit hart-kodiertem `"read"`/`"write"`
    aufrufen. Asymmetrie eliminiert; `_safe_start_span`
    bleibt mit `Literal["read", "write"]` als
    "Allowed-Operations"-Contract.

15. **Lastenheft GG-DNP3-001/GG-IEC-001 Audit-Trail-Note
    (F15)** — `spec/lastenheft.md §16` hatte beim Flip
    `🔲 M4 → ✅ M4` die historische Out-of-Scope-Verzicht-
    Fallback-Klausel ersatzlos entfernt. Faktisch korrekt
    (Adapter geliefert), aber Audit-Trail-Verlust. **Fix:**
    Fulfillment-Note "**Erfuellung ueber Pfad A** (Adapter
    geliefert); historische Akzeptanz erlaubte alternativ
    dokumentierten Out-of-Scope-Verzicht" an beide Cluster-
    Zeilen angehaengt. Audit-Trail-Reader sieht jetzt
    beide ursprueglichen Compliance-Pfade.

---

## Folge auf andere Welle-6a-Decisions

- **ADR 0024 §4.5 OTel-Span-Wrap** bleibt unveraendert.
  Die F2/F10-Spec-Schaerfung (`reference` optional;
  `latency_ms` Event-encoded) ist `architecture.md §8.2`-
  Aktualisierung, nicht ADR-Status-Wechsel. Welle-7-Closure
  kann ADR 0024 mit der konkreten Wrap-Implementation
  zusammenfuehren.

- **Welle-1-§7-Folge-Pflicht** (`AC-ADAPTER-LIGHTWEIGHT`-
  Planted-Violator-Test) bleibt erfuellt durch die
  produktiv-arbeitenden 6 Tests in
  `tests/unit/test_arch_check_planted_violator.py`
  (3 positive: protocol_*/persistence_*/driving_; 2
  negative: outside-adapter-boundary direkt gegen
  `_is_adapter_lightweight_path` + unrelated-driven-bucket;
  1 Schwellwert: low-complexity-darf-nicht-triggern).

- **Trigger 006 (`strict_bytes`)** bleibt aktiv. Slice 034
  beruehrt `pyproject.toml`/`strict_bytes` NICHT — der Fix
  von F8 (typed `Callable` statt `object`) erweitert die
  static-type-Safety im Adapter-Helper-Code, ist aber kein
  bytes/str-Boundary-Issue.

- **Welle-6b-Vorlauf** wurde um F13
  (`AC-ADAPTER-LIGHTWEIGHT`-Coverage-Schaerfung fuer
  `_protocol_*.py`-Cross-Adapter-Helper) ergaenzt.

---

## Verifikation

- `make test-unit`: **1566 Tests gruen** (Welle-6a-Endstand
  1564 + 6 neue Tests aus Slice 034: 2× F1-Record-Event-
  raises + 2× F3-Operation-spezifischer-Catch + 2× F2-
  reference-Attribut. F4-Test-Umbau ohne Count-Aenderung).
- `make arch-check`: **alle Contracts KEPT**; kein neuer
  Contract aus Slice 034.
- `make typecheck`: gruen unter mypy --strict mit
  `strict_bytes = true`. Kein neuer `# type: ignore` im
  Wrapper-Modul (F8 hat den Hot-Path-`type: ignore[
  operator]` eliminiert).
- `make gates`: **alle 9 A-1-Gates gruen** ohne
  `CRITICAL_COV_TARGETS`-Override.
- `make docs-check`: cache-frei gruen.

## Anti-Scope (Slice 034 NICHT)

- **Kein neuer arch_check-Contract** (F13 ist Welle-6b-
  Vorlauf-Item, nicht Slice-034-Lieferung).
- **Keine Adapter-Code-Diffs** in den 5 `protocol_*/`-
  Paketen (Welle-6a-Anti-Scope bleibt — der Wrapper ist
  Cross-Adapter-Helper, die konkreten Adapter sehen den
  Slice nicht).
- **Keine neuen `noqa`-Marker** — Slice 027 Compliance.
- **Keine Welle-5b-Erbschaft-Items** (GPL-Boundary-
  Hardening, IedServer-Smoke-Reaktivierung) — alle in
  Welle 6b geparkt.
- **Keine ADR-Status-Wechsel** (ADR 0024 bleibt
  `Accepted`; ADR 0035 bleibt `Provisional`).
- **Kein TaskCreate-Tooling** als Slice-Inhalt.

---

## Slice-Schluss-Hash

`<wird im Commit eingetragen>` — `feat(welle-6a): Slice
034 — OTel-Span-Wrap + Planted-Violator Review-Folge
(15 Findings)`.
