# Current State

## Phase

Architecture, hardware-transfer, navigation, local obstacle-protection, and semantic-perception foundation. The on-board Linux appliance lifecycle and customer-visible fault behavior are defined. ESS23-RS drivebase, STL-27L LiDAR, local OAK 4D depth obstacle protection, robot_navigation, and a conditional semantic perception and grasping pipeline are recorded as proposed candidates or architecture decisions. No HomeMy runtime package, systemd unit, real-hardware configuration, or source code has been copied.

## Goal

Build HomeMy as a safe, modular ROS 2 platform for a household robot. It must support normal Ubuntu development while booting as a one-button customer appliance when customer mode is later enabled.

## Active Architecture

- HomeMy uses an on-board Linux computer as the only computer required for customer startup.
- Developer mode keeps normal Ubuntu login and desktop through graphical.target.
- Customer mode will use homemy.target and must not require a customer Ubuntu login, terminal, or manual ROS command.
- systemd starts and supervises product services; it does not supply the customer interface.
- A HomeMy status display must show BOOTING, SELF_TEST, READY, READY_LIMITED, or FAULT with clear error information.
- The external AI server remains remote and optional. Its failure maps to READY_LIMITED only after local mandatory checks pass.
- STL-27L is the primary planned local 2D source for the validated floor and near-field operating envelope. A future OAK 4D provides complementary local 3D depth geometry for separately commissioned larger or higher obstacles.
- A future semantic perception and grasping path selects YOLO or Grounding DINO on demand, uses SAM2 plus local OAK depth for object geometry, and treats every model output only as a candidate, never as movement authority.
- External AI, semantic classification, and network availability are outside the immediate obstacle-protection response.
- Power-on, restart, and ready state never authorize motion automatically.

## Active Transfer Scope

- ESS23-RS drivebase behavior may be adapted from roboter_ws only through the non-moving HomeMy commissioning contract. All HomeMy vehicle measurements remain open.
- STL-27L driver, scan normalization, and diagnostics may be adapted after new LiDAR frame and mount commissioning.
- robot_navigation may be adapted only as a hardware-independent Nav2 and simulation candidate. Its real profile awaits HomeMy footprint, LiDAR, obstacle protection, movement-gate, and safety commissioning.
- Local OAK 4D depth is a proposed complementary obstacle-protection candidate governed by contracts/hardware/obstacle-protection.md. It remains local; no camera bring-up or protection code has been copied.
- Semantic perception and grasping are architecture-only. No YOLO, Grounding DINO, SAM2, grasp model, local camera bring-up, or manipulation code is selected for transfer.
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
4. Measure the completed HomeMy chassis, drivebase, LiDAR mount, OAK mount, footprint, and safety topology before accepting any real-motion or navigation configuration.
5. Commission the HomeMy obstacle-protection and safe-stop design with synthetic geometry and fault injection before OAK or LiDAR data can affect movement.
6. Validate a LiDAR-only degraded envelope only if its geometry, blind zones, speed, and stop behavior are independently proven; do not touch the external AI server or network path.
7. Use synthetic RGB-D fixtures to evaluate the semantic perception and grasping pipeline before selecting model implementations or enabling manipulation.

## Context Entry Points

1. AGENTS.md for safety and work rules.
2. context/index.json for task-specific files.
3. contracts/hardware/drivebase-commissioning.md for ESS23-RS adaptation.
4. contracts/hardware/lidar-commissioning.md for STL-27L adaptation.
5. contracts/hardware/obstacle-protection.md for STL-27L/OAK 4D protection roles and O0-O5 evidence.
6. contracts/hardware/navigation-commissioning.md for robot_navigation assessment.
7. contracts/ros/system-lifecycle.md for appliance behavior.
8. integration/roboter_ws/TRANSFER_MANIFEST.md for incoming transfers.
9. docs/decisions/2026-08-31-semantic-perception-and-grasping.md for the proposed semantic perception and grasping pipeline.

## Open Decisions

- On-board Linux computer specification and operating-system image.
- Physical power controller, safety controller, and customer status display.
- Exact HomeMy emergency-stop, movement-gate, command-ownership, and safe-stop topology.
- Exact HomeMy chassis, wheel, drive-train, LiDAR-frame, OAK-frame, sensor-mount, protection-volume, and footprint measurements.
- Exact local model implementations, accelerator, ROS interfaces, and validation thresholds for semantic perception and grasping.
- External AI health endpoint, authentication storage, and capability protocol.
- Whether HomeMy includes robot_interfaces, safety_monitor, mission-gate and behavior-tree patterns, semantic maps, or app functions from roboter_ws.
- Disk encryption, TPM recovery path, update strategy, and service access model.
