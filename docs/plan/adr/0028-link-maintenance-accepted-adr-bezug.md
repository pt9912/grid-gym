# ADR 0028 — Link-Maintenance an Accepted-ADR-`Bezug:`-Linien

**Status:** Proposed
**Datum:** 2026-05-23
**Bezug:**
[`ADR 0004`](0004-identifier-based-cross-references.md) §1 (Positions-
fragilitaet von Pfad-/Anker-Verweisen),
[`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
§3 (Aenderungsregeln nach `Accepted`),
[`ADR 0011`](0011-schaerfung-ohne-abloesung.md) (Schaerfung-ohne-
Supersedes-Pattern; ADR 0028 ist selbst eine Schaerfung von ADR 0006 §3
in dieser Form, nicht eine Pfad-Maintenance).

---

## 1. Kontext

`ADR 0006 §3` regelt Aenderungen an akzeptierten ADRs:

> Nach `Accepted` ist der Entscheidungstext immutable. Fachliche
> Aenderungen kommen als neue ADR, die die bestehende ADR abloest.
>
> Zulaessig bleiben nur Metadaten-Aenderungen an der alten ADR:
> Statuswechsel auf `Superseded`, `Status geaendert am`,
> `Superseded by`, ein kurzer Hinweis im Header, dass die ADR
> historisch ist.
>
> Keine zulaessige Metadaten-Aenderung sind neue Begruendungen,
> neue Regeln, erweiterte Scope-Definitionen oder korrigierte
> Konsequenzen. Solche Inhalte gehoeren in die Nachfolge-ADR.

Der enumerierte Zulaessig-Katalog ist auf Lifecycle-Metadaten
fokussiert (Status-Mechanik), die enumerierte Verbots-Liste auf
inhaltliche Edits („Begruendungen / Regeln / Scope /
Konsequenzen"). **Nicht explizit angesprochen** ist der Sonderfall,
dass eine verlinkte Ziel-Datei verschoben oder umbenannt wird (z. B. ein
Slice-Plan wandert von `planning/in-progress/` nach
`planning/done/`). Das Verweis-Ziel bleibt **inhaltlich gleich**,
nur sein Datei-Pfad aendert sich — und der Markdown-Link in der
ADR `Bezug:`-Zeile zeigt danach auf eine 404-Stelle.

In der Praxis wurde dieser Konflikt bisher per **Forwarder-Stub**
geloest: am alten Pfad bleibt eine 10–25-zeilige Stub-Datei
stehen, die auf das neue Ziel verweist. Stand 2026-05-23 gibt es
fuenf solche Stubs:

| Stub-Pfad                                              | Ziel                                                                 | Anker-ADRs (`Bezug:`-Linien)                                                  |
| ------------------------------------------------------ | -------------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `planning/in-progress/M1-tick-loop-spine.md`           | `planning/done/M1-tick-loop-spine.md`                                | ADR 0008, ADR 0009                                                            |
| `planning/in-progress/M2-devices.md`                   | `planning/done/M2-devices.md`                                        | ADR 0013, 0014, 0015, 0016, 0017, 0018, 0019, 0020, 0021                       |
| `planning/open/003-random-port-adr.md`                 | `planning/done/003-random-port-adr.md`                               | ADR 0007, ADR 0009                                                            |
| `planning/open/012-snapshot-composition.md`            | `planning/done/012-snapshot-composition.md`                          | ADR 0010                                                                       |
| `planning/next/M1-tick-loop-spine.md`                  | `planning/done/M1-tick-loop-spine.md`                                | ADR 0007                                                                       |

Das Stub-Pattern hat zwei strukturelle Schwaechen:

- **Es skaliert nicht.** Jede zukuenftige Restrukturierung unter
  `docs/plan/planning/` wuerde neue Stubs erzeugen. Nach drei
  Restrukturierungs-Runden traegt das `planning/`-Verzeichnis
  mehr Forwarder als Inhalt.
- **Es widerspricht der Ratio von `ADR 0004` §1.** ADR 0004
  begruendet die Kennungs-Pflicht primaer am Beispiel
  positionsabhaengiger Abschnitts-Verweise (`§4.2`, Anker am
  Titel-Slug) — sie sind „positionsfragil" und „brechen still bei
  Strukturaenderungen". Die gleiche Klasse von Positionsfragilitaet
  trifft Markdown-Pfad-Links bei Datei-Verschiebung: das
  Verweis-Ziel ist identifiziert ueber seine Lage im Dateisystem.
  Der Stub-Forwarder konserviert diese Fragilitaet, statt sie zu
  beheben.

`ADR 0006 §3` und `ADR 0004` §1 ziehen damit in dieselbe
Richtung: Pfad-Pflege ist nicht „fachliche Aenderung", sondern
genau die Art von Maintenance, die ADR 0004 §1 als Konsequenz
positionsabhaengiger Verweise vorsieht.

---

## 2. Entscheidung

Ein **Pfad-Update an einer Markdown-Hyperlink-URL in einer
`Bezug:`-Linie einer Accepted-ADR** ist **keine fachliche
Aenderung** im Sinne von `ADR 0006 §3`, sofern alle drei
Bedingungen erfuellt sind:

1. **Inhaltliche Identitaet des Ziels:** Die Ziel-Datei ist nach
   der Pfad-Aenderung inhaltlich dieselbe wie vorher (reine
   Verschiebung, Umbenennung oder Restrukturierung, ohne den
   Entscheidungs-/Kontext-Inhalt des Ziels zu aendern).
2. **Linktext-Identitaet oder rein syntaktische Mitfuehrung:**
   Der Linktext (das Markdown-Label vor der URL) bleibt
   unveraendert oder spiegelt **nur** den neuen Pfad-Namen wider
   (z. B. `\`in-progress/M2-devices.md\`` → `\`done/M2-devices.md\``).
   Keine neue inhaltliche Beschreibung wird hinzugefuegt.
