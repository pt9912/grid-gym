# Harness-Konventionen

Diese Datei deklariert die *repo-lokalen* Strukturregeln von `grid-gym`
gegenueber der adoptierten Harnesskonvention (Baseline) und die
Abweichungen ggue. dieser Baseline. Sie ist **Pflicht** (Existenz); ihre
Form (Einzeldatei, ADR-artiger Adaptions-Block) ist hier bewusst gewaehlt.

Bei Konflikt zwischen dieser Datei und einer kanonischen Quelle gilt die
kanonische Quelle (Source Precedence in [`harness/README.md`](README.md)).
Diese Datei ist autoritativ fuer *Form*-Fragen, nicht ueber *Inhalt*.

## Purpose

Default-Ort fuer:

- **Adaptionen** ggue. der Baseline (`MR-<NNN>`, mit Begruendung und
  Aufloesungs-Trigger).
- **ID-Schema-Deklaration** — welches Praefix-Schema dieses Repo nutzt
  (`MR-000`).
- **Zusatzklassen-Deklarationen** fuer repo-spezifische Bindung-Klassen
  der Sensors-Tabelle jenseits der vier kanonischen.
- **Modus-Deklarationen** pro Sub-Area (Greenfield / Brownfield / Hybrid).

Diese Datei **dupliziert keinen Baseline-Text** — sie verweist und
ergaenzt. Eine Kopie ginge gegen die Baseline in Drift, sobald letztere
sich weiterentwickelt.

## Baseline

- **Konvention:** AI-Harness-Kurs (`pt9912/ai-harness-course`) — das
  operative Agenten-Regelwerk und die verkoerperten Lab-Templates.
- **Stand:** Release `v1.2.0` · 2026-06-16 (Tag-gepinnt; Commit
  `0473cc55ff5df8afc4b473635f3ef78de25f2714`).
- **Datum der Adoption:** 2026-06-13.
- **Baseline-Update:** 2026-06-18 — Pin `templates-v2`/`47af124` →
  `v1.2.0`/`0473cc55` nach Delta-Analyse (kein Inhaltskonflikt mit
  `MR-000..005`; die konkrete Source-Precedence-Rangwahl bleibt laut v1.2.0
  Repo-Sache, deklariert in `MR-001`/`MR-002`).

## Adoptierte Konventions-Quellen

Pointer auf die Baseline — **keine** Wiederholung des Inhalts. Hart auf
den Tag/Commit gepinnt fuer Reproduzierbarkeit (nicht `main`):

