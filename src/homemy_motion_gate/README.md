# homemy_motion_gate

Die eine Stelle auf HomeMy, die Fahrbefehle zum Antrieb durchlässt. Der Vertrag steht in [`contracts/ros/motion-gate.md`](../../contracts/ros/motion-gate.md).

**Stand:** in der Simulation getestet. Am Roboter nie gelaufen. Das zweite, elektrische Bewegungs-Gate der PMU gibt es noch nicht.

## Was der Knoten tut

Er entscheidet 20-mal je Sekunde neu und sendet auf `/cmd_vel` immer einen Befehl: den freigegebenen oder null.

| Betriebsart | Befehle kommen von | zusätzlich nötig |
| --- | --- | --- |
| Kartieren (`/homemy/mapping_mode/active`) | Controller, `/homemy/cmd_vel/teleop` | nichts weiter: gedrückt fährt, losgelassen oder stumm steht |
| Fahr-Auftrag (`/homemy/mission/drive_active`) | Navigation, `/homemy/cmd_vel/nav` | Standort sicher (`/homemy/localization/ready`) |

Immer nötig: genau eine Betriebsart aktiv, Lebenszyklus READY, READY_LIMITED oder OPERATING, Not-Halt frisch als gelöst gemeldet, frischer Scan, frischer Befehl. Fehlt etwas oder ist es veraltet, bleibt das Gate zu. Nichts davon rastet ein: Sobald die Bedingungen wieder erfüllt sind, geht es weiter.

Die Geschwindigkeit wird auf die Grenzen der Betriebsart begrenzt, beim Kartieren 0,20 m/s und 0,70 rad/s.

## Hindernisschutz

Der Knoten fährt den Umriss des Roboters (aus `homemy_description/config/geometry.yaml`) eine Sekunde entlang des Befehls voraus. Käme dabei ein Scanpunkt näher als 5 cm an den Umriss und näher als jetzt, wird der Befehl gesperrt. Wegfahren von einem Hindernis bleibt deshalb erlaubt, auch Zurücksetzen nach einem Halt. Nach einer Sperre geht es erst weiter, wenn der Schutz 0,5 s lang frei war.

Bekannte Lücken: In den blinden Sektoren des LiDAR merkt sich der Schutz nichts. Hindernisse unter der Scanebene von 164 mm und auf Armhöhe sieht er nicht. Die Tiefe der OAK ist noch kein Eingang.

## Ausgaben

| Topic | Typ | Inhalt |
| --- | --- | --- |
| `/cmd_vel` | `geometry_msgs/Twist` | Befehl an den Antrieb, 20 Hz |
| `/homemy/motion_gate/status_json` | `std_msgs/String`, latched | Betriebsart, offen oder zu, Gründe |
