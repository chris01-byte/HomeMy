# Mechanischer Fertigungsstand PMU Rev A

**Prüfbarer Fertigungsvorschlag für einen Engineering-Prototyp; keine Fertigungs-, DRC- oder Strombelastbarkeitsfreigabe.** Die Geometrie wird aus `reports/board-pad-geometry.json` abgeleitet. Ihr SHA-256 steht in `busbar-pcb-interface.json`. Native PCB-Dateien wurden für diese Unterlagen nicht geändert. Nach der Integration sind Bohrdaten, Fräsdaten, Netzzuordnung und Bauraum erneut am tatsächlichen Board zu prüfen.

## Dateien und Bezugssystem

- `busbar-pcb-interface.json`: verbindliche Maßkoordinaten des Vorschlags, alle BC-Kontaktlands/Bohrungen, alle NT-Änderungen und Kupferkonturen.
- `BUSBAR_TOP_VIEW_1to1.svg`: 400×190 mm Blatt, Maßstab1:1, gemeinsamer Ausschnitt des oberen PCB-Bereichs. Ausdruck100%,100-mm-Kontrollstrecke messen. Keine Druckanpassung.
- `PCB_STACKUP_PRESSFIT.md`: Lagenaufbau, Fertigungsbohrungen, Einpresswerkzeuge und Prüfmerkmale.
- `CONNECTOR_ASSEMBLY.md`: Anschlussmontage und Kabel-/Bauraumgrenzen.
- `busbar-calculations.json`: nachvollziehbare Verlust- und adiabatische Rechenwerte; `build_mechanical.py` reproduziert JSON und SVG ohne PCB-Mutation.

Alle Koordinaten in mm, Draufsicht auf F.Cu: Ursprung linke obere Boardecke, x nach rechts, y nach unten. Auch die Unterseitenteile werden in diesem gemeinsamen Bezug **nicht gespiegelt** dargestellt. Der Fertiger leitet die Werkstückansicht aus den Koordinaten ab. Außenkontur360×300 mm; eine Spiegelung würde die asymmetrischen Ausschnitte vertauschen.

## Zusätzliche Kupferteile

Material Cu-ETP/CW004A, geforderter Liefernachweis der Leitfähigkeit; Rechnung verwendet 1.724×10⁻⁸ Ωm bei20°C. Dicke2.00±0.10 mm, Kontur±0.20 mm, Bohrposition±0.10 mm, DurchgangsbohrungØ3.40±0.10 mm. Schnittkanten vollständig entgraten, Kantenbruch0.2–0.4 mm; Kontaktflächen eben und gratfrei, keine Lackierung oder Klebung im Stromkontakt. Keine Lötzinnschicht als mechanisches Abstandsmaterial. Oxidfreie Kontaktflächen unmittelbar vor Montage reinigen; Oberflächenprozess und Alterungsverhalten sind am Muster zu verifizieren.

| Teil | Netz/Funktion | Kontur bzw. Begrenzung | Lokaler Mindestquerschnitt der Rechnung |
|---|---|---|---|
| BB1 | BATT_SENSED_P | x37..49,y14..86 |24 mm² |
| BB2 | MAIN_COMMON | x65..75,y14..86 |20 mm² |
| BB3 | SYS_BUS_P | x94..106,y14..74 |24 mm² |
| BB4 | MOTION_SENSED_P | x129..141,y19..79 |24 mm² |
| BB5 | MOTION_COMMON | x160..170,y19..79 |20 mm² |
| BB6 | MOTION_BUS_P | L-Teil; Kopf x188..278,y8..32; Schenkel x188..202,y32..87 |24 mm² an den12-mm-Ausschnitten unter J3/J5; Bohrungseinschnürungen gesondert |
| BB7 | BATT_N | x8..356,y105..136; Ausschnitte laut JSON |konservativ32 mm² im langen Hals; lokale Loch-/Ausschnittkombinationen gesondert |
| NB1..NB8 | jeweiliger Sternpunkt NT1..NT8 |20×10 mm, zweiØ3.4-Bohrungen,10 mm Achsabstand |20 mm² zwischen Lochzentren; am Loch nur13.2 mm² |

BB1..BB7 liegen auf der PCB-Unterseite. NB1..NB8 liegen oben, jeweils unmittelbar auf den beiden10×10-mm-Pads ihres Net-Ties. Die bestehende kurze Kupferbrücke im Net-Tie bleibt erhalten. Die Schienen überbrücken **keinen** Shunt, MOSFET-Schalter oder separaten Rückleiter. Ihre tatsächliche Unterseiten-Verbindung erfolgt ausschließlich an den aufgelisteten BC-Kontakten und NT*.2.

