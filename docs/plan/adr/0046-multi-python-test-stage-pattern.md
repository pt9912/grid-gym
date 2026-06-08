# ADR 0046 — Multi-Python-Test-Stage-Pattern fuer Library-Compat-Smokes (M6 Welle 6)

**Status:** Provisional — direkter `Proposed → Provisional`-
Sprung (dieser Commit).
**Datum:** 2026-06-08
**Status geaendert am:** 2026-06-08 — `Proposed → Provisional`.
**Bezug:**

- [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
  — Lifecycle- und Supersedes-Pflichten, auf denen die
  Schaerfungs-ohne-Supersedes-Form aufbaut.
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) —
  Schaerfung-ohne-Supersedes-Pattern (Form-Vorbild;
  Erlaubnis-Anker fuer die additive Build-Pattern-
  Erweiterung).
- [`ADR 0002`](0002-language-and-build-stack.md) — Ziel-ADR
  der Schaerfung: Sprach- und Build-Stack. §2 Sprach-Floor
  (`requires-python = ">=3.13"`, Python 3.14 Referenz-
  Runtime) bleibt textlich **unveraendert**; das Multi-Stage-
  Dockerfile-Build-Pattern wird additiv um eine Library-
  Compat-Test-Stage erweitert.
- [`ADR 0005`](0005-type-check-gate.md) — Multi-Stage-
  Dockerfile-Gate-als-Stage-Pattern (jede Pflicht-Pruefung
  ist ein eigenes `--target`-Build-Ziel); die NEU `iec61850-
  test`-Stage folgt demselben Stage-pro-Gate-Pattern.
- [`ADR 0035`](0035-iec61850-adapter-profile.md) — Erst-
  Anwendungsfall: §2.5 Decision I-e (2c-Mock-only-Fallback;
  `pyiec61850-ng` 1.6.1.2 `manylinux1_x86_64`-Wheel
  segfaultet im SWIG-Layer auf Python >=3.13). Der dort
  dokumentierte Welle-6-Schaerfungspfad „Python-3.12-Runtime
  fixieren" wird mit dieser ADR verankert.
- [`ADR 0028`](0028-link-maintenance-accepted-adr-bezug.md)
  — Link-Maintenance-Pattern fuer den ADR-Index-Update an
  der ADR-0002-Zeile.
- [Trigger 009](../planning/done/009-iec61850-smoke-reactivation.md)
  — Aktivierungs-Trigger (IEC-61850-In-Process-Smoke-
  Reaktivierung). Trigger 009 nennt explizit „Eventueller
  ADR 0036 wenn das Pattern repo-weit als 'Library-Compat-
  Test-Stage'-Pattern wiederverwendet wird" — Pfad B
  produziert diesen ADR (Nummer 0046, weil 0036 bereits
  UI-Stack-Choice ist).

---

## 1. Kontext

[ADR 0035](0035-iec61850-adapter-profile.md) §2.5 (Decision
I-e) hat den IEC-61850-In-Process-Smoke unter einem **2c-
Mock-only-Fallback** geschlossen: der Probe-Run auf Python
3.12 lief Float/Int32/String-Roundtrip mit
`IedServer(model_path=fixture)` sauber durch, aber der
Docker-Stack auf Python 3.14 segfaultet im
`_pyiec61850.so`-SWIG-Layer mit exit 139 beim ersten
`IedServer.start()`.

[Trigger 009](../planning/done/009-iec61850-smoke-reactivation.md)
hat dem Library-Upgrade-Pfad (Pfad A) am 2026-06-01 einen
Probe-Run gemacht:

> Linux-Wheel ist ausschliesslich
> `py3-none-manylinux1_x86_64` (kein cp-Tag) — der Wheel
> enthaelt SWIG-Bindings, die intern an eine spezifische
> Python-ABI gebunden sind, ohne dass das Wheel-Manifest
> das markiert. Konsequenz: `pip install pyiec61850-ng`
> auf Python 3.14 zieht den vermeintlich Python-Version-
> agnostischen Wheel und segfaultet beim ersten SWIG-Call.

