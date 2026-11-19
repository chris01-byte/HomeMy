# homemy_mission

Auftragssteuerung von HomeMy. Version 1 kennt einen Auftrag: **zu einem Raum fahren**. Dazu kommt **Abbrechen**. Die Schnittstelle zur App steht in [`contracts/api/app-bridge.md`](../../contracts/api/app-bridge.md), Abschnitt Missions.

**Stand:** in der Simulation getestet. Am Roboter nie gelaufen.

## Ablauf

1. Die App sendet `go_to_room` mit der Raum-ID.
2. Der Knoten prüft: kein Auftrag läuft, Kartiermodus aus, Roboter bereit, Standort sicher, Räume gehören zur geladenen Karte, Navigation bereit. Fehlt etwas, lehnt er ab und nennt den Grund.
3. Er löst das Fahrziel des Raums auf. Der Code dafür ist aus Amadeus übernommen (`semantic_room_goal.py`, Commit `05439c7`), samt Tests.
4. Er schickt das Ziel an Nav2 (`navigate_to_pose`) mit dem Verhaltensbaum ohne Recovery aus `homemy_navigation`.
5. Er meldet `/homemy/mission/drive_active`. Nur damit öffnet die Bewegungsfreigabe die Navigation.

## Selbstheilung

- Scheitert eine Fahrt, wartet der Knoten 3 s und versucht es erneut, höchstens dreimal. Erst dann endet der Auftrag als „nicht erfüllt“, und der Roboter ist wieder bereit.
- Ist der Standort nicht mehr sicher, hält die Bewegungsfreigabe den Roboter an. Der Auftrag wartet bis zu 15 s, dass der Standort zurückkommt.
- Beginnt der Kartiermodus, wird der Auftrag abgebrochen. Ein Fehler oder das Ausschalten beenden ihn.
- Nach einem Neustart läuft kein Auftrag von selbst weiter.

## Schnittstellen

| Richtung | Topic | Typ |
| --- | --- | --- |
| Eingang | `/homemy/mission/command_json` | `std_msgs/String` |
| Eingang | `/homemy/room_manager/status_json`, `/homemy/localization/status_json`, `/homemy/localization/ready`, `/homemy/mapping_mode/active`, `/homemy/lifecycle/state` | |
| Ausgang | `/homemy/mission/status_json` | `std_msgs/String`, latched |
| Ausgang | `/homemy/mission/drive_active` | `std_msgs/Bool`, latched |
| Aktion | `/navigate_to_pose` | `nav2_msgs/action/NavigateToPose` |