Unter J2/J3/J4/J5/J6 werden je12×12-mm-Freiräume gefräst. Die Pressfit-Pins ragen bei1.60-mm-Platine nominell1.9 mm nach unten; unter Berücksichtigung3.5±0.2 mm Pinlänge und1.60..1.70 mm PCB sind1.6..2.1 mm möglich. Die2-mm-Schiene darf diese Pins weder belasten noch als Kontaktfläche verwenden. Rechteckige Ausschnitte sind nötig: acht eng benachbarteØ2.4-Löcher ließen zwischen den Pinreihen fast keine belastbare Kupferbrücke übrig. Die CAD-Kontur hat rechtwinklige Sollgrenzen; Innenradien bis1 mm dürfen die12×12-Freigängigkeit der inneren geraden Flanken nicht unterschreiten.

BB7 besitzt zusätzliche12×12-mm-Ausschnitte um NT*.1. Dort liegen getrennte Kupfer-Unterlegscheiben Ø8/Ø3.4×1 mm für die jeweiligen Branch-Pads. Diese Scheiben, Muttern und Schrauben berühren BB7 nicht. Erst die obere NB-Brücke verbindet Branch-Pad1 mit BATT_N-Pad2. So bleibt der definierte Sternpunkt mechanisch erkennbar. Der Branch-Pad1-Ausschnitt und die benachbarte Pad2-Bohrung lassen lokal weniger Kupfer als die angenommene lange Halsbreite; diese lokalen Bereiche sind in der Messung einzeln zu erfassen.

## Kontaktlands, Isolation und Befestigung

BC1..BC15: neue einpoligeØ8.0-mm-Kupferlands mitØ3.20±0.10-mm-PTH, mindestens25 µm Hülsenkupfer, Vollanschluss auf den verbundenen Kupferlagen undØ8.2-mm-Lötstoppöffnung beidseitig. Kein Pastendruck und keine thermischen Speichen. Bei NT1..NT8 bleiben Padgröße10×10 mm und Netzzuordnung erhalten; beide Pads bekommenØ3.20±0.10-mm-PTH. Alle übrigen/inneren Fremdnetze halten die elektrische Mindestfreistellung ein. Bohrungen sind keine unplattierten mechanischen Löcher.

