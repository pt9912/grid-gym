# 006 — `--strict-bytes`-Modus aktivieren

**Status:** Done — Aktivierung produktiv mit
M4-Welle-6a-C3 2026-06-01. `[tool.mypy] strict_bytes = true`
in `pyproject.toml` aktiv; `make typecheck` cache-frei
gruen ohne neue ignores. Pattern analog Slice 027 / Slice
028 (Trigger-Closure als done/-Move bei Aktivierung).
**Datum:** 2026-05-15 (eroeffnet), 2026-05-25 (Welle-7-Closure-
Decision), 2026-05-30 (M4-Welle-3-C3-Re-Eval), 2026-06-01
(M4-Welle-6a-C3 Aktivierung + Self-Close-Move).
**Quelle:** [`ADR 0005`](../../adr/0005-type-check-gate.md) §6.

## Closure-Notiz (M4-Welle-6a-C3, 2026-06-01)

Die M4-Welle-3-C3-Re-Eval hat das Aktivierungs-Kriterium
positiv bestaetigt (Modbus-Codec `bytes`-Pfade explizit-
typed; keine impliziten `bytes ↔ str`-Coercions im Repo).
M4-Welle-6a-C3 zieht die Aktivierung produktiv:

- `[tool.mypy] strict_bytes = true` im
  `pyproject.toml`-Block ergaenzt (zwischen
  `extra_checks = true` und `enable_error_code = [...]`).
- `make typecheck` cache-frei gruen — kein Repo-Sweep-
  Folge-Fix notwendig (Welle-3-Re-Eval hatte das schon
  vorbereitet, Modbus-Codec ist explizit).
- Keine neuen `# type: ignore`-Marker (Welle-1-Pflicht:
  Slice 027 / `noqa-gate` greift unveraendert).
- Diese Datei wandert von `open/` nach `done/`
  (`git mv`-Pattern analog Slice 028).

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

## M4-Welle-3-Re-Eval (2026-05-30)

**Befund (positiv):** Aktivierungs-Kriterium 1 (M4-
Protokolladapter bringt einen ersten produktiven `bytes`-
Pfad) ist mit M4-Welle-3-C2 `d721982` real eingetroffen:
`src/grid_gym/adapters/driven/protocol_modbus/_codec.py`
ist der erste produktive `bytes`/`int`/`float`-Konvertierungs-
Pfad im Repo (`struct.pack`/`struct.unpack` mit
`_registers_to_bytes`/`_bytes_to_registers`-Helpern).

**`# type: ignore`-Zaehlung im Modbus-Modul** (Stand
`d721982` + C3):

| Datei                                               | `# type: ignore` |
| --------------------------------------------------- | ---------------- |
| `protocol_modbus/__init__.py`                       | 0                |
| `protocol_modbus/_config.py`                        | 0                |
| `protocol_modbus/_codec.py`                         | 0                |
| `protocol_modbus/_port.py`                          | 2                |
| `protocol_modbus/_errors.py`                        | 0                |

Die zwei `# type: ignore[no-untyped-call]` in
`_port.py:128/148` decken pymodbus-API-Aufrufe
(`client.connect()`/`client.close()`) ab, fuer die
pymodbus 3.x keine Type-Stubs ausliefert. **Sie sind
nicht bytes-bezogen** — `--strict-bytes` aendert ihren
Status nicht.

**Re-Eval-Lauf (cache-frei, 2026-05-30):**

```bash
docker run --rm --user "$(id -u):$(id -g)" \
  -e UV_CACHE_DIR=/tmp/uv-cache \
  -e UV_PROJECT_ENVIRONMENT=/tmp/uv-venv \
  -v "$(pwd)":/src -w /src grid-gym-source:latest \
  uv run mypy --config-file pyproject.toml --strict-bytes
```

Ausgabe: `Success: no issues found in 116 source files`.

**Folgerung:** `--strict-bytes` bringt am Modbus-Code
**null zusaetzliche Findings** ueber das `mypy --strict`-
Baseline hinaus. `_codec.py` benutzt `bytes` strikt
(kein `bytearray`/`memoryview`-Drift; `bytes(out)`-Konvertierung
am Ende von `_registers_to_bytes` ist explizit). Damit ist
das Repo `--strict-bytes`-aktivierungs-faehig **ohne neue
Ignores im Modbus-Code**.

**Entscheidung:** Trigger 006 ist **aktivierungs-reif**.
Die Aktivierung selbst bleibt ein separater Folge-Slice
(`strict_bytes = true` plus Repo-Sweep); bis dieser Slice
gestartet wird, bleibt diese Trigger-Notiz in `open/`.
M4-Welle-3-C3 selbst aktiviert `--strict-bytes` noch
**nicht** — der Welle-3-Scope ist Modbus-Adapter, nicht
mypy-Config (vgl.
`docs/plan/planning/done/M4-welle-3.md` §7
Risiko-Bullet „Trigger 006 sprengt Welle-3-Scope").

## Wandert nach

- `next/`: wenn der Aktivierungs-Slice geplant wird;
  konkreter Slice-Plan beschreibt die drei Erwartete-
  Lieferung-Items oben (mypy-Config-Erweiterung, Kern-
  Pruefung, Test-Suite-Anpassung) plus den Aktivierungs-
  Commit.
- `in-progress/`, wenn der `next/`-Slice-Plan in Arbeit
  geht.
- `done/`, wenn `[tool.mypy]` `strict_bytes = true` aktiv
  ist und `make gates` ohne Override gruen bleibt.
