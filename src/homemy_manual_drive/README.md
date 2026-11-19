# homemy_manual_drive

Fahren mit dem Funk-Controller DualShock 4 (CUH-ZCT2E) beim Kartieren. Der Vertrag steht in [`contracts/hardware/manual-drive.md`](../../contracts/hardware/manual-drive.md).

**Stand:** in der Simulation und mit einem nachgebildeten Eingabegerät getestet. Am echten Controller und am Roboter nie gelaufen.

## Funküberwachung `controller_link`

Der Joystick-Treiber von ROS (`joy_node`) wiederholt den letzten Zustand 20-mal je Sekunde, solange Linux den Controller als Gerät führt. Reißt die Funkverbindung ab, ohne dass sich der Controller abmeldet, behält Linux das Gerät noch eine Weile. In dieser Zeit wiederholt der Treiber zum Beispiel „vorwärts“ weiter. Die `/joy`-Nachrichten beweisen also nicht, dass der Controller noch da ist.

Der DualShock 4 sendet bei bestehender Funkverbindung laufend Berichte, auch wenn niemand etwas drückt. Linux stellt seine Bewegungssensoren als eigenes Gerät bereit („Wireless Controller Motion Sensors“), das mit jedem Funkpaket einen Bericht liefert. `controller_link` liest dieses Gerät und meldet auf `/homemy/controller/link` (`std_msgs/Bool`, 20 Hz), ob in den letzten 0,15 s ein Bericht kam. Die Bewegungsfreigabe fährt beim Kartieren nur, solange diese Meldung frisch und wahr ist.

Sind zwei Controller gekoppelt, kann der Knoten sie nicht unterscheiden und meldet „getrennt“.

Der Dienst braucht Lesezugriff auf `/dev/input/event*` (Gruppe `input`).

## Controller-Profil

`launch/manual_drive.launch.py` startet `joy_node`, `teleop_twist_joy` und `controller_link`. Die Befehle gehen an `/homemy/cmd_vel/teleop`, also an die Bewegungsfreigabe, nie direkt an den Antrieb.

| Taste | Wirkung |
| --- | --- |
| Steuerkreuz hoch/runter | vorwärts/rückwärts, 0,12 m/s |
| Steuerkreuz links/rechts | drehen, 0,40 rad/s |
| R1 gehalten | schneller: 0,20 m/s und 0,70 rad/s |

Übernommen aus Amadeus (`src/robot_bringup/config/teleop_joy.yaml`, Commit `05439c7`): Steuerkreuz statt Stick, Totzone 0,20, kein Totmann-Knopf (Entscheidung des Projektinhabers). Achsen- und Tastennummern werden in Schritt M1 am HomeMy-Rechner bestätigt.
