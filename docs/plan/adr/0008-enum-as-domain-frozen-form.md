# ADR 0008 — Enum-Subklassen als AC-DOMAIN-FROZEN-Form

**Status:** Provisional — Empfehlung getragen, Acceptance synchron
mit der M1-Welle-1-PR-Mergung.
**Datum:** 2026-05-17
**Status geaendert am:** 2026-05-17 — `Proposed → Provisional` mit
Freigabe der Implementierung in
`tools/arch_check.py` (`_inherits_enum`). Acceptance synchron zur
M1-Welle-1-PR; bei Mergung wird der Status auf `Accepted` gehoben.
**Letzte inhaltliche Aenderung:** 2026-05-17 — erste Fassung.
**Bezug:**
[`ADR 0002`](0002-language-and-build-stack.md) §A-1 [`AC-DOMAIN-FROZEN`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)
(erweiterter Vertrag),
[`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
§3 (Erweiterungs-ADR ohne `Supersedes`, weil dieser ADR den
A-1-Vertrag nur erweitert, nicht aufweicht),
[`docs/user/code-review.md`](../../user/code-review.md) §3.5
(Folge-ADR-Pflicht bei Aenderung der A-1-Reichweiten),
M1-Slice-Plan
[`docs/plan/planning/done/M1-tick-loop-spine.md`](../planning/done-archive/M1-tick-loop-spine.md)
§3 Welle 1 (Trigger der Erweiterung — `Quality`/`CommandResult`
als Enums).

---

## 1. Kontext

`ADR 0002 §A-1` fixiert [`AC-DOMAIN-FROZEN`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) als verbindliches A-1-
Contract. Der Vertragstext erkennt heute zwei Frozen-Konventionen:

1. `@dataclass(frozen=True, slots=True)` (beide Keywords als
   `ast.Constant(value=True)`).
2. Vererbung von `FrozenModel` (`ast.Name` oder `ast.Attribute`,
   literaler Klassenname).

Der Slice-Plan M1 Welle 1 verlangt zwei Enum-Klassen in
`hexagon/core/domain/`:

- `Quality` (`GG-DATA-003`) — Telemetrie-Qualitaetsstatus.
- `CommandResult` (`GG-DATA-004`) — Steuerbefehl-Endstatus.

Beide sind Enum-Subklassen (konkret `enum.StrEnum`, damit
`canonical_json` ueber den `str`-Branch serialisieren kann). Enum-
Subklassen erfuellen keine der heute akzeptierten Konventionen,
sind aber in Python by-construction immutable: `enum.Enum`-Member
sind nach der Klassenerstellung schreibgeschuetzt
(`__setattr__`/`__delattr__` der Enum-Metaklasse blockieren
Re-Definition), und `Enum.__init_subclass__` verhindert das
Hinzufuegen weiterer Member nach der Klassen-Definition.

`ADR 0002 §A-1` nennt diesen Fall im Vertragstext explizit als
Trigger: „andere Frozen-Konventionen erfordern Re-Alias oder
**ADR-Erweiterung**". Diese ADR ist die ADR-Erweiterung.

---

## 2. Entscheidung

[`AC-DOMAIN-FROZEN`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) akzeptiert eine dritte Frozen-Form:

3. Vererbung von einer Python-`enum`-Basisklasse — namentlich
   einer der folgenden Top-Level-Klassen aus `enum`:
   `Enum`, `StrEnum`, `IntEnum`, `Flag`, `IntFlag`, `ReprEnum`.

Erkennung erfolgt wie bei `FrozenModel` ueber **literalen
Klassennamen**, sowohl als `ast.Name` (Bare-Import,
`from enum import StrEnum`) als auch als `ast.Attribute`
(`import enum` → `class Q(enum.StrEnum): ...`). Re-Exports unter
demselben literalen Namen matchen — das ist die etablierte
Heuristik der `FrozenModel`-Erkennung; sie hat dieselben Grenzen
(keine Import-Resolving, kein Alias-Tracking).

Implementierung in `tools/arch_check.py` (`_inherits_enum`) als
zusaetzliche `or`-Alternative in `_is_frozen_class`:

```python
def _is_frozen_class(node: ast.ClassDef) -> bool:
    return (
        _has_frozen_dataclass_decorator(node)
        or _inherits_frozen_model(node)
        or _inherits_enum(node)
    )
```

---

## 3. Begruendung

Enum-Subklassen sind in Python **strukturell immutabler** als
beide bestehenden Konventionen:

| Eigenschaft                                    | `@dataclass(frozen, slots)` | `FrozenModel`            | `Enum`-Subklasse |
| ---------------------------------------------- | --------------------------- | ------------------------ | ---------------- |
| Instance attribute set wirft typed error       | ja (`FrozenInstanceError`)  | ja (`ValidationError`)   | n/a (keine veraenderbaren Instance-Attribute) |
| Klassen-Attribute (Member) nach Definition aenderbar | ja (Python-Default)   | ja (Python-Default)      | nein (`Enum`-Metaklasse blockiert) |
| Neue Member nach Definition hinzufuegbar       | n/a                          | n/a                      | nein (`Enum.__init_subclass__`) |
| Member-Werte ueberschreibbar                   | n/a                          | n/a                      | nein (read-only descriptor) |

Enum-Member sind also nicht nur „nicht-mutiert-by-convention",
sondern „nicht-mutierbar-by-language". Das macht die Aufnahme in
[`AC-DOMAIN-FROZEN`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert) strenger als eine Aufweichung — es ist eine
Vertragserweiterung im strengeren Sinne von ADR 0006 §3
(„Bei reiner Erweiterung … reicht eine neue ADR ohne Supersedes").

Alternative Optionen wurden gegen diese Entscheidung abgewogen:

- **Literal-TypeAlias statt Enum.** Funktionell aequivalent fuer
  Typ-Sicherheit, aber Aufrufer schreiben Roh-Strings statt
  `Quality.VALID` — schlechtere Lesbarkeit und kein Autocomplete.
  Verworfen.
- **`FrozenModel`-Marker-Mehrfachvererbung mit `StrEnum`.** MRO mit
  `Enum.__init_subclass__` ist fragil und ueberraschend; Welle-1-
  Domain-Code soll keinen MRO-Hack tragen. Verworfen.

---

## 4. Reichweite

Diese ADR aendert ausschliesslich [`AC-DOMAIN-FROZEN`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert). Alle anderen
A-1-Contracts ([`AC-NO-JSON`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-NO-TIME`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-NO-RAND`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-NO-IO-MOD`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert),
[`AC-NO-GOD-UTILS`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-TYPED-ERRORS`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-NO-CYCLES`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-HEXAGON-PURE`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert),
[`AC-ADAPTER-LIGHTWEIGHT`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-CORE-NO-ADAPTERS`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-CORE-NO-DRIVING`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert),
[`AC-PORTS-NO-OUT`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-PORTS-NO-FW`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-ADAPTER-PURE`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert), [`AC-NO-FW`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert)) bleiben
unveraendert.

Zukuenftige Enum-Subklassen mit nicht-trivialer Logik in `__init__`
oder `__new__` bleiben unter dem Frozen-Vertrag, weil die Heuristik
nur die Basisklassen-Liste auswertet, nicht den Klassenkoerper.
Wenn das in einer spaeteren Welle als zu lax empfunden wird,
braucht es eine weitere Folge-ADR (z. B. „Enum-Subklassen duerfen
nur Member und literal docstrings im Body haben").

---

## 5. Operative Artefakte

- `tools/arch_check.py` — neuer `_inherits_enum`-Helper plus
  `_ENUM_BASE_NAMES`-Konstante (`{"Enum", "StrEnum", "IntEnum",
  "Flag", "IntFlag", "ReprEnum"}`).
- `tools/arch_check.py` Modul-Docstring + `_check_domain_frozen`-
  Docstring nennen Enum-Subklassen als dritte zulaessige
  Frozen-Form.
- `ADR 0002 §A-1`-Tabellenzeile [`AC-DOMAIN-FROZEN`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert): Verweis auf
  diese ADR ergaenzt.
- Direkter Unit-Test fuer `_inherits_enum` unter
  `tests/unit/test_arch_check_domain_frozen.py` (Happy-Path je
  Basisklasse + Rejection-Case fuer Nicht-Enum-Basis).

---

## 6. Konsequenzen

- **Positiv:** Domain-Code kann Spec-Werte aus `GG-DATA-003`/`004`
  als Python-`StrEnum` modellieren — kein Workaround-Pattern.
  `canonical_json` serialisiert Member ueber den `str`-Branch
  ohne Konversion an der Domain-Eingangsgrenze.
- **Positiv:** Der AC-DOMAIN-FROZEN-Vertrag wird strikter im
  Sinne der Frozen-Garantie, nicht laxer — Enum-Subklassen sind
  by-language-Immutable.
- **Neutral:** Ein zusaetzlicher `_check_*`-Helper in
  `tools/arch_check.py`; `test_arch_check_registration.py`
  bleibt unveraendert (es prueft die `main()`-Aufrufstruktur,
  nicht die internen Helper).
- **Negativ:** Die Heuristik ist literal-Name-basiert wie
  `FrozenModel` — ein Re-Export unter demselben Namen
  („`class StrEnum: ...`" in einem fremden Modul) matched
  ebenfalls. Diese Grenze ist bei `FrozenModel` etabliert und
  wird hier konsistent uebernommen.

---

## 7. Nicht Gegenstand dieser ADR

- Sonstige Frozen-Konventionen (`@attrs.frozen`,
  `pydantic.BaseModel` ohne `FrozenModel`-Alias, `NamedTuple`).
  Bei Bedarf eigene Folge-ADR.
- Vertrag fuer Enum-Subklassen mit komplexem Body-Code (z. B.
  Methoden mit Seiteneffekten). Heuristik laesst das heute
  durch; Schaerfung waere eigene Folge-ADR.
- Aenderungen an `GG-DATA-003`/`004`-Wertelisten — die Spec
  bleibt unangetastet.
