# Roadmap — grid-gym

**Status:** Skelett
**Stand:** 2026-05-14
**Bezug:** [Lastenheft](../../../../spec/lastenheft.md), [Architektur](../../../../spec/architecture.md)

---

## 1. Zweck

Diese Roadmap fuehrt die Meilensteine, die sich aus dem Lastenheft und
der Architektur ergeben. Sie ist die Quelle fuer die Status-Spalte
der `GG-TRACE-001`-Implementierungsmatrix
([Lastenheft §27.2](../../../../spec/lastenheft.md#272-anforderung-zu-implementierung))
mit `M[N]`-Markern.

Die Roadmap ist noch ein Skelett. Sie wird mit dem ersten ADR zur
Sprach- und Build-Wahl (`GG-AR-OPEN-001`) und der ersten
Implementierungs-Slice gefuellt.

---

## 2. Konvention

- Meilensteine werden fortlaufend numeriert (`M1`, `M2`, …).
- Jeder Meilenstein hat:
  - Lieferziel (was wird umgesetzt),
  - Lastenheft-IDs (`GG-*`),
  - Architekturartefakte (`GG-AR-*`),
  - Abnahmekriterium (Verifikationspfad),
  - Status (Pending / In Progress / Done).
- Abgeschlossene Meilensteine wandern als Closure-Notiz nach
  `docs/plan/planning/done/`.
- Themes fuer kommende Meilensteine werden in `docs/plan/planning/next/`
  als Scope-Skizze gefuehrt, bevor sie hier als aktiver Slice aufgenommen
  werden.

---

## 3. Meilensteine

### M1 — _(offen, wird mit erster Slice gefuellt)_

- **Lieferziel:** offen
- **Lastenheft-IDs:** offen
- **Architekturartefakte:** offen
- **Abnahmekriterium:** offen
- **Status:** Pending

---

## 4. Vorbedingungen

Vor M1 muessen folgende Punkte geklaert sein:

- `GG-AR-OPEN-001` Sprach- und Build-Wahl (eigener ADR).
- `GG-AR-OPEN-002` API/Simulation als ein oder zwei Prozesse.
- Initiales Repository-Layout gemaess der Hexagonalen Sicht
  (`GG-AR-P-002`, `GG-AR-TABU-001..008`).
