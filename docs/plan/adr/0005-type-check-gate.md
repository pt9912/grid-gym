# ADR 0005 — Type-Check-Gate (mypy --strict)

**Status:** Provisional — Spike-0-Gate live, Acceptance an ADR 0002 gekoppelt
**Datum:** 2026-05-14
**Status geaendert am:** 2026-05-14 — `Proposed → Provisional` synchron
zu ADR 0002; Operative Artefakte (Dockerfile-Stage `typecheck`,
Makefile-Target `make typecheck`, `[tool.mypy]`-Konfiguration im
Spike-0-Skelett) sind als validierter Pfad gemaess der
Provisional-Stufe der Lifecycle-Tabelle in `ADR 0006`
gekennzeichnet.
**Letzte inhaltliche Aenderung:** 2026-05-15 — Pre-Acceptance-Schliff
nach dem zweiten Review (`ADR 0006` §3): mypy-Floor von `>=1.13` auf
`>=2.0,<3.0` gehoben (mypy 2.x ist die aktuelle Major; Lock-resolved
auf `2.1.0`). 3.x-Upgrade benoetigt Nachfolge-ADR. Inhaltlich vorher:
2026-05-14 — Spike-Vertrag lokal ergaenzt, `[tool.mypy]`-Vertrag
verschaerft (`mutable-override`, expliziter `files`-Scope),
Wirkungsabschnitt in Provisional/Accepted aufgeteilt, Sachkorrektur
Option C (`pyrefly`), Querverweise gemaess `ADR 0004` auf Kennungen
umgestellt.
**Bezug:** [Lastenheft](../../../spec/lastenheft.md),
[Architektur](../../../spec/architecture.md),
[ADR 0002](0002-language-and-build-stack.md) (Sprach-Stack),
[ADR 0006](0006-adr-lifecycle-superseding-and-process-corrections.md) (Status-Werte),
[ADR 0004](0004-identifier-based-cross-references.md)
**Bedingt durch:** `ADR 0002` `Accepted`. Diese ADR liefert die
Konfiguration des vierten Spike-0-Gates (`mypy --strict`) im
Spike-0-Pflichtnachweis-Vertrag von `ADR 0002`; Acceptance erfolgt
synchron.

---

## 1. Kontext

`GG-QG-005` (Static-Analysis-Gate) sowie die Akzeptanzkriterien fuer
`GG-PRINC-004` (LSP) und `GG-PRINC-005` (ISP) sind in `ADR 0002` und
der V-Modell-Traceability-Matrix `GG-TRACE-001` (§27.1-Tabelle in
`spec/lastenheft.md`, Zeilen `GG-PRINC-004/005`) aktuell nur
teilweise automatisiert:

- `ruff` deckt SRP-/ISP-Heuristiken auf Klassen-Ebene
  (`PLR0902`/`PLR0903`/`PLR0904`) ab und liefert McCabe-Komplexitaet.
- `import-linter` + `tools/arch_check.py` decken DIP-Abhaengigkeiten
  und die Tabus aus `GG-AR-TABU-001..008` ab.
- **LSP (Liskov Substitution Principle)** und **strukturelle
  ISP-Pruefungen** (Protocol-Konformitaet, ob ein Klient nur eine
  Teilmenge eines Ports nutzt) sind weder von `ruff` noch von
  `import-linter` erfassbar — sie verlangen einen echten
  Type-Checker mit Variance- und Subtyp-Reasoning.

Diese ADR legt fest, mit welchem Werkzeug das geschieht und wie hart
das Gate ist.

---

## 2. Bewertungskriterien

Abgeleitet aus `GG-QG-005`, `GG-PRINC-004/005`, `GG-CC-005` (formale
Naming-Konsistenz auf Typebene) und der `uv`-getriebenen Toolchain aus
`ADR 0002`.

| Kennung   | Kriterium                                                                  | Gewicht |
| --------- | -------------------------------------------------------------------------- | ------- |
| K-VARI    | Variance-Pruefung (Subtypen verengen Parameter / weiten Return-Typen nicht) | P0      |
| K-PROTO   | Strukturelle Protocol-Konformitaet (Subtyp erfuellt Port-Protocol vollstaendig) statisch geprueft | P0      |
| K-STRICT  | „Strict"-Modus mit no-untyped-defs, no-implicit-Optional, etc. moeglich    | P0      |
| K-STUBS   | Stub-Versorgung fuer Stack: FastAPI, Pydantic v2, psycopg, structlog, OTEL | P1      |
| K-UV      | Integration in `uv`-Workspace, `dependency-groups`, lockfile-bar           | P1      |
| K-CI      | CI-Laufzeit unter ~30 Sekunden auf Spike-0-Skelett akzeptabel              | P1      |
| K-EDITOR  | Editor-Parity (gleiche Diagnose lokal wie in CI)                            | P2      |
| K-DEPS    | Keine Node.js-Toolchain noetig                                              | P2      |

