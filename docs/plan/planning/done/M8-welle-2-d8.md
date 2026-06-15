# M8 Welle 2-D8 — Generische `ScenarioFaultEngine` (Carveout D-8)

**Status:** Done (geschlossen 2026-06-14) — Cross-Cutting-Review-Folge der
Welle 2 (`5792ab8`). Loest [`carveouts.md`](../in-progress/carveouts.md) §2.1 **D-8** auf
(Scenario-/runtime-getriebene Fault-Engines + `_KNOWN_FAULT_TYPES`-Update
fuer die drei neuen Welle-2-Fault-Typen).

**Container:** [`roadmap.md`](../in-progress/roadmap.md) §4 M8. Design (C1):
[`ADR 0059`](../../adr/0059-generic-scenario-fault-engine.md) `Accepted`.
Slice-Origin: Carveout-D-8-Aktivierung (kein `open/`-Trigger — ein
`Deferred`-Carveout aktivieren triggert den Slice).

---

## 1. Lieferziel

Die drei neuen Welle-2-Fault-Typen (`connection_loss`/`winding_fault`/
`genset_fault`) end-to-end nutzbar machen: bisher trugen EV-Charger,
Transformer und Diesel geraeteseitig `inject_fault`/`clear_fault` + HTTP-
Whitelist, aber **keine Runtime-Engine** — eine YAML mit diesen Typen
crashte fail-loud beim `make demo`-Startup (`_KNOWN_FAULT_TYPES` stale).

Statt drei weitere typ-spezifische Engines (Duplikation der ohnehin schon
doppelten Battery/Grid-Engine) generalisiert dieser Slice zu **einer**
`ScenarioFaultEngine` — die Schluessel-Erkenntnis ist, dass die Engine den
Fault-Typ gar nicht kennen muss (`inject_fault(fault.type, …)` reicht ihn
ans Ziel-Geraet, das validiert). D-8 schrumpft damit von „3 Engines" auf
„1 Generalisierung" + Whitelist-Update.

## 2. DoD (≤ 3 beobachtbare Kriterien)

- [x] **Generalisierung**: NEU
      [`ScenarioFaultEngine`](../../../../src/grid_gym/hexagon/core/faults/scenario_fault_engine.py)
      (`faults, supported_types, subsystem`) haelt die einzige Kopie der
      [`ADR 0025`](../../adr/0025-fault-recovery-pattern.md)-Scheduling-Logik;
      `BatteryFaultEngine`/`GridFaultEngine`
      sind duenne Compat-Subklassen — die bestehenden M3-Fault-Unit-/
      Integration-Tests bleiben **unveraendert gruen** (Regressionsnetz).
      NEU
      [`test_scenario_fault_engine.py`](../../../../tests/unit/hexagon/core/faults/test_scenario_fault_engine.py)
      (Fenster, Idempotenz, Recovery, manual-recovery, Single-Pass ueber
      alle 5 Typen, target-None-/non-injectable-Branches, mistargeting-
      Wurf).
- [x] **Composition + Whitelist**: `_compose_fault_port` liefert eine
      Single-Engine (Klasse `_FaultPortComposition` entfernt);
      `_KNOWN_FAULT_TYPES` auf 5 Typen (single source of truth, aus
      `FAULT_TYPE_*`-Konstanten); dead `assert_supported_type` entfernt.
      [`test_fault_port_composition.py`](../../../../tests/unit/adapters/driving/http_api/test_fault_port_composition.py)
      migriert (None/Single-Engine/Reject + D-8-Accept der drei neuen
      Typen).
- [x] **End-to-End**: NEU
      [`diesel_fault_demo.yaml`](../../../../tests/integration/scenarios/diesel_fault_demo.yaml)
      + [`test_diesel_fault_scenario.py`](../../../../tests/integration/test_diesel_fault_scenario.py)
      treiben `genset_fault` ueber den produktiven `_compose_fault_port`
      durch Loader → TickLoop → Diesel (genset_fault-Telemetrie 1 im
      Window, 0 ausserhalb). `make gates` + `make docs-check` +
      `make test-integration` gruen.
      [`ADR 0059`](../../adr/0059-generic-scenario-fault-engine.md)
      `Accepted`, Carveout D-8 → Resolved.

## 3. Realization-Notes

