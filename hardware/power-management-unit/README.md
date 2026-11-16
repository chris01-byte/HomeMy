# HomeMy Power Management Unit (PMU)

Die PMU ist die zentrale Energieverteilungs-, Schutz-, Mess- und Zustandssteuerung des HomeMy-Roboters.

## Aktueller Stand

**Die einzige aktuelle Leiterplatte ist Revision A2, 280 × 260 mm**, unter [`rev-a2-layout-280x260/`](rev-a2-layout-280x260/README.md).

- CAD vollständig, Entwurf, **nicht bestellbar**. Alle Fertigungs-, Bestückungs-, Bestromungs- und Produktionsfreigaben sind `false`; maßgeblich ist `rev-a2-layout-280x260/release-status.json`.
- Die Gegenprüfung vom 2026-11-16 hat 25 Befunde (GP-01 bis GP-25) ergeben und empfiehlt, diesen Stand nicht zu bestellen: [`reviews/2026-11-16-rev-a2-gegenpruefung/`](reviews/2026-11-16-rev-a2-gegenpruefung/README.md).
- Frühere Platinen (360 × 300 mm Rev A, 300 × 280 mm A1) und das alte Bestellpaket Rev A-P1 wurden am 2026-11-16 entfernt. Sie sind in der Git-Historie bis Commit `d37c7f7` abrufbar. Entscheidung: `docs/decisions/2026-11-16-pmu-rev-a2-canonical.md`.

## Verzeichnisse

| Pfad | Inhalt |
|---|---|
| `rev-a2-layout-280x260/` | Aktuelles KiCad-Projekt (Schaltplan und Leiterplatte), Stückliste, Fertigungsentwurf, CAD-Nachweise |
| `rev-a/` | Schaltungsauslegung Rev A, die für A2 unverändert gilt: Schaltungsbeschreibungen, Berechnungen, Datenblätter, Prozessunterlagen, Prüferquellen. Enthält keine Leiterplatte mehr |
| `reviews/` | Prüfberichte mit Befunden, Rechenwegen, Skripten und Ergebnisdaten |

## Quellen der Wahrheit

In dieser Reihenfolge lesen:

1. `requirements.yaml` – verbindliche elektrische Werte und Statusklassen.
2. `ASTRA_PCB_HANDOFF.md` – Topologie, Schutzkonzept und Systemverhalten (ursprünglicher Auftrag).
3. `interfaces-and-layout.md` – Anschlüsse, Schnittstellen und Layoutregeln.
4. `rev-a/README.md` und `rev-a/design/` – ausgearbeitete Schaltung, Bauteilwahl, Berechnungen.
5. `rev-a2-layout-280x260/README.md` – aktuelle Leiterplatte und ihr Status.
6. `reviews/2026-11-16-rev-a2-gegenpruefung/README.md` – offene Befunde.
7. `verification-plan.md` und `DESIGN_REVIEW_AND_BRINGUP.md` – Prüf- und Inbetriebnahmestrategie.

`REQUIREMENTS_TRACEABILITY.md`, `REV_A_ASSUMPTIONS.md` und `REV_B_VALIDATION.md` ordnen Anforderungen, Annahmen und spätere Messungen zu.

## Nächster Schritt

Über die Befunde entscheiden und die angenommenen Änderungen in einer KiCad-Revision der A2-Platine umsetzen. Topologie, Netze, Schutzfunktionen und Bauteilwerte nur anhand dokumentierter Entscheidungen ändern. Danach native Prüfungen und die Prüfskripte der Gegenprüfung wiederholen.

## Freigabestatus

- Engineering-Prototyp: erst nach behobenen Befunden, Prüfung durch eine Fachperson und ausdrücklicher Bestellfreigabe.
- Bestromung: erst nach Schließen der Energization Gates.
- Produktion/Rev B: nicht freigegeben.
- Aktorbewegung: nicht freigegeben.
