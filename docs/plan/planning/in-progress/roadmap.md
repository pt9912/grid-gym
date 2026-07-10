# Roadmap — grid-gym

**Status:** Slice-getrieben
([`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md)). **M1..M8
abgeschlossen** — die MUSS-/SOLLTE-Roadmap ist geliefert, **v0.2.0 released**.
Kein aktiver Slice; zuletzt abgeschlossen:
[`055`](../done/055-profile-preflight-e2e-sensor.md) (E2E-Sensor
produktiver Profil-Pfad, Test-only) und
[`038`](../done/038-gg-term-002-003-full-equality-matrix.md)
(volle [`GG-TERM-002`](../../../../spec/lastenheft.md#gg-term-002)/003-Equality-Matrix → **v0.3.0**).
**Stand:** 2026-07-03

**Bezug:** [Lastenheft](../../../../spec/lastenheft.md),
[Architektur](../../../../spec/architecture.md),
[`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md) (Planungsmodell),
[`ADR 0001`](../../adr/0001-documentation-and-planning-structure.md) (Doku-/
Planungsstruktur), [`carveouts.md`](carveouts.md).

---

## 1. Zweck

Diese Roadmap fuehrt (a) die **gelieferte Historie** (Meilensteine M1..M8, jetzt
eingefroren) als Nachschlag-Index und (b) die **aktive/geplante Slice-Arbeit**.

Seit [`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md) ist das
Planungsmodell **slice-getrieben**: Wellen/Slices sind die oberste Einheit, es
werden **keine neuen Meilensteine (`M{N}`)** mehr eroeffnet, und die
Release-Entscheidung faellt **pro Slice** (§5).

**`M{N}`-Marker sind historisch.** Die bestehenden `M{N}`-Statusmarker in der
[`GG-TRACE-001`](../../../../spec/lastenheft.md#gg-trace-001)-Matrix
(Lastenheft §27.2), in `spec/protocol_profiles.md` (Adapter-Provenienz) und in
`spec/persistence-schema.yaml` bleiben als Aufzeichnung eingefroren; neue
Anforderungs-Erfuellung wird per **Slice-Referenz** (bzw. Release-Version)
eingetragen.

---

## 2. Konvention

- Neue Arbeit = **Slice** (`NNN-slug.md`, repo-weit fortlaufende dreistellige
  Nummer; Muster `041`/`045`/`051`/`053`), grosse Slices sub-gesliced als
  `NNN-a`/`NNN-b`.
- Lifecycle: `open → next → in-progress → done`
  ([`ADR 0001`](../../adr/0001-documentation-and-planning-structure.md)).
- Jeder Slice-Plan traegt Akzeptanzkriterien, einen Verifikationspfad und ein
  **Release-Feld** (§5).
- Abgeschlossene Slices wandern per Self-Move nach [`../done/`](../done/) mit
  Closure-Notiz.

---

## 3. Gelieferte Historie (M1..M8, eingefroren)

Die Meilenstein-Ebene ist Historie; das vollstaendige Detail (Wellen,
Abnahme-Belege, ADR-Sweeps) lebt in den `M{N}-results.md`-Closure-Docs unter
[`../done/`](../done/). Diese Tabelle ist der Nachschlag-Index.

| Meilenstein | Lieferziel | Abschluss | Closure-Doc |
| ----------- | ---------- | --------- | ----------- |
| M1 | Tick-Loop-Spine | 2026-05-17 | [`M1-tick-loop-results.md`](../done/M1-tick-loop-results.md) |
| M2 | Geraetemodelle | 2026-05-20 | [`M2-devices-results.md`](../done/M2-devices-results.md) |
| M3 | Faults + Multi-Agent + Observability | 2026-05-25 | [`M3-results.md`](../done/M3-results.md) |
| M4 | Protokolladapter (MQTT/Modbus/OPC-UA/DNP3/IEC-61850) | 2026-06-01 | [`M4-results.md`](../done/M4-results.md) |
| M5 | UI + Demo | 2026-06-04 | [`M5-results.md`](../done/M5-results.md) |
| M6 | Performance + Security + CI/CD-Haertung | 2026-06-08 | [`M6-results.md`](../done/M6-results.md) |
| M7 | MVP-Abschluss → **v0.1.0** | 2026-06-12 | [`M7-results.md`](../done/M7-results.md) |
| M8 | SOLLTE-Geraete & Netz → **v0.2.0** | 2026-07-01 | [`M8-results.md`](../done/M8-results.md) |

Der MVP-Abnahmescope und die architektonischen Vorbedingungen sind mit
M7/M8 erfuellt; Detail in [`M7-results.md`](../done/M7-results.md) bzw.
[`M8-results.md`](../done/M8-results.md).

---

## 4. Aktive / geplante Slices

**Kein aktiver Slice.** Zuletzt abgeschlossen (2026-07-10):
[`058`](../done/058-marker-sensor-drift-guard.md) (Sensor-Marker-Drift-Guard
Meta-Test, Follow-up zu 054, Test-only) +
[`054`](../done/054-pytest-marker-drift-sensor-targets.md)
(pytest-Marker-Sweep `determinism`/`fault`, Test-only); davor
[`055`](../done/055-profile-preflight-e2e-sensor.md) (E2E-Sensor
produktiver Profil-Pfad → Replay-Preflight; Slice-038-Review-INFO-
Aufloesung, Test-only, Release **nein**) und
[`038`](../done/038-gg-term-002-003-full-equality-matrix.md) (volle
[`GG-TERM-002`](../../../../spec/lastenheft.md#gg-term-002)/003-Equality-Matrix,
[`ADR 0073`](../../adr/0073-gg-term-full-equality-matrix-runmetadata.md) `Accepted` →
Release **v0.3.0**, 2026-07-03 — erster Release-Zyklus des
slice-getriebenen Modells); davor
[`053`](../done/053-planungsmodell-slices-ohne-meilensteine.md) (slice-first-
Umstellung, [`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md)).

