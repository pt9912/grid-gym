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
abgeschlossen — Welle-0-Doc und Welle-1-Doc sind nach
[`../done/M4-welle-0.md`](../done/M4-welle-0.md) bzw.
[`../done/M4-welle-1.md`](../done/M4-welle-1.md) gewandert
(Self-Close-Moves `556ae9f` bzw. `81b5cba`). Der kanonische
M4-Slice-Plan
[`M4-protocol-adapters.md`](M4-protocol-adapters.md) bleibt
in `in-progress/` bis M4-Welle-7-Closure. **Naechster aktiver
Schritt:** M4-Welle-2 (MQTT-Adapter — `paho-mqtt`-Wrapper +
Topic-Schema + Mosquitto-Sibling-Smoke).
