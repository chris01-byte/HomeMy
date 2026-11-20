# Runbook: HomeMy zum ersten Mal am Roboter starten

## Zweck

Vom frisch aufgesetzten Roboterrechner bis zur ersten Kartierfahrt mit dem Controller. Die Reihenfolge ist fest: Rechner, Geräte, gesperrter Start, LiDAR, IMU, Antrieb, erste Fahrt.

Stand der Software: In der Simulation geprüft, auch mit diesem Startprofil und allen drei Treibern an simulierten Geräten. Am echten Roboter ist noch nichts gelaufen. Diese Anleitung ist deshalb selbst ungeprüft; Abweichungen bitte festhalten.

## Grenzen

- **Motoren drehen erst ab Abschnitt 7.** Dafür muss eine Person am Roboter stehen, die Hand am Not-Halt-Schalter. Zuerst sind die Räder aufgebockt.
- Diese Anleitung ist keine Freigabe. Die Freigabe gibt jedes Mal die Person am Roboter.
- Besteht ein Schritt nicht: nicht weitergehen und keinen Wert raten.
- Die Werte dieses Roboters stehen nur in `~/.config/homemy/robot_local.yaml`. Diese Datei gehört nicht ins Repository.
- Die App-Verbindung hat keinen Zugriffsschutz (Entscheidung für den Labor-Prototyp). `bridge_address:=0.0.0.0` nur im Labornetz verwenden.

## Sichere Voreinstellung

Ohne die örtliche Datei kann der Roboter nichts bewegen und nutzt keinen echten Messwert:

| Gerät | ausgeliefert | öffnet sich durch |
| --- | --- | --- |
| Antrieb | Der Treiber rechnet nur. Er öffnet den Bus nicht und sendet nichts. | `dry_run: false` und `allow_rs485: true`, dazu die Encoderwerte |
| LiDAR | Der Scan geht nur auf `/scan_unconfirmed`. Kartierung, Standort und Fahren bekommen keinen. | `alignment_confirmed: true` |
| IMU | Wird nur gelesen und mit den Rädern verglichen. | `use_imu_fusion:=true` beim Start |

Zurück in diesen Zustand kommt man jederzeit: die Zeile in der örtlichen Datei auskommentieren und neu starten.

## Voraussetzungen

- Roboterrechner mit Ubuntu 24.04 und ROS 2 Jazzy.
- Drei USB-Adapter: RS485 für den Antrieb, der Adapter des LiDAR, ein eigener RS485-Adapter für den IMU.
- Der Roboter steht frei, mindestens 1,5 m Platz nach vorn.
- Der Not-Halt-Schalter ist eingebaut und geprüft: Er nimmt den Motoren den Strom, auch wenn der Rechner läuft.
- Die HomeMy-App ist auf dem iPhone (`docs/runbooks/install-app-on-iphone.md`).
- Ein Karton, ein Maßband, zwei Böcke für die Räder.

## 1. Rechner einrichten (einmal)

```bash
git clone https://github.com/chris01-byte/HomeMy.git ~/HomeMy
```

```bash
cd ~/HomeMy && source /opt/ros/jazzy/setup.bash && rosdep update --rosdistro jazzy
```

```bash
rosdep install --from-paths src --ignore-src -y --rosdistro jazzy
```

Die Modbus-Bibliothek für den Antrieb. Unter Ubuntu 24.04 verlangt pip den Schalter am Ende oder eine virtuelle Umgebung:

```bash
python3 -m pip install --break-system-packages -r src/homemy_drivebase/requirements-modbus.txt
```

Der LiDAR-Treiber des Herstellers, unverändert, in einem eigenen Ordner:

```bash
src/homemy_lidar_bringup/vendor/build_vendor_driver.sh
```

HomeMy bauen:

```bash
colcon build --base-paths src
```

Zugriff auf die seriellen Geräte (danach einmal ab- und anmelden):

```bash
sudo usermod -aG dialout,input $USER
```

In jedem neuen Terminal gelten diese drei Zeilen:

```bash
source /opt/ros/jazzy/setup.bash
```

```bash
source ~/homemy_lidar_ws/install/setup.bash
```

```bash
source ~/HomeMy/install/setup.bash
```

## 2. Den drei Adaptern feste Namen geben (einmal)

Alle drei Adapter melden sich als `/dev/ttyUSB…`, in der Reihenfolge des Einsteckens. Ohne feste Namen könnte ein Programm am falschen Gerät sprechen. Deshalb: **immer nur einen Adapter einstecken**, seine Seriennummer lesen, die Regel eintragen.

```bash
udevadm info -a -n /dev/ttyUSB0 | grep -E 'idVendor|idProduct|ATTRS{serial}' | head -3
```

Die Vorlagen mit der weiteren Anleitung:

