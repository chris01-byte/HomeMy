# Astra-Auftrag: PMU Rev A.2 auf 300 × 280 mm fertigstellen

## Ziel

Erzeuge aus der kanonischen PMU-Referenz einen **vollständigen, gerouteten und prüfbaren KiCad-Arbeitsstand mit exakt 300 × 280 mm Platinenkontur**. Zielverzeichnis:

`hardware/power-management-unit/rev-a2-300x280/`

Das Ziel ist ein bestellbarer Engineering-Prototyp nach menschlicher Endkontrolle. Produktions- und Bestromungsfreigabe bleiben false.

## Verbindliche Ausgangsbasis

Lies zuerst vollständig:

1. `hardware/power-management-unit/README.md`
2. `hardware/power-management-unit/requirements.yaml`
3. `hardware/power-management-unit/ASTRA_PCB_HANDOFF.md`
4. `hardware/power-management-unit/interfaces-and-layout.md`
5. `hardware/power-management-unit/rev-a/README.md`
6. sämtliche Markdown-Dateien in `hardware/power-management-unit/rev-a/design/`
7. `hardware/power-management-unit/rev-a/manufacturing/PCB_STACKUP_PRESSFIT.md`
8. `hardware/power-management-unit/verification-plan.md`

Elektrische Quelle ist der hierarchische Rev-A-Schaltplan unter `rev-a/kicad/`. Die dortige Leiterplatte darf als geprüfte Referenz für Schaltung, Footprints und kritische Geometrien dienen, aber nicht durch simples Beschneiden auf 300 × 280 mm umgebaut werden.

Die entfernten 250/275/280/300×220-Versuche sind verworfen. Suche nicht nach ihnen, stelle sie nicht wieder her und übernimm keine Koordinaten oder Reparaturskripte daraus.

## Harte Randbedingungen

- Platinenkontur: exakt 300 × 280 mm.
- Alle Schaltplanbauteile, Footprints und elektrischen Netze müssen vollständig und paritätsgleich übernommen werden.
- Topologie, Werte, Bauteile, Footprints, Schutzfunktionen, Netznamen, Kelvinführung, Gate-Beschaltung, Busbar-, Press-fit- und Steckerschnittstellen bleiben unverändert, sofern keine belegte KiCad-Korrektur zwingend nötig ist.
- Vierlagiger Aufbau und die dokumentierten Hochstrom-/Fertigungsregeln bleiben verbindlich.
- Steckverbinder, Busbar-Kontakte, Montagebohrungen, Keep-outs, Antennenfreiraum, Testzugang und mechanische Randabstände müssen verwendbar bleiben.
- Batterie-, SYS-, Motion- und Arm-Leistungspfade benötigen die dokumentierten Netzklassen, Kupferflächen, Via-Felder und Engstellenprüfungen.
- Kelvin- und Gate-Leitungen werden als echte Mess-/Steuerpfade geführt, nicht über Lastkupfer.
- Kein DRC-Regelabbau, keine versteckten Ausnahmen und keine unbegründeten Warnungsunterdrückungen.
- Keine reale Bestromung und keine Aktorprüfung.

## Arbeitsreihenfolge

1. Lege einen neuen Arbeitsbranch auf Basis dieses bereinigten Branches an. Schreibe das neue CAD ausschließlich nach `rev-a2-300x280/`.
2. Erzeuge den neuen Board-Umriss, übertrage den vollständigen Schaltplan/Footprint-Satz und beweise die Parität, bevor Routing beginnt.
3. Platziere zuerst Anschlüsse, Montagebohrungen, Busbar-/Press-fit-Kontakte, Shunts, Haupt- und Motion-MOSFETs, Chopper-Leistungsteile und große Kondensatoren.
4. Lege anschließend Controller, Messung, Wake/AON, CAN, LED und Logik in klar getrennten Zonen an.
5. Route in dieser Priorität:
   - Batterie-, Haupt-, SYS-, Motion- und Arm-Leistungspfade;
   - Shunt-Kelvin-, Gate- und Chopper-Schleifen;
   - Versorgungs- und Massebezüge;
   - CAN, I2C, Fault-, Wake- und LED-Signale;
   - restliche Steuer- und Testsignale.
