"""Decision logic of the motion gate. Pure Python; no ROS.

The gate is the one place on HomeMy that lets drive commands reach the
drive. Every cycle it decides afresh from the latest inputs; nothing is
latched here. Only the emergency stop and hardware faults latch, and they
do so in hardware and in the lifecycle state, not in this module
(docs/decisions/2026-11-17-self-healing-and-latching.md).

Rules (contracts/ros/motion-gate.md):

- Exactly one operating mode may drive: mapping (commands from the
  controller) or a drive mission (commands from navigation). Neither or both
  active means closed.
- Every input must be fresh. Missing, stale, malformed, or non-finite input
  closes the gate; it never opens it.
- The lifecycle state must be READY, READY_LIMITED, or OPERATING, and the
  emergency stop must be reported released.
- In mapping mode the controller's radio link must be up.
- In a drive mission the localization must be reported ready.
- The command is clamped to the mode's speed limits.
- The reactive protection may block the command; after a block the command
  passes again only when the protection has been clear for ``clear_time_s``.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Callable, Generic, List, Optional, Tuple, TypeVar

T = TypeVar("T")

MODE_OFF = "off"
MODE_MAPPING = "mapping"
MODE_MISSION = "mission"
MODE_CONFLICT = "conflict"

ALLOWED_LIFECYCLE_STATES = frozenset({"READY", "READY_LIMITED", "OPERATING"})


@dataclass(frozen=True)
class Stamped(Generic[T]):
    value: T
    received_at: float  # monotonic seconds


@dataclass(frozen=True)
class ModeLimits:
    max_linear_mps: float
    max_angular_rps: float

    def __post_init__(self) -> None:
        for value in (self.max_linear_mps, self.max_angular_rps):
            if not (math.isfinite(value) and value > 0):
                raise ValueError("limits must be positive and finite")


@dataclass(frozen=True)
class GateConfig:
    mapping_limits: ModeLimits
    mission_limits: ModeLimits
    mode_timeout_s: float = 1.5
    lifecycle_timeout_s: float = 3.0
    estop_timeout_s: float = 1.0
    controller_link_timeout_s: float = 0.2
    command_timeout_s: float = 0.25
    localization_timeout_s: float = 1.0
    scan_timeout_s: float = 0.3
    clear_time_s: float = 0.5

    def __post_init__(self) -> None:
        for name in (
            "mode_timeout_s",
            "lifecycle_timeout_s",
            "estop_timeout_s",
            "controller_link_timeout_s",
            "command_timeout_s",
            "localization_timeout_s",
            "scan_timeout_s",
        ):
            value = getattr(self, name)
            if not (math.isfinite(value) and value > 0):
                raise ValueError(f"{name} must be positive and finite")
        if not (math.isfinite(self.clear_time_s) and self.clear_time_s >= 0):
            raise ValueError("clear_time_s must not be negative")


@dataclass
class GateInputs:
    mapping_active: Optional[Stamped[bool]] = None
    mission_drive_active: Optional[Stamped[bool]] = None
    lifecycle_state: Optional[Stamped[str]] = None
    estop_pressed: Optional[Stamped[bool]] = None
    controller_link: Optional[Stamped[bool]] = None
    localization_ready: Optional[Stamped[bool]] = None
    teleop_command: Optional[Stamped[Tuple[float, float]]] = None
    nav_command: Optional[Stamped[Tuple[float, float]]] = None
    scan_received_at: Optional[float] = None


@dataclass(frozen=True)
class GateDecision:
    mode: str
    open: bool
    command: Tuple[float, float]  # (linear m/s, angular rad/s) sent to the drive
    reasons: Tuple[str, ...]
    requested: Optional[Tuple[float, float]] = None


def fresh(stamped: Optional[Stamped], now: float, timeout_s: float) -> bool:
    return stamped is not None and 0 <= now - stamped.received_at <= timeout_s


def select_mode(inputs: GateInputs, now: float, config: GateConfig) -> str:
    mapping = fresh(inputs.mapping_active, now, config.mode_timeout_s) and bool(
        inputs.mapping_active.value
    )
    mission = fresh(inputs.mission_drive_active, now, config.mode_timeout_s) and bool(
        inputs.mission_drive_active.value
    )
    if mapping and mission:
        return MODE_CONFLICT
    if mapping:
        return MODE_MAPPING
    if mission:
        return MODE_MISSION
    return MODE_OFF


def clamp(command: Tuple[float, float], limits: ModeLimits) -> Tuple[float, float]:
    v, w = command
    return (
        max(-limits.max_linear_mps, min(limits.max_linear_mps, v)),
        max(-limits.max_angular_rps, min(limits.max_angular_rps, w)),
    )


def precondition_reasons(inputs: GateInputs, now: float, config: GateConfig, mode: str) -> List[str]:
    """Everything that keeps the gate closed before the obstacle check."""

    reasons: List[str] = []
    if mode == MODE_OFF:
        reasons.append("mode_off")
    elif mode == MODE_CONFLICT:
        reasons.append("mode_conflict")

    state = inputs.lifecycle_state
    if state is None:
        reasons.append("lifecycle_missing")
    elif not fresh(state, now, config.lifecycle_timeout_s):
        reasons.append("lifecycle_stale")
    elif state.value not in ALLOWED_LIFECYCLE_STATES:
        reasons.append("lifecycle_not_ready")

    if inputs.estop_pressed is None:
        reasons.append("estop_missing")
    elif not fresh(inputs.estop_pressed, now, config.estop_timeout_s):
        reasons.append("estop_stale")
    elif inputs.estop_pressed.value:
        reasons.append("estop_pressed")

    if inputs.scan_received_at is None or not (
        0 <= now - inputs.scan_received_at <= config.scan_timeout_s
    ):
        reasons.append("scan_stale")

    if mode == MODE_MAPPING:
        if not (fresh(inputs.controller_link, now, config.controller_link_timeout_s)
                and inputs.controller_link.value):
            reasons.append("controller_link_down")
        if not fresh(inputs.teleop_command, now, config.command_timeout_s):
            reasons.append("command_stale")
    elif mode == MODE_MISSION:
        if not (fresh(inputs.localization_ready, now, config.localization_timeout_s)
                and inputs.localization_ready.value):
            reasons.append("localization_not_ready")
        if not fresh(inputs.nav_command, now, config.command_timeout_s):
            reasons.append("command_stale")
    return reasons


def finite_command(command: Tuple[float, float]) -> bool:
    return all(math.isfinite(value) for value in command)


ProtectionCheck = Callable[[float, float], Tuple[bool, str]]


@dataclass
class MotionGate:
    """Stateful wrapper: the only state is the time of the last obstacle block."""

    config: GateConfig
    last_block_at: Optional[float] = field(default=None)

    def step(self, inputs: GateInputs, now: float, protection: ProtectionCheck) -> GateDecision:
        mode = select_mode(inputs, now, self.config)
        reasons = precondition_reasons(inputs, now, self.config, mode)
        requested: Optional[Tuple[float, float]] = None
        if mode == MODE_MAPPING and inputs.teleop_command is not None:
            requested = inputs.teleop_command.value
        elif mode == MODE_MISSION and inputs.nav_command is not None:
            requested = inputs.nav_command.value

        if requested is not None and not finite_command(requested):
            reasons.append("command_invalid")
        if reasons:
            return GateDecision(mode, False, (0.0, 0.0), tuple(reasons), requested)

        limits = self.config.mapping_limits if mode == MODE_MAPPING else self.config.mission_limits
        command = clamp(requested, limits)
        allowed, _detail = protection(*command)
        if not allowed:
            self.last_block_at = now
            return GateDecision(mode, False, (0.0, 0.0), ("obstacle",), requested)
        if command != (0.0, 0.0) and self.last_block_at is not None:
            if 0 <= now - self.last_block_at < self.config.clear_time_s:
                return GateDecision(mode, False, (0.0, 0.0), ("obstacle_clear_wait",), requested)
        return GateDecision(mode, True, command, (), requested)
