# 027 — Noqa-Abbau und Noqa-Gate-Scharfschaltung

**Status:** Next — Scope skizziert, noch kein aktiver Slice.
**Datum:** 2026-05-24
**Ausloeser:** `tools/check_noqa.py` meldet bestehende `# noqa`-Marker.
**Ziel:** Alle aktuellen `# noqa`-Marker entfernen und danach das Noqa-Gate
hart schalten.

---

## 1. Zielbild

Das Repository soll keine lokalen `# noqa`-Suppressions mehr enthalten.
Bestehende Faelle werden entweder durch bessere Typisierung,
kleinere Funktionen, explizite Hilfsobjekte, passende Domain-Errors
oder Test-Stubs ohne ungenutzte Argumente ersetzt.

Ausnahme-Regel:

- Es werden in diesem Slice keine neuen `# noqa`-Marker eingefuehrt.
- Bestehende Marker werden entfernt; verbleibende Marker sind No-Go fuer die
  Auslieferung dieses Slices, solange kein Folgepaket-Freigabeprozess abgeschlossen ist.
- Eine dauerhafte technische Ausnahme darf im Rahmen dieses Spikes nicht
  per `# noqa` gelöst werden. Falls technische Huerde vorliegt, ist ein
  Folgepaket mit separatem Freigabeprozess anzulegen.

Minimale Ausnahmedokumentation für ein Folgepaket (obligatorisch, falls
technisch unvermeidbar):

- Kurzbegründung (1 Satz), betroffene Datei/Zeile(n), Sicherheits-/Stabilitätsrisiko.
- Konkreter alternativer Plan (neuer Paket-Scope, neue DoD, erwartete Marker-Reduktion).
- Owner + Datum + Referenz auf Folge-PR/Issue.
- Freigabe durch fachliche Leitung + Architektur-Review mit Datum.

Nach Abschluss der Ausnahme-Dokumentation bleibt der finale Gate im Slice trotzdem
ein Blocker: `python tools/check_noqa.py --fail-on-noqa` auf dem vollständigen
Scope darf erst nach Schliessung des Folgepakets gruen laufen.

Nach Abschluss gilt:

- `python tools/check_noqa.py --fail-on-noqa` findet keine Marker.
- `make lint` bleibt gruen.
- `make format-check` bleibt gruen.
- Das Noqa-Gate wird in einem Folge-Commit in die Docker-/Make-Gates
  aufgenommen.

## 2. Aktueller Bestand

Quelle:

```bash
python tools/check_noqa.py
```

Stand 2026-05-24 (durch erneuten Lauf vor Paketstart zu verifizieren):

| Gruppe | Anzahl | Dateien |
| ------ | ------ | ------- |
| `TRY003` | 13 | HTTP-API, Agent-Bus, Scenario-Validator, TickLoop-Snapshot-Resume |
| `PLR0913` | 5 | Observability-Port/-Adapter, OTLP-Config/-Logs, Scenario-Loader, RuleBasedAgent |
| `PLR0915` / `C901` | 5 | TickLoop, RuleBasedAgent, Scenario-Validator |
| `ARG002` / `ARG003` | 5 | Device-Models und Test-Stubs |
| `BLE001` | 3 | `tools/arch_check.py` grimp-API-Fallbacks |
| `S101` | 1 | `RuleBasedAgent` interner Konstruktor-Assert |
| `S311` | 1 | Mersenne-Twister-Adapter |
| `PLR0911` | 1 | Comparator-Dispatcher in RuleBasedAgent |
| `RUF100` | 1 | Unused-noqa in Test-Stub-Zeile |

Hinweis: Eine Zeile kann mehrere Ruff-Codes enthalten; die Summe der
Gruppen-Codes kann daher ober- oder unterhalb der Kommentarstellenzahl
liegen, sofern der Ausführungsmodus von `check_noqa` identisch bleibt.

## 3. Arbeitspakete

### 3.0 Hard-Steuerung der Reihenfolge (nicht parallel)

