# Current State

## Phase

Repository foundation. No runtime packages, hardware configuration, or transferred robot code are present yet.

## Goal

Build HomeMy as a safe, modular ROS 2 platform for a household robot. Start in simulation and integrate capabilities from roboter_ws only through explicit transfer records.

## Current Safe State

- The repository is private and uses main as its default branch.
- No actuator, sensor, map, home data, or deployment configuration is tracked here.
- The default execution mode is simulation or motorless validation.
- No capability is transferred from roboter_ws by this initial commit.

## Next Safe Step

1. Define package ownership and high-level architecture.
2. Define contracts before accepting a source transfer.
3. Create synthetic test fixtures before connecting hardware or home-specific data.

## Context Entry Points

1. AGENTS.md for safety and work rules.
2. context/index.json for task-specific files.
3. integration/roboter_ws/TRANSFER_MANIFEST.md for incoming transfers.

## Open Decisions

- Primary hardware architecture and ROS 2 package boundaries.
- Simulation stack and test strategy.
- First capability to transfer from roboter_ws.
