# homemy_lidar_bringup

Alles, was zwischen dem LiDAR STL-27L und den Verbrauchern des Scans liegt. Vertrag: `contracts/hardware/lidar-commissioning.md`.

```
STL-27L --USB--> Herstellertreiber --/scan_raw--> scan_normalize --/scan--> scan_mask --/scan_masked-->
                                                                              Kartierung, Standort, Hindernisschutz
```

Stand: In der Simulation geprüft, auch mit dem unveränderten Herstellertreiber an einem simulierten LiDAR. Am echten LiDAR von HomeMy ist nichts gelaufen.

## Sperre

Ausgeliefert kann der echte Scan nichts beeinflussen. Solange in `config/stl27l.yaml` `alignment_confirmed: false` steht, sendet `scan_normalize` den Scan nur auf `/scan_unconfirmed`. Auf `/scan` kommt nichts an. Kartierung und Standort bekommen dann keinen Scan, und die Bewegungsfreigabe bleibt zu, weil ihr der Scan fehlt.

Die Sperre fällt erst, wenn am Roboter geprüft ist, wo beim Sensor „vorn“ ist und in welche Richtung er zählt (Schritt L3), und wenn die Maske zum Scan passt (Schritt L4).

## Herstellertreiber

Der Treiber `ldlidar_stl_ros2` wird nicht kopiert und nicht verändert. `vendor/ldlidar_stl_ros2.repos` nagelt ihn auf den Stand fest, mit dem Amadeus gefahren ist. Auf dem Roboterrechner baut ihn ein Skript in einem eigenen Arbeitsbereich:

```bash
source /opt/ros/jazzy/setup.bash
```

```bash
src/homemy_lidar_bringup/vendor/build_vendor_driver.sh
```

```bash
source ~/homemy_lidar_ws/install/setup.bash
```

Unter Ubuntu 24.04 lässt sich der Treiber nur mit einem Zusatz für den Compiler bauen (dem Quelltext fehlt eine Einbindung). Das Skript setzt ihn; der Quelltext bleibt, wie er ist.

Fehlt der LiDAR beim Start, beendet sich der Treiber. Die Startdatei startet ihn dann alle drei Sekunden neu, bis der LiDAR da ist. Wird das Kabel im Betrieb gezogen, läuft der Treiber weiter, meldet Zeitüberschreitungen und sendet keine Scans; steckt das Kabel wieder, kommen die Scans zurück.

Er sendet auf `/scan_raw` im Frame `lidar_raw`. Diesen Frame gibt es im Robotermodell absichtlich nicht: Der rohe Scan hat eine wechselnde Strahlenzahl und die Nullrichtung des Geräts, niemand soll ihn im Raum einordnen.

Der Anschluss heißt `/dev/homemy_lidar`. Den festen Namen richtet `config/99-homemy-lidar.rules.example` ein. Nie `/dev/ttyUSB0` verwenden: Der RS485-Adapter des Antriebs ist auch ein USB-Seriell-Gerät, und die Nummern hängen von der Einsteckreihenfolge ab.

## `scan_normalize`

Übernommen von Amadeus (`scan_vereinheitlichen.py`, Stand `05439c7`) und für HomeMy erweitert.

- **Feste Strahlenzahl.** Der STL-27L liefert je Umdrehung verschieden viele Strahlen (bei Amadeus gemessen: 2146 bis 2176). slam_toolbox merkt sich die Zahl des ersten Scans und verwirft danach jeden Scan mit anderer Zahl, ohne Warnung. Der Knoten setzt jeden Scan auf 2160 Strahlen um. Er nimmt dafür immer den nächstgelegenen echten Messwert und mittelt nie, damit an Kanten keine Flächen entstehen, die es nicht gibt.
- **Ausrichtung am Roboter.** Der Ausgang liegt in `lidar_link`: 0° ist geradeaus, positiv ist nach links. Wie der Sensor verdreht eingebaut ist, steht in `yaw_offset_deg`. Bei Amadeus waren es +90°. Für HomeMy ist der Wert nicht gemessen.
- Ungültige Messungen des Treibers (NaN) bleiben NaN. Scans ohne Strahlen oder mit unbrauchbaren Winkelangaben werden verworfen.

| Richtung | Topic | Typ |
| --- | --- | --- |
| Eingang | `/scan_raw` | `sensor_msgs/LaserScan` |
| Ausgang, bestätigt | `/scan` | `sensor_msgs/LaserScan` |
| Ausgang, unbestätigt | `/scan_unconfirmed` | `sensor_msgs/LaserScan` |

## `scan_mask`