Die Pakete `A`–`E` dürfen wegen Überschneidungen in `tick_loop.py`,
`validator.py` und `rule_based.py` **nicht parallel** abgearbeitet werden.
Verbindliche Reihenfolge:

1. Paket A
2. Paket E
3. Paket C
4. Paket B
5. Paket D

Nach jedem Paket gilt:

- `python tools/check_noqa.py` ausfuehren (keine neuen Marker in bereits
  bereinigten Bereichen) als harte Stufe:
  - `python tools/check_noqa.py --fail-on-noqa <Datei1> <Datei2> ...`
- Nach Paket A–E (und ohne offene technische Ausnahmen) folgt die finale
  Repo-Absicherung mit:
  - `python tools/check_noqa.py --fail-on-noqa`
- Betroffene Paket-Tests laufen gruen.
- Bei betroffenen Dateien in den Kernpaketen darf kein anderer Paket-Scope
  gestartet werden, solange kein Testlauf + Check in diesem Paket abgeschlossen ist.
- Bei betroffenen `Protocol`-Schnittstellen werden einschliesslich
  Contract-Tests/Mocks erneut ausgeführt.

### A — Test- und Stub-Faelle zuerst

Scope:

- `tests/unit/hexagon/core/devices/test_protocol_contract.py`
- `tests/unit/hexagon/core/scenario/test_loader_welle_6b.py`
- `src/grid_gym/hexagon/core/devices/battery/model.py`
- `src/grid_gym/hexagon/core/devices/grid_connection/model.py`

Vorgehen:

- Test-Stubs so umbauen, dass ungenutzte Parameter als `_state`,
  `_run_id` oder ueber Hilfsfunktionen modelliert sind.
- Device-Methoden mit bewusst ignoriertem Payload ueber eine
  lokale `_payload = payload`-freie Signaturloesung pruefen; wenn
  der `Protocol`-Vertrag oder bestehende Aufrufer den Namen erzwingen, eine kleine interne
  `_ignore_payload(payload)`-Hilfsfunktion nur bei echtem Bedarf.
- `RUF100` faellt automatisch weg, sobald die betreffende `noqa`
  entfernt ist.

Akzeptanz:

 - Keine `ARG002`, `ARG003`, `RUF100`-Marker mehr.
 - Betroffene Unit-Tests laufen gruen.
 - Bei Signaturanpassungen in protocol-gebundenen Methoden gelten Contract-Tests
   in `tests/unit/hexagon/core/devices/test_protocol_contract.py` als hard.

Paket-Abnahme (hard):
- `python tools/check_noqa.py --fail-on-noqa tests/unit/hexagon/core/devices/test_protocol_contract.py tests/unit/hexagon/core/scenario/test_loader_welle_6b.py src/grid_gym/hexagon/core/devices/battery/model.py src/grid_gym/hexagon/core/devices/grid_connection/model.py`
- `pytest tests/unit/hexagon/core/devices/test_protocol_contract.py`
- `pytest tests/unit/hexagon/core/scenario/test_loader_welle_6b.py`
- Contract-Verhalten in betroffenen `Device`-/Protocol-Flows unverändert: bestehende
  erfolgreiche und Fehlerpfade sind testgedeckt.

### B — TRY003 durch explizite Error-Typen oder Factory-Helfer

Scope:

- `src/grid_gym/adapters/driving/http_api/app.py`
- `src/grid_gym/hexagon/core/agents/bus.py`
- `src/grid_gym/hexagon/core/scenario/validator.py`
- `src/grid_gym/hexagon/core/simulation/tick_loop.py`

Vorgehen:

- Fuer Konfigurations-/Snapshot-Mismatch-Faelle gezielte
  Error-Klassen oder kleine Message-Factory-Funktionen einfuehren,
  sodass Ruff keine langen Inline-Literals in `raise`-Statements
  mehr meldet.
- TickLoop-Resume-Diagnostik als eigene Helper-Funktionen kapseln,
  aber bestehende Exception-Typen und Fehlermeldungsinformation
  erhalten.
- Keine pauschale Verschiebung in Per-File-Ignores.

Akzeptanz:

