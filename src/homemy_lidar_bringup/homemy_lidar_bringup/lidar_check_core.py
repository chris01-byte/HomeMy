"""Evaluation for the LiDAR check tool. Pure Python and numpy; no ROS.

After Amadeus ``lidar_totzone_messen.py`` (Roboter_ws 05439c7): the robot's
own parts show as returns that are near and do not move at all over many
scans. A person or a box nearby scatters.
"""

from __future__ import annotations

import warnings
from collections import Counter
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

Sector = Tuple[float, float]  # start, end in degrees; end may exceed 180 for a sector across the seam


def beam_count_summary(counts: Sequence[int]) -> Dict:
    if not counts:
        return {"scans": 0}
    counter = Counter(int(c) for c in counts)
    value, hits = counter.most_common(1)[0]
    return {
        "scans": len(counts),
        "min": min(counter),
        "max": max(counter),
        "distinct": len(counter),
        "most_common": value,
        "most_common_share": hits / len(counts),
    }


def rate_hz(stamps_s: Sequence[float]) -> Optional[float]:
    if len(stamps_s) < 2 or stamps_s[-1] <= stamps_s[0]:
        return None
    return (len(stamps_s) - 1) / (stamps_s[-1] - stamps_s[0])


def beam_medians(ranges: np.ndarray, range_min: float, range_max: float,
                 presence: float = 0.8) -> Tuple[np.ndarray, np.ndarray]:
    """Median and spread per beam over all scans; NaN where a beam is valid too rarely.

    The spread is the width of the middle 90 % of the values, so that a
    single outlier does not turn a fixed part into a moving one.
    """

    field = np.asarray(ranges, dtype=float)
    valid = np.isfinite(field) & (field >= range_min) & (field <= range_max)
    field = np.where(valid, field, np.nan)
    enough = valid.mean(axis=0) >= presence
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)  # beams without any valid value
        median = np.where(enough, np.nanmedian(field, axis=0), np.nan)
        low, high = np.nanpercentile(field, [5.0, 95.0], axis=0)
        spread = np.where(enough, high - low, np.nan)
    return median, spread


def fixed_near_beams(median: np.ndarray, spread: np.ndarray, near_limit_m: float = 0.6,
                     spread_limit_m: float = 0.02) -> np.ndarray:
    """True for beams that see something near and immobile: the robot itself."""

    with np.errstate(invalid="ignore"):
        return np.isfinite(median) & (median < near_limit_m) & (spread < spread_limit_m)


def sectors_of(angles_deg: np.ndarray, flags: np.ndarray, gap_deg: float = 2.0) -> List[Sector]:
    """Contiguous sectors of flagged beams on the circle, in degrees from -180."""

    angles = np.sort((np.asarray(angles_deg, dtype=float)[np.asarray(flags, dtype=bool)] + 180.0) % 360.0 - 180.0)
    if len(angles) == 0:
        return []
    sectors: List[List[float]] = [[float(angles[0]), float(angles[0])]]
    for angle in angles[1:]:
        if angle - sectors[-1][1] > gap_deg:
            sectors.append([float(angle), float(angle)])
        else:
            sectors[-1][1] = float(angle)
    # Join a sector that crosses the seam at +-180 degrees.
    if len(sectors) > 1 and (sectors[0][0] + 360.0) - sectors[-1][1] <= gap_deg:
        sectors[-1][1] = sectors[0][1] + 360.0
        sectors.pop(0)
    return [(start, end) for start, end in sectors]


def _covered(inner: Sector, outer: Sector) -> bool:
    for shift in (-360.0, 0.0, 360.0):
        if outer[0] + shift <= inner[0] and inner[1] <= outer[1] + shift:
            return True
    return False


def _overlaps(a: Sector, b: Sector) -> bool:
    for shift in (-360.0, 0.0, 360.0):
        if a[0] <= b[1] + shift and b[0] + shift <= a[1]:
            return True
    return False


def compare_with_mask(found: Sequence[Sector], mask: Sequence[Sector]) -> Dict:
    """Which found sectors the mask hides, and which mask sectors the scan confirms."""

    return {
        "found": [
            {"start": s[0], "end": s[1], "width": s[1] - s[0], "masked": any(_covered(s, m) for m in mask)}
            for s in found
        ],
        "mask": [
            {"start": m[0], "end": m[1], "width": m[1] - m[0], "confirmed": any(_overlaps(m, s) for s in found)}
            for m in mask
        ],
    }


def nearest_target(angles_deg: np.ndarray, ranges: np.ndarray, ignore: Optional[np.ndarray] = None,
                   minimum_m: float = 0.15, maximum_m: float = 3.0,
                   window: int = 5) -> Optional[Tuple[float, float]]:
    """Bearing and distance of the nearest object, for the direction check.

    A single near beam can be noise, so the range profile is first smoothed
    with a running median over ``window`` beams.
    """

    values = np.asarray(ranges, dtype=float).copy()
    values[~np.isfinite(values) | (values < minimum_m) | (values > maximum_m)] = np.nan
    if ignore is not None:
        values[np.asarray(ignore, dtype=bool)] = np.nan
    half = window // 2
    padded = np.concatenate([values[-half:], values, values[:half]]) if half else values
    stacked = np.stack([padded[i:i + len(values)] for i in range(window)])
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", RuntimeWarning)
        enough = np.isfinite(stacked).sum(axis=0) > window // 2
        smooth = np.where(enough, np.nanmedian(stacked, axis=0), np.nan)
    if not np.isfinite(smooth).any():
        return None
    index = int(np.nanargmin(smooth))
    bearing = (float(np.asarray(angles_deg, dtype=float)[index]) + 180.0) % 360.0 - 180.0
    return bearing, float(smooth[index])
