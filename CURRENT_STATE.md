# Current State

## Phase

Architecture, hardware-transfer, navigation, local obstacle-protection, semantic-perception, appliance-lifecycle, and battery/power foundation. The onboard Linux lifecycle, one-button customer behavior, coarse LED status, battery monitor, electronic main power path, reverse-current blocking, and initial protection thresholds are recorded as accepted architecture. This central subsystem is named the HomeMy Power Management Unit (PMU). A consolidated GPT Astra handoff now authorizes a complete Revision-A engineering prototype and separates its design/order gates from the measurements that gate a later Revision-B production design. The KiCad design, exact Revision-A component selections, firmware, systemd units, and real-hardware validation remain pending. The robot side of the app runs in simulation under ROS 2 Jazzy (`src/`). Software stage S2 is done in simulation: in a test stand ported from Amadeus, HomeMy is driven with the simulated controller through the real teleop profile, motion gate, and blind-sector mask, maps a synthetic four-room apartment with slam_toolbox, switches to the saved map with AMCL, and drives to a room on command from the app. No hardware driver exists; nothing can move a real motor.

## Goal

Build HomeMy as a safe, modular ROS 2 platform for a household robot. It must support normal Ubuntu development while booting as a one-button customer appliance when customer mode is later enabled.

## Active Architecture

- HomeMy uses an onboard Linux computer as the only computer required for customer startup.
- Developer mode keeps normal Ubuntu login and HDMI desktop through `graphical.target`.
- Customer mode will use `homemy.target` without a customer Ubuntu login, GUI, terminal, or manual ROS command.
- systemd starts and supervises product services; it does not supply the customer interface.
- HomeMy has one customer-facing Power button and no customer-facing mechanical master switch.
- An ESP32-S3 independently controls startup/self-hold, shutdown coordination, watchdog behavior, battery telemetry, and the physical status LED.
- The planned electronic main path uses LM74930-Q1 with external back-to-back MOSFET banks. Fuse and battery BMS remain the final protection layers.
- An addressable 5 V LED strip shows OFF, BOOTING, SELF_TEST, READY, READY_LIMITED, OPERATING, FAULT, and SHUTTING_DOWN without depending on Linux.
- Detailed battery/performance diagnostics are stored by Linux and viewed through development/service interfaces; no permanent graphical display is installed.
- The selected battery is a 10S7P 36 V/17.5 Ah/630 Wh pack, 42 V full, 27.5 V BMS cut-off, 50 A continuous, with separate charge/discharge ports and supplied 60 A fuse. It is not approved for regeneration.
- Battery monitoring uses an INA228 and planned 0.5 mOhm four-terminal high-side shunt.
- Reverse battery current is blocked electronically. The provisional motor-bus chopper uses two external 10 ohm/100 W chassis resistors in parallel, with at least 500 J documented bank pulse capability required before release.
- The onboard compute/sensor branch is budgeted at approximately 65 W at the battery side; the discussed basic Ubuntu/sensor measurement was approximately 25 W before the DC/DC converter and without ROS workload.
- The 65 W compute/sensor budget is enforced through Linux/BIOS configuration and has no dedicated branch current sensor. The INA228 continues to measure the complete robot.
- Two ESS23-RS20 drive motors use RS485 and a tested 10:1 self-locking reduction. Two ESS17-RS07 motors provide the self-locking vertical arm lifts through a planned 24 V converter.
- Each of two arms has six planned RobStride joints: RS02 for J1-J4 and RS00 for J5-J6, with additional reduction planned for J2/J3. Final joint hardware remains under test.
- The twelve RobStride joints and ESP32 power telemetry are planned on 1 Mbit/s CAN with 100 Hz joint updates. ESS motors remain on two separate isolated RS485 buses.
- The battery's external 60 A fuse is the only melting fuse. TPS26631 devices protect the PC and 5 V converter inputs; one TPS48110-Q1 motion gate protects passive arm, drive, and lift-converter outputs.
- The external 5 V converter is to provide at least 5 V/5 A continuous; no software current limit is credited as its protection.
- The external AI server remains remote and optional. Its failure maps to READY_LIMITED only after local mandatory checks pass.
- STL-27L is the primary planned local 2D source for the validated floor and near-field operating envelope. An OAK-D-S2, the same model as on Amadeus, provides complementary local 3D depth geometry; the OAK 4D is not available.
- An HWT601-AGV-485 six-axis IMU is planned for yaw-rate-aided odometry on its own read-only RS485 port. It has no absolute heading and is never a movement authority. Its main purpose is heading on tile joints, where Amadeus measured chassis yaw that wheel encoders did not see.
- The STL-27L sits inside the base at the front and scans through an open slot in the structural acrylic ring, about 164 mm above the floor in the CAD model. Two struts and four slot webs give six predicted blind sectors, 34 degrees in total. A closed acrylic window failed the owner's test.
- HomeMy has no autonomous exploration. A technician or the customer drives it once through all rooms with the same DualShock gamepad as Amadeus, without a dead-man button by owner decision, to build one map of the home. The controller is wireless and mapping mode is switched on in the app; rooms are then managed in the app as named areas on that saved map, following the Amadeus app concept.
- A future semantic perception and grasping path selects YOLO or Grounding DINO on demand, uses SAM2 plus local OAK depth, and treats every model output only as a candidate, never as movement authority.
- Power-on, restart, and ready state never start motion by themselves. Within an active mission or mode a stop is a pause: only an emergency stop or a hardware fault latches, everything else heals by itself within fixed limits (owner decision 2026-11-17).

