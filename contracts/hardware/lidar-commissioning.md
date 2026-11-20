# STL-27L LiDAR Commissioning Contract

Status: proposed for HomeMy. The chain from the vendor driver to the masked scan is implemented in `src/homemy_lidar_bringup` and tested in simulation, including the unchanged vendor driver against a simulated device (2026-11-20). As delivered, the real scan reaches no consumer. No mounted-frame value is copied; nothing has run on the HomeMy LiDAR.
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

## Implementation Status (2026-11-20)

Chain: vendor driver `/scan_raw` (frame `lidar_raw`) → `scan_normalize` `/scan` (frame `lidar_link`) → `scan_mask` `/scan_masked` → mapping, localization, obstacle protection.

- **Vendor driver.** `ldlidar_stl_ros2` is pinned to the source robot's commit in `src/homemy_lidar_bringup/vendor/ldlidar_stl_ros2.repos` and built unchanged by `build_vendor_driver.sh`. Under Ubuntu 24.04 (GCC 13) it builds only when the compiler is handed the pthread header the vendor's logger forgets to include; the script does that without touching the source. The driver's own angle crop is off; HomeMy masks in `scan_mask`.
- **Normalisation.** Ported from the source with unchanged principle (nearest input beam, never interpolation), 2160 beams. HomeMy addition: the output grid is robot-aligned in `lidar_link`, and the device's zero direction is one parameter, `yaw_offset_deg`, in the same file as the driver's `laser_scan_dir`. The robot model therefore holds only the LiDAR's position; the raw frame `lidar_raw` is deliberately not in the model.
- **Lock.** `alignment_confirmed` is false as delivered. The normalised scan then goes only to `/scan_unconfirmed`; nothing arrives on `/scan`, so mapping and localization get no scan and the motion gate stays closed for lack of one. The lock is opened only after L3 and L4 have passed on the robot.
- **Check tool.** `lidar_check` only listens: `stats` (L1, L2), `target` (L3), `sectors` (L4, comparison with the mask).
- `yaw_offset_deg` is 0.0 and not measured. The source value of +90 degrees is not taken over.

Validated in simulation only:

- unit tests of the grid, the normaliser node, the check evaluation, and the mask;
- the test stand's simulated LiDAR behaves like the vendor driver (varying beam count, 0 to 360 degrees, device mounted askew, NaN where nothing is measured), and the whole drive simulation (`test_drive_sim_e2e.py`) runs through normalisation and mask;
- `src/homemy_bringup/test/test_lidar_sim.py` runs the unchanged vendor driver: the test stand sends the device's own serial packets (format and checksum read from the vendor driver's source) through a pseudo-terminal. Observed: 18 different beam counts between 2147 and 2167 at about 10 Hz from the driver, a fixed 2160 after normalisation, direction and rotation sense correct against the walls of the test apartment, the robot's own struts and webs exactly inside the six mask sectors, the lock, and loss and return of the data stream (the driver keeps running, reports time-outs, and resumes by itself).

The simulated device follows the packet format the vendor driver reads. It is no evidence about the HomeMy LiDAR's mounting, noise, or USB behaviour.

Observed with the vendor driver: the beam at the device's zero direction stays NaN in most scans (one beam of 2160).

## Design Prediction for Masking

HomeMy mounts the LiDAR inside the base behind an open slot. The CAD-derived blind sectors of the two struts and the slot webs are recorded in `docs/decisions/2026-11-16-lidar-slot-and-support-webs.md`. They are the expected starting point for L4, not accepted mask values. L4 passes only when live scans confirm each sector and its margin.

## Commissioning Sequence

1. L0: with motion disabled, verify USB identity, permissions, driver provenance, and clean start and stop behavior.
2. L1: verify raw scans, timestamps, range data, and the actual beam-count distribution while stationary.
3. L2: verify normalized output on a fixed angle grid and test masked-return handling with synthetic input.
4. L3: use a physical directional target to validate scan direction and the complete LiDAR-to-base frame transform together.
5. L4: characterize chassis, strut, and slot-web occlusion, then verify the intended mask against live scans.
6. L5: test reconnect, stale-data detection, and a controlled sensor-loss fault without enabling motion.
7. L6: only after the drivebase, footprint, and safety contracts are commissioned, validate the LiDAR in a separate navigation integration test.

A missing, stale, ambiguous, or invalid scan prevents any dependent future capability from declaring itself ready. It does not justify changing mount parameters by guesswork.

## Validation

Ported software must pass source-derived and HomeMy-specific synthetic tests for variable beam count, interpolation, direction, invalid ranges, masked values, stale timestamps, and endpoint restart. These pass in simulation as listed above; stale scans are caught by the motion gate's freshness check (`contracts/ros/motion-gate.md`). Hardware acceptance requires measured HomeMy values; prior source results are only evidence for what to test.

## Rollback

Set `alignment_confirmed` back to false, disable the HomeMy LiDAR bring-up, or retain its sensor-only profile. Do not restore source mount values, map configuration, or navigation settings as a shortcut. Any rollback keeps motion disabled unless its separate contracts remain satisfied.
