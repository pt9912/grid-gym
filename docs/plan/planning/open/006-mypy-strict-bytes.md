# 006 — `--strict-bytes`-Modus aktivieren

**Status:** Open — Trigger-Watch (M3-Welle-7-Closure-Decision
2026-05-25: **verschoben auf M4-Vorlauf** mit geschaerftem
Aktivierungs-Kriterium; siehe §Decision unten).
**Datum:** 2026-05-15 (eroeffnet), 2026-05-25 (Welle-7-Closure-
Decision).
**Quelle:** [`ADR 0005`](../../adr/0005-type-check-gate.md) §6.

---

## Trigger

`GG-DATA-005` verlangt UTF-8-Bytes als Vertragsschnittstelle der
kanonischen Serialisierung (A-2). ADR 0005 nennt:

> Aktivierung des `--strict-bytes`-Modus (bei `bytes`/`str`-Trenn-
> scharfe) sobald das Domain-Modell konsolidiert ist
> (`GG-DATA-005` UTF-8-Bytes-Vertrag).

## Erwartete Lieferung

- `[tool.mypy]`-Erweiterung um `strict_bytes = true` (oder
  Eintrag in `enable_error_code`, je nach mypy-Version).
- Pruefung, dass kein `bytes ↔ str`-Implicit-Coercion im Kern
  passiert (Persistenz, Replay-Diff, WebSocket-Frame).
- Anpassung der Test-Suite, falls Tests bisher `bytes` und `str`
  vermischt haben.

## Decision (M3-Welle-7-Closure, 2026-05-25)

**Verschieben.** Aktivierung in M3-Welle 7 wuerde keinen Test
fixen und keine konkrete Drift aufdecken, weil das Repo aktuell
keinen produktiven `bytes`/`bytearray`-Pfad im Domain-Code hat.

**Befunde:**

- `src/grid_gym/hexagon/core/serialization/snapshot_codec.py:134`
  verbietet `bytes` und `bytearray` als Snapshot-Wert-Typen
  explizit; Verstoesse werfen `WrongTypeError`. Spiegelt das
  Verbot in `canonical_json` (1:1-Vertragsspiegel).
- `canonical_json` liefert `str` (JSON-String), kein `bytes`.
  UTF-8-Encoding passiert in den Konsumenten ueber Stdlib-
  Standardpfade (`str.encode("utf-8")`), nicht im Domain-Code.
- OTLP-Adapter aus M3-Welle 6
  (`src/grid_gym/adapters/driven/telemetry_otlp/`) nutzen
  Protocol-Buffer-Serialisierung der OTel-SDK — Library-interna,
  kein eigener `bytes`-Pfad.
- `grep -rn "bytearray\|bytes(" src/ tools/` (Stand 2026-05-25):
  ein Treffer, der Verbots-Kommentar in `snapshot_codec.py`.

`--strict-bytes` (mypy `disable_bytearray_promotion` / `disable_
memoryview_promotion`) bringt erst dann Mehrwert, wenn echter
Binaer-Code im Repo entsteht.

## Aktivierungs-Kriterium (geschaerft, 2026-05-25)

Aktivierung sobald **eines** der folgenden Ereignisse eintritt:

- **M4-Protokolladapter** (MQTT/Modbus/OPC-UA/DNP3/IEC 61850) bringt
  einen ersten produktiven `bytes`-Pfad. Konkrete Wahrscheinlichkeits-
  Schwerpunkte: MQTT-Frames (`paho`-mqtt `bytes`-Payload), Modbus-
  Telegramme (`pymodbus`-`bytes`-Buffer), OPC-UA-`ByteString`.
- **Snapshot-v2→v3-Lese-Migrations-Pfad** (M6 `GG-PERSIST-*`-Slice)
  liest historische Snapshots aus rohem `bytes`-Storage.
- **Trace-/Span-Roundtrip-Test** (M3-Welle-7-Folge oder spaeter)
  serialisiert OTLP-Records lokal zu `bytes` und validiert das
  Wire-Format gegen die OTel-Spec.

Bei Aktivierung wandert Trigger 006 nach `next/` mit einem
Slice-Plan, der die drei Erwartete-Lieferung-Items oben (mypy-
Config, Kern-Pruefung, Test-Suite-Anpassung) konkret schedulet.

## Wandert nach

- `next/`, sobald eines der drei Aktivierungs-Kriterien oben
  eintritt; mit konkretem Slice-Plan,
- `in-progress/`, wenn Konfigurations-Slice geplant ist,
- `done/`, wenn `[tool.mypy]` `strict_bytes = true` aktiv ist und
  `make gates` ohne Override gruen bleibt.
