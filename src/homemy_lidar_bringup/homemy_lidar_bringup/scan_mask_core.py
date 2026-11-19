"""Masks the LiDAR's blind sectors. Pure Python and numpy; no ROS.

Inside a blind sector the LiDAR sees the robot's own struts and slot webs,
and nothing behind them. Every range in such a sector is therefore set to
NaN, which REP 117 defines as "no valid measurement": mapping does not clear
free space there, and obstacle protection treats the sector as unknown.
"""

from __future__ import annotations

import math
from typing import List, Sequence, Tuple

import numpy as np

Sector = Tuple[float, float]  # start, end in degrees, start < end


def normalise_degrees(angle: float) -> float:
    return (angle + 180.0) % 360.0 - 180.0


def build_sectors(starts: Sequence[float], ends: Sequence[float], margin_deg: float) -> List[Sector]:
    if len(starts) != len(ends):
        raise ValueError("sector_start_deg and sector_end_deg must have the same length")
    if not (math.isfinite(margin_deg) and 0.0 <= margin_deg <= 10.0):
        raise ValueError("margin_deg must be between 0 and 10")
    sectors = []
    for start, end in zip(starts, ends):
        start, end = float(start), float(end)
        if not (math.isfinite(start) and math.isfinite(end)):
            raise ValueError("sector bounds must be finite")
        if not (-180.0 <= start < end <= 180.0):
            raise ValueError("each sector needs -180 <= start < end <= 180")
        if end - start > 45.0:
            raise ValueError("a blind sector wider than 45 degrees is implausible; check the configuration")
        sectors.append((start - margin_deg, end + margin_deg))
    return sectors


def blind_mask(angles_rad: np.ndarray, sectors: Sequence[Sector]) -> np.ndarray:
    """True for each beam angle that lies in a blind sector."""

    degrees = (np.degrees(np.asarray(angles_rad, dtype=float)) + 180.0) % 360.0 - 180.0
    mask = np.zeros(len(degrees), dtype=bool)
    for start, end in sectors:
        if start < -180.0:
            mask |= (degrees >= start + 360.0) | (degrees <= end)
        elif end > 180.0:
            mask |= (degrees >= start) | (degrees <= end - 360.0)
        else:
            mask |= (degrees >= start) & (degrees <= end)
    return mask


def apply_mask(ranges: Sequence[float], angle_min: float, angle_increment: float,
               sectors: Sequence[Sector]) -> np.ndarray:
    values = np.asarray(ranges, dtype=float).copy()
    angles = angle_min + np.arange(len(values)) * angle_increment
    values[blind_mask(angles, sectors)] = np.nan
    return values


def blind_degrees(sectors: Sequence[Sector]) -> float:
    return float(sum(end - start for start, end in sectors))
