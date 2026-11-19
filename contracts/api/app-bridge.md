# App Bridge Contract

Status: proposed. Both sides are implemented and tested in simulation: the app in `ios/HomeMy/`, the robot side in `src/homemy_map_manager`, `src/homemy_room_manager`, `src/homemy_mapping_mode`, `src/homemy_mission`, and `src/homemy_bringup`. Nothing has run on robot hardware.
Owner: HomeMy platform and app.

## Scope

This contract defines what the HomeMy app and the robot exchange. It covers mapping mode, the stop request, the live map, the map store, the room overlay, and missions (drive to a room).

It does not define manual driving itself. Controller input, speed limits, and the stop on controller loss belong to `contracts/hardware/manual-drive.md`; whether a command reaches the drive is decided by the motion gate (`contracts/ros/motion-gate.md`). Both are proposed and tested in simulation only, so the mapping-mode part of this contract may only run in simulation or against the mock until the manual-drive commissioning steps have passed.

## Transport

- rosbridge v2 protocol over WebSocket, JSON text frames, default `ws://<robot>:9090/`.
- The app opens two connections: one for control (mapping mode, missions, and stop) and one for the map and rooms. Large map messages can then never delay a stop request.
- The app sends no motor commands and publishes to no velocity topic.
- The bridge listens on the loopback interface by default. Opening it to the network is an explicit launch argument.
- The bridge accepts only the topics in the table below: the app may publish to the four command topics and subscribe to the four status topics and `/map`. Services and actions are refused. A velocity command cannot pass the bridge.
- This version has no authentication and no encryption. By owner decision of 2026-11-19 the laboratory prototype runs without access control, on a trusted laboratory network only. Authentication is required before customer use, because the mapping-mode switch travels over this bridge.

## Topics

| Topic | Type | Direction | Purpose |
| --- | --- | --- | --- |
| `/homemy/mapping_mode/command_json` | `std_msgs/String` | app to robot | switch mapping mode, request stop |
| `/homemy/mapping_mode/status_json` | `std_msgs/String` | robot to app | mapping-mode state |
| `/map` | `nav_msgs/OccupancyGrid` | robot to app | live map |
| `/homemy/map_manager/command_json` | `std_msgs/String` | app to robot | save the map |
| `/homemy/map_manager/status_json` | `std_msgs/String` | robot to app | map store state |
| `/homemy/room_manager/command_json` | `std_msgs/String` | app to robot | create, change, delete rooms |
| `/homemy/room_manager/status_json` | `std_msgs/String` | robot to app | room overlay state |
| `/homemy/mission/command_json` | `std_msgs/String` | app to robot | drive to a room, cancel |
| `/homemy/mission/status_json` | `std_msgs/String` | robot to app | mission state |

Robot-internal topics of the mapping-mode manager, not reachable over the bridge:

| Topic | Type | Direction | Purpose |
| --- | --- | --- | --- |
| `/homemy/mapping_mode/active` | `std_msgs/Bool` | output, latched | mapping mode active, for the movement gate and mapping |
| `/homemy/lifecycle/state` | `std_msgs/String` | input, latched | lifecycle state name, republished at least every 3 s |
| `/joy` | `sensor_msgs/Joy` | input | controller activity |
| `/homemy/controller/link` | `std_msgs/Bool` | input | radio link of the controller, from the link watchdog |

Every `std_msgs/String` carries exactly one JSON object in `data`.

A `request_id` is 1 to 64 characters, starts with a letter or digit, and otherwise contains only letters, digits, `_`, `.`, `:`, and `-`.

## Mapping Mode

Mapping mode is new for HomeMy. Amadeus started its mapping stack from a terminal.

### Commands

```json
{"command": "enable", "request_id": "ios-mode-1"}
{"command": "disable", "request_id": "ios-mode-2"}
{"command": "stop", "request_id": "ios-stop-3"}
```

- `enable` switches mapping mode on. It never moves the robot. Motion additionally needs input from the connected controller.
- `disable` ends mapping mode in the normal way.
- `stop` ends mapping mode at once. It is always accepted, in every state, and is idempotent. The app repeats it until the status confirms `off`. The mode manager itself commands no motion; it publishes `off`, and the movement gate turns that into zero motion.

