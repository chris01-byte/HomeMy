# Lagenaufbau und Pressfit-Prozess

Status: verbindlicher **Anforderungsentwurf** für den Leiterplattenfertiger und den Prototyp-Montagebetrieb. Schichtdicken, Laminatartikel, Mikroschliff und Einpresskraftkurve sind noch nicht an einem Fertigungslos bestätigt. Quellen: lokal archiviertes `../evidence/chopper/7461103.pdf`, Revision001.005 vom2025-09-11, Seiten1 und3; Ursprungs-URL und SHA-256 in `../evidence/chopper/source_manifest.json`. Diese Herstellerquelle enthält die hier zusammengefassten spezifischen Bohr- und Prozesswerte.

## Leiterplatte

Außenkontur360.00×300.00 mm, Fertigungsziel mechanische Gesamtdicke zwischen den äußeren Kupferoberflächen **1.60 +0.10/−0.00 mm**, ohne aufgedruckte Lötstoppdicke. 1.6 mm±10% ist wegen des Hersteller-Mindestwertes1.6 mm für7461103 unzulässig. Der Fertiger darf seine interne Sollmitte1.65 mm wählen, muss die obere/untere Grenze über das ganze Los einhalten. Für Hülsen-Widerstände wird konservativ1.70 mm Länge gerechnet.

| Reihenfolge oben nach unten | Fertigungsanforderung | Funktion |
|---|---|---|
| F.Mask | Lötstopp nach gewähltem Fertigungsprozess, ausgesparte BC-/NT-Kontaktlands | kein alleiniger Bar-Isolationsnachweis |
| F.Cu | mindestens70 µm **fertig**, nominell2oz | Hauptstrom, Bauteile, kurze Gate-/Kelvinanschlüsse |
| Dielektrikum1 | nominal0.15 mm | vom Fertiger mit Harz-/Kupferverteilung abgleichen |
| In1.Cu | mindestens35 µm fertig, nominell1oz | lokale LOGIC_GND/CHOP_GND-Referenzen, keine pauschale Hauptstromanrechnung |
| Kern | nominal1.09 mm beim rechnerischen1.60-mm-Aufbau | genaue Pressdicke vom Fertiger bestimmen |
| In2.Cu | mindestens35 µm fertig, nominell1oz | Signale, getrennte Hilfsnetze; kein unkontrollierter Ersatz-Rückweg |
| Dielektrikum2 | nominal0.15 mm | möglichst symmetrisch zuDielektrikum1 |
| B.Cu | mindestens70 µm fertig, nominell2oz | parallele Hauptstromflächen und definierte Bar-Kontakte |
| B.Mask + zusätzliche Folie | Maskenprozess plus separate0.20-mm-Folie unter Bars | Folie und Cu-Kontaktscheiben lautMECHANICAL_BUILD.md |

Die Zahlen70+150+35+1090+35+150+70=1600 µm sind ein überprüfbarer Nennaufbau, keine Behauptung verfügbare Standard-Prepregs ergäben exakt diese Dicke. Der Fertiger liefert seine konkreten Glasgewebe/Harz-/Kernartikel, gepressten Sollwerte und Toleranzen vor Datensatzfreigabe. Alle Kupferdicken sind **fertige Mindestdicken**, keine bloßen Startfolienangaben. Kupferbalance und Verzug mit allen schweren Flächen prüfen. Ein Innenlagen-Referenzplan, der den Sternpunkt überbrückt, ist elektrisch nicht zulässig.

Baseline-Laminat ist FR-4 mitTg innerhalb125..135°C, weil Würth dort das Einpressverhalten qualifiziert hat. Ein höheresTg, etwa170°C, ist eine alternative Materialausführung und verlangt laut Hersteller eine kundenseitige Vorbewertung; keine stillschweigende Substitution. Konkretes Laminat, CTI, Tg/Td-Prüfverfahren, Feuchte-/Lötprofil und Rohmaterialhersteller sind vom Fertiger zu benennen. Eine bloße Bezeichnung„FR4“ genügt nicht zur Prozessfreigabe. Die Strom-/Temperaturziele bleiben unter den später bestätigten Material- und Bauteilgrenzen.

## Drei getrennte Bohrklassen

| Bohrklasse | Fertigmaß | Rohbohr-/Plattieranforderung | Zweck |
|---|---|---|---|
| PF:48 Pressfit-Löcher J1..J6 | Ø1.475±0.050 mm bei chemischer Oberfläche | RohbohrungØ1.600 +0.000/−0.030 mm;25..60 µm Kupfer in der Hülse; chemischer Oberflächenprozess | ausschließlich Würth7461103 |
| BC/NT:31 Verschraubungs-PTH | Ø3.20±0.10 mm | Rohbohrer nach Fertigerkompensation; mindestens25 µm Hülsenkupfer |15 BC plus2×8 NT; keine Pressfit-Anforderung |
| V:Transfer-/Thermalvias | Ø0.40 mm fertig, im HochstromfeldØ0.80-mm-Pad | mindestens25 µm Hülsenkupfer; Fertiger bestätigt Toleranz und Aspektverhältnis | Strom-/Wärmetransfer; Anzahl lokal nachweisen |

