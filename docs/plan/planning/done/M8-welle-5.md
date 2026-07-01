# Welle 5 — M8 Closure (SOLLTE-Geraete & Netz)

**Status:** Done 2026-07-01 (M8-Closure-Welle) — Stack C0
(Slice-Doc + Decisions 5-D-1..D-5) + C1 (Trigger-Archival
`open/016..024` → `done-archive/`, rename-only) + C2 (Link-Pflege
Fan-out + [`open/README.md`](../open/README.md)/[`carveouts.md`](../in-progress/carveouts.md)-Sweep) +
C3 (NEU [`M8-results.md`](M8-results.md)) + C4 (Roadmap M8 → `Done` +
Top-Status-Sweep + README-Sync) + C5 (Release v0.2.0:
`pyproject`-Bump + CHANGELOG-Finalisierung + Tag). Pattern analog
[`M7-welle-X.md`](../done-archive/M7-welle-X.md) +
[`M6-welle-7.md`](../done-archive/M6-welle-7.md).
**Datum:** 2026-07-01 (Welle-5-C0 · Done 2026-07-01).
**Quelle:** [`roadmap.md §4 M8`](../in-progress/roadmap.md) +
[`M8-welle-0.md`](M8-welle-0.md) (M8-Eroeffnungs-Decisions) +
[`carveouts.md`](../in-progress/carveouts.md) (Trigger-Archival-Zusage
`T-016..024` „mit M8-Closure").

---

## 1. Context

M8 (SOLLTE-Geraete & Netz) ist die neunte Meilenstein-Spanne und
der **erste Post-MVP-Feature-Meilenstein**. Alle Substanz-Wellen
sind `Done`:

- **Welle 0** Slice-Plan-Eroeffnung + Trigger-Triage
  ([`M8-welle-0.md`](M8-welle-0.md)).
- **Welle 1 (Architektur-Cleanup)** Slice
  [`041`](../done/041-adapter-pure-ignore-imports-rueckbau.md)
  ([`AC-ADAPTER-PURE`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-`ignore_imports`-Rueckbau → `[]`,
  [`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md) `Accepted`) +
  [`042`](../done/042-fault-engine-location-and-naming.md)
  (Fault-Engine-Standort/-Naming, [`ADR 0051`](../../adr/0051-fault-engine-location-and-naming.md) `Accepted`) +
  NEU [`ADR 0054`](../../adr/0054-composition-asgi-entrypoint-and-scenario-hook.md) (`composition`-Paket + ASGI-Entrypoint).
- **Welle 2 (Geraete)** alle vier SOLLTE-Geraete
  ([`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015)..018): EV-Charger
  ([`ADR 0055`](../../adr/0055-ev-charger-device-pattern.md)), Transformer
  ([`ADR 0056`](../../adr/0056-transformer-device-pattern.md)), Wind-Turbine
  ([`ADR 0057`](../../adr/0057-wind-turbine-device-pattern.md)), Diesel-Generator
  ([`ADR 0058`](../../adr/0058-diesel-generator-device-pattern.md)) + generische
  `ScenarioFaultEngine` ([`ADR 0059`](../../adr/0059-generic-scenario-fault-engine.md), Welle-2-D8) +
  Codec-Dedup-Slice [`045`](../done/045-fault-state-flag-codec-dedup.md).
  Trigger 016..019 aufgeloest.
- **Welle 3 (Netzbilanz)** Schaerfungen des
  [`GG-GRID-005`](../../../../spec/lastenheft.md#gg-grid-005)..007-Modells: Inselnetz
  ([`ADR 0060`](../../adr/0060-island-grid-bilanz-pattern.md)), Trafo-Grenzen
  ([`ADR 0061`](../../adr/0061-transformer-limit-bilanz-pattern.md)), Blindleistung
  ([`ADR 0062`](../../adr/0062-reactive-power-bilanz-pattern.md)/[`ADR 0063`](../../adr/0063-pv-volt-var-q-emission-pattern.md)/[`ADR 0064`](../../adr/0064-grid-connection-q-transformer-apparent-power.md);
  Snapshot v2→v3). Trigger 020..022 aufgeloest.
- **Welle 4 (BESS-Telemetrie)** additive Telemetrie-Schaerfungen
  ([`GG-BESS-006`](../../../../spec/lastenheft.md#gg-bess-006)/007): Temperatur
  ([`ADR 0065`](../../adr/0065-battery-thermal-telemetry-pattern.md)) + Zellspannung
  ([`ADR 0066`](../../adr/0066-battery-cell-voltage-telemetry-pattern.md)). Trigger 023/024 aufgeloest.

**Parallel (Post-MVP-Trigger-Watch, keine SOLLTE-Feature-Welle,
seither geliefert):** Replay-Paar [`039`](../done/039-api-replay-trigger-surface.md)/[`040`](../done/040-replay-finalize-headless-run-end-seam.md)
([`ADR 0067`](../../adr/0067-run-end-seam-and-partial-run.md)/[`ADR 0068`](../../adr/0068-api-replay-binding-persistence.md)) +
Multi-Run-Execution ([`ADR 0069`](../../adr/0069-multi-run-execution-and-scenario-store.md)) +
Scenario-Scheduled-Commands (Trigger 046, [`ADR 0070`](../../adr/0070-scenario-scheduled-device-commands.md)) +
Harness-Durchsetzungsschicht (Slice
[`051`](../done/051-durchsetzungsschicht-enforcement-layer.md),
[`ADR 0071`](../../adr/0071-enforcement-layer-hooks.md)).

Welle 5 ist die **reine Closure-Welle** (Doku + Release, kein
Feature-Code): Trigger-Archival, Closure-Artefakt
[`M8-results.md`](M8-results.md), Roadmap-DoD-Sweep,
Top-Level-Doku-Sync und der Minor-Release **v0.2.0**.

---

## 2. Scope

Closure-Sektionen im NEU [`M8-results.md`](M8-results.md) (Pattern
analog [`M7-results.md`](M7-results.md)):

1. **Welle-Tabelle** — Quick-Glance aller M8-Wellen (0..5) +
   parallele Post-MVP-Wellen mit Status.
2. **Abnahme-Belege** — Lastenheft-IDs, die M8 produktiv gemacht
   hat ([`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015)..018,
   [`GG-GRID-005`](../../../../spec/lastenheft.md#gg-grid-005)..007,
   [`GG-BESS-006`](../../../../spec/lastenheft.md#gg-bess-006)/007).
3. **Pro-Welle-Reviews** — Review-Folgen pro Substanz-Welle.
4. **S-Sweep** — Welle-5-End-to-End-Verifikation.
5. **Welle-5-Erbschaft (Post-M8)** — offene Trigger +
   Forward-Pointer.
6. **M8-Wandert-Nach** — was nach `done/` zieht + Post-M8-Modus.

Plus M8-ADR-Decision-Sweep (0050/0051/0054/0055..0071) +
Nicht-vollzogene Items (bewusst).

---

## 3. Architektur-Entscheidungen (Welle-5)

### Welle-5-D-1 — Kein neuer ADR in Welle 5

Closure-Welle traegt keine NEU ADRs (Doku + Release). Pattern
analog M5-/M6-/M7-Welle-Closure.

### Welle-5-D-2 — Kein ADR-Accept-Flip noetig (alle bereits `Accepted`)

**Final:** anders als bei M7 (dort flippten fuenf `Provisional`-
ADRs in der Closure-Welle-X) sind **alle M8-ADRs bereits
`Accepted`** — jeder wurde mit seiner Substanz-Welle produktiv
belegt und dort auf `Accepted` gezogen (0050/0051 mit Welle 1,
0054..0059 mit Welle 1/2, 0060..0064 mit Welle 3, 0065/0066 mit
Welle 4, 0067..0071 mit den parallelen Post-MVP-Wellen). Die
Closure-Welle traegt daher **keinen** C1-ADR-Status-Commit; der
M8-ADR-Sweep in [`M8-results.md §7`](M8-results.md) ist rein
dokumentarisch.

[`ADR 0050`](../../adr/0050-adapter-pure-bridge-retirement.md)/[`ADR 0051`](../../adr/0051-fault-engine-location-and-naming.md)
loesen die M7-Welle-X-D-2-Deferral auf: die zwei in M7 bewusst
auf `Proposed` gehaltenen Vorschlaege sind mit ihren
Umsetzungs-Slices ([`041`](../done/041-adapter-pure-ignore-imports-rueckbau.md)/[`042`](../done/042-fault-engine-location-and-naming.md))
in M8-Welle-1 produktiv geworden und `Accepted`.

### Welle-5-D-3 — Trigger-Archival: `open/016..024` → `done-archive/`

**Final: die neun aufgeloesten SOLLTE-Trigger wandern jetzt
(rename-only) nach `done-archive/`.** Die Substanz-Wellen 2/3/4
haben die Trigger-Docs [`016`](../done-archive/016-sollte-ev-charger-device.md)..[`024`](../done-archive/024-sollte-battery-cell-voltage.md)
je auf `Status: Resolved` gesetzt, die **physische
Archivierung** aber bewusst auf die M8-Closure verschoben
([`carveouts.md`](../in-progress/carveouts.md) §2 `T-016..024`:
„Archivierung … mit M8-Closure"). Welle 5 vollzieht den Move in
**einem reinen `git mv`-Commit** (C1, git-Rename-Detection) und
zieht die Inbound-Links im **unmittelbar folgenden** Commit (C2)
nach — konform zur Wave-Self-Close-Konvention
([`../README.md`](../README.md) §Wave-Self-Close).

Ziel `done-archive/` (nicht `done/`) folgt der in
[`carveouts.md`](../in-progress/carveouts.md) verankerten Zusage
und dem M7-Praezedenzfall (aufgeloeste `open/`-Trigger 034/035
liegen in `done-archive/`). Der generische Wortlaut in
[`open/README.md`](../open/README.md) („nach `../done/`") wird auf
`done-archive/` praezisiert.

### Welle-5-D-4 — M8-Abschluss-Kriterium

**Final: M8 = SOLLTE-Geraete & Netz komplett.** Alle vier
SOLLTE-Geraete ([`GG-DEV-015`](../../../../spec/lastenheft.md#gg-dev-015)..018),
das komplette SOLLTE-Netzmodell
([`GG-GRID-005`](../../../../spec/lastenheft.md#gg-grid-005)..007) und die zwei
BESS-Telemetrie-IDs ([`GG-BESS-006`](../../../../spec/lastenheft.md#gg-bess-006)/007)
sind produktiv; die parallel abgearbeiteten Post-MVP-Trigger
(039/040/046 + Slice 051) sind aufgeloest. Verbleibende offene
Trigger (033-Nachfolge, 037 Multi-Node, 038 volle GG-TERM-Matrix,
047 SNMP/LwM2M, Tooling-Querschnitt) sind Post-M8 legitim offen
und blockieren den Abschluss nicht.

### Welle-5-D-5 — Release v0.2.0 als Teil der Closure

**Final: die M8-Closure schneidet den Minor-Release v0.2.0.**
Anders als eine reine Doku-Closure gibt es **echten
Runtime-Delta** seit v0.1.0 (neue Geraetemodelle, Netzbilanz-Q,
BESS-Telemetrie, Multi-Run-Execution, Scenario-Commands) — der
Release ist damit [`release-policy`](../../adr/0042-sbom-tool-and-release-pattern.md)-konform
(kein Doku-only-Cut wie das verworfene v0.1.1,
[`M8-welle-0.md`](M8-welle-0.md)). `Minor`-Bump, weil neue
Gerätemodelle additive Features sind. C5 bumpt
[`pyproject.toml`](../../../../pyproject.toml) `0.1.0 → 0.2.0`,
finalisiert den CHANGELOG-`[Unreleased]`-Abschnitt zu
`[0.2.0]` und pusht den Tag `v0.2.0` (loest
[`release.yml`](../../../../.github/workflows/release.yml) aus:
GHCR-Image + 5 Assets + SBOM).

---

## 4. Liefer-Reihenfolge

### C0 — `docs(plan)`: M8-welle-5 Slice-Doc

**Dieser Commit.** Slice-Doc + Decisions 5-D-1..D-5 +
DoD-Checkliste + [`in-progress/README.md`](../in-progress/README.md)/[`../README.md`](../README.md)-Bestand-Zeile.

### C1 — `docs(plan)`: Trigger-Archival (rename-only)

Reiner `git mv` der neun `open/016..024-*.md` nach
`done-archive/` — keine Inhalts-Edits (5-D-3).

### C2 — `docs(plan)`: Link-Pflege-Fan-out

die `open/016..024`-Trigger-Links auf `done-archive/` (ADRs
analog) in
Roadmap, [`carveouts.md`](../in-progress/carveouts.md), den
M8-Welle-Docs, [`M2-devices-results.md`](M2-devices-results.md)
und [`ADR 0055`](../../adr/0055-ev-charger-device-pattern.md)..[`ADR 0066`](../../adr/0066-battery-cell-voltage-telemetry-pattern.md). [`open/README.md`](../open/README.md)
Bestand-Tabelle + Intro bereinigt (SOLLTE-Zeilen `Resolved`,
Move nach `done-archive/`); [`carveouts.md`](../in-progress/carveouts.md)
Archiv-Status nachgezogen.

### C3 — `docs(plan)`: NEU `M8-results.md`

Closure-Artefakt mit den sechs Sektionen aus §2 + ADR-Sweep +
Nicht-vollzogene-Items. Pattern analog
[`M7-results.md`](M7-results.md).

### C4 — `docs(plan)`: M8-Closure-Top-Level-Sync

- [`roadmap.md`](../in-progress/roadmap.md): M8-Section-Header
  `In Progress → Done`; Top-Status-Block auf M8-`Done` +
  Post-M8-Trigger-Watch; historische Belege unberuehrt.
- [`../README.md`](../../../../README.md) +
  [`README.de.md`](../../../../README.de.md): Status-Block M1..M8;
  ADR-Zaehlung; Geraete-/Netz-/BESS-Delta.
- `M8-welle-5.md` Status-Header + §9-DoD.
- `make gates` + `make docs-check` als Closure-Verifikation.

### C5 — `chore(release)`: v0.2.0

`pyproject.toml` `0.1.0 → 0.2.0`; CHANGELOG `[Unreleased]` →
`[0.2.0] - 2026-07-01` + neuer leerer `[Unreleased]`;
`make fullbuild` gruen; Tag `v0.2.0` auf main-Tip + Push
(release.yml). Self-Close-Move `M8-welle-5.md` bleibt hier nicht
noetig — die M8-Welle-Docs liegen bereits in `done/`.

---

## 5. Critical Files

**Welle-5-NEU (C0/C3):** `M8-welle-5.md` (C0);
`docs/plan/planning/done/M8-results.md` (C3).
**Welle-5-RENAME (C1):** `open/016..024-*.md` → `done-archive/`.
**Welle-5-MODIFY (C2 + C4 + C5):** Roadmap,
[`carveouts.md`](../in-progress/carveouts.md),
[`open/README.md`](../open/README.md), M8-Welle-Docs,
[`M2-devices-results.md`](M2-devices-results.md), [`ADR 0055`](../../adr/0055-ev-charger-device-pattern.md)..[`ADR 0066`](../../adr/0066-battery-cell-voltage-telemetry-pattern.md)
(C2); Roadmap-Header + READMEs (C4);
[`pyproject.toml`](../../../../pyproject.toml) +
[`CHANGELOG.md`](../../../../CHANGELOG.md) (C5).
**UNBERUEHRT:** aller Code (`src/`, `tests/`), `docs/user/*.md`,
alle ADR-Bodies (nur Link-Pflege per
[`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md), keine
Inhalts-Aenderung), bestehende `done/M8-welle-*.md` (nur
Link-Pflege).

---

## 6. Verifikationspfad

- `make docs-check` cache-frei gruen (faengt Trigger-Move-Fan-out
  + ADR-Index-Drift).
- `make gates` cache-frei gruen am Closure-Hash (Doku-only —
  Test-Counts unveraendert).
- `make fullbuild` gruen vor Tag-Push (C5;
  [`harness/README.md`](../../../../harness/README.md) Sensors:
  „Vor Welle-/Meilenstein-Closure").

---

## 7. Risiken

- **R1 Trigger-Move-Fan-out** — 016..024 sind aus ~28
  Nicht-`done-archive`-Docs referenziert (inkl. [`ADR 0055`](../../adr/0055-ev-charger-device-pattern.md)..[`ADR 0066`](../../adr/0066-battery-cell-voltage-telemetry-pattern.md)).
  Mitigation: `make docs-check` nach C2; `done-archive/**` ist
  d-check-`ids`/`codepaths`-ignoriert, aber Inbound-Links aus
  `done/`/`in-progress/`/`adr/` sind es nicht.
- **R2 ADR-Link-Pflege vs. Accepted-Immutabilitaet** — die
  Link-Aenderung von open/ auf done-archive/
  in Accepted-ADRs ist reine Bezug-/Link-Pflege
  ([`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md)), kein
  Decision-Text-Edit. Mitigation: nur die Pfad-Segmente ersetzen.
- **R3 Release-Prerequisite** — `make fullbuild` war zeitweise im
  Defer-Pfad (OTel-CVE-2026-42504); Trigger 033 ist **Resolved
  2026-06-18**, der Defer damit aufgehoben. Mitigation: `fullbuild`
  vor dem Tag-Push tatsaechlich gruen fahren.
- **R4 `:latest`-Alias** — [`release.yml`](../../../../.github/workflows/release.yml)
  setzt `:latest` nur, wenn der Tag-Commit der aktuelle
  Default-Branch-Tip ist. Mitigation: erst alle C0..C5-Commits
  nach `main` pushen, **dann** den Tip taggen.

---

## 8. Wandert nach

Nach C3 liegt `M8-results.md` in `done/`; `M8-welle-5.md` liegt
(wie die uebrigen M8-Welle-Docs) direkt in `done/`. Die neun
aufgeloesten Trigger liegen nach C1 in `done-archive/`. **M8 ist
abgeschlossen — SOLLTE-Geraete & Netz sind geliefert, v0.2.0 ist
released.** Aktiver Slice danach: **keiner**
(Post-M8-Trigger-Watch); [`roadmap.md`](../in-progress/roadmap.md)-Top-Status
traegt den Watch-Modus + die offenen Trigger als Eintrittspunkte.

---

## 9. DoD-Checkliste (mit C4 abzuhaken)

- [ ] C1: `open/016..024-*.md` → `done-archive/` (rename-only).
- [ ] C2: Link-Fan-out `open/016..024` → `done-archive/` +
      [`open/README.md`](../open/README.md)/[`carveouts.md`](../in-progress/carveouts.md)-Sweep;
      `make docs-check` gruen.
- [ ] C3: `M8-results.md` mit 6 Sektionen + ADR-Sweep
      (0050/0051/0054/0055..0071 alle `Accepted`, 5-D-2) +
      Abschluss-Kriterium (5-D-4).
- [ ] C4: [`roadmap.md`](../in-progress/roadmap.md) M8 `Done` +
      Top-Status-Sweep + Post-M8-Trigger-Watch; READMEs M1..M8.
- [ ] C5: `pyproject` `0.2.0` + CHANGELOG `[0.2.0]` +
      `make fullbuild` gruen + Tag `v0.2.0` gepusht (5-D-5).
- [ ] `make gates` cache-frei gruen am Closure-Hash.

---

## References

- [`roadmap.md §4 M8`](../in-progress/roadmap.md) —
  M8-Meilenstein-Vorbelegung + Wellen-Skizze.
- [`M8-welle-0.md`](M8-welle-0.md) — M8-Eroeffnungs-Decisions
  (v0.1.1-Verwurf-Note).
- [`carveouts.md`](../in-progress/carveouts.md) — Trigger-Archival-
  Zusage `T-016..024`.
- [`M7-welle-X.md`](../done-archive/M7-welle-X.md) +
  [`M6-welle-7.md`](../done-archive/M6-welle-7.md) —
  Closure-Welle-Vorbilder.
- [`M7-results.md`](M7-results.md) — Results-Doc-Vorbild.
- ADR-Index [`../../adr/README.md`](../../adr/README.md).
