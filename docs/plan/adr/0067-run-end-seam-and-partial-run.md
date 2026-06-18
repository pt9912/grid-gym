# ADR 0067 — Driver-unabhaengige Run-End-Naht + Partial-Run-Markierung (Slice 040)

**Status:** Accepted — Validierung mit Slice-040-Lieferung (`make gates`
gruen: lint/format-check/typecheck/arch-check/test-unit/
`coverage-gate-critical` + `docs-check` + `accept-pin-check`; Unit-Pins fuer
Natur-Terminierung-Finalize, Failure→Partial (kein `diverged`), Headless-
Finalize-genau-einmal, Idempotenz).
**Datum:** 2026-06-17
**Bezug:**

- [`ADR 0049`](0049-replay-lifecycle-finalize-hook.md) §2.1/§7 — `finalize()`-
  Terminal-Naht; ADR 0049 §7 vertagt **genau** die Driver-unabhaengige
  Run-End-Naht + Auto-`completed`-Transition (Trigger 040). Diese ADR
  schliesst die Naht (ohne Auto-`completed`).
- [`ADR 0011`](0011-schaerfung-ohne-abloesung.md) — Schaerfung-ohne-Supersedes
  (Form-Anker; additive Run-Lifecycle-Naht, ADR 0049 bleibt textlich
  unveraendert).
- [`ADR 0039`](0039-run-control-and-status-tracking.md) — `control_state`/
  `request(...)`-Transition-Matrix; diese ADR aendert sie **nicht**.
- [`ADR 0024`](0024-observability-port-trio.md) — `LogPort` (Partial-Run-Reject
  nutzt den bestehenden strukturierten Reject-Log-Pfad).
