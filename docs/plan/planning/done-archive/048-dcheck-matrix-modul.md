# 048 — d-check `matrix`-Modul einfuehren (Referenzrichtungs-Gate, SDP)

**Status:** **Resolved 2026-06-17** — **Option A (Voll-SDP)** gewaehlt und
umgesetzt via Slice [`049`](../done/049-sdp-matrix-doku-umbau.md): das
`matrix`-Modul ist in [`.d-check.yml`](../../../../.d-check.yml) aktiv
(SDP-Klassen + Abwaerts-Regeln + `status: forbidden: [superseded,
deprecated]` + `exclude-sections` fuer die `## Historie`-/Traceability-
Sektionen). Die Spec-Straten wurden zeitlos umgebaut (ADR-/Welle-/Status-
Provenance in ausgenommene `## Historie`-Sektionen); `make docs-check` gruen.
[`ADR 0004`](../../adr/0004-identifier-based-cross-references.md)-Bezug bereinigt, [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md)-Supersede-Lineage als Inline-Code (kein
Lineage-Carve-out im Modul → offener d-check-CR, siehe unten). Doc-
Archivierung nach `done-archive/` folgt mit der M8-Meilenstein-Closure.
**Datum:** 2026-06-16
**Quelle:** User-Wunsch „matrix-Modul in `.d-check.yml` einfuehren";
Grundlage ist das Lab-Regelwerk
[§Referenz-Richtung (SDP)](https://github.com/pt9912/ai-harness-course/releases/download/v1.2.0/lab-regelwerk.zip)
(`grundlagen-konventionen.md`). d-check liefert das Modul seit v0.10.0
(Spec `DC-FA-MTX-001`).

---

## Trigger

d-check ist mit dem v0.10.0-Pin (Commit der `D_CHECK_IMAGE`-Anhebung)
im Voll-Funktionsumfang verfuegbar. Das Modul `matrix` kodiert
**Referenzrichtungs-Regeln zwischen Dokumentklassen** maschinell: ein
Spec-Stratum darf nicht abwaerts auf ADRs/Planung verweisen, und
Verweise auf inaktive (superseded/deprecated) ADRs sind Befunde.

Das Regelwerk liefert die normative Grundlage (Stabilitaets-Rang
**Vertrag › Technik › Sicht › ADR › Slice**; normative Kanten zeigen
strikt aufwaerts; Provenance lebt nur unter einer Historie-/Versions-
Tabelle, „Regel 5: Body vs. Changelog"). Offen ist nur, **wie viel
davon grid-gym heute schon einhaelt** — und damit, in welchem Umfang
sich das Modul ohne Doku-Umbau aktivieren laesst.

## Messung (Trockenlauf 2026-06-16, d-check v0.10.0)

Kandidaten-Matrix (SDP-Regeln, Klassen unten) gegen die lebende Doku,
nicht-destruktiver `-json`-Lauf — **119 Befunde**, alle aus `matrix`:

| reason             |  Anzahl | Bedeutung                                        |
| ------------------ | ------: | ------------------------------------------------ |
| `matrix-forbidden` |     117 | Abwaerts-Verweis Spec-Stratum → ADR im Fliesstext |
| `matrix-inactive`  |       2 | Verweis auf inaktive (superseded) ADR             |

Die 117 Richtungs-Befunde verteilen sich auf:

| Quelldatei                  | Befunde |
| --------------------------- | ------: |
| `spec/architecture.md`      |      68 |
| `spec/protocol_profiles.md` |      28 |
| `spec/lastenheft.md`        |      21 |

Die 2 Status-Befunde:

- `docs/plan/adr/0004-identifier-based-cross-references.md` Z. 6
  (`**Bezug:**`) → `ADR 0003` <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
  (Status `Superseded`). **Echter Befund** — der Bezug zeigt auf eine
  abgeloeste ADR und sollte auf die abloesende
  [ADR 0006](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md)
  zeigen.
- `docs/plan/adr/0006-adr-lifecycle-superseding-and-process-corrections.md`
  Z. 6 (`**Bezug:**`) → `ADR 0003`. <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
  **Grenzfall** — [ADR 0006](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md)
  *ist* die abloesende ADR; ihr Verweis auf
  `ADR 0003` ist legitime <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
  Supersede-Lineage (Regelwerk Regel 2: ADR→ADR-Lineage ist normativ).
  Das `matrix`-Modul kennt heute keinen Lineage-Carve-out → potenzieller
  d-check-Change-Request (Supersedes-Feld als erlaubte Kante).

## Bewertung

grid-gym ist **nicht SDP-konform**: die Spec-Straten verlinken ADRs als
Entscheidungs-Provenance direkt im bindenden Text (Werte-Zellen,
`**Status:**`-Zeile, Tabellen-Begruendungen), nicht nur unter einer
Historie-Sektion. Das Regelwerk erlaubt **Grandfathering** fuer vor
Konvention-Einfuehrung entstandene Faelle; das `matrix`-Modul scannt
aber das ganze Repo und kennt kein „nur ab jetzt".

Konsequenz: **Voll-SDP-Aktivierung bricht `make docs-check` sofort mit
117 Befunden** (das Gate ist fail-closed). Die Aktivierung ist daher
keine reine Config-Aenderung, sondern entweder ein Doku-Umbau oder eine
bewusste Scope-Verengung.

## Entscheidung fuer 2026-06-17 (offen)

| Option | Inhalt | Gate-Wirkung | Aufwand |
| ------ | ------ | ------------ | ------- |
| **A — Voll-SDP** | alle Richtungs- + Status-Regeln; 117 Abwaerts-Verweise umbauen (in Historie-/Versions-Tabelle verschieben **oder** Bezug-Felder umkehren: ADR deklariert, was sie schaerft) | sofort 117 Fixes noetig | gross (eigener Doku-Slice) |
| **B — nur Status** | nur `status: forbidden: [superseded, deprecated]`, **keine** Richtungs-Regeln | nur 2 Fixes (matrix-inactive) | klein |
| **C — Grandfathering** | volle Regeln + Baseline/Ignore bestehender Verweise | 0 Fixes, aber braucht d-check-CR (Baseline-Datei) | mittel (CR-abhaengig) |
| **D — Hybrid** | B jetzt + A als separater Doku-Umbau-Slice ueber Zeit | 2 Fixes jetzt, Rest als Schuld | klein jetzt |

**Empfehlung:** **D** — zuerst B liefern (Status-Regel fAengt den echten
matrix-inactive-Befund in
[ADR 0004](../../adr/0004-identifier-based-cross-references.md), schuetzt
kuenftig vor Verweisen auf abgeloeste ADRs, ohne den 117er-Umbau), den
Lineage-Grenzfall in
[ADR 0006](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md)
als d-check-CR notieren; die Voll-SDP-Richtungsregeln (Option A) als
eigenen Doku-Umbau-Slice planen.

## Erwartete Lieferung (Skizze)

1. **Klassen-Block** in `.d-check.yml` (`matrix` zur `modules`-Liste):

   | Stratum/Klasse | grid-gym-Pfad | Anmerkung |
   | -------------- | ------------- | --------- |
   | Vertrag (Decke) | `spec/lastenheft.md` | abnahmebindende `GG-*`-Anforderungen |
   | Technik | `spec/protocol_profiles.md` | technische Protokoll-Festlegungen |
   | Sicht | `spec/architecture.md` | derivativ, `GG-AR-*` |
   | ADR | `docs/plan/adr/[0-9]*.md` | 4-stellig `NNNN-*.md` |
   | Slice/Planung | `docs/plan/planning/**/*.md` | grid-gym nutzt `NNN-*.md`, keine `slice-*.md` |

2. **Status-Regel** `status: forbidden: [superseded, deprecated]`
   (Option B/D) + `exclude-sections` fuer die Historie-Sektion der
   Spec-Straten.
3. **Bezug-Fix** in
   [ADR 0004](../../adr/0004-identifier-based-cross-references.md):
   Bezug von der abgeloesten
   `ADR 0003` auf <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
   [ADR 0006](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md)
   umstellen — **Achtung Pflege-Regel
   [ADR 0001](../../adr/0001-documentation-and-planning-structure.md) §4:
   `Accepted`-ADRs nicht inhaltlich ueberschreiben**; der Bezug-Header
   ist Metadaten, die Korrektheit der Aenderung ist vorab zu klaeren.

## Akzeptanzkriterien

- **Happy:** Gewaehlte Option aktiviert, `make docs-check` gruen
  (0 Befunde), `matrix` in der `modules`-Liste.
- **Boundary:** Verweis auf eine `Superseded`-ADR aus einem
  Planungs-/ADR-Artefakt → Befund `matrix-inactive`.
- **Negative (nur bei A/D-Vollausbau):** neuer Abwaerts-Verweis aus
  einem Spec-Stratum auf eine ADR-Datei im bindenden Text → Befund
  `matrix-forbidden`.

## Verifikationspfad

`make docs-check` (Gate, fail-closed) nach der Aenderung; bei Option
A/D zusaetzlich Stichprobe, dass die Historie-/Versions-Tabelle der
Spec-Straten korrekt via `exclude-sections` ausgenommen ist.

## Out-of-Scope

- Semantische Unterscheidung Verifikations-Zeiger vs.
  Entscheidungsgrundlage (bleibt Reviewer-Aufgabe, Regelwerk).
- d-check-Lineage-Carve-out fuer Supersedes-Kanten (eigener CR, falls
  Option A/D den Grenzfall in
  [ADR 0006](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md)
  echt machen soll).
- Einfuehrung eines separaten Technik-Stratums `spec/spezifikation.md` <!-- d-check:ignore (bewusst nicht existent: grid-gym hat dieses Stratum nicht) -->
  (grid-gym faltet Technik in `protocol_profiles.md`/Sicht).
