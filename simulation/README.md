# Simulation and Test Scenarios

Simulation is the default integration target for HomeMy. It lets contracts, mission logic, and failure behavior be verified before hardware is involved.

## Planned Contents

- fixtures/: synthetic sensor, map, and message data.
- scenarios/: deterministic end-to-end behavior cases.
- adapters/: controllable replacements for hardware and network dependencies.
- evidence/: compact test summaries; bulky generated output stays untracked.

## Rules

Fixtures must be synthetic or anonymized. A scenario names the contract it exercises, expected success and failure behavior, and its executable command. Passing simulation does not grant real-hardware permission.
