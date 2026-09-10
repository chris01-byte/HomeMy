# Bestückungsorientierung der Leistungsbauteile

Diese Unterlage legt die Orientierung für den Rev-A-Prototyp fest. Alle Ansichten sind **von der Bauteilseite**, +X nach rechts und +Y nach unten. Koordinaten sind absolute PCB-Koordinaten in mm. Die Winkel stammen aus der nativen KiCad-Platine; −90° entspricht 270°. Eine Bestückmaschine benötigt zusätzlich die zum konkreten Bauteil und Zuführer passende Nullwinkeldefinition. Die Tabellen sind kein ungeprüfter Maschinenimport.

`assembly-orientation.json` enthält den geprüften PCB-SHA-256, jede Padposition und die vorhandenen Fab-/Silk-Grafiken. [Die vergrößerte Padansicht](ASSEMBLY_ORIENTATION.svg) und [PNG-Vorschau](ASSEMBLY_ORIENTATION.png) ergänzen die Angaben. Die gezeichneten Padumrisse sind vereinfacht; für die Lötflächen gelten ausschließlich die nativen Footprints.

## Q1–Q10: Nexperia PSMN1R0-100ASFJ

Herstellerzuordnung: Pin 1 = Gate, Pins 2–6 = Source, Pins 7–12 = Drain; die Metallbasis `mb` ist ebenfalls Drain. Das Projekt bezeichnet diese Basis mit **Pad 13**. Sie ist keine elektrisch getrennte Kühlfläche. Quellen: [archiviertes Datenblatt](https://github.com/chris01-byte/HomeMy/blob/26c7b057e5b61e150468c9402286b78b4c66bd4c/hardware/power-management-unit/rev-a/evidence/power/psmn1r0-100asf.pdf), Seite 2 und [Gehäusezeichnung Seite 10](https://github.com/chris01-byte/HomeMy/blob/26c7b057e5b61e150468c9402286b78b4c66bd4c/hardware/power-management-unit/rev-a/evidence/power/psmn1r0-100asf-10.png); [Herstellerquelle](https://assets.nexperia.com/documents/data-sheet/PSMN1R0-100ASF.pdf).

In der Hersteller-Draufsicht kennzeichnet der kleine, ausdrücklich als „pin 1 index & Gate ID“ bezeichnete Index die Gate-Ecke. Größere kreisförmige Formmarken sind nicht als Gate-Index zu verwenden. Ober- und Unteransicht der Zeichnung sind gespiegelt: Die Unteransicht darf nicht unverändert als Bestückansicht benutzt werden.

| Ref | Bauteilzentrum X, Y | KiCad-Winkel | Gate-Pad 1 X, Y | Source-/Drain-Seite in Draufsicht |
|---|---|---:|---|---|
| Q1 | 55, 25 | 90° | 60.65, 30 | Source rechts, Drain links; Gate unten rechts |
| Q2 | 55, 50 | 90° | 60.65, 55 | Source rechts, Drain links; Gate unten rechts |
| Q3 | 55, 75 | 90° | 60.65, 80 | Source rechts, Drain links; Gate unten rechts |
| Q4 | 85, 25 | −90° | 79.35, 20 | Source links, Drain rechts; Gate oben links |
| Q5 | 85, 50 | −90° | 79.35, 45 | Source links, Drain rechts; Gate oben links |
| Q6 | 85, 75 | −90° | 79.35, 70 | Source links, Drain rechts; Gate oben links |
| Q7 | 150, 30 | 90° | 155.65, 35 | Source rechts, Drain links; Gate unten rechts |
| Q8 | 150, 65 | 90° | 155.65, 70 | Source rechts, Drain links; Gate unten rechts |
| Q9 | 180, 30 | −90° | 174.35, 25 | Source links, Drain rechts; Gate oben links |
| Q10 | 180, 65 | −90° | 174.35, 60 | Source links, Drain rechts; Gate oben links |

Damit zeigen die Source-Seiten jedes gegensinnig geschalteten MOSFET-Paares zueinander. Eine Drehung um 180° würde Gate und Drain-Basis auf falsche Netze setzen. Vor dem ersten Reflow das reale Gehäusemerkmal und Pad 1 unter Vergrößerung fotografisch abgleichen. Die abschließende native Prüfung bestätigt bei Q1–Q10 den expliziten Fab-Gate-Index, die Source-/Drain-Texte und die Körperkontur von 12 × 9.4 mm. Damit ist das frühere 12 × 13.2 mm Fab-Landfeld ersetzt; es war keine Gehäusekörperkontur.

## Q40, Shunts und U1

| Ref / Artikel | Zentrum / Winkel | Verbindliche Montagezuordnung |
|---|---|---|
| Q40 / IPT015N10N5ATMA1 | (302, 35), 0° | Logisches Gate-Pad 1 bei (296.75, 30.8), links oben. Source-Pad 2 links, Drain-Pad 3 rechts. Das importierte HSOF-Footprint hat bereits ein Silk-Dreieck und eine abgeschrägte Fab-Ecke am Gate. |
| RSH1 / CSS4J-4026R-L500F | (30, 45), 0° | Große Force-Pads 1/4 bei X = 25.975/34.025 und Y = 45.85. Kleine Sense-Pads 2/3 bei denselben X-Koordinaten und Y = 41.75, also nach Norden. |
| RSH2 / CSS4J-4026R-L500F | (120, 45), 0° | Große Force-Pads 1/4 bei X = 115.975/124.025 und Y = 45.85. Kleine Sense-Pads 2/3 bei Y = 41.75, also ebenfalls nach Norden. |
| U1 / LM74930QRGERQ1 | (65, 98), 0° | Pin 1 / DGATE bei (63.1, 96.75), oben links. Die linke Padreihe zählt 1–6 nach unten; die untere Reihe 7–12 nach rechts. Zentrum Pad 25 bei (65, 98) bleibt elektrisch **FLOAT**. |

Q40 verwendet die logische KiCad-Gruppierung 1 = Gate, 2 = alle Source-Anschlüsse, 3 = Drain-Tab. Das [offizielle Infineon-Datenblatt](https://www.infineon.com/assets/row/public/documents/24/49/infineon-ipt015n10n5-datasheet-en.pdf), Revision 2.4 vom 2023-05-04, bestätigt auf Seite 1 unabhängig davon die physischen Pins 1 = Gate, 2–8 = Source und den Drain-Tab. Die Herstelleranschlüsse 2–8 sind deshalb nicht mit logischen Padnummern 2–8 eines anderen Footprints gleichzusetzen. Der [archivierte Primärquellen-Auszug](https://github.com/chris01-byte/HomeMy/blob/26c7b057e5b61e150468c9402286b78b4c66bd4c/hardware/power-management-unit/rev-a/evidence/chopper/ipt015n10n5-primary-source.json) enthält URL, Revisionsstand, Pin- und Parameterdaten; sein Hash steht im Quellenmanifest. Der ursprüngliche lokale PDF-Download scheiterte an TLS, der spätere Web-Reader-Zugriff auf Hersteller-PDF und Produktseite war erfolgreich. Es werden keine lokal vorhandenen Original-PDF-Bytes behauptet. Das tatsächliche Padbild stammt aus `Package_TO_SOT_SMD.pretty/Infineon_PG-HSOF-8-1.kicad_mod` und wurde mit dieser Herstellerzuordnung verglichen.

Bei den Shunts müssen die schmalen realen Sense-Zungen auf den kleinen nördlichen Pads liegen. Die mechanisch ungleichen Force-/Sense-Anschlüsse legen die Orientierung fest; eine Drehung um 180° ist unzulässig. Die vier Projektnummern dokumentieren die Force-/Sense-Zuordnung. Aufdruck-Leserichtung allein ist kein Montagebezug. [Bourns-Zeichnung und empfohlenes Landbild](https://github.com/chris01-byte/HomeMy/blob/26c7b057e5b61e150468c9402286b78b4c66bd4c/hardware/power-management-unit/rev-a/evidence/power/css4j-4026-2.png), [Herstellerdatenblatt](https://www.bourns.com/docs/product-datasheets/css4j-4026.pdf).

U1 ist besonders zu prüfen: Sein freies Mittelpad darf weder mit BATT_N noch mit einer Massefläche oder Thermal-Vias verbunden werden. Die native Netzbezeichnung `unconnected-(U1-EP_FLOAT-Pad25)` kennzeichnet einen isolierten Anschluss, keine zu routende Versorgung. Das Mittelpad bleibt als vorgesehene Lötfläche bestehen; „FLOAT“ bedeutet elektrisch frei, nicht automatisch ohne Lötpaste. Grundlage: [TI LM74930-Q1, Seiten 3–4 und Package-Anhang](https://github.com/chris01-byte/HomeMy/blob/26c7b057e5b61e150468c9402286b78b4c66bd4c/hardware/power-management-unit/rev-a/evidence/power/lm74930-q1.pdf), [Herstellerquelle](https://www.ti.com/lit/ds/symlink/lm74930-q1.pdf). Vor dem ersten Einschalten isoliertes EP-Land und fehlende Thermal-Vias gegen Fertigungsdaten und Röntgen-/AOI-Prüfplan kontrollieren.

## J1–J6: Richtung der rechtwinkligen M5-Anschlussfläche

Die Schraubachse verläuft horizontal. Das aktuelle Lochbild hat zwei X-Spalten und vier Y-Reihen. Gemäß [Würth-Ansichten](https://github.com/chris01-byte/HomeMy/blob/26c7b057e5b61e150468c9402286b78b4c66bd4c/hardware/power-management-unit/rev-a/evidence/chopper/redcube-drill.png) liegen zulässige Front-/Rückorientierungen damit entlang ±Y. Alle acht Pins eines Terminals führen dasselbe Netz; eine mechanische Drehung um 180° passt in dasselbe Lochmuster. Eine Drehung um 90° wäre ein anderes Lochmuster und darf nicht aus der Lage am linken Platinenrand abgeleitet werden.

| Ref | PCB-Zentrum / gespeicherter Winkel | Anschlussfläche und Werkzeugzugang |
|---|---|---|
| J1 | (15, 45), 0° | nach Norden, −Y |
| J2 | (15, 115), 0° | nach Norden, −Y |
| J3 | (220, 20), 0° | nach Norden, −Y, über die obere Boardkante |
| J4 | (220, 115), 0° | nach Süden, +Y |
| J5 | (250, 20), 0° | nach Norden, −Y, über die obere Boardkante |
| J6 | (250, 115), 0° | nach Süden, +Y |

Diese Zuordnung ist eine ausdrückliche **manuelle Montageanweisung**. Der gespeicherte Winkel 0° des symmetrischen Footprints kodiert die Anschlussfläche nicht. Die nun vorhandenen Fab-Achspfeile und Ref-spezifischen Richtungstexte ergänzen sie ohne Änderung der Pads; alle sechs Richtungstexte wurden auf dem finalen nativen Board geprüft. Mindestens 25 mm freien axialen Schraub-/Werkzeugzugang als Planungsraum reservieren; die reale Werkzeug-, Ringkabelschuh- und Kabelbiegehülle am Muster prüfen. Herstellerzeichnung: [7461103, Revision 001.005, Seite 1](https://github.com/chris01-byte/HomeMy/blob/26c7b057e5b61e150468c9402286b78b4c66bd4c/hardware/power-management-unit/rev-a/evidence/chopper/7461103.pdf); Einpressprozess und Gegenhalten gemäß [CONNECTOR_ASSEMBLY.md](CONNECTOR_ASSEMBLY.md).

## Grafische Prüfung und erster Artikel

Der native Stand beim ersten Audit war ohne Padnummerneinblendung für CCPAK, U1 und M5 nicht ausreichend eindeutig. `annotate_assembly.py` hat die gemeldeten nichtleitenden Merkmale ergänzt. Die abschließende read-only Prüfung des PCB-SHA-256 `70bb8eb588f2fc7200f718df0e11659aad3c40c7e9d5652228eb7a58d232065f` bestätigt alle 20 bauteilbezogenen Grafikprüfungen: Gate-/Pin-1-Index, korrekte CCPAK-Fab-Körperkontur, U1-FLOAT-/NO-VIA-Texte, Shunt-Sense-Seite, Q40-Gate-Markierung und alle M5-Anschlussrichtungen. `assembly-orientation.json` enthält die aktuellen Grafiken und einzelnen Ergebnisse; die Padansichten wurden daraus neu erzeugt. Die Platine blieb während der Prüfung unverändert.

Für den ersten Artikel sind Bestückungsfotos mit sichtbaren Bauteilindizes, Abgleich mit dem Padnummernplan, Anschlussrichtung jedes M5-Terminals sowie der dokumentierte freie Zustand von U1.25 festzuhalten. Diese Evidenz wird mit dem freigegebenen Bestückungsdatensatz versioniert. Es wurde hier weder eine Platine bestückt noch ein Montageprozess qualifiziert.
