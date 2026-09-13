# Current State

## Phase

Architecture, hardware-transfer, navigation, local obstacle-protection, semantic-perception, appliance-lifecycle, and battery/power foundation. The accepted PMU electrical reference is retained under `hardware/power-management-unit/rev-a`. The only active PCB layout target is a new 300 × 280 mm engineering prototype under `hardware/power-management-unit/rev-a2-300x280`. Failed compact-layout experiments are no longer part of the working tree. Production, energization, assembly and actuator authorization remain false until their documented review gates are closed.

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
- STL-27L is the primary planned local 2D source for the validated floor and near-field operating envelope. A future OAK 4D provides complementary local 3D depth geometry.
- A future semantic perception and grasping path selects YOLO or Grounding DINO on demand, uses SAM2 plus local OAK depth, and treats every model output only as a candidate, never as movement authority.
- Power-on, restart, ready state, and fault recovery never authorize motion automatically.

## Active Transfer Scope

- ESS23-RS drivebase behavior may be adapted from roboter_ws only through the non-moving HomeMy commissioning contract. All HomeMy vehicle measurements remain open.
- STL-27L driver, scan normalization, and diagnostics may be adapted after new LiDAR frame and mount commissioning.
- robot_navigation may be adapted only as a hardware-independent Nav2 and simulation candidate. Its real profile awaits HomeMy footprint, LiDAR, obstacle protection, movement gate, and safety commissioning.
- Local OAK 4D depth is a proposed complementary obstacle-protection candidate governed by `contracts/hardware/obstacle-protection.md`. It remains local; no camera bring-up or protection code has been copied.
- Semantic perception and grasping are architecture-only. No YOLO, Grounding DINO, SAM2, grasp model, local camera bring-up, or manipulation code is selected for transfer.
- VL53 near-field hardware, `vl53_near_field`, CH341/DKMS support, and source VL53-driven collision configuration are excluded from HomeMy.
- `robot_interfaces` and `safety_monitor` are deferred until HomeMy has a separate need and contract for them.
- The external AI server, network transport, remote relay, inference backend, LLM planner, and deployment are explicitly deferred and must not be modified.

## Current Safe State

- The repository is public; it contains no secrets, home data, maps, camera data, or deployment configuration.
- The default execution mode is simulation or motorless validation.
- PMU Revision-A CAD and engineering evidence are tracked; no systemd unit, actuator/sensor runtime, map, home data, or deployment configuration is introduced.
- No capability from roboter_ws has been copied into HomeMy code.
- The proposed transfer baseline is roboter_ws main commit `05439c7a13d7a92e69b9eb4663e3a2a1b44626a1`.
- Customer mode is not enabled as the default boot target.
- Battery/power values are architecture and initial commissioning thresholds only; no hardware protection validation has been performed.

## Next Safe Step

1. Use `hardware/power-management-unit/ASTRA_300X280_LAYOUT.md` to create the new 300 × 280 mm PCB from the retained Rev-A electrical reference.
2. Complete native ERC, DRC, schematic/PCB parity, high-current continuity and manufacturability review before generating an order package.
3. Obtain an independent human schematic/layout/BOM review and explicit prototype-order decision. Do not infer energization or production approval from CAD completion.
4. Bring up the approved prototype with a current-limited source and no actuators; close every energization gate before connecting the battery.
5. Use the prototype to measure MOSFET paths, shunts, inrush, external converters, chopper energy, thermal behavior, arm currents and fuse/BMS coordination for a later production revision.
6. Define and simulate the ESP32 lifecycle state machine, button timing, heartbeat, hardware latches, event log and LED behavior before connecting actuators.
7. Continue non-PMU runtime work only under the existing simulation and commissioning contracts.

## Context Entry Points

1. `AGENTS.md` for safety and work rules.
2. `context/index.json` for task-specific files.
4. `hardware/power-management-unit/ASTRA_PCB_HANDOFF.md` for the current PMU topology and two-stage release model.
5. `hardware/power-management-unit/interfaces-and-layout.md` for connectors, layout, component ownership, Astra outputs, and Revision-A/Revision-B gates.
6. `hardware/power-management-unit/requirements.yaml` for explicit locked, provisional, Revision-A design/assumption/energization, and Revision-B validation requirements.
7. `hardware/power-management-unit/verification-plan.md` for staged prototype bring-up and production evidence.
8. `docs/decisions/2026-09-10-battery-monitor-and-power-architecture.md` for the accepted battery, power, button, LED, and communication design memory.
9. `contracts/hardware/customer-power-on.md` for physical one-button startup and shutdown.
10. `contracts/ros/system-lifecycle.md` for appliance behavior.
11. `contracts/hardware/drivebase-commissioning.md` for ESS23-RS adaptation.
12. `contracts/hardware/lidar-commissioning.md` for STL-27L adaptation.
13. `contracts/hardware/obstacle-protection.md` for STL-27L/OAK 4D protection roles and O0-O5 evidence.
14. `contracts/hardware/navigation-commissioning.md` for `robot_navigation` assessment.
15. `integration/roboter_ws/TRANSFER_MANIFEST.md` for incoming transfers.
16. `docs/decisions/2026-08-31-semantic-perception-and-grasping.md` for the proposed semantic perception and grasping pipeline.

## Open Decisions

- Revision-A CAD choices are implemented and documented in the RevA-P1 package. Physical component behavior, thermal/current assumptions and external integration remain to be validated.
- Conservative Revision-A prototype assumptions to document: generous board outline and mounting, connector directions, external converter pinouts, busbar/heat-spreader provisions, and initial test limits.
- Revision-B measurements: main inrush/no-precharge proof, regenerative energy, 24 V lift-bus behavior, converter capability, per-arm current, connector/cable temperature, full-load thermal behavior, and fuse/BMS/electronic-trip selectivity.
- Final production mechanics: enclosure, component-height envelope, airflow, service access, busbar geometry, battery enclosure/venting, and chassis heat-spreader interface.
- Exact Power-button timing, heartbeat, non-volatile logging, and temperature thresholds start as configurable Revision-A choices and become production limits only after validation.
- Exact HomeMy emergency-stop, movement-gate, command-ownership, and safe-stop topology.
- Final onboard Linux computer specification and measured ROS power budget.
- Exact HomeMy chassis, wheel, drive-train, LiDAR-frame, OAK-frame, sensor-mount, protection-volume, arm-mass, joint-speed, and footprint measurements.
- Final RobStride joint selection/reduction, USB-CAN adapter, CAN identifiers/message contract, and RS485 addressing/update rates.
- Exact local model implementations, accelerator, ROS interfaces, and validation thresholds for semantic perception and grasping.
- External AI health endpoint, authentication storage, and capability protocol.
- Whether HomeMy includes `robot_interfaces`, `safety_monitor`, mission-gate and behavior-tree patterns, semantic maps, or app functions from roboter_ws.
- Disk encryption, TPM recovery path, update strategy, and service access model.
