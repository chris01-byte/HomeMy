# Current State

## Phase

Architecture foundation. The on-board Linux appliance lifecycle and customer-visible fault behavior are defined. No runtime package, systemd unit, display hardware, power hardware, or transferred robot code is implemented yet.

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

## Current Safe State

- The repository is currently public; it contains no secrets, home data, maps, camera data, or deployment configuration.
- The default execution mode is simulation or motorless validation.
- No systemd unit, actuator, sensor, map, home data, or deployment configuration is tracked here.
- No capability is transferred from roboter_ws by this initial architecture work.
- The future customer mode is not enabled as a default boot target.

## Next Safe Step

1. Implement the lifecycle state machine in simulation with synthetic service and AI-health results.
2. Define the status-display event schema and synthetic customer fault scenarios.
3. Select and contract the physical power, independent safety, and customer-display hardware.
4. After a first local end-to-end simulation path, add minimal systemd units and test customer-mode cold boot early.

## Context Entry Points

1. AGENTS.md for safety and work rules.
2. context/index.json for task-specific files.
3. contracts/ros/system-lifecycle.md for appliance behavior.
4. integration/roboter_ws/TRANSFER_MANIFEST.md for incoming transfers.

## Open Decisions

- On-board Linux computer specification and operating-system image.
- Physical power controller, safety controller, and customer status display.
- Motion-gate and emergency-stop hardware contract.
- External AI health endpoint, authentication storage, and capability protocol.
- Disk encryption, TPM recovery path, update strategy, and service access model.
