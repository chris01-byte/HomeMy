# homemy_bringup

Startprofile für HomeMy.

| Profil | Startet | Wofür |
| --- | --- | --- |
| `app_backend.launch.py` | Kartenspeicher, Raumverwaltung, Kartiermodus, App-Brücke | die Roboterseite der App |
| `app_sim.launch.py` | dasselbe plus Ersatz für SLAM, Controller und Lebenszyklus aus `homemy_simulation` | die App ohne Hardware ausprobieren und testen |

Keines der Profile startet einen Treiber oder sendet einen Fahrbefehl.

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

## Ende-zu-Ende-Test

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

Mit `HOMEMY_RECORD_FIXTURES=<Ordner>` schreibt der Test die empfangenen Nachrichten in diesen Ordner. So entstanden die Dateien in `ios/HomeMy/HomeMyTests/Fixtures/backend/`, mit denen die Swift-Tests der App prüfen, dass sie die echten Antworten des Roboters versteht:

```bash
HOMEMY_RECORD_FIXTURES=$PWD/ios/HomeMy/HomeMyTests/Fixtures/backend \
  python3 -m pytest src/homemy_bringup/test/test_app_bridge_e2e.py
```
