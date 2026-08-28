# STL-27L LiDAR Commissioning Contract

Status: proposed for HomeMy; no source code, navigation profile, or mounted-frame value copied.
Owner: HomeMy sensor integration.
Source reference: chris01-byte/Roboter_ws src/amadeus_lidar_bringup/ and vendor_ldlidar_stl_ros2.repos at commit 05439c7a13d7a92e69b9eb4663e3a2a1b44626a1.

## Scope

HomeMy uses the same STL-27L LiDAR model as the source robot. Driver integration, scan normalization, and diagnostics are candidates for staged adaptation. The new chassis changes the physical relation between LiDAR and robot, so all frame, mask, and consumer assumptions are HomeMy measurements.

## Safe Default

Initial LiDAR work is sensor-only and motorless. A running LiDAR, a valid scan, or an available map never authorizes motion. The sensor status is a required input to future safety and navigation contracts, not a replacement for them.

## Portable Behavior Candidates

- Pinned source-vendor manifest and repeatable driver setup process.
- Driver bring-up and raw scan health observation.
- Scan normalization from varying source beam counts to a fixed angle grid.
- Diagnostics and tests for scan direction, masked values, timestamps, and normalized output.

The source found that the STL-27L does not always publish the same beam count. The normalizer is therefore a candidate safety and mapping dependency, not merely a display refinement.

## Required Measurements and Confirmation

Record these values only after the LiDAR is installed on the finished HomeMy chassis:

| Area | Required HomeMy evidence |
| --- | --- |
| Mount | measured LiDAR position and orientation relative to base_link, including height, yaw, roll, pitch, and mechanical rigidity |
| Scan direction | confirmed direction from a physical directional test; driver configuration and frame yaw are checked together |
| Masking | exact chassis, mast, cable, and self-occlusion sectors; verify the driver representation of masked returns |
| Data quality | scan frequency, beam-count variation, range behavior, timestamp age, and behavior after USB reconnect |
| Platform | device identity, udev rule, user permissions, driver version, and behavior on the new Linux computer |
| Consumers | all later TF, SLAM, Nav2, collision, and diagnostics consumers use the HomeMy frame and no old source geometry |

The source pairing laser_scan_dir=true and tf_yaw=+1.5708 is evidence about the source installation only. It must not be copied as a HomeMy calibration constant and may only be accepted or replaced as one coupled, measured result.

## Commissioning Sequence

1. L0: with motion disabled, verify USB identity, permissions, driver provenance, and clean start and stop behavior.
2. L1: verify raw scans, timestamps, range data, and the actual beam-count distribution while stationary.
3. L2: verify normalized output on a fixed angle grid and test masked-return handling with synthetic input.
4. L3: use a physical directional target to validate scan direction and the complete LiDAR-to-base frame transform together.
5. L4: characterize chassis and mast occlusion, then verify the intended mask against live scans.
6. L5: test reconnect, stale-data detection, and a controlled sensor-loss fault without enabling motion.
7. L6: only after the drivebase, footprint, and safety contracts are commissioned, validate the LiDAR in a separate navigation integration test.

A missing, stale, ambiguous, or invalid scan prevents any dependent future capability from declaring itself ready. It does not justify changing mount parameters by guesswork.

## Validation

Ported software must pass source-derived and HomeMy-specific synthetic tests for variable beam count, interpolation, direction, invalid ranges, masked values, stale timestamps, and endpoint restart. Hardware acceptance requires measured HomeMy values; prior source results are only evidence for what to test.

## Rollback

Disable the HomeMy LiDAR bring-up or retain its sensor-only profile. Do not restore source mount values, map configuration, or navigation settings as a shortcut. Any rollback keeps motion disabled unless its separate contracts remain satisfied.
