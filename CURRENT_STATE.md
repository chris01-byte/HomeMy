# Current State

## Phase

Architecture, hardware-transfer, and navigation foundation. The on-board Linux appliance lifecycle and customer-visible fault behavior are defined. ESS23-RS drivebase, STL-27L LiDAR, local OAK camera foundation, and robot_navigation are recorded as proposed source candidates. No HomeMy runtime package, systemd unit, real-hardware configuration, or source code has been copied.

## Goal

Build HomeMy as a safe, modular ROS 2 platform for a household robot. It must support normal Ubuntu development while booting as a one-button customer appliance when customer mode is later enabled.

## Active Architecture

- HomeMy uses an on-board Linux computer as the only computer required for customer startup.
- Developer mode keeps normal Ubuntu login and desktop through graphical.target.
- Customer mode will use homemy.target and must not require a customer Ubuntu login, terminal, or manual ROS command.
- systemd starts and supervises product services; it does not supply the customer interface.
- A HomeMy status display must show BOOTING, SELF_TEST, READY, READY_LIMITED, or FAULT with clear error information.
- The external AI server remains remote and optional. Its failure maps to READY_LIMITED only after local mandatory checks pass.
- Power-on, restart, and ready state never authorize motion automatically.

## Active Transfer Scope

- ESS23-RS drivebase behavior may be adapted from roboter_ws only through the non-moving HomeMy commissioning contract. All HomeMy vehicle measurements remain open.
- STL-27L driver, scan normalization, and diagnostics may be adapted after new LiDAR frame and mount commissioning.
- robot_navigation may be adapted only as a hardware-independent Nav2 and simulation candidate. Its real profile awaits HomeMy footprint, LiDAR, obstacle protection, movement-gate, and safety commissioning.
- The local OAK hardware foundation is a later candidate. A future OAK 4D upgrade requires its own contract.
- VL53 near-field hardware, vl53_near_field, CH341/DKMS support, and source VL53-driven collision configuration are excluded from HomeMy.
- robot_interfaces and safety_monitor are deferred until HomeMy has a separate need and contract for them.
- The external AI server, network transport, remote relay, inference backend, LLM planner, and deployment are explicitly deferred and must not be modified.

## Current Safe State

- The repository is public; it contains no secrets, home data, maps, camera data, or deployment configuration.
- The default execution mode is simulation or motorless validation.
- No systemd unit, actuator, sensor, map, home data, or deployment configuration is tracked here.
- No capability from roboter_ws has been copied into HomeMy code.
- The proposed transfer baseline is roboter_ws main commit 05439c7a13d7a92e69b9eb4663e3a2a1b44626a1.
- The future customer mode is not enabled as a default boot target.

## Next Safe Step

1. Design and test a hardware-independent HomeMy drivebase core using the commissioning contract and synthetic fixtures.
2. Design and test LiDAR scan normalization and health behavior with synthetic variable-beam inputs.
3. Assess the smallest hardware-independent robot_navigation slice with synthetic maps and a non-moving drivebase profile.
4. Measure the completed HomeMy chassis, drivebase, LiDAR mount, footprint, and safety topology before accepting any real-motion or navigation configuration.
5. Select and commission a HomeMy-specific obstacle-protection and safe-stop design before enabling real navigation; it must not assume VL53 hardware exists.
6. Create a separate local OAK contract before porting camera bring-up; do not touch the external AI server or network path.

## Context Entry Points

1. AGENTS.md for safety and work rules.
2. context/index.json for task-specific files.
3. contracts/hardware/drivebase-commissioning.md for ESS23-RS adaptation.
4. contracts/hardware/lidar-commissioning.md for STL-27L adaptation.
5. contracts/hardware/navigation-commissioning.md for robot_navigation assessment.
6. contracts/ros/system-lifecycle.md for appliance behavior.
7. integration/roboter_ws/TRANSFER_MANIFEST.md for incoming transfers.

## Open Decisions

- On-board Linux computer specification and operating-system image.
- Physical power controller, safety controller, and customer status display.
- HomeMy obstacle-protection, movement-gate, and emergency-stop topology replacing the source VL53 assumptions.
- Exact HomeMy chassis, wheel, drive-train, LiDAR-frame, sensor-mount, and footprint measurements.
- External AI health endpoint, authentication storage, and capability protocol.
- Whether HomeMy includes robot_interfaces, safety_monitor, mission-gate and behavior-tree patterns, semantic maps, or app functions from roboter_ws.
- Disk encryption, TPM recovery path, update strategy, and service access model.
