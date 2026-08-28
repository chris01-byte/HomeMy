# Hardware Foundation Transfer Candidates

Status: proposed for staged adaptation; no HomeMy code copied.
Source baseline: chris01-byte/Roboter_ws main at commit 05439c7a13d7a92e69b9eb4663e3a2a1b44626a1.

## Scope Approved for Assessment

The user has approved assessment and staged adaptation of the ESS23-RS drive base, STL-27L LiDAR, and local OAK camera foundation. The external AI server and its connection are actively being changed elsewhere and are out of scope.

## ESS23-RS Drive Base

Source: src/base_hardware/.
Planned HomeMy destination: src/homemy_drivebase/.

Portable candidates:

- Modbus protocol handling for the ESS23-RS controllers.
- Absolute encoder-position odometry, input validation, watchdog behavior, and fail-closed error paths.
- Dry-run-first startup, explicit RS485 enable, and source tests as a regression reference.

Must be measured or confirmed on the completed HomeMy chassis before any real-motion profile:

- wheel radius, effective track width, physical wheel positions, and the complete URDF and footprint;
- gear ratio and motion limits, even if the motor controller is the same;
- motor IDs, RS485 device path, left/right inversion, encoder word order, and verified encoder counts;
- acceleration, braking, start RPM, speed limits, and all odometry uncertainty values;
- emergency-stop, motion-gate, and independent safety-controller integration.

Do not copy the Amadeus calibration values, physical dimensions, device aliases, or real-motion configuration. HomeMy begins with a non-moving commissioning profile.

## STL-27L LiDAR

Source: src/amadeus_lidar_bringup/ and its pinned vendor manifest.
Planned HomeMy destination: src/homemy_lidar_bringup/.

Portable candidates:

- Driver integration and package structure.
- Scan normalization for the sensor's varying beam count.
- Tests and diagnostics for scan direction, masks, and normalized output.

Must be measured or revalidated on the new chassis:

- sensor frame position and yaw, mast geometry, and masked sectors;
- the coupled scan-direction and frame-yaw contract;
- USB identity, udev rule, driver version, scan rate, and time behavior on the new Linux computer;
- all navigation and safety assumptions consuming the scan.

The known source pairing laser_scan_dir=true and tf_yaw=+1.5708 is not a portable chassis constant. It must be verified as a pair after the LiDAR is mounted.

## OAK Camera Foundation

Source candidates: local OAK bring-up and rectification portions of src/robot_bringup/.
Planned HomeMy destination: a future homemy_oak_bringup package.

The same OAK hardware may be prepared for local camera bring-up, device diagnostics, and frame calibration. No remote image relay, semantic-perception backend, CycloneDDS peer configuration, server deployment, LLM planner, or AI-network configuration may be copied or modified. A future OAK 4D upgrade requires a separate camera, frame, bandwidth, and safety contract rather than assuming OAK-D-S2 parameters transfer.

## Explicitly Excluded

- External AI server, network transport, peer addresses, credentials, and deployment.
- Semantic perception, remote image relay, LLM planning, and off-board inference behavior.
- Real maps, home data, ROS bags, camera recordings, and current deployment files.
- Any current robot-description geometry, Nav2 footprint, or calibrated navigation parameter.

## Other Candidates Requiring User Approval

- VL53 near-field protection and its CH341/DKMS dependency. This is valuable safety work, but only if HomeMy uses the same sensors and the new Linux platform is separately validated.
- robot_interfaces message definitions, after HomeMy package ownership is fixed.
- safety_monitor, mission gate, and behavior-tree patterns, after the HomeMy safety-chain topology is decided.
- robot_navigation, global localization, and exploration algorithms, only after the new footprint, sensor frames, and navigation requirements are measured.
- map managers, semantic rooms, app, and UI functions, only if the HomeMy customer workflow needs them.

## Next Safe Step

Create HomeMy commissioning contracts and synthetic tests for the drive base and LiDAR. Port only the smallest hardware-independent code slice after those contracts exist. Real hardware verification waits for the completed chassis and explicit human approval.