**Naechster Aktivierungs-Kandidat** (Planner-Notiz 2026-07-03,
aktualisiert 2026-07-10): Hygiene-Buendel — Teil 1
[`054`](../done/054-pytest-marker-drift-sensor-targets.md)
(pytest-Marker-Sweep `determinism`/`fault`) **2026-07-10 aufgeloest → `done/`**
(alle drei Marker-Sensoren nicht-leer gruen; deferrter CI-Anker via
[`058`](../done/058-marker-sensor-drift-guard.md) als Meta-Drift-Guard
geschlossen). Verbleibend
[`056`](../open/056-adr-index-status-sync.md) (ADR-Index-Status-Sync)
+ [`057`](../open/057-app-version-single-source.md)
(`_APP_VERSION`-Single-Sourcing) — als ein Slice oder zwei kleine;
057 traegt das einzige Runtime-Delta (Release-Entscheidung dort).

Weitere trigger-getriebene Folgearbeit + Aktivierungs-Bedingungen:
[`../open/`](../open/) (Trigger-Watch). Cross-Slice-Carveouts
(Anti-Scope + Erbschaft): [`carveouts.md`](carveouts.md).

---

## 5. Release-Modell (pro Slice)

Seit [`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md) faellt
die Release-Entscheidung **pro Slice**: jeder Slice-Plan traegt ein DoD-Feld
„Release-Entscheidung: ja/nein (+ SemVer-Ziel)".

- **`nein`** → das Delta sammelt unter [`CHANGELOG.md`](../../../../CHANGELOG.md)
  `[Unreleased]`.
- **`ja`** → der Abschluss-Commit schneidet den Tag (`pyproject`-Bump +
  CHANGELOG-Finalisierung + `v*.*.*`-Tag → `release.yml`), gebunden an die Regel
  „kein Doku-only-Release" (Runtime-Delta-Pflicht) + `make fullbuild` vor dem
  Tag. SemVer folgt dem Delta (Minor bei additiven Features, Patch bei Fixes).

Aktuelles Release: **v0.3.0** (2026-07-03, Slice 038 — erster
Release unter dem Slice-Release-Modell).
