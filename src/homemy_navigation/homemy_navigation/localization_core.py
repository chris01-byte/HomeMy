"""Localization logic of HomeMy without ROS.

Two parts:

- which mode the localization should be in: mapping with slam_toolbox,
  holding the last SLAM map until it is saved, or navigating on the saved
  map with AMCL;
- whether the position on the saved map can be trusted ("ready").

The readiness check follows the Amadeus lesson of 2026-08-15: AMCL reported
a pose 1.95 m off with a small covariance, because unknown map cells had
been loaded as free. A covariance alone is therefore no proof. HomeMy also
requires that most LiDAR endpoints land next to an occupied map cell.
"""

from __future__ import annotations

import json
import math
import os
import tempfile
from dataclasses import dataclass
from typing import Optional, Sequence, Tuple

import numpy as np

MODE_IDLE = "idle"  # no map yet
MODE_MAPPING = "mapping"  # slam_toolbox builds a new map
MODE_SLAM_HOLD = "slam_hold"  # mapping ended; the SLAM map waits to be saved
MODE_NAVIGATION = "navigation"  # saved map with AMCL


@dataclass(frozen=True)
class SavedMapRef:
    fingerprint: str
    yaml_path: str
    version: str


def desired_mode(
    mapping_active: bool,
    current: str,
    saved: Optional[SavedMapRef],
    live_fingerprint: Optional[str],
) -> str:
    """The mode the localization should be in now.

    - Mapping mode wins.
    - After mapping, the SLAM map is kept until a saved map has exactly its
      fingerprint; then navigation starts on that saved map. A saved map of
      an earlier run does not replace an unsaved new SLAM map.
    - Without mapping in this session, the newest saved map is used.
    """

    if mapping_active:
        return MODE_MAPPING
    if current in (MODE_MAPPING, MODE_SLAM_HOLD):
        if saved is not None and live_fingerprint is not None and saved.fingerprint == live_fingerprint:
            return MODE_NAVIGATION
        return MODE_SLAM_HOLD
    if saved is not None:
        return MODE_NAVIGATION
    return MODE_IDLE


class OccupancyIndex:
    """Answers "is this point within ``radius_m`` of an occupied cell?" for one map."""

    def __init__(self, data: Sequence[int], width: int, height: int, resolution: float,
                 origin_xy: Tuple[float, float], radius_m: float, occupied_threshold: int = 65) -> None:
        if width <= 0 or height <= 0 or not resolution > 0:
            raise ValueError("invalid map geometry")
        grid = np.asarray(data, dtype=np.int16).reshape(height, width)
        occupied = grid >= occupied_threshold
        cells = max(0, int(math.ceil(radius_m / resolution)))
        near = occupied.copy()
        # Dilation with a disc of the given radius, by shifted copies.
        for dy in range(-cells, cells + 1):
            for dx in range(-cells, cells + 1):
                if dx == 0 and dy == 0 or dx * dx + dy * dy > cells * cells:
                    continue
                shifted = np.zeros_like(occupied)
                ys = slice(max(dy, 0), height + min(dy, 0))
                yd = slice(max(-dy, 0), height + min(-dy, 0))
                xs = slice(max(dx, 0), width + min(dx, 0))
                xd = slice(max(-dx, 0), width + min(-dx, 0))
                shifted[yd, xd] = occupied[ys, xs]
                near |= shifted
        self.near = near
        self.free = grid == 0
        self.width = width
        self.height = height
        self.resolution = resolution
        self.origin = np.asarray(origin_xy, dtype=float)
        self.occupied_cells = int(occupied.sum())

    def agreement(self, points_xy: np.ndarray) -> Tuple[float, int]:
        """Share of the points next to an occupied cell, and how many points counted."""

        points = np.asarray(points_xy, dtype=float).reshape(-1, 2)
        points = points[np.isfinite(points).all(axis=1)]
        if len(points) == 0:
            return 0.0, 0
        idx = np.floor((points - self.origin) / self.resolution).astype(int)
        inside = (idx[:, 0] >= 0) & (idx[:, 0] < self.width) & (idx[:, 1] >= 0) & (idx[:, 1] < self.height)
        hits = np.zeros(len(points), dtype=bool)
        hits[inside] = self.near[idx[inside, 1], idx[inside, 0]]
        return float(hits.mean()), int(len(points))


