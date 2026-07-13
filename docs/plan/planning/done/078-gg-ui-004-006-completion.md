# 078 — UI-Vervollstaendigung (Start-Knopf + grafische Geraete-Ansicht)

**Status:** **Abgeschlossen (`done/`, 2026-07-13). S1 (SVG-Diagramm) + S2 (Start-Knopf)
+ S3 (Handbuch/Closure) done. Released als v0.7.1.** Der bess-ems-E2E-Rerun gegen die
neue v2.2.0-Image + der Dashboard-Live-Feed-Bugfix ([`GG-UI-002`](../../../../spec/lastenheft.md#gg-ui-002)/[`GG-UI-003`](../../../../spec/lastenheft.md#gg-ui-003),
fehlende HTMX-ws-Extension) fielen im Zuge der Handbuch-Screenshots an.
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
| **S2** ✓ | **Start-Knopf ([`GG-UI-004`](../../../../spec/lastenheft.md#gg-ui-004)):** `ControlAction` (Domain + HTTP-Schema) um `start` erweitert (sanktionierter Literal-Pfad) + generischer Control-POST-Handler + Control-Seite mit Start-Button (status-poll-JS: enabled nur bei `pending`; sonst disabled/„laeuft bereits"). [`ADR 0039`](../../adr/0039-run-control-and-status-tracking.md) Decision 13 amendiert (`start`: `pending → running`, running=No-op, paused/stopped=409). Tests + empirisch verifiziert. | Implementation |
| **S3** ✓ | **Handbuch + Closure:** Screenshots (SVG-Grafik, Control mit Start, **Dashboard mit Live-Feed+Chart**, overview, health = 8 Nav-Seiten); Closure-Review (keine HIGH/MEDIUM, 2 LOW gefaltet); **CI-Fix** (openapi-Enum-Pin) + **Dashboard-Live-Feed-Bugfix** (fehlende HTMX-ws-Extension + Chart-Metrik-Mapping). `make gates` + `docs-check` + `fullbuild` gruen. **→ Released v0.7.1.** | Implementation |

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
