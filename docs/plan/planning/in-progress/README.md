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
(`DeviceProtocolPort`-Foundation), Welle 2 (MQTT-Adapter),
Welle 3 (Modbus-TCP-Adapter), Welle 4 (OPC-UA-Adapter,
**erster rein-async-Stack** im Repo) und Welle 5a (DNP3-
Adapter-Spike, **zwei-Library-Setup** `nfm-dnp3` +
`dnp3-outstation`) sind abgeschlossen; Welle 3 ist per
Doku-Review-Folge 2026-05-31 (Slice 031) nach `done/`
gewandert, Welle 4 mit Slice-032 + Nachzug-Commit
`1c2dfa3` und Self-Close-Move `3bc015b`, Welle 5a mit
ADR 0034 `Provisional` (`Proposed` per `b0fea7e` →
`Provisional` per C3 `6903a08`) und C2-Merge `224b370`.
Welle-0-, Welle-1-, Welle-2-, Welle-3-, Welle-4- und
Welle-5a-Docs sind alle nach
[`../done/M4-welle-0.md`](../done/M4-welle-0.md),
[`../done/M4-welle-1.md`](../done/M4-welle-1.md),
[`../done/M4-welle-2.md`](../done/M4-welle-2.md),
[`../done/M4-welle-3.md`](../done/M4-welle-3.md),
[`../done/M4-welle-4.md`](../done/M4-welle-4.md) bzw.
[`../done/M4-welle-5a.md`](../done/M4-welle-5a.md) gewandert
(Self-Close-Moves `556ae9f` / `81b5cba` / `0d6ad6c` /
`506c8ca` / `3bc015b` / `9fea2be`). Der kanonische
M4-Slice-Plan [`M4-protocol-adapters.md`](M4-protocol-adapters.md)
bleibt in `in-progress/` bis M4-Welle-7-Closure. **Naechster
aktiver Schritt:** M4-Welle-5b (IEC-61850-Spike — Library-
Recherche 2026-06-01 abgeschlossen: produktive Library
`pyiec61850-ng>=1.6,<2.0` (PyPI, manylinux1+Win-Wheels,
**GPLv3**, Beta, SWIG-Bindings zu libiec61850 1.6), eine
Library liefert Client (`MMSClient`) **und** in-process-
Server (`IedServer` mit Context-Manager); kein zweites
Test-Sibling-Library noetig (Pattern analog Welle-3-Modbus
mit pymodbus, nicht Welle-5a-Zwei-Library-Setup). Lizenz-
Boundary-Decision: `src/grid_gym/adapters/driven/protocol_iec61850/*`
+ zugehoerige Tests werden GPLv3-isoliert via SPDX-Header,
Rest grid-gym bleibt MIT (Dual-License-Policy, neu fuer
grid-gym).
