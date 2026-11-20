# homemy_simulation

Ersatzteile für die Simulation. **Nie auf dem Roboter starten.** Jeder Knoten meldet beim Start eine Warnung, dass er simuliert.

| Knoten | Ersetzt | Verhalten |
| --- | --- | --- |
| `synthetic_map` | SLAM | Veröffentlicht `/map` erst nach dem ersten Einschalten des Kartiermodus. Jede neue Kartierfahrt beginnt klein und mit neuem Fingerabdruck. Solange der Controller „fährt“, wird jede Sekunde mehr von der Testwohnung sichtbar. Nach der Fahrt bleibt die letzte Karte veröffentlicht. |
| `sim_base` | Fahrantrieb, LiDAR, Odometrie, IMU: der **Prüfstand** | siehe unten |
| `sim_controller` | Funk-Controller, `joy_node` und die Person am Controller | Sendet `/joy` mit 20 Hz. Mit `follow_route` fährt eine sorgfältige Person die Kartierroute der Welt mit dem Steuerkreuz ab: erst auf der Stelle zum nächsten Wegpunkt drehen, dann geradeaus. Ohne Route meldet das Steuerkreuz „vorwärts“ (Achse 7). Mit `driving` false lässt die Person los; mit `connected` false ist der Controller aus und sendet nichts. |

Die Testwohnung von `synthetic_map` ist dieselbe wie im Mock der App: 48 × 36 Zellen zu 10 cm. Sie ist erfunden und keine echte Wohnung, und sie ist zu klein zum Fahren.

## Der Prüfstand `sim_base`

Er ersetzt nur die Geräte; alles dahinter ist der echte HomeMy-Code. Übernommen aus dem Prüfstand von Amadeus (roboter_ws, Branch `claude/blissful-pasteur-s1eivj`, Commit `940a748`: `ap06_world.py`, `sh_robustheit_welt.py`), umgestellt auf HomeMy:

- Maße aus `homemy_description/config/geometry.yaml`;
- der LiDAR sitzt im Sockel auf 164 mm und sieht die eigenen Streben und Stege (kurze Rückmeldungen in den sechs blinden Sektoren);
- keine VL53 und keine niedrigen Hindernisse.

| Topic | Inhalt |
| --- | --- |
| Antrieb, Form `cmd_vel` | `/cmd_vel` fährt den Roboter direkt; ohne frischen Befehl bremst er nach 0,25 s. Der Prüfstand liefert `/odom` und TF selbst. |
| Antrieb, Form `modbus` | Zwei simulierte ESS23-RS-Motoren an einem simulierten RS485-Bus (`ess23_sim.py`). Ein Pseudo-Terminal steht für den USB-Adapter; darüber laufen echte Modbus-RTU-Telegramme. So fährt der **echte Antriebstreiber** die simulierten Motoren und rechnet `/odom` und TF aus deren Encoderzählern. Die Motoren haben wie die echten keine eigene Überwachung. |
| LiDAR, Form `scan` | `/scan`: 720 Strahlen, 10 Hz, `lidar_link`, ab −π gegen den Uhrzeiger, 1 cm Rauschen, kein Treffer als +inf |
| LiDAR, Form `raw` | `/scan_raw`, wie der Herstellertreiber des STL-27L ihn sendet: je Scan 2146 bis 2176 Strahlen, 0 bis 360°, Frame `lidar_raw`, Sensor schief eingebaut, NaN ohne Messung. Die **echte Vereinheitlichung** macht daraus `/scan`. |
| LiDAR, Form `serial` | Ein simulierter STL-27L an einer nachgebildeten seriellen Leitung (`stl27l_sim.py`): Er sendet die Datenpakete des Geräts, 21 600 Messpunkte je Sekunde, mit leicht schwankender Drehzahl. So liest der **unveränderte Herstellertreiber** sie und sendet `/scan_raw` selbst. |
| `/odom`, TF `odom → base_link` | nur in der Form `cmd_vel`: 50 Hz, mit Maßstabsfehlern von 2 % beim Drehen und −1 % bei der Strecke. In der Form `modbus` weicht stattdessen der simulierte Roboter leicht von den Nennmaßen ab (Radradius −1 %, Spurweite +2 %), sodass die Odometrie des Treibers ähnlich danebenliegt. |
| IMU, Form `topic` | `/imu/data`: Drehrate mit Nullpunktfehler und Rauschen, ohne Lage |
| IMU, Form `modbus` | Ein simulierter HWT601 an einer eigenen simulierten RS485-Leitung (`hwt601_sim.py`), kopfüber eingebaut. So liest das **echte Leseprogramm** ihn aus, und die Aufbereitung muss das Vorzeichen der Einbaulage anwenden. Der simulierte Sensor zählt jede Anfrage, die kein reines Lesen ist. |
| `/joint_states` | die beiden Radgelenke |
| `/homemy/sim/ground_truth`, `/homemy/sim/status_json` | nur für Tests: wahre Lage, Berührung, Abstand, Fahrstrecke, Raum |

Mit dem Parameter `start_pose` (`[x, y, yaw]` in der Welt) beginnt der Roboter woanders als in der Weltdatei, zum Beispiel dort, wo er vor einem Neustart stand.

Die Fahrphysik läuft in einem eigenen Thread mit 100 Hz. Jeder Antrieb ist eine Verzögerung erster Ordnung wie bei Amadeus gemessen. Eine Berührung zählt, sobald der rechteckige Umriss plus 2 cm ein Hindernis berührt.

## Die Testwohnung `worlds/testwohnung.json`

Vier Räume (Wohnzimmer, Flur, Küche, Schlafzimmer) auf 9,4 × 5,4 m, Türen 85 cm breit, Möbel als Quader. Der Couchtisch besteht aus vier Beinen, weil der LiDAR unter der Platte hindurch misst. Die Wohnung ist absichtlich unsymmetrisch, denn bei Amadeus führten symmetrische Welten zu falschen Schleifenschlüssen. Sie ist erfunden und keine echte Wohnung.

Die Kartierroute führt durch alle Räume. Ein Test prüft, dass jede Strecke 5 cm Abstand hält und an jedem Wendepunkt Platz zum Drehen ist.

`world.py` bewertet außerdem eine fertige Karte gegen die Welt: Abstand der Wandzellen zur nächsten Wand, einmal direkt und einmal nach einer starren Ausrichtung, dazu der Anteil der bekannten freien Fläche.

## Zur Laufzeit umschalten

Den Roboterzustand und das Not-Halt-Signal liefert auch in der Simulation die Überbrückung aus `homemy_boot_manager`.

```bash
ros2 param set /homemy_sim_controller driving false
ros2 param set /homemy_sim_controller connected false
ros2 param set /lifecycle_bridge state FAULT
ros2 param set /lifecycle_bridge estop_pressed true
ros2 param set /homemy_sim_base bus_silent true
ros2 param set /homemy_sim_base lidar_silent true
ros2 param set /homemy_sim_base imu_silent true
ros2 param set /homemy_sim_base yaw_kick_deg 5.0
ros2 param set /homemy_sim_base encoder_jump_counts 500000
```

Gestartet werden die Knoten über `homemy_bringup/launch/app_sim.launch.py` (Stufe S1) und `drive_sim.launch.py` (Stufe S2).
