# Homes Are Mapped by a Person With a Gamepad; Rooms Are Managed in the App

Status: accepted by the project owner. No HomeMy code, contract, or hardware test exists yet.
Date: 2026-11-16.

## Context

Amadeus tried to explore homes autonomously with frontier exploration. After months of work the multi-room stage was still open on 2026-10-01: real pre-runs were blocked by source timing limits and by geometry checks that rejected every frontier goal. Amadeus did reach a first room change on 2026-08-18, but no complete multi-room run passed.

Amadeus already had the parts of a simpler workflow: manual driving with a gamepad, a versioned map store, and an app in which a person draws rooms on a saved map.

## Decision

HomeMy gets **no autonomous exploration mode**.

Instead:

1. A person drives HomeMy once through all rooms with a gamepad, for example a PS5 DualSense, while the robot builds the map.
2. The finished map is saved as a version.
3. Rooms are then defined and managed in the HomeMy app, following the Amadeus app concept.

The Amadeus concept, which HomeMy adopts:

- **One metric map for the whole home.** Rooms are not mapped as separate maps; they are named areas on that one map.
- **Versioned map store.** A map is saved only on an explicit command. Each version is immutable and carries a content fingerprint.
- **Room overlay bound to one map version.** Each room is a polygon with a name, an optional colour, and an optional navigation goal. If the map changes, the overlay is no longer editable or usable until it is bound to the new version.
- **App over a WebSocket bridge.** The app shows the map, the robot position, and the rooms, and sends commands to the map and room managers. It sends no direct motor commands.

Navigation to a room's goal remains in scope. It is governed by the navigation and obstacle-protection contracts and is not changed by this decision.

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

Open owner decisions for that contract:

- **Dead-man button.** Recommended: drive only while a button is held. Amadeus ran without one by owner choice and observed self-starting from stick drift before switching to the digital direction pad.
- **Who maps.** A technician during setup, or the customer. This decides whether manual driving must exist in customer mode.

## Lessons From Amadeus to Keep

- Drive slowly, especially in turns. Fast turns degraded the map.
- Use the digital direction pad rather than the analogue sticks. The sticks did not return to an exact zero.
- The LiDAR scan normalizer and the pinned slam_toolbox rotation fix were the decisive map-quality fixes. They belong to the LiDAR transfer candidate.
- Amadeus button and axis numbers were measured on a DualShock. A DualSense has a different layout; HomeMy must measure its own controller.

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
