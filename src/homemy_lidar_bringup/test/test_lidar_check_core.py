"""Tests of the LiDAR check evaluation (no ROS)."""

import numpy as np
import pytest

from homemy_lidar_bringup import lidar_check_core as core
from homemy_lidar_bringup.scan_grid import grid_angles

ANGLES = np.degrees(grid_angles(2160))


def scans_with(parts, count=30, far=3.0, noise=0.03, seed=1):
    """Scans of a room about 3 m away with moving noise, plus fixed near parts."""

    rng = np.random.default_rng(seed)
    scans = far + rng.normal(0.0, noise, (count, len(ANGLES)))
    for start, end, distance in parts:
        inside = (ANGLES >= start) & (ANGLES <= end)
        scans[:, inside] = distance + rng.normal(0.0, 0.001, (count, int(inside.sum())))
    return scans


def found_sectors(scans):
    median, spread = core.beam_medians(scans, 0.02, 25.0)
    return core.sectors_of(ANGLES, core.fixed_near_beams(median, spread))


def test_beam_count_summary_shows_the_variation():
    summary = core.beam_count_summary([2146, 2160, 2160, 2176])
    assert summary == {
        "scans": 4, "min": 2146, "max": 2176, "distinct": 3, "most_common": 2160, "most_common_share": 0.5,
    }
    assert core.beam_count_summary([]) == {"scans": 0}


def test_rate():
    assert core.rate_hz([0.0, 0.1, 0.2, 0.3]) == pytest.approx(10.0)
    assert core.rate_hz([1.0]) is None
    assert core.rate_hz([1.0, 1.0]) is None


def test_own_parts_are_found_as_sectors():
    sectors = found_sectors(scans_with([(72.9, 76.1, 0.20), (-137.9, -126.9, 0.24)]))
    assert len(sectors) == 2
    assert sectors[0] == pytest.approx((-137.9, -126.9), abs=0.2)
    assert sectors[1] == pytest.approx((72.9, 76.1), abs=0.2)


def test_a_near_but_moving_object_is_not_an_own_part():
    rng = np.random.default_rng(2)
    scans = scans_with([])
    inside = (ANGLES >= -10) & (ANGLES <= 10)
    scans[:, inside] = 0.4 + rng.normal(0.0, 0.05, (len(scans), int(inside.sum())))
    assert found_sectors(scans) == []


def test_a_far_fixed_wall_is_not_an_own_part():
    assert found_sectors(scans_with([(-20.0, 20.0, 1.5)])) == []


def test_beams_that_are_mostly_invalid_are_ignored():
    scans = scans_with([(30.0, 40.0, 0.2)])
    inside = (ANGLES >= 30.0) & (ANGLES <= 40.0)
    scans[5:, inside] = np.nan
    assert found_sectors(scans) == []


def test_sector_across_the_seam_is_one_sector():
    scans = scans_with([(175.0, 180.0, 0.2), (-180.0, -174.0, 0.2)])
    sectors = found_sectors(scans)
    assert len(sectors) == 1
    assert sectors[0][0] == pytest.approx(175.0, abs=0.2)
    assert sectors[0][1] == pytest.approx(186.0, abs=0.2)


def test_comparison_passes_when_every_part_is_masked_and_every_sector_confirmed():
    mask = [(71.4, 77.6), (-139.4, -125.4)]
    result = core.compare_with_mask([(72.9, 76.1), (-137.9, -126.9)], mask)
    assert all(entry["masked"] for entry in result["found"])
    assert all(entry["confirmed"] for entry in result["mask"])


def test_comparison_shows_an_unmasked_part_and_an_unconfirmed_sector():
    """A scan that is turned by 90 degrees fits the mask nowhere."""

    mask = [(71.4, 77.6), (-139.4, -125.4)]
    result = core.compare_with_mask([(162.9, 166.1), (-47.9, -36.9)], mask)
    assert not any(entry["masked"] for entry in result["found"])
    assert not any(entry["confirmed"] for entry in result["mask"])


def test_comparison_notices_a_part_wider_than_its_mask_sector():
    result = core.compare_with_mask([(70.0, 79.0)], [(71.4, 77.6)])
    assert result["found"][0]["masked"] is False
    assert result["mask"][0]["confirmed"] is True


def test_comparison_handles_the_seam():
    result = core.compare_with_mask([(175.0, 186.0)], [(-186.5, -172.5)])
    assert result["found"][0]["masked"] is True
    assert result["mask"][0]["confirmed"] is True


def test_nearest_target_gives_bearing_and_distance():
    ranges = np.full(len(ANGLES), 3.0)
    ranges[(ANGLES >= 88.0) & (ANGLES <= 92.0)] = 0.7
    bearing, distance = core.nearest_target(ANGLES, ranges)
    assert 88.0 <= bearing <= 92.0
    assert distance == pytest.approx(0.7)


def test_nearest_target_ignores_single_beams_and_masked_sectors():
    ranges = np.full(len(ANGLES), 3.0)
    ranges[100] = 0.2  # one noisy beam
    own = (ANGLES >= 72.0) & (ANGLES <= 77.0)
    ranges[own] = 0.2
    ranges[(ANGLES >= -2.0) & (ANGLES <= 2.0)] = 0.8
    bearing, distance = core.nearest_target(ANGLES, ranges, ignore=own)
    assert abs(bearing) <= 2.0
    assert distance == pytest.approx(0.8)


def test_nearest_target_without_anything_in_range():
    assert core.nearest_target(ANGLES, np.full(len(ANGLES), np.nan)) is None
    assert core.nearest_target(ANGLES, np.full(len(ANGLES), 10.0)) is None
