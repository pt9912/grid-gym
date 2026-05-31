# In Progress

Lebende Roadmap und aktive Slice-Plaene, an denen gearbeitet wird.

## Bestand

| Datei                     | Gegenstand                                                                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`roadmap.md`](roadmap.md)              | Meilenstein-Uebersicht (M1..Mx) mit Lastenheft-/Architektur-Bezuegen, Abnahmekriterien und Status.                                                  |
| [`M4-protocol-adapters.md`](M4-protocol-adapters.md) | M4-Slice-Plan (MQTT/Modbus/OPC-UA/DNP3/IEC; Vorbelegung Welle 0..7 + Out-of-Scope + Risiken + Verifikationspfad; Pattern analog `done/M3-faults-agents-observability.md`). |

M3 ist mit Welle 7 vollstaendig abgeschlossen
(2026-05-25, siehe
[`../done/M3-results.md`](../done/M3-results.md)). **M4** ist
mit Welle 0 am 2026-05-26 eroeffnet; Welle 1
(`DeviceProtocolPort`-Foundation) ist am 2026-05-30
abgeschlossen; Welle 2 (MQTT-Adapter) ist ebenfalls am
2026-05-30 abgeschlossen; Welle 3 (Modbus-TCP-Adapter)
ist am 2026-05-30 abgeschlossen und per Doku-Review-Folge
2026-05-31 nach `done/` gewandert — Welle-0-, Welle-1-,
Welle-2- und Welle-3-
Doc sind nach
[`../done/M4-welle-0.md`](../done/M4-welle-0.md),
[`../done/M4-welle-1.md`](../done/M4-welle-1.md) bzw.
[`../done/M4-welle-2.md`](../done/M4-welle-2.md) bzw.
[`../done/M4-welle-3.md`](../done/M4-welle-3.md) gewandert
(Self-Close-Moves `556ae9f` / `81b5cba` / `0d6ad6c` plus
Doku-Review-Folge fuer Welle 3). Der
kanonische M4-Slice-Plan
[`M4-protocol-adapters.md`](M4-protocol-adapters.md) bleibt
in `in-progress/` bis M4-Welle-7-Closure. **Naechster aktiver
Schritt:** M4-Welle-4 (OPC-UA-Adapter — `asyncua`-Wrapper
und async→sync-Marshal-Pattern).
