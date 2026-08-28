# Transfer Manifest: roboter_ws to HomeMy

## Rule

A transfer moves one bounded capability at a time. roboter_ws remains the source of record until the HomeMy implementation, contract, tests, and rollback path are accepted.

Do not copy whole packages, local deployment files, home data, maps, bags, credentials, or historic logs.

## Current Status

Four user-approved candidates are recorded for staged adaptation. No HomeMy runtime code, real-hardware configuration, or deployment file has been copied.

Source baseline: chris01-byte/Roboter_ws main at commit 05439c7a13d7a92e69b9eb4663e3a2a1b44626a1.

## Active Candidate Entries

| Capability | Source | Planned destination | Status |
| --- | --- | --- | --- |
| ESS23-RS drive-base foundation | src/base_hardware/ | src/homemy_drivebase/ | proposed; user-approved for staged adaptation after HomeMy chassis commissioning |
| STL-27L LiDAR foundation | src/amadeus_lidar_bringup/ and pinned vendor manifest | src/homemy_lidar_bringup/ | proposed; user-approved for staged adaptation after new mount validation |
| Local OAK camera foundation | local bring-up portions of src/robot_bringup/ | future src/homemy_oak_bringup/ | proposed; no server, relay, inference, or network work |
| Navigation algorithms and dry-run foundation | src/robot_navigation/ | future src/homemy_navigation/ | proposed; user-approved for simulation and algorithm adaptation after HomeMy geometry and safety commissioning |

Detailed constraints, excluded scope, and deferred candidates are in docs/transfers/roboter_ws/2026-08-28-hardware-foundation-candidates.md.

## Explicitly Excluded

- VL53 near-field hardware, vl53_near_field, CH341/DKMS support, and source VL53-specific obstacle or collision-monitor configuration.
- Source chassis geometry, Nav2 footprint, robot radius, costmaps, maps, static transforms, calibration, and real-navigation profiles.
- External AI server, network transport, CycloneDDS peer configuration, remote image relay, semantic-perception backend, LLM planner, and off-board inference. The user is actively changing that work elsewhere.

## Deferred Until Needed

robot_interfaces, safety_monitor, source mission-gate and behavior-tree integrations, semantic maps, app, and UI are not selected for transfer. They need a separate HomeMy purpose and contract before reassessment.

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
