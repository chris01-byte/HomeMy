"""Tests of the blind-sector mask (no ROS)."""

import math
import pathlib

import numpy as np
import pytest
import yaml

from homemy_lidar_bringup.scan_mask_core import apply_mask, blind_degrees, blind_mask, build_sectors

CONFIG = yaml.safe_load(
    (pathlib.Path(__file__).resolve().parents[1] / "config" / "scan_mask.yaml").read_text()
)["scan_mask"]["ros__parameters"]


def configured(margin=None):
    return build_sectors(
        CONFIG["sector_start_deg"],
        CONFIG["sector_end_deg"],
        CONFIG["margin_deg"] if margin is None else margin,
    )


def test_configured_sectors_match_the_decision_record():
    # 34.4 degrees blind in total without margin (LiDAR slot decision).
    assert blind_degrees(configured(margin=0.0)) == pytest.approx(34.2, abs=0.3)
    assert len(configured()) == 6


def test_sectors_are_mirror_images():
    starts, ends = CONFIG["sector_start_deg"], CONFIG["sector_end_deg"]
    left = sorted(zip(starts[:3], ends[:3]))
    right = sorted((-e, -s) for s, e in zip(starts[3:], ends[3:]))
    assert left == right


def test_front_and_rear_stay_visible():
    sectors = configured()
    angles = np.radians([0.0, 45.0, -45.0, 90.0, -90.0, 180.0, 179.0, -179.0])
    assert not blind_mask(angles, sectors).any()


def test_blind_bearings_are_masked_including_margin():
    sectors = configured()
    assert blind_mask(np.radians([74.0, 130.0, 158.5, -74.0, -130.0, -158.5]), sectors).all()
    assert blind_mask(np.radians([72.0, 138.5]), sectors).all()  # within 1.5 degree margin
    assert not blind_mask(np.radians([70.0, 140.5]), sectors).any()


def test_apply_mask_sets_nan_and_keeps_the_rest():
    beams = 720
    angle_min = -math.pi
    increment = 2 * math.pi / beams
    ranges = np.full(beams, 2.0)
    masked = apply_mask(ranges, angle_min, increment, configured())
    blind = np.isnan(masked)
    # 34.2 degrees plus 1.5 degrees margin on both sides of six sectors.
    assert blind.mean() == pytest.approx((34.2 + 6 * 3.0) / 360.0, abs=0.01)
    assert np.all(masked[~blind] == 2.0)


def test_angles_beyond_plus_minus_pi_wrap():
    sectors = build_sectors([170.0], [179.0], 2.0)
    assert blind_mask(np.radians([-179.5, 181.0 - 360.0 + 360.0]), sectors).all()


@pytest.mark.parametrize(
    "starts, ends, margin",
    [([10.0], [5.0], 1.0), ([0.0], [90.0], 1.0), ([0.0, 1.0], [2.0], 1.0), ([0.0], [5.0], 20.0), ([float("nan")], [1.0], 1.0)],
)
def test_invalid_configuration_is_refused(starts, ends, margin):
    with pytest.raises(ValueError):
        build_sectors(starts, ends, margin)
