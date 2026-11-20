# HWT601 IMU Commissioning Contract

Status: proposed for HomeMy. Reader and yaw-rate aid are implemented in `src/homemy_state_estimation` and tested in simulation against a simulated sensor (2026-11-20). As delivered, the IMU influences nothing: the odometry comes from the wheels alone. No mount, axis, scale, bias, or noise value is measured; nothing has run on the HomeMy IMU.
Owner: HomeMy sensor integration.
Source reference: chris01-byte/Roboter_ws `src/robot_state_estimation/` at development commit `08a4b9ac0b7a128ced2199f20976f3aa92ea55fe` (not on main). Transfer record: `docs/transfers/roboter_ws/2026-11-16-hwt601-imu-state-estimation.md`.

## Scope

HomeMy uses the same HWT601-AGV-485 as the source robot: six axes, Modbus RTU over RS485, no absolute heading. Its one purpose is the chassis yaw rate for the odometry. Wheel encoders cannot see the chassis turning on a tile joint or on a slipping wheel; the source robot measured -3.2 degrees of chassis yaw over one joint while its encoders reported +0.006 degrees.

Out of scope: orientation or heading from the sensor, tilt detection, a scan gate against tilt, and any use of the IMU as a condition for or against motion.

## Safe Default

- The reader only reads: Modbus function 0x03, six motion registers from 0x34. No write function exists in the code, so the sensor's settings and calibration cannot be changed.
- The IMU has its own USB-RS485 adapter and device name (`/dev/homemy_imu`). The reader refuses the device of the drive (`/dev/homemy_drive`) and of the LiDAR (`/dev/homemy_lidar`), also under any other name that leads to the same device.
- The IMU commands nothing and permits nothing. Valid IMU data never opens the motion gate.
- Fusion is opt-in (`use_imu_fusion:=true`). Without it the drive driver alone owns `/odom` and `odom -> base_link`, and the gyro is only compared with the wheels (shadow mode).

## Chain

```
HWT601 --RS485--> hwt601_imu --/imu/data_raw--> yaw_rate --/imu/yaw_rate--> (opt-in) EKF --> /odom, odom -> base_link
                                                    ^
                                 wheel odometry ----+   (standstill, comparison)
```

| Topic | Type | Content |
| --- | --- | --- |
| `/imu/data_raw` | `sensor_msgs/Imu`, frame `imu_link` | acceleration and angular rate in the sensor's own axes; no orientation |
| `/homemy/imu/status_json` | `std_msgs/String` | reader: connected, fresh, rate, accepted and rejected samples |
| `/imu/yaw_rate` | `sensor_msgs/Imu`, frame `base_link` | only `angular_velocity.z`: chassis yaw rate with the bias removed |
| `/homemy/imu/yaw_rate_status_json` | `std_msgs/String` | ready, reason, bias, and the totals of gyro yaw and wheel yaw since the bias was learned |

## Required Behavior

- **Reader.** Unchanged from the source: 100 Hz polling, one deadline for the whole answer, checksum and address checks, saturated values rejected, time stamps strictly increasing. After three failed readings it closes the port and reconnects once per second.
- **Bias.** The gyro's zero offset is learned only while the wheel odometry reports standstill (below 0.005 m/s and 0.005 rad/s for 1 s) over a window of 5 s. A window with too much scatter or an implausibly large mean is rejected and tried again. Afterwards the bias follows slowly (30 s time constant) while standing, and is frozen while the wheels turn. If the wheels stand but the gyro turns faster than 0.03 rad/s, somebody is moving the robot: nothing is learned.
- **No output without a bias.** Before the first bias, and with stale, invalid, or backward-stamped samples, `/imu/yaw_rate` carries nothing.
- **Mounting.** One parameter names the sensor axis that is vertical, one its sign. Both are HomeMy measurements (step I3).
- **Fusion (opt-in).** A planar EKF (`robot_localization`) takes forward speed from the wheels and the yaw rate from both, the gyro with about 75 times the weight of the wheels. If the gyro falls silent, the wheels' yaw rate carries on, which is the odometry HomeMy has without the IMU. The source robot instead refused any fallback to encoder yaw; HomeMy chooses the fallback because its default odometry is the encoder odometry anyway, and a frozen heading would be worse.

