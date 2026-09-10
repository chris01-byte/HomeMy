# Startprompt für GPT Astra: HomeMy PMU Revision A

Arbeite im GitHub-Repository `chris01-byte/HomeMy` auf Basis des aktuellen `main`-Standes. Erstelle die vollständige Revision A der HomeMy **Power Management Unit (PMU)** als funktionsfähigen Engineering- und Messprototypen. Bleibe an der Aufgabe, bis alle unten genannten Repository-Artefakte vollständig erstellt, geprüft und committed sind. Nimm selbstständig alle reversiblen Repository-Änderungen vor; bestelle oder fertige keine reale Hardware.

## Verbindliche Quellen und Priorität

Lies zuerst `AGENTS.md` und `CURRENT_STATE.md`, danach vollständig und in dieser Reihenfolge:

1. `hardware/power-management-unit/requirements.yaml`
2. `hardware/power-management-unit/ASTRA_PCB_HANDOFF.md`
3. `hardware/power-management-unit/interfaces-and-layout.md`
4. `hardware/power-management-unit/verification-plan.md`
5. `docs/decisions/2026-09-10-battery-monitor-and-power-architecture.md`
6. `contracts/hardware/customer-power-on.md`
7. `contracts/ros/system-lifecycle.md`

Bei Widersprüchen gilt diese Reihenfolge. Nutze für Halbleiter, Steckverbinder und Schutzbauteile aktuelle Primärquellen der Hersteller und lege Datenblätter bzw. belastbare Quellen im Entwicklungsnachweis ab.

## Entscheidungsregel

Fehlende Messwerte, die erst mit einer gebauten PMU ermittelt werden können, dürfen den Schaltplan oder das Layout nicht stoppen.

- `LOCKED`: unverändert umsetzen.
- `PROVISIONAL`: einstellbar und messbar umsetzen.
- `REV_A_DESIGN`: exaktes Bauteil bzw. Schaltungsdetail selbst auswählen, berechnen und dokumentieren.
- `REV_A_ASSUMPTION`: konservative, konfigurierbare Prototypannahme treffen und in `REV_A_ASSUMPTIONS.md` festhalten.
- `REV_A_ENERGIZATION_GATE`: PCB vollständig erstellen; Bedingung sichtbar als Pflicht vor dem ersten Bestromen dokumentieren.
- `REV_B_VALIDATION`: nicht als Blocker behandeln; Messplan und Rückwirkung auf Revision B dokumentieren.

Stelle nur dann eine Rückfrage, wenn eine fehlende Information selbst eine konservative Revision-A-Lösung oder ein strombegrenztes, motorloses Bring-up unsicher bzw. technisch unmöglich macht. Triff sonst eine begründete Annahme und arbeite weiter.

## Erwartete Implementierung

Erzeuge unter `hardware/power-management-unit/` ein vollständiges KiCad-Projekt mit hierarchischem Schaltplan und gerouteter vierlagiger Revision-A-Platine. Wähle exakte, bestellbare Prototypbauteile und Footprints für LM74930-Q1-Hauptpfad, INA228, Haupt- und Motion-Shunts, TPS48110-Q1-Motion-Gate, beide TPS26631-Zweige, MOSFET-Bänke, analogen Bremschopper, ESP32-S3-Modul, Always-on-Wake/Self-Hold/Forced-off, CAN/ESD/Terminierung, LED-Ausgang, Temperaturmessung, Steckverbinder und Schutzbeschaltung.

Nutze für die vorläufig unbekannte Mechanik eine großzügige rechteckige Laborplatine mit vier Befestigungsbohrungen, gut erreichbaren Randsteckern, Antennen-Keep-out, Testpunkten, Rework-/DNP-Optionen und dokumentierten provisorischen Maßen. Lege Hochstrompfade nicht als gewöhnliche Leiterbahnen allein aus; berechne Kupferflächen, Via-Felder und Kupferstreifen/Busbar-Lösung. Motion muss hardwareseitig standardmäßig AUS sein.

## Abzuliefernde Dateien

Erstelle und committe mindestens:

- vollständige KiCad-Schaltplan- und PCB-Dateien;
- BOM mit Herstellerteilenummern, Ratings, Lifecycle und Alternativen kritischer Teile;
- `REQUIREMENTS_TRACEABILITY.md`;
- `REV_A_ASSUMPTIONS.md` mit Einstellwerten, Testpunkten und sicheren Erstwerten;
- `REV_B_VALIDATION.md` mit den später zu messenden Größen und den betroffenen Produktionsentscheidungen;
- nachvollziehbare FET-, Shunt-, eFuse-, Timer-, Toleranz-, Selektivitäts-, Chopper- und Thermikberechnungen;
- Stecker-/Pin-/Kabeltabelle und Power-button-Zeitablauf;
- ERC-/DRC-Berichte ohne ungeprüfte Ausnahmen;
- als Revision A bezeichnete Gerber-, Bohr-, Bestückungs-, BOM- und Assembly-Ausgaben;
- eine kurze Design-Review-Checkliste und Bring-up-Reihenfolge.

Setze in allen Metadaten `rev_a_engineering_prototype: true` und `rev_b_production: false`. Gib am Ende eine knappe Zusammenfassung der gewählten Bauteile, Berechnungen, Annahmen, Prüfergebnisse, verbleibenden Energization Gates und Revision-B-Messungen. Committe die Arbeit in logisch prüfbaren Commits auf einem eigenen Branch. Die reale Bestellung, Bestückung oder Inbetriebnahme bleibt beim Projektinhaber.
