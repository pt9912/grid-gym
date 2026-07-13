# bess-ems-Feldvertrags-Fixtures (vendored)

**Quelle:** Schwesterprojekt `bess-ems`, Stand **v2.1.0** (`v2.1.0-8-g0512b17`).
Wortgleich uebernommen aus `bess-ems/config/schema/`:

- `mqtt-telemetry-envelope.schema.json` — der feld-normative Wire-Vertrag
  (`$defs.telemetry`/`command`/`command_ack`); **Typ-Autoritaet** fuer die
  Encoder-Tests (Slice 077 S2).
- `mqtt-golden-vectors.field.v1.json` — die field-authority-Golden-Vektoren
  (`telemetry`/`status`/`fault`/`command_ack`); **strukturelle** Abnahme
  (Feld-Praesenz/Namen; **nicht** wertgenau).

**Warum vendored:** der Docker-Test-Container mountet nur das grid-gym-Repo; das
bess-ems-Repo ist zur Testzeit nicht erreichbar. Der Vertrag ist ein **publiziertes
Artefakt** (bess-ems' Feldvertrags-ADR §5) — hier reproduzierbar eingefroren.

**Drift-Watch:** bei einem bess-ems-Contract-Bump (neuer `v*`-Tag mit Aenderung an
`config/schema/`) diese Fixtures neu ziehen + die Encoder anpassen. Das
Envelope-Schema ist seit v2.0.0 unveraendert; die Golden-Vektoren kamen mit v2.1.0.
