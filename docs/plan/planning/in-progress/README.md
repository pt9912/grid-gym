# In Progress

Lebende Roadmap und aktive Slice-Plaene, an denen gearbeitet wird.

## Bestand

| Datei | Gegenstand |
| ----- | ---------- |
| [`roadmap.md`](roadmap.md) | Meilenstein-Uebersicht (M1..Mx) mit Lastenheft-/Architektur-Bezuegen, Abnahmekriterien und Status. |
| [`carveouts.md`](carveouts.md) | Cross-Meilenstein-Index aller aktiven Carveouts (Anti-Scope + Trigger-Watch + Erbschaft). |
| [`M6-perf-security-cicd.md`](M6-perf-security-cicd.md) | M6-Slice-Plan (Performance + Security + CI/CD-Haertung; aktiver Meilenstein). |
| [`M6-welle-5c.md`](M6-welle-5c.md) | M6-Welle-5c-Slice-Doc (SOLLTE-Items + IP/Netz-Beschraenkung; `GG-SAFE-005` ✓ produktiv per Lastenheft-Traceability Z. 2291 an 4 Geraeten + `GG-SAFE-006` ⚠ partial (Core-Diff ✓; Per-Lauf-Status-Marker + ReplaySource-Integration fehlen → NEU Trigger 036) + Demo-Compose `ports`-Hardening per `carveouts.md §2.7`-Auflage). **In Progress 2026-06-07** mit C0 (dieser Commit, nach Slice-Doc-Iteration ueber 2 Review-Runden mit 8 Findings vor Push). |

**Aktive Welle:** M6-Welle-5c (SOLLTE-Items + IP/Netz-
Beschraenkung; `GG-SAFE-005/006` + Demo-Compose-Hardening) —
**In Progress 2026-06-07** mit C0 (dieser Commit; Slice-Doc-
Anlage; Decisions D-1..D-6 final nach Slice-Doc-Iteration
ueber 2 Review-Runden mit 8 Findings vor Push). `GG-SAFE-005`
✓ produktiv an 4 Geraeten (Battery/Load/GridConnection/PV) per
Lastenheft-Traceability Z. 2291; `GG-SAFE-006` ⚠ partial
(Core-Diff-Algorithm `diff_replay` ✓ produktiv; Per-Lauf-
Status-Marker + ReplaySource-Integration fehlen → NEU Trigger
036); Demo-Compose-Port-Bind-Hardening per `carveouts.md
§2.7`-Auflage. Schliesst die Welle-5-Subdivision (5a + 5b +
5c).

**Aktiver Meilenstein:** M6 (Performance + Security + CI/CD-
Haertung; in `roadmap.md §3 M6`). M1..M5 sind `Done`; alle
abgeschlossenen Slice-/Welle-Docs leben unter
[`../done/`](../done/) und sind dort in
[`../done/README.md`](../done/README.md) gelistet.