Unter den BB-Schienen liegen vier durchgängige Lagen KaptonHN, nominal zusammen0.20 mm. Festgelegtes Halbzeug: GoodfellowIM30-FM-000200, Bestellcode312-663-72,50 µm,500×500-mm-Blatt; Herstellerdickentoleranz±20%, deshalb Wareneingang des Vierlagenstapels aufhöchstens0.22 mm begrenzen. Ein Blatt liefert die konturgefrästen/geschnittenen Einzelteile, jede Lage ohne Stoß unter ihrer Schiene. Außerhalb der Kontaktfenster ist die Folie umlaufend mindestens1 mm größer als die Kupferkontur. Alle Fremdnetz-Vias und Leiterbahnen darunter bleiben isoliert. **Lötstopp allein ist keine zulässige Isolation.** In jedem Kontaktfenster liegt eine gestanzte Cu-ETP-Scheibe Ø8/Ø3.4×0.25±0.02 mm, mindestens0.01 mm höher als der zulässige Folienstapel. Diese23 Scheiben (15×BC,8×NT*.2) gleichen den Folienabstand aus; ohne sie wäre der Kontakt nicht definiert. IsolationsfensterØ8.5, Position±0.10 mm; keine Kleberreste zwischen Kupferflächen. [Goodfellow-Produktblatt](https://www.goodfellow-japan.jp/en/product/polyimide-film-IM30-FM-000200.htm).

Festgelegte Prototypklemmung je Schraube: AccuSSCF-M3-12-A2-P80, MutterHPN-M3-A2, unterseitiger FedersitzHDTW-M3-A4-BL(Ø9/Ø3.2×1±0.2 mm) und dreiSPIROL660001-Tellerfedern **gleichgerichtet ineinander**. Jede Feder istØ8/Ø3.2×0.3 mm, freieHöhe0.55 mm, Kegelhöhe0.25 mm; Herstellerkraft104 N bei0.1875 mm Federweg. Drei parallele Federn liefern rechnerisch312 N; freieStapelhöhe1.15 mm und nominell komprimierteStapelhöhe0.9625 mm. Reibung und Toleranzen sind am Coupon zu messen. Eine solche Tellerfeder ist keine gezahnte Schnorr-Sicherungsscheibe. [SPIROL660001](https://shop.spirol.com/item/disc-springs/disc-springs-to-din-en-16983/660001).

15BC-Schrauben erhalten zusätzlich oben eineHDTW-M3-A4-BL-Scheibe;16NT-Schraubenköpfe liegen unmittelbar auf den2-mm-NB-Kupferbrücken. Gesamtbedarf31Schrauben,31Muttern,46Scheiben,93Tellerfedern, zusätzlich Couponmaterial. Alle exakten Artikel und Primärquellen stehen in `MECHANICAL_CATALOG_BOM.json`; Lagerbestand und Lieferzeit sind nicht bestätigt. [Schraube](https://www.accu.co.uk/metric-cap-head-screws/659714-SSCF-M3-12-A2-P80), [Mutter](https://www.accu.co.uk/hexagon-nuts/7888-HPN-M3-A2), [Federsitz](https://www.accu.co.uk/metric-flat-washers/173323-HDTW-M3-A4-BL).

Zielklemmkraft200..400 N, vor PCB-Montage an einer gleich dicken Coupon-Anordnung einstellen. Maßgeblich ist die gemessene Federkompression/Kraft; das beschichtete Schraubgewinde trägt ein unbekanntes Reibmoment bei. T=KFd mit angenommenemK=0.20 ergibt lediglich0.12..0.24 Nm ohne diese Zusatzreibung, **kein** Montage-Drehmoment. Der Hersteller beschreibtPrecote80 als einmalige Schraubensicherung; nach Demontage Schrauben ersetzen und den spezifizierten Aushärteprozess des gelieferten Beschichtungsartikels einhalten. Unterlegscheiben-/WerkzeugfreiraumØ9 mm an BC ist im JSON reserviert. Keine gezahnte Scheibe aufPCB und keine Stromtragfähigkeitsannahme für Stahlschraube oder Gewinde.

M3×12 ist der feste Prototypartikel. KritischerNT*.2-Stapel: NB2.1+PCB1.7+Cu-Scheibe0.27+BB2.1+Federsitz1.2+komprimierteFedern0.9625+Mutter2.4=10.7325 mm; bei angenommenerSchrauben-Mindestlänge11.8 mm verbleiben1.0675 mm oder gut zwei0.5-mm-Gewindegänge. Tatsächliche Schraubenlänge und Feder-/Materialtoleranzen am Coupon nachmessen; keine zusätzliche Scheibe unterNT-Schraubenköpfe einsetzen. DieBC-Stapel sind kürzer. Einschließlich freiem Schraubenende bleibt die Unterseitenhüllhöhe nominell unter12 mm. Eine isolierende, unabhängig am Gehäuse abgestützte Trägerplatte nimmt Gewicht und Kabelkräfte auf; mindestens15 mm Abstand abPCB-Unterseite für Schienen, Verschraubungen und berührungssichere Abdeckung. Ein bloßes Aufhängen der Rückleiterschiene an vierPCB-Ecken ist nicht als Montage freigegeben. Freie Metallflächen durch eine verschraubte isolierende Abdeckung unzugänglich machen; Stützen/Kabelklemmen dürfen den ESP-Antennenfreiraum nicht überbauen.

Vor dem ersten Bestromen drei repräsentative, identisch aufgebaute Coupons prüfen: Kraft200..400 N beim definierten Federweg, Kontakt≤100 µΩ bei20°C, zehn Temperaturzyklen20→100→20°C, danach Kraft weiterhin im Zielbereich, Widerstandsdrift≤25%, keine Risse/bleibendePCB-Eindrückung oder durchschnittene Folie. Dieser festgelegte Prüfvorbehalt betrifft die Wirkung der konkret gewählten Montage; er verdeckt keine fehlende Befestigungsauswahl. Die Versuche wurden noch nicht durchgeführt.

Montagefolge: vollständiges SMT/THT-Löten und Reinigung; unbestromte Sicht-/Netzprüfung; Pressfit mit Gegenhalter; Kontrolle der Pins; Folie/Kupferscheiben; Unterseitenschienen und obere NB-Brücken; Klemmkraftprüfung; Kupplungs-/Kabelmontage mit separater Zugentlastung; Deckel. Kein Nachlöten der Kupferteile auf eine bereits bestückte und eingepresste Platine.

## Durchgängiger elektrischer Pfad und verbleibende Engstellen

J1 → zwei kurze äußere Kupferflächen → RSH1.Force1 → Shunt → RSH1.Force4 → Flächen/Vias/BB1 → Q1..Q3 Drain-Basis → MOSFET-Kanäle/Source-Anschlüsse → Flächen/Vias/BB2 → Q4..Q6 Source/Kanäle/Drain → BB3/Flächen → RSH2.Force1 → Shunt → RSH2.Force4 → BB4/Flächen → Q7/Q8 → BB5 → Q9/Q10 → BB6/Flächen → J3/J5. Rückstrom J4/J6 bleibt auf ARM_L_N/ARM_R_N bis NB1/NB2, danach BB7 → J2. Zusätzliche Zweige schließen ausschließlich am zugeordneten NB-Sternpunkt an.

Der Pfad enthält absichtlich Bauteil- und PCB-Abschnitte, die nicht durch einen massiven Streifen ersetzt werden können:

- RSH1/RSH2 Force-Pads sind2.55×5.6 mm. Ein mindestens5.6 mm breiter Kupferanschluss führt ausschließlich von der Force-Seite ab und weitet innerhalb3 mm auf mindestens12 mm auf. Sense-Pads bleiben eigene Kelvin-Abgänge; kein Bar-/Via-Sammelanschluss über den Sense-Strompfad. Längen für die beiden Force-Fächer anhand der endgültigen Kupferfüllung messen.
- Die Haupt-FETs haben fünf Source-Pads pro Die, zusammen6 mm nominelle Anschlussbreite in der Leiterplattenebene. Ihre kurzen Anschlüsse und der Gate-Pad-Freistich bleiben lokale Engstellen. Gleichmäßige Stromteilung zwischen drei Haupt- bzw. zwei Motion-FETs wird nicht durch gleiche Stückzahl bewiesen.
- Die einzelneØ8-mm-Klemmstelle muss Strom aus der B.Cu-Fläche sammeln. Die umliegenden Vias und die Lochhülse reduzieren den Widerstand; der massive Bar-Querschnitt beseitigt den lokalen Ausbreitungswiderstand der Kupferfolie nicht. Jeder Anschluss ist deshalb separat per Vierleitermessung und Temperaturbild zu beurteilen.
- Die bisherigen Viasummen156/154/229/180/157/245 für BB1..BB6 gelten vor den neuen Bohrungen. Für eine Rechnung mit160 gleich belastetenØ0.4-mm-Vias müssen160 tatsächlich elektrisch angeschlossene Vias je betrachteter vollständiger Transferstelle nachgewiesen werden. Über die ganze Platine verteilte Vias lassen sich nicht einer lokalen Kontaktstelle gutschreiben. Individuelle Arrays, Lagewechsel und reale Stromverteilung fehlen noch im Qualifikationsnachweis.

Ein Strom darf nur für den **schwächsten** Abschnitt freigegeben werden. Diese Unterlagen geben deshalb weder50 A noch60 A Dauerstrom und auch keinen150-A-Impuls der gesamten Platine frei.

## Rechenbasis und messbare Abnahmekriterien

Rechenwerte in `busbar-calculations.json`: ρ100°C=2.2660256×10⁻⁸ Ωm, gleichförmiger Querschnitt; Kupferdichte8.96 g/cm³ und Wärmekapazität0.385 J/(gK) als technische Näherungen. Bei Lochstellen ist die freie Breite w−3.4 mm anzusetzen, neben mehreren Ausschnitten die tatsächlich verbleibende Summe der Stege. Diese lokalen Korrekturen ersetzen nicht die Feld-/Kontaktanalyse.

Beispiel BB2:72×10×2 mm ergibt81.58 µΩ und0.204 W bei50 A bzw.0.294 W bei60 A. BB7, mit konservativ über die ganze348-mm-Länge nur16×2 mm gerechnet:246.43 µΩ,0.616 W bei50 A bzw.0.887 W bei60 A. Ein6-mm-langer5.6-mm-breiter Hals aus zwei ideal parallel betriebenen70-µm-Außenlagen:173.42 µΩ,0.434 W bei50 A. **Eine** Außenlage verdoppelt diesen Halswiderstand. Eine einzelneØ3.2-mm-Lochhülse mit25 µm Cu und1.7 mm Länge hat ungefähr153.3 µΩ ohne Pad-Ausbreitungswiderstand. Ein20-mm-langer,20-mm-breiter ARM_R_N/ARM_L_N-Rückleiter aus zweimal70 µmCu ergibt161.86 µΩ bzw.0.101 W bei25 A (eineLage0.202 W); der Weg vonJ4/J6 zum zugehörigenNB-Brückeneingang muss diese Breite außer dem gesondert geprüften Padfächer halten. Diese Werte zeigen, weshalb gute massive Schienen allein nicht genügen.

Ziel für die fertig montierte einzelne Klemmverbindung: höchstens100 µΩ bei20°C in Vierleiteranordnung, Messpunkte unmittelbar an Schiene und zugehöriger PCB-Fläche, Leitungs-/Flächenanteil dokumentieren. Das entspricht0.25 W bei50 A pro vollständigem Kontakt. Nach den festgelegten thermischen Zyklen und Ent-/Montageversuchen Änderung≤25%; messbarer Drift erfordert geänderte Klemmung, keine rechnerische Schönung. Diese Ziele sind bislang nicht gemessen.

Eine50-A-Gesamtverlustzahl wird nicht angegeben, solange gemeinsame Stromwege, FET-Aufteilung, Kontaktwiderstände und tatsächliche Kupferbreiten nicht feststehen. Für einen späteren überwachten, motorlosen Stromtest schrittweise steigern und stationäre Temperatur erfassen; technische ZielgrenzePCB≤100°C und lokale Erhöhung≤30 K, zusätzlich niedrigere Grenzwerte aller betroffenen Teile einhalten. Daraus lässt sich später Rθ=(Thot−Tamb)/P bestimmen. Ein ideal adiabatischer Kurzpuls-Rechenwert belegt weder Wärmestau bei Wiederholung noch Kontaktdruckstabilität oder die zulässige FET-SOA.

## Konkret erforderliche PCB-Korrekturen

1. BC1..BC15 und modifizierte NT1..NT8 als elektrisch korrekte Bauteile in Schaltplan/PCB übernehmen; neue Bohrungen nicht nachträglich durch Netzflächen bohren.
2. Kupfer- und Via-Verbindungen zu jedem BC-Land nachführen; Thermal-Reliefs aus; Via-Zahlen und lokale Engstellen nach neuer Kupferfüllung neu bestimmen. BC15(27,110) benötigt einen breiten direkten BATT_N-Anschluss zu J2.
3. Die alte CHOPPER_N-Zone x300..313,y35..51 verfehlt Q40.Source auf der Westseite. Source-F.Cu-Landbereich x294.5..299.5,y31.7..46 einschließlich Anschluss zu NT10(299,44) vorsehen, Gate-Freistellung erhalten. C312.N(299,17) und C313.N(316,17) getrennt2–3 mm breit nachy23 herausführen und dort8 mm breit auf B.Cu verbinden. Eine direkte Querleitung aufy17 würde C312.P(304,17) kreuzen. Source-Rückweg8 mm aufB.Cu über(298,44),(303,53),(342,53),(342,114) nachNT7.1(340,122) als zu prüfende Route. Prioritäten gegenüber MOTION_BUS beachten.
4. LED-Leistungsmasse J18.3 und C246.N auf LOGIC_5V_N, breit nachJ11.2/NT8; LOGIC_GND/NT9 führt keinen LED-Laststrom. Source-JSON ist entsprechend korrigiert; finale CAD-Netze kontrollieren.
5. Rechteckiger9×9-mm-Terminalkörper beschreibt keine Ringkabelschuh-/Schraubendreherhülle. Horizontale M5-Zugänge, Ausrichtung, Kabelradius, Gegenhalter und Nachbarteile separat mechanisch prüfen. H3 darf nicht im ESP-Antennenfreiraum liegen; aktuelle Zielposition(292,292).
6. Pressfit-Fertigungsdicke1.60..1.70 mm statt einer handelsüblichen1.6-mm-Spezifikation mitnegativer Toleranz; genaues Laminat/Tg und Einpressprozess festlegen.

Die Pad-Näherungsprüfung des Generators verwendet konservative Umkreise der tatsächlichen Pads undØ9-mm-Schraubhüllen. Null Treffer bedeutet ausschließlich keine solche Padnähe unter0.5 mm; sie ersetzt weder Bauteilkörper-, Werkzeug-, Netz-Durchgangs-, Enclosure- noch KiCad-DRC-Prüfung.
