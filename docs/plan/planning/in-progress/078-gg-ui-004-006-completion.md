# 078 — UI-Vervollstaendigung (Start-Knopf + grafische Geraete-Ansicht)

**Status:** **Aktiv — in Arbeit (`in-progress/`, seit 2026-07-13). S1 (SVG-Diagramm)
done, S2 (Start-Knopf) + S3 (Handbuch/Closure/Release) offen.**
**Datum:** 2026-07-13

---

## Ziel

Zwei bei der UI-Traceability-Durchsicht (2026-07-13) aufgedeckte Nachzuege schliessen:

- [`GG-UI-004`](../../../../spec/lastenheft.md#gg-ui-004) (**MUSS**, Replay-Steuerung):
  Die Abnahme verlangt „mindestens **Start**, Pause, Resume, Stop". Die UI bot bisher
  nur Pause/Resume/Stop; **Start** lief ausschliesslich ueber die HTTP-API bzw. den
  Demo-Auto-Start. → Start-Knopf in der Control-Seite.
- [`GG-UI-006`](../../../../spec/lastenheft.md#gg-ui-006) (**SOLLTE**, grafische
  Geraete-Ansicht): bisher eine HTMX-Polling-**Tabelle** (erfuellte das bedingte
  Minimum); die echte **grafische** Darstellung (Inline-SVG) war als Welle-7-Erbschaft
  zurueckgestellt. → SVG-Einlinien-Diagramm.

Beide Design-Entscheidungen vom User bestaetigt (2026-07-13): **SVG-Einlinien-Diagramm**
(Sammelschiene + Geraeteknoten) fuer die Geraete-Grafik, **Start-Knopf fuer
pending-Runs** (im auto-startenden Demo disabled/„laeuft bereits") fuer die
Replay-Steuerung.

## Slice-Schnitt

| Slice | Inhalt | Rolle |
| --- | --- | --- |
| **S1** ✓ | **SVG-Einlinien-Diagramm ([`GG-UI-006`](../../../../spec/lastenheft.md#gg-ui-006)):** `_devices_content.html` bekommt einen `#devices-diagram`-Container; der bestehende `/devices/state`-Poll (1s) speist per `renderDiagram(payload)` zusaetzlich zur Tabelle ein SVG (Sammelschiene mit Netz/Batterie/PV/Last/Zaehler-Knoten, nach worst-case-Quality eingefaerbt, Fault-Flag-Warnung; XSS-sicher via `createElementNS`). Konsistent mit der bestehenden client-seitigen Tabelle; Integration-Smoke. | Implementation |
| **S2** | **Start-Knopf ([`GG-UI-004`](../../../../spec/lastenheft.md#gg-ui-004)):** `ControlAction` um `start` erweitern (sanktionierter Literal-Pfad, `ControlRequest`-Docstring) + Control-POST-Handler + Control-Seite mit Start-Button (enabled nur bei `pending`; sonst disabled/„laeuft bereits"). Ggf. [`ADR 0039`](../../adr/0039-run-control-and-status-tracking.md)-Amendment. Tests. | Implementation |
| **S3** | **Handbuch + Closure:** neue Screenshots (SVG-Grafik + Control-mit-Start) ins Anwenderhandbuch; Review vor Commit; `make gates` + `docs-check` + `fullbuild`; Release. | Implementation |

## DoD

- Grafische Geraete-Ansicht: die Devices-Page zeigt ein SVG-Einlinien-Diagramm der
  MVP-Geraete (ID/Typ/Zustand/Quality grafisch), live-aktualisiert; Tabelle bleibt
  daneben.
- Replay-Steuerung: die Control-Seite bietet einen Start-Knopf (funktional fuer
  `pending` Runs, disabled sonst) — die Abnahme „bietet Start an" ist erfuellt.
- Additiv/regressionsfrei: bestehende Devices-/Control-Smokes bleiben gruen;
  `make gates` + `make docs-check` + `make fullbuild` gruen.
- **Release-Entscheidung:** ja (Patch — reine UI-Vervollstaendigung, kein Vertrags-/
  Determinismus-Delta).

## Bezug

- [`GG-UI-004`](../../../../spec/lastenheft.md#gg-ui-004) +
  [`GG-UI-006`](../../../../spec/lastenheft.md#gg-ui-006).
- [`ADR 0039`](../../adr/0039-run-control-and-status-tracking.md) (Run-Control/Status)
  fuer die `start`-Action.
- M5-Welle-6a/6b (Fault-Form / Devices-Tabelle) als UI-Muster-Vorlage.
