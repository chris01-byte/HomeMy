# homemy_lidar_bringup

Aufbereitung des STL-27L-Scans. Bisher enthält das Paket nur die Maske für die blinden Sektoren. Treiber und Vereinheitlichung der Strahlzahl folgen mit der LiDAR-Inbetriebnahme (`contracts/hardware/lidar-commissioning.md`).

## `scan_mask`

Hinter den beiden Streben und den Stegen im Acrylring sieht der LiDAR nur den Roboter selbst. Der Knoten setzt jeden Strahl in diesen sechs Sektoren auf NaN. NaN heißt nach REP 117 „keine gültige Messung“: Die Kartierung trägt dort keinen freien Raum ein, und der Hindernisschutz behandelt den Sektor als unbekannt.

| Richtung | Topic | Typ |
| --- | --- | --- |
| Eingang | `/scan` | `sensor_msgs/LaserScan` |
| Ausgang | `/scan_masked` | `sensor_msgs/LaserScan` |

Die Sektoren stehen in `config/scan_mask.yaml`. Sie kommen aus der CAD-Vorhersage in `docs/decisions/2026-11-16-lidar-slot-and-support-webs.md`: ±72,9 bis 76,1°, ±126,9 bis 137,9°, ±157,2 bis 160,1°, gemessen an der LiDAR-Achse, 0° = geradeaus, positiv = nach links. Dazu kommt ein Rand von 1,5° je Seite. Sektoren und Rand werden in Schritt L4 am echten Scan gemessen.

Der Knoten setzt voraus, dass der Scan in `lidar_link` mit 0° nach vorn und Drehsinn gegen den Uhrzeiger vorliegt. Für den echten Treiber wird das in Schritt L3 festgestellt; bis dahin darf der echte Scan keine Bewegung beeinflussen.

## Prüfung

Die Tests prüfen die eingetragenen Sektoren gegen die Entscheidung, die Spiegelsymmetrie, den Rand und das Umrechnen der Winkel. Ein Test in `homemy_simulation` prüft, dass die Selbstrückmeldungen der Streben und Stege im Prüfstand vollständig in diese Sektoren fallen.