## Active Transfer Scope

- ESS23-RS drivebase behavior may be adapted from roboter_ws only through the non-moving HomeMy commissioning contract. All HomeMy vehicle measurements remain open.
- STL-27L driver, scan normalization, and diagnostics may be adapted after new LiDAR frame and mount commissioning.
- robot_navigation may be adapted only as a hardware-independent Nav2 and simulation candidate. Its real profile awaits HomeMy footprint, LiDAR, obstacle protection, movement gate, and safety commissioning.
- Local OAK-D-S2 depth is a proposed complementary obstacle-protection candidate governed by `contracts/hardware/obstacle-protection.md`. It remains local; no camera bring-up or protection code has been copied.
- Semantic perception and grasping are architecture-only. No YOLO, Grounding DINO, SAM2, grasp model, local camera bring-up, or manipulation code is selected for transfer.
- HWT601 reading and yaw-rate fusion may be adapted from roboter_ws development commit `08a4b9a` (not on main) after a HomeMy IMU contract exists. Mount, axes, bias, noise, timing, and tuning are HomeMy measurements.
- Gamepad driving, the versioned map store, the room overlay, and the map and room parts of the Amadeus iOS app may be adapted from `05439c7`. Gamepad driving needs a HomeMy manual-drive contract first. Autonomous exploration is excluded.
- VL53 near-field hardware, `vl53_near_field`, CH341/DKMS support, and source VL53-driven collision configuration are excluded from HomeMy.
- `robot_interfaces` and `safety_monitor` are deferred until HomeMy has a separate need and contract for them.
- The external AI server, network transport, remote relay, inference backend, LLM planner, and deployment are explicitly deferred and must not be modified.

## Current Safe State

- The repository is public; it contains no secrets, home data, maps, camera data, or deployment configuration.
- The default execution mode is simulation or motorless validation.
- No systemd unit, actuator, sensor, PMU KiCad design, map, home data, or deployment configuration is tracked here.
- Ported or written code: the iPhone app (`ios/HomeMy/`) and ten ROS 2 packages in `src/`. None contains a hardware driver. The motion gate is the only velocity publisher; in the `drive_sim` profile its commands reach the simulated drive. The app bridge refuses every topic outside the app contract.
- The proposed transfer baseline is roboter_ws main commit `05439c7a13d7a92e69b9eb4663e3a2a1b44626a1`.
- Customer mode is not enabled as the default boot target.
- Battery/power values are architecture and initial commissioning thresholds only; no hardware protection validation has been performed.

## Next Safe Step

Software stages S1 (robot side of the app) and S2 (driving in simulation: mapping with the controller, localization on the saved map, drive to a room from the app) are done in simulation. Open in S2: a global position search at start-up like Amadeus' scan localizer, and repeatability over several starts and rooms. Stages S3 (arm in simulation) and S4 (fetch mission in simulation) also need no hardware; the PMU steps below need the hardware.

