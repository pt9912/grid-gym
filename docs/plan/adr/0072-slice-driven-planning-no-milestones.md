# ADR 0072 — Slice-getriebenes Planungsmodell: Meilenstein-Ebene entfernt + Release pro Slice (Accepted)

**Status:** Accepted — umgesetzt via
[`Slice-Plan 053`](../planning/done/053-planungsmodell-slices-ohne-meilensteine.md)
(C0..C4: Roadmap/Konventionen/README auf slice-first, `make gates` +
`make docs-check` gruen).
**Datum:** 2026-07-01
**Status geaendert am:** 2026-07-01 — `Proposed → Accepted`
(Slice-053-Closure C4).
**Bezug:**

- [`ADR 0001`](0001-documentation-and-planning-structure.md) — Dokumentations-
  und Planungsstruktur; §3 (Roadmap „liefert die Meilenstein-Marker `M1`, `M2`,
  … fuer Lastenheft §27.2") wird hiermit geschaerft.
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) — Schaerfung-ohne-Abloesung
  (die Form dieser ADR; kein Supersede).
- [`roadmap.md`](../planning/in-progress/roadmap.md) — die living Roadmap, die
  auf slice-first umgestellt wird.

---

## 1. Kontext

Die Meilenstein-Ebene (`M1..M8`) war bisher die oberste Planungs-Gruppierung
ueber Wellen und Slices, verankert in
[`ADR 0001`](0001-documentation-and-planning-structure.md) §3 (`M{N}`-Marker fuer
[`Lastenheft §27.2`](../../../spec/lastenheft.md#gg-trace-001)). Mit **M8
abgeschlossen + v0.2.0 released** ist die MUSS-/SOLLTE-Roadmap geliefert; die
Meilenstein-Container bringen fuer die weitere Arbeit mehr Zeremonie als Nutzen.

Kuenftig soll **slice-getrieben** gearbeitet werden (Wellen/Slices als oberste
Einheit) und die **Release-Entscheidung pro Slice** fallen, nicht pro
Meilenstein. Der Verzeichnis-Lifecycle (`open → next → in-progress → done`) und
die Wellen/Slice-Mechanik bleiben unveraendert.

---

## 2. Entscheidung

### 2.1 Meilenstein-Ebene entfaellt als forward-Planungseinheit

Neue Arbeit laeuft als **Slice** (ggf. in Wellen sub-gesliced) direkt ueber
`open → next → in-progress → done`, ohne Meilenstein-Container. Es werden keine
neuen `M{N}` eroeffnet; „aktiver/naechster Meilenstein" entfaellt als Konzept.
Damit wird die `ADR 0001` §3-Konsequenz („Roadmap liefert `M{N}`-Marker")
geschaerft: die Roadmap fuehrt fortan **gelieferte Historie + aktive/geplante
Slices**, vergibt aber keine neuen `M{N}`.

### 2.2 Naming: repo-weit fortlaufende Slice-Nummern

Neue Slice-/Wellen-Docs heissen `NNN-slug.md` (repo-weit eindeutige
dreistellige Nummer, fortlaufend — Muster wie die bestehenden Standalone-Slices
`041`/`045`/`051`). Grosse Slices sub-slicen als `NNN-a`/`NNN-b`. Das
`M{N}-welle-*`-Praefix wird fuer **neue** Docs retired; es bleibt nur in der
eingefrorenen Historie. (Die ADR-Dateinamen-Konvention `NNNN-slug.md` aus
`ADR 0001` §2 ist davon unberuehrt.)

### 2.3 Release-Entscheidung pro Slice

Jeder Slice-Plan traegt ein DoD-Feld **„Release-Entscheidung: ja/nein
(+ SemVer-Ziel)"**:

- `nein` → das Delta sammelt unter [`CHANGELOG.md`](../../../CHANGELOG.md)
  `[Unreleased]`.
- `ja` → der Abschluss-Commit schneidet den Tag (`pyproject`-Bump +
  CHANGELOG-Finalisierung + `v*.*.*`-Tag → `release.yml`), gebunden an die
  bestehenden Regeln (kein Doku-only-Release / Runtime-Delta-Pflicht;
  `make fullbuild` vor dem Tag). SemVer folgt dem Delta (Minor bei additiven
  Features, Patch bei Fixes).

### 2.4 Historie friert ein; `M{N}`-Marker bleiben

`done/`/`done-archive/`-Closure-Docs (`M{N}-results.md`, `M{N}-welle-*.md`) und
**alle** `M{N}`-Marker in den Spec-Straten werden **nicht** umgeschrieben — sie
sind die Aufzeichnung: die
[`GG-TRACE-001`](../../../spec/lastenheft.md#gg-trace-001)-§27.2-Matrix, die
Adapter-Provenienz-Tabelle in
[`spec/protocol_profiles.md`](../../../spec/protocol_profiles.md) und die
`M{N}`-Kommentar-Marker in `spec/persistence-schema.yaml`. Es werden keine neuen
`M{N}` vergeben; kuenftige Anforderungs-Erfuellung wird per **Slice-Referenz**
(bzw. Release-Version) eingetragen — z. B. traegt ein neuer Protokolladapter
seine Provenienz in `protocol_profiles.md` als `Slice NNN` statt `M{N}`.

### 2.5 Form: Schaerfung von ADR 0001, kein Supersede

Diese ADR schaerft
[`ADR 0001`](0001-documentation-and-planning-structure.md) §3 additiv per
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md)-Pattern (kein Supersede): der
Directory-Lifecycle und die uebrige `ADR 0001`-Struktur bleiben unveraendert und
in Kraft; nur die Meilenstein-Marker-Konsequenz wird ersetzt. Der Index-Eintrag
([`README.md`](README.md)) traegt die Lineage in der „Schaerfungen"-Spalte der
`0001`-Zeile.

---

## 3. Konsequenzen

- Die [`roadmap.md`](../planning/in-progress/roadmap.md) wird von milestone-first
  auf slice-first umgebaut: kompakte „Gelieferte Historie"-Tabelle (Pointer auf
  die `done/M{N}-results.md`-Closure-Docs) + „Aktive/geplante Slices" +
  „Release-Modell (pro Slice)".
- Die Konventionen ([`harness/conventions.md`](../../../harness/conventions.md),
  [`AGENTS.md`](../../../AGENTS.md),
  [`planning/README.md`](../planning/README.md)) stellen „Cross-Meilenstein" /
  „Welle-/Meilenstein-Closure" / `M{N}`-Praefix-Naming auf slice-first um;
  Historie-Verweise bleiben.
- Release-Kadenz wird flexibel und delta-getrieben statt an Meilenstein-Closures
  gebunden.
- Keine Meilenstein-Closure-Zeremonie mehr (`M{N}-welle-X` + `M{N}-results.md`);
  Slice-Closure (Self-Move nach `done/` + DoD) bleibt.

---

## 4. Nicht Gegenstand dieser ADR

- **Umschreiben der Historie:** `done/`/`done-archive/`-Closure-Docs und die
  `M{N}`-Marker der Spec-Straten bleiben eingefroren (§2.4).
- **Verzeichnis-Lifecycle:** `open → next → in-progress → done` und die
  ADR-Dateinamen-Konvention (`ADR 0001` §2) bleiben unveraendert.
- **Spec-Straten-Inhalt:** keine fachliche Aenderung an
  [`spec/lastenheft.md`](../../../spec/lastenheft.md) /
  [`spec/architecture.md`](../../../spec/architecture.md) (die Spec ist per SDP
  ohnehin meilensteinfrei — [`AGENTS.md`](../../../AGENTS.md) §2.5).
