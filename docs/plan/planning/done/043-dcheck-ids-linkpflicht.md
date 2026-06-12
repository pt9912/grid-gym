# 043 — `ids`-Linkpflicht fuer Kennungen via d-check-Modul-Scope

**Status:** Closed (2026-06-12) — aufgeloest durch d-check
**v0.3.0** (liefert `<modul>.scope` per grid-gym-CR, dort
slice-017/`DC-FA-CONF-002`; Digest-Pin-Bump `84ca599` durch den
Maintainer) + ids-Aktivierung in grid-gym: Linkpflicht-Sweep
Stufe 1 `01f2a49` (84 Kennungen, docs/user + lastenheft +
protocol_profiles) + Stufe 2 `4d37a65` (228 Kennungen
architecture.md inkl. Traceability-Gewinn; Review-Schaerfung:
alle Links mit Abschnitts-Anker statt nur Datei) +
Bestands-Link-Anker-Sweep `8c0646c` (99 Kapitel- + 20
ID-Anker repo-weit). `ids` produktiv in `.d-check.yml`
(Scope `spec/` + `docs/user/`, 4 Muster mit
GG-AR-vor-GG-Praezedenz); `make docs-check` cache-frei gruen
mit 0 Befunden. Move nach `done/` in diesem Commit.
**Datum:** 2026-06-12
**Quelle:** Trigger-002-Erbschaft (Kennungs-Aufloesung
`GG-*`/`AC-*`/`ADR NNNN` war dort vertagt; Trigger 002 wurde
2026-06-12 mit der d-check-Migration `766ae8c` abgeloest) +
User-Doku-Audit 2026-06-12 (Post-M7).

---

## Trigger

grid-gym will das d-check-`ids`-Modul (Linkpflicht fuer nackte
Kennungen, d-check `DC-FA-ID-001`) aktivieren. Messung
(d-check v0.2.0 @ `ea7396a`, Overlay-Config):

| ids-Scope | Befunde | Bewertung |
| --------- | ------- | --------- |
| globaler Scan-Scope (noetig fuer `links`/`anchors`) | 2776 (2058 `ADR NNNN`, 371 `GG-*`, 311 `AC-*`, 36 `GG-AR-*`) | Masse in historischen `done/`-Wellen-Docs — Retro-Verlinkung waere Audit-Trail-Umschreiben |
| kuratiert (`spec/` + `docs/user/`) | 312 (davon 190 nackte `GG-*`-Referenzen in `architecture.md` — Traceability-Gewinn) | fixbar, gestaffelt |

**Blocker:** `scan.roots`/`scan.ignore` gelten in d-check global
fuer alle Module; kein `-config`-Flag. Ein engerer `ids`-Scope
ist heute nicht ausdrueckbar, ohne die breite
`links`/`anchors`-Abdeckung zu opfern.

## Erwartete Lieferung

1. **d-check-Feature `<modul>.scope`** (Change Request an
   d-check uebergeben 2026-06-12, dort als Slice-Kandidat
   „slice-017-modul-scope"): optionaler Schluessel
   `<modul>.scope.roots`/`.ignore`, ersetzt den globalen
   Scan-Scope fuer genau dieses Modul; Module ohne `scope`
   erben global (abwaertskompatibel); Constraints spiegeln
   `scan.*` (Existenzpflicht, Repo-Escape-Verbot → Exit 2,
   Ignore-Pruning). Out-of-Scope dort: Per-Pattern-Scope,
   `-config`-Flag, Schnittmengen-Semantik.
2. **Digest-Pin-Bump** in `Makefile` auf das d-check-Release
   mit dem Feature.
3. **`.d-check.yml`-Erweiterung:** `modules: [links, anchors,
   ids]` + `ids.scope.roots: ["spec", "docs/user"]` +
   Muster (Praezedenz-Reihenfolge!):
   `GG-AR-[A-Z0-9-]+-\d{3}` → `spec/architecture.md`,
   `GG-[A-Z]+-\d{3}` → `spec/lastenheft.md`,
   `AC-[A-Z][A-Z0-9-]+` → `spec/architecture.md`,
   `ADR[- ]\d{4}` → `docs/plan/adr/`.
4. **Gestaffelter Fix-Sweep:** erst `docs/user/` +
   `lastenheft`/`protocol_profiles` (~84 Befunde), dann der
   `architecture.md`-Traceability-Sweep (~228) als eigener
   Commit.

**Nicht-Ziele:** Retro-Verlinkung der historischen
Planning-Docs (`docs/plan/planning/**`); Carveout-IDs
`D-n`/`T-nnn`/`P-n` als ids-Klasse (zu kollisionstraechtig,
z. B. `3b-D-1`-Decision-IDs — erst bei eindeutigem Muster).

## Aktivierung

d-check-Release mit Modul-Scope-Feature verfuegbar
(Digest in den Release-Notes) ODER alternativ Entscheid fuer
die Doppelpass-Bruecke (zweiter Container-Lauf mit
Overlay-Config), falls das Feature laenger nicht kommt.

## Konsequenz wenn ungeloest

Kennungs-Referenzen (`GG-*`/`AC-*`/ADR) bleiben die einzige
unvalidierte Referenzklasse der Doku (Links + Anker prueft
d-check seit `766ae8c`); nackte Kennungen ohne
Definitions-Link bleiben unentdeckt.

## Bezuege

- d-check: `README.md` (ids-Modul) + `spec/lastenheft.md`
  `DC-FA-ID-001` + `spec/spezifikation.md` §`.d-check.yml`
  (externes Repo `pt9912/d-check`).
- [`.d-check.yml`](../../../../.d-check.yml) — aktuelle
  grid-gym-Konfiguration (links + anchors).
- [`../done/002-check-refs-tool.md`](../done/002-check-refs-tool.md)
  — Vorgaenger-Trigger (abgeloest mit der d-check-Migration
  `766ae8c`; der dort vertagte Kennungs-Scope ist hierher
  weitergereicht).
