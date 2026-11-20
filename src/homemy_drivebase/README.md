# homemy_drivebase

Treiber für den Fahrantrieb von HomeMy: zwei ESS23-RS an einem RS485-Bus (Modbus RTU). Der Vertrag steht in [`contracts/hardware/drivebase-commissioning.md`](../../contracts/hardware/drivebase-commissioning.md).

> Übernommen aus `src/base_hardware` in chris01-byte/Roboter_ws, Commit `05439c7` (Amadeus). Die Logik ist unverändert. Geändert sind Namen, Vorgabewerte und Texte. Das Lese-Werkzeug stammt aus `tools/kartierung/encoder_position_pruefen.py`.

**Stand:** In der Simulation fährt der Treiber simulierte Motoren über einen simulierten RS485-Bus. An den HomeMy-Motoren ist er nie gelaufen.

## Sichere Voreinstellung: Der Treiber bewegt nichts

Mit der mitgelieferten Konfiguration rechnet der Treiber nur. Er öffnet den RS485-Adapter nicht und sendet nichts an die Motoren. Drei Sperren liegen hintereinander:

| Sperre | Parameter | Voreinstellung |
| --- | --- | --- |
| Trockenlauf | `dry_run` | `true` |
| RS485-Freigabe | `allow_rs485` | `false` |
| Encoderwerte bekannt | `encoder_counts_per_motor_revolution`, `encoder_expected_segment`, `encoder_expected_resolution` | alle `0`: gesperrt |

Ein Motorlauf braucht alle drei. Die Werte kommen aus den Inbetriebnahme-Schritten H1 bis H3 und aus einer ausdrücklichen Freigabe durch eine Person am Roboter.

Im Trockenlauf meldet der Treiber auf `/odom` die *befohlene* Bewegung, nicht eine gemessene. Der Roboter steht dabei.

## Was der Treiber tut

- Er nimmt `/cmd_vel` an. Dieses Topic kommt nur von der Bewegungsfreigabe.
- Er rechnet die Radgeschwindigkeiten und Motordrehzahlen aus (Getriebe 10:1).
- Bleibt `/cmd_vel` 0,25 s aus, stoppt er beide Motoren.
- NaN oder unendliche Werte verwirft er und stoppt.
- Die Odometrie kommt aus den absoluten Encoderzählern der Motoren, nicht aus den Sollwerten. Bremswege und kurze Buslücken gehen so nicht verloren.
- Unplausible Zählersprünge, veraltete Rückmeldungen und Busfehler sperren die Fahrt und stoppen. Nach einem Busfehler baut er die Verbindung neu auf und beginnt mit einem Stopp.
- Er meldet seinen Zustand auf `/homemy/drivebase/state_json` und liefert `odom → base_link`, solange keine IMU-Fusion läuft.

## Bekannte Lücke: Die Motoren haben keine eigene Überwachung

Soweit bekannt, fährt ein ESS23-RS mit der zuletzt befohlenen Drehzahl weiter, bis er einen Stopp bekommt. Stürzt der Treiber ab oder fällt der USB-Adapter aus, während der Roboter fährt, hält ihn die Software nicht mehr an. Dann bleibt der Not-Halt-Schalter. Ob die Motoren eine Abschaltung bei Kommunikationsausfall anbieten, wird in H5 am Handbuch und am Motor geprüft.

## Inbetriebnahme in Stufen

Die Stufen H0 bis H5 stehen im Vertrag. Kurz:

1. **H1, nur lesen:** Adapter und Motor-IDs finden, Register lesen. Kein Motorbefehl.

   ```bash
   ros2 run homemy_drivebase ess23_readonly_check --confirm-stack-stopped
   ```

   Das Werkzeug sendet ausschließlich Leseabfragen.
2. **H2, nur lesen:** Zähler je Motorumdrehung bestimmen, Rad von Hand drehen:

   ```bash
   ros2 run homemy_drivebase ess23_readonly_check --confirm-stack-stopped --measure-wheel 1 --turns 1 --gear-ratio 10
   ```

3. **H3, Räder aufgebockt, Person am Not-Halt:** erst jetzt `dry_run: false` und `allow_rs485: true`. Drehrichtung prüfen und `invert_left`/`invert_right` setzen.
4. **H4:** Strecke und Drehung gegen ein Maßband kalibrieren (`wheel_radius_m`, `wheel_separation_m`).
5. **H5:** Fehlerfälle: Bus ziehen, Treiber beenden, Not-Halt.

## Einrichtung am Roboterrechner

Die Modbus-Bibliothek kommt über pip, in genau der Version, mit der der Treiber an Amadeus lief:

```bash
python3 -m pip install -r src/homemy_drivebase/requirements-modbus.txt
```

Unter Ubuntu 24.04 verlangt pip dafür entweder eine virtuelle Umgebung oder den Schalter `--break-system-packages`. Welcher Weg am Roboterrechner gilt, wird bei dessen Einrichtung festgelegt.

Der RS485-Adapter bekommt über eine udev-Regel den festen Namen `/dev/homemy_drive`. Vorlage: `config/99-homemy-drive.rules.example`.

## Tests

- 74 Tests ohne ROS und ohne Hardware, von Amadeus übernommen: Sicherheitsverdrahtung des Knotens, Encoder-Odometrie mit Überlauf und Sprüngen, Lese-Werkzeug.
- In `homemy_bringup` fährt der Treiber im Ende-zu-Ende-Test simulierte Motoren: Kartierfahrt, Fahrten zu Räumen, Neustarts.

```bash
colcon test --packages-select homemy_drivebase
```