1. Start GPT Astra with `hardware/power-management-unit/ASTRA_START_PROMPT.md` and have it complete the Revision-A hierarchical KiCad schematic, exact prototype-part selection, routed PCB, BOM, calculations, assumptions record, and prototype fabrication package.
2. Review Astra's schematic, BOM, layout, ERC/DRC, component data, current-path calculations, and conservative Revision-A assumptions before ordering the prototype. Missing post-build measurements do not block this step.
3. Build and bring up Revision A first with a current-limited supply and no actuators; close all energization gates before applying the battery.
4. Use Revision A to measure the MOSFET path, shunts, inrush without precharge, DC/DC converters, brake-chopper energy, thermal behavior, arm currents, and fuse/BMS coordination. Feed the evidence into a later Revision-B production layout.
5. Define and simulate the ESP32 power/lifecycle state machine, button timing, heartbeat, hardware latches, event log, and LED behavior before connecting actuators.
6. Design and test a hardware-independent HomeMy drivebase core using the commissioning contract and synthetic fixtures.
7. Design and test LiDAR scan normalization and health behavior with synthetic variable-beam inputs.
8. Assess the smallest hardware-independent `robot_navigation` slice with synthetic maps and a non-moving drivebase profile.
9. Measure the completed HomeMy chassis, drivebase, mounts, footprint, arm masses, joint speeds, power loads, and safety topology before accepting any real-motion configuration.
10. Commission obstacle protection and safe-stop behavior with synthetic geometry and fault injection before OAK or LiDAR data can affect movement.
11. Use synthetic RGB-D fixtures to evaluate semantic perception and grasping before selecting model implementations or enabling manipulation.

## Context Entry Points

1. `AGENTS.md` for safety and work rules.
2. `context/index.json` for task-specific files.
3. `hardware/power-management-unit/ASTRA_START_PROMPT.md` for the ready-to-use Astra implementation prompt.
4. `hardware/power-management-unit/ASTRA_PCB_HANDOFF.md` for the current PMU topology and two-stage release model.
5. `hardware/power-management-unit/interfaces-and-layout.md` for connectors, layout, component ownership, Astra outputs, and Revision-A/Revision-B gates.
6. `hardware/power-management-unit/requirements.yaml` for explicit locked, provisional, Revision-A design/assumption/energization, and Revision-B validation requirements.
7. `hardware/power-management-unit/verification-plan.md` for staged prototype bring-up and production evidence.
8. `docs/decisions/2026-09-10-battery-monitor-and-power-architecture.md` for the accepted battery, power, button, LED, and communication design memory.
9. `contracts/hardware/customer-power-on.md` for physical one-button startup and shutdown.
10. `contracts/ros/system-lifecycle.md` for appliance behavior.
11. `contracts/hardware/drivebase-commissioning.md` for ESS23-RS adaptation.
12. `contracts/hardware/lidar-commissioning.md` for STL-27L adaptation.
13. `contracts/hardware/obstacle-protection.md` for STL-27L/OAK-D-S2 protection roles and O0-O5 evidence.
14. `contracts/hardware/navigation-commissioning.md` for `robot_navigation` assessment.
15. `integration/roboter_ws/TRANSFER_MANIFEST.md` for incoming transfers.
16. `docs/decisions/2026-08-31-semantic-perception-and-grasping.md` for the proposed semantic perception and grasping pipeline.
17. `docs/transfers/roboter_ws/2026-11-16-hwt601-imu-state-estimation.md` for the HWT601 IMU candidate.
18. `docs/decisions/2026-11-16-lidar-slot-and-support-webs.md` for the LiDAR slot, web positions, and the sectors to mask.
19. `docs/decisions/2026-11-16-manual-mapping-and-app-room-management.md` for manual mapping and app room management.
20. `contracts/api/app-bridge.md`, `ios/HomeMy/README.md`, and `src/homemy_bringup/README.md` for the app, its interface, and the robot side in simulation.
21. `docs/architecture/softwarekonzept.md` for the draft software concept (German): drive to rooms, fetch and bring objects on command from the app.
22. `docs/decisions/2026-11-17-self-healing-and-latching.md` for what latches the robot and what heals by itself.
23. `docs/decisions/2026-11-17-oak-d-s2-camera.md` for the camera on top of the robot.
24. `contracts/hardware/manual-drive.md` and `contracts/ros/motion-gate.md` for driving with the controller and the one place that lets drive commands through.
25. `src/homemy_simulation/README.md` and `src/homemy_bringup/README.md` for the test stand and the `drive_sim` profile.
26. `src/homemy_description/README.md` for the robot model and its frames.
27. `src/homemy_mission/README.md` and `src/homemy_navigation/README.md` for driving to a room, localization on the saved map, and Nav2.

