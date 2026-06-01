# In Progress

Lebende Roadmap und aktive Slice-Plaene, an denen gearbeitet wird.

## Bestand

| Datei                     | Gegenstand                                                                                                                                          |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| [`roadmap.md`](roadmap.md)              | Meilenstein-Uebersicht (M1..Mx) mit Lastenheft-/Architektur-Bezuegen, Abnahmekriterien und Status.                                                  |
| [`M4-protocol-adapters.md`](M4-protocol-adapters.md) | M4-Slice-Plan (MQTT/Modbus/OPC-UA/DNP3/IEC; Vorbelegung Welle 0..7 + Out-of-Scope + Risiken + Verifikationspfad; Pattern analog `done/M3-faults-agents-observability.md`). |
| [`M4-welle-7.md`](M4-welle-7.md) | Welle-7-Slice-Doc (M4-Closure analog M3-Welle-7) — `In Progress` 2026-06-01; bleibt in `in-progress/` bis Self-Close-Move nach `done/` als M5-Welle-0-Pre-C0. |

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
abgeschlossen 2026-06-01** mit C0 `9776dd9` + C1 `9312239`
+ C2 `9d3912f` + Pre-C3 `81140e2` + C3 `0a5e895` + C4
`69b37f1` + **Slice 034 Review-Folge `bde8fdb`** (1 HIGH
+ 6 MEDIUM + 4 LOW-MEDIUM + 4 LOW Findings adressiert,
F13 als Welle-6b-Vorlauf-Item dokumentiert) + Hash-Sync
`b6a778d` + **Self-Close-Move `d1cb65d`** (rename-only)
+ Pre-C0-Sync (dieser Commit). 1537 → 1566 Unit-Tests
(+29 mit 19 OTel-Span-Wrap + 6 AC-ADAPTER-LIGHTWEIGHT-
Planted-Violator + 4 Slice-034-Adapter-Tests).
Welle-0..5b- und Welle-6a-Docs sind alle nach
[`../done/M4-welle-0.md`](../done/M4-welle-0.md),
[`../done/M4-welle-1.md`](../done/M4-welle-1.md),
[`../done/M4-welle-2.md`](../done/M4-welle-2.md),
[`../done/M4-welle-3.md`](../done/M4-welle-3.md),
[`../done/M4-welle-4.md`](../done/M4-welle-4.md),
[`../done/M4-welle-5a.md`](../done/M4-welle-5a.md),
[`../done/M4-welle-5b.md`](../done/M4-welle-5b.md),
[`../done/M4-welle-6a.md`](../done/M4-welle-6a.md) bzw.
[`../done/M4-welle-6b.md`](../done/M4-welle-6b.md)
gewandert (Self-Close-Moves `556ae9f` / `81b5cba` /
`0d6ad6c` / `506c8ca` / `3bc015b` / `9fea2be` / `30860ed`
/ `d1cb65d` / `bf23458`). Der kanonische M4-Slice-Plan
[`M4-protocol-adapters.md`](M4-protocol-adapters.md)
bleibt in `in-progress/` bis M4-Welle-7-Closure.
**Welle 6b (IEC-61850-Lizenz-und-Smoke-Hardening, Welle-5b-
Erbschaft + Slice-034-F13-Vorlauf-Item) abgeschlossen
2026-06-01** mit C0 `14d1bcb` (Slice-Doc) + C1 `8947c62`
(SPDX-Header-Lint via NEU `tools/check_spdx.py` + 10.
A-1-Gate `make spdx-check`) + C2 `9e2bf39` (NEU
`AC-IEC61850-GPL-BOUNDARY` arch_check-Contract, 19 → 20
KEPT; AST-Import-Scan; 8 Property-Tests) + C3 `2539574`
(IedServer-Smoke-Probe Pfad C aktiv mit Trigger 009 nach
PyPI-Pfad-A-Befund: Library-Stand identisch zu Welle 5b,
kein cp314-Manylinux-Wheel; plus Slice-034-F13-Coverage-
Schaerfung `_is_adapter_lightweight_path` erweitert um
flat-file `_protocol_*.py`-Cross-Adapter-Helper) + C4
`314ccae` (Status/DoD-Sync + NEU `CONTRIBUTING.md` mit
Dual-License-Policy + Top-Level-Doku-Sync) + **Self-Close-
Move `bf23458`** als M4-Welle-7-Pre-C0 (rename-only) +
Pre-C0-Sync (dieser Commit). 1566 → 1584 Unit-Tests (+18
unique: 9 SPDX-Lint + 8 GPL-Boundary-Property + 1 F13-
Cross-Adapter-Helper-Positiv). 10/10 A-1-Gates gruen (10.
NEU `spdx-check`); 20/20 Contracts KEPT (14. NEU
`AC-IEC61850-GPL-BOUNDARY`).

**Aktive Welle:** M4-Welle-7 (M4-Closure) eroeffnet
2026-06-01 mit C0 (dieser Commit; Slice-Doc-Anlage
[`M4-welle-7.md`](M4-welle-7.md)). Geplante Lieferung in
4 Commits + Self-Close-Move-Folge: C1 ADR-Status-Wechsel
0030..0035 von `Provisional` auf `Accepted`, C2 NEU
`done/M4-results.md` mit Welle-Tabelle/Abnahme-Belegen/
Pro-Welle-Reviews/S-1..S-6-Sweep/Wandert-Nach + ADR-0028-
Linkpflege, C3 M4-Closure-Top-Level-Sync (Roadmap-DoD,
M4 auf `Done`, M5 als naechster aktiver Slice, READMEs),
C4 `make fullbuild` cache-frei gruen als Welle-7-Closure-
Gate + Self-Close-Move `M4-protocol-adapters.md` nach
`done/`.
