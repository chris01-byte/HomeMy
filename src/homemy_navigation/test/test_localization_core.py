"""Tests of the localization logic (no ROS)."""

import math

import numpy as np
import pytest

from homemy_navigation.localization_core import (
    MODE_IDLE,
    MODE_MAPPING,
    MODE_NAVIGATION,
    MODE_SLAM_HOLD,
    Check,
    OccupancyIndex,
    ReadinessConfig,
    ReadinessGuard,
    SavedMapRef,
    desired_mode,
    load_last_pose,
    save_last_pose,
    sigmas_from_covariance,
)

SAVED = SavedMapRef(fingerprint="a" * 64, yaml_path="/maps/wohnung/v1/map.yaml", version="v1")


def test_mapping_mode_always_wins():
    for current in (MODE_IDLE, MODE_SLAM_HOLD, MODE_NAVIGATION, MODE_MAPPING):
        assert desired_mode(True, current, SAVED, "a" * 64) == MODE_MAPPING


def test_after_mapping_the_slam_map_is_held_until_it_is_saved():
    assert desired_mode(False, MODE_MAPPING, None, "b" * 64) == MODE_SLAM_HOLD
    # An older saved map does not replace the new, unsaved SLAM map.
    assert desired_mode(False, MODE_SLAM_HOLD, SAVED, "b" * 64) == MODE_SLAM_HOLD
    assert desired_mode(False, MODE_SLAM_HOLD, SAVED, None) == MODE_SLAM_HOLD
    # Saved: navigation on exactly that map.
    assert desired_mode(False, MODE_SLAM_HOLD, SAVED, "a" * 64) == MODE_NAVIGATION


def test_start_up_uses_the_newest_saved_map_or_waits_for_one():
    assert desired_mode(False, MODE_IDLE, SAVED, None) == MODE_NAVIGATION
    assert desired_mode(False, MODE_IDLE, None, None) == MODE_IDLE
    assert desired_mode(False, MODE_NAVIGATION, SAVED, "c" * 64) == MODE_NAVIGATION


def box_map():
    """A 4 x 3 m room with walls, 5 cm cells, origin at (-0.5, -0.5)."""

    width, height = 100, 80
    grid = np.zeros((height, width), dtype=int)
    grid[0, :] = grid[-1, :] = 100
    grid[:, 0] = grid[:, -1] = 100
    return grid.ravel().tolist(), width, height


def test_points_on_walls_agree_and_points_in_the_room_do_not():
    data, width, height = box_map()
    index = OccupancyIndex(data, width, height, 0.05, (-0.5, -0.5), radius_m=0.15)
    walls = np.array([[-0.5 + 0.025, y] for y in np.linspace(0.0, 3.0, 20)])
    middle = np.array([[2.0, 1.5]] * 20)
    assert index.agreement(walls) == (1.0, 20)
    assert index.agreement(middle)[0] == 0.0
    assert index.agreement(np.vstack([walls, middle]))[0] == pytest.approx(0.5)


def test_points_outside_the_map_and_non_finite_points():
    data, width, height = box_map()
    index = OccupancyIndex(data, width, height, 0.05, (-0.5, -0.5), radius_m=0.15)
    assert index.agreement(np.array([[50.0, 50.0]])) == (0.0, 1)
    assert index.agreement(np.array([[np.nan, 1.0]])) == (0.0, 0)


def test_dilation_reaches_the_radius_only():
    data, width, height = box_map()
    index = OccupancyIndex(data, width, height, 0.05, (-0.5, -0.5), radius_m=0.15)
    wall_x = -0.5 + 0.025
    assert index.agreement(np.array([[wall_x + 0.14, 1.5]]))[0] == 1.0
    assert index.agreement(np.array([[wall_x + 0.30, 1.5]]))[0] == 0.0


def good(t, agreement=0.95):
    return Check(time=t, agreement=agreement, points=300, sigma_xy_m=0.05, sigma_yaw_deg=2.0)


def test_readiness_needs_consecutive_good_checks():
    guard = ReadinessGuard(ReadinessConfig())
    assert not guard.update(good(0.0))
    assert guard.update(good(0.5))
    assert guard.is_ready(0.6)


def test_small_covariance_with_a_disagreeing_scan_is_not_ready():
    # The Amadeus 1.95 m case: confident filter, scan does not fit the walls.
    guard = ReadinessGuard(ReadinessConfig())
    for t in range(5):
        guard.update(Check(time=float(t), agreement=0.40, points=300, sigma_xy_m=0.12, sigma_yaw_deg=9.5))
    assert not guard.is_ready(4.1)
    assert guard.reason == "scan_disagrees"


def test_hysteresis_holds_and_then_drops():
    guard = ReadinessGuard(ReadinessConfig())
    guard.update(good(0.0))
    guard.update(good(0.5))
    assert guard.update(good(1.0, agreement=0.70))  # below acquire, above hold
    assert not guard.update(good(1.5, agreement=0.50))
    assert not guard.is_ready(1.6)


def test_stale_checks_drop_readiness():
    guard = ReadinessGuard(ReadinessConfig(check_timeout_s=1.0))
    guard.update(good(0.0))
    guard.update(good(0.5))
    assert guard.is_ready(1.4)
    assert not guard.is_ready(1.6)
    assert guard.reason == "check_stale"


def test_too_few_points_is_not_ready():
    guard = ReadinessGuard(ReadinessConfig())
    for t in range(3):
        guard.update(Check(time=float(t), agreement=1.0, points=10, sigma_xy_m=0.01, sigma_yaw_deg=1.0))
    assert not guard.is_ready(2.1)
    assert guard.reason == "too_few_points"


def test_sigmas_from_covariance():
    cov = [0.0] * 36
    cov[0], cov[7], cov[35] = 0.04, 0.01, math.radians(5.0) ** 2
    sigma_xy, sigma_yaw = sigmas_from_covariance(cov)
    assert sigma_xy == pytest.approx(0.2)
    assert sigma_yaw == pytest.approx(5.0)
    assert sigmas_from_covariance([0.0] * 5) == (math.inf, math.inf)
    cov[0] = float("nan")
    assert sigmas_from_covariance(cov) == (math.inf, math.inf)


def test_last_pose_is_bound_to_its_map(tmp_path):
    path = str(tmp_path / "localization" / "last_pose.json")
    save_last_pose(path, "a" * 64, (1.0, 2.0, 0.5), 1000.0)
    assert load_last_pose(path, "a" * 64) == (1.0, 2.0, 0.5)
    assert load_last_pose(path, "b" * 64) is None
    assert load_last_pose(str(tmp_path / "missing.json"), "a" * 64) is None
    (tmp_path / "broken.json").write_text("{not json")
    assert load_last_pose(str(tmp_path / "broken.json"), "a" * 64) is None


def test_invalid_readiness_config_is_refused():
    with pytest.raises(ValueError):
        ReadinessConfig(acquire_agreement=0.5, hold_agreement=0.6)
    with pytest.raises(ValueError):
        ReadinessConfig(minimum_points=0)
