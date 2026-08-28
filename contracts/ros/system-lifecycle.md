# System Lifecycle Contract

Status: accepted architecture; implementation pending.
Owner: HomeMy platform.

## Scope

This contract defines how the on-board Linux computer starts, reports state, and stops. It does not replace independent emergency-stop, power, or actuator-safety hardware.

## Product Requirement

A customer presses the robot's physical power control once. No Ubuntu login, password, terminal, or manual ROS command is required for normal operation. The robot must visibly report either ready, limited ready, or a fault.

## Operating Modes

| Mode | systemd target | User experience |
| --- | --- | --- |
| Developer | graphical.target | Normal Ubuntu login and desktop for VS Code, terminals, simulation, and diagnostics. Product services are started deliberately. |
| Customer | homemy.target | No GDM login screen. HomeMy services and a restricted status interface start automatically. |

systemd always starts before either mode. It chooses the configured target; it is not an alternative to the Ubuntu login screen. systemd itself has no customer user interface.

## Service Boundary

HomeMy product processes run under a non-interactive service account such as homemy. They must not depend on a desktop session, shell startup files, an open terminal, or interactive input.

The future homemy.target composes at least:

- a status display service;
- a boot manager;
- local ROS 2 and hardware services;
- a bounded external AI health checker.

homemy-status-display.service is the customer interface. It renders state, error code, plain-language message, and next action. It is a HomeMy application started by systemd, not a systemd interface.

## States

| State | Meaning | Motion gate |
| --- | --- | --- |
| BOOTING | Linux and product services are starting. | Closed |
| SELF_TEST | Mandatory local dependencies are checked. | Closed |
| READY | All required local functions and configured optional functions are available. | Closed until a separate safety and mission contract permits motion |
| READY_LIMITED | Local mandatory checks pass, but a non-critical capability such as the external AI server is unavailable. | Closed until a separate safety and mission contract permits motion |
| OPERATING | An accepted customer operation is running. | Controlled only by separate safety and mission contracts |
| FAULT | A mandatory local dependency or safety check failed. | Closed |

Allowed startup transitions are BOOTING -> SELF_TEST -> READY, BOOTING -> SELF_TEST -> READY_LIMITED, or BOOTING -> SELF_TEST -> FAULT. Any safety-critical loss while running closes the motion gate before recovery or restart is attempted.

READY and READY_LIMITED never imply automatic actuator activation.

## Fault Contract

Every fault shown to a customer includes a stable code, severity, affected component, short message, and recommended action. The same record is written to local diagnostics with time and software version.

Examples:

- E-AI-001: external AI server unavailable; local operation may remain limited.
- E-SYS-001: mandatory local service failed to start; operation is unavailable.
- E-SAFE-001: required safety check failed; movement is blocked.

A failed service must not leave a stale green ready indication. If systemd restarts a service, HomeMy returns to SELF_TEST with the motion gate closed.

## Shutdown

A controlled shutdown first rejects new work, closes the motion gate, sends and verifies the required stop condition, records final state, stops HomeMy services, and only then requests operating-system shutdown. Exact actuator verification belongs to the relevant hardware contract.

## Validation

Implementation must prove simulated lifecycle transitions, customer-mode cold boot without a desktop session, visible fault output, recovery after a non-critical AI outage, and a safe shutdown. No runtime or hardware validation has been performed for this architecture document.

## Rollback

Until customer mode is validated, keep graphical.target as the development default and do not enable homemy.target as the default boot target. Disabling the HomeMy target must leave the normal developer desktop available and must not enable actuators.