PF-Pad-Ø2.10 mm ist ein PCB-Entwurfswert, nicht die Hersteller-Stromfreigabe. Nominaler Ring(2.10−1.475)/2=0.3125 mm; beim größten Fertigloch1.525 mm bleiben0.2875 mm vor Registriertoleranz. Herstellerzeichnung fordert mindestens0.10 mm Ring. Werkzeug-/Lagenregistrierung ist so zu begrenzen, dass der tatsächliche Mindestring nach Mikroschliff nicht unter0.10 mm fällt. Alle acht Pins sind zum jeweiligen Anschlussnetz verbunden.

Die Herstellerwerte für Rohbohrung, Fertigbohrung und25..60 µm Cu sind **gleichzeitig** einzuhalten; beliebige unabhängige Eckwerte dürfen nicht kombiniert werden. Beispiel: RohØ1.60 und Cu25 µm ergeben alleinØ1.55, noch außerhalb des größten zulässigen PF-Fertigmaßes1.525. Der Fertiger muss die gemeinsame Prozessmitte entsprechend wählen und den chemischen Oberflächenauftrag mit einrechnen. Die alternative HAL-SpezifikationØ1.45±0.05 mm bei maximal15 µm Sn wird hier nicht verwendet. Die gewöhnliche globale Via-/PTH-Toleranz darf die PF-Klasse nicht überschreiben.

Fertigungsdaten müssen PF-Löcher separat kennzeichnen, obwohl das Excellon-Fertiglochmaß1.475 mm lautet. Der Leiterplattenbetrieb kompensiert auf den geforderten Rohbohrer; die CAD-Bohrdatei eigenmächtig auf1.60 mm zu ändern würde ein falsches Fertigmaß kommunizieren. Kein Lötpastendruck, kein Lot und kein Verguss in den Einpresslöchern. Durchgängigkeit und Lochverschmutzung vor der Presse prüfen.

## Einpresswerkzeuge und Ablauf

Je Terminal acht Löcher im lokalen Rasterx=±3.81 mm, y=−3.81/−1.27/+1.27/+3.81 mm. Untere Stützmatrix: dieselben acht Achsen, DurchgangØ1.75 +0.10/−0.00 mm; ausreichend Tiefe für mindestens2.1 mm Pinüberstand. Die Matrix stützt die Platine an jeder Einpresszone über den gesamten Hub. Die Stempel-Auflage darf weder M5-Gewinde noch seitliche Anschlussfläche beschädigen. Werkzeugzeichnungen müssen sich auf die tatsächliche rechtwinklige Terminalgeometrie beziehen; eine einfache Schraubzwinge auf den Gewindeflansch ist nicht spezifiziert.

1. Nach allen Lötprozessen Leiterplatte, Pinraster und Oberfläche visuell prüfen; keine verbogenen Pins, Restlot, Delamination oder blockierte Löcher. Bauteile mindestens3 mm von den Pressfit-Lochbereichen und PCB-Rand entfernt halten; Werkzeuge dürfen Nachbarbauteile nicht berühren.
2. PCB auf formschlüssiger, planparalleler Matrix positionieren; Stempel rechtwinklig zur PCB bewegen. Jeden Anschluss in **einem** kontinuierlichen Hub einpressen, ohne Kippen oder Nachhämmern. Die finale Sitzhöhe optisch/messtechnisch gegen Herstellerzeichnung prüfen.
3. Kraft-Weg-Kurve aufzeichnen. Datenblatt-Mindest-Einpresskraft40 N pro Pin entspricht320 N für acht Pins als einfache Summe; daraus folgt weder eine erlaubte Maximalkraft noch eine vollständige Kraftkurven-Schablone. Maximalwert, Kurvenform und Endlage am Coupon mit dem gewählten Laminat/Fertiger qualifizieren, bevor Platinen bestückt eingepresst werden. Für Serienproduktion verlangt der Hersteller Kraftüberwachung.
4. Nach dem Hub beide Seiten inspizieren, PCB-Verformung, Sitz und alle acht Pins dokumentieren. Ein zulässiger Materialspan wird nach Herstellerhinweis von einem beschädigten/aufgerissenen Loch unterschieden; lose leitfähige Späne entfernen.
5. Coupon-Auspressprüfung frühestens24 h nach Einpressen; Hersteller-Mindest-Auspresskraft30 N pro Pin. Nicht an der zu verwendenden Baugruppe zerstörend prüfen. Mikroschliff ausgewählter Coupons dokumentiert Kupferdicke, Ring und Rissfreiheit.

Einpressen erfolgt nach SMT-/THT-Löten. Würth beschreibt Wave/Reflow für diese Pressfit-Serie als nicht anwendbar. Nach dem Einpressen keine thermisch unbewertete Reflow-/Wellenlötbehandlung durchführen. Bei ungeeigneter Kraftkurve oder beschädigtem Loch nicht durch Lot„reparieren“; die Verbindung ist dann ein anderer, unqualifizierter Prozess.

## Prüfprotokoll für das erste Fertigungslos

Losnummer, laminatspezifischesTg, Fertigdicke an mindestensvier Ecken und nahe den sechs Klemmen, Rohbohrer-/Werkzeugdaten, PF-Fertiglochverteilung, Hülsenkupfer-Mikroschliff, chemische Oberflächenart/-dicke, Registrierung, Presswerkzeug-ID, kalibrierte Kraftmessung, Kraft-Weg-Kurven aller sechs Anschlüsse, Sitzhöhen, Coupon-Auspressversuch nach24 h und Fotos beider Seiten festhalten. Diese Aufzeichnungen existieren derzeit nicht; Herstellerdatenblattwerte ersetzen keine Messung des PMU-Fertigungsloses.