`stop` is a software request. It is not an emergency stop and does not replace any hardware stop path.

### Status

Published at least once per second and on every change, reliable and latched for late subscribers.

```json
{
  "schema_version": 1,
  "event": "status",
  "ok": true,
  "request_id": null,
  "message": "Mapping mode is off.",
  "mapping_mode": {
    "state": "off",
    "controller_connected": false,
    "auto_end_timeout_s": 300,
    "auto_end_remaining_s": null,
    "last_end_reason": null,
    "enable_block_reason": null
  },
  "time": 1731790000.0
}
```

| Field | Values |
| --- | --- |
| `event` | `status`, `enable_result`, `disable_result`, `stop_result` |
| `ok` | false when a command was refused; `message` says why |
| `request_id` | the command's ID on a result event, otherwise null |
| `state` | `off` or `active` |
| `controller_connected` | whether the wireless controller is connected |
| `auto_end_timeout_s` | seconds without controller input after which mapping mode ends by itself; greater than zero |
| `auto_end_remaining_s` | seconds left while `active`; null while `off` |
| `last_end_reason` | null, `app_disable`, `app_stop`, `inactivity_timeout`, `fault`, or `shutdown` |
| `enable_block_reason` | null, or the reason why `enable` would be refused now: `not_ready`, `fault`, or `shutting_down` |
| `time` | robot time in seconds |

### Rules for the Robot

- Mapping mode is `off` after every power-on and restart.
- `enable` is accepted only in the lifecycle states READY and READY_LIMITED. A missing lifecycle state, or one older than 3 s, counts as not ready. While active, the lifecycle state is OPERATING.
- A fault or a shutdown ends mapping mode at once.
- Mapping mode ends by itself after `auto_end_timeout_s` without controller input. The proposed value is 300 seconds.
- A lost app connection does not end mapping mode. The app is never part of the stop path.
- A disconnected controller does not end mapping mode by itself, but the robot must stand still while no controller is connected; the motion gate enforces this. The controller counts as connected while the radio-link watchdog reported the link up within 0.5 s (`contracts/hardware/manual-drive.md`). Repeated `/joy` messages do not count, because the joystick driver keeps repeating its last state after a silent radio loss.
- While mapping mode is active the growing map is published on `/map`. After it ends, the last map stays available on `/map` and in the map store status until it is saved or a new mapping run begins.

### Rules for the App

- A status older than 2.5 seconds is unknown.
- `enable` is offered only when the control connection is up, the status is fresh, the state is `off`, and `enable_block_reason` is null.
- The stop button is offered whenever the control connection is up and the state is `active` or unknown.
- Saving the map is offered only while a fresh status confirms `off`.

## Map Store and Room Overlay

The JSON payloads are unchanged from the source robot at roboter_ws commit `05439c7` (schema version 1). Only the topic names are HomeMy names:

| Source topic | HomeMy topic |
| --- | --- |
| `/robot_map_manager/command_json` | `/homemy/map_manager/command_json` |
| `/robot_map_manager/status_json` | `/homemy/map_manager/status_json` |
| `/semantic_map/command_json` | `/homemy/room_manager/command_json` |
| `/semantic_map/status_json` | `/homemy/room_manager/status_json` |

The payload key `semantic_map` in the room overlay status keeps its source name.

Commands the app sends:

- map store: `save` with the fixed map name `wohnung`. HomeMy keeps one map for the whole home.
- room overlay: `upsert_room` and `delete_room`, each with `request_id`, the current `map_fingerprint`, and `base_revision`.

The app binds rooms fail-closed: live map, map store, and room overlay must report the same map fingerprint, otherwise room editing stays locked.

Not yet covered: saving a second map after rooms exist, and moving rooms to a new map version. The owner accepted this limit for the prototype on 2026-11-19.

## Missions

V1 knows one mission: drive to a room. The robot drives to the room's stored navigation goal. The motion gate decides whether navigation commands reach the drive (`contracts/ros/motion-gate.md`).

### Commands

```json
{"command": "go_to_room", "room_id": "kueche", "request_id": "ios-go-1"}
{"command": "cancel", "request_id": "ios-cancel-2"}
```