- Keine `TRY003`-Marker mehr.
 - Snapshot-/Validator-Tests pruefen weiterhin die diagnostisch
  relevanten Pfad- und Mismatch-Details.
 - Bestehende Public-API-/Contract-Behauptungen zu den berührten Komponenten
  bleiben bestehen.

Paket-Abnahme (hard):
- `python tools/check_noqa.py --fail-on-noqa src/grid_gym/adapters/driving/http_api/app.py src/grid_gym/hexagon/core/agents/bus.py src/grid_gym/hexagon/core/scenario/validator.py src/grid_gym/hexagon/core/simulation/tick_loop.py`
- `pytest tests/unit/hexagon/core/scenario/test_loader_welle_6b.py`
  - gezielte Regressionstests für:
    - `tests/unit/hexagon/core/scenario` (Fehlerpfade, Snapshot-/Mismatch-Cases),
    - `tests/unit/hexagon/core/agents` (Fallback-/Bus-Fehlerpfade, falls betroffen),
    - `tests/unit/adapters/driving/http_api` (HTTP-API-Contract-/Request-Handling-Pfade).

### C — PLR0913-APIs entflechten ohne Vertragsbruch

Scope:

- `src/grid_gym/hexagon/ports/driven/observability.py`
- `src/grid_gym/adapters/driven/observability_null/null_adapters.py`
- `src/grid_gym/adapters/driven/telemetry_otlp/logs.py`
- `src/grid_gym/adapters/driven/telemetry_otlp/_config.py`
- `src/grid_gym/hexagon/core/scenario/loader.py`
- `src/grid_gym/hexagon/core/agents/rule_based.py`

Vorgehen:

- Observability-Log-Parameter in ein typed Record/Envelope ziehen,
  falls das den Port-Vertrag nicht verschlechtert.
- OTLP-Config-Overrides als Mapping oder Builder-Objekt pruefen.
- Loader-/Agent-Konstruktoren ueber kleine Config-Dataclasses
  zusammenfassen, aber bestehende externe API-Kompatibilitaet
  gezielt testen.

Akzeptanz:

- Keine `PLR0913`-Marker mehr.
 - Port-/Adapter-Contract-Tests decken die neue Signaturform ab.
 - Bei Signaturänderungen: bestehende Aufruferstellen oder
  Vertragstests sind zwingend nachzuziehen.

Paket-Abnahme (hard):
- `python tools/check_noqa.py --fail-on-noqa src/grid_gym/hexagon/ports/driven/observability.py src/grid_gym/adapters/driven/observability_null/null_adapters.py src/grid_gym/adapters/driven/telemetry_otlp/logs.py src/grid_gym/adapters/driven/telemetry_otlp/_config.py src/grid_gym/hexagon/core/scenario/loader.py src/grid_gym/hexagon/core/agents/rule_based.py`
- `pytest tests/unit/hexagon/ports`
- `pytest tests/unit/adapters`
- `pytest tests/unit/hexagon/core/scenario/test_loader_welle_6b.py`
- mindestens ein API-Contract/Vertrags-Test der berührten Module gegen alte/neu
  aufrufende Pfade.

### D — Lange Funktionen und Komplexitaet reduzieren

Scope:

- `src/grid_gym/hexagon/core/simulation/tick_loop.py`
- `src/grid_gym/hexagon/core/scenario/validator.py`
- `src/grid_gym/hexagon/core/agents/rule_based.py`

Vorgehen:

- Lange Restore-/Validate-Blöcke in feldbezogene Parser-Helfer
  zerlegen.
- `_run_tick_body` entlang der bestehenden Phasen A0a/A/A2/B/C/D/D2/E
  auf private Phase-Methoden aufteilen.
- Rule-Parsing in Condition-/Action-Parser trennen.
- Comparator-Dispatcher als Mapping auf kleine Predicate-Funktionen
  ersetzen, wenn dadurch `PLR0911` verschwindet ohne Lesbarkeit zu
  verlieren.

Akzeptanz:

- Keine `PLR0915`, `C901`, `PLR0911`-Marker mehr.
 - Replay-/TickLoop-/Scenario-Validator-Tests laufen gruen.
 - Bestehende Schnittstellen-Verhaltenstests (inkl. Regel- und
  Resume-Szenarien) laufen weiterhin gruen.

