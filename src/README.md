# ROS 2 Source Packages

This directory will contain HomeMy-owned ROS 2 packages. It starts deliberately empty: package names and boundaries follow accepted contracts, not a bulk import.

## Intended Roles

- homemy_interfaces: stable messages, services, and actions.
- homemy_bringup: launch composition, profiles, and safe defaults.
- homemy_core: hardware-independent mission and state logic.
- homemy_capability_name: one bounded sensor, actuator, perception, or integration capability per package.

## Appliance Roles Planned

- homemy_boot_manager: lifecycle state machine, bounded health checks, and customer-mode readiness decision.
- homemy_status_display: customer-visible state, error code, message, and next action.
- homemy_bringup: local stack composition for developer and customer profiles; it must begin in a safe state.

ROS packages expose explicit startup, readiness, failure, and shutdown behavior. They must not require a desktop session, shell startup file, open terminal, or interactive input.

## Deployment Boundary

systemd unit and target templates belong in deployment/systemd. Package code remains independently testable in simulation; it must not use a desktop autologin or an interactive terminal as its production supervisor.

## Package Admission

A new package needs an owner, a contract, unit tests, a simulation or motorless path, and an explicit statement of real-hardware impact. A transferred package must first appear in the transfer manifest.

## Boundary Rule

Hardware access stays behind narrow adapters. Mission and application code consume contracts rather than device-specific topics or parameters.
