# HWT601 IMU and Yaw-Rate State Estimation Transfer Candidate

Status: proposed for staged adaptation; no HomeMy code copied; no HomeMy IMU has been connected or measured.

## 1. Source

- Repository: chris01-byte/Roboter_ws, package `src/robot_state_estimation/`.
- Immutable commit: `08a4b9ac0b7a128ced2199f20976f3aa92ea55fe` (2026-10-01) on the development branch `feature/hwt-hold-recovery-resume`.
- This capability is **not** on roboter_ws `main`. The general HomeMy baseline `05439c7` therefore does not contain it, and this candidate carries its own pinned commit.
- The source package itself is a selective port of the earlier reference `1d91229` (`codex/hwt601-encoder-shadow`), which is not an ancestor of the pinned commit.

## 2. HomeMy Intent and Destination

HomeMy uses the same HWT601-AGV-485 as the source robot. Its purpose is yaw-rate-aided planar odometry: wheel encoders supply forward speed, the gyro supplies yaw rate. The sensor has six axes and no absolute heading reference, so its orientation output is not a heading source.

Planned destination: a future `src/homemy_state_estimation/` package. The drivebase encoder path stays in the separate drivebase candidate.

## 3. Interface and Incompatible Assumptions

Source interface, as evidence of what a HomeMy contract must define:

| Item | Source behavior at the pinned commit |
| --- | --- |
| Transport | Modbus RTU over RS485, 115200 baud, device address 0x50 |
| Access | function 0x03 only, six motion registers from 0x34; no write function is implemented, so sensor configuration and calibration cannot be altered |
| Rate | 100 Hz polling; full scale 4 g and 400 deg/s |
| Bus ownership | dedicated serial port; the driver refuses the motor RS485 adapter |
| Output | `sensor_msgs/Imu` raw data, a derived yaw-rate-only stream, JSON status, and diagnostics |
| Bias | gyro bias is estimated only during confirmed standstill and frozen while moving |
| Fusion | `robot_localization` EKF in planar mode, fusing encoder forward velocity and IMU yaw rate only; it publishes `odom -> base_link` while SLAM keeps `map -> odom` |
| Failure | stale or invalid data is fail-closed; hard source faults latch until restart; there is no silent fallback to encoder yaw |

Portable candidates:

- the strict read-only Modbus decoder, CRC handling, and serial transport with deadline diagnostics;
- yaw-rate-only fusion, standstill bias calibration, and freshness and health supervision as design patterns;
- the planar EKF structure (encoder speed plus gyro yaw rate), without its numeric tuning;
- the source unit tests as a regression reference.

Not portable, and to be measured or decided for HomeMy:

- mount position, axis mapping, and signs. The source mounting is specific to the source chassis and is marked not approved for fusion in its own configuration;
- gyro bias limits, noise variances, and EKF covariances. They were derived from recordings of the source unit;
- response and freshness budgets and the recovery and hold budgets, which are tuned to the source computer, adapter, and mission gate;
- device aliases, the adapter identity guard, and the read-only encoder reader that depends on source bus ownership;
- every coupling to the source exploration stack, mission gate, and VL53 sources.

HomeMy consequences that are not yet reflected elsewhere:

- The IMU needs a **third** serial bus. The two planned isolated USB-RS485 adapters remain reserved for the ESS23 drive bus and the ESS17 lift bus.
- The adapter stays external to the PMU. PMU Revision A scope is unchanged; the IMU supply rail and voltage must be confirmed from the manufacturer datasheet.
- The CAD model contains no IMU mounting location yet.
- The source ran on ROS 2 Humble. Dependency compatibility must be checked once the HomeMy ROS distribution is fixed.

## Why HomeMy Needs It: Tile Joints

Source evidence, recorded in the source project log at the reference commit `1d91229`:

- 2026-08-24: a manual remap on a tiled floor produced fan-shaped, offset walls and was discarded. The robot visibly rocked on larger tile joints. Encoders and the motor bus reported no fault.
- 2026-09-10: a measured run over one joint was stopped after 8.5 cm. In that window the encoders reported +0.006 degrees of yaw, the HWT601 -3.21 degrees, and a wheel-independent LiDAR matcher -3.00 degrees. The joint turned the chassis and the wheel encoders could not see it.
- In the same run the tilt was small: at most 0.019 rad change of the gravity direction, far below the tilt limits.
- 2026-09-10: over a full turn in place the totals were HWT 362.09, LiDAR 361.75, and encoders 358.03 degrees.

The source therefore fuses encoder forward speed with gyro yaw rate and keeps encoder yaw out of the estimate. HomeMy adopts that principle.

A second source mechanism is a scan gate that withholds LiDAR scans during tilt or impact. Its node exists at `1d91229` and on `feature/modulare-sensorfusion`, but **not** at the pinned commit `08a4b9a`, which kept only its core logic. If HomeMy needs the gate, it is a separate candidate from `1d91229`.

Whether HomeMy needs it is a measurement, not an assumption. Two differences from the source robot point in opposite directions: the HomeMy LiDAR sits about 0.16 m above the floor instead of 0.66 m, so a downward tilt of 1 degree reaches the floor at about 9 m and 3 degrees at about 3 m; and the CAD shows support castors of only 30 mm diameter.

## 4. Tests and Results Actually Run

None for HomeMy. This record is a source review only.

The pinned source commit contains 96 HWT601 test functions in nine test files (counted, not executed here). The source documentation states that its historical acceptances are not current acceptances, and its latest real pre-runs on 2026-10-01 were still blocked, partly by IMU recovery budgets and encoder read timing. Source results are regression evidence, not HomeMy acceptance.

## 5. Hardware and Safety Impact

The IMU is a read-only sensor and has no actuator effect. Its output influences odometry, which navigation and mapping consume. It is never a movement authority: valid IMU data does not permit motion, and missing, stale, saturated, or uncalibrated IMU data keeps every dependent function from declaring itself ready.

Proposed commissioning stages for the HomeMy contract, all motorless until I5:

1. I0: verify device identity, adapter, permissions, and read-only access on a dedicated port.
2. I1: validate the protocol decoder, timeouts, and stale-data handling with synthetic frames.
3. I2: record stationary data cold and warm; derive HomeMy bias and noise values.
4. I3: confirm axis mapping and signs by hand rotation with motor power removed.
5. I4: run fusion in shadow mode and compare it with encoder and LiDAR observations without using it for control.
6. I5: only after drivebase commissioning and explicit human approval, validate fused odometry in bounded supervised motion.

## 6. Risks and Rollback

Risks: gyro bias drift with temperature and vibration, wrong axis mapping, timing interaction between three serial buses, hidden coupling to the source exploration stack, and overconfidence from source test counts.

Rollback: remove the state-estimation service from composition and return to the documented encoder-only odometry profile, or keep motion disabled if no such profile is commissioned. Do not copy source calibration, covariance, or timing values as a shortcut.

## Next Safe Step

Write the HomeMy IMU commissioning contract in `contracts/hardware/` before porting code, then port only the read-only protocol decoder with synthetic tests (I1).