---

## 3. Optionen

### Option A: `mypy --strict`

- Kanonischer Python-Type-Checker, PEP 484-Referenzimplementierung.
- Strict-Modus deckt: `disallow-untyped-defs`,
  `disallow-incomplete-defs`, `disallow-any-generics`,
  `warn-unused-ignores`, `warn-redundant-casts`,
  `no-implicit-optional`, `strict-equality`, `extra-checks`.
- Variance: vollstaendig (`K-VARI ✓`).
- Protocol-Konformitaet: gut, mit ein paar bekannten Loechern bei
  generischen Protocols (`K-PROTO o`).
- Stubs: Pydantic v2 liefert eigene Inline-Annotationen; FastAPI
  ebenso; `psycopg-stubs` separat. structlog und
  `opentelemetry-api` sind annotiert.
- CI-Laufzeit: typischerweise 5–15s auf einem Spike-0-Skelett.
- Pip-installierbar via `uv`, keine Node.js noetig (`K-DEPS ✓`).

### Option B: `pyright` (Microsoft)

- TypeScript-Style-Type-Checker, sehr schnell.
- Variance + Protocol-Konformitaet: state-of-the-art (`K-VARI ✓`,
  `K-PROTO ++`).
- Strict-Modus konfigurierbar via `pyproject.toml`
  `[tool.pyright]`.
- Standard-Toolchain in VSCode/Pylance (`K-EDITOR ++`).
- Benoetigt Node.js (oder das pyright-python-Wrapper-Package, das die
  Node-Binaries laedt).
- CI-Laufzeit: sehr schnell, oft < 5s.

### Option C: `pyrefly` (Meta, Rust-basiert)

- Junges Projekt (Stand 2026), noch nicht produktionsreif, keine
  etablierte CI-Praxis.
- Heute kein Gate-Kandidat — beobachten, in ein bis zwei Jahren neu
  bewerten.

---

## 4. Entscheidung

**`mypy --strict` als Pflicht-Gate.**

Begruendung:

- `K-VARI` (P0) und `K-STRICT` (P0) sind in beiden Tools erfuellt.
  `K-PROTO` (P0) ist bei `pyright` etwas besser, aber `mypy` reicht
  fuer unsere Port-Strukturen (Driving/Driven-Ports sind eindeutige
  Protocols, keine Generics-Akrobatik geplant). Re-Evaluation
  triggert, sobald `ports/` generische Protocols mit Variance-
  Annotationen einfuehrt (siehe offene Folge-Punkte).
- `K-DEPS`: `mypy` ist pip-installierbar und passt 1:1 in den
  `uv`-Workspace aus `ADR 0002`. Keine Node.js-Toolchain.
- `K-EDITOR`: Pylance (pyright-basiert) bleibt **freie
  Entwicklerwahl** im Editor — Editor-Diagnose und CI-Gate duerfen
  divergieren, weil Pylance regelmaessig restriktiver ist als
  `mypy`. Das ist akzeptabel: Editor warnt frueh, CI haelt das
  produktive Gate.
- `K-STUBS`: Pydantic v2, FastAPI, structlog, opentelemetry-api
  liefern eigene Annotationen; `psycopg-stubs` und
  `types-PyYAML` werden in der `typecheck`-Dependency-Group
  mitgeliefert.

Pyright wird **nicht** in CI verwendet, bleibt aber als optionales
Developer-Tool ueber Pylance dokumentiert.

---

## 4a. Validierungs-Spike-Vertrag

Lokaler Vertrag fuer den Provisional-Status (per Lifecycle-Pflicht aus
`ADR 0006`); die Durchfuehrung selbst geschieht im Spike-0 von
`ADR 0002`, dieses Gate ist der vierte Gate dort.

**Akzeptanzkriterium:** Im Spike-0-Skelett ist mindestens ein bewusst
herbeigefuehrter LSP- oder Protocol-Variance-Verstoss in einem
separaten Branch hinterlegt, der `mypy --strict` rot werden laesst,
ohne die anderen drei Gates (`lint-imports`, `ruff check`,
`arch_check.py`) zu beruehren. Auf `main` (sauberes Skelett) sind alle
vier Gates gruen.

**Dauer:** Innerhalb des Zeitfensters von Spike-0 (`ADR 0002`
nennt max. 5 Personentage); diese ADR fuegt keine zusaetzliche Dauer
hinzu.

