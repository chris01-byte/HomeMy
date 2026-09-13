# HomeMy Power Management Unit (PMU)

## Verbindlicher Arbeitsstand

Die PMU ist die zentrale Energieverteilungs-, Schutz-, Mess- und Zustandssteuerung des HomeMy-Roboters.

Der nächste PCB-Arbeitsstand ist **ausschließlich 300 × 280 mm**. Frühere Verkleinerungsversuche mit 250 × 200, 275 × 210, 280 × 220 und 300 × 220 mm sind verworfen und nicht Teil dieses Arbeitsstands.

## Quellen der Wahrheit

In dieser Reihenfolge lesen:

1. `requirements.yaml` – verbindliche elektrische Werte und Statusklassen.
2. `ASTRA_PCB_HANDOFF.md` – Topologie, Schutzkonzept und Systemverhalten.
3. `interfaces-and-layout.md` – Anschlüsse, Schnittstellen und Layoutregeln.
4. `rev-a/README.md` und `rev-a/design/` – ausgearbeitete Schaltung, Bauteil- und Hochstromregeln.
5. `verification-plan.md` – Prüf- und Inbetriebnahmestrategie.
6. `ASTRA_300X280_LAYOUT.md` – begrenzter Arbeitsauftrag für das neue Layout.

## Beibehaltene Referenz

`rev-a/` ist die erfolgreiche elektrische und mechanische Referenz. Sie enthält den hierarchischen KiCad-Schaltplan, Footprints, Bauteilauswahl, Hochstromregeln, Berechnungen und überprüfbare Fertigungsgrundlagen. Ihre vorhandene Leiterplatte darf als Referenz dienen, ist aber **nicht** die Zielgeometrie des neuen Layouts.

Topologie, Netznamen, Schutzfunktionen, Bauteilwerte, Footprints, Kelvin-Verbindungen, Gate-Beschaltung, Busbar-/Press-fit-Schnittstellen und Sicherheitsregeln dürfen beim Übertragen nicht stillschweigend verändert werden.

## Aktiver Layoutauftrag

Astra erstellt einen neuen, vollständigen KiCad-PCB-Arbeitsstand in:

`hardware/power-management-unit/rev-a2-300x280/`

Die Zielkontur ist fest 300 × 280 mm. Alte kompakte Layouts dürfen weder fortgesetzt noch als CAD-Quelle kopiert werden. Der elektrische Ausgangspunkt ist der Schaltplan aus `rev-a/kicad/`.

## Freigabestatus

- Engineering-Prototyp: nach vollständiger Prüfung und menschlicher Bestellfreigabe zulässig.
- Bestromung: erst nach Schließen der in den Dokumenten genannten Energization Gates.
- Produktion/Rev B: nicht freigegeben.
- Aktorbewegung: durch diesen PCB-Auftrag nicht freigegeben.
