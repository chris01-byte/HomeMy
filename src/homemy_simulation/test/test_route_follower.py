"""Tests of the simulated operator's direction-pad decisions."""

import math

from homemy_simulation.sim_controller_node import RouteFollower


def test_turns_first_then_drives_straight():
    follower = RouteFollower([(2.0, 2.0)])
    assert follower.press((0.0, 0.0, 0.0)) == (1.0, 0.0)  # target to the left: turn left
    assert follower.press((0.0, 0.0, math.radians(40.0))) == (1.0, 0.0)  # 5 degrees off
    assert follower.press((0.0, 0.0, math.radians(42.0))) == (0.0, 1.0)  # 3 degrees off


def test_turns_right_for_targets_on_the_right():
    follower = RouteFollower([(1.0, -1.0)])
    assert follower.press((0.0, 0.0, 0.0)) == (-1.0, 0.0)


def test_corrects_only_beyond_the_start_threshold():
    follower = RouteFollower([(5.0, 0.0)])
    assert follower.press((0.0, 0.0, 0.0)) == (0.0, 1.0)
    assert follower.press((0.0, 0.0, math.radians(8.0))) == (0.0, 1.0)  # within 12 degrees
    assert follower.press((0.0, 0.0, math.radians(15.0))) == (-1.0, 0.0)


def test_advances_through_waypoints_and_stops_at_the_end():
    follower = RouteFollower([(1.0, 0.0), (1.0, 1.0)], tolerance_m=0.1)
    follower.press((0.95, 0.0, 0.0))
    assert follower.index == 1
    assert follower.press((1.0, 0.95, math.pi / 2)) == (0.0, 0.0)
    assert follower.done
