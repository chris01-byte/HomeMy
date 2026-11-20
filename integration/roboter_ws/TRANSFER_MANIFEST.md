# Transfer Manifest: roboter_ws to HomeMy

## Rule

A transfer moves one bounded capability at a time. roboter_ws remains the source of record until the HomeMy implementation, contract, tests, and rollback path are accepted.

Do not copy whole packages, local deployment files, home data, maps, bags, credentials, or historic logs.

## Current Status

Nine user-approved candidates are recorded for staged adaptation. The local OAK-D-S2 obstacle-protection boundary is documented. Ported so far: the iPhone app, the versioned map store, and the room overlay, all tested in simulation. No driver, real-hardware configuration, or deployment file has been copied.

Source baseline: chris01-byte/Roboter_ws main at commit 05439c7a13d7a92e69b9eb4663e3a2a1b44626a1.

Exception: the HWT601 candidate is not on roboter_ws main. It is pinned to development-branch commit 08a4b9ac0b7a128ced2199f20976f3aa92ea55fe.

## Active Candidate Entries

| Capability | Source | Planned destination | Status |
| --- | --- | --- | --- |
| ESS23-RS drive-base foundation | src/base_hardware/ and tools/kartierung/encoder_position_pruefen.py at 05439c7 | src/homemy_drivebase/ | adapting; driver, encoder odometry, read-only check tool, and their 74 tests ported with unchanged logic; non-moving default (dry run, RS485 writes off, encoder path locked); source geometry, inversion, IDs, device path, and encoder values not taken over; runs in simulation against simulated motors over a pseudo-terminal; nothing has run on the HomeMy motors |
| STL-27L LiDAR foundation | src/amadeus_lidar_bringup/ and pinned vendor manifest | src/homemy_lidar_bringup/ | proposed; user-approved for staged adaptation after new mount validation |
| Local OAK-D-S2 depth obstacle-protection foundation | local bring-up portions of src/robot_bringup/ | future src/homemy_oak_bringup/ | proposed; same camera model as the source, so bring-up fixes transfer, unit calibration and mount do not; local 3D complement to STL-27L under the HomeMy obstacle-protection contract; no server, relay, inference, or network work |
| Navigation algorithms and dry-run foundation | src/robot_navigation/ (config/nav2_params_real.yaml at 05439c7, controller values of 71d3a87) | src/homemy_navigation/ | adapting; Nav2 profile rewritten for Jazzy and the HomeMy outline with the masked LiDAR as obstacle source, recovery-free tree, commands only to the motion gate; new localization manager with a scan-agreement check instead of the source localization guard; the source's global scan matcher (global_scan_matcher.py with its tests) is ported for finding the position on the whole map, with a smaller clearance, a grid-dependent coarse step, and a 5 % instead of 15 % uniqueness margin; tested in simulation |
| HWT601 IMU and yaw-rate state estimation | src/robot_state_estimation/ at commit 08a4b9a | future src/homemy_state_estimation/ | proposed; user-approved for staged adaptation after a HomeMy IMU commissioning contract; read-only sensor on a dedicated third serial bus |
| Gamepad driving for manual mapping | src/robot_bringup/ teleop_joy launch and config at 05439c7 | src/homemy_manual_drive/ | adapting; teleop profile ported under contracts/hardware/manual-drive.md, commands go only to the HomeMy motion gate; no separate radio-link supervision, as in the source (owner decision 2026-11-19); tested in simulation; source bypass branch excluded |
| Versioned map store | src/robot_map_manager/ | src/homemy_map_manager/ | adapting; ported with HomeMy topics and storage path, source unit tests pass under Jazzy, end-to-end test in simulation; no motion effect |
| Room overlay on a saved map | src/semantic_map_manager/ | src/homemy_room_manager/ | adapting; ported with HomeMy topics and storage path, source unit tests pass under Jazzy, end-to-end test in simulation; no motion effect |
| App for map and room management | ios/Robotersteuerung/ | ios/HomeMy/ | adapting; app side ported and tested against a mock under contracts/api/app-bridge.md; mission, exploration, and e-stop parts removed; mapping mode and stop added; robot side runs in simulation |
| Mission manager, go_to_room | src/mission_manager/ at 05439c7: semantic_room_goal.py and its tests, navigate_to_pose_no_recovery.xml | src/homemy_mission/, src/homemy_navigation/config/ | adapting; room-goal resolution ported unchanged with its tests; mission state machine rewritten small for HomeMy (one command plus cancel, preconditions, bounded retries, drive-active signal); RunMission, explore, and pick-and-place not ported; tested in simulation |
| Drive gate | src/robot_navigation/robot_navigation/cmd_vel_mission_gate.py at 05439c7 | src/homemy_motion_gate/ | adapting; rewritten under contracts/ros/motion-gate.md rather than copied: the source gated only Nav2 and explore and never the gamepad; kept the fail-closed rules (fresh inputs, explicit zero at 20 Hz, localization for missions), added the mapping mode for controller commands, the emergency-stop input, and a reactive footprint check on the masked scan; tested in simulation |
| Test stand (simulated devices) | tools/simulation/ap06_world.py and sh_robustheit_welt.py on branch claude/blissful-pasteur-s1eivj at 940a748 | src/homemy_simulation/ (world.py, sim_base) | adapting; world, ray casting, measured drive model, collision check, and map oracle ported with HomeMy geometry, LiDAR self-returns instead of a mast crop, IMU yaw rate added, VL53 and low obstacles left out; simulation only |
| slam_toolbox mapping profile | src/amadeus_lidar_bringup/config/slam_toolbox_amadeus.yaml at 05439c7, loop-closure thresholds from 940a748 | src/homemy_navigation/ | adapting; masked scan, HomeMy frames, 5 cm grid in simulation; switched on and off by mapping mode; tested in simulation |

