# 002 — `tools/check_refs.py` als Querverweis-Linter — Closure-Notiz

**Status:** Done — geschlossen 2026-05-17 mit Welle-7-Audit-Fix.
**Datum:** 2026-05-15 (geoeffnet); 2026-05-17 Closure mit
Welle-7-Audit-Erbe.
**Quelle:** [`ADR 0004`](../../adr/0004-identifier-based-cross-references.md)
§3 (Retrofit-Regel), §4 (Konsequenzen); externer Welle-7-Audit
(11 broken Markdown-Refs nach dem `in-progress/ → done/`-Move
des Slice-Plans).
**Verlinkt:**
`tools/check_refs.py` (geloescht 2026-06-12 — abgeloest durch
d-check, siehe `.d-check.yml`),
`Makefile`-Target `docs-check` (laeuft seither ueber d-check),
`Dockerfile`-Stage `docs-check` (entfernt).

---

## Trigger (historisch)

ADR 0004 forderte Kennungs-basierte Querverweise und nannte
Tool-Unterstuetzung als Folgearbeit:

> Dokumentations-Tooling (z. B. ein moeglicher
> `tools/check_refs.py` als Folgearbeit) kann spaeter ueber die
> Kennungen einen Index erzeugen und nicht aufgeloeste Verweise
> melden.

Aktivierungs-Kriterium: „Sobald nach Spike-0 zwei oder mehr
Fundstellen mit stillem Querverweis-Drift beobachtet werden".

## Aktivierung (Welle 7)

Der Welle-7-Audit hat **11 broken Markdown-Pfad-Links** auf
einmal entdeckt (Pfad-Drift nach dem `in-progress/ → done/`-
Move des M1-Slice-Plans). Das ueberschreitet das
Aktivierungs-Kriterium deutlich.

## Lieferung

- **`tools/check_refs.py`** (stdlib-only):
  - Scant `docs/**/*.md` + `spec/**/*.md` nach relativen
    `[text](path)`-Links.
  - Aufloest Pfade relativ zur Source-Datei, prueft Existenz im
    Repo.
  - Ueberspringt `http(s)://`, `mailto:`, `ftp://` und reine
    `#anchor`-Refs.
  - Exit-Code 0 (alle aufgeloest) oder 1 (Verstoesse). Output-
    Format `{source_rel}:{lineno}\t{target}\t{reason}`.
- **`Dockerfile`-Stage `docs-check`** (Welle 7): laeuft
  `python tools/check_refs.py` im `source`-Image. Erfordert
  `docs/`, `deploy/`, `Makefile`, `Dockerfile`, `CHANGELOG.md`
  im Build-Kontext — `.dockerignore` entsprechend angepasst.
- **`Makefile`-Target `make docs-check`**: ruft den
  Dockerfile-Stage auf.

## Welle-7-Audit-Befunde (durch das Tool jetzt automatisierbar)

Der Welle-7-Aufrueum-Sweep hat folgende Klassen broken-link
gefangen, die das Tool ab sofort vor jedem Commit/PR
mechanisch faengt:

- **Post-Move-Pfad-Drift** (M1-Slice-Plan `in-progress/ →
  done/`): 8 Refs in nicht-immutable-Dateien aktualisiert,
  3 immutable ADR-Bezug-Pfade initial via Forwarder-Stubs abgefangen
  (`in-progress/M1-tick-loop-spine.md`,
  `open/003-random-port-adr.md`, `open/012-snapshot-composition.md`,
  `next/M1-tick-loop-spine.md`).
- **Tatsaechliche Drift** (echter Bug, nicht nur Pfad-Move):
  - `done/M1-tick-loop-spine.md:25 roadmap.md` → korrigiert
    auf `../in-progress/roadmap.md`.
  - `open/README.md:34 next/001-...` → korrigiert auf
    `done/001-...`.

## Scope-Abgrenzung — was bleibt fuer eine spaetere Welle

Trigger 002 forderte urspruenglich auch:

- **Kennungs-Aufloesung** (`GG-*`/`GG-AR-*`/`AC-*`/`ADR-NNNN`-
  Refs gegen die Definitionsstellen im Text): nicht in dieser
  Welle-7-Lieferung. Welle 7 macht nur den Markdown-Link-
  Validator.
- **`§…`-Verweise auf ID-tragende Sektionen** (Drift-Erkennung
  fuer Section-Refs): nicht in Welle 7.

Diese Restposten sind eigene Folge-Slices in M2-Welle-0 oder
M5 (Doku-Generierung). Der heutige Linter deckt das aktuelle
Bottleneck (Pfad-Drift nach File-Moves) vollstaendig ab.

## Wandert nach

`done/` (jetzt). Erweiterungen (Kennungs-Linter, Section-Drift)
sind eigene Folge-Trigger.
