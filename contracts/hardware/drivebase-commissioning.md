# ESS23-RS Drivebase Commissioning Contract

Status: proposed for HomeMy; no source code or real-motion profile copied.
Owner: HomeMy drivebase integration.
Source reference: chris01-byte/Roboter_ws src/base_hardware/ at commit 05439c7a13d7a92e69b9eb4663e3a2a1b44626a1.

## Scope

HomeMy uses the same ESS23-RS NEMA23 closed-loop drive family as the source robot. The controller protocol and fail-closed software behavior are candidates for staged adaptation. The HomeMy chassis is different, so no source geometry, calibration, wiring assumption, or real-motion setting is accepted as a HomeMy value.

## Safe Default

The initial HomeMy drivebase profile is non-moving. It must keep dry-run enabled and RS485 writes disabled until the commissioning record is complete and a person explicitly authorizes a limited test. A reboot, service restart, or valid controller reply never enables motion by itself.

## Portable Behavior Candidates

- Modbus RTU handling and explicit validation of controller writes.
- Absolute encoder-position odometry instead of commanded-velocity fallback.
- Input validation, stale-feedback handling, watchdog stop, and controlled reconnect behavior.
- Low-depth command queueing, finite-value validation, and synthetic regression tests.

The source uses FC03 for reads and FC06 for writes. Exact register mapping and response behavior must be verified on each HomeMy controller before use.

## Required Measurements and Confirmation

Record these values only after the HomeMy chassis is complete:

| Area | Required HomeMy evidence |
| --- | --- |
| Chassis geometry | measured wheel radius, wheel centers, wheel separation, wheel positions, physical footprint, and sensor mounting relation |
| Drive train | confirmed gear ratio, wheel direction, safe speed range, and observed acceleration and braking behavior |
| Controller identity | RS485 device path, motor IDs, left/right inversion, baud and serial settings |
| Encoder protocol | absolute-position word order, counts per motor revolution, segment and resolution values, sign behavior, and reset behavior |
| Odometry | independent straight-line and turn references over short and long distances; uncertainty derived from repeated measurements |
| Safety | independent emergency stop, motion-gate topology, safe stop behavior, and no-motion state after start, error, and shutdown |

Do not reuse source values for wheel radius, effective track width, gear ratio, motor inversion, motor ID, device path, encoder enable values, speed limit, acceleration, braking, start RPM, or covariance. Matching motors do not prove matching vehicle behavior.

## Commissioning Sequence

1. H0: verify the robot is stationary, motion is hardware-gated, and no uncontrolled drive process owns the serial port.
2. H1: perform read-only controller identification and encoder-register checks with no motor command.
3. H2: verify encoder units, word order, signs, and controller configuration using the approved read-only or lifted-wheel procedure.
4. H3: after explicit approval, perform a bounded, low-speed raised-wheel direction and watchdog check.
5. H4: calibrate straight travel and turning against independent external references; use both short and long distances to separate fixed offsets from scale error.
6. H5: verify stale feedback, transport fault, controller reset, reconnect, emergency stop, start, and shutdown behavior all close the motion gate.

Any failed stage keeps real motion disabled. A failed or ambiguous measurement is a result, not a parameter-change invitation.

## Validation

Before hardware use, ported behavior must pass synthetic unit tests for normal commands, non-finite input, quantization, stale feedback, transport error, semantic encoder error, controller reset, and restart. Hardware results must be logged in a HomeMy-specific commissioning record; source test results are regression evidence, not HomeMy acceptance.

## Rollback

Keep the non-moving profile active, remove the HomeMy drivebase service from customer composition, and preserve the independent motion gate. No rollback may re-enable a previous vehicle's calibration or bypass the hardware safety chain.
