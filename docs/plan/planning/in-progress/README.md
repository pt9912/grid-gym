# In Progress

Lebende Roadmap und aktive Slice-Plaene, an denen gearbeitet wird.

## Bestand

| Datei                     | Gegenstand                                                                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`roadmap.md`](roadmap.md)              | Meilenstein-Uebersicht (M1..Mx) mit Lastenheft-/Architektur-Bezuegen, Abnahmekriterien und Status.                                                  |
| [`M4-protocol-adapters.md`](M4-protocol-adapters.md) | M4-Slice-Plan (MQTT/Modbus/OPC-UA/DNP3/IEC; Vorbelegung Welle 0..7 + Out-of-Scope + Risiken + Verifikationspfad; Pattern analog `done/M3-faults-agents-observability.md`). |
| [`M4-welle-6a.md`](M4-welle-6a.md) | Welle-6a-Slice-Doc (Cross-Adapter-Hardening Mainstream) — `Done` 2026-06-01; bleibt in `in-progress/` bis Self-Close-Move nach `done/` als M4-Welle-6b-Pre-C0 (Pattern Welle 1..5b). |

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
C3 `ca96bca`) und C2-Merge `944bca5` + Slice-033-Review-
Folge `7e0c91b` (15 Findings 10 HIGH + 5 MEDIUM ohne ADR-
Status-Aenderung adressiert). 2c-Mock-only-Fallback fuer
IEC-Integration-Smoke bleibt aktiv (Welle-6b-Reaktivierung
steht). **Welle 6a (Cross-Adapter-Hardening Mainstream)
abgeschlossen 2026-06-01** mit C0 `9776dd9` (Slice-Doc) +
C1 `9312239` (Adapter-Profil-Index unter
`spec/protocol_profiles.md` + Lastenheft-§16-`✅ M4` x 5
+ Architektur-§8.2-OTel-Wrap-Pattern-Forward-Pointer) +
C2 `9d3912f` (OTel-Span-Wrap fuer alle 5 protocol_*-
Adapter via `OtelSpanWrappedDeviceProtocolPort`-
Composition-Wrapper) + Pre-C3 `81140e2` (git mv
trigger-006 → done/) + C3 `0a5e895` (Planted-Violator-
Test als Welle-1-§7-Folge-Pflicht-Closure +
`strict_bytes = true` als Trigger-006-Closure +
compose.yml-Header-Konsolidierung + Trigger-004-Defer)
+ C4 (dieser Commit). 1537 → 1564 Unit-Tests (+27 mit
13 OTel-Span-Wrap + 7 AC-ADAPTER-LIGHTWEIGHT-Planted-
Violator + 7 Slice-033-Review-Folge-Updates).
Welle-0-, Welle-1-, Welle-2-, Welle-3-, Welle-4-,
Welle-5a- und Welle-5b-Docs sind alle nach
[`../done/M4-welle-0.md`](../done/M4-welle-0.md),
[`../done/M4-welle-1.md`](../done/M4-welle-1.md),
[`../done/M4-welle-2.md`](../done/M4-welle-2.md),
[`../done/M4-welle-3.md`](../done/M4-welle-3.md),
[`../done/M4-welle-4.md`](../done/M4-welle-4.md),
[`../done/M4-welle-5a.md`](../done/M4-welle-5a.md) bzw.
[`../done/M4-welle-5b.md`](../done/M4-welle-5b.md) gewandert
(Self-Close-Moves `556ae9f` / `81b5cba` / `0d6ad6c` /
`506c8ca` / `3bc015b` / `9fea2be` / `30860ed`); der Welle-
6a-Doc [`M4-welle-6a.md`](M4-welle-6a.md) bleibt vorerst
in `in-progress/`, der Self-Close-Move folgt im Pre-C0-
Sync vor Welle 6b. Der kanonische M4-Slice-Plan
[`M4-protocol-adapters.md`](M4-protocol-adapters.md)
bleibt in `in-progress/` bis M4-Welle-7-Closure.
**Naechster aktiver Schritt:** M4-Welle-6b (IEC-61850-
Lizenz-und-Smoke-Hardening, Welle-5b-Erbschaft) — SPDX-
Header-Konsistenz-Check in `tools/check_refs.py`, neuer
`arch_check.py`-Contract `AC-IEC61850-GPL-BOUNDARY`
(19/19 → 20/20 Contracts), CONTRIBUTING.md-Sync mit
GPL-Boundary-Policy, IedServer-Smoke-Reaktivierungs-
Probe (3 Pfade: Library-Upgrade / Dockerfile-Python-
Downgrade / Mock-only-Defer).