Paket-Abnahme (hard):
- `python tools/check_noqa.py --fail-on-noqa src/grid_gym/hexagon/core/simulation/tick_loop.py src/grid_gym/hexagon/core/scenario/validator.py src/grid_gym/hexagon/core/agents/rule_based.py`
- `pytest tests/unit/hexagon/core/simulation/test_tick_loop.py`
- `pytest tests/unit/hexagon/core/scenario/test_validator.py`
- `pytest tests/unit/hexagon/core/agents/test_rule_based.py`
- Replay-/Resume-spezifische Integrationsabdeckung wird vor/nach Refactor
  gegen identische Erwartungsartefakte (Snapshots, Entscheidungswege) gegengeprueft.

### E — Spezialfaelle ersetzen

Scope:

- `tools/arch_check.py`
- `src/grid_gym/adapters/driven/random_mt/mersenne_twister.py`
- `src/grid_gym/hexagon/core/agents/rule_based.py`

Vorgehen:

- `BLE001`: grimp-Aufrufe mit engeren bekannten Exception-Typen
  absichern; falls grimp keine stabile Exception-Hierarchie anbietet,
  Wrapper-Funktion mit bewusst typisiertem Tool-Error einfuehren.
- `S311`: Ruff-konforme Trennung zwischen deterministischem PRNG und
  Security-Kontext pruefen, z. B. Adapter-Kommentar im Code ohne
  Suppression oder alternative Ruff-konforme Konstruktion.
- `S101`: Konstruktor-Assert durch explizite Guard-Exception oder
  typisierten Helper ersetzen.

Akzeptanz:

 - Keine `BLE001`, `S311`, `S101`-Marker mehr.
 - `make arch-check-custom` bleibt gruen.

Paket-Abnahme (hard):
- `python tools/check_noqa.py --fail-on-noqa tools/arch_check.py src/grid_gym/adapters/driven/random_mt/mersenne_twister.py src/grid_gym/hexagon/core/agents/rule_based.py`
- `pytest tests/unit/hexagon/core/agents/test_rule_based.py`
- `pytest tests/unit/adapters/driven/random_mt`
- `pytest tests/unit/test_arch_check_registration.py` oder `pytest tests/unit/test_arch_check_domain_frozen.py`
  Arch-Check-Regressionstestset im Repo)
- Bei `tools/arch_check.py` ist eine lokale Validierung mit vorhandenen
  bekannten Fallback-Szenarien in den bestehenden Testpfaden nachweislich grün.

## 4. Scharfstellung

Erst nachdem `python tools/check_noqa.py --fail-on-noqa` lokal gruen ist:

1. Dockerfile-Stage fuer Noqa-Check ergaenzen oder in bestehendes
   Custom-Arch-/Lint-Gate integrieren.
2. Make-Target ergaenzen, z. B. `make noqa-check`.
3. Aggregierte Gates (`make gates` und spaeter CI) um dieses Target
   erweitern.
4. `docs/plan/planning/next/README.md` und spaeter Lifecycle-Move nach
   `in-progress/` bzw. `done/` aktualisieren.

## 5. Definition of Done

- `python tools/check_noqa.py --fail-on-noqa` meldet:
  `[check_noqa] no # noqa markers found`
- `make lint` gruen.
- `make format-check` gruen.
- `make arch-check-custom` gruen, falls `tools/arch_check.py` beruehrt wurde.
- Relevante Unit-Tests fuer geaenderte Module gruen.
- Noqa-Check ist in Make/Docker als hartes Gate verdrahtet.
- Dieses Plan-Dokument wandert nach `done/` mit kurzer Closure-Notiz.

No-Go bei diesem Slice:

- `python tools/check_noqa.py --fail-on-noqa` ist gruen, aber ein hartes DoD- oder
  Contract-Check fehlt.
- Es werden neue Marker als Dauer-Ausnahme eingeführt statt ein Folgepaket mit
  dokumentierter Freigabe zu starten.