3. **Keine Verweis-Mengen-Aenderung:** Es wird kein zusaetzlicher
   Verweis hinzugefuegt, keiner entfernt und keiner inhaltlich
   neu interpretiert. Das Verweis-Netz bleibt strukturell gleich.

Solche Pfad-Fixups sind als **Maintenance-Edits** zulaessig und
sollen im selben Commit wie die ausloesende Datei-Verschiebung
durchgefuehrt werden (oder unmittelbar danach, wenn die
Verschiebung durch einen separaten Slice-Closure-Commit
erfolgt ist).

Pfad-Fixups, die mehr als ein Marker-Symbol pro ADR-Bezug-Linie
beruehren (z. B. eine ganze Stub-Cleanup-Welle), werden in einem
Commit zusammengefasst und in der Commit-Message explizit auf
ADR 0028 als Erlaubnis-Anker verwiesen.

---

## 3. Abgrenzung zu `ADR 0006` §3

`ADR 0006 §3` enumeriert die verbotenen Aenderungs-Klassen:

- neue Begruendungen
- neue Regeln
- erweiterte Scope-Definitionen
- korrigierte Konsequenzen

Ein Pfad-Fixup nach §2 ist **keine** dieser Klassen — der
Entscheidungstext bleibt syntaktisch identisch, nur der URL-Teil
eines Hyperlinks zeigt auf den neuen Ablageort derselben
Inhalts-Datei. ADR 0028 nimmt `ADR 0006` §3 nichts weg; sie
stellt klar, dass §3 dieses Maintenance-Szenario nicht meint.

`ADR 0006 §3` bleibt **textlich unveraendert** (Accepted-
Immutability per `ADR 0006 §3` selbst). ADR 0028 liegt parallel
neben `ADR 0006 §3`, beide gelten gemeinsam. Das entspricht
exakt dem Schaerfung-ohne-Supersedes-Muster aus `ADR 0011`.

---

## 4. Abgrenzung zu `ADR 0004`

`ADR 0004` §1 begruendet die Pflicht-Regel fuer kennungsbasierte
Verweise mit der Positionsfragilitaet markdown-basierter Pfade
und `§…`-Verweise. Slice-Plaene unter `docs/plan/planning/`
besitzen heute **keine eigene Kennung** (`GG-*`/`AC-*`/`ADR n`);
die `Bezug:`-Zeile verwendet daher zwangslaeufig einen
Markdown-Pfad als primaeren Verweis.

