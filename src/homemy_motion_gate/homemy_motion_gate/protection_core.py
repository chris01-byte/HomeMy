"""Reactive obstacle protection: does a drive command lead into an obstacle?

The check simulates the robot outline along the commanded motion for a short
horizon and asks whether any measured obstacle point would come closer to
the outline than a safety margin. It looks only at the commanded motion, so
moving away from an obstacle stays possible (backing out of a stop), and it
needs no object recognition.

Pure Python and numpy; no ROS. Points are in base_link (X forward, Y left).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Tuple

import numpy as np


@dataclass(frozen=True)
class Outline:
    """Rounded-rectangle outline of the robot in base_link, metres."""

    x_min: float
    x_max: float
    y_half: float
    corner_radius: float

    def __post_init__(self) -> None:
        if not (self.x_max > self.x_min and self.y_half > 0):
            raise ValueError("outline must have positive size")
        half_x = (self.x_max - self.x_min) / 2
        if not 0 <= self.corner_radius <= min(half_x, self.y_half):
            raise ValueError("corner radius does not fit the outline")

    def signed_distance(self, points: np.ndarray) -> np.ndarray:
        """Distance from each point to the outline; negative inside."""

        points = np.asarray(points, dtype=float).reshape(-1, 2)
        centre = np.array([(self.x_max + self.x_min) / 2, 0.0])
        half = np.array([(self.x_max - self.x_min) / 2, self.y_half]) - self.corner_radius
        q = np.abs(points - centre) - half
        outside = np.linalg.norm(np.maximum(q, 0.0), axis=1)
        inside = np.minimum(np.max(q, axis=1), 0.0)
        return outside + inside - self.corner_radius

    def max_radius(self) -> float:
        """Largest distance from the base_link origin to the outline."""

        r = self.corner_radius
        corners = [
            (self.x_max - r, self.y_half - r),
            (self.x_min + r, self.y_half - r),
        ]
        return max(math.hypot(x, y) for x, y in corners) + r


@dataclass(frozen=True)
class ProtectionResult:
    allowed: bool
    nearest_m: float  # current distance of the nearest point to the outline
    reason: str  # "clear", "no_motion", "obstacle"


class FootprintGuard:
    """Blocks a command when it would bring an obstacle within ``margin_m``.

    A point counts against the command only if the motion brings it closer
    than the margin *and* closer than it is now. A point that is already
    within the margin therefore blocks motion towards it but not motion away
    from it.
    """

    def __init__(
        self,
        outline: Outline,
        margin_m: float,
        horizon_s: float,
        step_s: float = 0.05,
        min_lookahead_m: float = 0.05,
    ) -> None:
        for name, value in (("margin_m", margin_m), ("horizon_s", horizon_s), ("step_s", step_s)):
            if not (math.isfinite(value) and value > 0):
                raise ValueError(f"{name} must be positive")
        if not (math.isfinite(min_lookahead_m) and min_lookahead_m >= 0):
            raise ValueError("min_lookahead_m must not be negative")
        if step_s > horizon_s:
            raise ValueError("step_s must not exceed horizon_s")
        self.outline = outline
        self.margin_m = margin_m
        self.horizon_s = horizon_s
        self.step_s = step_s
        self.min_lookahead_m = min_lookahead_m

    def poses(self, v: float, w: float) -> np.ndarray:
        """Robot poses (x, y, yaw) along the command, from the first step on.

        The horizon is stretched so that the robot travels at least
        ``min_lookahead_m``, which keeps the check meaningful at creeping speed.
        """

        horizon = self.horizon_s
        if abs(v) > 1e-9:
            horizon = max(horizon, self.min_lookahead_m / abs(v))
        steps = max(1, int(math.ceil(horizon / self.step_s)))
        t = np.arange(1, steps + 1) * (horizon / steps)
        yaw = w * t
        if abs(w) > 1e-9:
            x = v / w * np.sin(yaw)
            y = v / w * (1.0 - np.cos(yaw))
        else:
            x = v * t
            y = np.zeros_like(t)
        return np.stack((x, y, yaw), axis=1)

    def check(self, v: float, w: float, points: np.ndarray) -> ProtectionResult:
        points = np.asarray(points, dtype=float).reshape(-1, 2)
        points = points[np.isfinite(points).all(axis=1)]
        if len(points) == 0:
            nearest = math.inf
        else:
            now = self.outline.signed_distance(points)
            nearest = float(now.min())
        if abs(v) < 1e-6 and abs(w) < 1e-6:
            return ProtectionResult(True, nearest, "no_motion")
        if len(points) == 0:
            return ProtectionResult(True, nearest, "clear")

        # Only points that the outline can reach within the horizon matter.
        reach = self.outline.max_radius() + self.margin_m + abs(v) * max(
            self.horizon_s, self.min_lookahead_m / max(abs(v), 1e-9)
        )
        near = np.hypot(points[:, 0], points[:, 1]) <= reach
        if not near.any():
            return ProtectionResult(True, nearest, "clear")
        candidates = points[near]
        distance_now = self.outline.signed_distance(candidates)

        for x, y, yaw in self.poses(v, w):
            c, s = math.cos(yaw), math.sin(yaw)
            shifted = candidates - np.array([x, y])
            local = np.stack(
                (c * shifted[:, 0] + s * shifted[:, 1], -s * shifted[:, 0] + c * shifted[:, 1]),
                axis=1,
            )
            distance = self.outline.signed_distance(local)
            closing = (distance < self.margin_m) & (distance < distance_now - 1e-4)
            if closing.any():
                return ProtectionResult(False, nearest, "obstacle")
        return ProtectionResult(True, nearest, "clear")


def scan_to_points(
    ranges: np.ndarray,
    angle_min: float,
    angle_increment: float,
    range_min: float,
    range_max: float,
    sensor_xy: Tuple[float, float],
    sensor_yaw: float,
) -> np.ndarray:
    """LaserScan ranges to base_link points; drops NaN, inf, and out-of-range values."""

    ranges = np.asarray(ranges, dtype=float)
    angles = angle_min + np.arange(len(ranges)) * angle_increment + sensor_yaw
    valid = np.isfinite(ranges) & (ranges >= range_min) & (ranges <= range_max)
    r = ranges[valid]
    a = angles[valid]
    return np.stack(
        (sensor_xy[0] + r * np.cos(a), sensor_xy[1] + r * np.sin(a)), axis=1
    )
