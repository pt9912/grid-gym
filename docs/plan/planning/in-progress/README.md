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
**erster rein-async-Stack** im Repo), Welle 5a (DNP3-
Adapter-Spike, **zwei-Library-Setup** `nfm-dnp3` +
`dnp3-outstation`) und Welle 5b (IEC-61850-Adapter-Spike,
**erster GPL-isolierter Sub-Module-Praezedenzfall** im Repo
+ **erste SWIG-/C-native Library**) sind abgeschlossen;
Welle 5b mit ADR 0035 `Provisional` (`Proposed` per
`88c1a33` → C1-Review-Folge `da8aed9` → `Provisional` per
C3 dieser Commit) und C2-Merge `944bca5`. 2c-Mock-only-
Fallback aktiviert (Probe-Run auf Python 3.12 lief, aber
grid-gym-Docker-Stack Python 3.14 segfaultet im
`_pyiec61850.so`-SWIG-Layer; Welle-6-Schaerfungspfade
dokumentiert; Slice 033 `7e0c91b` als C2-Review-Folge hat 15
Findings 10 HIGH + 5 MEDIUM ohne ADR-Status-Aenderung
adressiert). Welle-0-, Welle-1-, Welle-2-, Welle-3-, Welle-4-,
Welle-5a- und Welle-5b-Docs sind alle nach
[`../done/M4-welle-0.md`](../done/M4-welle-0.md),
[`../done/M4-welle-1.md`](../done/M4-welle-1.md),
[`../done/M4-welle-2.md`](../done/M4-welle-2.md),
[`../done/M4-welle-3.md`](../done/M4-welle-3.md),
[`../done/M4-welle-4.md`](../done/M4-welle-4.md),
[`../done/M4-welle-5a.md`](../done/M4-welle-5a.md) bzw.
[`../done/M4-welle-5b.md`](../done/M4-welle-5b.md) gewandert
(Self-Close-Moves `556ae9f` / `81b5cba` / `0d6ad6c` /
`506c8ca` / `3bc015b` / `9fea2be` / `30860ed`). Der kanonische M4-Slice-Plan
[`M4-protocol-adapters.md`](M4-protocol-adapters.md) bleibt
in `in-progress/` bis M4-Welle-7-Closure. **Naechster
aktiver Schritt:** M4-Welle-6 (Cross-Adapter-Hardening —
OTel-Span-Wrap der 5 `protocol_*`-Adapter, Adapter-Profil-
Index unter `spec/protocol_profiles/`,
`AC-ADAPTER-LIGHTWEIGHT`-Planted-Violator-Property-Test als
Welle-1-§7-Folge-Pflicht-Closure; **plus Welle-5b-
Schaerfungs-Erbschaft**: SPDX-Header-Konsistenz-Check in
`tools/check_refs.py`, CONTRIBUTING.md-Sync mit GPL-
Boundary-Policy, `arch_check.py`-Contract gegen GPL-
Boundary-Crossing, IEC-61850-IedServer-Smoke-Reaktivierung
unter Python 3.12 oder via Library-Upgrade).
