# 056 — ADR-Index-Statusspalte: 10 Zeilen hinter den Datei-Headern (Index-Drift)

**Status:** Done — 2026-07-10 (Buendel-Closure via Slice 059)
**Datum:** 2026-07-03
**Quelle:** Slice-038-Closure-Handoff (Befund beim README-Status-Sync
fuer v0.3.0 verifiziert).

---

## Befund

Die Statusspalte im ADR-Index
([`docs/plan/adr/README.md`](../../adr/README.md)) zeigt fuer elf
Zeilen `Provisional`, obwohl die ADR-Dateien selbst (Header-Feld
`Status:`, kanonisch per [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) §4)
laengst `Accepted` sind — die Meilenstein-ADR-Sweeps (M3-/M5-Closure)
haben die **Dateien** gezogen, aber die **Index-Spalte** nicht
nachgezogen. Stichproben-verifiziert 2026-07-03:

- Index `Provisional`, Datei **`Accepted`**: [`ADR 0022`](../../adr/0022-fault-injection-protocol.md)
  (M3-Welle-7-Closure), [`ADR 0024`](../../adr/0024-observability-port-trio.md)
  (M3-Welle-7-Closure), [`ADR 0036`](../../adr/0036-ui-stack-choice.md)
  (M5-Welle-7), [`ADR 0039`](../../adr/0039-run-control-and-status-tracking.md)
  (M5-Welle-7-C1).
- Betroffene Index-Zeilen insgesamt: `0008`, `0022`..`0027`,
  `0036`, `0038`..`0040` (11 Zeilen; vermutlich 10 davon Drift).
- [`ADR 0008`](../../adr/0008-enum-as-domain-frozen-form.md) ist laut
  eigenem Header tatsaechlich noch `Provisional` — bei Aufloesung
  pruefen, ob das bewusst so ist oder ein vergessener Sweep.

Folge-Inkonsistenz: die README-Statuszeile („69 von 71 ADRs
`Accepted` (1 `Provisional`, 1 `Superseded`)" in
[`README.md`](../../../../README.md)/[`README.de.md`](../../../../README.de.md))
passt weder zur Index-Spalte (61/11/1 bei 73 ADRs) noch exakt zum
Datei-Stand.

## Erwartete Lieferung

- Index-Spalte gegen die Datei-Header abgleichen (Datei-Header ist
  die kanonische Quelle, [`ADR 0006`](../../adr/0006-adr-lifecycle-superseding-and-process-corrections.md) §4;
  die Index-Konvention sagt selbst „diese Tabelle reflektiert sie").
- [`ADR 0008`](../../adr/0008-enum-as-domain-frozen-form.md)-Status klaeren
  (bewusst `Provisional` vs. vergessener Sweep) — bei Sweep-Luecke
  Status-Pfad in der Datei nachziehen.
- README-/README.de-ADR-Zaehlung auf den abgeglichenen Stand
  korrigieren (aktuell 73 ADRs gesamt).
- Doku-only → Release-Entscheidung **nein**.

## Aktivierungs-Kriterium

Naechster Doku-/Hygiene-Slice (Buendel-Kandidat mit
[`057`](057-app-version-single-source.md); 054-Marker-Sweep
2026-07-10 erledigt → `done/`) ODER der naechste
ADR-Decision-Sweep.

## Wandert nach

`done/`, sobald Index-Spalte, Datei-Header und README-Zaehlung
konsistent sind.

---

## Closure 2026-07-10 (Slice 059)

Geliefert im Hygiene-Buendel [`059`](059-hygiene-bundle-adr-index-app-version.md):
10 Drift-Zeilen (0022–0027, 0036, 0038–0040) im Index auf `Accepted`
angeglichen; [`ADR 0008`](../../adr/0008-enum-as-domain-frozen-form.md) als
vergessener M1-Welle-1-Sweep auf `Accepted` nachgezogen (Datei-Header + Index,
Substanz `_inherits_enum`/[`AC-DOMAIN-FROZEN`](../../adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) gruen); README/README.de melden
jetzt **72 von 73 ADRs `Accepted` (1 `Superseded`, 0 `Provisional`)**.
`make docs-check` gruen. Details + DoD in Slice 059.
