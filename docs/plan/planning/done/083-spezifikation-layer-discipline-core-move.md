# 083 — Spezifikations-Schicht: Fundament + Disziplin-Kern-Umzug (PRINC/CC/SEED)

**Status:** **Abgeschlossen (`done/`, 2026-07-16).** Erster Slice des
Migrations-Arcs (Spec-Schichtung); atomarer Vertrag-Cut **ausgeführt**. Erster
Slice führt [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §4.4 Schritt
**(i)** „Residuum-Umzug nach spezifikation.md" für den harten Kern aus und legt
die neue Schicht an. **Doku-/Config-only → kein Release.**
**Datum:** 2026-07-16
**Quelle:** [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) `Accepted`
(Dreischicht-Spec-Modell), §4-Detailentscheidungen mit Owner ratifiziert
(`9e62ee2`).

> **Closure / Verifikation (2026-07-16).** Umgesetzt: `spec/spezifikation.md`
> angelegt (V-Modell-Pflichtenheft mit `GG-PRINC-*`, `GG-CC-*`, `GG-SEED-*` +
> Werkzeug-Durchsetzung + Sektion „5. Offene Spezifikationspunkte" mit
> `GG-SPEC-OPEN-001`); §5.1 + `GG-SEED-*` aus `lastenheft.md` entfernt
> (Vertrag anforderungsrein, verifiziert self-ref-frei); §27.1-PRINC/CC-Residuum
> (14 Zeilen) + §27.1.1-SEED-Zeile aus `traceability.md` entfernt; **40**
> Markdown-Links `lastenheft.md#…` → `spezifikation.md#…` repointet (5 ADRs +
> `architecture.md` + `docs/user/code-review.md` + Slice-Docs); `.d-check.yml`:
> `matrix`-Klasse `technik`→`spezifikation` (beide Pfade) **inkl.
> `matrix.rules`-Rename**, höher-priorisiertes `ids`-Muster
> `GG-(PRINC|CC|SEED)-\d{3}`→spezifikation.md + `GG-SPEC-OPEN`, `exclude-sections`
> += „5. Offene Spezifikationspunkte", `trace`-Kommentar nachgezogen.
> **SDP-Erkenntnis:** `spezifikation.md` darf weder `GG-AR-*` noch `ADR NNNN`
> referenzieren (beides abwärts/`matrix-forbidden`); die Realisierung trägt reine
> Werkzeug-Prosa, die GG-AR-Kopplung bleibt architecture.md-Aufwärts-Bezug.
> **Gates:** `make docs-check` (303 Dateien, 0 Befunde) + `make gates` grün;
> gate-blinder Sweep = 17 Refs, alle unverändert-gültig (Prefixe bleiben → kein
> Bruch; PR-Template-§3.x zeigt auf `code-review.md`, keine Drift).
>
> **Review (adversarial, vor Commit):** Content-Fidelity aller 15 Anforderungstexte
> verbatim; Cut/SDP/Repoint/`.d-check.yml`/Anker sauber, **blocker-frei**. Ein
> gate-unsichtbarer Fund: das per
> [`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md) §2 sanktionierte
> Link-Repointen in [`ADR 0005`](../../adr/0005-type-check-gate.md) ließ umgebende
> Prosa stehen, die nun „§27.1-Zeilen in `lastenheft.md`" behauptet (durch 083
> entfernt). **Bewusst nicht geglättet:**
> [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) §3
> + [`ADR 0028`](../../adr/0028-link-maintenance-accepted-adr-bezug.md) §7 verbieten
> inhaltliche Accepted-ADR-Edits jenseits des Pfad-Links; die Prosa-Drift ist damit
> akzeptierte Immutabilitäts-Historie (gleiche Klasse wie nach Slice 063). Gilt auch
> für die Präsens-Motivationsprosa in
> [`ADR 0080`](../../adr/0080-three-layer-spec-model.md).
>
> **Nachtrag (Owner-Korrektur, 2026-07-16):** Die anfangs angelegte Sektion „5. Offene
> Spezifikationspunkte" (`GG-SPEC-OPEN-*`, Schritt 1 / ADR §4.5) wurde **wieder
> entfernt** — `spezifikation.md` beschreibt das *Soll*; offene Prozess-/Tooling-Punkte
> gehören in die Planung, nicht in die Spec. Betroffen: `spezifikation.md` (§5 raus),
> `.d-check.yml` (`GG-SPEC-OPEN`-`ids`-Regel + exclude-section raus), Slice 086
> (§27.1-Generator/Gate als eigene Vertagung statt `GG-SPEC-OPEN`),
> [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §4.5 (zurückgenommen-annotiert).
> `architecture.md`-§19 (`GG-AR-OPEN-*`) folgt aus demselben Prinzip als eigener
> Bereinigungs-Slice.

---

## Motivation

Der Vertrag (`lastenheft.md`) vermischt echte Anforderungen mit
Spezifikations-/Disziplin-Inhalt. Die Familien `GG-PRINC-*` (SOLID) und
`GG-CC-*` (Clean-Code) sind der **harte Kern** — klar Spezifikation, interne
Disziplin (ADR §1/§2b), kein Grenzfall.
[`GG-SEED-001`](../../../../spec/spezifikation.md#gg-seed-001) ist der **einzige
Grenzfall** der Scope-Familien: interne Determinismus-/Test-Konvention, Wesen wie
`GG-CC-*`, entschieden nach Spezifikation (ADR §4.2a).

Ihre Realisierung (`ruff`/`mypy`-Durchsetzung) lebt heute als **Residuum** in der
advisory-RTM `traceability.md` §27.1 (Z. 63–76) — dem einzigen genuin
einzigartigen Inhalt dort. Dieser Slice macht sie **erstklassig** in der neuen
Schicht statt RTM-Beifang.

## Betroffene Kennungen

- **Umzug (Definition + Realisierung):** `GG-PRINC-*` (001–006), `GG-CC-*`
  (001–008), [`GG-SEED-001`](../../../../spec/spezifikation.md#gg-seed-001)
  (15 IDs).
- **Neue Datei:** die Spezifikations-Schicht (V-Modell-Pflichtenheft), neue
  `matrix`-Klasse `spezifikation` (Geschwister zu `spec/protocol_profiles.md`,
  ADR §4.1).
- **Neue Familie:** `GG-SPEC-OPEN-*` (Offene Spezifikationspunkte, analog
  `GG-AR-OPEN-*`, ADR §4.5). Seed: `GG-SPEC-OPEN-001` = §27.1-Generator-Promotion
  nach Bezug-Stabilisierung (ADR §4.4 iv, in Slice 086 adressiert).
- **Prefixe bleiben** (ADR §4.3) — kein `GG-SPEC-*`-Rename; nur `ids`-Ziel
  umbiegen.

## Umfang / Erwartete Lieferung (atomarer Vertrag-Cut)

1. **Anlegen** der Datei spezifikation.md
   (`spec/spezifikation.md` <!-- d-check:ignore (geplant: entsteht in diesem Slice) -->):
   - V-Modell-Kopf (Pflichtenheft, `WIE-funktional/QS`); SDP-Aufwärts-Bezug auf
     `lastenheft.md`, **seitwärts** auf `protocol_profiles.md` (schicht-intern,
     ADR §4.1).
   - Sektion **„Offene Spezifikationspunkte"** (`GG-SPEC-OPEN-*`, Tabelle
     ID | Frage | Status), geseedet mit `GG-SPEC-OPEN-001`.
2. **Umzug** von `GG-PRINC-*` / `GG-CC-*` (aus `lastenheft.md` §5.1, Z. ~281–403)
   **+** [`GG-SEED-001`](../../../../spec/spezifikation.md#gg-seed-001) (Z. ~113,
   separater Excision-Punkt oben im Rahmen-Teil). Definition **und** die
   §27.1-Residuum-Realisierung (`ruff PLR0904`/`mypy`/… → Prinzip) wandern als
   spezifikationseigener Inhalt mit.
3. **Cut** der Sektionen aus `lastenheft.md`; Vertrag bleibt anforderungsrein.
4. **Repoint** aller ~35 brechenden Markdown-Links auf die neuen Anker
   (Ziel spezifikation.md statt `lastenheft.md`). Repoint-Fläche vollständig:
   `architecture.md`-Bezug (PRINC/CC **nicht nur** §2/§4-Tabus, sondern auch
   §4.2-Ports [Z. 244 [`GG-AR-PORT-DRN-009`](../../../../spec/architecture.md#driven-ports-vom-kern-aufgerufen)→PRINC-005] und §7-Domain-Prosa [Z. 465
   CC-007] — zeigen **aufwärts** auf die Spezifikations-IDs, SDP-konform, s.
   Design-Entscheidung 2); `docs/user/code-review.md`; historische Slices in
   `done/` (reine Anker-Hygiene); ADR-Links in 8 ADR-Dateien (mechanische Hygiene,
   von [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §3 sanktioniert —
   **kein** ADR-/Slice-Entscheidungsinhalt geändert).
5. **Gate-blinder Konfidenz-Sweep** (manuell, docs-check prüft `src/**`/`.github/**`
   **nicht**): `src/`, `tests/`, `.github/`, `pyproject.toml`, `Makefile` — **~17**
   PRINC/CC/SEED-Refs (SEED-001×4, CC-001×5, CC-005×2, CC-006/08, PRINC-002/04, PRINC-005×2).
   **Weil die Prefixe bleiben (ADR §4.3), brechen diese Klartext-Refs nicht** (der
   ID-String bleibt identisch) — der Sweep ist Konfidenz-/Kontext-Prüfung (zeigt die
   Referenz noch auf die gemeinte Familie?), keine Reparatur. **Ausnahme:**
   Sektionsnummer-Refs (z. B. `.github/PULL_REQUEST_TEMPLATE.md` „§3.x GG-CC-…")
   driften mit der neuen Datei-Nummerierung → auf ID-only prüfen/umstellen.
6. **d-check-Config** (`.d-check.yml`):
   - `matrix.classes`: `technik` → `spezifikation` mit **beiden** Pfaden
     (`spec/protocol_profiles.md` + die neue Datei). **Zwingend mitziehen:** die
     vier `matrix.rules`-Einträge, die `technik` nennen (`contract→technik`,
     `technik→sicht`, `technik→adr`, `technik→slice`), auf `spezifikation`
     umbenennen — sonst zeigen sie ins Leere und die Kante `spezifikation→sicht
     (allow:false)`, auf die Design-Entscheidung 2 baut, verschwindet still.
   - `ids.patterns`: höher-priorisiertes Muster `GG-(PRINC|CC|SEED)-\d{3}` →
     spezifikation.md **über** der generischen `lastenheft.md`-Regel.
   - `matrix.exclude-sections` += die **exakte** Überschrift inkl. Nummer
     (Präzedenz-Form: `"19. Offene architektonische Punkte"`), also z. B.
     `"N. Offene Spezifikationspunkte"` — ein un-numerierter String matcht sonst
     nicht und die `GG-SPEC-OPEN-*`-Zeilen dürfen ihre auflösende ADR nicht
     *abwärts* zitieren (`matrix-forbidden`).
   - `ids`: `GG-SPEC-OPEN-*` in ein spezifikation.md-Ziel aufnehmen; als Meta
     **außerhalb** des `trace`-`id-pattern` halten (wie ARCH/OPEN).
   - **`trace`-Ausnahme-Kommentar** (Z. 103–107) mitziehen: er begründet den
     Ausschluss von SEED/PRINC/CC mit „via traceability.md abgedeckt" — nach dem
     Umzug „via spezifikation.md" (das Regex selbst bleibt unverändert, kein
     RTM-Waise).
7. **§27.1.1**: SEED-Zeile entfernen (SEED ist jetzt Spezifikation, kein
   „Anforderung ohne Design-Artefakt" mehr).

## Design-Entscheidungen / Risiken (im Slice zu dokumentieren)

1. **§27.1-Zeilen für PRINC/CC — differenziert:** die Familien verlassen den
   Vertrag → sie sind keine contract-`Anforderung` mehr, ihre §27.1-Zeilen
   (Z. 63–76) entfallen aus der anforderungs-indizierten Tabelle. **Nur wo
   architecture.md heute schon aufwärts zeigt** (PRINC-005 §4.2, PRINC-006 §2/
   §4-Tabus, CC-002/03/04/06/07/08 §4-Tabus) bleibt die Design-Beziehung als
   **architecture.md-Bezug-Aufwärtszeiger** erhalten (Design-Entscheidung 2). Für
   **PRINC-001..004 / CC-001 / CC-005** (kein architecture.md-Zeiger) **entfällt die
   Design-Zuordnung ersatzlos** — ihre Realisierung ist die Werkzeug-Durchsetzung,
   die selbst-enthalten nach spezifikation.md wandert (es geht keine Traceability
   „verloren", die es gab; nichts wird fälschlich als „rekonstruierbar" behauptet).
   Die endgültige §27.1-Modell-Fassung (authored→derived) macht **Slice 086**; 083
   nimmt die PRINC/CC-Zeilen nur heraus.
2. **SDP-Richtung — kein Abwärts-Verweis aus der Spezifikation:** spezifikation.md
   ist SDP-**oberhalb** von `architecture.md` (`contract > spezifikation >
   architektur`). Es darf **nicht** auf `GG-AR-*` verweisen (`matrix-forbidden`).
   Die architektonische Durchsetzung eines Prinzips (z. B.
   [`GG-CC-004`](../../../../spec/spezifikation.md#gg-cc-004) „keine Zyklen" ↔
   [`GG-AR-TABU-004`](../../../../spec/architecture.md#architektur-tabus-build-architekturtest))
   wird als **architecture.md-Bezug nach oben** auf die Spezifikations-ID
   ausgedrückt (ADR §2c). In der Spezifikation steht nur die **Werkzeug**-
   Durchsetzung (`ruff`/`mypy`-Regeln) — Gate-Tooling, keine Schicht-Kante.
3. **SEED-Grenzfall:** einziger Scope-Familien-Umzug; der *Kundenwunsch*
   Determinismus bleibt via `GG-SIM-*` / `GG-RT-*` im Vertrag, SEED ist nur das
   *Wie* (ADR §4.2a).

## Verifikationspfad

- `make gates` + `make docs-check` grün (`anchors`/`links`/`ids`/`matrix`
  bestätigen: keine toten Anker, alle Repoints resolven, neue Klasse SDP-konform).
- **Manueller Grep-Sweep** (Nachweis im Handoff): `grep -rnE
  'GG-(PRINC|CC|SEED)-[0-9]{3}' src tests .github pyproject.toml Makefile` — jede
  Fundstelle zeigt auf einen existierenden Anker.
- `static-gates` vor Push (`format-check` ≠ `lint`); RUF003 beachten (kein
  Unicode-`−` in `#`-Kommentaren).

## DoD

- spezifikation.md existiert, `matrix`-Klasse `spezifikation` (beide Pfade) aktiv;
  `GG-PRINC-*`/`GG-CC-*`/[`GG-SEED-001`](../../../../spec/spezifikation.md#gg-seed-001)
  **nur** dort definiert, aus `lastenheft.md` entfernt.
- Alle Doku-Links + gate-blinden Refs repointet; `make docs-check` grün + Sweep sauber.
- `GG-SPEC-OPEN-*`-Sektion angelegt + `GG-SPEC-OPEN-001` geseedet.
- **Release-Entscheidung: nein.** Doku/Config + Kommentar-Deltas in `src` → kein
  Runtime-Delta → kein Tag (Regel „kein Doku-only-Release"); Delta sammelt unter
  `[Unreleased]`.

## Wandert nach

- `in-progress/` bei Aktivierung, dann `done/` mit Closure-Notiz.
- Beim Promoten die `../next/083-…`-Rückverweise in 084/085/086 mitziehen (sonst
  brechen sie; docs-check `links` fängt es).

## Bezug

- [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §2/§4 (Modell +
  ratifizierte Vorgaben), §4.4 Schritt (i).
- Nachfolge-Slices: [`084`](084-architecture-bezug-drift-fix.md)
  (Bezug-Drift-Fix, §4.4 ii), [`085`](../open/085-spezifikation-layer-qs-families-move.md)
  (QS/Abnahme-Familien), [`086`](../open/086-traceability-derived-27-1-finalization.md)
  (Traceability-Modell-Finalisierung).
- Präzedenz Schicht-Umzug: [`063`](../done/063-traceability-doc-auslagern.md);
  Traceability-Ableitung: [`066`](../done/066-traceability-recut-delegate-27-2.md).
- [`docs/plan/traceability.md`](../../traceability.md) §27.1 (Residuum-Quelle),
  [`roadmap.md`](../in-progress/roadmap.md) (Arc-Status).
