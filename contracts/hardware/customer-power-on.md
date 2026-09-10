# Customer Power-On Contract

Status: accepted design direction; hardware implementation pending.  
Owner: HomeMy platform and hardware integration.

## Scope

This contract covers the customer-visible physical start and controlled shutdown path. It applies before the onboard Linux computer has booted and complements, but does not replace, the emergency-stop and actuator-safety chain. Detailed electrical assumptions are recorded in `docs/decisions/2026-09-10-battery-monitor-and-power-architecture.md`.

## Product Requirement

One customer-facing Power button starts HomeMy as an appliance. There is no customer-facing mechanical master switch. The customer must not start a Linux computer, enter an Ubuntu password, open a terminal, attach a display, or start a separate external computer.

## Selected Architecture

- An ESP32-S3 is the independent power and status controller.
- An LM74930-Q1 with external back-to-back MOSFET banks is the planned electronic main power path.
- A separate independent motion gate remains closed until the safety and mission contracts permit motion.
- An addressable 5 V LED strip is the customer-visible status indicator; HomeMy has no permanently installed graphical display.
- Detailed diagnostics are stored by Linux and are available through development/service interfaces.
- The battery fuse and BMS remain the final protection layers.

## Required Button Behavior

- A deliberate press while OFF asserts the hardware start path.
- After power-path startup, the ESP32 takes over electrical self-hold.
- A short press while running requests controlled HomeMy shutdown; it does not immediately remove battery power.
- A long press provides a forced-shutdown fallback if Linux or the normal shutdown path fails.
- Exact debounce, long-press duration, grace timeout, and button-driver circuit remain implementation parameters and require test evidence.
- A latched hardware fault or unrecovered low battery prevents restart.
- No power recovery causes an automatic restart.

## Startup Path

1. The customer presses the Power button.
2. The electronic path supplies the ESP32, LED strip, onboard Linux computer, and non-motion branches required for boot.
3. The ESP32 assumes self-hold and shows BOOTING.
4. Linux starts HomeMy through systemd customer mode using `homemy.target`, without a desktop login.
5. The boot manager performs mandatory local self-tests and the bounded external-AI health check.
6. The lifecycle result becomes READY, READY_LIMITED, or FAULT.
7. Power-on and ready state do not grant motion authority; the motion gate remains governed separately.

## Shutdown Path

1. A short button press or software request starts controlled shutdown.
2. HomeMy rejects new work and enters SHUTTING_DOWN.
3. The motion gate closes and the required stop condition is verified.
4. Final state and diagnostics are recorded.
5. Linux services stop and the operating system shuts down.
6. The ESP32 waits for shutdown acknowledgement or the defined timeout.
7. The ESP32 releases self-hold and the electronic main path enters low-current shutdown.

## Failure Behavior

- The ESP32 drives the status LED before Linux is available, so a failed Linux boot cannot leave a stale green state.
- Missing Linux heartbeat closes the independent motion gate before restart or shutdown handling.
- Hardware undervoltage, overcurrent, short circuit, or critical thermal faults may remove power without waiting for Linux.
- A forced long press may bypass a failed Linux shutdown, but must first command the motion gate closed wherever hardware remains responsive.
- A hardware protection trip latches until its documented reset conditions and deliberate button action are satisfied.
- Main-path removal is not used as the normal motor stop mechanism.

## Customer-Visible LED States

| State | Indication |
| --- | --- |
| OFF | Dark |
| BOOTING | Pulsing blue |
| SELF_TEST | Moving yellow |
| READY | Steady green |
| READY_LIMITED | Amber |
| OPERATING | Cyan activity pattern |
| FAULT | Flashing red |
| SHUTTING_DOWN | Pulsing violet |

LED brightness and current are limited. The status indication must be controlled by the ESP32 and must not depend on the Ubuntu GUI.

## Validation

Implementation must prove cold power-on, button debounce, self-hold takeover, Linux boot without customer login or GUI, failed-boot indication, short-press shutdown, long-press fallback, heartbeat loss, brownout, hardware latch-off, restart inhibition, and that no startup path enables motion automatically.

No hardware validation has been performed for this document.

## Rollback

Until this contract is implemented, retain the developer-controlled power and shutdown procedure. Removing or disabling customer power automation must leave the independent motion gate in its safe state. Real actuators remain disconnected or independently inhibited during power-controller commissioning.

