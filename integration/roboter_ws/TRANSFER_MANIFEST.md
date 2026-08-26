# Transfer Manifest: roboter_ws to HomeMy

## Rule

A transfer moves one bounded capability at a time. roboter_ws remains the source of record until the HomeMy implementation, contract, tests, and rollback path are accepted.

Do not copy whole packages, local deployment files, home data, maps, bags, credentials, or historic logs.

## Current Status

No transfer has been accepted yet.

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
