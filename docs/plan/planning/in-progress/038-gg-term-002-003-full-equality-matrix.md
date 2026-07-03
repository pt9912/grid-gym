# 038 — Volle `GG-TERM-002/003`-Equality-Matrix (1b-Carveout)

**Status:** **In Progress** (aktiviert 2026-07-03 per Maintainer-
Beauftragung: Compliance-/Audit-Vollstaendigkeit der
Reproduzierbarkeits-Metadaten). Historischer Trigger-Stand: Open —
dokumentierter Scope-Carveout aus M7-Welle-1b.
**Datum:** 2026-06-09 (aktualisiert 2026-07-03: Stand nach Slice
039/040 nachgezogen, C0-Entscheidungspunkte ergaenzt, DoD-Feld
per [`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md) D-3 nachgeruestet; aktiviert + Tranchen-Plan §T)
**Release-Entscheidung:** **ja** (SemVer-Ziel: minor) — echtes
Runtime-Delta (`RunMetadata`-Felder + Alembic-Migration +
Preflight-Erweiterung); finale Bestaetigung im aufloesenden C0
([`ADR 0072`](../../adr/0072-slice-driven-planning-no-milestones.md) D-3).
**Quelle:** M7-Welle-1b-a-C0 (Decision 1b-a-D-6;
[`docs/plan/planning/done-archive/M7-welle-1b-a.md`](../done-archive/M7-welle-1b-a.md)).

---

## Lastenheft-Akzeptanz

[`GG-TERM-002`](../../../../spec/lastenheft.md#gg-term-002) (Determinismus) + [`GG-TERM-003`](../../../../spec/lastenheft.md#gg-term-003) (Reproduzierbarkeit)
sind normative Begriffsdefinitionen
([`spec/lastenheft.md`](../../../../spec/lastenheft.md)):

> **[`GG-TERM-002`](../../../../spec/lastenheft.md#gg-term-002):** Determinismus bedeutet: Bei gleicher Version,
> gleicher Plattformarchitektur, gleichen Eingabedaten, gleicher
> Szenario-Datei, gleicher Konfiguration und gleichem Seed erzeugt
> ein Simulationslauf dieselben fachlichen Ausgaben in derselben
> Tick-Reihenfolge.
>
> **[`GG-TERM-003`](../../../../spec/lastenheft.md#gg-term-003):** … speichert alle zur Wiederholung notwendigen
> Metadaten, mindestens Version, Szenario-Hash, Konfiguration,
> Startzeit im Simulationszeitmodell, Seed, Tick-Groesse und
> aktivierte Adapter.

Der *testbare* Determinismus-Vertrag traced auf [`GG-AR-P-008`](../../../../spec/architecture.md#2-architekturprinzipien)
([`GG-SIM-001`](../../../../spec/lastenheft.md#gg-sim-001)/002/003, [`GG-RT-002`](../../../../spec/lastenheft.md#gg-rt-002)); [`GG-TERM-002`](../../../../spec/lastenheft.md#gg-term-002)/003 liefern die
normative Feld-/Akzeptanz-Definition (n/a in der Impl-Matrix,
Lastenheft Z. 2231, Stand 2026-07-03).

## Carveout-Stand (M7-Welle-1b-a-C0 2026-06-09)

M7-Welle-1b implementiert per **1b-a-D-6** nur einen **MVP-E2E-
Replay-Preflight** ueber die bereits stabil strukturierten
`RunMetadata`-Felder:

- ✓ `scenario_hash`
- ✓ `schema_version`
- ✓ `seed`
- ✓ `tick_ms`
- ✓ `tool_version`

Preflight-Vertrag (formal in [`ADR 0049`](../../adr/0049-replay-lifecycle-finalize-hook.md), 1b-b): „Replay-Diff wird
nur ausgefuehrt, wenn die vorhandenen deterministischen
Vergleichsmetadaten gleich sind; fehlende Vollfelder bleiben als
dokumentierter [`GG-TERM-002`](../../../../spec/lastenheft.md#gg-term-002)/003-Carveout offen." Boundary-Pins
einzeln fuer die 5 Felder (1b-b).

**Stand-Update (2026-07-03, nach Slice 039/040):**

- `RunMetadata` traegt inzwischen zusaetzlich `replay_of`
  ([`ADR 0068`](../../adr/0068-api-replay-binding-persistence.md), Slice 039); die zugehoerige Alembic-Migration
  `0003_add_replay_of.py` ist das Vorbild fuer den
  Add-Column-Pfad dieses Slices.
- `finalize()` feuert seit Slice 040 auch auf der
  Headless-Run-End-Naht ([`ADR 0067`](../../adr/0067-run-end-seam-and-partial-run.md), `run_session()`-
  Kontextmanager) — der Preflight greift damit auf beiden
  Exit-Pfaden.
- Der Vergleichspunkt selbst bleibt zentral:
  `_REPLAY_PREFLIGHT_FIELDS` in
  `src/grid_gym/hexagon/core/simulation/tick_loop.py` — die
  Feld-Erweiterung ist ein Single-Point-Change, die Hauptarbeit
  liegt in Quellen-Anbindung, Kanonik und Boundary-Tests.

## Offene Vollfelder (dieser Trigger)

Die folgenden Lastenheft-Pflichtfelder sind **noch nicht**
strukturiert in `RunMetadata` verankert und damit **nicht** im
1b-Preflight:

- ✗ **Plattformarchitektur** (`platform_arch`).
- ✗ **Aktivierte Adapter / Adapterprofile** (`enabled_adapters`) —
  **Quellen-Luecke:** es gibt keinen Adapter-Registry-/Profil-
  Begriff im Code; der Wert muss aus der Composition-Root-
  Verdrahtung oder einer expliziten Profil-Konfiguration
  abgeleitet werden (C0-Entscheidungspunkt E-2).
- ✗ **Startzeit im Simulationszeitmodell** (`sim_start_time`) —
  heute nur Wall-Clock `started_at`/`ended_at`
  (`src/grid_gym/hexagon/core/domain/run.py`), nicht
  Simulationszeit. **Quellen-Luecke:** das Szenario-Schema
  (`ScenarioSimulation`: `tick_ms`/`duration_s`/`seed`) kennt
  keine Run-Level-Startzeit; Simulationszeit ist tick-indiziert
  und startet implizit bei 0 (`start_simulation_time` existiert
  nur als Fault-Eintrags-Feld). Der Wert kann also nirgends
  „strukturiert" werden — er muss erst definiert werden
  (C0-Entscheidungspunkt E-1).
- ✗ **Separater kanonischer Konfigurations-Hash** (`config_hash`)
  ueber `scenario_hash` hinaus.

## C0-Entscheidungspunkte (entschieden 2026-07-03, [`ADR 0073`](../../adr/0073-gg-term-full-equality-matrix-runmetadata.md))

- **E-0 Speicherort → `RunMetadata`-Erweiterung** (kein Envelope;
  Praezedenz `replay_of`) — [`ADR 0073`](../../adr/0073-gg-term-full-equality-matrix-runmetadata.md) §2.1.
- **E-1 `sim_start_time` → Option (b), Konstante `0`** (ms;
  `simulation_time` ist definiert als „ms ab Lauf-Start", kein
  Kalenderzeit-Anker; Scenario-Feld waere `schema_version`-Kaskade)
  — [`ADR 0073`](../../adr/0073-gg-term-full-equality-matrix-runmetadata.md) §2.2.
- **E-2 `enabled_adapters` → statische Composition-Root-
  Deklaration** (kanonische Package-Namen, dedupliziert +
  lexikografisch sortiert, komma-separiert persistiert; NICHT
  Wiring-Introspection, da API-Laeufe die Metadata vor dem Wiring
  persistieren) — [`ADR 0073`](../../adr/0073-gg-term-full-equality-matrix-runmetadata.md) §2.3.
- **E-3 `config_hash` → versionierte ConfigView v1**
  (`sha256(canonical_json({config_view: 1, max_age_ms}))`;
  Aufnahme-Pflicht fuer neue determinismus-relevante Runtime-
  Knobs) — [`ADR 0073`](../../adr/0073-gg-term-full-equality-matrix-runmetadata.md) §2.4.
- **NEU Fehlend-Reject:** leere Vollfelder (`""`/`()`) sind auf
  beiden Seiten Reject-Grund `missing` — leer==leer ist KEIN
  valider Vergleich (Legacy-/Bare-Adapter-Laeufe fail-closed) —
  [`ADR 0073`](../../adr/0073-gg-term-full-equality-matrix-runmetadata.md) §2.6.

## Substanz-Skizze (bei Aufloesung)

- `RunMetadata`-Erweiterung **oder** NEU `ReplayComparisonMetadata`-
  Envelope (Speicherort-Entscheidung im aufloesenden C0).
- Alembic-Migration fuer die neuen Felder.
- Canonicalization-Regeln (`platform_arch`-Normalform,
  `enabled_adapters`-Sortier-Kanonik, `sim_start_time`-Format,
  `config_hash`-Hash-Verfahren) — Reject-Semantik fuer fehlende/
  abweichende Werte **vor** Diff-Klassifikation.
- Parametrisierte Boundary-Tests pro Vollfeld (ein generischer
  Mismatch-Test reicht nicht).
- [`ADR-0011`](../../adr/0011-schaerfung-ohne-abloesung.md)-Schaerfung an [`ADR 0049`](../../adr/0049-replay-lifecycle-finalize-hook.md) (additiv zum Preflight-
  Vertrag, kein Bruch).

## §T Tranchen-Plan (aktiviert 2026-07-03)

| Tranche | Rolle | Inhalt | Status |
| ------- | ----- | ------ | ------ |
| C0 | Architect | Entscheidungen E-0..E-3 + Fehlend-Reject; NEU [`ADR 0073`](../../adr/0073-gg-term-full-equality-matrix-runmetadata.md) `Provisional` ([`ADR-0011`](../../adr/0011-schaerfung-ohne-abloesung.md)-Schaerfung an [`ADR 0049`](../../adr/0049-replay-lifecycle-finalize-hook.md) §2.3); ADR-Index + 0049-Schaerfungs-Vermerk | **done** 2026-07-03 |
| C1 | Implementation | `RunMetadata`-Vollfelder + Kanonik-Regeln + Alembic-Migration `0004` + InMemory-/Postgres-Repos + Unit-Tests | offen |
| C2 | Implementation | `_REPLAY_PREFLIGHT_FIELDS`-Erweiterung + Reject-Semantik + parametrisierte Boundary-Tests pro Vollfeld | offen |
| C3 | Verifier | Public-Contract-Sync (Traceability, `persistence-schema.yaml`, CHANGELOG) + Replay-/Verification-Evidence | offen |
| C4 | Planner | DoD-Checkliste, Release-Entscheidung (ja, minor), `make fullbuild`, Tag, Self-Move nach `done/` | offen |

## DoD-Checkliste (mit C4 abzuhaken)

- [ ] Alle 4 Vollfelder strukturiert in `RunMetadata` + Persistenz
      (Alembic-Migration, beide Repository-Adapter).
- [ ] Kanonisierungs-Regeln implementiert und im Folge-ADR fixiert;
      Reject-Semantik fuer fehlende/abweichende Werte **vor**
      Diff-Klassifikation.
- [ ] Preflight vergleicht 9 Felder; parametrisierte Boundary-Tests
      pro Vollfeld gruen.
- [ ] Folge-ADR `Accepted`; ADR-Index aktualisiert.
- [ ] Replay-Evidence ([`harness/replay.md`](../../../../harness/replay.md)) +
      Verification-Evidence ([`harness/verification.md`](../../../../harness/verification.md)) festgehalten.
- [ ] `make gates` + `make docs-check` gruen; vor Tag `make fullbuild`.
- [ ] Release-Entscheidung vollzogen (ja, minor: `pyproject`-Bump +
      CHANGELOG-Finalisierung + `v*.*.*`-Tag) — Runtime-Delta-Pflicht
      erfuellt.
- [ ] Self-Move nach `done/` (reiner `git mv`) + Link-/Bestand-Pflege.

## Wandert nach

`done/`, sobald die volle [`GG-TERM-002`](../../../../spec/lastenheft.md#gg-term-002)/003-Matrix strukturiert,
kanonisiert und per-Feld-Boundary-getestet im Replay-Preflight
verankert ist.

## References

- [`../done-archive/M7-welle-1b-a.md`](../done-archive/M7-welle-1b-a.md)
  — 1b-a-D-6 (Equality-Scope-Beschluss + Carveout-Begruendung).
- [`../done-archive/M7-welle-1.md`](../done-archive/M7-welle-1.md)
  — [`GG-MVP-002`](../../../../spec/lastenheft.md#gg-mvp-002)-Gruppenplan (§2.5 + R4 auf Preflight korrigiert).
- [`../../../../spec/lastenheft.md`](../../../../spec/lastenheft.md#gg-mvp-002)
  — [`GG-TERM-002`](../../../../spec/lastenheft.md#gg-term-002)/[`GG-TERM-003`](../../../../spec/lastenheft.md#gg-term-003) normative Definitionen.
- [`../../adr/0011-schaerfung-ohne-abloesung.md`](../../adr/0011-schaerfung-ohne-abloesung.md)
  — Schaerfungs-Pattern fuer die additive Vollausbau-ADR.
