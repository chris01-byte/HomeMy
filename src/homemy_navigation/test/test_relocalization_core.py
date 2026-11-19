"""Tests of the search bookkeeping (no ROS)."""

import math

import pytest

from homemy_navigation.global_scan_matcher import ScanCandidate, SearchResult
from homemy_navigation.relocalization_core import (
    STATE_IDLE,
    STATE_PAUSED,
    STATE_SEARCHING,
    STATE_WAITING,
    SearchConfig,
    SearchPlanner,
)


def result(x=2.0, y=1.0, yaw=0.3, score=0.97, ratio=0.99, second=0.80):
    return SearchResult(
        candidates=(
            ScanCandidate(x, y, yaw, score, ratio),
            ScanCandidate(x + 3.0, y, yaw + 2.0, second, 0.7),
        ),
        valid_scan_points=600,
    )


def attempt(planner, now, outcome):
    assert planner.may_start(now, None, True, 600)
    planner.note_started()
    assert planner.state == STATE_SEARCHING
    return planner.note_result(now + 2.0, outcome)


def test_unknown_position_starts_at_once_but_a_set_position_gets_time():
    planner = SearchPlanner(SearchConfig(start_after_s=5.0))
    assert planner.may_start(0.0, None, True, 600)
    assert not planner.may_start(0.0, 2.0, True, 600)
    assert planner.may_start(0.0, 5.5, True, 600)


def test_no_search_while_moving_or_with_a_poor_scan():
    planner = SearchPlanner(SearchConfig())
    assert not planner.may_start(0.0, None, False, 600)
    assert planner.last_reason == "robot_moving"
    assert not planner.may_start(0.0, None, True, 50)
    assert planner.last_reason == "too_few_scan_points"


def test_two_agreeing_results_are_needed():
    planner = SearchPlanner(SearchConfig())
    assert attempt(planner, 0.0, result()) is None
    assert planner.state == STATE_WAITING
    assert not planner.may_start(2.5, None, True, 600)  # retry interval
    pose = attempt(planner, 4.5, result(x=2.05, yaw=0.32))
    assert pose is not None and pose.x_m == pytest.approx(2.05)
    assert planner.state == STATE_IDLE and planner.last_reason == "found"


def test_disagreeing_results_do_not_count_together():
    planner = SearchPlanner(SearchConfig())
    assert attempt(planner, 0.0, result()) is None
    assert attempt(planner, 5.0, result(x=6.0, y=3.0, yaw=-2.0)) is None  # elsewhere
    assert attempt(planner, 10.0, result(x=6.02, y=3.0, yaw=-2.0)) is not None


def test_weak_or_ambiguous_results_are_refused():
    planner = SearchPlanner(SearchConfig())
    assert attempt(planner, 0.0, result(score=0.80)) is None
    assert "not_unique_or_weak" in planner.last_reason
    assert attempt(planner, 5.0, result(ratio=0.70)) is None
    # A mirror-symmetric room: the second hypothesis is as good as the first.
    assert attempt(planner, 10.0, result(score=0.97, second=0.96)) is None
    assert planner.matches == []


def test_a_slightly_symmetric_room_is_accepted_with_the_homemy_margin():
    # Kitchen of the test apartment: best 0.975, turned by 180 degrees 0.919.
    planner = SearchPlanner(SearchConfig())
    assert attempt(planner, 0.0, result(score=0.975, second=0.919)) is None
    assert attempt(planner, 5.0, result(score=0.975, second=0.919)) is not None
    strict = SearchPlanner(SearchConfig(minimum_score_ratio=1.15))
    assert attempt(strict, 0.0, result(score=0.975, second=0.919)) is None
    assert strict.matches == []


def test_a_failed_search_breaks_the_consensus():
    planner = SearchPlanner(SearchConfig())
    assert attempt(planner, 0.0, result()) is None
    assert attempt(planner, 5.0, None) is None
    assert attempt(planner, 10.0, result()) is None  # counts as the first match again
    assert attempt(planner, 15.0, result()) is not None


def test_a_round_without_result_pauses_and_then_tries_again():
    planner = SearchPlanner(SearchConfig(maximum_attempts=3, pause_after_failure_s=10.0))
    now = 0.0
    for _ in range(3):
        assert attempt(planner, now, result(score=0.5)) is None
        now += 5.0
    assert planner.state == STATE_PAUSED and planner.rounds_failed == 1
    finished = now - 5.0 + 2.0
    assert not planner.may_start(finished + 9.0, None, True, 600)
    assert planner.may_start(finished + 10.5, None, True, 600)  # heals by itself: never latched


def test_reset_forgets_everything():
    planner = SearchPlanner(SearchConfig())
    attempt(planner, 0.0, result())
    planner.reset()
    assert planner.state == STATE_IDLE and planner.matches == [] and planner.attempts == 0


@pytest.mark.parametrize(
    "kwargs",
    [dict(minimum_score_ratio=1.0), dict(minimum_score=0.0), dict(maximum_attempts=1, required_consistent_matches=2),
     dict(minimum_scan_points=10), dict(start_after_s=math.nan), dict(consensus_position_m=0.0)],
)
def test_invalid_configuration_is_refused(kwargs):
    with pytest.raises(ValueError):
        SearchConfig(**kwargs)
