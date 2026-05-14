# ADR 0005 — Type-Check-Gate (mypy --strict)

**Status:** Proposed — Entscheidung bedingt
**Datum:** 2026-05-14
**Bezug:** [Lastenheft](../../../spec/lastenheft.md),
[Architektur](../../../spec/architecture.md),
[ADR 0002](0002-language-and-build-stack.md) (Sprach-Stack),
[ADR 0003](0003-adr-lifecycle.md) (Status-Werte),
[ADR 0004](0004-identifier-based-cross-references.md)
**Bedingt durch:** `ADR 0002` `Accepted`. Solange `ADR 0002` auf
`Proposed`/`Provisional` steht, ist auch diese ADR nicht aktivierbar;
sie wandert zeitgleich mit `ADR 0002` auf `Accepted`.

---

## 1. Kontext

`GG-QG-005` (Static-Analysis-Gate) sowie die Akzeptanzkriterien fuer
`GG-PRINC-004` (LSP) und `GG-PRINC-005` (ISP) sind in `ADR 0002` und
`§27.1` aktuell nur teilweise automatisiert:

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
| K-PROTO   | Protocol-/`@runtime_checkable`-Konformitaet automatisch geprueft            | P0      |
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

### Option C: `pyrefly` (Pytype-Nachfolger)

- Junges Projekt (Stand 2026), noch keine etablierte CI-Praxis.
- Heute kein Gate-Kandidat — beobachten, in ein bis zwei Jahren neu
  bewerten.

---

## 4. Entscheidung

**`mypy --strict` als Pflicht-Gate.**

Begruendung:

- `K-VARI` (P0) und `K-STRICT` (P0) sind in beiden Tools erfuellt.
  `K-PROTO` (P0) ist bei `pyright` etwas besser, aber `mypy` reicht
  fuer unsere Port-Strukturen (Driving/Driven-Ports sind eindeutige
  Protocols, keine Generics-Akrobatik geplant).
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

## 5. Konsequenzen

### 5.1 Tooling und Konfiguration

- `mypy` und benoetigte Stubs landen in
  `pyproject.toml` `[dependency-groups]` `typecheck`:

  ```toml
  [dependency-groups]
  typecheck = [
      "mypy>=1.13",
      "psycopg[binary,pool]",      # liefert eigene types
      "types-PyYAML",
      "types-protobuf",            # falls Protobuf im Stack landet
  ]
  ```

- Strict-Konfiguration in `pyproject.toml`:

  ```toml
  [tool.mypy]
  python_version = "3.13"
  strict = true
  warn_unused_configs = true
  warn_redundant_casts = true
  warn_unused_ignores = true
  warn_no_return = true
  warn_return_any = true
  warn_unreachable = true
  no_implicit_optional = true
  no_implicit_reexport = true
  strict_equality = true
  extra_checks = true
  enable_error_code = [
      "redundant-self",
      "redundant-expr",
      "possibly-undefined",
      "truthy-bool",
      "truthy-iterable",
      "unused-awaitable",
      "explicit-override",
  ]

  [[tool.mypy.overrides]]
  # Tests duerfen typisierungsschwaecher sein (Fixtures, monkeypatch).
  module = "tests.*"
  disallow_untyped_defs = false
  warn_return_any = false

  [[tool.mypy.overrides]]
  # Dritte-Partei-Pakete ohne Annotation als Insel; nicht ignorieren,
  # sondern explizit pro Modul whitelisten, wenn sie auftreten.
  module = []
  ignore_missing_imports = true
  ```

- Dockerfile bekommt einen `typecheck`-Stage (eigenes Build-Target,
  ueber Makefile-Ziel `make typecheck` einzeln laufbar).
- `Makefile`-Aggregator `gates` zieht `typecheck` zwischen
  `format-check` und `arch-check` mit; `ci` erbt es ueber `gates`.

### 5.2 Schliesst / verbindet

- `GG-QG-005` (Static-Analysis-Gate, SOLLTE) bekommt damit eine
  konkrete Pflicht-Implementierung.
- `GG-PRINC-004` (LSP) und `GG-PRINC-005` (ISP) sind auf
  automatisierter Type-Ebene abgedeckt; Restanteil bleibt
  Code-Review.
- `GG-CC-005` (sprechende Namen) bleibt heuristisch via `ruff N`;
  mypy ergaenzt nichts spezifisches.

### 5.3 Wirkung auf andere Dokumente

Die folgenden Aenderungen werden **erst bei `Accepted`** ausgefuehrt
(parallel zur Akzeptanz von `ADR 0002`):

- `pyproject.toml` `[dependency-groups]` und `[tool.mypy]` analog
  zu §5.1.
- `Dockerfile`-Stage `typecheck` (siehe `make typecheck`).
- `Makefile` Aggregatoren: `typecheck` Teil von `gates`.
- `§27.1`-Eintraege fuer `GG-PRINC-004/005` werden um konkreten
  ADR-Verweis erweitert.

### 5.4 Migrations-Pfad

- Spike-0 baut das Skelett **bereits mit `strict = true`** auf.
  Strikter Start ist billiger als spaeteres Nachziehen — ein leeres
  Repository hat keine Type-Schulden.
- Falls ein Adapter punktuell nicht strict-kompatibel ist
  (z. B. dynamische Protokoll-Bibliothek), kommt eine Per-Modul-
  Ausnahme ueber `[[tool.mypy.overrides]]` mit Datum und
  ADR-/Issue-Verweis. Keine `# type: ignore`-Kommentare ohne
  Begruendung im Code.

---

## 6. Offene Folge-Punkte

- ADR fuer Pyright als optionales Pre-Commit-Hook fuer Entwickler-
  Maschinen (Trigger-basiert, sobald Editor-Parity-Druck entsteht).
- ADR fuer Type-Coverage-Metrik (z. B. `mypy --html-report` mit
  Schwelle) — heute nicht noetig, weil `strict = true` ohnehin
  100% Coverage erzwingt.
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
