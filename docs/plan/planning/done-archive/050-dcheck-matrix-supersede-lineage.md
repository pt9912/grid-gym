# 050 — d-check `matrix`-Modul: Supersede-Lineage-Carve-out (CR)

**Status:** **Resolved 2026-06-17** — d-check **v0.11.0** liefert den
Lineage-Carve-out (`allow-supersede-lineage` + `supersede-fields`). Migration
vollzogen: `D_CHECK_IMAGE` auf den v0.11.0-Digest gepinnt
([`Makefile`](../../../../Makefile)), `matrix.status.allow-supersede-lineage:
true` + `supersede-fields: [Supersedes, Aenderungstyp]` in
[`.d-check.yml`](../../../../.d-check.yml), [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md)-Bezug auf `ADR 0003` <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
wieder als **klickbarer Link** (Inline-Code-Workaround entfernt).
`make docs-check` gruen; **Boundary verifiziert** (Nicht-Lineage-Verweis auf
`ADR 0003` bleibt `matrix-inactive` → Carve-out scoped, Gate nicht <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
geschwaecht). Doc-Archivierung nach `done-archive/` folgt mit der
M8-Meilenstein-Closure.
**Datum:** 2026-06-17
**Quelle:** Slice [`049`](../done/049-sdp-matrix-doku-umbau.md) §3 +
Trigger [`048`](048-dcheck-matrix-modul.md) (Out-of-Scope: Lineage-Carve-out).
d-check ist das Cross-Repo-Tool (`ghcr.io/pt9912/d-check`); das Feature wird
**dort** ergaenzt, nicht repo-lokal.

---

## Trigger

Die `status`-Regel des `matrix`-Moduls
([`.d-check.yml`](../../../../.d-check.yml),
`status: forbidden: [superseded, deprecated]`) flaggt **jede** Referenz auf
ein inaktives Dokument als `matrix-inactive` — auch die **legitime
Supersede-Lineage**: die abloesende ADR verweist per Definition auf die ADR,
die sie abloest (Lab-Regelwerk Regel 2: ADR→ADR-Lineage ist normativ). Das
`matrix`-Modul kennt heute **keinen** Carve-out dafuer.

**Konkreter Fall:** [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) (`Aenderungstyp: Supersedes ADR 0003`) <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
verweist in seinem `Bezug`-Header auf `ADR 0003` — normative Lineage, wird <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
aber als `matrix-inactive` gemeldet und bricht das fail-closed
`make docs-check`.

**Zweiter, verwandter Befund:** der zeilen-scoped
`<!-- d-check:ignore (...) -->`-Marker **unterdrueckt `matrix-inactive`
nicht** (greift nur fuer `codepaths`/`ids`). Damit fehlt aktuell *jeder*
saubere Einzelfall-Opt-out.

**Aktueller Workaround (Slice 049):** der Lineage-Link in [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) wurde
auf Inline-Code `ADR 0003` umgestellt (Referenz sichtbar, aber **nicht <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
klickbar**) — informationsaermer als noetig.

## Erwartete Lieferung (d-check-CR)

1. **Lineage-Carve-out (primaer):** eine Kante `X → Y` ist von
   `status: forbidden` ausgenommen, wenn `X` `Y` deklariert abloest.
   Erkennung ueber ein konfigurierbares Supersedes-Feld:

   ```yaml
   matrix:
     status:
       forbidden: [superseded, deprecated]
       allow-supersede-lineage: true
       supersede-fields: ["Supersedes", "Aenderungstyp"]
   ```

   Semantik: traegt `X` ein Feld aus `supersede-fields`, dessen Wert die ID/
   den Pfad von `Y` nennt, ist genau die Kante `X → Y` erlaubt — alle anderen
   Referenzen auf `Y` bleiben `matrix-inactive`.
2. **`d-check:ignore` fuer `matrix` (sekundaer):** der zeilen-scoped Marker
   soll **alle** Module abdecken (inkl. `matrix-inactive`/`matrix-forbidden`)
   — oder die Modul-Abdeckung wird in der d-check-README explizit dokumentiert.
3. **Spec/README** (`DC-FA-MTX-001`) um beide Optionen ergaenzt.

## Aktivierungs-Kriterium

d-check-Release mit `allow-supersede-lineage`-Option (bzw. `matrix`-faehigem
`d-check:ignore`). Dann grid-gym-Migration:

- `allow-supersede-lineage: true` in [`.d-check.yml`](../../../../.d-check.yml)
  setzen,
- in [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) den Inline-Code `ADR 0003` wieder auf den klickbaren <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
  `Bezug`-Link zuruecksetzen,
- `make docs-check` gruen verifizieren.

## Akzeptanzkriterien (Migration)

- **Happy:** mit aktivem Carve-out erzeugt [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) → ADR 0003 **keinen** <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
  `matrix-inactive`-Befund (weil [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) `ADR 0003` deklariert abloest). <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
- **Boundary:** eine *andere* (nicht-abloesende) Datei → `ADR 0003` bleibt <!-- d-check:ignore (ADR 0003 superseded — nur vom Supersedeer ADR 0006 verlinkbar) -->
  `matrix-inactive` (Carve-out auf die Lineage-Kante beschraenkt).
- **Negative/Default:** ohne die Option (Default) Verhalten bit-genau wie
  heute.

## Out-of-scope

- Allgemeine `from`-Klassen-Lineage jenseits ADR→ADR (Slice-Supersedes o. Ae.)
  — eigener Bedarf, falls je gefordert.
- Aenderung der grid-lokalen SDP-Klassen/Regeln (Slice 049 fixiert) — dieser
  Trigger betrifft nur den Tool-seitigen Carve-out.
