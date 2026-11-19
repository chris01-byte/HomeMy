# homemy_bringup

Startprofile für HomeMy.

| Profil | Startet | Wofür |
| --- | --- | --- |
| `app_backend.launch.py` | Kartenspeicher, Raumverwaltung, Kartiermodus, App-Brücke | die Roboterseite der App |
| `app_sim.launch.py` | dasselbe plus Ersatz für SLAM und Controller aus `homemy_simulation` und die Überbrückung des Roboterzustands | die App ohne Hardware ausprobieren und testen (Stufe S1) |
| `drive_sim.launch.py` | die Roboterseite der App plus Robotermodell, LiDAR-Maske, Bewegungsfreigabe, Controller-Profil, slam_toolbox, Lokalisierungs-Manager mit AMCL, Nav2, Auftragssteuerung, und den Prüfstand mit simuliertem Bediener | Fahren, Kartieren und „Fahre zu Raum“ in der Simulation (Stufe S2) |

Keines der Profile startet einen echten Treiber. Nur in `drive_sim` gibt es einen Fahrbefehl, und der geht an den simulierten Antrieb.

## Fahren und Kartieren in der Simulation

```bash
ros2 launch homemy_bringup drive_sim.launch.py operator_route:=true
```

Dann in der App den Kartiermodus einschalten. Der simulierte Bediener fährt die Kartierroute durch alle vier Räume der Testwohnung; slam_toolbox baut dabei die Karte, die die App live zeigt. Nach dem Ausschalten des Kartiermodus lässt sie sich speichern. Ohne `operator_route` ist der simulierte Controller verbunden, drückt aber nichts.

Nach dem Speichern schaltet der Roboter auf die gespeicherte Karte um. In der App lassen sich dann Räume mit Fahrziel anlegen und mit „Hinfahren“ anfahren.

Weitere Argumente: `world_file`, `start_pose` (Startlage `[x, y, yaw]` in der Welt, für Neustarts), `bridge_address`, `bridge_port`, `storage_root`, `auto_end_timeout_s`.

## Die App gegen die Simulation laufen lassen

```bash
colcon build --base-paths src
source install/setup.bash
ros2 launch homemy_bringup app_sim.launch.py
```

Danach in der App im iOS-Simulator `ws://127.0.0.1:9090/` eintragen. Karten und Räume landen dabei in `~/.local/share/homemy-sim`, getrennt von echten Karten.

Für ein iPhone im selben Labornetz muss die Brücke ausdrücklich geöffnet werden:

```bash
ros2 launch homemy_bringup app_sim.launch.py bridge_address:=0.0.0.0
```

Weitere Argumente: `bridge_port`, `storage_root`, `auto_end_timeout_s`, `controller_driving`, `initial_map`.

## Die App-Brücke

- Sie lauscht standardmäßig nur auf `127.0.0.1`.
- Sie hat keine Anmeldung und keine Verschlüsselung. Nur in einem vertrauenswürdigen Labornetz öffnen.
- Sie lässt nur die Topics des App-Vertrags zu. Senden darf die App nur auf die drei Befehls-Topics, lesen nur die drei Status-Topics und `/map`. Dienste und Aktionen sind gesperrt. Ein Fahrbefehl über die Brücke ist damit nicht möglich.

## Ende-zu-Ende-Tests

`test/test_drive_sim_e2e.py` startet `drive_sim.launch.py` dreimal und fährt die ganze Kartierroute und mehrere Aufträge durch den echten Code (etwa sechs Minuten). Geprüft werden:

1. Bei ausgeschaltetem Kartiermodus bewegt der gedrückte Controller nichts.
2. Lässt die Person das Steuerkreuz los, steht der Roboter; drückt sie wieder, fährt er weiter. Wird der Controller ausgeschaltet, hält der Roboter innerhalb einer Sekunde und nach weniger als 15 cm; der Kartiermodus bleibt aktiv.
3. Not-Halt gedrückt: Stillstand; gelöst: weiter.
4. Die Route endet ohne Berührung im Schlafzimmer.
5. Die Karte von slam_toolbox stimmt mit der Welt überein: nach starrer Ausrichtung liegen 95 % der Wandzellen innerhalb von 5 cm und keine weiter als 15 cm entfernt, die ganze Karte ist um höchstens 2° verdreht, mindestens 85 % der freien Fläche sind bekannt.
6. Die Karte wird mit der Nachricht der App gespeichert, mit dem Fingerabdruck der Live-Karte.
7. Über die Brücke kommt kein Fahrbefehl herein; die Bewegungsfreigabe bleibt der einzige Sender auf `/cmd_vel`.
8. Nach dem Speichern schaltet die Lokalisierung auf die gespeicherte Karte mit AMCL um und meldet „Standort sicher“; Startlage ist die letzte SLAM-Lage.
9. Drei Räume werden mit den Nachrichten der App angelegt; „Fahre zu Wohnzimmer“ führt vom Schlafzimmer durch Flur und zwei Türen ins Wohnzimmer, ohne Berührung, höchstens 35 cm neben dem Fahrziel.
10. Eine abgebrochene Fahrt hält den Roboter an; während des Kartiermodus wird eine Fahrt abgelehnt.
11. Neustart dort, wo der Roboter stand: Er übernimmt die gesicherte Lage und fährt ins Schlafzimmer.
12. Neustart, nachdem der Roboter heimlich in die Küche getragen wurde: Er traut der gesicherten Lage nicht und lehnt eine Fahrt zunächst ab („nicht lokalisiert“). Dann findet er sich im Stand über die Suche in der ganzen Karte wieder, auf höchstens 30 cm genau, und fährt ins Wohnzimmer.

`test/test_app_bridge_e2e.py` startet `app_sim.launch.py` in einem eigenen Prozess und spricht über einen WebSocket mit genau den Nachrichten, die die App sendet. Geprüft werden:

1. Kartierfahrt: einschalten, Karte wächst, beenden.
2. Karte speichern, Räume werden bearbeitbar, Raum mit Fahrziel anlegen.
3. Stopp, auch doppelt.
4. Die Brücke verweigert `/cmd_vel`, `/rosout` und Dienstaufrufe.
5. Automatisches Ende ohne Controller-Eingabe.
6. Getrennter Controller wird gemeldet.
7. Ein Fehler im Lebenszyklus beendet den Kartiermodus und sperrt das Einschalten.

```bash
colcon test --base-paths src --packages-select homemy_bringup
```

Mit `HOMEMY_RECORD_FIXTURES=<Ordner>` schreiben beide Tests die empfangenen Nachrichten in diesen Ordner. So entstanden die Dateien in `ios/HomeMy/HomeMyTests/Fixtures/backend/`, mit denen die Swift-Tests der App prüfen, dass sie die echten Antworten des Roboters versteht. Die Auftragsnachrichten (`mission_*.json`) stammen aus dem Fahrtest:

```bash
HOMEMY_RECORD_FIXTURES=$PWD/ios/HomeMy/HomeMyTests/Fixtures/backend \
  python3 -m pytest src/homemy_bringup/test/test_app_bridge_e2e.py src/homemy_bringup/test/test_drive_sim_e2e.py
```
