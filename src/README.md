# ROS 2 Source Packages

This directory will contain HomeMy-owned ROS 2 packages. It starts deliberately empty: package names and boundaries follow accepted contracts, not a bulk import.

## Intended Roles

- `homemy_interfaces`: stable messages, services, and actions.
- `homemy_bringup`: launch composition, profiles, and safe defaults.
- `homemy_core`: hardware-independent mission and state logic.
- `homemy_<capability>`: one bounded sensor, actuator, perception, or integration capability per package.

## Package Admission

A new package needs an owner, a contract, unit tests, a simulation or motorless path, and an explicit statement of real-hardware impact. A transferred package must first appear in the transfer manifest.

## Boundary Rule

Hardware access stays behind narrow adapters. Mission and application code consume contracts rather than device-specific topics or parameters.
# ROS 2 Source Packages

This directory will contain HomeMy-owned ROS 2 packages. It starts deliberately empty: package names and boundaries follow accepted contracts, not a bulk import.

## Intended Roles

- homemy_interfaces: stable messages, services, and actions.
- homemy_bringup: launch composition, profiles, and safe defaults.
- homemy_core: hardware-independent mission and state logic.
- homemy_<capability>: one bounded sensor, actuator, perception, or integration capability per package.

## Package Admission

A new package needs an owner, a contract, unit tests, a simulation or motorless path, and an explicit statement of real-hardware impact. A transferred package must first appear in the transfer manifest.

## Boundary Rule

Hardware access stays behind narrow adapters. Mission and application code consume contracts rather than device-specific topics or parameters.