- [Trigger 040](../planning/done/040-replay-finalize-headless-run-end-seam.md)
  — Forward-Gap (M7-Welle-1b-b-C2-Review-Befund #4).
- [Trigger 039](../planning/done/039-api-replay-trigger-surface.md)
  — API-Replay-Surface (Folge-Slice; konsumiert die Naht).

---

## 1. Kontext

[`ADR 0049`](0049-replay-lifecycle-finalize-hook.md) liefert die idempotente
Core-`TickLoop.finalize()`-Naht, **getriggert aber nur** vom
`DemoTickLoopDriver.stop()` (Lifespan-/extern-Stop). Drei Luecken
(Trigger 040):

1. **Natuerliche Terminierung:** `_tick_forever()` verlaesst den Loop bei
   terminalem `control_state` ohne `finalize()` (nur `stop()` ruft es).
2. **Tick-Failure:** `_force_stop_after_failure` finalisiert nicht; ein
   spaeterer `finalize()` diffte einen **partiellen** Lauf gegen die volle
   Referenz (irrefuehrender `diverged`-Status).
3. **Headless-Runner ohne asyncio-Driver:** die [`GG-MVP-003`](../../../spec/lastenheft.md#gg-mvp-003)-Abnahme-CLI
   (M7-Welle-2) treibt Ticks ggf. ohne `DemoTickLoopDriver` und muss
   `finalize()` selbst garantieren.

---

## 2. Entscheidung

### §2.1 Run-Session-Kontextmanager (Core-Run-End-Naht)

NEU sync-Kontextmanager `TickLoop.run_session()` (`contextlib.contextmanager`),
der `finalize()` im `finally` **garantiert** — fuer **jeden** Konsumenten
(Headless-Runner, Test-Runner) eine driver-unabhaengige Naht:

```python
with tick_loop.run_session():
    while tick_loop.control_state not in ("stopped", "completed"):
        tick_loop.tick()
# finalize() ist hier garantiert genau einmal gelaufen
```

- **Normaler Exit:** `finalize()` im `finally` (Replay-Diff bei Bindung).
- **Exception-Exit:** `mark_run_failed()` **vor** dem `finally`-`finalize()`
  (Partial-Run, §2.2/§2.3), dann Re-Raise.
- **Idempotenz** bleibt bei `finalize()` (`_finalized`-Flag) — der
  Kontextmanager fuegt **keine** zweite Emission hinzu, wenn ein Caller
  zusaetzlich `stop()`/`finalize()` ruft.

**Kein Auto-`completed`-Transition** (Trigger-040-Option B verworfen): ein
Auto-`completed` braeuchte ein Tick-Budget/Szenario-Ende, das es nicht gibt
([`ADR 0049`](0049-replay-lifecycle-finalize-hook.md) §2.1/§7) — out-of-scope.
Die Naht garantiert `finalize()` **unabhaengig** vom terminalen State; die
latente Natur-Terminierungs-Luecke (falls ein spaeteres Tick-Budget
`completed` auto-setzt) ist dadurch ohne Auto-Transition abgedeckt.

### §2.2 `mark_run_failed()` — Partial-Run-Signal

NEU idempotente Core-Methode `TickLoop.mark_run_failed()` setzt ein
`_run_failed: bool`-Flag. Es markiert, dass der Lauf **abnormal** terminierte
(Tick-Failure) — ein per Failure abgebrochener Lauf ist damit von einem
sauber zu Ende gelaufenen unterscheidbar (heute beide terminal `"stopped"`,
ununterscheidbar). `control_state` bleibt unveraendert (ADR 0039-Matrix
unberuehrt).

### §2.3 `finalize()`-Partial-Zweig

`finalize()` prueft `_run_failed` **vor** dem Replay-Preflight/Diff: bei
gesetztem Flag **kein** `diff_replay()` und **kein** `replay_diff_status`,
stattdessen ein strukturierter `log_port`-Reject (`reason="partial_run"`,
ueber den bestehenden `_log_replay_reject`-Pfad aus ADR 0049 §2.3). Begruendung:
ein Replay-Diff eines partiellen gegen einen vollen Lauf ist fachlich
bedeutungslos — wie der Preflight-Mismatch liefert er **kein** Status, nur
Evidence. Der no-op-Pfad (keine Replay-Bindung) bleibt vorrangig.

### §2.4 Driver-Verdrahtung

`DemoTickLoopDriver._run_loop()` triggert `finalize()` **auf jedem
Exit-Pfad** (statt nur `stop()`):

- **Natuerliche Terminierung** (`_tick_forever` returnt) → `finalize()`.
- **Tick-Failure** → `mark_run_failed()` (vor `_force_stop_after_failure`) →
  `finalize()`.
- **Externer Cancel** (`stop()`) → `finalize()` (sauber, **nicht** als failed
  markiert).

Realisiert ueber einen `finally`-Block in `_run_loop` (gegen einen harten
`finalize()`-Fehler abgeschirmt — ADR 0049 §2.3 F1-Pattern). Der explizite
`finalize()`-Aufruf in `stop()` wird redundant (Idempotenz-Flag) und entfaellt;
der Stop-Status-Mirror (`request("stop")`, Welle-4b-Review-Fix #9) bleibt.

### §2.5 Hexagonal-Reinheit

`run_session()`/`mark_run_failed()` sind reiner Core-Spine (kein Adapter-/
Library-Import); `contextlib` ist stdlib. `make arch-check`
([`AC-HEXAGON-PURE`](0002-language-and-build-stack.md#a-1--architekturtests-verbindlich-automatisiert))
verifiziert. Der Driver triggert, der Core entscheidet
([`GG-AR-P-003`](../../../spec/architecture.md#2-architekturprinzipien)/[`GG-AR-P-007`](../../../spec/architecture.md#2-architekturprinzipien),
Praezedenz ADR 0049 §2.1).

---

## 3. Begruendung

- **Headless-Vorbedingung ([`GG-MVP-003`](../../../spec/lastenheft.md#gg-mvp-003)).** Ein Abnahme-CLI ohne
  asyncio-Driver bekommt mit `run_session()` die `finalize()`-Garantie ohne
  Driver-Kopplung.
- **Partial-Run-Korrektheit.** Ohne `mark_run_failed()` diffte ein
  Failure-Lauf als `diverged` — ein falsches Determinismus-Signal. Das
  Partial-Reject haelt `replay_diff_status` nur fuer **valide** Vergleiche
  definiert (konsistent mit dem Preflight-Reject, ADR 0049 §2.3).
- **Kontextmanager statt Auto-`completed`.** Der CM deckt alle drei Luecken
  ohne den nicht-existenten Tick-Budget-Trigger; Auto-`completed` bleibt ein
  eigener spaeterer Scope.
- **Schaerfung ohne Supersedes ([`ADR 0011`](0011-schaerfung-ohne-abloesung.md)).**
  ADR 0049/0039 bleiben textlich unveraendert; diese ADR ergaenzt eine
  Run-Lifecycle-Naht + ein Partial-Signal additiv.

---

## 4. Reichweite

- NEU `TickLoop.run_session()` + `mark_run_failed()` + `_run_failed`-Flag +
  `finalize()`-Partial-Zweig (`hexagon/core/simulation/tick_loop.py`).
- `DemoTickLoopDriver._run_loop()`: `finalize()` im `finally` +
  `mark_run_failed()` im Failure-Pfad; `stop()`-`finalize()` entfaellt
  (`_tick_loop_driver.py`).
- NEU Unit-Pins (`tests/unit/...`): Natur-Terminierung, Failure→Partial,
  Headless-`run_session`-Finalize-genau-einmal, Idempotenz.
- ADR-Index NEU ADR-0067-Zeile + ADR-0049-`Schaerfungen`-Spalte.
- **Unberuehrt:** `diff_replay()`-Algorithmus, `ReplaySample`/`ReplayDelta`,
  `control_state`-Transition-Matrix (ADR 0039), `replay_diff_status`-Kodierung
  (ADR 0049 §2.4).

---

## 5. Konsequenzen

- **Positiv:** `finalize()` feuert deterministisch genau einmal auf jedem
  Run-End-Pfad (Driver, Headless, natuerliche Terminierung); ein Failure-Lauf
  diffte nicht mehr als `diverged`.
- **Neutral:** `_run_failed` ist Run-Lifecycle-State, **nicht** Tick-
  Determinismus — das Snapshot-Schema traegt es nicht (wie `_finalized`).
- **Neutral:** der Demo-Lauf hat keine Replay-Bindung → `finalize()` no-op
  (unveraendert).

---

## 6. Nicht Gegenstand dieser ADR

- **Auto-`completed`-Transition** (Tick-Budget/Szenario-Ende) — eigener
  spaeterer Scope (ADR 0049 §7).
- **Oeffentliche API-Replay-Bedienung** (`POST /runs` `replay_of` +
  `RunMetadata`-Spalte + Migration) — [Trigger 039](../planning/done/039-api-replay-trigger-surface.md).
- **`started_at`/`ended_at`-Timestamp-Setzen** — eigener Scope (ADR 0049 §7).
- **Asynchroner/entkoppelter Diff** — additive Schaerfung bei Last-Druck
  (ADR 0049 §2.6).