- **Altitude statt Special-Case**: der Review-Altitude-Winkel
  („generalize the mechanism over N special cases") direkt umgesetzt — die
  ~90 Zeilen Scheduling-Logik leben nach diesem Slice **einmal**.
- **Compat-Subklassen** halten das Risiko klein: die produktive Single-
  Engine ist neu, aber Battery/Grid-Verhalten ist verhaltens-erhaltend
  (gleiche supported_types/IDs); die bewaehrten M3-Tests laufen als
  Regressionsnetz unveraendert.
- **`clear_fault(fault.type)`** statt hartkodierter Typ-Konstante — fuer
  die Subklassen identisch (ihr Filter garantiert genau einen Typ), fuer
  die generische Engine notwendig (sie clearet mit dem injizierten Typ).

## 4. Lerneintrag (Closure-Pflicht)

**Geschaerfte Regel (Carveout-Aktivierung als Slice-Origin):** Ein
`Deferred`-Carveout, der dreimal per-ADR §6 fortgeschrieben wurde
(2a/2b/2d), ist ein Signal — die wiederholte Deferral war hier teils mit
**falscher Begruendung** notiert (der produktive Composite-`_compose_fault_port`
existierte laengst; die Engine war ein kleiner Lift, kein „M-Folge-
Infrastruktur"). Konsequenz: bei der naechsten gleichartig wiederholten
Deferral die Begruendung gegen den Code pruefen, statt sie fortzuschreiben.
**Zweite Regel:** neue fault-faehige Geraete brauchen ab jetzt **null**
Engine-Code — nur ihren `FAULT_TYPE_*` in `_KNOWN_FAULT_TYPES` + die
geraeteseitige `inject_fault`-Validierung. Die „9-Naht"-Checkliste
([`M8-welle-2d.md`](M8-welle-2d.md) §4) bleibt unveraendert; die Fault-
Engine ist keine eigene Naht mehr.

## 5. Review-Folge

3 parallele Finder (Rollentrennung). **Kein Korrektheits-Bug** in der
Engine-Logik (alle drei bestaetigen semantische Identitaet zur alten
Battery/Grid-Engine). Eingearbeitete Punkte:

- **F12-Exception-Isolation entfernt** (Finder A/B-Headline): die alte
  `_FaultPortComposition` lief Grid auch bei Battery-Exception (try/finally)
  und re-raiste danach. **Bewertung: kein echter Regress** — auch der alte
  Code re-raiste, der Tick bricht ab, es wird keine Telemetrie emittiert;
  zwei Laeufe mit gleichem Seed werfen identisch an derselben Stelle ab
  (Determinismus bleibt). Der TickLoop faengt Fault-Exceptions nicht (nur
  Span-Tracing-try/finally), also gibt es kein Swallowed-Exception-
  Szenario, das F12 schuetzen muesste. Dokumentiert, nicht wiederhergestellt.
- **Determinismus haengt jetzt an Fault-Listen-Reihenfolge** (Finder A):
  nur relevant, wenn ein Geraet zwei Fault-Typen gleichzeitig traegt —
  aktuell unterstuetzt jedes der 5 Geraete genau einen Typ, also nicht
  erreichbar (im ADR §2.3 vermerkt).
- **Test-Gaps geschlossen** (Finder A/B/C): NEU Tests fuer den
  mistargeting-Wurf (`FaultUnsupportedTypeError` durch die Engine),
  target-None-Branches (inject + clear) und den non-injectable-device-Skip
  — die Branches, die der entfernte F12-Composite-Test nicht mehr deckt.
- **Integration-Test umging `_compose_fault_port`** (Finder C): auf den
  produktiven Composer umgestellt (echter E2E-Wiring-Guard inkl. fail-fast-
  Validierung); der schwache Determinismus-Smoke (Diesel hat keine RNG-
  Konsumenten) ehrlich umdokumentiert (Telemetrie-Stabilitaet, nicht Seed-
  Beweis — der starke Beweis liegt in `test_fault_demo_scenario.py`).

**Bewusst nicht in Scope** ([`ADR 0059`](../../adr/0059-generic-scenario-fault-engine.md)
§6): Target-Typ-Vorvalidierung beim
Laden (Fault-Typ ↔ Ziel-Geraetetyp; aktuell wirft ein Mismatch beim Tick),
produktiver Composite-Adapter unter `adapters/driven/`, AgentBus-getriebene
manual-recovery.