6. Fülle Kupferzonen neu, prüfe Rückstrompfade sowie jede Hochstrom-Engstelle und führe danach ERC, DRC und Paritätsprüfung nativ aus.
7. Erzeuge erst nach bestandenem CAD-Stand die Fertigungs-, Bestückungs- und Prüfunterlagen.

## Verbindliches Iterationsbudget

Eine Schleife bedeutet: eine zusammenhängende Änderung, anschließend Metriken und native Prüfung.

- maximal 2 Platzierungsschleifen;
- maximal 3 Hochstrom-/kritische Routing-Schleifen;
- maximal 5 Rest-Routing-/DRC-Reparaturschleifen;
- insgesamt maximal 10 Schreib-/Prüfschleifen;
- maximal ein externer oder digitaler Autorouter-Lauf, nur wenn dessen Ergebnis vor Import vollständig geprüft wird;
- keine rekursiven Hilfsagenten für Schreibarbeit.

Nach jeder Schleife protokollieren: offene Verbindungen, betroffene Netze, ERC-, DRC- und Paritätsbefund, geänderte Hochstromengstellen sowie Verbesserung gegenüber der vorherigen Schleife.

## Vorzeitiges Abbruchkriterium

Stoppe vor Ablauf des Budgets, wenn eine der Bedingungen eintritt:

- zwei aufeinanderfolgende Schleifen verbessern die Zahl der offenen Verbindungen/DRC-Befunde nicht;
- eine Reparatur verschlechtert einen kritischen Leistungs-, Kelvin-, Gate-, Sicherheits- oder Mechanikpfad;
- Fertigstellung erfordert eine Änderung an gesperrter Topologie, Bauteilwahl, Footprint oder Schutzfunktion;
- KiCad-Prüfungen laufen wiederholt nicht regulär zu Ende;
- ein notwendiger mechanischer Anschluss passt nach zwei vollständigen Platzierungsvarianten nicht.

Dann den besten elektrisch sicheren WIP-Stand sichern, keine weiteren automatischen Versuche starten und einen kurzen Blockerbericht mit konkreter Nutzerentscheidung erstellen.

## Fertigkriterien

„Fertig“ darf nur gemeldet werden, wenn alle folgenden Punkte belegt sind:

- exakt 300 × 280 mm Boardkontur;
- vollständige Schaltplan-/PCB-Parität;
- null offene Verbindungen;
- ERC regulär mit Exit-Code 0 und ohne ungeklärte Befunde;
- DRC regulär mit Exit-Code 0 und ohne ungeklärte Befunde;
- alle dokumentierten kritischen Leistungspfade durchgängig und regelkonform;
- überprüfte Kelvin-, Gate-, Rückstrom-, Chopper-, Antennen-, Montage- und Anschlussgeometrie;
- BOM, Positionsdaten, Gerber, Bohrdaten, Stackup-/Fertigungshinweise und Prüfreports konsistent zum finalen Commit;
- keine veralteten oder temporären Dateien im Ergebnisverzeichnis;
- `fabrication_release=false`, `assembly_release=false`, `energization_release=false`, `production_release=false`, bis der Nutzer separat freigibt.

## Abschluss

Committe und pushe nur den besten Endstand. Antworte anschließend mit:

- Branch und Commit-SHA;
- Platinenmaß;
- Anzahl Footprints und Netze;
- offene Verbindungen;
- ERC-/DRC-/Paritätsergebnis mit Exit-Codes und Reportpfaden;
- Liste der erzeugten Fertigungsdateien;
- verbleibende Annahmen und Energization Gates;
- klare Aussage „Engineering-Prototyp bestellbar nach menschlicher Prüfung“ oder „nicht bestellbar“;
- falls abgebrochen: verbrauchtes Schleifenbudget und exakt eine priorisierte Blockerliste.

Keine weitere Iteration nach Abschluss oder Abbruch.