## Open Decisions

- Revision-A design choices Astra must now close: exact MOSFETs, shunts, wake-latch, ESP32 variant, CAN/ESD, chopper, TVS, eFuse settings, connectors, footprints, configurable timer, and preliminary thermal/current calculations.
- Conservative Revision-A prototype assumptions to document: generous board outline and mounting, connector directions, external converter pinouts, busbar/heat-spreader provisions, and initial test limits.
- Revision-B measurements: main inrush/no-precharge proof, regenerative energy, 24 V lift-bus behavior, converter capability, per-arm current, connector/cable temperature, full-load thermal behavior, and fuse/BMS/electronic-trip selectivity.
- Final production mechanics: enclosure, component-height envelope, airflow, service access, busbar geometry, battery enclosure/venting, and chassis heat-spreader interface.
- Exact Power-button timing, heartbeat, non-volatile logging, and temperature thresholds start as configurable Revision-A choices and become production limits only after validation.
- Exact HomeMy emergency-stop, movement-gate, command-ownership, and safe-stop topology.
- Final onboard Linux computer specification and measured ROS power budget.
- Exact HomeMy chassis, wheel, drive-train, LiDAR-frame, OAK-frame, sensor-mount, protection-volume, arm-mass, joint-speed, and footprint measurements.
- Final RobStride joint selection/reduction, USB-CAN adapter, CAN identifiers/message contract, and RS485 addressing/update rates.
- HWT601 mount location, supply, third serial adapter, axis mapping, and behavior on IMU loss.
- Manual driving (`contracts/hardware/manual-drive.md`, proposed): as simple as on Amadeus, without radio-link supervision (owner decision 2026-11-19). Open: axis numbers, mapping speeds, stopping distances, how long the robot keeps driving after a silent radio loss with a direction held, and re-pairing for the customer (steps M1 to M4).
- Localization at start-up when the robot was moved while off: the stored pose is then rejected (scan check) and the robot reports "not localized"; a global search over the map is still to be ported from Amadeus.
- Motion gate (`contracts/ros/motion-gate.md`, proposed): margins, horizon, and clear time of the reactive protection; an obstacle memory for the blind sectors; the arm side; the link to the PMU motion gate.
- Whether HomeMy needs a tilt-based scan gate on tile joints; to be measured on the built chassis.
- App bridge access control and customer network setup before customer use. The laboratory prototype runs without access control by owner decision (2026-11-19).
- Moving rooms to a new map version after remapping. The app cannot save a second map once rooms exist; the owner accepted this for the prototype (2026-11-19).
- Measured LiDAR mask sectors and margins for the slotted base ring (L4); the recorded values are CAD predictions.
- OAK-D-S2 tilt check: the tilt is set by hand (owner decision 2026-11-19), so the camera transform is a calibrated constant. The threshold of the proposed start-up floor-plane check is open.
- Gripper details: a two-jaw parallel gripper is decided; drive, sensors, and interface are open.
- Bounds of each healing step and the clear time before motion continues after a protection stop.
- Exact local model implementations, accelerator, ROS interfaces, and validation thresholds for semantic perception and grasping.
- External AI health endpoint, authentication storage, and capability protocol.
- Whether HomeMy includes `robot_interfaces`, `safety_monitor`, mission-gate and behavior-tree patterns, semantic maps, or app functions from roboter_ws.
- Disk encryption, TPM recovery path, update strategy, and service access model.
