# Current State

## Phase

Architecture, hardware-transfer, navigation, local obstacle-protection, semantic-perception, appliance-lifecycle, and battery/power foundation. The onboard Linux lifecycle, one-button customer behavior, coarse LED status, battery monitor, electronic main power path, reverse-current blocking, and initial protection thresholds are recorded as accepted architecture. This central subsystem is named the HomeMy Power Management Unit (PMU). A consolidated GPT Astra handoff defines its topology, requirement status, layout rules, fabrication blockers, and verification plan. The KiCad design, production component selections, firmware, systemd units, and real-hardware validation remain pending. No HomeMy runtime package or source code has been copied.

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
- No systemd unit, actuator, sensor, PMU KiCad design, map, home data, or deployment configuration is tracked here.
- No capability from roboter_ws has been copied into HomeMy code.
- The proposed transfer baseline is roboter_ws main commit `05439c7a13d7a92e69b9eb4663e3a2a1b44626a1`.
- Customer mode is not enabled as the default boot target.
- Battery/power values are architecture and initial commissioning thresholds only; no hardware protection validation has been performed.

## Next Safe Step

1. Have GPT Astra create the hierarchical PMU KiCad schematic and controlled pre-layout from `hardware/power-management-unit/ASTRA_PCB_HANDOFF.md`; keep fabrication release false while listed blockers remain.
2. Close exact MOSFET, shunt, connector, wake-latch, CAN, TVS, mechanics, timer, and converter requirements using manufacturer data and calculations.
3. Validate the MOSFET path, shunt sharing, inrush without precharge, DC/DC converters, brake-chopper energy, thermal behavior, and fuse/BMS coordination using current-limited supplies and non-moving loads.
4. Define and simulate the ESP32 power/lifecycle state machine, button timing, heartbeat, hardware latches, event log, and LED behavior before connecting actuators.
5. Design and test a hardware-independent HomeMy drivebase core using the commissioning contract and synthetic fixtures.
6. Design and test LiDAR scan normalization and health behavior with synthetic variable-beam inputs.
7. Assess the smallest hardware-independent `robot_navigation` slice with synthetic maps and a non-moving drivebase profile.
8. Measure the completed HomeMy chassis, drivebase, mounts, footprint, arm masses, joint speeds, power loads, and safety topology before accepting any real-motion configuration.
9. Commission obstacle protection and safe-stop behavior with synthetic geometry and fault injection before OAK or LiDAR data can affect movement.
10. Use synthetic RGB-D fixtures to evaluate semantic perception and grasping before selecting model implementations or enabling manipulation.

## Context Entry Points

1. `AGENTS.md` for safety and work rules.
2. `context/index.json` for task-specific files.
3. `hardware/power-management-unit/ASTRA_PCB_HANDOFF.md` for the current PMU topology, layout brief, and release blockers.
4. `hardware/power-management-unit/interfaces-and-layout.md` for connectors, harnesses, placement, component classes, Astra outputs, and blocker checklist.
5. `hardware/power-management-unit/requirements.yaml` for explicit locked, provisional, open, and blocking requirements.
6. `hardware/power-management-unit/verification-plan.md` for staged evidence before fabrication and motion.
7. `docs/decisions/2026-09-10-battery-monitor-and-power-architecture.md` for the accepted battery, power, button, LED, and communication design memory.
8. `contracts/hardware/customer-power-on.md` for physical one-button startup and shutdown.
9. `contracts/ros/system-lifecycle.md` for appliance behavior.
10. `contracts/hardware/drivebase-commissioning.md` for ESS23-RS adaptation.
11. `contracts/hardware/lidar-commissioning.md` for STL-27L adaptation.
12. `contracts/hardware/obstacle-protection.md` for STL-27L/OAK 4D protection roles and O0-O5 evidence.
13. `contracts/hardware/navigation-commissioning.md` for `robot_navigation` assessment.
14. `integration/roboter_ws/TRANSFER_MANIFEST.md` for incoming transfers.
15. `docs/decisions/2026-08-31-semantic-perception-and-grasping.md` for the proposed semantic perception and grasping pipeline.

## Open Decisions

- Exact PMU schematic and PCB, MOSFETs, thermal design, shunt sharing, brake-chopper components, TVS network, and measured evidence supporting operation without precharge.
- Exact resettable eFuse settings, cable gauges, connectors, grounding, power distribution, converter selection, and battery enclosure/venting. The 60 A battery fuse remains the only melting fuse.
- Exact board outline, mounting holes, component-height envelope, connector directions, busbar geometry, airflow, and chassis heat-spreader interface.
- Proven per-arm current envelope or a higher-current arm connector; exact battery and chopper connectors with temperature/pulse derating.
- Exact Power-button debounce, long-press duration, shutdown timeout, hardware override, heartbeat, and non-volatile logging.
- Exact battery, MOSFET, shunt, brake-resistor, and converter temperature sensors and thresholds.
- Exact HomeMy emergency-stop, movement-gate, command-ownership, and safe-stop topology.
- Final onboard Linux computer specification and measured ROS power budget.
- Exact HomeMy chassis, wheel, drive-train, LiDAR-frame, OAK-frame, sensor-mount, protection-volume, arm-mass, joint-speed, and footprint measurements.
- Final RobStride joint selection/reduction, USB-CAN adapter, CAN identifiers/message contract, and RS485 addressing/update rates.
- Exact local model implementations, accelerator, ROS interfaces, and validation thresholds for semantic perception and grasping.
- External AI health endpoint, authentication storage, and capability protocol.
- Whether HomeMy includes `robot_interfaces`, `safety_monitor`, mission-gate and behavior-tree patterns, semantic maps, or app functions from roboter_ws.
- Disk encryption, TPM recovery path, update strategy, and service access model.
