# Transfer Manifest: roboter_ws to HomeMy

## Rule

A transfer moves one bounded capability at a time. roboter_ws remains the source of record until the HomeMy implementation, contract, tests, and rollback path are accepted.

Do not copy whole packages, local deployment files, home data, maps, bags, credentials, or historic logs.

## Current Status

Three user-approved hardware-foundation candidates are recorded for staged adaptation. No HomeMy runtime code, real-hardware configuration, or deployment file has been copied.

Source baseline: chris01-byte/Roboter_ws main at commit 05439c7a13d7a92e69b9eb4663e3a2a1b44626a1.

## Active Candidate Entries

| Capability | Source | Planned destination | Status |
| --- | --- | --- | --- |
| ESS23-RS drive-base foundation | src/base_hardware/ | src/homemy_drivebase/ | proposed; user-approved for staged adaptation after HomeMy chassis commissioning |
| STL-27L LiDAR foundation | src/amadeus_lidar_bringup/ and pinned vendor manifest | src/homemy_lidar_bringup/ | proposed; user-approved for staged adaptation after new mount validation |
| Local OAK camera foundation | local bring-up portions of src/robot_bringup/ | future src/homemy_oak_bringup/ | proposed; no server, relay, inference, or network work |

Detailed constraints, excluded scope, and other candidates are in docs/transfers/roboter_ws/2026-08-28-hardware-foundation-candidates.md.

## Explicitly Deferred

The external AI server, network transport, CycloneDDS peer configuration, remote image relay, semantic-perception backend, LLM planner, and off-board inference are not to be copied or modified. The user is actively changing that work elsewhere.

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
