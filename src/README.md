# ROS 2 Source Packages

HomeMy-owned ROS 2 packages for ROS 2 Jazzy. Package names and boundaries follow accepted contracts, not a bulk import.

## Existing Packages

| Package | Purpose | Origin |
| --- | --- | --- |
| `homemy_map_manager` | versioned map store for the app | ported from Amadeus `robot_map_manager` at `05439c7` |
| `homemy_room_manager` | rooms drawn in the app, bound to one map version | ported from Amadeus `semantic_map_manager` at `05439c7` |
| `homemy_mapping_mode` | mapping mode switched from the app | new |
| `homemy_simulation` | stand-ins for SLAM, controller, and lifecycle; simulation only | new |
| `homemy_bringup` | launch profiles `app_backend` and `app_sim`, end-to-end test | new |

None of them drives a motor or publishes a velocity command. They implement `contracts/api/app-bridge.md`.

```bash
colcon build --base-paths src
colcon test --base-paths src
```

## Intended Roles

- homemy_interfaces: stable messages, services, and actions.
- homemy_bringup: launch composition, profiles, and safe defaults.
- homemy_core: hardware-independent mission and state logic.
- homemy_capability_name: one bounded sensor, actuator, perception, or integration capability per package.

## Appliance Roles Planned

- homemy_boot_manager: lifecycle state machine, bounded health checks, and customer-mode readiness decision. It publishes the lifecycle state that the ESP32 shows on the LED strip.
- homemy_power_link: heartbeat and lifecycle state to the ESP32 in the power management unit, which drives the LED strip. Error code, message, and next action reach the app, not a display.
- homemy_bringup: local stack composition for developer and customer profiles; it must begin in a safe state.

ROS packages expose explicit startup, readiness, failure, and shutdown behavior. They must not require a desktop session, shell startup file, open terminal, or interactive input.

## Deployment Boundary

systemd unit and target templates belong in deployment/systemd. Package code remains independently testable in simulation; it must not use a desktop autologin or an interactive terminal as its production supervisor.

## Package Admission

A new package needs an owner, a contract, unit tests, a simulation or motorless path, and an explicit statement of real-hardware impact. A transferred package must first appear in the transfer manifest.

## Boundary Rule

Hardware access stays behind narrow adapters. Mission and application code consume contracts rather than device-specific topics or parameters.
