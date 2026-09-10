# Rev A-P1 Hochstromregeln und Engstellen

Engineering prototype – not production qualified.

Die Regeln sichern die überprüfte Prototypgeometrie. Sie erklären die Platine
nicht zu einer thermisch qualifizierten 50-A-Baugruppe. Für den Betriebsstrom
gelten weiterhin die gestuften Messungen im Bring-up-Plan.

| Netzklasse | Exakte Netze | Neue Leistungsleiterbahnen mindestens | Via-Pad / Fertigloch mindestens |
|---|---|---:|---:|
| PWR_BATTERY | BATT_FUSED_P, BATT_SENSED_P, MAIN_COMMON, BATT_N | 4 mm | 0,8 / 0,4 mm |
| PWR_SYS | SYS_BUS_P | 4 mm | 0,8 / 0,4 mm |
| PWR_MOTION | MOTION_SENSED_P, MOTION_COMMON, MOTION_BUS_P | 4 mm | 0,8 / 0,4 mm |
| PWR_ARM | ARM_L_N, ARM_R_N | 6 mm | 0,8 / 0,4 mm |

Der bevorzugte Routingwert ist 6 mm. Die Mindestwerte werden zusätzlich in
`.kicad_dru` erzwungen; Netzklassen allein wären lediglich Routingvorgaben.
Grundlage ist die [KiCad-10-Regeldokumentation](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html#custom_design_rules).

Die 25 Leistungsflächen haben nun 1,2 mm Mindestfüllbreite. Die zusätzliche
DRC-Verbindungsprüfung auf den Außenlagen hat 1,0 mm als Schwelle gegen schmale
Kupferreste. **1,0 mm ist keine zulässige Breite für einen vollständigen
50-A-Strompfad.** Eine pauschale 4-mm-Flächenregel bewertet auch einzelne Stege
zwischen Via-Bohrungen und Abzweige als alleinige Lastpfade. Die tatsächlichen
Lastpfade werden deshalb zusätzlich anhand der gespeicherten Füllpolygone,
aller Leistungspads, lokaler Querschnitte und der zwingenden Busbars beurteilt.
Die Innenlagen werden nicht pauschal dem Hauptstrom zugerechnet.

Die strengere Füllung deckte zwei Trennstellen im BATT_N-Rückleiter unter den
Arm-Sternpunkten auf. Dessen untere Kante wurde von Y=133 auf Y=137 mm erweitert
und nativ neu gefüllt. Der Rückleiter ist nun wieder zusammenhängend; die
getrennten Arm-Netze und ihre Sternbrücken bleiben erhalten.

## Steuerabzweige und Kelvin-Leitungen

492 vorhandene Kupferelemente sind in drei benannten, eingefrorenen PCB-Gruppen
erfasst: 480 Steuer-/Referenzabzweige, sechs SYS-eFuse-Zuleitungsstücke und sechs
kurze eFuse-Padfächer. Ihre Mindestbreiten betragen 0,20 / 0,80 / 0,25 mm.
Steuer-Vias behalten 0,60/0,30 mm. Die SYS-Abgänge versorgen die 3-A-/2-A-Zweige,
niemals den gesamten Batterie-/Motion-Strom.

`high-current-tap-capture.json` hält Mitgliedschaft und Geometrie jedes Elements
fest. `audit_high_current.py` lehnt Änderungen und neu hinzugefügte dünne
Leistungsleiter ab. Die Ausnahme ist weder ein Breitenfilter noch eine pauschale
Ausnahme für ein ganzes Netz. Engstellen an den einzeln benannten Widerstands-
und C6-Anschlüssen sind auf deren Bias-/Referenzpads beschränkt.

MAIN_KELVIN_P/N, MOTION_KELVIN_P/N, Filter-, Mess- und Gate-Netze erhalten keine
Hochstrom-Netzklasse. Die 46 kritischen Signalpfade und 125 geschützten
Analogelements werden separat geprüft. Für die Leistungsanalyse werden alle
492 ausgenommenen Kupferelemente entfernt: **247 von 247 geprüften Verbindungen
bleiben bestehen**, einschließlich aller Shunt-Force-Pads, Q1–Q10-Leistungspads,
J1–J6-Anschlusspins und BC-Kontakte. Die Geometrie aller Tap-Elemente bleibt
unverändert. Ein Negativversuch in einer Projektkopie weist nach, dass eine
neue 0,2-mm-Motion-Leiterbahn und ein 0,6/0,3-mm-Leistungsvia gemeldet werden.
Der Prozessstatus dieses separaten Sandbox-Versuchs wird ausdrücklich getrennt
von den regulär bestandenen ERC-/DRC-Abschlussläufen dokumentiert.

## Verbleibende konstruktive Engstellen

| Stelle | Geometrie / Funktion | Verbindliche Behandlung |
|---|---|---|
| J1–J6 | Je acht Press-fit-Pins; Ø2,10-mm-Lands, Ø1,475-mm-Fertigloch | Beide Außenlagen angeschlossen; solid, keine Thermalspokes. Loch-/Kupfer-/Einpressprozess nach eigener Tabelle; kein einzelner Pin als Gesamtstrompfad. |
| RSH1/RSH2 | Force-Lands 2,55 × 5,6 mm, nur F.Cu direkt am SMD-Bauteil | Vier Force-Fächer separat vermessen; Strom breitet sich vor B.Cu-Transfer aus. Pads 2/3 bleiben Kelvin. Kein Busbar-Bypass des Shunts. |
| Q1–Q10 | Fünf einzelne Source-Leads, Drain-Pads 7–12 plus Metallbasis 13 | Jeder Leistungsanschluss geometrisch geprüft; unvermeidbare einzelne Lead-Hälse. Stromteilung und lokale Erwärmung am Muster prüfen, keine Gesamtstrom-Anrechnung für einen einzelnen Lead. |
| BC1–BC15 | Ø8-mm-Kontaktland um Ø3,2-mm-PTH | Lokale Stromaufweitung und Kontaktwiderstand bleiben trotz 2-mm-Busbar. Kontaktziel ≤100 µΩ bei 20 °C und Drift ≤25 % am Coupon prüfen. |
| Via-Felder | Ø0,8/0,4 mm; 25 µm Mindesthülsenkupfer | Stege zwischen vielen Bohrungen sind Parallelpfade. Feldzahlen ersetzen keine lokale Stromteilungs-/Temperaturmessung. Alle aktuellen Zahlen stehen im Geometriebericht. |
| BATT_N unter SYS-Abgang | F.Cu wird dort durch den SYS-Abgang unterbrochen | B.Cu und BB7 übernehmen den durchgehenden Rückweg. Neue untere Kupferverbindung unter NT1/NT2 erhalten. |
| Arme / NT1–NT2 | Separate Rückleiter, lokale 12,5-mm-Querschnittsfenster; NT-Lochränder und NB1/NB2 | Beide Außenlagen und die definierten Kupferbrücken verwenden; 25-A-Armplanung bleibt messpflichtig. |
| NT3–NT8 | Eigene Zweiglands vor der gemeinsamen BATT_N-Seite | NB-Brücken und getrennte Unterlegscheiben montieren; keine unbeabsichtigte Überbrückung durch BB7. |
| Q40 / J12 | Source-Transfer über zehn lokale Ø0,4-mm-Vias, 8-mm-B.Cu-Rückweg, 3-mm-Drainhals am Stecker | Etwa 9,3-A-Anfangsstrom der Bremsbank separat prüfen; Pulsenergie, VDS-Spitzen und Stromteilung messen. |
| Drive / Lift | 8-mm-Rückwege; Lift-Ansätze 3 mm auf zwei Innenlagen | Beide geprüften Lift-Verbindungen erhalten; keine pauschale Hauptstromfreigabe der Innenlagen. |
| U3/U4 / J11 | Kurze 0,25-mm-IC-Padfächer; 0,8/1,25-mm-Zuleitungsstücke; 2-mm-J11-Hals | Nur jeweiliger eFuse-/5-V-Zweigstrom. Die schmalen Anschlüsse sind explizite Ausnahmen, keine Vorlage für Hauptstromrouting. |

Die vollständigen 85 Querschnittsmessungen mit Koordinaten, getrennten
Kupferintervallen und Lagen stehen in `evidence/high-current-audit.json` und im
Bestellpaket als `POWER_CROSS_SECTIONS.csv`. Fensterbreiten sind lokale
Messungen, keine globale Minimum-Cut- oder Stromdichtesimulation. Jeder
Routing-/Flächenwechsel macht den Paket-Hash ungültig und verlangt eine neue
Engstellenprüfung, neue native Prüfungen und eine neue Paketversion.
