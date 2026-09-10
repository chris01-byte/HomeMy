# System Lifecycle Contract

Status: accepted architecture; implementation pending.  
Owner: HomeMy platform.

## Scope

This contract defines how the onboard Linux computer starts, reports state, and stops. It does not replace independent emergency-stop, power, or actuator-safety hardware. The physical start and shutdown path is defined in `contracts/hardware/customer-power-on.md`.

## Product Requirement

A customer presses HomeMy's physical Power button once. No Ubuntu login, password, terminal, display, or manual ROS command is required for normal operation. The robot visibly reports coarse lifecycle state through its ESP32-controlled LED strip. Detailed faults are stored locally and exposed through development/service interfaces.

## Operating Modes

| Mode | systemd target | User experience |
| --- | --- | --- |
| Developer | `graphical.target` | Normal Ubuntu login and desktop for VS Code, terminals, simulation, HDMI diagnostics, and deliberate product-service startup. |
| Customer | `homemy.target` | No GDM login screen. HomeMy services start automatically. Customer state is shown by the robot LED strip, not an Ubuntu desktop. |

systemd always starts before either mode. It chooses the configured target; it is not a customer interface.

## Service Boundary

HomeMy product processes run under a non-interactive service account such as `homemy`. They must not depend on a desktop session, shell startup files, an open terminal, or interactive input.

The future `homemy.target` composes at least:

- a boot/lifecycle manager;
- local ROS 2 and hardware services;
- power-controller communication and heartbeat;
- local diagnostic and event logging;
- a bounded external-AI health checker.

The ESP32 owns the physical LED output. Linux reports lifecycle and diagnostic state to it, but an absent or failed Linux process cannot directly create a green ready indication.

## States

| State | Meaning | LED | Motion gate |
| --- | --- | --- | --- |
| OFF | Main path is off. | Dark | Closed |
| BOOTING | Power controller, Linux, and services are starting. | Pulsing blue | Closed |
| SELF_TEST | Mandatory local dependencies are checked. | Moving yellow | Closed |
| READY | Required local functions and configured optional functions are available. | Steady green | Closed until a separate safety and mission contract permits motion |
| READY_LIMITED | Mandatory local checks pass, but a non-critical capability is unavailable. | Amber | Closed until separately permitted |
| OPERATING | An accepted customer operation is running. | Cyan activity pattern | Controlled only by separate safety and mission contracts |
| FAULT | A mandatory dependency or safety check failed. | Flashing red | Closed |
| SHUTTING_DOWN | Work is rejected, motion is stopped, and Linux is being closed. | Pulsing violet | Closed |

Allowed startup transitions are BOOTING -> SELF_TEST -> READY, BOOTING -> SELF_TEST -> READY_LIMITED, or BOOTING -> SELF_TEST -> FAULT. Any safety-critical loss while running closes the motion gate before recovery, restart, or shutdown is attempted.

READY and READY_LIMITED never imply automatic actuator activation.

## Fault Contract

Every fault record contains a stable code, severity, affected component, short message, recommended action, time, and software version. The LED strip shows only the coarse state; it does not encode detailed service instructions.

Examples:

- E-AI-001: external AI server unavailable; local operation may remain limited.
- E-SYS-001: mandatory local service failed to start; operation is unavailable.
- E-SAFE-001: required safety check failed; movement is blocked.
- E-PWR-001: power-controller or battery protection fault; movement and restart behavior follow the hardware contract.

A failed service must not leave a stale green ready indication. If systemd restarts a mandatory service, HomeMy returns to SELF_TEST with the motion gate closed.

## Heartbeat

Linux and the independent ESP32 power controller exchange a bounded heartbeat and lifecycle state. Loss of heartbeat:

1. invalidates READY or OPERATING;
2. closes the independent motion gate;
3. produces a locally available fault record where possible;
4. enters the defined restart or shutdown timeout path;
5. never automatically restores motion.

Exact transport, periods, timeout, and retry policy remain implementation parameters.

## Shutdown

A controlled shutdown first rejects new work, enters SHUTTING_DOWN, closes the motion gate, sends and verifies the required stop condition, records final state, stops HomeMy services, and requests operating-system shutdown. Only after acknowledgement does the ESP32 release the electronic main power path.

A long Power-button press is the independent forced-shutdown fallback described by the hardware contract. It is not the normal shutdown path.

## Diagnostics

The Linux diagnostic application displays voltage, signed current, power, accumulated energy and charge, estimated state of charge, remaining time, temperatures, protection state, faults, and time histories. An HDMI monitor is connected only during development. The same data is stored locally and may later be published through ROS 2, including `sensor_msgs/BatteryState` where appropriate.

## Validation

Implementation must prove simulated lifecycle transitions, customer-mode cold boot without a desktop session, correct LED output, detailed local fault recording, recovery after a non-critical AI outage, heartbeat loss, controlled shutdown, forced-shutdown fallback, and motion-gate closure before any restart attempt.

No runtime or hardware validation has been performed for this architecture document.

## Rollback

Until customer mode is validated, keep `graphical.target` as the development default and do not enable `homemy.target` as the default boot target. Disabling the HomeMy target must leave the normal developer desktop available and must not enable actuators or bypass independent safety hardware.

