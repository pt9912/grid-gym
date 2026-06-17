# 047 — Device-Management-Protokolladapter SNMP und LwM2M

**Status:** Open — Trigger-Watch
**Datum:** 2026-06-16
**Quelle:** Stakeholder-Frage zu Device-Management-Protokollen; neue
Lastenheft-IDs [`GG-SNMP-001`](../../../../spec/lastenheft.md#gg-snmp-001) und [`GG-LWM2M-001`](../../../../spec/lastenheft.md#gg-lwm2m-001).

---

## Kontext

M4 hat die `DeviceProtocolPort`-Familie mit fuenf gelieferten
Simulationsadaptern abgeschlossen: MQTT, Modbus-TCP, OPC-UA, DNP3 und
IEC-61850. SNMP und LwM2M sind fachlich ebenfalls Device-Management- und
Telemetry-Protokolle, gehoeren aber nicht zum M4-Lieferumfang und haben
aktuell keinen Adapter-Code, kein Adapter-Profil und keine ADR.

Diese Notiz verhindert einen stillen Support-Claim: SNMP und LwM2M sind
als `SOLLTE`-Folgearbeit verankert, aber bis zur Lieferung nicht
unterstuetzt.

## Erwartete Lieferung

Die Arbeit wird in mindestens drei getrennte Slices geschnitten:

1. **Profil-/ADR-Slice:** Architekturentscheidung, ob beide Protokolle
   denselben `DeviceProtocolPort`-Sync-Vertrag nutzen oder ob LwM2M wegen
   Observe/Notify und Rollenmodell ein Schwester-Pattern braucht.
2. **SNMP-Slice:** `src/grid_gym/adapters/driven/protocol_snmp/` <!-- d-check:ignore (geplant: entsteht mit Trigger-Aktivierung) -->
   mit OID-/MIB-Mapping, Version-/Security-Annahmen, Polling-Read,
   optionalem Set-Pfad nur bei expliziter Profilfreigabe, typisierten
   Fehlern, Unit-Tests und deterministischem Smoke-Test.
3. **LwM2M-Slice:** `src/grid_gym/adapters/driven/protocol_lwm2m/` <!-- d-check:ignore (geplant: entsteht mit Trigger-Aktivierung) -->
   mit Object-/Resource-Mapping, Client-/Server-Rollenentscheidung,
   CoAP-/Security-Annahmen, Observe-/Read-/Write-/Execute-Profil,
   typisierten Fehlern, Unit-Tests und deterministischem Smoke-Test.

Beide Adapter muessen als Simulations- und Testadapter dokumentiert
werden und duerfen keine produktive Anlagensteuerung versprechen.

## Aktivierungs-Bedingung

Aktivierung sobald eines der folgenden Ereignisse eintritt:

- Stakeholder-Bedarf fuer SNMP- oder LwM2M-basierte Device-Management-
  Demo;
- Integrationspartner verlangt ein konkretes Mapping fuer OIDs/MIBs oder
  LwM2M Objects/Resources;
- Review-/Validation-Befund fordert Device-Management-Protokolle ueber
  die bestehenden Feldbus-/Telemetry-Adapter hinaus.

SNMP ist der bevorzugte erste Implementierungs-Slice, sofern kein
LwM2M-spezifischer Stakeholder-Bedarf vorliegt: der Polling-Pfad ist
kleiner und etabliert das Erweiterungsmuster fuer neue
`DeviceProtocolPort`-Adapter.

## Wandert nach

- `next/`, sobald ein Profil-/ADR-Scope fuer SNMP oder LwM2M skizziert
  ist,
- `in-progress/`, wenn der konkrete Adapter-Slice aktiv geplant ist,
- `done/`, wenn Adapter-Profil, Implementierung, Tests und Doku fuer den
  jeweiligen Protokoll-Scope geliefert sind.

## Bezug

- [`GG-SNMP-001`](../../../../spec/lastenheft.md#gg-snmp-001) —
  SNMP als geplanter Simulationsadapter.
- [`GG-LWM2M-001`](../../../../spec/lastenheft.md#gg-lwm2m-001) —
  LwM2M als geplanter Simulationsadapter.
- [`GG-AR-PORT-DRN-007`](../../../../spec/architecture.md#driven-ports-vom-kern-aufgerufen) —
  `DeviceProtocolPort` als bestehende Adapter-Surface.
- [`ADR 0030`](../../adr/0030-device-protocol-port-surface.md) —
  `DeviceProtocolPort`-Sync-Vertrag und Lifecycle-Pattern.
- [`spec/protocol_profiles.md`](../../../../spec/protocol_profiles.md) —
  aktueller Profil-Index der fuenf gelieferten Adapter; SNMP/LwM2M werden
  dort erst mit Profil-ADR und Implementierung aufgenommen.
