# Customer Power-On Contract

Status: accepted design direction; hardware implementation pending.
Owner: HomeMy platform and hardware integration.

## Scope

This contract covers the customer-visible physical start and controlled shutdown path. It applies before the on-board Linux computer has booted and complements, but does not replace, the emergency-stop and actuator safety chain.

## Product Requirement

One physical power control starts HomeMy as an appliance. The customer must not start a Linux computer, enter an Ubuntu password, open a terminal, or start a separate external computer.

## Required Behavior

- The on-board Linux computer is the only computer required for normal local robot startup.
- The external AI server is not a power-on prerequisite. Its absence is reported as limited capability by the lifecycle contract.
- Power-on never grants motion or actuator permission by itself.
- The selected power and safety hardware holds the motion path closed until the separate safety contract permits it.
- A visible boot, ready, limited, or fault indication is available to the customer without a Linux desktop.

## Startup Path

1. The customer activates the physical power control.
2. The power path starts the on-board Linux computer and status indication.
3. Linux starts HomeMy through systemd customer mode.
4. The boot manager performs local self-tests and the external AI health check.
5. The lifecycle result is shown as READY, READY_LIMITED, or FAULT.

## Shutdown Path

A deliberate shutdown request first reaches HomeMy. HomeMy rejects new work, closes the motion gate, performs the required safe-stop verification, records the final status, and requests operating-system shutdown. The selected power controller waits for a clean shutdown acknowledgement or applies its separately defined safe fallback.

## Failure Behavior

A boot failure before the status display is available requires an independent visible fault indication from the selected power or safety hardware. A missing Linux heartbeat or failed safe shutdown must not leave the motion path enabled.

## Open Hardware Decisions

- Physical power-controller and safety-controller implementation.
- Display, LED, or combined customer status indicator.
- Button behavior for power-on, short press, long press, and emergency stop.
- Battery, charger, brownout, and power-loss behavior.
- Heartbeat interface between Linux and independent power or safety hardware.

## Validation

Implementation must prove cold power-on, Linux boot without a customer login, failed boot indication, controlled shutdown, interrupted power recovery, and that no startup path can enable motion automatically. No hardware validation has been performed for this document.

## Rollback

Before this contract is implemented, retain the existing developer-controlled power and shutdown procedure. Removing or disabling customer power automation must leave the independent emergency-stop and motion gate in their safe state.
