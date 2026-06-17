# ADR 0054 — Composition-ASGI-Entrypoint und Scenario-Hook-Inversion

**Status:** Accepted
**Datum:** 2026-06-13
**Bezug:**

- [`ADR 0050`](0050-adapter-pure-bridge-retirement.md) — `AC-ADAPTER-PURE`-
  Bridge-Rueckbau; §2.5 verlangt das Composition-Root-Paket. Diese ADR
  schaerft die Umsetzung des letzten Rueckbau-Schritts (041-C3b).
- [`ADR 0006`](0006-adr-lifecycle-superseding-and-process-corrections.md)
  — ADR-Lifecycle.
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) — Schaerfung ohne Supersedes.
- [`ADR 0039`](0039-run-control-and-status-tracking.md) — historische
  Demo-Bootstrap-/Lifespan-Verkabelung.
- [`spec/architecture.md`](../../../spec/architecture.md#2-architekturprinzipien) —
  [`GG-AR-P-002`](../../../spec/architecture.md#2-architekturprinzipien), [`GG-AR-TABU-001`](../../../spec/architecture.md#architektur-tabus-build-architekturtest)..004.

---

## 1. Kontext

`AC-ADAPTER-PURE` (`type = forbidden`, ohne `allow_indirect_imports`)
prueft **indirekte** Import-Ketten. Das Scenario-Demo-Bootstrap
(`_demo_scenario_setup`) wird von `app.py` im Lifespan-Env-Branch
(`GRID_GYM_DEMO_SCENARIO_PATH`) konsumiert. Ein reiner Move des Bootstraps
nach `grid_gym.composition` (041-C3a-Pattern) liesse die Kette
`app` (Adapter) → `composition._demo_scenario_setup` → `core.scenario`/
`core.faults` bestehen — eine indirekte `AC-ADAPTER-PURE`-Verletzung.

Der bisherige Lazy-Import in `app.py` kappte die direkte Kante nur,
solange die `ignore_imports`-Bridge fuer
`_demo_scenario_setup → core.scenario.loader`/`core.faults` bestand.
041-C3b entfernt die letzten Bridges; deshalb muss der Adapter den
Bootstrap-Import endgueltig verlieren.

## 2. Entscheidung

### 2.1 Scenario-Hook-Inversion

`app.py` importiert das Scenario-Bootstrap **nicht** mehr. Stattdessen:

- `app.py` exportiert einen Registrierungs-Hook
  `_register_scenario_configurator(configurator)` plus einen
  modul-lokalen, **fail-closed** Default-Konfigurator (wirft, solange
  nichts registriert ist).
- Der Lifespan-Env-Branch ruft den registrierten Konfigurator, statt
  `configure_scenario_demo_run` direkt zu importieren.

Damit traegt der **Composition-Root** den `composition`-Import, nicht der
Adapter — `AC-ADAPTER-PURE` haelt ohne `ignore_imports`.

### 2.2 Composition-ASGI-Entrypoint

NEU `grid_gym/composition/asgi.py` ist der **produktive ASGI-Entrypoint**:
importiert die FastAPI-`app` aus dem HTTP-Adapter, importiert
`configure_scenario_demo_run` aus `composition._demo_scenario_setup`,
registriert den Konfigurator beim Import und re-exportiert `app`.

### 2.3 Deployment- und Aufrufer-Wechsel

Der uvicorn-Ziel-String wechselt von
`grid_gym.adapters.driving.http_api:app` auf
`grid_gym.composition.asgi:app` in:

- `Dockerfile`-`ENTRYPOINT` (produktiver Container),
- `__main__.py` (`python -m grid_gym demo`),
- Integration-Smokes, die den Env-Lifespan-Pfad fahren.

Der reine Adapter-Entrypoint bleibt importierbar (z. B. fuer den
OpenAPI-Build-Export), startet aber **ohne** registrierten Konfigurator
und faellt fail-closed, falls die Scenario-Env-Var gesetzt ist.

## 3. Konsequenzen

Positive Konsequenzen:

- `AC-ADAPTER-PURE` ist ohne **jede** `ignore_imports`-Bridge gruen
  (`ignore_imports = []`); ADR 0050 erreicht `Accepted`.
- Composition Root ist explizit und ein einziger Ort.
- Fail-closed: ein falscher Entrypoint mit gesetzter Scenario-Env-Var
  bricht laut, statt das Scenario still zu ueberspringen.

Kosten und Risiken:

- Deployment-Entrypoint-Wechsel beruehrt `Dockerfile`/`compose.yml` —
  Verifikation via vollem `make fullbuild` (Compose-Smoke) ist Pflicht.
- `app.py` darf den `AC-NO-GOD-UTILS`-Public-Function-Cap (max 5) nicht
  reissen — der Hook ist deshalb `_`-prefixt (intern).

## 4. Out-of-Scope

- Neue HTTP-API-Surface oder Scenario-Semantik.
- App-Factory-Pattern (mehrere App-Instanzen) — der modul-globale
  Konfigurator reicht fuer den Single-App-Prozess.

## 5. Acceptance

`Accepted` mit 041-C3b: `ignore_imports = []`, `make arch-check` 7/7 +
`tools/arch_check.py` clean, `make fullbuild` gruen (inkl. Compose-Smoke
ueber den neuen Entrypoint).