Solange kein Kennungsraum fuer Slice-Plaene besteht, ist die
Pflege der Pfad-Links die naheliegende und mit ADR 0004 §1
konsistente Antwort auf Verzeichnis-Umzuege. ADR 0028 aendert
`ADR 0004` §3 (Retrofit-Regel fuer `§…`-Verweise) **nicht**;
sie betrifft ausschliesslich Markdown-Hyperlink-URLs in
`Bezug:`-Linien.

Die Einfuehrung eines Slice-Plan-Kennungsraums (z. B.
`GG-SLICE-M1`, `GG-SLICE-M2`) bleibt explizit out-of-scope
dieser ADR.

---

## 5. Operative Folge

**Erstanwendung von ADR 0028** ist das Aufraeumen der oben in
§1 tabellierten fuenf Forwarder-Stubs. Konkret:

- Die `Bezug:`-Pfade in den 13 Anker-ADRs (0007, 0008, 0009,
  0010, 0013, 0014, 0015, 0016, 0017, 0018, 0019, 0020, 0021)
  werden auf die `planning/done/`-Ziele umgestellt — je ADR
  eine Zeile, gleiches Linktext-Schema, kein Inhalts-Edit.
- Die fuenf Stub-Dateien werden geloescht.
- Begleit-Updates in Planungs-Dokumenten (`roadmap.md`,
  `planning/done/welle-*.md`, `planning/*/README.md`,
  weitere referenzierende Slice-Plaene) ziehen die Pfade
  konsistent nach.
- Der ADR-Index `docs/plan/adr/README.md` traegt ADR 0028 in der
  „Aktive ADRs"-Tabelle ein und ergaenzt die ADR-0006-Zeile in
  der „Schaerfungen / Folge-ADRs"-Spalte um den Querverweis auf
  ADR 0028 (analog zum bestehenden ADR-0011-Eintrag).

**Zukuenftige Anwendung:** wenn ein Slice-Plan oder eine andere
referenzierte Planungs-Datei verschoben wird, werden die
`Bezug:`-Pfade in betroffenen Accepted-ADRs **im selben Slice-
Closure-Commit** mitgezogen. Forwarder-Stubs werden nicht mehr
angelegt.

---

## 6. Konsequenzen

- **Positiv:** Verzeichnis-Restrukturierungen unter
  `docs/plan/planning/` erzeugen keine permanente Forwarder-
  Schicht mehr; das `planning/`-Verzeichnis bleibt auf Inhalt
  fokussiert.
- **Positiv:** Accepted-ADRs bleiben durch reine Pfad-Pflege
  wartbar, ohne dass dafuer eine Nachfolge-ADR pro betroffener
  Original-ADR aufgemacht werden muesste (eine Nachfolge-ADR pro
  Pfad-Move waere unverhaeltnismaessig; das war ein verstecktes
  Hemmnis des Stub-Patterns).
- **Positiv:** Der Edit-Diff ist konventionell auf eine
  `Bezug:`-Zeile (oder wenige Zeilen, falls mehrere Slice-Plaene
  referenziert werden) begrenzt. Reviewer koennen so leicht
  pruefen, dass die Aenderung nur Maintenance ist.
- **Neutral:** Die fuenf bestehenden Stubs sind in ihrem
  Header-Text schon explizit als „Link-Stabilitaets-Garantie
  fuer ADR 0006 §3" begruendet. Mit ADR 0028 entfaellt diese
  Begruendung; die Loeschung im §5-Cleanup ist konsequent.
- **Neutral:** Eine ADR mehr im Index.

---

## 7. Nicht Gegenstand dieser ADR

- Einfuehrung eines Kennungsraums fuer Slice-Plaene (eigener
  Folge-ADR, falls noetig).
- Automatisierte Link-Validierung (`tools/check_refs.py` existiert
  bereits als Trigger-002-Closure 2026-05-17 mit Welle-7-Audit;
  eine Erweiterung um automatische Pfad-Migration ist
  Routinearbeit, kein ADR-Stoff).
- Inhaltliche Aenderungen an Accepted-ADRs ueber Pfad-Links
  hinaus — die bleiben unter `ADR 0006 §3` vollumfaenglich
  verboten.
- Migration der Markdown-`Bezug:`-Linien auf einen kuenftigen
  Slice-Plan-Kennungsraum (waere fachliche Aenderung im Sinne
  von ADR 0006 §3 und braeuchte eigene Folge-ADRs pro betroffener
  Anker-ADR).
