# 049 — Voll-SDP-Doku-Umbau: `matrix`-Gate aktivieren (Trigger 048, Option A)

**Status:** **Done (2026-06-17).** Umsetzung von Trigger
[`048`](../done-archive/048-dcheck-matrix-modul.md) **Option A (Voll-SDP)**: das
d-check `matrix`-Modul (Referenzrichtungs-Gate, `DC-FA-MTX-001`) ist in
`.d-check.yml` aktiv (volle Abwaerts-Regeln + Status-Regel +
`exclude-sections`); die Spec-Straten sind zeitlos umgebaut, `make docs-check`
gruen (0 Befunde). Nach `done/` verschoben (2026-06-17).
**Scope-Praezisierung gegenueber der Eroeffnung** (User-Steuerung):
der Body traegt **gar keine** ADR-Erwaehnung (auch nicht semantisch `ADR X`
oder „ADR X §Y verbindlich"), **keine** Status-/Wellen-/Decision-Prozess-
Angaben; Provenance vollstaendig in `## Historie`. Aufwaerts-Refs werden
**verlinkt** (`GG-AR-*`/`GG-*` → Definitions-`#anchor`).

**Container:** Trigger [`048`](../done-archive/048-dcheck-matrix-modul.md) (Messung,
Optionen, Empfehlung). Quelle: Lab-Regelwerk §Referenz-Richtung (SDP),
Stabilitaets-Rang **Vertrag › Technik › Sicht › ADR › Slice**.

---

## 1. Zweck

SDP-Konformitaet maschinell durchsetzen: normative Kanten zeigen **strikt
aufwaerts**. Die Spec-Straten (`lastenheft` = Vertrag, `protocol_profiles` =
Technik, `architecture` = Sicht) duerfen nicht abwaerts auf ADRs/Slice-Plaene
verweisen; Verweise auf inaktive (superseded/deprecated) ADRs sind Befunde.

## 2. Messung (d-check v0.10.0, Voll-SDP-Config)

129 Befunde: **123 `matrix-forbidden`** + **6 `matrix-inactive`**.

| Quelle | → ADR | → Slice | → Inter-Spec |
|---|---:|---:|---:|
| `spec/architecture.md` | 66 | 2 | 0 |
| `spec/lastenheft.md` | 15 | 6 | 6 (1 Sicht, 5 Technik) |
| `spec/protocol_profiles.md` | 19 | 9 | 0 |

`matrix-inactive` (6): [`ADR 0004`](../../adr/0004-identifier-based-cross-references.md) Z. 6 → `ADR 0003` (**echter Fix**: auf <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
[`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) umstellen); [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) Z. 6 → `ADR 0003` (**legitime <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
Supersede-Lineage** → `d-check:ignore` + CR-Notiz); 4× in Trigger
[`048`](../done-archive/048-dcheck-matrix-modul.md) selbst (diskutiert `ADR 0003` <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
bewusst → `d-check:ignore`).

## 3. Fix-Mechanismus (Option Y, validiert)

**Im bindenden Body: keine ADR-Referenz** — weder Link noch nackte Kennung
(`` [`ADR 0002`](../../adr/0002-language-and-build-stack.md) ``) noch „ADR X §Y verbindlich". Die Spec traegt ihre Aussage
selbst; die ADR zeigt ueber ihren `**Bezug:**`-Header **aufwaerts** auf die
`GG-*`-/`GG-AR-*`-ID. Body-Saetze werden so umformuliert, dass die
ADR-Erwaehnung entfaellt, ohne die normative Aussage zu aendern.

**Provenance unter `## Historie` (SDP Regel 5):** je Spec-Datei eine Sektion
mit Ueberschrift **exakt `## Historie`** (am Datei-Ende), die das Mapping
Spec-Item → ADR als Tabelle traegt (Link erlaubt). `matrix`-`exclude-sections:
[Historie]` nimmt genau diese Ueberschrift vom Richtungs-Gate aus.
**Validiert:** ein ADR-Link unter `## Historie` erzeugt keinen `matrix`-Befund;
die Ueberschrift muss **exakt** „Historie" lauten (Substring „Historie /
ADR-Provenance" greift nicht). Mehrere Body-Erwaehnungen derselben ADR
kollabieren auf **eine** Provenance-Zeile → die Tabelle bleibt kompakt.

**Slice-Verweise (→ Slice):** ebenfalls aus dem Body; in `## Historie` als
Provenance-Zeile **oder** Prosa-Referenz ohne Link/Code (`codepaths` wuerde
einen nackten Dateinamen pruefen).

**Status-Befunde:** [`ADR 0004`](../../adr/0004-identifier-based-cross-references.md)-Bezug — der redundante (bereits durch
[`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) abgedeckte) `ADR 0003`-Link wurde aus dem Bezug-Header entfernt <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
(Metadaten-Pflege, kein Decision-Edit). [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md)-Supersede-Lineage auf
`ADR 0003`: **`d-check:ignore` greift NICHT fuer `matrix-inactive`** → der
Link wurde auf Inline-Code `` `ADR 0003` `` umgestellt (Referenz sichtbar, <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
kein Link → kein Befund). Diskussions-Refs im Trigger 048 ebenfalls
Inline-Code. **Offener d-check-CR:** Supersedes-Lineage-Carve-out im
`matrix`-Modul (damit die abloesende ADR ihre abgeloeste verlinken darf).

## 4. DoD

- [x] `matrix` in `.d-check.yml` `modules` aktiv; SDP-Klassen + Abwaerts-
      Regeln + `status: forbidden: [superseded, deprecated]` +
      `exclude-sections` (`Historie` + Traceability-Sektionen §18/§19/§27).
- [x] `make docs-check` gruen (0 Befunde, `matrix` scharf).
- [x] `AGENTS.md` §2.5 nachgezogen (Spec ist Zielbild: kein Status/Welle/ADR
      im Body; Provenance in `## Historie`; Aufwaerts-Refs verlinkt).
- [x] Trigger 048 `Resolved`; CHANGELOG.

**Umsetzungs-Notizen:**

- `protocol_profiles.md` (Technik) + `architecture.md` (Sicht): Body komplett
  zeitlos umgebaut, je eine `## Historie`-Provenance-Tabelle.
- `lastenheft.md` (Vertrag): Body (§1–26) war **bereits zeitlos**; die
  ADR-/Welle-Provenance liegt in der Traceability-Matrix §27 (via
  `exclude-sections` ausgenommen) — keine Body-Edits noetig.
- **Rang-Praezisierung:** `protocol_profiles → architecture` (`GG-AR-*`) waere
  unter Vertrag › Technik › Sicht ein Abwaerts-Link → der [`GG-AR-PORT-DRN-007`](../../../../spec/architecture.md#driven-ports-vom-kern-aufgerufen)-
  Bezug wurde aus `protocol_profiles.md` **entfernt** (nicht verlinkt); der
  umgekehrte `architecture → protocol_profiles`-Index-Link (aufwaerts) bleibt.

## 5. Risiken

- **AGENTS.md §2.5-Spannung:** die heutige Konvention erlaubt explizit, dass
  `architecture.md` ADRs referenziert. Voll-SDP kehrt das um → §2.5 wird
  mitgezogen (Quelle gewinnt, `AGENTS.md` nachgezogen).
- **Gate-Wechselwirkung:** `matrix` ↔ `ids` ↔ `codepaths`. Validiert fuer
  ADR-Inline-Code; Slice-Refs pro Fall, um `codepaths` nicht zu brechen.
- **Lesbarkeit:** klickbare Spec→ADR-Navigation entfaellt; die ADR-Nummer
  bleibt als Inline-Code, Auffindbarkeit ueber den ADR-Index + ADR-`Bezug:`.

## 6. Nicht-Ziele

- d-check-Lineage-Carve-out fuer Supersedes-Kanten (eigener CR).
- `adr → slice`-Richtungsregel (ADR-`Bezug:`-Slice-Provenance bleibt erlaubt;
  nicht Gegenstand der 117 Spec-Befunde).
- Inhaltliche Spec-Aussagen aendern — nur die Referenz-**Form** (Link → Code/
  Prosa/ID), nicht die Aussage.
