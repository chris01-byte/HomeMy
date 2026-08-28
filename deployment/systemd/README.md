# systemd Deployment

Status: layout only. No unit or target is installed, enabled, or tested.

This directory will hold HomeMy-owned systemd unit and target templates once the first local end-to-end simulation path exists. It is the deployment boundary between packaged HomeMy software and the operating system.

## Intended Units

- homemy.target: customer appliance target.
- homemy-boot-manager.service: lifecycle state machine and self-test coordinator.
- homemy-status-display.service: customer-visible state and fault display.
- homemy-local-stack.target: local ROS 2 and hardware services.
- homemy-ai-health.service: bounded external AI health supervision.

## Rules

Unit files must use explicit paths, a non-interactive service account, deterministic environment files, restart policy, ordered dependencies, and journald logging. They must not depend on a desktop login, shell startup files, a developer terminal, or embedded credentials.

Developer mode stays on graphical.target. Customer mode remains inactive until simulation, cold boot, fault display, safe shutdown, and hardware safety checks have been proven.

## Installation Boundary

Versioned templates live here. An explicit deployment process will later install them into the operating-system unit directory. The repository must not treat this directory as proof that a customer-mode system is enabled.
