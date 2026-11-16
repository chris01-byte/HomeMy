# Homes Are Mapped by a Person With a Gamepad; Rooms Are Managed in the App

Status: accepted by the project owner. No HomeMy code, contract, or hardware test exists yet.
Date: 2026-11-16.

## Context

Amadeus tried to explore homes autonomously with frontier exploration. After months of work the multi-room stage was still open on 2026-10-01: real pre-runs were blocked by source timing limits and by geometry checks that rejected every frontier goal. Amadeus did reach a first room change on 2026-08-18, but no complete multi-room run passed.

Amadeus already had the parts of a simpler workflow: manual driving with a gamepad, a versioned map store, and an app in which a person draws rooms on a saved map.

## Decision

HomeMy gets **no autonomous exploration mode**.

Instead:

1. A person drives HomeMy once through all rooms with a gamepad while the robot builds the map. The gamepad is the same DualShock model that Amadeus uses.
   Either a technician or the customer may do this.
2. The finished map is saved as a version.
3. Rooms are then defined and managed in the HomeMy app, following the Amadeus app concept.

The Amadeus concept, which HomeMy adopts:

- **One metric map for the whole home.** Rooms are not mapped as separate maps; they are named areas on that one map.
- **Versioned map store.** A map is saved only on an explicit command. Each version is immutable and carries a content fingerprint.
- **Room overlay bound to one map version.** Each room is a polygon with a name, an optional colour, and an optional navigation goal. If the map changes, the overlay is no longer editable or usable until it is bound to the new version.
- **App over a WebSocket bridge.** The app shows the map, the robot position, and the rooms, and sends commands to the map and room managers. It sends no direct motor commands.

Navigation to a room's goal remains in scope; the owner confirmed this explicitly. It is governed by the navigation and obstacle-protection contracts and is not changed by this decision.

### Not Selected

- Autonomous frontier exploration, coverage driving, portal or door bridging, and the Amadeus `explore` package with its exploration modes.
- Mapping each room as a separate map.
- The Amadeus "Explore" functions in the app and in the browser app.

## Requirements for Manual Driving

Manual driving is the first planned use of real HomeMy motion. It needs its own HomeMy contract before any drive test. The contract must at least require:

- every drive command passes through the HomeMy movement gate and the local obstacle protection; no default path bypasses them;
- releasing the controls, losing the controller connection, or a command timeout stops the robot;
- bounded mapping speeds. Amadeus mapped at 0.12 m/s and 0.40 rad/s; HomeMy values follow its own drivebase commissioning;
- manual driving is a deliberate, visible operating state; power-on or READY never enables it;
- a defined way to back out of a protection stop. Amadeus used a second control branch that bypassed its collision monitor; that bypass is not a HomeMy default.

### Owner Decisions on Manual Driving (2026-11-16)

- **Controller:** the same DualShock model as Amadeus. The Amadeus button assignment is kept: direction pad up and down drives, left and right turns, R1 selects the faster mode.
- **No dead-man button.** The robot drives as soon as a direction is pressed. This is an owner decision against the recommendation in the first version of this record.
- **Who maps:** a technician or the customer. Manual driving must therefore work in customer mode, without an Ubuntu login or terminal.

Consequences the manual-drive contract must cover because there is no dead-man button:

- only the digital direction pad may command motion. Amadeus observed self-starting from analogue stick drift;
- the stop on controller disconnect, on an empty controller battery, and on command timeout must be proven with a direction held down;
- mapping mode is entered and left explicitly, so that a controller lying around cannot move the robot outside that mode.

Still open: how a customer enters mapping mode and connects the controller without an Ubuntu login, and whether the controller is wired or wireless.

The button and axis numbers come from the operating-system driver and the joystick node, not only from the controller. They are expected to carry over, but must be checked once on the HomeMy computer before the first drive.

## Lessons From Amadeus to Keep

- Drive slowly, especially in turns. Fast turns degraded the map.
- Use the digital direction pad rather than the analogue sticks. The sticks did not return to an exact zero.
- The LiDAR scan normalizer and the pinned slam_toolbox rotation fix were the decisive map-quality fixes. They belong to the LiDAR transfer candidate.
- Tile joints matter. On Amadeus a single joint turned the chassis by about 3 degrees within 8.5 cm of travel while the wheel encoders saw none of it; the HWT601 gyro and the LiDAR both measured it. A map driven over tiles on encoder heading alone showed fan-shaped, offset walls. HomeMy therefore maps with gyro yaw rate in the odometry; see the HWT601 transfer record.

## Evidence

- Amadeus exploration status at roboter_ws commit `08a4b9a` (2026-10-01): stage 3 open, no passed multi-room run.
- Amadeus manual mapping, map store, room overlay, and iOS app at the transfer baseline `05439c7`. The map manager and room manager have 51 Python tests each; the iOS app has 44 Swift tests. Not run for HomeMy.

## Impact

- Navigation: maps come from manual mapping. Localization and navigation to room goals remain.
- New transfer candidates for gamepad driving, map store, room overlay, and the app, recorded in `docs/transfers/roboter_ws/2026-11-16-manual-mapping-and-app-candidates.md`.
- Safety: a manual-drive contract is required before the first drive test.
- Privacy: home maps and room names are private home data. They stay on the robot and in the app, never in this repository.
- Network: the WebSocket bridge exposes robot topics to the local network. Access control and the customer network setup are open.

## Validation

None. Architecture decision only.

## Risks and Rollback

Risks: a poorly driven map, rooms becoming invalid after remapping, unsafe manual driving without a tested stop path, and an unprotected bridge on the home network.

Rollback: keep the robot in simulation or the non-moving profile and remove manual driving and the app bridge from customer composition. Reconsidering autonomous exploration is a new decision, not a rollback.
