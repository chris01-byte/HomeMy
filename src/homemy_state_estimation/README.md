# homemy_state_estimation

Der IMU-Sensor HWT601 von HomeMy: Auslesen und Aufbereiten der Drehrate für die Odometrie. Vertrag: `contracts/hardware/imu-commissioning.md`.

Stand: In der Simulation geprüft, an einem simulierten Sensor. Am echten Sensor von HomeMy ist nichts gelaufen.

## Wozu

Die Räder merken nicht, wenn sich das Fahrgestell auf einer Fliesenfuge oder bei durchrutschendem Rad verdreht. Bei Amadeus wurden über eine Fuge −3,2° Drehung gemessen, während die Räder +0,006° meldeten. Der Gyro des IMU sieht diese Drehung. HomeMy nutzt vom IMU deshalb genau eine Größe: die Drehrate um die Hochachse.

## Was ausgeliefert gilt

Ausgeliefert beeinflusst der IMU nichts. Die Odometrie kommt allein von den Rädern. Der IMU wird nur gelesen und mit den Rädern verglichen. Erst mit `use_imu_fusion:=true` fließt seine Drehrate in die Odometrie ein.

Der IMU kann nie eine Bewegung auslösen oder erlauben.

## Bausteine

| Programm | Aufgabe |
| --- | --- |
| `hwt601_imu` | Liest den Sensor 100-mal je Sekunde über RS485 aus und sendet `/imu/data_raw`. Übernommen von Amadeus (Stand `08a4b9a`). Das Programm kann nur lesen: Einstellungen und Kalibrierung des Sensors kann es nicht ändern. |
| `yaw_rate` | Macht aus den Rohdaten die Drehrate des Fahrgestells (`/imu/yaw_rate`). Lernt dazu den Nullpunktfehler des Gyros, solange die Räder stehen, und hält ihn fest, sobald sie drehen. Ohne gelernten Nullpunkt sendet es nichts. |
| EKF (`robot_localization`) | Nur mit `use_imu_fusion:=true`: rechnet `/odom` aus der Geschwindigkeit der Räder und der Drehrate des Gyros. Fällt der Gyro aus, geht es mit der Drehrate der Räder weiter. |

Der IMU hängt an einem eigenen USB-RS485-Adapter mit dem festen Namen `/dev/homemy_imu` (`config/99-homemy-imu.rules.example`). Den Anschluss des Antriebs und des LiDAR lehnt das Leseprogramm ab, auch unter einem anderen Namen.

## Zustand ansehen

```bash
ros2 topic echo --once /homemy/imu/status_json
```

```bash
ros2 topic echo --once /homemy/imu/yaw_rate_status_json
```

Die zweite Meldung zeigt, ob der Nullpunkt gelernt ist (`ready`), wie groß er ist (`bias_radps`) und zwei Summen seit dem Lernen: die Drehung laut Gyro (`gyro_yaw_deg`) und laut Rädern (`wheel_yaw_deg`). Ihr Unterschied zeigt, was die Räder nicht sehen.

Gründe, warum noch keine Drehrate kommt:

| `reason` | Bedeutung |
| --- | --- |
| `waiting_for_standstill` | Der Roboter steht noch nicht ruhig, oder die Odometrie der Räder fehlt. |
| `learning_bias` | Der Nullpunkt wird gerade gelernt (5 Sekunden). |
| `bias_window_unsteady` | Während des Lernens wurde der Roboter bewegt. Es wird neu versucht. |
| `bias_implausibly_large` | Der gemessene Nullpunkt ist zu groß. Dreht jemand den Roboter, oder stimmt die Achse nicht? |
| `imu_stale` | Vom Sensor kommen keine Daten. |

## Schritte am Roboter

Alle Schritte bis I4 sind ohne Motoren.

| Schritt | Inhalt |
| --- | --- |
| I0 | udev-Regel einrichten, `ros2 launch homemy_state_estimation imu.launch.py` starten. Die erste Meldung oben muss `"ready": true` zeigen. |
| I1 | Rate etwa 100 Hz. Kabel ziehen: `ready` wird `false`. Kabel stecken: `ready` wird von selbst wieder `true`. |
| I2 | Roboter ruhig stehen lassen, kalt und warm: `bias_radps` notieren. |
| I3 | Motoren stromlos. Roboter von Hand nach links drehen: `gyro_yaw_deg` muss steigen. Eine volle Drehung muss 360° ergeben. Sonst `yaw_axis`, `yaw_sign` oder die Skala in `config/hwt601.yaml` anpassen. |
| I4 | Mit dem Controller fahren und die beiden Summen vergleichen, auch über eine Fliesenfuge. |
| I5 | Erst nach der Inbetriebnahme des Antriebs und mit Freigabe einer anwesenden Person: `use_imu_fusion:=true`. |

## Prüfung

- 28 von Amadeus übernommene Tests für das Entschlüsseln der Sensordaten und die serielle Verbindung.
- 26 Tests der Drehraten-Aufbereitung: kein Ausgang ohne Nullpunkt, Bewegung wird nie als Nullpunkt gelernt, von Hand gedrehter Roboter, Einbaulage, Lücken und ungültige Daten.
- `homemy_bringup/test/test_imu_sim.py`: das echte Leseprogramm an einem simulierten Sensor. Ergebnis bei einer vollen Drehung auf der Stelle: Der Gyro lag 0,1° neben der Wahrheit, die Räder 11°. Eine Verdrehung des Fahrgestells um 5° ohne Raddrehung sah nur der Gyro.

Was die Simulation nicht zeigt: Nullpunkt, Rauschen und Zeitverhalten des echten Sensors, seine Einbaulage und das Verhalten des USB-Adapters.
