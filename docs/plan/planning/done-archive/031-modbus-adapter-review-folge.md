# 031 — Modbus-Adapter Review-Folge

**Status:** Done — umgesetzt nach M4-Welle-3-Doku-Review
2026-05-31. Dieser Slice behebt die in der Welle-3-Abnahme
gefundenen Modbus-Adapter-Luecken, ohne den Welle-3-Scope
rueckwirkend umzudefinieren.
**Quelle:** Review von
[`M4-welle-3.md`](M4-welle-3.md) gegen Code, Tests und Doku.

---

## Lieferung

1. **FC06-Guard fuer Multi-Register-Datatypes**
   - `function_code=6` ist nur noch fuer Datatypes mit genau
     einem Register (`int16`, `uint16`) gueltig.
   - `int32`/`uint32`/`float32` mit FC06 werden in der
     Config-Validation fail-fast als typed
     `ModbusConfigFunctionCodeDatatypeMismatchError`
     abgelehnt.
   - Unit-Tests decken Ablehnung fuer Multi-Register-
     Datatypes und Akzeptanz fuer Single-Register-Datatypes.

2. **Read-/Write-Fehler-Taxonomie geschaerft**
   - `write()`-Fehler sind unter
     `DeviceProtocolPortWriteError` fangbar:
     `ModbusPortWriteAccessMismatchError`,
     `ModbusPortWriteNotStartedError`,
     `ModbusPortWriteFailedError` und
     `ModbusPortMissingCommandPayloadError`.
   - Alte Catch-All-Basisklassen
     `ModbusPortAccessMismatchError` und
     `ModbusPortNotStartedError` bleiben erhalten.
   - Codec-/Payload-Fehler aus `write()` werden am
     Adapter-Rand in `ModbusPortWriteFailedError`
     uebersetzt; Decode-Fehler aus `read()` analog in
     `ModbusPortReadFailedError`.

3. **Integration-Smoke bewusst eng gelassen**
   - Entscheidung: Option B. Der E2E-Smoke bleibt ein
     Default-Profil-Test fuer alle 5 Datatypes
     (`big_endian`, `word_swap=false`, Parent-`unit_id=1`).
   - Byte-Order-/Word-Swap-Matrix und Unit-ID-Override
     bleiben Unit-/Mock-Test-Abdeckung, nicht E2E-Smoke.
   - ADR 0032, M4-Welle-3-Doku, Roadmap und README-Tabelle
     sind entsprechend synchronisiert.

## Verifikation

- `make docs-check` — gruen (`all markdown link targets resolved`).
- `make format-check` — gruen (`235 files already formatted`).
- `make gates` — gruen; 1314 Unit-Tests, 95.45 %
  Gesamt-Coverage, 90.81 % Branch-Coverage, 95.35 %
  Critical-Coverage, keine bekannten Dependency-
  Vulnerabilities, keine `# noqa`-Marker.
- `make test-integration` — gruen; 23 Integration-Tests,
  inklusive
  `test_modbus_adapter_roundtrip_through_all_datatypes`.
- `docker run --rm grid-gym-typecheck:latest uv run mypy
  --config-file pyproject.toml --strict-bytes` — gruen;
  116 Source-Files.

## Wandert Nach

- `done/031-modbus-adapter-review-folge.md` (dieses Dokument).
