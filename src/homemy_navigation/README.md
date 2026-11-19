# homemy_navigation

Standort und Wegplanung von HomeMy.

**Stand:** in der Simulation geprüft: Kartieren mit slam_toolbox, Umschalten auf die gespeicherte Karte mit AMCL, Selbstfinden nach dem Versetzen, Fahren mit Nav2. Am Roboter nie gelaufen.

## Lokalisierungs-Manager

`localization_manager` ist der einzige Bediener von slam_toolbox, Kartenserver und AMCL (alle drei sind Lifecycle-Knoten):

| Lage | slam_toolbox | Kartenserver und AMCL |
| --- | --- | --- |
| Kartiermodus aktiv | aktiv; jede Kartierfahrt beginnt eine neue Karte | aus |
| Kartiermodus beendet, Karte nicht gespeichert | angehalten, seine Karte bleibt sichtbar | aus |
| Karte gespeichert (gespeicherte Version = Live-Karte) | aus | Kartenserver lädt genau diese Version; AMCL startet an der letzten SLAM-Lage |
| Start mit gespeicherter Karte | aus | neueste gespeicherte Version; AMCL startet an der zuletzt gesicherten Lage, wenn sie zu genau dieser Karte gehört; passt sie nicht, sucht der Roboter die ganze Karte ab |

Im Stand rechnet AMCL nur auf Anfrage nach. Nach dem Setzen der Startlage fordert der Manager deshalb bis zu 30 Nachrechnungen an (`request_nomotion_update`), damit der Scan die Lage bestätigt oder widerlegt. Die gesicherte Lage gilt als genau (15 cm, 8°), weil sich ein ausgeschalteter Roboter nicht bewegt.

## Selbstfinden in der Karte

Der Roboter kann jederzeit verschoben oder getragen werden. Passt der Scan nicht zur vermuteten Lage, oder ist gar keine Lage bekannt, sucht der Manager die ganze Karte ab:

1. Auslöser: Der Standort ist seit 5 s nicht sicher, und der Roboter steht (aus `/odom`). Ohne bekannte Lage beginnt die Suche sofort.
2. Suche: Für alle freien Kartenstellen und alle Blickrichtungen wird bewertet, wie gut der aktuelle Scan zu den Wänden der Karte passt und ob die Strahlen durch freien Raum laufen. Erst grob (etwa 10 cm, 5°), dann fein um die besten Stellen. Der Code ist aus Amadeus übernommen (`global_scan_matcher.py`, Commit `05439c7`), samt Tests.
3. Annahme: Gesamtwert und Anteil der Scanpunkte an Kartenwänden je mindestens 0,85; ein klarer Vorsprung vor der nächsten anderen Stelle; und zwei Suchen auf verschiedenen Scans müssen dieselbe Stelle liefern (20 cm, 8°).
4. Dann startet AMCL dort, und die Prüfung „Standort sicher“ läuft wie sonst.
5. Ohne Ergebnis nach fünf Versuchen: 10 s Pause, dann von vorn. Nichts rastet ein. Solange meldet der Roboter „nicht lokalisiert“ und nimmt keine Fahrt an.

Die Suche bewegt den Roboter nicht. In der Testwohnung dauert ein Durchgang etwa 2,5 s.

**Abweichungen von Amadeus:**

- Der Vorsprung vor der nächsten Stelle muss 5 % betragen statt 15 %. Mit 15 % wurden in der rechteckigen Küche der Testwohnung richtige Treffer abgelehnt, weil dort die um 180° gedrehte Lage etwa 90 % des Scans erklärt. Mit 5 % wurden alle 17 probierten Lagen angenommen; ein völlig symmetrischer Raum wird weiterhin abgelehnt. Der Wert stammt aus der Simulation und muss an einer echten Karte bestätigt werden.
- Als mögliche Stellen gelten alle, an denen `base_link` mindestens 12 cm Abstand zur nächsten nicht freien Zelle hat, statt 40 cm. Bei HomeMy liegt `base_link` nur 11 cm hinter der Vorderkante; ein Roboter dicht vor einer Wand muss gefunden werden.
- Die Schrittweite der groben Suche richtet sich nach dem Kartenraster.

**Geprüft in der Simulation (19.11.2026):**

- Die Suche allein, auf einer aus der Testwohnung erzeugten Karte: 17 Lagen, Fehler höchstens 4,5 cm und 1,8°.
- Der ganze Ablauf auf einer von slam_toolbox gebauten Karte: Der Roboter wurde ausgeschaltet an sechs Stellen in vier Räumen gesetzt. Er fand sich jedes Mal mit zwei Suchläufen wieder, etwa 20 s nach dem Start, mit 5 bis 9 cm Fehler, ohne sich zu bewegen. Im Ende-zu-Ende-Test fährt er danach in einen anderen Raum.

An einer echten Karte ist das nicht geprüft.

**Grenzen:** In einem Raum, der von jeder Stelle gleich aussieht (leerer symmetrischer Raum, langer Flur), findet die Suche nichts Eindeutiges. Dann hilft es, den Roboter an eine markantere Stelle zu stellen. Ein falscher Treffer kann den Roboter nicht in ein Hindernis fahren: Der Hindernisschutz der Bewegungsfreigabe nutzt die Kartenlage nicht, und die Prüfung „Standort sicher“ vergleicht beim Fahren weiter Scan und Karte.

**„Standort sicher“** (`/homemy/localization/ready`, 5 Hz) meldet er nur, wenn AMCL sicher ist **und** mindestens 80 % der LiDAR-Endpunkte höchstens 15 cm neben einer belegten Kartenzelle liegen; zum Halten reichen 60 %. Das ist die Lehre aus Amadeus: Dort meldete AMCL einmal sicher eine Lage, die 1,95 m falsch war. Die letzte sichere Lage sichert er alle 2 s, gebunden an den Fingerabdruck der Karte.

Status: `/homemy/localization/status_json` (Modus, Grund, Übereinstimmung, Unsicherheit, Herkunft der Startlage, Stand der Suche, geschätzte Lage).

## Kartieren mit slam_toolbox

`launch/slam.launch.py` startet slam_toolbox (online, asynchron) mit `config/slam_toolbox.yaml`. Ausgangspunkt ist Amadeus (`slam_toolbox_amadeus.yaml`, Commit `05439c7`) mit den strengeren Schwellen für Schleifenschlüsse aus dem Amadeus-Prüfstand. Eingang ist `/scan_masked`; 5-cm-Raster in der Simulation.

## Fahren mit Nav2

`launch/navigation.launch.py` startet Kartenserver, AMCL, Planer (A*), Regler (Regulated Pure Pursuit), Geschwindigkeitsglätter und `bt_navigator`. `config/nav2.yaml` folgt den bei Amadeus real gefahrenen Werten (Commit `05439c7`, Regler aus `71d3a87`):

- Umriss: die abgerundete HomeMy-Grundfläche, `base_link` auf der Antriebsachse;
- Hindernisquelle: der maskierte LiDAR-Scan; keine VL53, noch keine OAK-Tiefe;
- unbekannte Zellen sind nie frei (`allow_unknown: false`);
- Verhaltensbaum ohne Recovery (`config/navigate_to_pose_no_recovery.xml`): kein Drehen, kein Zurücksetzen auf eigene Faust; geheilt wird im Auftrag;
- die Befehle gehen über den Glätter an `/homemy/cmd_vel/nav`, also an die Bewegungsfreigabe, nie direkt an den Antrieb.

Alle Werte sind Simulationswerte; die Werte für den Roboter kommen aus der Inbetriebnahme.
