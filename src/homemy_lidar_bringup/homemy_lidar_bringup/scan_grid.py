"""Fixed angle grid for the LiDAR scan. Pure Python and numpy; no ROS.

After Amadeus ``scan_gitter.py`` (Roboter_ws 05439c7). The STL-27L delivers
a different number of beams with every revolution. slam_toolbox (Karto)
remembers the beam count of the first scan and silently drops every scan
with another count. Every scan is therefore put on a fixed grid first.

Nearest neighbour, never interpolation: between two neighbouring beams
there can be a depth edge (door frame, furniture edge). An interpolated
value would invent a surface that does not exist.

HomeMy addition: the output grid lies in the robot-aligned LiDAR frame
(``lidar_link``: 0 = straight ahead, counter-clockwise positive). The
bearing of the device's own zero direction in that frame, ``yaw_offset``,
is applied here, so that every consumer sees an aligned scan.
"""

from __future__ import annotations

import math
from typing import Sequence, Tuple

import numpy as np

FULL_TURN = 2.0 * math.pi


def grid_angles(beams_out: int) -> np.ndarray:
    """Beam angles of the output grid: from -pi, counter-clockwise, no duplicate direction."""

    if beams_out < 2:
        raise ValueError("the output grid needs at least 2 beams")
    return -math.pi + np.arange(beams_out) * FULL_TURN / beams_out


def grid_indices(count_in: int, angle_min_in: float, increment_in: float, beams_out: int,
                 yaw_offset_rad: float = 0.0) -> Tuple[np.ndarray, np.ndarray]:
    """For each output beam: index of the nearest input beam, and whether there is one.

    An output beam is valid if an input beam lies within half an input
    increment of its direction. Output beams outside the input's angular
    coverage are invalid and become NaN.
    """

    if count_in < 2:
        raise ValueError("input scan with fewer than 2 beams")
    if not (math.isfinite(increment_in) and increment_in > 0.0):
        raise ValueError("angle_increment must be positive and finite")
    if not (math.isfinite(angle_min_in) and math.isfinite(yaw_offset_rad)):
        raise ValueError("angle_min and yaw offset must be finite")

    # Direction of each output beam in the device frame, as an angle from the first input beam.
    relative = np.mod(grid_angles(beams_out) - yaw_offset_rad - angle_min_in, FULL_TURN)
    index = np.rint(relative / increment_in).astype(np.int64)
    tolerance = 0.5 * increment_in * (1.0 + 1e-9)
    valid = (index <= count_in - 1) & (np.abs(relative - index * increment_in) <= tolerance)
    # Just below a full turn the nearest input beam can be the first one again.
    wraps = ~valid & (FULL_TURN - relative <= tolerance)
    index = np.where(wraps, 0, np.clip(index, 0, count_in - 1))
    return index, valid | wraps


def to_grid(values: Sequence[float], index: np.ndarray, valid: np.ndarray,
            fill: float = float("nan")) -> np.ndarray:
    """Pick the values by index; output beams without an input beam get ``fill``."""

    if values is None or len(values) == 0:
        return np.full(len(index), fill, dtype=np.float32)
    field = np.asarray(values, dtype=np.float32)
    picked = field[np.clip(index, 0, len(field) - 1)]
    return np.where(valid, picked, np.float32(fill)).astype(np.float32)
