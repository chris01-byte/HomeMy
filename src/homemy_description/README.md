# homemy_description

Robotermodell von HomeMy (URDF) für Simulation, Anzeige und Navigation.

**Stand:** Werte aus der CAD-Datei `hardware/cad/homemy.step` (ausgewertet am 16.11.2026), keine Messungen. Jeder Wert wird bei der Inbetriebnahme durch einen gemessenen ersetzt.

## Koordinaten

`base_link` liegt auf dem Boden unter der Mitte der Antriebsachse: X nach vorn, Y nach links, Z nach oben. Die Entscheidung zum LiDAR-Schlitz rechnet in einem Konstruktionsrahmen mit Ursprung in der Mitte der Grundfläche; es gilt `base_link` X = Konstruktion X − 0,0906 m.

| Rahmen | Lage in `base_link` (m) | Herkunft |
| --- | --- | --- |
| `lidar_link` | X 0,0694, Y 0, Z 0,1638 | Drehachse und Scanebene des STL-27L |
| `left_wheel_link`, `right_wheel_link` | Y ±0,1997, Z 0,0762 | Radmitten, Raddurchmesser 152,4 mm |
| `left_caster_link`, `right_caster_link` | X −0,2326, Y ±0,170 | hintere Lenkrollen, 30-mm-Rad |
| `imu_link` | X 0, Y 0, Z 0,10 | Platzhalter, der Einbauort des HWT601 ist offen |
| `oak_mount_link` | X −0,0729, Y −0,0026, Z 1,244 | Mitte von OAK und Halter im CAD |
| `oak_link`, `oak_optical_frame` | um `oak_tilt_deg` geneigt | Neigung von Hand |

Grundfläche: X −0,2906 bis +0,1094, Y ±0,250, Eckenradius 0,100 m. Die Antriebsachse liegt 108 mm hinter der Vorderkante; vor ihr gibt es keine Stützrolle.

Alle Werte stehen in `config/geometry.yaml`. Prüfstand, Bewegungsfreigabe und Navigation lesen dieselbe Datei.

## Neigung der OAK

Die Neigung wird von Hand eingestellt (Entscheidung vom 19.11.2026). Der Winkel ist ein eingemessener Wert: Er kommt aus dem Einmessprotokoll und wird als `oak_tilt_deg` übergeben, positiv heißt nach unten. Der Standardwert 0 dient nur der Anzeige. Siehe `docs/decisions/2026-11-17-oak-d-s2-camera.md`.

## Noch nicht im Modell

- Die Arme und ihre Fahrhaltung (Stufe S3). Der Fahrumriss nimmt an, dass die Arme beim Fahren innerhalb der Grundfläche bleiben. Das ist eine Annahme, bis die Fahrhaltung festgelegt ist.
- Genaue Formen: Das Gehäuse besteht aus Quadern. Die runden Ecken gibt es nur im Fahrumriss.

## Verwendung

```bash
ros2 launch homemy_description description.launch.py oak_tilt_deg:=0.0
```

Die Tests vergleichen das erzeugte Modell mit der Maßdatei:

```bash
colcon test --packages-select homemy_description
```