Hinter den beiden Streben und den Stegen im Acrylring sieht der LiDAR nur den Roboter selbst. Der Knoten setzt jeden Strahl in diesen sechs Sektoren auf NaN. NaN heißt nach REP 117 „keine gültige Messung“: Die Kartierung trägt dort keinen freien Raum ein, und der Hindernisschutz behandelt den Sektor als unbekannt.

| Richtung | Topic | Typ |
| --- | --- | --- |
| Eingang | `/scan` | `sensor_msgs/LaserScan` |
| Ausgang | `/scan_masked` | `sensor_msgs/LaserScan` |

Die Sektoren stehen in `config/scan_mask.yaml`. Sie kommen aus der CAD-Vorhersage in `docs/decisions/2026-11-16-lidar-slot-and-support-webs.md`: ±72,9 bis 76,1°, ±126,9 bis 137,9°, ±157,2 bis 160,1°, gemessen an der LiDAR-Achse, 0° = geradeaus, positiv = nach links. Dazu kommt ein Rand von 1,5° je Seite. Sektoren und Rand werden in Schritt L4 am echten Scan gemessen.

## Prüfwerkzeug `lidar_check`

Das Werkzeug hört nur zu. Es sendet nichts und bewegt nichts.

```bash
ros2 run homemy_lidar_bringup lidar_check stats --topic /scan_raw
```

Zeigt Rate, Strahlenzahlen und Alter der Scans (Schritte L1 und L2).

```bash
ros2 run homemy_lidar_bringup lidar_check target
```

Zeigt jede Sekunde, in welcher Richtung das nächste Objekt steht (Schritt L3). Ein Karton genau vor dem Roboter muss bei etwa 0° erscheinen. Trägt man ihn nach links, muss der Winkel steigen.

```bash
ros2 run homemy_lidar_bringup lidar_check sectors
```

Sucht die eigenen Teile des Roboters im Scan und vergleicht sie mit der Maske (Schritt L4). Eigene Teile erkennt es daran, dass sie nah sind und sich über viele Scans gar nicht bewegen.

## Schritte am Roboter

Alle Schritte sind ohne Motoren. Der Roboter steht still.

| Schritt | Inhalt |
| --- | --- |
| L0 | Treiber mit dem Skript bauen, udev-Regel einrichten, `ros2 launch homemy_lidar_bringup stl27l.launch.py` starten und beenden. |
| L1, L2 | `lidar_check stats` auf `/scan_raw` und auf `/scan_unconfirmed`: Rate etwa 10 Hz, wechselnde Strahlenzahl am Eingang, feste 2160 am Ausgang. |
| L3 | `lidar_check target` mit einem Karton vorn, dann links. Stimmt der Winkel vorn nicht, `yaw_offset_deg` um die Abweichung ändern. Sinkt der Winkel nach links, `laser_scan_dir` umstellen. Danach wiederholen. |
| L4 | `lidar_check sectors`: Jeder feste Reflex muss in der Maske liegen, und jeder Maskensektor muss sich zeigen. Sonst die Sektoren in `config/scan_mask.yaml` anpassen. |
| danach | `alignment_confirmed: true` setzen und die gemessenen Werte im Vertrag festhalten. |

## Prüfung

- Tests des Rasters, von Amadeus übernommen und erweitert: nächster Nachbar statt Mittelung, wechselnde Strahlenzahlen, Drehung, Drehsinn, unvollständige und unbrauchbare Scans.
- ROS-Test von `scan_normalize` mit Scans, wie der Herstellertreiber sie sendet. Dazu die Sperre: Ohne Bestätigung kommt auf `/scan` nichts an.
- Tests der Auswertung des Prüfwerkzeugs: eigene Teile finden, Vergleich mit der Maske, verdrehter Scan fällt auf.
- Tests der Maske: eingetragene Sektoren gegen die Entscheidung, Spiegelsymmetrie, Rand.
- Im Prüfstand (`homemy_simulation`) verhält sich der simulierte LiDAR wie der Herstellertreiber: wechselnde Strahlenzahl, 0 bis 360°, schief eingebaut. Die ganze Fahr-Simulation läuft durch diese Kette.
- `homemy_bringup/test/test_lidar_sim.py` lässt den unveränderten Herstellertreiber laufen. Der Prüfstand sendet dafür die seriellen Datenpakete des Geräts über eine nachgebildete serielle Leitung. Geprüft werden: wechselnde Strahlenzahl am Treiber, festes Raster danach, Richtung und Drehsinn an den Wänden der Testwohnung, eigene Streben genau in der Maske, die Sperre, Kabel ziehen und wieder einstecken.

Was die Simulation nicht zeigt: die echte Nullrichtung, die echten Sektoren, das echte Rauschen und das Verhalten des USB-Adapters am Roboterrechner.