- **Agenten-Regelwerk (operativ, fuer Code-Agenten):**
  [agents-regelwerk.md @ `v1.2.0`](https://github.com/pt9912/ai-harness-course/blob/v1.2.0/kurs/de/agents-regelwerk.md)
  — Raw-Pin:
  `https://raw.githubusercontent.com/pt9912/ai-harness-course/0473cc55ff5df8afc4b473635f3ef78de25f2714/kurs/de/agents-regelwerk.md`.
  Modul-aufgeteiltes Bundle:
  [`lab-regelwerk.zip` @ Release `v1.2.0`](https://github.com/pt9912/ai-harness-course/releases/download/v1.2.0/lab-regelwerk.zip)
  (17 Module + 3 Grundlagen-Digeste). Derivativ — bei Konflikt gilt das
  Lehrmaterial.
- **Lehrmaterial (Module 00–16 + grundlagen):**
  [`kurs/de/` @ `v1.2.0`](https://github.com/pt9912/ai-harness-course/tree/v1.2.0/kurs/de).
- **Verkoerperte Form (Templates):**
  [`lab-templates.zip` @ Release `v1.2.0`](https://github.com/pt9912/ai-harness-course/releases/download/v1.2.0/lab-templates.zip)
  (Commit `0473cc55ff5df8afc4b473635f3ef78de25f2714`).

## Adaptions-Block

ADR-artige Liste der Abweichungen ggue. Baseline. Chronologisch
nummeriert; akzeptierte Eintraege werden nicht inhaltlich umgeschrieben,
nur durch neue `MR-<NNN>` aufgehoben.

### MR-000 — Baseline-Aussage und ID-Schema

- **Datum:** 2026-06-13
- **Geltungsbereich:** gesamtes Repo
- **Adaption:** Repo-weites ID-Praefix ist `GG-` (von „grid-gym") statt
  des Baseline-Beispiels `LH-`. Konkret: `` `GG-FA-*` ``/`` `GG-QA-*` ``
  und die Domaenen-Familien (`` `GG-DEV-*` ``, `` `GG-BESS-*` ``,
  `` `GG-SAFE-*` `` u. a.) im Lastenheft; `` `GG-AR-*` `` fuer
  Architektur-IDs (Sicht-Stratum); `` `ADR-<NNNN>` ``,
  `` `AC-*` `` (ADR-Acceptance-Kriterien), `MR-<NNN>`, `slice-<NNN>`.
  Das Schema ist maschinell ueber [`.d-check.yml`](../.d-check.yml)
  (`ids`-Modul) und [`ADR-0004`](../docs/plan/adr/0004-identifier-based-cross-references.md)
  durchgesetzt.
- **Begruendung:** Praefix ist laut Baseline explizit Repo-Wahl; `GG-`
  ist die seit M1 gewachsene, in Lastenheft, ADRs, Commits und Gates
  verankerte Klammer.
- **Aufloesungs-Trigger:** permanent.

### MR-001 — Source Precedence mit eigenen Rangstufen

- **Datum:** 2026-06-13
- **Geltungsbereich:** [`harness/README.md`](README.md) §Source Precedence
- **Adaption:** Die Precedence-Tabelle fuehrt zehn Raenge statt der
  Baseline-Default-Acht. Eingefuegt sind:
  (a) [`spec/protocol_profiles.md`](../spec/protocol_profiles.md) als
  eigener Rang 3 (Technik-Stratum, siehe `MR-002`);
  (b) die *ausfuehrbaren* Vertraege
  [`Makefile`](../Makefile)/[`Dockerfile`](../Dockerfile)/[`pyproject.toml`](../pyproject.toml)/`.github/workflows/`
  als eigener Rang 6 (zwischen ADR/Planung und `docs/user/`).
- **Begruendung:** Drei-Schichten-Spec
  (Lastenheft › Architektur › Protokollprofile) bildet die
  ADR-Schaerfungs-Regel strukturell ab; die ausfuehrbaren Build-/Gate-
  Vertraege sind in einem Docker-only-Repo normative Realitaet und
  ranken ueber der erzaehlenden Nutzerdoku.
- **Aufloesungs-Trigger:** permanent.

### MR-002 — Technik-Stratum ist `protocol_profiles.md`

- **Datum:** 2026-06-13
- **Geltungsbereich:** [`spec/`](../spec/)
- **Adaption:** Das Technik-Stratum (Baseline-Beispiel
  `spec/spezifikation.md`) <!-- d-check:ignore (Baseline-Beispielpfad; existiert hier bewusst nicht, MR-002) --> wird von
  [`spec/protocol_profiles.md`](../spec/protocol_profiles.md) getragen;
  eine eigene Spezifikations-Datei existiert bewusst nicht. Straten-
  Zuordnung: Vertrag = [`spec/lastenheft.md`](../spec/lastenheft.md)
  (`` `GG-FA-*`/`GG-QA-*` ``), Technik =
  [`spec/protocol_profiles.md`](../spec/protocol_profiles.md), Sicht =
  [`spec/architecture.md`](../spec/architecture.md) (`` `GG-AR-*` ``,
  keine eigenen Anforderungs-IDs).
- **Begruendung:** Die einzige technische Fortschreibung jenseits von
  Lastenheft und Architektur betrifft Adapter-Protokollprofile; ein
  leeres `spezifikation.md` waere eine stille Setzung. Das Technik-
  Stratum ist laut Baseline optional und darf in einer fachlich
  benannten Datei wohnen.
- **Aufloesungs-Trigger:** permanent (Re-Eval, falls technische
  Festlegungen jenseits der Protokollprofile entstehen).

### MR-003 — Carveout-Form: ein Cross-Meilenstein-Index statt Datei-pro-Carveout

- **Datum:** 2026-06-13
- **Geltungsbereich:** Carveout-Disziplin
- **Adaption:** Statt des Baseline-Verzeichnisses `docs/plan/carveouts/` <!-- d-check:ignore (Baseline-Pfad; dieses Repo nutzt das Index-Modell, MR-003) -->
  mit einer Datei pro Carveout fuehrt das Repo **einen** lebenden Index
  [`docs/plan/planning/in-progress/carveouts.md`](../docs/plan/planning/in-progress/carveouts.md)
  mit einer Vier-Typen-Taxonomie (`Deferred`, `Trigger-Gated`,
  `Out-of-Scope`, `Pattern-Forward`). Formale, watch-pflichtige Carveouts
  bekommen zusaetzlich ein Trigger-Doc unter
  [`docs/plan/planning/open/`](../docs/plan/planning/open/) (Datei
  `NNN-*.md`; im Index per ID `T-nnn` referenziert).
  Per-Welle-Anti-Scope und Pro-Meilenstein-Erbschaft leben in den
  jeweiligen [`done/`](../docs/plan/planning/done/)-Wellendocs.
- **Begruendung:** Carveout-Form ist laut Baseline Repo-Wahl. Bei
  Dutzenden meilenstein-uebergreifender Scope-Entscheidungen gibt ein
  einziger Index die geforderte „rot dokumentieren, nicht verstecken"-
  Sicht, ohne dass Reviewer drei `M-results`-Docs und 20+ Trigger-Docs
  querverlinken muessen. Aufloesungs-Trigger und Folge-Slice bleiben pro
  Eintrag erhalten (Carveout-Disziplin des Regelwerks).
- **Aufloesungs-Trigger:** Re-Eval, falls der Index ≥ 50 Eintraege wird
  (Split-Konvention in `carveouts.md` §4).

### MR-004 — harness/ als Mehrdatei-Bundle

- **Datum:** 2026-06-13
- **Geltungsbereich:** [`harness/`](.)
- **Adaption:** Die Baseline-Pflichtsektionen von `harness/README.md`
  zu Rollen, Review und Verifikation sind in dedizierte Dateien
  ausgelagert: [`harness/roles.md`](roles.md),
  [`harness/review.md`](review.md), [`harness/verification.md`](verification.md)
  und zusaetzlich [`harness/replay.md`](replay.md) (Replay-/Golden-
  Regeln). `harness/README.md` bleibt der Einstieg und verweist auf sie.
- **Begruendung:** Die Sektionen sind je eigene Uebergabe-Vertraege
  (Reviewer-Output-Schema, Verification-Evidence-Schema) und wachsen
  unabhaengig; getrennte Dateien halten `README.md` als Index lesbar.
  Es entsteht keine Inhaltsduplikation — `README.md` zeigt nur Pointer.
- **Aufloesungs-Trigger:** permanent.

### MR-005 — Sensors-Tabelle ohne separate Bindung-Spalte

- **Datum:** 2026-06-13
- **Geltungsbereich:** [`harness/README.md`](README.md) §Sensors
- **Adaption:** Die Sensors-Tabelle nutzt die Spalten
  `Target | Charakter | Wann verwenden` statt des Baseline-Schemas
  `Target | Vertrag | Bindung`. Die Bindung eines Gates an seine Quelle
  wird **inline** ausgedrueckt — per Link auf den begruendenden ADR
  (z. B. `make typecheck` →
  [`ADR-0005`](../docs/plan/adr/0005-type-check-gate.md)) bzw. auf den
  Carveout-Index, nicht in einer eigenen Spalte. Strukturell rote Gates
  werden als `Trigger-Gated`-Eintrag in
  [`carveouts.md`](../docs/plan/planning/in-progress/carveouts.md)
  dokumentiert, nicht in einer Status-Spalte.
- **Begruendung:** Die kanonische Lauf-Wahrheit lebt in CI, nicht in der
  Tabelle; eine `Wann verwenden`-Spalte ist fuer Agenten der
  handlungsleitendere Schluessel als eine Bindung-Spalte, solange jede
  Bindung per ADR-/Carveout-Link nachweisbar bleibt.
- **Aufloesungs-Trigger:** Re-Eval, falls Gates ohne ADR-/Carveout-Link
  auftauchen (dann waere eine explizite Bindung-Spalte faellig).

## Zusatzklassen-Deklaration fuer Sensors-Bindung

Die vier kanonischen Bindung-Klassen (ADR, Carveout, Schwelle,
Reproduzierbarkeit) genuegen — **keine Zusatzklassen.** Bindungen werden
inline per Link gefuehrt (siehe `MR-005`):

- *ADR-Bindung* — z. B. `make typecheck` ↔
  [`ADR-0005`](../docs/plan/adr/0005-type-check-gate.md).
- *Carveout-/Reproduzierbarkeits-Bindung* — z. B. der vulnignore-
  Temp-Deferral des OTel-Collector-Images ↔ Trigger `T-033` im
  [Carveout-Index](../docs/plan/planning/in-progress/carveouts.md).
- *Schwellen-Bindung* — `make coverage-gate` traegt die Schwelle im
  Target selbst (Wert nicht hier dupliziert — Quelle ist das
  [`Makefile`](../Makefile)).

## Modus-Deklaration pro Sub-Area

`grid-gym` wurde als **Greenfield**-Referenzimplementierung des Kurses
gebootstrappt (Doc fuehrt, Code folgt) und ist mit M7 / Release v0.1.0 im
**Steady-State**. Es gibt aktuell **keine** Brownfield-Sub-Area und damit
keinen Konvergenz-Backlog; eine spaetere BF-Sub-Area (z. B. ein
Alt-Port mit Bestandscode) bekaeme hier eine eigene Zeile **mit**
Graduation-Bedingung.

| Sub-Area (Pfad / Modul) | Modus | Begruendung | Graduation / Folge |
|---|---|---|---|
| `*` (Default, gesamtes Repo) | Greenfield | Spec/ADR fuehren, Code folgt; Steady-State seit M7. | n/a (GF) |
| [`src/grid_gym/hexagon/`](../src/grid_gym/hexagon/) (core + ports) | Greenfield | Fachlogik folgt Lastenheft + Architektur; Determinismus ist Produktvertrag. | n/a (GF) |
| [`src/grid_gym/adapters/`](../src/grid_gym/adapters/) (driving + driven) | Greenfield | Adapter folgen Architektur-Ports und [`protocol_profiles.md`](../spec/protocol_profiles.md). | n/a (GF) |
| [`spec/`](../spec/) + [`docs/plan/adr/`](../docs/plan/adr/) | Greenfield | Kanonische Quellen; Aenderung nur ueber Change-Process / Folge-ADR. | n/a (GF) |
| [`docs/plan/planning/`](../docs/plan/planning/) | Greenfield | Slice-Lifecycle `open/ → next/ → in-progress/ → done/`. | n/a (GF) |
| Tooling/Build (`Makefile`, `Dockerfile`, `pyproject.toml`, `.github/`) | Greenfield | Gates/CI folgen ADRs (z. B. [`ADR-0005`](../docs/plan/adr/0005-type-check-gate.md)). | n/a (GF) |
| [`tests/`](../tests/) | Greenfield | Tests tragen `GG-*`-Bezug; Determinismus-/Replay-/Fault-Marker. | n/a (GF) |
| [`deploy/`](../deploy/) | Greenfield | Compose-/Runtime-Artefakte folgen `GG-DEPLOY-*`. | n/a (GF) |

## Glossar (repo-spezifisch)

Nur Begriffe, die das Kurs-Glossar nicht traegt:

| Begriff | Bedeutung in `grid-gym` |
|---|---|
| Welle-Self-Close | Konvention, dass eine Welle ihre eigene Closure traegt (Slice-Lifecycle, [`docs/plan/planning/README.md`](../docs/plan/planning/README.md)). |
| Trigger-Doc | Formal akzeptierter Carveout-Watch unter [`open/`](../docs/plan/planning/open/) (Datei `NNN-*.md`) mit Aktivierungs-Bedingung; im Carveout-Index per ID `T-nnn` referenziert (siehe `MR-003`). |
| M{N}-Erbschaft | Pro-Meilenstein aggregierte Carveout-/Scope-Erbschaft in den `done/M{N}-results.md §5/§8`. |
