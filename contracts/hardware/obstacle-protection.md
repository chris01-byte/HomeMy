# Obstacle Protection Contract

Status: proposed for HomeMy; no perception or motion code has been copied.

Owner: HomeMy navigation and safety integration.

## Purpose

This contract defines the HomeMy obstacle-protection boundary after removal of the source VL53 assumptions. It assigns local sensing roles before real navigation or motion is accepted.

The STL-27L is the primary local 2D protection input for the validated floor and near-field operating envelope. A future OAK 4D is a complementary local 3D depth input for larger or higher obstacles that can lie outside the STL scan plane. The OAK role is based on measured geometry, not object classification.

This is an operational protection contract, not a claim that a camera or LiDAR is a certified functional-safety device. The independent emergency-stop and any required hardware safety controller remain separate from the ROS perception path.

## Scope and Non-Goals

In scope:

- local STL-27L scan health and protected floor/near-field geometry;
- local OAK 4D depth health and protected 3D geometry above or outside the STL scan plane;
- HomeMy movement-gate inputs, conservative stop behavior, degraded operation, and test evidence.

Out of scope:

- external AI server, network transport, remote image relay, off-board inference, LLM planning, and semantic object classification;
- source VL53 layers, collision-monitor configuration, OAK-D-S2 calibration, chassis geometry, or live navigation tuning;
- automatic motion authorization or automatic resume after a stop.

## Local Protection Model

A HomeMy motion command must pass through the local movement gate. The gate accepts only fresh, commissioned inputs and remains closed after boot, restart, configuration change, or protection fault until separately authorized.

The intended local inputs are:

| Input | Intended role | Required condition |
| --- | --- | --- |
| STL-27L scan | Primary 2D floor and near-field obstacle protection | Commissioned frame, masks, direction, timestamp, diagnostics, and known blind zones |
| OAK 4D depth | Complementary 3D protection for larger or higher obstacles | Commissioned mount, depth quality, camera-to-base_link transform, timestamp, and protected volume |
| Independent emergency stop | Independent final hardware boundary | Available without ROS, camera, LiDAR, external AI, or network |

The monitor evaluates local obstacle geometry inside measured HomeMy protection volumes. It must not require a model to identify an object before reacting. Unknown but valid occupied geometry inside an active protection volume is treated conservatively.

Protection volumes, response distance, speed limits, and braking allowance must be derived from HomeMy measurements, verified stop behavior, end-to-end input age, and the intended operating environment. No source dimensions, costmaps, or timing values are portable defaults.

## Required Behavior

- A detected obstacle in an active protected volume requests a zero-motion response and closes the movement gate according to the verified stop path.
- A protection event does not resume motion automatically. A separate, explicit recovery path must confirm that inputs are healthy and the route is clear.
- OAK depth processing runs locally on the on-board Linux computer. Remote AI availability cannot delay, permit, or veto an immediate protection response.
- External AI remains optional under the existing AI-health contract. Its outage is not an obstacle-protection input.
- The STL and OAK roles must have a documented boundary with no unexamined gap between the STL-proven floor/near-field envelope and the OAK-proven 3D envelope.

## Data Validity and Fail-Closed Rules

The following conditions keep movement closed in any operating region that depends on the affected sensor:

| Condition | Required response |
| --- | --- |
| STL scan absent, stale, ambiguous, uncommissioned, or diagnostically unhealthy | Fault or closed gate; no assumed floor/near-field coverage |
| OAK depth absent, stale, low quality, uncalibrated, missing camera-to-base_link transform, or diagnostically unhealthy | Fault or closed gate for any 3D-dependent operating region |
| Protection-volume configuration missing, incompatible with the measured chassis, or changed without review | Closed gate |
| Conflicting or implausible protection input | Conservative stop and fault investigation |
| OAK unavailable after a separately proven LiDAR-only operating envelope is selected | READY_LIMITED only within that documented envelope; no operation requiring OAK 3D coverage |

The system may not silently continue using cached scans, cached depth frames, permissive defaults, or source calibration. A LiDAR-only degraded mode is valid only after its geometry, speed, blind zones, obstacle cases, and stop behavior have been separately demonstrated for HomeMy.

## OAK 4D Commissioning Evidence

1. O0: use synthetic depth geometry and a closed movement gate to test volume occupancy, stop requests, timestamp bounds, and fault reporting.
2. O1: measure the OAK mount, field of view, camera-to-base_link transform, chassis occlusion, and overlap or boundary with the STL-proven envelope.
3. O2: validate depth quality, minimum and maximum usable distance, transparent or reflective material limits, lighting limits, USB/bandwidth behavior, and end-to-end latency without motion.
4. O3: inject stale frames, device disconnects, invalid depth, invalid transforms, dropped data, and restart sequences while movement remains disabled.
5. O4: after explicit human approval, test bounded low-speed physical stops against representative obstacles at several heights and distances under supervision.
6. O5: record the accepted operating envelope, remaining blind zones, maximum permitted speed, recovery behavior, and rollback path before enabling customer navigation.

## Navigation Integration

Nav2 and robot_navigation may consume validated obstacle geometry only after this contract and the navigation commissioning contract have passed their applicable evidence. Planning success, a valid depth image, or a valid LiDAR scan never grants motion by itself.

OAK depth may later be projected into a local 2D or voxel representation for navigation quality, but the immediate protection behavior must remain local, bounded, and independently testable from remote AI services.

## Rollback

Remove the OAK input from customer service composition and keep the movement gate closed unless a documented LiDAR-only operating envelope has already been validated. Do not restore VL53 layers, source collision settings, source camera calibration, or source navigation parameters as a shortcut.
