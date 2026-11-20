# ESS23-RS Drivebase Commissioning Contract

Status: proposed for HomeMy. The driver is ported as `src/homemy_drivebase` with a non-moving default and tested in simulation against simulated motors (2026-11-20). No real-motion profile exists; nothing has run on the HomeMy motors.
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

## Implementation Status (2026-11-20)

- `src/homemy_drivebase` is the source driver with unchanged logic. Names, defaults, and texts are HomeMy's.
- The delivered configuration is non-moving three times over: `dry_run: true`, `allow_rs485: false`, and encoder values of 0, which lock the real encoder path until H2.
- Geometry in the configuration is from the CAD model. Registers and ramps are the source values of the same motor family, kept as candidates for H1 to H3. Wheel radius, track width, inversion, motor IDs, device path, and encoder values of the source are not taken over.
- `ess23_readonly_check` is the read-only tool for H1 and H2. It sends only Modbus read requests.
- The Modbus library is pymodbus 3.14.0 and pyserial 3.5, installed with pip (`requirements-modbus.txt`), the versions the source driver ran with.

Validated in simulation only:

- the 74 source tests of the node's safety wiring, the encoder odometry, and the read-only tool pass unchanged apart from names and HomeMy's locked configuration;
- the driver runs against two simulated ESS23-RS motors on a simulated RS485 bus: a pseudo-terminal carries real Modbus RTU frames between pymodbus and the simulated motors (`src/homemy_simulation/homemy_simulation/ess23_sim.py`);
- `src/homemy_bringup/test/test_drivebase_sim.py`: with the delivered configuration not one byte reaches the bus; unlocked against the simulated motors the driver drives at the commanded speed, turns in the right sense, stops 0.25 s after the last command, refuses non-finite commands, reports a cut bus and reconnects with a stop first, and rejects a jump of the encoder counters without a jump in the odometry;
- in `test_drive_sim_e2e.py` the same driver carries the whole mapping run, the drives to rooms, and the restarts.

The simulated motors follow the registers the source driver was proven with. They are no evidence about the HomeMy motors.

### Known Gap: No Watchdog in the Motors

As far as known, an ESS23-RS keeps its last commanded speed until it receives a stop. If the driver process dies or the USB adapter fails while the robot moves, software can no longer stop it. The simulation reproduces this: with the bus cut, the simulated motors keep turning. On the prototype the external hardware emergency-stop switch covers this case (owner decision 2026-11-20). H5 checks in the motor manual and on the motor whether a stop on communication loss can be configured.

## Validation

Before hardware use, ported behavior must pass synthetic unit tests for normal commands, non-finite input, quantization, stale feedback, transport error, semantic encoder error, controller reset, and restart. These pass in simulation as listed above. Hardware results must be logged in a HomeMy-specific commissioning record; source test results are regression evidence, not HomeMy acceptance.

## Rollback

Keep the non-moving profile active, remove the HomeMy drivebase service from customer composition, and preserve the independent motion gate. No rollback may re-enable a previous vehicle's calibration or bypass the hardware safety chain.