- `go_to_room` names a room of the room overlay by `room_id` (or, for tools, by `room` name). The room must have a navigation goal.
- `cancel` ends the running mission. It is always accepted and idempotent. The app repeats it until the status no longer reports `running`, for at most four seconds. The app's stop button sends `cancel` as well as the mapping-mode `stop`.

### Status

Published at least twice per second and on every change, reliable and latched.

```json
{
  "schema_version": 1,
  "event": "status",
  "ok": true,
  "request_id": null,
  "message": "Auftrag läuft.",
  "mission": {
    "state": "running",
    "command": "go_to_room",
    "room_id": "kueche",
    "room_name": "Küche",
    "phase": "driving",
    "attempt": 1,
    "max_attempts": 3,
    "distance_remaining_m": 2.4,
    "result": null
  },
  "start_block_reason": "busy",
  "time": 1731790000.0
}
```

| Field | Values |
| --- | --- |
| `event` | `status`, `go_to_room_result`, `cancel_result`, `command_result` (a refused, malformed command) |
| `mission.state` | `idle`, `running`, `succeeded`, `failed`, `canceled` |
| `mission.phase` | while running: `starting`, `driving`, `waiting_retry`; afterwards `arrived`, `failed`, `canceled` |
| `mission.result` | null, `arrived`, `app_cancel`, `mapping_started`, `localization_lost`, `navigation_failed:<code>`, `goal_rejected`, `lifecycle_fault`, `lifecycle_shutting_down` |
| `start_block_reason` | null when `go_to_room` would be accepted now; otherwise `busy`, `mapping_active`, `not_ready`, `no_map`, `rooms_not_bound`, `not_localized`, `navigation_unavailable`; on a refused `go_to_room_result` also `room_invalid` |

In the idle state `command`, `room_id`, `room_name`, `phase`, and `result` are null, and `attempt` and `max_attempts` are 0.

### Rules for the Robot

- One mission at a time.
- `go_to_room` is accepted only with mapping mode off, a lifecycle state of READY or READY_LIMITED, a trusted position on the saved map (`/homemy/localization/ready`), rooms bound to exactly the loaded map (same fingerprint), and navigation available.
- A failed drive is a pause: the robot waits 3 s and tries again, up to three attempts. Only then the mission ends as `failed`, and the robot is ready for the next command.
- A lost position stops the robot through the motion gate; the mission waits up to 15 s for it to come back, then ends as `failed` with `localization_lost`.
- Starting mapping mode cancels a running mission. A fault or shutdown ends it.
- After a restart no mission continues by itself.

### Rules for the App

- A mission status older than 2.5 seconds is unknown.
- "Drive there" is offered only for a room with a navigation goal, when the control connection is up, the mission status is fresh, no mission is running, and `start_block_reason` is null.
- Cancel is offered while a mission runs or its state is unknown, once the robot has reported any mission status.

## Failure Behavior

- Missing, malformed, or stale status never enables an action in the app. It only disables.
- An unanswered command is reported to the user and is not repeated automatically, except `stop`.
- The robot must not depend on the app for any safety function.

## Validation

- `ios/HomeMy/Tools/mock_rosbridge.py` implements this contract without ROS, with synthetic data only.
- Swift tests cover frame encoding, status decoding, rejection of invalid payloads, and the app rules above, for mapping mode and missions. Python tests cover the mock, including missions.
- The robot side has unit and ROS-level tests per package, and two end-to-end tests that talk to the simulation over the real bridge with the app's frames. `test_app_bridge_e2e.py`: mapping run, saving, rooms, stop, the bridge allowlist, the automatic end, a disconnected controller, and a lifecycle fault. `test_drive_sim_e2e.py`: a real mapping run in the test stand, saving, rooms, drive to a room, cancel, refusal while mapping, and restarts with a correct and with a wrong stored position.
- Frames recorded from that test are decoded by the app's own Swift code (`ios/HomeMy/HomeMyTests/BackendFixtureTests.swift`); the app computes the same map fingerprint as the map store and unlocks room editing.
- Nothing has run on robot hardware. Simulation results are not robot acceptance.

## Rollback

Remove the bridge from robot composition. The app then shows no connection and offers no action. Removing the mapping-mode manager must leave the movement gate closed.
