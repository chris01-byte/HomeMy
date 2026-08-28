# Contracts

Contracts define boundaries before package code is accepted. They are the compatibility layer between HomeMy subsystems and between HomeMy and imported capabilities.

## Active Contracts

- [System lifecycle](ros/system-lifecycle.md): developer and customer modes, systemd supervision, states, fault reporting, and shutdown.
- [Customer power-on](hardware/customer-power-on.md): physical startup, controlled shutdown, and the independent safety boundary before Linux.
- [ESS23-RS drivebase commissioning](hardware/drivebase-commissioning.md): non-moving startup, chassis measurement, and H0-H5 drivebase evidence.
- [STL-27L LiDAR commissioning](hardware/lidar-commissioning.md): sensor-only startup, new mount validation, scan normalization, and L0-L6 evidence.
- [Navigation geometry and safety commissioning](hardware/navigation-commissioning.md): HomeMy footprint, replacement obstacle protection, movement gate, and N0-N5 navigation evidence without VL53.
- [External AI health](api/ai-server-health.md): bounded remote health checks, READY_LIMITED behavior, and customer-visible AI outage handling.

## Contract Areas

- ros/: topics, services, actions, messages, parameters, QoS, lifecycle, and failure behavior.
- hardware/: device capabilities, frame assumptions, power, limits, interlocks, safe defaults, and commissioning.
- api/: application and external service boundaries.
- data/: durable schemas, ownership, retention, and privacy constraints.

## Contract Rule

Every contract names its owner, status, inputs, outputs, failure behavior, validation, and rollback or compatibility plan. A source implementation cannot silently define the HomeMy contract.

## Safe Default

Until a contract explicitly says otherwise, components must fail closed, use synthetic data in tests, and avoid real hardware effects.