- Antrieb: `src/homemy_drivebase/config/99-homemy-drive.rules.example`
- LiDAR: `src/homemy_lidar_bringup/config/99-homemy-lidar.rules.example`
- IMU: `src/homemy_state_estimation/config/99-homemy-imu.rules.example`

Erwartet, wenn alle drei stecken:

```bash
ls -l /dev/homemy_drive /dev/homemy_lidar /dev/homemy_imu
```

Drei Zeilen, jede zeigt auf ein anderes `ttyUSB`. Sonst nicht weitergehen.

## 3. Controller koppeln (einmal)

Am Controller SHARE und PS gedrückt halten, bis die Leuchte schnell blinkt. Dann:

```bash
bluetoothctl
```

Darin nacheinander `scan on`, warten bis „Wireless Controller“ erscheint, dann `pair <Adresse>`, `trust <Adresse>`, `connect <Adresse>`, `quit`.

Erwartet:

```bash
ls /dev/input/js0
```

## 4. Gesperrt starten

Die örtliche Datei anlegen. Die Vorlage enthält nur Kommentare und schaltet nichts frei:

```bash
mkdir -p ~/.config/homemy && cp ~/HomeMy/src/homemy_bringup/config/robot_local.example.yaml ~/.config/homemy/robot_local.yaml
```

Starten (dieser Befehl gilt für alle weiteren Abschnitte):

```bash
ros2 launch homemy_bringup robot.launch.py bridge_address:=0.0.0.0 robot_params_file:=$HOME/.config/homemy/robot_local.yaml
```

Erwartet, in einem zweiten Terminal:

| Prüfung | Befehl | Ergebnis |
| --- | --- | --- |
| Antrieb gesperrt | `ros2 topic echo --once /homemy/drivebase/state_json` | `"dry_run": true` |
| LiDAR liefert | `ros2 topic hz /scan_unconfirmed` | etwa 10 Hz |
| Scan gesperrt | `ros2 topic hz /scan` | keine Nachrichten |
| IMU liefert | `ros2 topic echo --once /homemy/imu/status_json` | `"ready": true` |
| Freigabe zu | `ros2 topic echo --once /homemy/motion_gate/status_json` | `"open": false` |

In der App die Adresse `ws://<IP des Roboterrechners>:9090/` eintragen. Der Kartiermodus lässt sich einschalten. Das Steuerkreuz bewegt nichts. So muss es sein. Die Freigabe nennt dann als Grund `scan_stale`: Ihr fehlt der Scan.

## 5. LiDAR prüfen (ohne Motoren)

Einzelheiten: `src/homemy_lidar_bringup/README.md`. Der Roboter steht still, niemand steht daneben.

```bash
ros2 run homemy_lidar_bringup lidar_check stats --topic /scan_raw
```

Erwartet: etwa 10 Hz, wechselnde Strahlenzahl um 2160.

Richtung: einen Karton 0,5 bis 1 m genau vor den Roboter stellen, dann nach links tragen.

```bash
ros2 run homemy_lidar_bringup lidar_check target
```

Erwartet: vorn etwa 0°, beim Tragen nach links steigt der Winkel. Zeigt der Karton vorn zum Beispiel 90°, in der örtlichen Datei `yaw_offset_deg: -90.0` eintragen, neu starten, wiederholen. Sinkt der Winkel nach links, `laser_scan_dir: false` eintragen.

Eigene Streben:

```bash
ros2 run homemy_lidar_bringup lidar_check sectors
```

Erwartet: „Jeder feste Reflex liegt in der Maske, und jeder Maskensektor ist bestätigt.“ Sonst die Sektoren in der örtlichen Datei anpassen.

Erst wenn beides stimmt: `alignment_confirmed: true` eintragen und neu starten. Danach kommt `/scan` mit 10 Hz, und in der App erscheint im Kartiermodus die Karte der Umgebung, während der Roboter steht.

Das Steuerkreuz dabei nicht drücken. Solange der Antrieb gesperrt ist, meldet er die *befohlene* Bewegung als gefahren, obwohl der Roboter steht. Die Karte würde dadurch verschmieren.

## 6. IMU prüfen (ohne Motoren)

Einzelheiten: `src/homemy_state_estimation/README.md`.

```bash
ros2 topic echo --once /homemy/imu/yaw_rate_status_json
```

Erwartet nach etwa zehn Sekunden Stillstand: `"ready": true` und ein kleiner `bias_radps`.

Den Roboter von Hand eine volle Drehung nach links drehen. Erwartet: `gyro_yaw_deg` steigt um etwa 360. Sinkt der Wert, `yaw_sign: -1.0` eintragen. Bleibt er bei null, steht eine andere Achse senkrecht: `yaw_axis` anpassen.