**Erfolgs-Definition:** Akzeptanzkriterium erfuellt → `Provisional`
geht synchron mit `ADR 0002` auf `Accepted`.

**Misserfolgs-Definition:** Wenn das LSP-/Variance-Beispiel nicht
zuverlaessig rot wird (z. B. weil mypy in der gewaehlten Floor-Version
das Verschaerfungs-Pattern nicht erkennt), geht diese ADR auf
`Rejected`. Eine Folge-ADR mit anderem Type-Checker (z. B. `pyright`)
oder verschaerften enable_error_codes tritt an die Stelle. `ADR 0002`
selbst ist davon nicht zwingend betroffen — nur dieses vierte Gate.

---

## 5. Konsequenzen

### 5.1 Tooling und Konfiguration

- `mypy` und benoetigte Stubs landen in
  `pyproject.toml` `[dependency-groups]` `typecheck`. Mindestversion
  `mypy>=2.0,<3.0`: mypy 2.x ist seit 2026 die aktuelle Major-Version
  (Lock-resolved auf `2.1.0`). Die 2.x-Reihe behaelt
  `mutable-override` (seit 1.8) und `truthy-iterable` (seit 1.4) sowie
  alle weiteren `enable_error_code`-Eintraege aus dieser ADR
  unveraendert. Ein 3.x-Upgrade erfordert eine eigene Nachfolge-ADR,
  weil error-code-Renamings dort moeglich sind:

  ```toml
  [dependency-groups]
  typecheck = [
      "mypy>=2.0,<3.0",
      "psycopg[binary,pool]",      # liefert eigene types
      "types-PyYAML",
      "types-protobuf",            # falls Protobuf im Stack landet
  ]
  ```

- Strict-Konfiguration in `pyproject.toml`. Die meisten Settings sind
  redundant zu `strict = true`, werden aber explizit gefuehrt, damit
  der Vertrag dieser ADR ohne mypy-Versionsabgleich lesbar bleibt.
  Scope (zu pruefende Verzeichnisse) ist in der Konfiguration verankert,
  damit `make typecheck` und `mypy`-Aufruf von Hand denselben Vertrag
  haben:

  ```toml
  [tool.mypy]
  python_version = "3.13"
  # Scope: Produktionscode unter src/ plus Build-/Tool-Skripte.
  # tools/arch_check.py ist Gate-tragend und wird mitgeprueft.
  files = ["src/grid_gym", "tools"]
  strict = true
  warn_unused_configs = true
  warn_redundant_casts = true   # impliziert durch strict, fuer Lesbarkeit
  warn_unused_ignores = true    # impliziert durch strict, fuer Lesbarkeit
  warn_no_return = true
  warn_return_any = true        # impliziert durch strict, fuer Lesbarkeit
  warn_unreachable = true
  no_implicit_optional = true   # impliziert durch strict, fuer Lesbarkeit
  no_implicit_reexport = true
  strict_equality = true        # impliziert durch strict, fuer Lesbarkeit
  extra_checks = true           # impliziert durch strict, fuer Lesbarkeit
  enable_error_code = [
      "redundant-self",
      "possibly-undefined",
      "truthy-bool",
      "truthy-iterable",
      "unused-awaitable",
      "explicit-override",
      "mutable-override",       # LSP-Verschaerfung (mypy >= 1.8):
                                # Subklasse darf parent-Attribut nicht
                                # mit lockeren Typen ueberschreiben.
  ]
  # Hinweis: `redundant-expr` ist durch `extra_checks` (und damit durch
  # `strict`) bereits aktiv und wird hier nicht doppelt aufgefuehrt.

  [[tool.mypy.overrides]]
  # Tests duerfen typisierungsschwaecher sein (Fixtures, monkeypatch).
  module = "tests.*"
  disallow_untyped_defs = false
  warn_return_any = false
  ```

  Dritte-Partei-Pakete ohne Annotation werden **nicht** pauschal
  ignoriert. Sobald ein konkretes Modul auftritt, kommt eine eigene
  `[[tool.mypy.overrides]]`-Sektion mit `module = "paketname.*"`,
  `ignore_missing_imports = true` und Datum/ADR-/Issue-Verweis im
  Kommentar (Beispielformat siehe Migrations-Pfad).

- Dockerfile bekommt einen `typecheck`-Stage (eigenes Build-Target,
  ueber Makefile-Ziel `make typecheck` einzeln laufbar). Aufruf:
  `uv run mypy --config-file pyproject.toml` — Pfade kommen aus der
  `files`-Direktive, nicht aus der Kommandozeile, damit es genau eine
  Quelle fuer den Scope-Vertrag gibt.
- `Makefile`-Aggregator `gates` zieht `typecheck` zwischen
  `format-check` und `arch-check` mit; `ci` erbt es ueber `gates`.