Detailed constraints, excluded scope, and deferred candidates are in docs/transfers/roboter_ws/2026-08-28-hardware-foundation-candidates.md.

The HWT601 candidate is detailed in docs/transfers/roboter_ws/2026-11-16-hwt601-imu-state-estimation.md.

The manual-mapping and app candidates are detailed in docs/transfers/roboter_ws/2026-11-16-manual-mapping-and-app-candidates.md.

## Explicitly Excluded

- VL53 near-field hardware, vl53_near_field, CH341/DKMS support, and source VL53-specific obstacle or collision-monitor configuration.
- Source chassis geometry, Nav2 footprint, robot radius, costmaps, maps, static transforms, calibration, and real-navigation profiles.
- Autonomous exploration: the explore package, frontier and coverage modes, portal bridging, and the exploration functions of the app and browser app. See docs/decisions/2026-11-16-manual-mapping-and-app-room-management.md.
- External AI server, network transport, CycloneDDS peer configuration, remote image relay, semantic-perception backend, LLM planner, and off-board inference. The user is actively changing that work elsewhere.

## Deferred Until Needed

robot_interfaces, safety_monitor, source mission-gate and behavior-tree integrations, and the browser app are not selected for transfer. They need a separate HomeMy purpose and contract before reassessment.

## Required Entry

Add one entry for every proposed transfer:

| Field | Required content |
| --- | --- |
| Capability | Single user-visible or technical capability |
| Source | chris01-byte/roboter_ws path and immutable commit |
| Destination | Intended HomeMy package or contract |
| Contract | Topics, services, actions, messages, parameters, and failure behavior |
| Dependencies | ROS packages, hardware, network, and local-only assumptions |
| Validation | Unit, integration, simulation, and hardware checks actually run |
| Risks | Known limitations and safety impact |
| Rollback | How to remove or disable the transfer safely |
| Status | proposed, adapting, validated, or rejected |

## Transfer Sequence

1. Record the source commit and read only the matching source contract.
2. Extract or write the HomeMy contract before implementation.
3. Port the smallest testable part with synthetic fixtures.
4. Validate in simulation or motorless mode.
5. Record evidence, remaining risks, and rollback.
6. Update CURRENT_STATE.md only when the transfer changes the active project state.
