"""Yaw rate of the chassis from the gyro, for the odometry. Pure Python; no ROS.

Why: wheel encoders cannot see the chassis turning on a tile joint or on a
slipping wheel. Amadeus measured -3.2 degrees of chassis yaw over one joint
while the encoders reported +0.006 degrees. The gyro sees it.

What this does, and nothing more:

- picks the sensor axis that points up and gives it the robot's sign;
- learns the gyro's zero offset (bias) while the wheels stand still, and
  freezes it while they turn;
- gives out the corrected yaw rate only once a bias is known;
- keeps two running totals since then, the yaw seen by the gyro and the yaw
  seen by the wheels, so that the two can be compared without using the gyro
  for anything (shadow mode).

Design after the Amadeus yaw shadow path (Roboter_ws 08a4b9a). Different
here: standstill comes from the wheel odometry, not from a declaration by
the operator.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

AXES = {"x": 0, "y": 1, "z": 2}


@dataclass(frozen=True)
class YawRateConfig:
    yaw_axis: str = "z"                      # sensor axis along the robot's vertical
    yaw_sign: float = 1.0                    # +1: that axis points up, -1: down
    standstill_linear_mps: float = 0.005
    standstill_angular_radps: float = 0.005
    standstill_settle_s: float = 1.0         # wheels still for this long before samples count
    bias_window_s: float = 5.0               # still samples needed for the first bias
    bias_time_constant_s: float = 30.0       # slow tracking while standing afterwards
    bias_max_abs_radps: float = 0.05         # a larger offset is a fault, not a bias
    bias_max_stddev_radps: float = 0.01      # more scatter: the robot was moved during the window
    moved_by_hand_radps: float = 0.03        # wheels still, gyro turning: no bias learning
    input_timeout_s: float = 0.3

    def validate(self) -> None:
        if self.yaw_axis not in AXES:
            raise ValueError("yaw_axis must be x, y, or z")
        if self.yaw_sign not in (1.0, -1.0):
            raise ValueError("yaw_sign must be +1 or -1")
        for name in (
            "standstill_linear_mps", "standstill_angular_radps", "standstill_settle_s", "bias_window_s",
            "bias_time_constant_s", "bias_max_abs_radps", "bias_max_stddev_radps", "moved_by_hand_radps",
            "input_timeout_s",
        ):
            value = getattr(self, name)
            if not (math.isfinite(value) and value > 0.0):
                raise ValueError(f"{name} must be positive and finite")


class YawRateAid:
    def __init__(self, config: YawRateConfig) -> None:
        config.validate()
        self.config = config
        self.axis = AXES[config.yaw_axis]
        self.bias: Optional[float] = None
        self.reason = "waiting_for_standstill"
        self._window: List[Tuple[float, float]] = []
        self._wheel_at: Optional[float] = None
        self._wheel = (0.0, 0.0)
        self._still_since: Optional[float] = None
        self._last_imu_at: Optional[float] = None
        self.gyro_yaw = 0.0
        self.wheel_yaw = 0.0
        self.bias_updates = 0
        self.rejected_windows = 0
        self._last_rejection: Optional[str] = None

    # ------------------------------------------------------------- wheels
    def on_wheel(self, stamp_s: float, linear_mps: float, angular_radps: float) -> None:
        if not all(math.isfinite(v) for v in (stamp_s, linear_mps, angular_radps)):
            self._wheel_at = None
            self._still_since = None
            return
        if self._wheel_at is not None and self.bias is not None:
            span = stamp_s - self._wheel_at
            if 0.0 < span <= self.config.input_timeout_s:
                self.wheel_yaw += angular_radps * span
        still = (
            abs(linear_mps) <= self.config.standstill_linear_mps
            and abs(angular_radps) <= self.config.standstill_angular_radps
        )
        if not still:
            self._still_since = None
        elif self._still_since is None:
            self._still_since = stamp_s
        self._wheel_at = stamp_s
        self._wheel = (linear_mps, angular_radps)

    def standing(self, now_s: float) -> bool:
        """The wheels have been still, and reported so recently, for the settle time."""

        if self._wheel_at is None or self._still_since is None:
            return False
        if now_s - self._wheel_at > self.config.input_timeout_s:
            return False
        return now_s - self._still_since >= self.config.standstill_settle_s

    # ---------------------------------------------------------------- gyro
    def on_imu(self, stamp_s: float, angular_velocity: Sequence[float]) -> Optional[float]:
        """One gyro sample. Returns the corrected yaw rate, or None while there is none to trust."""

        values = tuple(angular_velocity)
        if len(values) != 3 or not math.isfinite(stamp_s) or not all(math.isfinite(v) for v in values):
            self.reason = "invalid_imu_sample"
            return None
        if self._last_imu_at is not None and stamp_s <= self._last_imu_at:
            self.reason = "imu_time_not_increasing"
            return None
        span = None if self._last_imu_at is None else stamp_s - self._last_imu_at
        self._last_imu_at = stamp_s
        raw = self.config.yaw_sign * values[self.axis]
        gap = span is not None and span > self.config.input_timeout_s

        if self.standing(stamp_s) and not gap:
            self._learn(stamp_s, raw, span)
        else:
            self._window.clear()
            if self.bias is None:
                self._last_rejection = None
                self.reason = "waiting_for_standstill"

        if self.bias is None:
            return None
        rate = raw - self.bias
        if span is not None and not gap:
            self.gyro_yaw += rate * span
        self.reason = "ok"
        return rate

    def _learn(self, stamp_s: float, raw: float, span: Optional[float]) -> None:
        config = self.config
        if self.bias is not None:
            residual = raw - self.bias
            if abs(residual) <= config.moved_by_hand_radps and span is not None:
                self.bias += residual * min(1.0, span / config.bias_time_constant_s)
            return
        self._window.append((stamp_s, raw))
        if stamp_s - self._window[0][0] < config.bias_window_s:
            # After a rejected window the cause stays visible while the next one runs.
            self.reason = self._last_rejection or "learning_bias"
            return
        samples = [value for _, value in self._window]
        mean = sum(samples) / len(samples)
        deviation = math.sqrt(sum((value - mean) ** 2 for value in samples) / len(samples))
        self._window.clear()
        if deviation > config.bias_max_stddev_radps:
            self.rejected_windows += 1
            self.reason = self._last_rejection = "bias_window_unsteady"
        elif abs(mean) > config.bias_max_abs_radps:
            self.rejected_windows += 1
            self.reason = self._last_rejection = "bias_implausibly_large"
        else:
            self.bias = mean
            self.bias_updates += 1
            self._last_rejection = None
            self.gyro_yaw = 0.0
            self.wheel_yaw = 0.0

    # -------------------------------------------------------------- status
    def status(self, now_s: float) -> dict:
        fresh = self._last_imu_at is not None and now_s - self._last_imu_at <= self.config.input_timeout_s
        ready = self.bias is not None and fresh
        return {
            "ready": ready,
            "reason": self.reason if fresh else "imu_stale",
            "bias_radps": self.bias,
            "standing": self.standing(now_s),
            "rejected_bias_windows": self.rejected_windows,
            "gyro_yaw_deg": math.degrees(self.gyro_yaw),
            "wheel_yaw_deg": math.degrees(self.wheel_yaw),
            "gyro_minus_wheel_yaw_deg": math.degrees(self.gyro_yaw - self.wheel_yaw),
        }
