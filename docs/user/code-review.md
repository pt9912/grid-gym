# Code-Review-Leitfaden grid-gym

**Status:** Aktiv seit 2026-05-15 (Post-Spike-0-Acceptance)
**Bezug:**
[`ADR 0002`](../plan/adr/0002-language-and-build-stack.md) §A-1
„Code-Review-Auflage fuer TABU-003" (Trigger 001 abgearbeitet);
[`ADR 0005`](../plan/adr/0005-type-check-gate.md) §5.1 (mypy-Strict-
Reichweite); [`ADR 0006`](../plan/adr/0006-adr-lifecycle-superseding-and-process-corrections.md)
§3 (Immutability-Vertrag fuer akzeptierte ADRs).

---

## 1. Zweck

Statische Analyse-Tools (`ruff`, `mypy --strict`, `import-linter`,
`tools/arch_check.py`) decken **15 von 16** A-1-Contracts vollstaendig
ab. Diese Doku beschreibt den **Code-Review-Restanteil** und die
**Folge-ADR-Pflicht bei `pyproject.toml`-Aenderungen**.

Die Checkliste in §3 ist im PR-Template verlinkt — jede PR muss sie
explizit durchgehen.

---

## 2. Was Tools schon erledigen

Wenn `make gates` lokal und in CI gruen ist, sind diese Punkte
abgehakt — ein Reviewer muss sie nicht erneut pruefen:

