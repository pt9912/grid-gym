# 089 — d-check `trace`: Design-Konsistenz-Gate (Change Request an d-check)

**Status:** **Geliefert + Abnahme bestanden (2026-07-17), aber bewusst NICHT
verdrahtet.** d-check hat die Fähigkeit als `trace.cross-consistency` umgesetzt
(v0.44.0), plus zwei Nachbesserungen aus unseren Befunden: link-transparente
Range-Fortsetzung (v0.44.1/v0.45.1) und `forward.req-pattern` (v0.45.0). Die
Abnahmekriterien §9 (1)–(3) sind gegen die Realdaten **bestanden**. Der Abgleich wird
dennoch **nicht als Gate verdrahtet**, sondern einmalig als Messinstrument benutzt —
siehe [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §4.4-4-Amendment und
„Anschlussschritte" unten. Kein Code-/Spec-Delta in grid-gym.
**Datum:** 2026-07-16 (Lieferung/Abnahme 2026-07-17)
**Adressat:** d-check (`ghcr.io/pt9912/d-check`)
**Quelle:** [`Trigger 088`](088-27-1-consistency-gate-generator.md) ·
[`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §4.4 (iii)
**Gegenstück:** [`Trigger 088`](088-27-1-consistency-gate-generator.md) bleibt der
grid-gym-seitige Watch; **dieses** Dokument ist die an d-check adressierte
Anforderung — die Cross-Repo-Kante ist damit dokumentiert, kein Dead-Letter.

---

## Verlauf

- **v1** an den d-check-Projekt-Agenten übergeben.
- Agent antwortete mit **6 konkreten Umbau-Punkten** — alle angenommen (unten).
- **v2** (Abschnitt „CR v2") = v1 + die 6 Punkte. **Nächster Schritt:** v2 an
  d-check zurückspielen; auf Feature-Release warten, dann grid-gym-seitig
  verdrahten (Abschnitt „Anschlussschritte").

## Eingearbeitete Agenten-Punkte (v1 → v2)

1. **Header-Binding statt Position** — Zellbindung per exaktem Header-Namen (wie
   das gelieferte `trace.requirements.table`, DC-FA-REQ-001); alle
   Positions-Indizes (`*-col: 0/1`) raus.
2. **Forward auf `trace.coverage` aufsetzen** — die Vorwärts-Tabelle über die
   vorhandene `coverage[]`-Extraktion (range-aware, Section-Whitelist/Blacklist)
   lesen, **kein** zweiter Tabellen-Parser.
3. **Eine Pattern-Syntax** — alle ID-Felder RE2 (`…-\d+`), kein Glob-`*`-Mix
   (d-check: Globs = Go `path.Match`, IDs = RE2 — nicht mischen).
4. **Generischer Rückkanten-Vertrag** — „gelabelte Referenz-Listen-Spalte in
   verankerter Artefakt-Tabelle"; das Kanten-Label ist Config, kein Kern-Keyword.
   Vor Config-Freeze an ≥1 zweitem Konsumenten gegenprüfen (Portabilität über
   grid-gym hinaus unbewiesen).
5. **Ausschluss-Ventil = bewusster Trade-off** — `exclude-req` (Zwischenschicht,
   §6) ist eine kuratierte Kante, die selbst driften kann; im ADR als solcher
   Trade-off benennen, nicht als „gelöst".
6. **Generator raus** — v1 = nur das Gate. Der Generator (Schreib-Pfad, näher an
   `--repair`/DC-FA-CLI-008 als an `--trace`) wird eine **eigene spätere CR** mit
   eigener ADR-Behandlung — nicht mit dem Gate verheiratet.

---

## CR v2 (zum Zurückspielen an d-check)

### 1. Problem

Anforderung→Design wird in zwei unabhängig gepflegten Sichten geführt: einer
**Vorwärts-RTM** (Anforderung → Menge Design-Artefakte, z. B. §27.1) und
**Rückwärts-Kanten** (jedes Artefakt nennt aufwärts die Anforderungen, die es
umsetzt). Beide driften unbemerkt. Realer Fall: §27.1 für ARCH-005 nennt
`{COMP-CORE, COMP-DOMAIN}`, die Rückkanten auf ARCH-005 kommen aber von
`{P-005, P-009, COMP-SCHED}` — Schnittmenge null.

### 2. Warum bestehende Module nicht reichen

`matrix` = Verweis-Richtung, nicht Mengengleichheit. `trace.coverage` =
Abdeckung (≥1 Design je Anforderung), nicht die konkreten Mengen. `ids`/`anchors`
= Existenz/Verlinkung. Keins vergleicht zwei unabhängig gepflegte Kanten-Mengen
und meldet die Differenz.

### 3. Kern-Fähigkeit (iii) — nur das Gate

Je Anforderungs-ID `R`: **F(R)** = Design-Artefakte aus der Vorwärts-RTM,
**B(R)** = Artefakte, deren Rückkante `R` nennt. Melde je `R` die Differenzen
`F(R)\B(R)` und `B(R)\F(R)` mit Richtungslabel. **1:N ist Normalfall** (ARCH-007
= fünf Kanten), nicht 1:1. **Modus** `equal` (F=B) oder `superset` (F⊇B).

### 4. Wiederverwendung statt neuem Parser (Punkt 1+2)

Beide Seiten sind kuratierte Tabellen → **derselbe header-gebundene Reader**:
`trace.requirements.table` (DC-FA-REQ-001, Zellbindung per exaktem Header-Namen)
plus die `trace.coverage[]`-Section-/Span-Semantik. Die einzige **neue** Logik ist
Invertierung + Mengenvergleich. d-check entscheidet, ob geteilter Reader oder
Extension.

### 5. Generischer Rückkanten-Vertrag (Punkt 4)

Der Rückkanten-Extraktor ist der portabilitätskritische Teil. Konsumenten-neutral:

> Eine **verankerte Tabelle** (Span), deren Zeilen je ein Design-Artefakt sind, mit
> (a) einer **header-gebundenen Artefakt-ID-Spalte** (oder Zeilen-Anker) und (b)
> einer **header-gebundenen Referenz-Listen-Spalte**, deren Zellwert eine Liste von
> Anforderungs-IDs (`req-pattern`, RE2) ist.

Kein grid-gym-spezifisches Kanten-Keyword im Kern — der Spaltenname ist Config.
**Empfehlung:** vor Config-Freeze an einem zweiten Konsumenten gegenprüfen;
grid-gym stellt die Referenz-Instanz (`spec/architecture.md`-„Bezug"-Spalten).

### 6. Zwischenschicht-Ableitungssprünge (Punkt 5)

Bei mehrschichtigen Spec-Modellen (Vertrag→Spezifikation→Architektur) liegt das
Design mancher Anforderungen in einer Mittelschicht, deren Artefakte keine
RTM-Vorwärts-Zeilen sind; Rückkanten können auf Mittelschicht-IDs zeigen.
Ausschluss per `exclude-req` (RE2). **Bewusster Trade-off:** dieses Ventil ist
selbst eine kuratierte Kante, die mit der Schicht-Struktur synchron bleiben muss
und driften kann (wie `exclude-sections`) — im ADR als solcher benennen.

### 7. Pattern-Syntax (Punkt 3)

Alle ID-Felder **RE2** (analog `id-pattern`/`req-pattern`), keine Glob-Alternation.

### 8. Config-Oberfläche (Vorschlag — d-check besitzt die finalen Schlüssel)

```yaml
trace:
  design-consistency:
    forward:                       # Anforderung -> Design-Menge; erbt coverage[]
      coverage-ref: "27.1"         # vorhandene Section-/Span-Semantik
      id-column: "Anforderung"     # header-gebunden
      design-column: "Design"      # header-gebunden
      design-pattern: "GG-AR-[A-Z0-9-]+"          # RE2
    backward:                      # generischer Rückkanten-Vertrag (§5)
      file: spec/architecture.md
      artifact-id-column: "Komponente"            # header-gebunden (oder Anker)
      edge-column: "Bezug"                        # header-gebunden; Name = Config
      req-pattern: "GG-(ARCH|SIM|RT|SAFE)-\d{3}"  # RE2
    mode: equal                    # equal | superset
    exclude-req: "GG-(PRINC|CC|SEED|QA|QG|COV|TESTTYPE|ARCHTEST)-\d+"   # RE2, §6
    require-complete: false        # advisory, bis Konsument scharfstellt
```

### 9. Ausgabe & Abnahme

Pro Differenz `Datei:Zeile` + Anforderungs-ID + fehlende/überzählige Menge mit
Richtung. Exit ≠ 0 nur bei `require-complete: true`. Abnahme gegen grid-gym:
(1) flaggt die ARCH-005- und ARCH-006-Drift; (2) flaggt die nach
`spec/spezifikation.md` verschobenen Familien **nicht** (Ventil §6 greift);
(3) konsistentes 1:N (ARCH-007) grün; (4) advisory vs. Gate über
`require-complete`.

### 10. Ausdrücklich außerhalb dieser CR

Der **Generator** (RTM aus Rückkanten erzeugen) ist eine eigene spätere CR mit
eigener ADR-Behandlung. v1 = nur Gate.

---

## grid-gym-Anschlussschritte (überholt — 2026-07-17)

**Schritt 2/3 sind zurückgenommen.** Das Verdrahten als **dauerhaftes** Gate entfällt:
§27.1 ist kein Spiegel der Bezug-Kanten, sondern eine kuratierte Vorwärts-Map. Gemessen:
161 Differenzen = 86 `F\B` + 75 `B\F`, wovon **65** der `B\F` Absicht sind
(Ports/Prinzipien/Nicht-Haupt-Komponenten) — `mode: equal` bliebe damit dauerhaft rot.
Die übrigen 10 sind **echte** Befunde und wandern in die Arbeitsliste (6× Phantom-Kanten in
die Nummernlücke der `GG-DEV-*`-Familie, 2× Drift —
[`GG-ARCH-005`](../../../../spec/lastenheft.md#gg-arch-005) und
[`GG-SIM-009`](../../../../spec/lastenheft.md#gg-sim-009) —, 2× Parser-Artefakt).
Begründung + Aufschlüsselung:
[`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §4.4-4.

Stattdessen, gemäß dem umgeschnittenen
[`Trigger 088`](088-27-1-consistency-gate-generator.md):

1. **Einmal-Lauf als Messinstrument** → Arbeitsliste sind **beide** Richtungen: 85 echte
   `F\B` über 62 Anforderungen (86 minus 1 Wildcard-Phantom) **und** die 8 echten `B\F`
   (= die §2d-Vorbedingung des `derived`-Wechsels). Fixtures für d-check erübrigen sich:
   die Abnahme lief direkt gegen die Realdaten.
2. **Kanten-Anmerkungen umziehen** §27.1 → `Bezug`-Zelle (Notation im §4.4-4-Amendment).
3. **Nachfolge-CR an d-check:** der **Generator** (§10 dieser CR — „eigene spätere CR"),
   mit den zwei Anforderungen, die erst die Messung sichtbar gemacht hat: Artefakt-Titel
   mitausgeben und Kanten-Anmerkung durchreichen.

### Abnahme-Ergebnis (§9, gegen die Realdaten statt gegen Fixtures)

| Kriterium | Ergebnis |
| --- | --- |
| (1) flaggt ARCH-005-/ARCH-006-Drift | **bestanden** — ARCH-005 zeigt beide Richtungen (`F\B = {COMP-CORE, COMP-DOMAIN}`, `B\F = {COMP-SCHED, P-005, P-009}`), exakt die „Schnittmenge null" aus §1 |
| (2) Mittelschicht-Familien nicht geflaggt (Ventil §6) | **bestanden** — 0 Befunde |
| (3) konsistentes 1:N (ARCH-007) grün | **bestanden** — 0 Differenzen |
| (4) advisory vs. Gate über `require-complete` | strukturell erfüllt; nicht verdrahtet |

Anmerkung zu (1)/(3): Beide bestanden **erst** ab v0.45.0. Bis v0.44.1 filterte die
Vorwärts-Sicht still über `trace.requirements.id-pattern` — mit unserer bewusst
gescopten RTM (ohne Arch-Meta) war `F(R)` leer, (1) sah nur wie ein Treffer aus und (3)
fiel durch. Der Befund führte zu `forward.req-pattern`.

## Bezug

- [`Trigger 088`](088-27-1-consistency-gate-generator.md) (grid-gym-seitiger Watch),
  [`ADR 0080`](../../adr/0080-three-layer-spec-model.md) §4.4 (iii)/(iv).
- Konsumenten-Instanz: `spec/architecture.md`-„Bezug"-Spalten,
  `docs/plan/traceability.md` §27.1.
