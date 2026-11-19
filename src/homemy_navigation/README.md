# homemy_navigation

Standort und Wegplanung von HomeMy.

**Stand:** in der Simulation geprüft: Kartieren mit slam_toolbox, Umschalten auf die gespeicherte Karte mit AMCL, Fahren mit Nav2. Am Roboter nie gelaufen.

## Lokalisierungs-Manager

`localization_manager` ist der einzige Bediener von slam_toolbox, Kartenserver und AMCL (alle drei sind Lifecycle-Knoten):

| Lage | slam_toolbox | Kartenserver und AMCL |
| --- | --- | --- |
| Kartiermodus aktiv | aktiv; jede Kartierfahrt beginnt eine neue Karte | aus |
| Kartiermodus beendet, Karte nicht gespeichert | angehalten, seine Karte bleibt sichtbar | aus |
| Karte gespeichert (gespeicherte Version = Live-Karte) | aus | Kartenserver lädt genau diese Version; AMCL startet an der letzten SLAM-Lage |
| Start mit gespeicherter Karte | aus | neueste gespeicherte Version; AMCL startet an der zuletzt gesicherten Lage, wenn sie zu genau dieser Karte gehört |

Im Stand rechnet AMCL nur auf Anfrage nach. Nach dem Setzen der Startlage fordert der Manager deshalb bis zu 30 Nachrechnungen an (`request_nomotion_update`), damit der Scan die Lage bestätigt oder widerlegt. Die gesicherte Lage gilt als genau (15 cm, 8°), weil sich ein ausgeschalteter Roboter nicht bewegt. Wurde er doch versetzt, passt der Scan nicht, und der Roboter meldet „nicht lokalisiert“. Ohne bekannte Lage meldet er ebenfalls „nicht lokalisiert“. Eine Suche über die ganze Karte wie bei Amadeus ist ein späterer Schritt.

**„Standort sicher“** (`/homemy/localization/ready`, 5 Hz) meldet er nur, wenn AMCL sicher ist **und** mindestens 80 % der LiDAR-Endpunkte höchstens 15 cm neben einer belegten Kartenzelle liegen; zum Halten reichen 60 %. Das ist die Lehre aus Amadeus: Dort meldete AMCL einmal sicher eine Lage, die 1,95 m falsch war. Die letzte sichere Lage sichert er alle 2 s, gebunden an den Fingerabdruck der Karte.

Status: `/homemy/localization/status_json` (Modus, Grund, Übereinstimmung, Unsicherheit, Herkunft der Startlage).

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
