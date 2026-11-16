# Manual Mapping, Map Store, Room Overlay, and App Transfer Candidates

Status: the app is ported to `ios/HomeMy/` and tested against a mock; gamepad driving, map store, and room overlay remain proposed with no HomeMy code.

## 1. Source

- Repository: chris01-byte/Roboter_ws.
- Immutable commit: `05439c7a13d7a92e69b9eb4663e3a2a1b44626a1`, the general HomeMy transfer baseline. Later roboter_ws `main` adds only CAD files.

| Capability | Source path |
| --- | --- |
| Gamepad driving | `src/robot_bringup/launch/teleop_joy.launch.py`, `src/robot_bringup/config/teleop_joy.yaml` |
| Map store | `src/robot_map_manager/` |
| Room overlay | `src/semantic_map_manager/` |
| App | `ios/Robotersteuerung/` (SwiftUI, iOS 16 or later) |
| Bridge composition | `rosbridge_server` in `src/robot_bringup/launch/app_mapping.launch.py` |

## 2. HomeMy Intent and Destination

Implements `docs/decisions/2026-11-16-manual-mapping-and-app-room-management.md`.

| Capability | Planned destination |
| --- | --- |
| Gamepad driving | manual-drive profile in a future `homemy_bringup`, under a HomeMy manual-drive contract |
| Map store | future `src/homemy_map_manager/` |
| Room overlay | future `src/homemy_room_manager/` |
| App | future HomeMy app, starting from the map, room, connection, and status parts of the Amadeus app |

New for HomeMy, with no source to adapt: a mapping-mode switch in the app and a robot-side mode manager that accepts it. The source started its mapping stack from a terminal. The HomeMy controller link is wireless.

## 3. Interface and Incompatible Assumptions

Source behavior worth keeping:

- **Map store:** receives `/map`, keeps only the latest valid map, saves only on an explicit command, writes atomically into immutable versions with a SHA-256 fingerprint, and validates map names. It has no drive, navigation, or mission interface.
- **Room overlay:** rooms are polygons with ID, name, optional colour, and optional navigation goal. Every write needs the current map fingerprint and base revision. The overlay locks itself when the map manager is silent or the fingerprint changes. It has no drive interface; a navigation goal is stored data, never a command.
- **App:** connects over a rosbridge WebSocket, shows the map, the robot pose, and a three-step room editor (draw area, save, optional goal). It sends no direct motor commands.
- **Gamepad driving:** `joy` plus `teleop_twist_joy`, commands sent through the collision path instead of directly to the base, a 20 Hz repeat for the base watchdog, slow default speeds, and a faster mode on a second button.
- **Controller assignment:** HomeMy uses the same DualShock model, so the source assignment is kept by owner decision: direction pad for driving and turning, R1 for the faster mode, and no dead-man button (`require_enable_button: false`). The axis and button numbers must be checked once on the HomeMy computer.

Not portable as is:

- the second control branch that sends directly to the base and bypasses the collision monitor;
- the source command topic chain (`cmd_vel_smoothed`, `nav2_collision_monitor`, VL53 sources), which HomeMy replaces with its own movement gate and obstacle protection;
- storage paths and names containing `amadeus`, the app's default bridge host, and every map, room, or home data file;
- the app's mission, exploration, grasping, and AI views, and the browser app (`src/smartphone_gui/`), which centres on missions and exploration;
- the unauthenticated bridge on the local network as a customer default.

## 4. Tests and Results Actually Run

App, 2026-11-16, on Linux with Swift 6.2 and Python 3:

- baseline before any change: the 44 source Swift tests and 7 source mock tests passed unchanged;
- after the port: 63 Swift tests passed (31 kept map and room tests, 32 new mapping-mode tests), and 19 Python mock tests passed, including a flow over a real WebSocket connection.

The SwiftUI views and the two connection services cannot be compiled on Linux. Their build is checked by the macOS job in `.github/workflows/app-checks.yml`. No test has run on an iPhone or against a robot.

Gamepad driving, map store, and room overlay: none for HomeMy. Source review only.

At the source commit: 51 Python tests for the map store, 51 for the room overlay, and 44 Swift tests in the app (counted, not executed here). The gamepad launch has no automated tests. Source results are regression evidence, not HomeMy acceptance.

## 5. Hardware and Safety Impact

The map store, room overlay, and app have no motion effect. Gamepad driving moves the robot and must not be adapted before a HomeMy manual-drive contract exists and the drivebase, LiDAR, movement gate, and obstacle protection have reached their non-moving commissioning stages. The first physical drive needs explicit approval by a person present at the robot.

## 6. Risks and Rollback

Risks: driving without a dead-man button, adopting the source bypass branch by accident, changed axis numbering on a different computer, invalid rooms after remapping, and an open bridge on the home network.

Rollback: remove the manual-drive profile and the bridge from composition; the map store and room overlay can stay as non-moving services. Do not restore source controller mappings, storage paths, or home data.

## Next Safe Step

Write the HomeMy manual-drive contract. In parallel, the map store and room overlay can be ported against synthetic maps, because they never command motion.
