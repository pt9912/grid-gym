# In Progress

Lebende Roadmap und aktive Slice-Plaene, an denen gearbeitet wird.

## Bestand

| Datei                     | Gegenstand                                                                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`roadmap.md`](roadmap.md)              | Meilenstein-Uebersicht (M1..Mx) mit Lastenheft-/Architektur-Bezuegen, Abnahmekriterien und Status.                                                  |
| [`M4-protocol-adapters.md`](M4-protocol-adapters.md) | M4-Slice-Plan (MQTT/Modbus/OPC-UA/DNP3/IEC; Vorbelegung Welle 0..7 + Out-of-Scope + Risiken + Verifikationspfad; Pattern analog `done/M3-faults-agents-observability.md`). |
| [`M4-welle-5a.md`](M4-welle-5a.md) | Welle-5a-Slice-Doc (DNP3-Adapter-Spike) — `Done` 2026-05-31; bleibt in `in-progress/` bis Self-Close-Move nach `done/` (Pattern Welle 1..4).                                  |

M3 ist mit Welle 7 vollstaendig abgeschlossen
(2026-05-25, siehe
[`../done/M3-results.md`](../done/M3-results.md)). **M4** ist
mit Welle 0 am 2026-05-26 eroeffnet; Welle 1
(`DeviceProtocolPort`-Foundation), Welle 2 (MQTT-Adapter),
Welle 3 (Modbus-TCP-Adapter), Welle 4 (OPC-UA-Adapter,
**erster rein-async-Stack** im Repo) und Welle 5a (DNP3-
Adapter-Spike, **zwei-Library-Setup** `nfm-dnp3` +
`dnp3-outstation`) sind abgeschlossen; Welle 3 ist per
Doku-Review-Folge 2026-05-31 (Slice 031) nach `done/`
gewandert, Welle 4 mit Slice-032 + Nachzug-Commit
`1c2dfa3` und Self-Close-Move `3bc015b`, Welle 5a mit
ADR 0034 `Provisional` (`Proposed` per `b0fea7e` →
`Provisional` per C3) und C2-Merge `224b370`. Welle-0-,
Welle-1-, Welle-2-, Welle-3- und Welle-4-Docs sind alle
nach
[`../done/M4-welle-0.md`](../done/M4-welle-0.md),
[`../done/M4-welle-1.md`](../done/M4-welle-1.md),
[`../done/M4-welle-2.md`](../done/M4-welle-2.md),
[`../done/M4-welle-3.md`](../done/M4-welle-3.md) bzw.
[`../done/M4-welle-4.md`](../done/M4-welle-4.md) gewandert
(Self-Close-Moves `556ae9f` / `81b5cba` / `0d6ad6c` /
`506c8ca` / `3bc015b`); der Welle-5a-Doc
[`M4-welle-5a.md`](M4-welle-5a.md) bleibt vorerst in
`in-progress/`, der Self-Close-Move folgt im naechsten
Pre-C0-Sync vor Welle 5b. Der kanonische M4-Slice-Plan
[`M4-protocol-adapters.md`](M4-protocol-adapters.md) bleibt
in `in-progress/` bis M4-Welle-7-Closure. **Naechster
aktiver Schritt:** M4-Welle-5b (IEC-61850-Spike —
`libiec61850`-Python-Binding-Recherche steht noch aus;
Sub-Slicing-Entscheidung per `M4-protocol-adapters.md`-§3
begruendet durch Variante C „beide Spikes" und unabhaengige
Library-Pfade).
