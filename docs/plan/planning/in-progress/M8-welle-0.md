# Welle 0 — M8 Slice-Plan-Eroeffnung + Trigger-Triage

**Status:** In Progress (eroeffnet 2026-06-13 per Stakeholder-Mandat) —
Vorabraeumung + Slice-Aktivierung fuer **M8 (SOLLTE-Geraete & Netz →
Release v0.2.0)**. Pattern analog
[`../done-archive/M7-welle-0.md`](../done-archive/M7-welle-0.md). Welle 0
ist ein reines Doc-Arbeitspaket (kein Code-Pfad-Wechsel); die
Code-Substanz beginnt mit Welle 1 (041-C1).

**Container:** Der Meilenstein-Scope lebt in
[`roadmap.md`](roadmap.md) §4 M8 (Wellen-Skizze 0..3) — anders als M4..M7
braucht M8 **kein** eigenes `M{N}-<name>.md`-Container-Doc, weil die
Wellen bereits auf existierende Slice-Plaene (`041`/`042`) bzw.
`open/`-Trigger-Docs (`T-016..024`) abgebildet sind. Welle-0 oeffnet den
Meilenstein und aktiviert die erste Welle.

---

## 1. Kontext

M7 ist seit 2026-06-12 mit Welle-X-Closure abgeschlossen — der MVP ist
geliefert ([`../done/M7-results.md`](../done/M7-results.md)). Release
v0.1.0 publiziert; ein Doku-/Tooling-Cut v0.1.1 wurde bewusst verworfen
(kein Runtime-Delta). M8 ist der **erste Post-MVP-Feature-Meilenstein**,
per Mandat 2026-06-13 eroeffnet (vorher Post-MVP-Trigger-Watch,
Welle-X-D-4 „kein M8-Auto-Open").

### 1.1 M8-Eingangsbestand

| Item | Quelle | M8-Welle | Charakter |
| ---- | ------ | -------- | --------- |
| `AC-ADAPTER-PURE`-`ignore_imports`-Rueckbau | [`041-...`](041-adapter-pure-ignore-imports-rueckbau.md) ([`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)) | **Welle 0/1** | Architektur-Cleanup, Voraussetzung; 8 Bruecken in Tranchen C1..C4. |
| Fault-Engine-Standort/Naming | [`042-...`](042-fault-engine-location-and-naming.md) ([`ADR 0051`](../../adr/0051-fault-engine-location-and-naming.md)) | **Welle 0/1** | `*FaultAdapter` → `*FaultEngine`, Standort bleibt `hexagon/core/faults`. |
| EV-Charger / Transformer / Wind / Diesel | T-016..019 ([`016`](../open/016-sollte-ev-charger-device.md)..[`019`](../open/019-sollte-diesel-device.md)) | **Welle 1** | `GG-DEV-015..018`; neue Geraetemodelle. Aktiviert zugleich `D-7` (Pre-init-Defense-Pattern). |
| Inselnetz / Transformatorgrenzen / Blindleistung | T-020..022 ([`020`](../open/020-sollte-island-grid.md)..[`022`](../open/022-sollte-reactive-power.md)) | **Welle 2** | `GG-GRID-005..007`; Netzbilanz-Erweiterung. |
| Battery-Temperatur / Zellspannung | T-023/024 ([`023`](../open/023-sollte-battery-temperature.md), [`024`](../open/024-sollte-battery-cell-voltage.md)) | **Welle 3** | `GG-BESS-006/007`; Telemetrie-Erweiterung. |

### 1.2 Bleibt Trigger-Gated (kein M8-Pflicht-Item)

- T-037 (`GG-DEPLOY-007..010` Multi-Node) → M10, Stakeholder-getrieben.
- T-038/T-039 (Equality-Matrix / API-Replay) → M9 (Export & Live-API).
- T-033 (OTel-Collector-CVE) → Stable-Watch, upstream-getrieben.
- T-004/005/007/011/040/044 → Tooling-Querschnitt, laufen unabhaengig.
- T-030/T-026 → Forschungs-Spikes, optional.

## 2. Welle-0-Entscheidungen

1. **Kein Container-Doc.** M8-Scope = `roadmap.md` §4 M8 + die referenzierten
   Slice-/Trigger-Docs (siehe Kopf). Vermeidet Doku-Duplikation.
2. **Welle-Reihenfolge fix.** Cleanup (`041`/`042`) **vor** Geraete-Wellen:
   die neuen Driving-Adapter der SOLLTE-Geraete duerfen keine neue
   `AC-ADAPTER-PURE`-Ausnahme erben, und der Driving-Port aus 041-C2
   ist die Surface, auf der sie aufsetzen.
3. **041/042 aktiviert.** Beide von `next/` nach `in-progress/` verschoben
   (reiner `git mv`); Cross-Refs in [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)/[`ADR 0051`](../../adr/0051-fault-engine-location-and-naming.md),
   ADR-Index, `roadmap.md` und [`../done/M7-results.md`](../done/M7-results.md)
   nachgezogen.
4. **Sub-Slicing-Schwelle** (analog M4..M7): > 300 Zeilen Slice-Doc ODER
   > 5 Code-Commits ODER > 2 unabhaengige Sub-Bereiche → Sub-Welle-Split.
5. **`ADR-0050`/`ADR-0051`-Acceptance** ist Welle-1-Substanz, nicht Welle-0:
   `Proposed → Provisional` sobald der jeweils erste Umsetzungs-Tranche
   gruen ist (041-C1 bzw. 042-C1).

## 3. Naechster Schritt

**Welle 1 — 041-C1 (Fault-Type-Quick-Win):** Fault-Type-Konstanten in
eine adapter-erlaubte Surface ziehen, `_runs_action_router.py` umstellen,
den `_runs_action_router → core.faults.types`-`ignore_imports`-Eintrag
aus [`pyproject.toml`](../../../../pyproject.toml) entfernen.
Sensor: `make arch-check` + engste Router-/Fault-Tests. Verhaltensneutral.

## 4. DoD (Welle 0)

- [x] `041`/`042` nach `in-progress/` aktiviert (reiner `git mv`).
- [x] Cross-Refs nachgezogen (`ADR 0050`/`ADR 0051`, ADR-Index, roadmap, M7-results).
- [x] `roadmap.md`-Status auf „M8 Welle 0 aktiv" geflippt.
- [ ] `make docs-check` gruen.
