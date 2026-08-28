# Hardware Foundation and Navigation Transfer Candidates

Status: proposed for staged adaptation; no HomeMy code copied.
Source baseline: chris01-byte/Roboter_ws main at commit 05439c7a13d7a92e69b9eb4663e3a2a1b44626a1.

## Scope Approved for Assessment

The user has approved assessment and staged adaptation of the ESS23-RS drive base, STL-27L LiDAR, local OAK camera foundation, and robot_navigation. The external AI server and its connection are actively being changed elsewhere and are out of scope. VL53 near-field hardware is not part of HomeMy.

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

## Local OAK Camera Foundation

Source candidates: local OAK bring-up and rectification portions of src/robot_bringup/.
Planned HomeMy destination: a future homemy_oak_bringup package.

The same OAK hardware may be prepared for local camera bring-up, device diagnostics, and frame calibration. No remote image relay, semantic-perception backend, CycloneDDS peer configuration, server deployment, LLM planner, or AI-network configuration may be copied or modified. A future OAK 4D upgrade requires a separate camera, frame, bandwidth, and safety contract rather than assuming OAK-D-S2 parameters transfer.

## robot_navigation

Source: src/robot_navigation/.
Planned HomeMy destination: src/homemy_navigation/.
Status: proposed for algorithm and simulation adaptation; no source real-navigation profile is accepted.

Portable candidates:

- hardware-independent Nav2 planning, controller, and dry-run test topology;
- synthetic-map tests, localization checks, and fail-closed readiness patterns;
- navigation diagnostics and algorithms that do not embed Amadeus geometry, map data, or VL53 assumptions.

Required before accepting a HomeMy real-navigation profile:

- measured HomeMy chassis envelope, all fixed protrusions, operating configurations, URDF, and padded Nav2 footprint;
- commissioned ESS23-RS odometry, STL-27L frame, scan normalization, timestamp behavior, and motion limits;
- a separately designed HomeMy obstacle-detection, motion-gate, emergency-stop, and safe-stop chain;
- HomeMy-specific costmaps, sensor layers, controller limits, map rules, and real-world validation.

Do not copy the Amadeus footprint, robot radius, local or global costmaps, static map transform, map files, velocity-smoother values, progress thresholds, or real-navigation launch profile. The source real path uses VL53-dependent obstacle and collision-monitor configuration; that configuration is excluded. A monitor with missing or unsuitable obstacle inputs must never be treated as a valid HomeMy safety chain.

## Explicitly Excluded

- VL53 near-field hardware, the vl53_near_field package, CH341/DKMS support, and source VL53-specific costmap or collision-monitor configuration.
- External AI server, network transport, peer addresses, credentials, and deployment.
- Semantic perception, remote image relay, LLM planning, and off-board inference behavior.
- Real maps, home data, ROS bags, camera recordings, and current deployment files.
- Any current robot-description geometry, Nav2 footprint, or calibrated navigation parameter.

## Deferred Until Needed

- robot_interfaces is a source package for shared custom ROS message and service definitions. It is not a behavior or hardware driver, and no transfer is selected until HomeMy actually needs a matching interface.
- safety_monitor observes safety state in the source project. It is not selected until the HomeMy physical safety and motion-gate topology are decided.
- mission-gate and behavior-tree patterns remain deferred until the HomeMy safety chain and customer workflow are defined.
- map managers, semantic rooms, app, and UI functions remain deferred until the HomeMy customer workflow needs them.

## Next Safe Step

Create a HomeMy navigation geometry and safety commissioning contract, then use synthetic maps and the non-moving drivebase profile to assess the smallest hardware-independent robot_navigation slice. Real hardware verification waits for the completed chassis, new footprint and LiDAR frame measurements, a replacement for the removed VL53 safety assumptions, and explicit human approval.