| Tool                 | Vertrag                                         | ADR-Bezug                 |
| -------------------- | ----------------------------------------------- | ------------------------- |
| `make lint`          | `ruff check`: A-1-Regelgruppen `BLE`/`TRY`/`B`/`DTZ`/`S`/`TID`/`C901`/`PLR*`/`N`/`RET`/`SIM`/`ARG`/`RUF` plus `flake8-tidy-imports.banned-{api,module-level-imports}` | [`ADR 0002`](../plan/adr/0002-language-and-build-stack.md) §A-1 ruff-Block |
| `make format-check`  | `ruff format --check`                           | [`ADR 0002`](../plan/adr/0002-language-and-build-stack.md) §A-1            |
| `make typecheck`     | `mypy --strict` mit `enable_error_code = [redundant-self, possibly-undefined, truthy-bool, truthy-iterable, unused-awaitable, explicit-override, mutable-override]` | [`ADR 0005`](../plan/adr/0005-type-check-gate.md) §5.1            |
| `make arch-check`    | 6 import-linter-Contracts ([`AC-CORE-NO-ADAPTERS`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) bis [`AC-NO-IO-MOD`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)) + 10 AST-Contracts via `tools/arch_check.py` ([`AC-HEXAGON-PURE`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-NO-JSON`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-NO-TIME`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-NO-RAND`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-NO-IO-MOD-NESTED`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-DOMAIN-FROZEN`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-NO-GOD-UTILS`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-TYPED-ERRORS`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-NO-CYCLES`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-ADAPTER-LIGHTWEIGHT`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)) | [`ADR 0002`](../plan/adr/0002-language-and-build-stack.md) §A-1 |
| `make test-unit`     | pytest mit `hypothesis`-Property-Tests; arch_check-Vollstaendigkeit (`test_arch_check_registration.py`) | [`ADR 0002`](../plan/adr/0002-language-and-build-stack.md) §A-2 / Drittes Review §3 |
| `make coverage-gate-critical` | ≥ 90 % Line + Branch auf kritischer Domain (mit Build-Arg-Override im Spike-0/M1-Stand) | [`ADR 0002`](../plan/adr/0002-language-and-build-stack.md) §A-1, [`GG-COV-003`](../../spec/lastenheft.md#gg-cov-003) |

**Wenn `make gates` rot ist, ist die PR nicht reviewable.** Bitte zuerst
gruen bekommen, dann Review anfordern.

---

## 3. Review-Checkliste

Jede PR durchlaeuft diese Checkliste. Wenn ein Punkt nicht zutrifft,
explizit „N/A — keine Adapter/Domain-Aenderung" o. ae. im PR-Kommentar
vermerken.

### 3.1 `AC-ADAPTER-PURE`-Reststeuerung (Logik-Anteil von GG-AR-TABU-003)

[`AC-ADAPTER-PURE`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) (import-linter) und [`AC-ADAPTER-LIGHTWEIGHT`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)
(`tools/arch_check.py`) decken **Import-Grenze und strukturelle
Komplexitaet**. Statische Tools koennen aber nicht erkennen, wenn
ein Adapter **fachliche Entscheidungen** trifft, statt nur Protokolle
oder Datenformate zu uebersetzen.

**Pruefen pro Adapter-PR:**

- [ ] Trifft der Adapter Wertebereich-Pruefungen, die in den Domain-
      Kern gehoeren? (z. B. Adapter, der `power_kw > 1000` ablehnt,
      statt das dem Battery-Modell zu ueberlassen.)
- [ ] Trifft der Adapter Geraete-Spezifische Logik? (z. B. SOC-
      Pruefung im Modbus-Adapter, die das Battery-Modell schon hat.)
- [ ] Trifft der Adapter Routing-Entscheidungen jenseits des
      Protocol-Mappings? (z. B. „wenn Topic X kommt, dann Befehl Y
      generieren" — das gehoert in den Kern.)
- [ ] Mapping-Funktionen sind dokumentiert? (z. B. „MQTT-Topic
      `bess/p_setpoint` → `Command(type=set_power_kw)`" als
      Doc-String.)

**Wenn unklar:** Pruefen, ob `core.errors.GridGymError`-Vererbung
greift (jeder Fachlogik-Fehler MUSS typisiert sein).

### 3.2 `GG-CC-001` Methoden-/Funktionsgroesse (Restanteil nach ruff)

ruffs `PLR0915` (max-statements=30), `PLR0911` (max-returns=6),
`PLR0912` (max-branches=12), `PLR0913` (max-args=5), `C901`
(max-complexity=10) decken den quantitativen Teil. **Restanteil:**

- [ ] Sind Methoden und Funktionen **inhaltlich kohaerent**? (Eine
      Funktion mit 25 Statements, die fuenf Dinge tut, ist tools-
      konform aber inhaltlich schlecht.)
- [ ] Sind Hilfsfunktionen aussagekraeftig benannt? (`_emit_decimal`
      statt `_helper2`.)

### 3.3 `GG-CC-005` Naming-Konsistenz (Restanteil nach ruff N)

ruff `N` (pep8-naming) deckt die formale Konvention. **Restanteil:**

- [ ] **Domain-Terminologie konsistent**: Begriffe aus dem
      Lastenheft (`tick`, `simulation_time`, `quality`, `event_id`)
      sind 1:1 verwendet — keine Synonyme („timestamp" vs.
      „simulation_time").
- [ ] Klassen-/Methodennamen passen zum Architektur-Vokabular
      (`ClockPort` nicht `TimeProvider`, `RandomPort` nicht
      `PrngSource`).
- [ ] Test-Funktionsnamen sind beschreibend („what_then_when"
      Pattern): `test_decimal_zero_variants_normalize_negative_sign`
      statt `test_decimal_1`.

### 3.4 SOLID-Restanteil (`GG-PRINC-002..006`)

ruff `PLR0902/0903/0904` (heute nur `PLR0904` aktiv, weil 0902/0903
nicht implementiert) plus `import-linter`-Layer-Contracts decken
die strukturelle Seite. **Restanteil:**

- [ ] **SRP**: Hat die Klasse **einen fachlich benennbaren Grund**
      fuer Aenderungen? (Bei zwei oder mehr → Refactor zu zwei
      Klassen.)
- [ ] **OCP**: Wird Erweiterung ueber Ports / Konfiguration angefasst,
      nicht durch Aenderung der Kernlogik? (Neuer Geraetetyp →
      `core/devices/<new_device>/` statt if-Branch im Scheduler.)
- [ ] **LSP**: Erfuellt ein Subtyp den Vertrag des Supertyps voll?
      (mypy faengt Variance, Code-Review faengt semantische
      Invarianten-Verletzungen — z. B. wenn `BatteryModel` mehr
      Constraints durchsetzt als das `DeviceModel`-Protocol
      verspricht.)
- [ ] **ISP**: Werden Ports schmal gehalten? (Neuer Port-Konsument
      braucht NICHT die ganze API zu kennen — sonst Split in
      kleinere Ports.)
- [ ] **DIP**: Domain haengt von Abstraktion ab, nicht von
      Implementation? (`import-linter` faengt die Modul-Grenze;
      Review faengt Konstruktor-Argumente, die `Concrete`-Typen
      statt `Protocol`-Typen verlangen.)

### 3.5 `pyproject.toml`-Folge-ADR-Pflicht (Post-Acceptance)

[`ADR 0002`](../plan/adr/0002-language-and-build-stack.md) und [`ADR 0005`](../plan/adr/0005-type-check-gate.md) sind seit 2026-05-15 `Accepted`. Per
[`ADR 0006`](../plan/adr/0006-adr-lifecycle-superseding-and-process-corrections.md) §3 sind die Entscheidungstexte immutable; Aenderungen an
verbindlichen Konfigurations-Sektionen brauchen **Folge-ADRs**.

**Welche `pyproject.toml`-Aenderungen sind ADR-relevant:**

- `[tool.ruff.lint] select` / `extend-select` / `ignore` /
  `extend-ignore` — Aenderung (oder Aufweichung) der Regelgruppen
  aus [`ADR 0002`](../plan/adr/0002-language-and-build-stack.md) §A-1. **Auch `extend-ignore = [...]` ist ADR-
  relevant**, weil eine entfernte Regel den A-1-Vertrag aufweicht
  ohne `select` zu beruehren.
- `[tool.ruff.lint.flake8-tidy-imports] banned-module-level-imports`
  / `banned-api` — Aenderung der A-1-Aufruf-Site-Verbote.
- `[tool.ruff.lint.per-file-ignores]` — Aenderung des Reichweiten-
  Vertrags (z. B. Adapter-Boundary-Modul-Liste).
- `[tool.ruff.lint.pylint] max-*` — Aenderung des [`GG-CC-001`](../../spec/lastenheft.md#gg-cc-001)-
  Methodenlaengen-Gates.
- `[tool.mypy] strict` / `files` / `enable_error_code` /
  `disable_error_code` — Aenderung des [`ADR-0005`](../plan/adr/0005-type-check-gate.md)-Strict-Vertrags.
  **`disable_error_code = [...]` ist explizit ADR-relevant**, weil
  es einen erzwungenen Check abschaltet.
- `[tool.importlinter] contracts` — Aenderung der A-1-Contracts.
- `[tool.grid_gym.arch_check] *-whitelist` / `*-exempt` — Aenderung
  der A-1-Reichweiten.

**Welche Aenderungen sind frei** (ohne Folge-ADR):

- Neue Dev-Tool-Versionen-Pin innerhalb des Major-Range (z. B.
  `mypy>=2.0,<3.0`-Untergrenze auf `>=2.1` heben). Major-Wechsel
  jedoch erfordert ADR.
- Neue `[project.dependencies]` fuer M1-Slice-Domain-Code (nicht-
  ADR-relevant, solange [`AC-HEXAGON-PURE`](../plan/adr/0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)-Whitelist mitgepflegt
  wird — wenn Whitelist sich aendert, ist Folge-ADR Pflicht).
- Reine Format-/Kommentar-Aenderungen.

**Pruefen pro `pyproject.toml`-PR:**

- [ ] Beruehrt diese PR eine der oben gelisteten Sektionen?
- [ ] Falls ja: ist eine Folge-ADR verlinkt (z. B. [`ADR 0008`](../plan/adr/0008-enum-as-domain-frozen-form.md))?
- [ ] Falls Folge-ADR fehlt: PR blockiert, bis ADR vorliegt
      (`Provisional` reicht — Acceptance synchron zur PR-Mergung).
- [ ] Per [`ADR 0006`](../plan/adr/0006-adr-lifecycle-superseding-and-process-corrections.md) §3 darf die Folge-ADR auf eine `Accepted`-
      ADR (z. B. [`ADR 0002`](../plan/adr/0002-language-and-build-stack.md)) als „Supersedes" verweisen, falls die
      Aenderung den A-1-Vertrag tatsaechlich aufweicht. Bei reiner
      Erweiterung (neue Regel hinzu) reicht eine neue ADR ohne
      Supersedes.

### 3.6 Tests und Coverage

- [ ] `hypothesis`-Property-Tests fuer Determinismus-relevante Pfade
      (Domain-Roundtrip, Scheduler-Order, Tick-Loop-Snapshots)?
- [ ] Negativ-Tests fuer typisierte Fehler? (z. B. `pytest.raises(FloatNotAllowedError)`
      statt `pytest.raises(CanonicalSerializationError)` — strikter
      ist besser).
- [ ] Coverage-Stage gruen via `make coverage-gate-critical`?
      (Spike-0/M1-Stand mit Build-Arg-Override, M1-Closure-Stand
      ohne Override.)

### 3.7 ADR-Querverweise

- [ ] Sind Querverweise gemaess [`ADR 0004`](../plan/adr/0004-identifier-based-cross-references.md) ueber Kennungen
      (`GG-*`/`GG-AR-*`/`AC-*`/`ADR-NNNN`) referenziert, nicht ueber
      `§...`-Sektionen?
- [ ] Wenn neue Folge-ADR: Header-Schema gemaess [`ADR 0006`](../plan/adr/0006-adr-lifecycle-superseding-and-process-corrections.md) §4
      (`Status`, `Datum`, `Status geaendert am`, ggf.
      `Letzte inhaltliche Aenderung`, `Superseded by`)?

---

## 4. Reviewer-Stimmen

Ein Review hat **eine** der drei Wirkungen:

1. **Approve**: Alle Checklisten-Punkte erfuellt, `make gates` gruen,
   keine offenen Folge-ADR-Triggers. PR ist mergebar.
2. **Request changes**: Checklisten-Verstoss oder offene Frage.
   Konkrete Aenderungs-Empfehlung in PR-Kommentaren.
3. **Comment**: Allgemeine Frage / Hinweis, kein Approval-Block.

**Ein Approve ohne `make gates`-Beweis ist nicht zulaessig.** Wenn
CI nicht aufgesetzt ist (heute noch nicht, M1-Welle-6 bringt
GitHub-Actions-Workflow), muss der Reviewer den lokalen
`make gates`-Output im PR-Kommentar zitieren.

---

## 5. Eskalationspfad

- **Disagreement zwischen Reviewer und Autor**: ein zweiter
  Reviewer entscheidet.
- **Folge-ADR-Frage strittig**: [`ADR 0006`](../plan/adr/0006-adr-lifecycle-superseding-and-process-corrections.md) §3 ist verbindlich —
  Aenderung an `Accepted`-ADR-Vertraegen braucht Nachfolge-ADR. Bei
  Zweifel an „beruehrt die PR den Vertrag?": Folge-ADR schreiben
  (im Zweifel mehr Dokumentation, nicht weniger).
- **Architektur-Frage**: an Architekt eskalieren; ggf. `GG-AR-OPEN-*`-
  Eintrag in `architecture.md §19` oeffnen.