### 5.2 Schliesst / verbindet

Bei Acceptance schliesst diese ADR die folgenden Trace-Lasten; die
genaue Wirkung pro Lifecycle-Stand steht im Wirkungs-Abschnitt:

- `GG-QG-005` (Static-Analysis-Gate, SOLLTE) erhaelt eine konkrete
  Pflicht-Implementierung.
- `GG-PRINC-004` (LSP) und `GG-PRINC-005` (ISP) werden auf
  automatisierter Type-Ebene abgedeckt; Restanteil bleibt
  Code-Review.
- `GG-CC-005` (sprechende Namen) bleibt heuristisch via `ruff N`;
  mypy ergaenzt nichts spezifisches.

### 5.3 Wirkung auf andere Dokumente

**Bei `Provisional`** (Spike-0 laufend) — bereits durch den
Spike-0-Pflichtnachweis-Vertrag in `ADR 0002` als vierter Gate
legitimiert:

- `pyproject.toml` `[dependency-groups]` `typecheck` und
  `[tool.mypy]` analog zum Tooling- und Konfigurationsabschnitt.
- `Dockerfile`-Stage `typecheck` (siehe `make typecheck`).
- `Makefile` Aggregator `gates`: `typecheck` zwischen
  `format-check` und `arch-check`.
- Die `GG-TRACE-001`-Matrix in `spec/lastenheft.md` darf auf
  diese ADR verweisen (V-Modell-Trace fuer
  `GG-PRINC-004/005`), aber `GG-QG-005` und
  `GG-PRINC-004/005` bleiben formal **nicht** als
  abschliessend automatisiert markiert (siehe
  Provisional-Stufe der Lifecycle-Tabelle in `ADR 0006`).

**Bei `Accepted`** (synchron zur Akzeptanz von `ADR 0002`):

- Die `GG-TRACE-001`-Matrix in `spec/lastenheft.md` markiert
  das Type-Check-Gate als geschlossene Implementierung fuer
  `GG-PRINC-004/005` (Variance + Protocol-Konformitaet);
  Restanteil bleibt Code-Review.
- `GG-QG-005` (Static-Analysis-Gate, SOLLTE) traegt diese ADR
  als verbindliche Pflicht-Implementierung.

### 5.4 Migrations-Pfad

- Spike-0 baut das Skelett **bereits mit `strict = true`** auf.
  Strikter Start ist billiger als spaeteres Nachziehen — ein leeres
  Repository hat keine Type-Schulden.
- Falls ein Adapter punktuell nicht strict-kompatibel ist
  (z. B. dynamische Protokoll-Bibliothek), kommt eine Per-Modul-
  Ausnahme ueber `[[tool.mypy.overrides]]` mit Datum und
  ADR-/Issue-Verweis im Kommentar, Format:

  ```toml
  [[tool.mypy.overrides]]
  # 2026-07-01, GG-AR-OPEN-XXX: pandapower-Wrapper hat keine
  # vollstaendigen Annotationen — Stubs in eigener ADR geplant.
  module = "grid_gym.adapters.pandapower.*"
  ignore_missing_imports = true
  ```

  Keine `# type: ignore`-Kommentare ohne Begruendung im Code.

---

## 6. Offene Folge-Punkte

- ADR fuer Pyright als optionales Pre-Commit-Hook fuer Entwickler-
  Maschinen (Trigger-basiert, sobald Editor-Parity-Druck entsteht).
- Re-Evaluation der Wahl `mypy` vs. `pyright`, sobald `ports/`
  generische Protocols mit Variance-Annotationen einfuehrt
  (`K-PROTO`-Argument verschiebt sich dann zugunsten pyright).
- ADR fuer Type-Coverage-Metrik (z. B. `mypy --html-report` mit
  Schwelle) — heute nicht noetig, weil `strict = true` alle Defs
  annotiert erzwingt; Restluecken (cast(), Any-Returns aus Drittlibs)
  bleiben moeglich und sind dann der Anlass fuer eine eigene
  Coverage-Schwelle.
- Aktivierung des `--strict-bytes` Modus (bei
  `bytes`/`str`-Trennscharfe) sobald das Domain-Modell konsolidiert
  ist (`GG-DATA-005` UTF-8-Bytes-Vertrag).

---

## 7. Nicht Gegenstand dieser ADR

- Wahl der Stub-Provider fuer einzelne Bibliotheken — folgt
  pragmatisch beim ersten Auftreten.
- Editor-Konfiguration (Pylance-Settings) — Entwicklerwahl.
- Type-Schulden-Audit fuer bestehenden Code — entfaellt, weil noch
  kein Code existiert.