The thresholds are proposals. Bias and noise limits are results of step I2, the weights of step I4.

## Required Measurements and Confirmation

| Area | Required HomeMy evidence |
| --- | --- |
| Device | adapter identity, udev rule, permissions, baud rate and address of the delivered sensor |
| Mount | place on the chassis, which sensor axis is vertical and its sign, rigidity; the CAD model has no IMU place yet |
| Scale | a full turn by hand must read 360 degrees; the data-sheet scales (4 g, 400 deg/s) are candidates |
| Bias and noise | stationary recordings cold and warm; limits for the bias window |
| Timing | observed rate and answer times on the HomeMy computer, with the drive bus and the LiDAR running |
| Fusion | comparison of gyro, wheels, and LiDAR over turns and over a tile joint before the fused odometry is used |

## Commissioning Sequence

All steps are without motors until I5.

1. I0: device name, permissions, and read-only access on the IMU's own adapter; the reader reports ready.
2. I1: rate, freshness, and behaviour with the cable pulled and plugged in again.
3. I2: stationary recordings cold and warm; set the bias and noise limits.
4. I3: with motor power removed, turn the robot by hand: a turn to the left must give a positive yaw rate, and a full turn 360 degrees. Set axis, sign, and scale.
5. I4: shadow mode while the robot is driven with the controller: compare the totals of gyro and wheels, also over a tile joint.
6. I5: only after drivebase commissioning and explicit approval of a person present: fused odometry in bounded, supervised motion.

A failed step keeps the fusion off. The robot then drives with encoder odometry as before.

## Implementation Status (2026-11-20)

- `hwt601_protocol.py` is the source decoder, unchanged. `hwt601_transport.py` has the source's read path unchanged; the guard against foreign ports uses HomeMy's device names instead of the source robot's alias and adapter serial number. `hwt601_imu_node.py` keeps the source's polling, time stamping, and error handling; the source's experimental development contract is left out.
- The yaw-rate aid is new and small. It follows the source's principle (bias only at standstill, frozen in motion, no output before). Different from the source: standstill comes from the wheel odometry, not from a declaration by the operator.
- The source's fusion health supervision, hold and recovery budgets, and mission-gate coupling are not ported.
- Mount, axis, sign, scale, bias limits, and filter weights of the source are not taken over.

Validated in simulation only:

- the 28 source tests of decoder and transport (two of them rewritten for HomeMy's device names), and 26 tests of the yaw-rate aid and the configuration;
- a simulated HWT601 on a simulated RS485 line (`src/homemy_simulation/homemy_simulation/hwt601_sim.py`), mounted upside down, with offset and noise; the real reader reads it through a pseudo-terminal;
- `src/homemy_bringup/test/test_imu_sim.py`, shadow mode: the reader only reads (not one request other than function 0x03 in more than a thousand); no yaw rate before the bias is learned; over a full turn in place the gyro total was within 0.1 degrees of the truth while the wheels were 11 degrees off (the simulated chassis differs from the nominal dimensions by 2 % and 1 %); a 5-degree turn of the chassis without the wheels was seen by the gyro and not by the wheels; a pulled cable and a broken checksum were noticed within a second, gave no yaw rate, and healed by themselves with the learned bias kept;
- the same test, fused: after a full turn plus the 5-degree kick the fused odometry was within 0.1 degrees of the truth and the wheels alone 6 degrees off; with the gyro silent the fused odometry kept turning with the wheels.

The simulated sensor follows the registers and scales the source reader was written for. It is no evidence about the HomeMy sensor's bias, noise, timing, or mounting.

## Open Points

- The IMU's place on the chassis, and with it axis and sign.
- A third isolated USB-RS485 adapter and the sensor's supply (transfer record).
- Whether HomeMy needs the source's scan gate against tilt: with the LiDAR 0.16 m above the floor, a tilt of 3 degrees reaches the floor at about 3 m.
- In fused mode nothing yet tells the motion gate that the odometry lost its gyro; the fallback to the wheels covers it.

## Rollback

Start without `use_imu_fusion`, or remove the IMU launch from the robot composition. The drive driver then owns `/odom` and `odom -> base_link` again. Do not copy source calibration, covariance, or timing values as a shortcut.
