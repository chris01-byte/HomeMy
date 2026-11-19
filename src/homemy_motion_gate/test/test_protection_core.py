"""Tests of the reactive obstacle protection (no ROS)."""

import math

import numpy as np
import pytest

from homemy_motion_gate.protection_core import FootprintGuard, Outline, scan_to_points

# HomeMy outline from homemy_description/config/geometry.yaml.
HOMEMY = Outline(x_min=-0.2906, x_max=0.1094, y_half=0.250, corner_radius=0.100)


def guard(**kwargs):
    options = dict(margin_m=0.05, horizon_s=1.0, step_s=0.05, min_lookahead_m=0.05)
    options.update(kwargs)
    return FootprintGuard(HOMEMY, **options)


def test_signed_distance_inside_on_and_outside():
    d = HOMEMY.signed_distance([[0.0, 0.0], [0.1094, 0.0], [0.2094, 0.0], [0.0, 0.35]])
    assert d[0] < 0
    assert d[1] == pytest.approx(0.0, abs=1e-9)
    assert d[2] == pytest.approx(0.10)
    assert d[3] == pytest.approx(0.10)


def test_rounded_corner_is_rounded():
    # A point diagonally off the front-left corner: distance to the arc.
    corner_centre = np.array([0.1094 - 0.1, 0.25 - 0.1])
    point = corner_centre + 0.15 * np.array([math.cos(math.pi / 4), math.sin(math.pi / 4)])
    assert HOMEMY.signed_distance([point])[0] == pytest.approx(0.05)


def test_max_radius_is_the_rear_corner_swing():
    # The rear corners swing widest when turning on the spot.
    assert HOMEMY.max_radius() == pytest.approx(math.hypot(0.1906, 0.15) + 0.1)


def test_no_points_and_no_motion_pass():
    g = guard()
    assert g.check(0.0, 0.0, np.empty((0, 2))).allowed
    assert g.check(0.2, 0.0, np.empty((0, 2))).allowed


def test_wall_ahead_blocks_forward_but_not_reverse_or_standstill():
    g = guard()
    wall = np.array([[0.30, y] for y in np.linspace(-0.4, 0.4, 41)])
    assert not g.check(0.20, 0.0, wall).allowed  # reaches it within 1 s
    assert g.check(-0.20, 0.0, wall).allowed  # backing away
    assert g.check(0.0, 0.0, wall).allowed


def test_far_obstacle_does_not_block():
    g = guard()
    wall = np.array([[1.5, y] for y in np.linspace(-0.4, 0.4, 41)])
    assert g.check(0.20, 0.0, wall).allowed


def test_obstacle_beside_does_not_block_straight_driving():
    g = guard()
    side = np.array([[x, 0.40] for x in np.linspace(-0.5, 0.5, 21)])  # 15 cm off the side
    assert g.check(0.20, 0.0, side).allowed


def test_rotation_near_a_rear_obstacle_is_blocked():
    g = guard()
    # A post just behind the rear-left corner, outside the outline now.
    post = np.array([[-0.33, 0.20]])
    assert HOMEMY.signed_distance(post)[0] > 0.0
    # Turning left swings the rear-left corner into the post; turning right
    # swings it away.
    assert not g.check(0.0, 0.6, post).allowed
    assert g.check(0.0, -0.6, post).allowed


def test_point_already_inside_margin_allows_moving_away():
    g = guard()
    touching = np.array([[0.13, 0.0]])  # 2 cm in front of the bumper
    assert not g.check(0.10, 0.0, touching).allowed
    assert g.check(-0.10, 0.0, touching).allowed


def test_creeping_speed_still_looks_ahead_min_lookahead():
    g = guard(horizon_s=0.2, min_lookahead_m=0.10)
    wall = np.array([[0.1094 + 0.12, 0.0]])
    # 0.01 m/s for 0.2 s is only 2 mm, but the lookahead stretches to 10 cm.
    assert not g.check(0.01, 0.0, wall).allowed


def test_non_finite_points_are_ignored():
    g = guard()
    points = np.array([[np.nan, 0.0], [np.inf, 1.0]])
    assert g.check(0.2, 0.0, points).allowed


@pytest.mark.parametrize(
    "kwargs",
    [dict(margin_m=0.0), dict(horizon_s=-1.0), dict(step_s=2.0), dict(min_lookahead_m=-0.1)],
)
def test_invalid_configuration_is_refused(kwargs):
    with pytest.raises(ValueError):
        guard(**kwargs)


def test_outline_must_fit_its_corner_radius():
    with pytest.raises(ValueError):
        Outline(x_min=0.0, x_max=0.1, y_half=0.25, corner_radius=0.1)


def test_scan_to_points_uses_sensor_pose_and_drops_invalid():
    ranges = np.array([1.0, np.nan, np.inf, 0.01, 2.0])
    points = scan_to_points(
        ranges,
        angle_min=0.0,
        angle_increment=math.pi / 2,
        range_min=0.05,
        range_max=10.0,
        sensor_xy=(0.0694, 0.0),
        sensor_yaw=0.0,
    )
    assert points.shape == (2, 2)
    assert points[0] == pytest.approx([1.0694, 0.0])
    # The fifth beam points at 2*pi, straight ahead again.
    assert points[1] == pytest.approx([2.0694, 0.0], abs=1e-9)
