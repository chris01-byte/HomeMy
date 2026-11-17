# homemy_mapping_mode

Schaltet den Kartiermodus von HomeMy. Die App schaltet ihn ein und aus, der Roboter beendet ihn bei Fehler, beim Ausschalten oder nach einer Zeit ohne Controller-Eingabe von selbst. Die Regeln stehen in [`contracts/api/app-bridge.md`](../../contracts/api/app-bridge.md).

Der Knoten bewegt nichts. Er sendet keinen Fahrbefehl und öffnet keinen Antrieb. Er meldet nur, ob der Kartiermodus aktiv ist. Dass „aus“ zu Stillstand führt, ist Aufgabe der Bewegungsfreigabe, die es noch nicht gibt.

## Schnittstellen

| Richtung | Topic | Typ | Zweck |
| --- | --- | --- | --- |
| Eingang | `/homemy/mapping_mode/command_json` | `std_msgs/String` | `enable`, `disable`, `stop` aus der App |
| Eingang | `/joy` | `sensor_msgs/Joy` | Controller: Verbindung und Eingabe |
| Eingang | `/homemy/lifecycle/state` | `std_msgs/String` | Zustand des Roboters, z. B. `READY` |
| Ausgang | `/homemy/mapping_mode/status_json` | `std_msgs/String` | Status für die App, latched, alle 0,5 s und bei jeder Änderung |
| Ausgang | `/homemy/mapping_mode/active` | `std_msgs/Bool` | Kartiermodus aktiv, für Bewegungsfreigabe und Kartierung |

## Regeln

- Nach jedem Start ist der Kartiermodus aus.
- Einschalten geht nur, wenn der Roboter `READY` oder `READY_LIMITED` meldet. Fehlt die Meldung oder ist sie älter als 3 s, gilt der Roboter als nicht bereit.
- `FAULT` oder `SHUTTING_DOWN` beenden einen aktiven Kartiermodus sofort.
- `stop` wird in jedem Zustand angenommen und darf beliebig oft wiederholt werden.
- Nach 300 s ohne Controller-Eingabe endet der Kartiermodus von selbst. Jede Eingabe am Steuerkreuz, an einem Stick oder einer Taste setzt die Zeit zurück.
- Ein getrennter Controller beendet den Kartiermodus nicht, die Zeit läuft aber weiter.
- Ein Verbindungsabbruch der App hat keine Wirkung.

## Annahmen, die am Roboter zu prüfen sind

- **Controller-Erkennung:** Der Controller gilt als verbunden, solange `/joy` höchstens 0,5 s alt ist. Das setzt voraus, dass `joy_node` den Zustand bei verbundenem Controller fortlaufend sendet (`autorepeat_rate`). Am HomeMy-Rechner mit dem DualShock prüfen.
- **Lebenszyklus:** Den Lebenszyklus-Manager gibt es noch nicht. Er muss seinen Zustand latched und mindestens alle 3 s senden. In der Simulation übernimmt das `homemy_simulation`.

## Parameter

Stehen in `config/homemy_mapping_mode.yaml`. Die wichtigsten: `auto_end_timeout_s` (300), `controller_timeout_s` (0,5), `controller_deadzone` (0,2), `lifecycle_timeout_s` (3).

## Tests

```bash
colcon test --base-paths src --packages-select homemy_mapping_mode
```

- `test/test_mapping_mode_core.py`: die reine Logik ohne ROS. Ein Hilfsprüfer bildet die Gültigkeitsprüfung der App nach.
- `test/test_mapping_mode_node.py`: der echte Knoten mit ROS 2 (Topics, QoS, Zeiten).
- Den Weg über die Brücke prüft der Ende-zu-Ende-Test in `homemy_bringup`.