Damit ist **Pfad A tot** mit dem aktuellen Library-
Distribution-Stand (kein cp314-Wheel; passiver Pfad ohne
Eskalations-Mechanismus). Trigger 009 nennt **Pfad B** als
aktiven Aufloesungs-Pfad: eine Dockerfile-Stage auf einer
aelteren Python-Version, in der der Smoke real-library
laeuft — explizit markiert als **Repo-Novum** („zweite
Python-Version im Build-Layer, separates uv-Lockfile-
Handling").

Das grid-gym-Build-Pattern ([ADR 0002](0002-language-and-build-stack.md)
+ [ADR 0005](0005-type-check-gate.md)) ist ein Multi-Stage-
Dockerfile, in dem jede Pflicht-Pruefung ein eigenes
`--target`-Build-Ziel ist (`lint`, `typecheck`, `arch-
check`, `test-unit`, `coverage-gate` …), alle abgeleitet von
einer gemeinsamen `source`-Stage auf der `base`-Python-
Version (`ARG PYTHON_VERSION=3.14`). Der Build-Stack ist
**single-Python**: `deps`/`source` syncen via `uv sync
--frozen` gegen `uv.lock`, der fuer den 3.13/3.14-Matrix-
Floor aufgeloest ist.

Eine Library-Compat-Test-Stage auf Python 3.12 bricht zwei
Annahmen dieses Patterns:

1. **Single-Python-Annahme** — die Stage braucht einen
   zweiten Interpreter (`python:3.12-slim`) neben der
   `base`-3.14-Stage.
2. **Lockfile-First-Annahme** — `uv sync --frozen` wuerde
   gegen den `requires-python = ">=3.13"`-Floor aus
   `pyproject.toml` brechen, und der `uv.lock` ist nicht
   fuer 3.12 aufgeloest.

Diese ADR verankert das Pattern, das diese beiden Bruchstellen
sauber kapselt, **ohne** den ADR-0002-Sprach-Floor oder den
Default-Build-Pfad anzutasten. Sie folgt dem ADR-0011-Pattern
(Schaerfung ohne Supersedes): ADR 0002 §2 bleibt textlich
unveraendert; das Build-Pattern wird additiv erweitert.

---

## 2. Entscheidung

ADR 0046 fixiert zwei orthogonale Punkte als „Library-Compat-
Test-Stage"-Pattern.

### §2.1 Dockerfile-Multi-Python-Stage-Pattern

Eine **Library-Compat-Test-Stage** ist eine additive
Dockerfile-Stage auf einer **gepinnten, von der `base`-Stage
abweichenden Python-Version**, eingefuehrt ueber einen
eigenen `FROM python:<compat-version>-slim`-Basis-Layer
(NICHT abgeleitet von `base`/`source`, weil die einen anderen
Interpreter tragen).

- Die `base`-Stage und alle von `source` abgeleiteten
  Pflicht-Gates bleiben auf `ARG PYTHON_VERSION` (Default
  3.14). Die Compat-Stage ist **opt-in** und liegt
  strukturell neben dem Default-Gate-Stack, nicht in ihm.
- Erst-Anwendung (Welle-6-C2): NEU Stage `iec61850-test` auf
  `python:3.12-slim`, gebaut per `make test-iec61850`.
- Die Stage ist ein eigenes `--target`-Build-Ziel wie jedes
  andere Gate ([ADR 0005](0005-type-check-gate.md)-Pattern);
  sie wird NICHT in die Default-`source`-Gate-Kette
  eingehaengt.
- **Verallgemeinerung:** Das Pattern gilt fuer jede Library
  mit einem cp-Tag-/ABI-Bruch gegen den `base`-Interpreter
  (z. B. spaeter asyncua oder andere SWIG-/C-Extension-
  Libraries). Jede solche Library bekommt eine eigene
  `<lib>-test`-Stage mit eigener Compat-Python-Version.

### §2.2 Library-Compat-Install-Form

Die Compat-Stage installiert das Projekt **NICHT** via `uv
sync --frozen` (das gegen den `requires-python = ">=3.13"`-
Floor aus `pyproject.toml` brechen wuerde und den fuer
3.13/3.14 aufgeloesten `uv.lock` nicht auf 3.12 anwenden
kann). Stattdessen:

```dockerfile
# Compat-Stage-Install (Beispiel iec61850-test, Python 3.12):
RUN python -m pip install --ignore-requires-python --no-deps -e .
RUN python -m pip install <test-runtime-set inkl. pyiec61850-ng + pytest + …>
```

- **`python -m pip install --ignore-requires-python --no-deps
  -e .`** installiert den Projektcode editable ohne Dependency-
  Resolution (`--no-deps`) und ohne Lockfile. `--ignore-requires-
  python` ist noetig, weil grid_gym selbst `requires-python =
  ">=3.13"` (ADR 0002 §2) traegt — `--no-deps` skippt nur die
  Dependencies, nicht die Floor-Auflage des eigenen Pakets.
  **`pip` statt `uv pip`**: nur pip bietet `--ignore-requires-
  python`; `uv pip install` (Stand uv 0.5.x) kennt das Flag nicht.
  Die Compat-Stage ist die einzige Stelle, an der grid-gym pip
  statt uv nutzt — bewusst auf den Compat-Scope begrenzt.
- **`python -m pip install <set>`** installiert das fuer den
  Smoke noetige Runtime-/Test-Set (inkl. der inkompatiblen
  Library). Das `<set>` deckt zusaetzlich die Pakete ab, die der
  Test-Collection-Pfad importiert (z. B. die Integration-Test-
  conftest-Deps). Diese unterstuetzen die Compat-Python-Version
  nativ, daher kein `--ignore-requires-python` noetig.
- **Scope-Begrenzung (verbindlich):** Diese Install-Form ist
  **ausschliesslich** Library-Compat-Stage-Scope. Der
  Default-Runtime-/Build-Pfad (`deps`/`source`/`build-app`/
  `runtime`-Stages) bleibt `uv sync --frozen`-basiert
  ([ADR 0002](0002-language-and-build-stack.md) Supply-
  Chain-Defense). `--ignore-requires-python` im Default-Pfad
  bleibt verboten.
- **`pyproject.toml` + `uv.lock` werden nicht editiert.**
  ADR 0002 §2 Sprach-Floor (`>=3.13`) bleibt unangetastet;
  3.12 ist kein neuer unterstuetzter Runtime-Floor, sondern
  eine isolierte Compat-Test-Umgebung.

---

## 3. Begruendung

- **Antizipiertes Schaerfungs-Material aus Trigger 009 und
  ADR 0035 §2.5 liefern.** Trigger 009 nennt den ADR
  („Library-Compat-Test-Stage"-Pattern) explizit als Pfad-B-
  Lieferung; ADR 0035 §2.5 nennt „Python-3.12-Runtime
  fixieren" als Welle-6-Schaerfungspfad. ADR 0046 ist dieser
  Commit.
- **Multi-Python-Cost isoliert.** Option B aus
  [Trigger 009 / Welle-6-D-4](../planning/done/M6-welle-6.md)
  (eigener Docker-Compose-Service) waere Overkill: der Smoke
  braucht keinen Sibling-Sim-Container, nur einen zweiten
  Interpreter. Eine Dockerfile-Stage haelt den Cost auf einem
  `--target`-Build-Ziel; der Default-`make test-integration`
  faehrt weiter Python 3.14.
- **Floor unangetastet.** Die Install-Form mit
  `--ignore-requires-python` ist explizit Compat-Stage-
  Scope. Wuerde der Floor auf 3.12 gesenkt, traefe das den
  gesamten Default-Build und waere eine ADR-0002-
  Kernentscheidung-Aenderung (Supersedes-Pflicht statt
  Schaerfung). Das ist hier ausdruecklich NICHT der Fall.
- **Schaerfung ohne Supersedes (ADR 0011-Pattern).** ADR
  0002 §2 + §A-1 bleiben textlich unveraendert; nur das
  Multi-Stage-Build-Pattern wird additiv um eine Compat-
  Stage-Form erweitert. ADR 0002 bleibt in Kraft, ADR 0046
  liegt parallel.
- **Pattern-Verallgemeinerung.** Die Form ist nicht IEC-
  spezifisch: jede C-Extension-/SWIG-Library mit cp-Tag-
  Bruch (asyncua, kuenftige Adapter-Libraries) kann dieselbe
  `<lib>-test`-Stage-Form nutzen. Der ADR codifiziert das
  einmal.

---

## 4. Reichweite

- ADR 0002 bleibt textlich unveraendert (`Accepted`-
  Immutability per [ADR 0006 §3](0006-adr-lifecycle-superseding-and-process-corrections.md)
  + [ADR 0011 §2](0011-schaerfung-ohne-abloesung.md)). ADR
  0046 ist eine parallele Schwester-ADR.
- ADR-Index Aktive-ADRs-Tabelle ADR-0002-Zeile bekommt einen
  ADR-0046-Eintrag in der „Schaerfungen / Folge-ADRs"-Spalte
  (Index-Pflege per [ADR 0011 §4](0011-schaerfung-ohne-abloesung.md)
  + [ADR 0028](0028-link-maintenance-accepted-adr-bezug.md));
  ADR-0046-Zeile NEU angelegt.
- **Test-Gating-Koordination (C2-Substanz, nicht ADR-
  Decision):** der Default-Pfad bleibt durch einen versions-
  bedingten Skip-Marker geschuetzt
  (`pytest.mark.skipif(sys.version_info >= (3, 13), …)`
  statt unconditional `skip`), und `make ci` koordiniert
  beide Stages (`make test-integration` auf 3.14 +
  `make test-iec61850` auf 3.12). Diese Substanz lebt im
  Welle-6-Slice-Doc
  ([`M6-welle-6.md`](../planning/done/M6-welle-6.md)
  D-4) und in der Audit-Doku `docs/user/deploy-hardening.md`,
  nicht als ADR-Decision-Text — sie ist Anwendung des
  Patterns, nicht das Pattern selbst.
- Trigger 009 bleibt offen, bis Welle-6-C2 die Stage real
  liefert; bei C2-Lieferung wandert Trigger 009 per
  [ADR 0043 §2.3](0043-image-audit-strategy.md)-analogem
  `open/ → done/`-Move in den abgeschlossenen Stand
  (Slice-Doc-gesteuert).

---

## 5. Lieferung

Lieferplan, Commit-Hashes und Verifikations-Gates fuer die
Erst-Anwendung (Trigger-009-Pfad-B via `iec61850-test`-Stage)
leben in der zugehoerigen Slice-Doc
[`M6-welle-6.md`](../planning/done/M6-welle-6.md) (C2:
`feat(deploy)`). Die NEU-Build-Substanz (Dockerfile-Stage
`iec61850-test`, `make test-iec61850`-Target, `make ci`-
Recipe-Erweiterung, versions-bedingter Skip-Marker in
`tests/integration/test_iec61850_in_process_smoke.py`) ist
dort mit Commit-Hash dokumentiert. Status-Pfad (`Proposed →
Provisional → Accepted`): siehe Status-Header dieser ADR.

---

## 6. Konsequenzen

- **Positiv:** Trigger-009-Pfad-B-Lieferung und ADR-0035-§2.5-
  Welle-6-Schaerfungspfad-Versprechen eingeloest; der IEC-
  61850-Real-Library-Roundtrip ist wieder in CI belegbar
  (`make test-iec61850`), nicht nur manuell.
- **Positiv:** Der Multi-Python-Cost ist auf eine opt-in-
  Stage isoliert; der Default-Build bleibt single-Python
  (3.14) und unveraendert schnell.
- **Positiv:** Pattern verallgemeinerbar — kuenftige Library-
  Inkompats (asyncua o. ae.) folgen derselben `<lib>-test`-
  Stage-Form ohne neuen ADR.
- **Neutral:** Repo-Novum (zweite Python-Version im Build-
  Layer). Maintenance-Schwelle: die Compat-Stage faellt nicht
  unter den Lockfile-Frozen-Vertrag, deshalb ist ihr Dep-Set
  manuell gepflegt (`--ignore-requires-python <set>`); das
  ist bewusst auf den Compat-Scope begrenzt.
- **Neutral:** Die `--ignore-requires-python`-Install-Form
  umgeht die Supply-Chain-Defense des Frozen-Lockfiles fuer
  diese eine Stage. Da die Stage nur Test-/Smoke-Code
  ausfuehrt (kein Runtime-/Distributions-Artefakt) und das
  Runtime-Image weiter `uv sync --frozen` nutzt, bleibt die
  Supply-Chain-Defense fuer alle Distributions-Pfade intakt.

---

## 7. Nicht Gegenstand dieser ADR

- **Senkung des ADR-0002-Sprach-Floors.** `requires-python =
  ">=3.13"` bleibt; 3.12 ist isolierte Compat-Test-Umgebung,
  kein unterstuetzter Runtime-Floor.
- **`--ignore-requires-python` im Default-Pfad.** Die
  Install-Form ist ausschliesslich Compat-Stage-Scope; der
  Default-`deps`/`source`/`build-app`/`runtime`-Pfad bleibt
  `uv sync --frozen` ([ADR 0002](0002-language-and-build-stack.md)).
- **Library-Upgrade-Pfad (Trigger-009-Pfad-A).** Sobald
  `pyiec61850-ng` einen stabilen cp314-/ABI3-Wheel publiziert,
  bleibt Pfad A der bevorzugte (passive) Aufloesungs-Pfad —
  dann faellt die Compat-Stage weg (Skip-Marker-Entfernung +
  Stage-Removal als eigener `chore(deps)`-Slice). ADR 0046
  ist die aktive Bruecke, nicht die Endform.
- **Konkrete Dep-Set-Pins der Compat-Stage.** Welche genauen
  Versionen die `--ignore-requires-python <set>`-Zeile
  installiert, ist C2-Implementation-Detail (Slice-Doc), kein
  ADR-Vertrag.
- **aarch64-Wheel-Unterstuetzung** fuer `pyiec61850-ng`
  ([ADR 0035](0035-iec61850-adapter-profile.md)-Anti-Scope;
  Welle 6+ falls Bedarf).
- **Separates physisches uv-Lockfile pro Compat-Stage.**
  Trigger 009 nannte „separates uv-Lockfile-Handling" als
  Option; ADR 0046 waehlt stattdessen die `uv pip install
  --ignore-requires-python`-Form (kein zweites `uv.lock`-
  Artefakt). Ein dediziertes Compat-Lockfile bleibt M7+-
  Material, falls das Compat-Dep-Set reproduzierbar gepinnt
  werden muss.