Auch hier das Steuerkreuz nicht drücken. Der Vergleich mit den Rädern (`wheel_yaw_deg`) gilt erst nach Abschnitt 7; bis dahin melden die Räder Stillstand.

## 7. Antrieb in Betrieb nehmen

Einzelheiten und alle Schritte H0 bis H5: `contracts/hardware/drivebase-commissioning.md`, `src/homemy_drivebase/README.md`.

**7.1 Nur lesen (H1, H2).** Das Startprofil mit Strg-C beenden: Das Lese-Werkzeug braucht den Bus allein. Es sendet ausschließlich Leseabfragen.

```bash
ros2 run homemy_drivebase ess23_readonly_check --confirm-stack-stopped --samples 20
```

Erwartet: Beide Motoren antworten. Dann ein Rad von Hand genau eine Umdrehung drehen:

```bash
ros2 run homemy_drivebase ess23_readonly_check --confirm-stack-stopped --measure-wheel 1 --turns 1 --gear-ratio 10
```

Motor-IDs und die drei Encoderwerte in die örtliche Datei eintragen.

**7.2 Erste Drehung, Räder aufgebockt (H3).** Ab hier steht eine Person am Not-Halt.

1. Räder aufbocken. Beide Räder drehen frei.
2. In der örtlichen Datei `dry_run: false` und `allow_rs485: true` eintragen.
3. Startprofil starten, in der App den Kartiermodus einschalten.
4. Steuerkreuz kurz nach oben: Beide Räder müssen vorwärts drehen. Dreht eines rückwärts, `invert_left` oder `invert_right` umstellen.
5. Loslassen: Die Räder stehen innerhalb einer halben Sekunde.
6. Steuerkreuz halten und den Controller ausschalten: notieren, wie lange die Räder weiterdrehen.
7. Not-Halt-Schalter drücken, während die Räder drehen: Sie müssen sofort stehen. Schalter lösen.
8. Nur aufgebockt (Schritt H5): Steuerkreuz halten und den USB-Stecker des Antriebs-Adapters ziehen. **Erwartung prüfen, nicht voraussetzen:** Die Motoren haben, soweit bekannt, keine eigene Überwachung und drehen dann mit der letzten Drehzahl weiter. Mit dem Not-Halt-Schalter anhalten. Das Ergebnis im Vertrag festhalten, und im Handbuch der Motoren nachsehen, ob sich ein Stopp bei Kommunikationsausfall einstellen lässt.

**7.3 Auf dem Boden (H4).** Freie Fläche, niedrige Geschwindigkeit, Person am Not-Halt.

- Einen Meter geradeaus fahren und mit dem Maßband vergleichen: `wheel_radius_m` anpassen.
- Eine volle Drehung auf der Stelle: `wheel_separation_m` anpassen. Der IMU hilft dabei: `gyro_yaw_deg` gegen `wheel_yaw_deg`.
- Auf ein Hindernis zufahren: Der Roboter muss davor anhalten und rückwärts wieder freikommen.

## 8. Erste Kartierfahrt

Alle Geräte freigeschaltet, Person am Not-Halt. In der App den Kartiermodus einschalten, mit dem Steuerkreuz langsam durch den Raum fahren, Kartiermodus beenden, Karte speichern, einen Raum einzeichnen.

„Hinfahren“ erst, wenn Fahren und Anhalten in Abschnitt 7 sauber waren.

## Wenn etwas nicht stimmt

| Beobachtung | Ursache | Abhilfe |
| --- | --- | --- |
| LiDAR-Treiber startet alle drei Sekunden neu | `/dev/homemy_lidar` fehlt | Abschnitt 2 |
| `/scan_unconfirmed` kommt, `/scan` nicht | Sperre ist zu | gewollt bis Abschnitt 5 |
| IMU `"state": "getrennt"` | `/dev/homemy_imu` fehlt oder gehört einem anderen Gerät | Abschnitt 2 |
| IMU `reason: waiting_for_standstill` | Roboter wurde bewegt | zehn Sekunden ruhig stehen lassen |
| Kartiermodus an, Steuerkreuz bewegt nichts | Freigabe zu | Grund in `/homemy/motion_gate/status_json` lesen |
| Roboter fährt weiter, obwohl niemand drückt | Not-Halt-Schalter drücken | danach nicht weiterfahren, Ursache klären |

## Rückweg und Aufräumen

- Startprofil mit Strg-C beenden.
- Um den Roboter wieder ganz zu sperren: `dry_run: false`, `allow_rs485: true` und `alignment_confirmed: true` in der örtlichen Datei auskommentieren.
- Die gemessenen Werte in die Verträge unter `contracts/hardware/` übertragen (Datum, wer gemessen hat). Die örtliche Datei selbst bleibt auf dem Roboter.