@dataclass(frozen=True)
class ReadinessConfig:
    acquire_agreement: float = 0.80
    hold_agreement: float = 0.60
    acquire_sigma_xy_m: float = 0.20
    hold_sigma_xy_m: float = 0.30
    acquire_sigma_yaw_deg: float = 10.0
    hold_sigma_yaw_deg: float = 15.0
    minimum_points: int = 50
    acquire_checks: int = 2
    check_timeout_s: float = 1.5

    def __post_init__(self) -> None:
        if not (0 < self.hold_agreement <= self.acquire_agreement <= 1):
            raise ValueError("expected 0 < hold_agreement <= acquire_agreement <= 1")
        if not (0 < self.acquire_sigma_xy_m <= self.hold_sigma_xy_m):
            raise ValueError("expected 0 < acquire_sigma_xy_m <= hold_sigma_xy_m")
        if not (0 < self.acquire_sigma_yaw_deg <= self.hold_sigma_yaw_deg):
            raise ValueError("expected 0 < acquire_sigma_yaw_deg <= hold_sigma_yaw_deg")
        if self.minimum_points < 1 or self.acquire_checks < 1 or not self.check_timeout_s > 0:
            raise ValueError("invalid readiness settings")


@dataclass(frozen=True)
class Check:
    time: float
    agreement: float
    points: int
    sigma_xy_m: float
    sigma_yaw_deg: float


class ReadinessGuard:
    """Decides "position trusted" with hysteresis; never latches.

    Acquiring needs ``acquire_checks`` consecutive good checks; holding needs
    each check to meet the looser hold limits. A missing check for longer
    than ``check_timeout_s`` drops readiness.
    """

    def __init__(self, config: ReadinessConfig) -> None:
        self.config = config
        self.ready = False
        self.good_in_row = 0
        self.last: Optional[Check] = None
        self.reason = "no_check"

    def reset(self, reason: str) -> None:
        self.ready = False
        self.good_in_row = 0
        self.last = None
        self.reason = reason

    def update(self, check: Check) -> bool:
        c = self.config
        self.last = check
        finite = all(math.isfinite(v) for v in (check.agreement, check.sigma_xy_m, check.sigma_yaw_deg))
        if not finite or check.points < c.minimum_points:
            self.reset("too_few_points" if finite else "invalid_check")
            self.last = check
            return self.ready
        if self.ready:
            if (check.agreement >= c.hold_agreement and check.sigma_xy_m <= c.hold_sigma_xy_m
                    and check.sigma_yaw_deg <= c.hold_sigma_yaw_deg):
                self.reason = "ok"
                return True
            self.ready = False
            self.good_in_row = 0
            self.reason = "scan_disagrees" if check.agreement < c.hold_agreement else "uncertain"
            return False
        if (check.agreement >= c.acquire_agreement and check.sigma_xy_m <= c.acquire_sigma_xy_m
                and check.sigma_yaw_deg <= c.acquire_sigma_yaw_deg):
            self.good_in_row += 1
        else:
            self.good_in_row = 0
            self.reason = "scan_disagrees" if check.agreement < c.acquire_agreement else "uncertain"
        if self.good_in_row >= c.acquire_checks:
            self.ready = True
            self.reason = "ok"
        return self.ready

    def is_ready(self, now: float) -> bool:
        if not self.ready or self.last is None:
            return False
        if not 0 <= now - self.last.time <= self.config.check_timeout_s:
            self.reset("check_stale")
            return False
        return True


def sigmas_from_covariance(covariance: Sequence[float]) -> Tuple[float, float]:
    """Position and yaw standard deviation from a 6x6 row-major covariance."""

    cov = list(covariance)
    if len(cov) != 36:
        return math.inf, math.inf
    var_xy = max(cov[0], cov[7])
    var_yaw = cov[35]
    if not (math.isfinite(var_xy) and math.isfinite(var_yaw)) or var_xy < 0 or var_yaw < 0:
        return math.inf, math.inf
    return math.sqrt(var_xy), math.degrees(math.sqrt(var_yaw))


def yaw_from_quaternion(x: float, y: float, z: float, w: float) -> float:
    return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def save_last_pose(path: str, fingerprint: str, pose: Tuple[float, float, float], wall_time: float) -> None:
    """Store the last trusted pose atomically, bound to the map fingerprint."""

    directory = os.path.dirname(path)
    os.makedirs(directory, exist_ok=True)
    payload = {
        "schema_version": 1,
        "map_fingerprint": fingerprint,
        "x": pose[0],
        "y": pose[1],
        "yaw": pose[2],
        "time": wall_time,
    }
    descriptor, temporary = tempfile.mkstemp(dir=directory, prefix=".last_pose.", suffix=".tmp")
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(payload, handle, allow_nan=False)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    except BaseException:
        if os.path.exists(temporary):
            os.unlink(temporary)
        raise


def load_last_pose(path: str, fingerprint: str) -> Optional[Tuple[float, float, float]]:
    """The stored pose if it belongs to this map; otherwise None."""

    try:
        with open(path, encoding="utf-8") as handle:
            payload = json.load(handle)
    except (OSError, ValueError):
        return None
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        return None
    if payload.get("map_fingerprint") != fingerprint:
        return None
    try:
        pose = (float(payload["x"]), float(payload["y"]), float(payload["yaw"]))
    except (KeyError, TypeError, ValueError):
        return None
    if not all(math.isfinite(v) for v in pose):
        return None
    return pose
