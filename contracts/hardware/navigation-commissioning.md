# Navigation Geometry and Safety Commissioning Contract

Status: proposed for HomeMy; no source navigation configuration or real-motion profile copied.

Owner: HomeMy navigation and safety integration.

Source reference: chris01-byte/Roboter_ws src/robot_navigation/ at commit 05439c7a13d7a92e69b9eb4663e3a2a1b44626a1.

## Scope

HomeMy may assess hardware-independent Nav2, localization, and dry-run behavior from the source navigation package. The source vehicle geometry, LiDAR mounting, obstacle layers, costmaps, map data, command chain, and live parameters are not HomeMy defaults.

HomeMy does not use VL53 near-field hardware. Therefore the source VL53 obstacle layers and VL53-driven collision-monitor configuration are not portable. Removing those files is not a replacement for a HomeMy obstacle-detection and safe-stop design.

The separate [Obstacle protection contract](obstacle-protection.md) assigns the local protection roles: STL-27L is the primary 2D source for the validated floor and near-field envelope, while OAK 4D depth may cover separately commissioned larger or higher obstacles. OAK protection uses local depth geometry, not remote AI or semantic classification.

## Safe Default

Navigation starts in simulation or a non-moving drivebase profile. A successful plan, valid map, ready LiDAR, valid depth image, or localization result never authorizes movement. Any missing, stale, ambiguous, or uncommissioned safety dependency keeps the movement path closed.

## Required HomeMy Evidence

| Area | Required evidence before real navigation |
| --- | --- |
| Footprint | measured base_link origin, chassis outline, wheels, bumpers, cables, sensor housings, fixed protrusions, and every permitted operating configuration |
| Padding | documented safety margin derived from measurements and the intended environment; no source robot radius or footprint is reused |
| LiDAR installation | commissioned LiDAR pose, direction, masks, normalized scan, timestamp limits, and known blind zones |
| Drivebase | commissioned ESS23-RS odometry, acceleration, braking, speed limits, and verified stop behavior |
| Obstacle protection | separate HomeMy obstacle-protection contract with STL-27L floor/near-field coverage, any OAK 4D protection volume, stale-data behavior, response path, degraded envelope, and safe-stop evidence; source VL53 assumptions are absent |
| Safety path | independent emergency stop, movement gate, command ownership, zero-command behavior, restart behavior, and fault behavior |
| Navigation configuration | HomeMy costmaps, planner/controller settings, map policy, localization criteria, and synthetic plus physical tests |

The footprint must represent the widest and longest permitted configuration, including all relevant fixed equipment. Any later arm, payload, bumper, or sensor-envelope change requires a new measurement and navigation review.

## Staged Acceptance

1. N0: use synthetic maps and the non-moving drivebase profile to test planning, cancellation, terminal status, and failure behavior.
2. N1: verify the HomeMy LiDAR installation, frame, masks, scan normalization, and stale-data response with no motion.
3. N2: publish and inspect the measured HomeMy footprint in the local costmap with no motion; test narrow-passage rejection on synthetic maps.
4. N3: test the complete HomeMy movement gate and obstacle-protection design by fault injection while motion remains disabled, including absent and stale STL input and, in every OAK-required region, stale depth, invalid depth, missing camera-to-base_link transform, and device loss.
5. N4: after N0-N3 and the applicable O0-O3 evidence pass, perform a bounded low-speed physical drive test with the completed safety chain only after explicit human approval.
6. N5: only after N0-N4 pass, validate localization, route planning, cancellation, and safe stop in the intended operating environment.

A source robot_navigation test or a valid Nav2 plan is not HomeMy hardware acceptance. A safety chain with no validated obstacle source must fail closed.

## Source Parts Not Accepted as Defaults

- VL53-specific costmap layers and collision-monitor configuration.
- Amadeus chassis footprint, robot radius, clearance, padding, and door assumptions.
- Source map files, map fingerprints, static map transforms, semantic targets, and environmental data.
- Source velocity-smoother values, progress thresholds, timeouts, costmaps, planner/controller tuning, and real-navigation launch profiles.
- Source OAK-D-S2 calibration, camera mounting, depth thresholds, device aliases, and protection assumptions.
- Any source mission or behavior-tree integration whose HomeMy safety and customer-workflow contract is not yet selected.

## Validation

Before real hardware tests, HomeMy navigation must pass synthetic tests for footprint collision, narrow passages, map and transform freshness, localization rejection, planning failure, cancellation, stale obstacle input, missing obstacle input, lost command ownership, and restart. OAK-required regions must additionally validate local depth age, depth quality, camera-to-base_link transform freshness, device loss, and conservative stop behavior.

Results must distinguish simulation, motorless tests, and approved physical tests.

## Rollback

Keep navigation in simulation or non-moving mode, remove it from customer service composition, and retain the independent movement gate. A LiDAR-only degraded profile is permitted only inside an already documented HomeMy operating envelope. Do not restore source geometry, source VL53 configuration, source OAK calibration, or old live settings as a shortcut.
