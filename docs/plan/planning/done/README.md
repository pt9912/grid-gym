# Abgeschlossene Plaene

Dieses Verzeichnis sammelt Closure-Notizen zu abgeschlossenen
Meilensteinen und Plaenen.

Eine Closure-Notiz fasst zusammen:

- was wurde geliefert (Code, Specs, ADRs),
- welche Lastenheft-IDs sind damit umgesetzt,
- was wurde explizit nicht erledigt und wandert weiter (`open/` oder
  Folge-Meilenstein),
- Verweis auf Tag/Release im CHANGELOG.

## Bestand

**Pflege-Regel (seit 2026-06-12):** `done/` haelt die
`M*-results.md`-Closure-Summaries (dauerhaft) plus die
Detail-Docs des jeweils AKTIVEN Meilensteins bis zu dessen
Closure. Mit der M(n)-Closure wandern die M(n)-Wellen-/Slice-/
Trigger-Detail-Docs nach
[`../done-archive/`](../done-archive/README.md) — ihr letzter
Umzug; danach sind sie eingefroren (`links`/`anchors` pruefen
das Archiv weiter, die `ids`-Linkpflicht endet dort).

| Datei                                          | Geschlossen | Gegenstand                                                                                          |
| ---------------------------------------------- | ----------- | --------------------------------------------------------------------------------------------------- |
| [`spike-0-results.md`](spike-0-results.md)                           | 2026-05-15  | Detail-Records zu Spike-0: Verstoss-Matrix (§3), Befunde (§4), Review-Trail (§6).                   |
| [`M1-tick-loop-results.md`](M1-tick-loop-results.md)                      | 2026-05-17  | M1-Abschluss-Ergebnisse: `make fullbuild` Gruen (mit `CRITICAL_COV_TARGETS`-Override) + Welle-7-Erbschaft. |
| [`M2-devices-results.md`](M2-devices-results.md)                        | 2026-05-20  | M2-Abschluss-Ergebnisse: `make fullbuild` cache-frei gruen **ohne** Override seit Welle 6c.         |
| [`M3-results.md`](M3-results.md)                                | 2026-05-25  | M3-Abschluss-Ergebnisse: Welle-Tabelle (Welle 0..7), Abnahme-Belege (`make fullbuild` cache-frei gruen ohne Override seit Welle-6-C2 `c61ab0d`; 1138 Unit-Tests + 21 Integration-Tests; 96 % Total-Coverage; 19 A-1-Contracts), Pro-Welle-Reviews, S-1..S-6-Verification, Welle-7-Erbschaft fuer M4+/M5+/M6+, M3-Wandert-Nach, Nicht-vollzogene Items. |
| [`M4-results.md`](M4-results.md)                                | 2026-06-01  | M4-Abschluss-Ergebnisse: Welle-Tabelle (Welle 0..7, 9 Code-Wellen 1..6b mit Sub-Slicing 5a/5b + 6a/6b), Abnahme-Belege (`make gates` cache-frei gruen ohne Override mit 10 A-1-Gates inkl. NEU `spdx-check`; 1584 Unit-Tests + 35 passed + 4 skipped Integration-Tests; 20 A-1-Contracts inkl. NEU `AC-IEC61850-GPL-BOUNDARY`; `make fullbuild`-krb5-CVE-Defer-Pfad pre-existing seit M3-Welle-7), Pro-Welle-Reviews (Slice 031/032/033/034 Review-Folgen), S-1..S-6-Verification, Welle-7-Erbschaft fuer M5+/M6+ (Trigger 009 IEC-61850-Smoke-Reaktivierung; Base-Image-Bump fuer krb5-CVE; OTel-Span-Wrap- + GPL-Boundary-Patterns als Wiederverwendung), M4-Wandert-Nach, Nicht-vollzogene Items. |
| [`M5-results.md`](M5-results.md)                                | 2026-06-04  | M5-Abschluss-Ergebnisse: Welle-Tabelle (Welle 0..7, 10 produktiv-Wellen 1..6c mit Sub-Slicing 4a/4b + 6a/6b/6c), Abnahme-Belege (`make gates` cache-frei gruen ohne Override mit 10 A-1-Gates; 1722 Unit-Tests + 80 passed + 4 skipped Integration-Tests; alle M5-Lastenheft-IDs `GG-API-001..004` + `GG-UI-001..009` + `GG-DEMO-001..008` erfuellt; `make fullbuild`-krb5-CVE-Defer-Pfad M4-Welle-7-Erbschaft), Pro-Welle-Reviews (4 Review-Folgen Welle-4b/5/6a/6b mit je 15/15 Findings + Welle-7-C2-Review-Folge 7 Findings), S-1..S-6-Verification, Welle-7-Erbschaft fuer M6+ (URL-Versionierung `/api/v1`-Mount, Snapshot-Envelope-v2-Body, CSV/JSONL-Export, Inline-SVG-Geraete-Grafik, dynamische Fault-Activation, IEC-61850-Smoke-Reaktivierung Trigger 009, Welle-3-Pre-init-Defense-Pattern), M5-Wandert-Nach, Nicht-vollzogene Items. |
| [`M6-results.md`](M6-results.md)                                | 2026-06-08  | M6-Abschluss-Ergebnisse: Welle-Tabelle (Welle 0..7 mit Sub-Slicing 4a/4b-a/b/c + 5a/5b/5c), Abnahme-Belege (`GG-CICD-*`/`GG-QG-002`/`GG-RT-001/004/005`/`GG-SAFE-*`-Audit/`GG-DEPLOY-001..006/011` — `make gates` 10 A-1-Gates ohne Override; Trigger 008/009/010/031 aufgeloest), Pro-Welle-Reviews, S-1..S-6-Verification, Welle-7-Erbschaft fuer M7+ (Trigger 033..037 + next/-Plaene), M6-Wandert-Nach, ADR-Decision-Sweep (0041..0046 Accepted), Nicht-vollzogene Items. (Zeile beim Post-M7-Index-Sweep 2026-06-12 nachgetragen — fehlte seit der M6-Closure.) |
| [`M7-results.md`](M7-results.md)                                | 2026-06-12  | M7-Abschluss-Ergebnisse: Welle-Tabelle (0/1a/1b-a/1b-b/2/3a/3b/X), Abnahme-Belege (**alle vier `GG-MVP-*` + alle vier `GG-SAFE-001..004` produktiv — der MVP ist geliefert**; `make gates` 10 A-1-Gates cache-frei gruen ohne Override; 139 passed / 4 skipped Integration), Pro-Welle-Reviews (6 Review-Folgen), S-1..S-6-Verification, Welle-X-Erbschaft (Trigger 033/037/038/039/040 + [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)/0051 `Proposed` + IEC-Pfad-A-Watch), Post-M7-Modus (Trigger-Watch, kein M8-Auto-Open per Welle-X-D-4), M7-ADR-Decision-Sweep (5 Accepted + 2 Proposed), Nicht-vollzogene Items. |
