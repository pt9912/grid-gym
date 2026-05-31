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
(`DeviceProtocolPort`-Foundation), Welle 2 (MQTT-Adapter)
und Welle 3 (Modbus-TCP-Adapter) sind am 2026-05-30
abgeschlossen; Welle 3 ist per Doku-Review-Folge
2026-05-31 (Slice 031) nach `done/` gewandert. Welle 4
(OPC-UA-Adapter, **erster rein-async-Stack** im Repo)
ist am 2026-05-31 abgeschlossen und bleibt bis zum
M4-Welle-5-Pre-C0-Move in `in-progress/`. Welle-0-,
Welle-1-, Welle-2- und Welle-3-Docs sind bereits nach
[`../done/M4-welle-0.md`](../done/M4-welle-0.md),
[`../done/M4-welle-1.md`](../done/M4-welle-1.md),
[`../done/M4-welle-2.md`](../done/M4-welle-2.md) bzw.
[`../done/M4-welle-3.md`](../done/M4-welle-3.md) gewandert
(Self-Close-Moves `556ae9f` / `81b5cba` / `0d6ad6c` /
`506c8ca`). Der kanonische M4-Slice-Plan
[`M4-protocol-adapters.md`](M4-protocol-adapters.md) bleibt
in `in-progress/` bis M4-Welle-7-Closure. **Naechster
aktiver Schritt:** M4-Welle-5 (DNP3/IEC-Disposition —
Variante A Verzicht-Default oder Variante B Mini-Spike als
Opt-In; informiert durch asyncua-Erfahrung aus Welle 4).
