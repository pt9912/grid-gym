# 040 — `finalize()`-Trigger an einer Core-Run-End-Naht (Headless-Pfad)

**Status:** Open — Forward-Gap aus M7-Welle-1b-b-C2-Review-Folge
**Datum:** 2026-06-09
**Quelle:** M7-Welle-1b-b-C2-Review (Befund #4; Lifecycle-Hook-
Trigger-Pfad).

---

## Kontext

M7-Welle-1b-b liefert den Core-`TickLoop.finalize()`-Replay-Hook
(ADR 0049). **Getriggert** wird er heute aber **ausschliesslich**
vom `DemoTickLoopDriver.stop()` (asyncio-Driver, Lifespan-/extern-
Stop-Pfad). Das deckt den produktiven Demo-/API-Pfad ab (dort
endet ein Lauf ueber `stop()`), hat aber drei Lücken:

1. **Natürliche Terminierung:** `_tick_forever()` verlaesst den
   Loop bei terminalem `control_state` (`stopped`/`completed`).
   `"completed"` wird vom Core heute nie auto-gesetzt (ADR 0049
   §2.1), daher latent — aber falls eine spaetere Welle ein
   Tick-Budget / Szenario-Ende einfuehrt, das `completed`
   auto-setzt, feuert `finalize()` ohne expliziten `stop()`-Aufruf
   nicht.
2. **Tick-Failure-Pfad:** `_force_stop_after_failure` finalisiert
   nicht; ein spaeterer Shutdown-`finalize()` wuerde dann einen
   **partiellen** Lauf gegen die volle Referenz diffen
   (irrefuehrender `diverged`-Status).
3. **Headless-Runner ohne asyncio-Driver:** die `GG-MVP-003`-
   Abnahme-CLI (M7-Welle-2) treibt Ticks ggf. **ohne**
   `DemoTickLoopDriver`. Ein solcher Runner muss `finalize()`
   selbst aufrufen — sonst bleibt der Replay-Diff +
   `replay_diff_status` fuer einen headless-Lauf still aus.

## Offene Substanz (dieser Trigger)

- Eine **explizite Core-Run-End-Naht**, an der `finalize()`
  deterministisch genau einmal feuert — unabhaengig davon, ob ein
  asyncio-Driver, ein Headless-Runner oder ein Tick-Budget den
  Lauf beendet. Optionen: Auto-`completed`-Transition im
  `TickLoop` (mit Finalize-Hook), oder ein Run-Lifecycle-
  Kontextmanager, der `finalize()` im `finally` garantiert.
- **Partial-Run-Markierung:** ein per Tick-Failure abgebrochener
  Lauf sollte beim Diff als unvollstaendig erkennbar sein (statt
  als `diverged`), oder `finalize()` im Failure-Pfad ueberspringen.

## Aktivierungs-Bedingung

- **`GG-MVP-003` Abnahme-CLI (M7-Welle-2)**, falls sie Replay-
  Validierung headless (ohne `DemoTickLoopDriver`) braucht — dann
  ist die Core-Run-End-Naht Vorbedingung.
- ODER Einfuehrung eines Tick-Budgets / Szenario-Endes mit
  Auto-`completed`-Transition.

## Wandert nach

`done/`, sobald `finalize()` an einer Driver-unabhaengigen Core-
Run-End-Naml deterministisch feuert (Headless + natuerliche
Terminierung abgedeckt) und der Partial-Run-Fall sauber behandelt
ist.

## References

- [`../done/M7-welle-1b-b.md`](../done/M7-welle-1b-b.md) —
  Replay-Lifecycle-Slice (1b-b-D-1 Terminal-Naht).
- [`../in-progress/M7-mvp-completion.md`](../in-progress/M7-mvp-completion.md)
  — `GG-MVP-003`-Abnahme-CLI ist M7-Welle-2 (Headless-Konsument).
- [`../../adr/0049-replay-lifecycle-finalize-hook.md`](../../adr/0049-replay-lifecycle-finalize-hook.md)
  — §2.1 Terminal-Naht (Driver triggert, Core entscheidet).
