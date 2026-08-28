# Contracts

Contracts define boundaries before package code is accepted. They are the compatibility layer between HomeMy subsystems and between HomeMy and imported capabilities.

## Active Contracts

- [System lifecycle](ros/system-lifecycle.md): developer and customer modes, systemd supervision, states, fault reporting, and shutdown.
- [Customer power-on](hardware/customer-power-on.md): physical startup, controlled shutdown, and the independent safety boundary before Linux.
- [External AI health](api/ai-server-health.md): bounded remote health checks, READY_LIMITED behavior, and customer-visible AI outage handling.

## Contract Areas

- ros/: topics, services, actions, messages, parameters, QoS, lifecycle, and failure behavior.
- hardware/: device capabilities, frame assumptions, power, limits, interlocks, and safe defaults.
- api/: application and external service boundaries.
- data/: durable schemas, ownership, retention, and privacy constraints.

## Contract Rule

Every contract names its owner, status, inputs, outputs, failure behavior, validation, and rollback or compatibility plan. A source implementation cannot silently define the HomeMy contract.

## Safe Default

Until a contract explicitly says otherwise, components must fail closed, use synthetic data in tests, and avoid real hardware effects.
