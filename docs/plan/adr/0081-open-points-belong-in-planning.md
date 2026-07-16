# ADR 0081 — Offene Punkte gehören in die Planung, nicht in die Soll-Spezifikation

**Status:** Accepted (2026-07-16) — Owner-ratifiziert; direkter `Proposed → Accepted`-Sprung
per [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md) §2-Klausel
(„ADR ohne Validierungsbedarf": strukturelle Doku-Entscheidung, kein Spike).
**Datum:** 2026-07-16
**Bezug:**

- [`ADR 0080`](0080-three-layer-spec-model.md) — definiert die Soll-Schichten
  (Lastenheft / Spezifikation / Architektur), die dieser ADR frei von offenen
  Punkten hält. Companion; nimmt zugleich [`ADR 0080`](0080-three-layer-spec-model.md)
  §4.5 (`GG-SPEC-OPEN-*`) endgültig zurück.
- [`ADR 0001`](0001-documentation-and-planning-structure.md) — Doku-/Planungsstruktur;
  die Planungs-Schicht (`docs/plan/planning/`) ist die Heimat offener Punkte.
- [`ADR 0028`](0028-link-maintenance-accepted-adr-bezug.md) — Pfad-/Link-Pflege beim
  Auflösen bestehender Offen-Sektionen (Kennungs-Repoints).

---

## 1. Kontext

[`ADR 0080`](0080-three-layer-spec-model.md) etablierte die drei **Soll-Schichten**
und die Source-Precedence-Ränge: Rang 1–3 = normatives **Soll** (`lastenheft.md`,
`spezifikation.md`/`protocol_profiles.md`, `architecture.md`), Rang 4 = **ADR**
(Architektur-/Struktur-*Entscheidungen*), Rang 5 = **Planung**
(`docs/plan/planning/`: Slices, Roadmap, Trigger, DoD).

Historisch trugen die Soll-Schichten jedoch **„Offene Punkte"-Sektionen**:
`architecture.md` §19 (`GG-AR-OPEN-*`) und — kurzzeitig — `spezifikation.md`
(`GG-SPEC-OPEN-*`, in Slice 083 angelegt und auf Owner-Entscheidung wieder entfernt).

Ein **offener Punkt ist eine *unentschiedene* Frage.** Eine Soll-Spezifikation
beschreibt den **Ziel-Zustand** — das, was *entschieden* ist. Beides zu vermischen

- verwischt „was das System sein soll" mit „was wir noch nicht entschieden haben",
- erzeugt genau die Drift/Pflegelast, die die Schichtung beseitigen sollte: die
  Offen-Liste muss handgepflegt werden, und *geschlossene* Einträge werden zu einem
  stale Provenienz-Log neben dem ohnehin entscheidenden ADR.

Der Konflikt wurde in Slice 083 konkret: die `GG-SPEC-OPEN-*`-Sektion wurde gemäß
[`ADR 0080`](0080-three-layer-spec-model.md) §4.5 angelegt und dann zurückgebaut — ihr
einziger Seed (§27.1-Positivtabelle-Generator) war Traceability-**Tooling**, kein
Spezifikations-Inhalt.

## 2. Entscheidung

**(a) Soll-Specs (Rang 1–3) enthalten ausschließlich Entschiedenes.** `lastenheft.md`,
`spezifikation.md`, `protocol_profiles.md` und `architecture.md` führen **keine**
„Offene Punkte"-Sektionen.

**(b) Der Lebenszyklus einer Frage bindet die Dokument-Wahl:**

| Zustand | Dokument | Rang |
| --- | --- | --- |
| **Offen** (unentschieden) | Planung: `docs/plan/planning/open/` (Vorabklärung / Trigger-Watch); optional Register in `roadmap.md` | 5 |
| **In Klärung** (Optionen gerahmt, Empfehlung) | `Proposed`-ADR | 4 |
| **Entschieden** | der ADR hält Entscheidung + Kontext (Rang 4); die Soll-Spec wird auf den neuen Soll aktualisiert (Rang 1–3) | 4 → 1–3 |

Kurz: **offene Frage → Planung · Entscheidung → ADR · Ergebnis → Spec.** Die Spec
zeigt nie den *Weg*, nur das *Ziel*.

**(c) Provenienz** („welche offene Frage löste welcher ADR") lebt im ADR (`Kontext`)
und im ADR-Index ([`docs/plan/adr/README.md`](README.md)), **nicht** als persistenter
Log in der Soll-Spec. Ein geschlossener Offen-Punkt braucht keinen Spec-Eintrag — der
ADR + sein Kontext halten Entscheidung und Frage bereits.

## 3. Konsequenzen

**Positiv:**

- Soll-Specs zeigen nur das Ziel, kein Prozess-/Planungs-Rauschen.
- Keine handgepflegten Offen-Listen in der Spec, die gegen die Planung driften.
- Klare Zuständigkeit: „wohin gehört diese offene Frage?" hat eine feste Antwort.

**Negativ / Kosten:**

- Bestehende Offen-Sektionen müssen aufgelöst werden — konkret `architecture.md`
  §19 (`GG-AR-OPEN-*`). Deren Kennungen sind quer referenziert (u. a. in ADRs);
  Kennungs-/Pfad-Repoints laufen per [`ADR 0028`](0028-link-maintenance-accepted-adr-bezug.md)
  (Maintenance-Edit, keine fachliche ADR-Änderung).

## 4. Umsetzung

- `spezifikation.md`: bereits frei (Slice-083-Korrektur;
  [`ADR 0080`](0080-three-layer-spec-model.md) §4.5 zurückgenommen).
- `architecture.md` §19 (`GG-AR-OPEN-*`): **aufzulösen** — *offene* Punkte in die
  Planung (Trigger-Watch `open/` + ggf. Roadmap-Register), *geschlossene* Punkte
  entfernen (Provenienz bleibt in den auflösenden ADRs). In einem Folge-Slice, mit
  Repoint der `GG-AR-OPEN-*`-Referenzen.
- Künftig: neue offene Punkte werden **gar nicht erst** in eine Soll-Spec geschrieben,
  sondern direkt in der Planung angelegt.

## 5. Abgrenzung

- **Zu [`ADR 0080`](0080-three-layer-spec-model.md):** Companion. 0080 definiert die
  Soll-Schichten; 0081 sagt, was **nicht** hineingehört. 0081 nimmt §4.5 (`GG-SPEC-OPEN-*`)
  formal zurück (der §4.5-Originaltext bleibt als Historie mit Rücknahme-Annotation stehen).
- **Zu [`ADR 0001`](0001-documentation-and-planning-structure.md):** verfeinert die
  Rollenverteilung Spec / ADR / Planung, ohne die Struktur zu ändern.
- Die konkrete Migration des `GG-AR-OPEN-*`-Kennungsraums regelt der §19-Folge-Slice,
  nicht dieser ADR.

## 6. Alternativen (verworfen)

- **Offene Punkte in der Spec belassen, nur markieren:** heilt die Vermischung nicht;
  die Drift zwischen Spec-Offen-Liste und Planung bleibt.
- **Offene Punkte ganz abschaffen:** verliert echte Vorab-Klärungs-Arbeit. Sie brauchen
  nicht *Abschaffung*, sondern den richtigen Ort (Planung).
