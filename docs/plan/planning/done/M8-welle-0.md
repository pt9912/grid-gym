# Welle 0 — M8 Slice-Plan-Eroeffnung + Trigger-Triage

**Status:** Done 2026-06-13 — Vorabraeumung + Slice-Aktivierung fuer
**M8 (SOLLTE-Geraete & Netz → Release v0.2.0)**, plus Closure von Welle 1
(Architektur-Cleanup, siehe §3). Pattern analog
[`../done-archive/M7-welle-0.md`](../done-archive/M7-welle-0.md). Welle 0
selbst war ein reines Doc-Arbeitspaket; die Code-Substanz lief in Welle 1
(Slices 041 + 042, beide Done).

**Container:** Der Meilenstein-Scope lebt in
[`roadmap.md`](../in-progress/roadmap.md) §4 M8 (Wellen-Skizze 0..3) — anders als M4..M7
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
| [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-`ignore_imports`-Rueckbau | [`041-...`](041-adapter-pure-ignore-imports-rueckbau.md) ([`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)) | **Welle 1** | Architektur-Cleanup, Voraussetzung; 8 Bruecken in Tranchen C1..C4. |
| Fault-Engine-Standort/Naming | [`042-...`](042-fault-engine-location-and-naming.md) ([`ADR 0051`](../../adr/0051-fault-engine-location-and-naming.md)) | **Welle 1** | `*FaultAdapter` → `*FaultEngine`, Standort bleibt `hexagon/core/faults`. |
| EV-Charger / Transformer / Wind / Diesel | T-016..019 ([`016`](../done-archive/016-sollte-ev-charger-device.md)..[`019`](../done-archive/019-sollte-diesel-device.md)) | **Welle 2** | [`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015)..018; neue Geraetemodelle. Aktiviert zugleich `D-7` (Pre-init-Defense-Pattern). |
| Inselnetz / Transformatorgrenzen / Blindleistung | T-020..022 ([`020`](../done-archive/020-sollte-island-grid.md)..[`022`](../done-archive/022-sollte-reactive-power.md)) | **Welle 3** | [`GG-GRID-005`](../../../../spec/lastenheft.md#gg-grid-005)..007; Netzbilanz-Erweiterung. |
| Battery-Temperatur / Zellspannung | T-023/024 ([`023`](../done-archive/023-sollte-battery-temperature.md), [`024`](../done-archive/024-sollte-battery-cell-voltage.md)) | **Welle 4** | [`GG-BESS-006`](../../../../spec/lastenheft.md#gg-bess-006)/007; Telemetrie-Erweiterung. |

### 1.2 Bleibt Trigger-Gated (kein M8-Pflicht-Item)

- T-037 ([`GG-DEPLOY-007`](../../../../spec/lastenheft.md#gg-deploy-007)..010 Multi-Node) → M10, Stakeholder-getrieben.
- T-038/T-039 (Equality-Matrix / API-Replay) → M9 (Export & Live-API).
- T-033 (OTel-Collector-CVE) → Stable-Watch, upstream-getrieben.
- T-004/005/007/011/040/044 → Tooling-Querschnitt, laufen unabhaengig.
- T-030/T-026 → Forschungs-Spikes, optional.

## 2. Welle-0-Entscheidungen

1. **Kein Container-Doc.** M8-Scope = `roadmap.md` §4 M8 + die referenzierten
   Slice-/Trigger-Docs (siehe Kopf). Vermeidet Doku-Duplikation.
2. **Welle-Reihenfolge fix.** Cleanup (`041`/`042`) **vor** Geraete-Wellen:
   die neuen Driving-Adapter der SOLLTE-Geraete duerfen keine neue
   [`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-Ausnahme erben, und der Driving-Port aus 041-C2
   ist die Surface, auf der sie aufsetzen.
3. **041/042 aktiviert.** Beide von `next/` nach `in-progress/` verschoben
   (reiner `git mv`); Cross-Refs in [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)/[`ADR 0051`](../../adr/0051-fault-engine-location-and-naming.md),
   ADR-Index, `roadmap.md` und [`../done/M7-results.md`](../done/M7-results.md)
   nachgezogen.
4. **Sub-Slicing-Schwelle** (analog M4..M7): > 300 Zeilen Slice-Doc ODER
   > 5 Code-Commits ODER > 2 unabhaengige Sub-Bereiche → Sub-Welle-Split.
5. **[`ADR-0050`](../../adr/0050-adapter-pure-bridge-retirement.md)/[`ADR-0051`](../../adr/0051-fault-engine-location-and-naming.md)-Acceptance** ist Welle-1-Substanz, nicht Welle-0:
   `Proposed → Provisional` sobald der jeweils erste Umsetzungs-Tranche
   gruen ist (041-C1 bzw. 042-C1).

## 3. Welle-1-Closure — Architektur-Cleanup (Done 2026-06-13)

Welle 1 (Slices 041 + 042) lieferte die Adapter-/Core-Entkopplung als
Voraussetzung fuer die Geraete-Wellen — verhaltensneutral, je per
`make fullbuild` (inkl. Compose-Smoke) und CI verifiziert:

- **Slice [`041`](041-adapter-pure-ignore-imports-rueckbau.md)**
  ([`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-Bridge-Rueckbau, C1..C4): **8 → 0**
  `ignore_imports` (`ignore_imports = []`). NEU `RunExecutionPort`
  (Driving-Port), `ControlAction`/Fault-Konstanten nach `core.domain.*`,
  Demo-/Scenario-Bootstrap im Composition-Root `grid_gym.composition`
  mit eigenem `composition.asgi`-Entrypoint.
  [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md) + NEU
  [`ADR 0054`](../../adr/0054-composition-asgi-entrypoint-and-scenario-hook.md)
  `Accepted`.
- **Slice [`042`](042-fault-engine-location-and-naming.md)**
  (Fault-Engine-Naming): `*FaultAdapter` → `*FaultEngine`, Standort
  bleibt `hexagon/core/faults`, keine Compat-Aliase.
  [`ADR 0051`](../../adr/0051-fault-engine-location-and-naming.md) `Accepted`.

Alle 7 Architektur-Contracts gruen **ohne Ausnahme**.

### Lerneintrag (Closure-Pflicht)

1. **[`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) prueft indirekte Ketten.** Ein Modul nach
   `composition/` zu verschieben reicht NICHT, solange ein Adapter es
   noch importiert (Adapter → composition → `core.*` bleibt verboten).
   Loesung: Dependency invertieren — Hook im Adapter + Registrierung im
   Composition-Entrypoint
   ([`ADR 0054`](../../adr/0054-composition-asgi-entrypoint-and-scenario-hook.md)).
   Betraf das Scenario-Bootstrap (041-C3b), nicht `_demo_setup` (C3a,
   kein src-Adapter-Importer → reiner Move genuegte).
2. **`make coverage-gate` vor dem Push fahren, nicht nur `test-unit`.**
   Neue Protocol-/Port-Stubs druecken die Branch-Coverage; inline
   `def f(): ...` erzeugt ungedeckte Branch-Kanten — Block-Form + Docstring
   nutzen (Coverage-Exclude greift nur auf `...` allein auf der Zeile).
   Kostete in 041-C2 einen CI-Fix.
3. **`tools/`/`deploy/` im Rename-/Audit-Scope nicht vergessen** — die
   `codepaths`-roots umfassen sie; ein src+tests-only-Audit uebersah
   `tools/_demo_replay.py` (042, typecheck-Fehler nach dem Rename).
4. **Keine Compat-Aliase bei vollstaendigem In-Repo-Rename**
   ([`ADR 0051`](../../adr/0051-fault-engine-location-and-naming.md) §2.3) —
   alle Referenzen umbenennbar, kein Uebergangsbedarf, kein spaeterer
   Alias-Removal-Slice.
5. **`app.py`-Public-Function-Cap** ([`AC-NO-GOD-UTILS`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), max 5 public
   top-level): neue Funktionen `_`-prefixen (Cross-Modul-`_`-Import ist
   im Repo etabliert, z. B. `_DEMO_RUN_ID`).

### Naechster Schritt

Welle 2 — Geraete `T-016..019` ([`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015)..018); erstes echtes Feature,
eigene Welle-Doc bei Aktivierung.

## 4. DoD (Welle 0)

- [x] `041`/`042` nach `in-progress/` aktiviert (reiner `git mv`).
- [x] Cross-Refs nachgezogen ([`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)/[`ADR 0051`](../../adr/0051-fault-engine-location-and-naming.md), ADR-Index, roadmap, M7-results).
- [x] `roadmap.md`-Status auf „M8 Welle 0 aktiv" geflippt.
- [x] `make docs-check` gruen.
