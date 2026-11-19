"""When to search the whole map for the robot, and when to believe the result.

The search itself is the matcher ported from Amadeus
(global_scan_matcher.py). This module is the bookkeeping around it, without
ROS and without threads: when a search may start, how many attempts a round
has, and the rule that two searches on different scans must agree before the
result is used.

Acceptance follows the Amadeus localizer (roboter_ws 05439c7,
global_scan_localizer.py): a total score and a share of scan points next to
map walls of at least 0.85 each, a clear winner over the next different
hypothesis, and two consecutive agreeing results. One value differs:

- ``minimum_score_ratio`` is 1.05 instead of 1.15. In the HomeMy test
  apartment 1.15 rejected correct results in the plain rectangular kitchen,
  where a pose turned by 180 degrees explains about 90 % of the scan; 1.05
  accepted all 17 tried poses. A perfectly symmetric scene still gives 1.00
  and is refused. The value is a simulation result and must be confirmed on
  a real map.

A wrong result cannot move the robot into an obstacle: the motion gate's
obstacle protection does not use the map position, and the readiness check
keeps comparing the scan with the map while the robot drives.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional

from homemy_navigation.global_scan_matcher import (
    ScanCandidate,
    SearchResult,
    result_is_accepted,
    scan_candidates_consistent,
)

STATE_IDLE = "idle"
STATE_SEARCHING = "searching"
STATE_WAITING = "waiting"  # between attempts of a round
STATE_PAUSED = "paused"  # a round ended without a result


@dataclass(frozen=True)
class SearchConfig:
    start_after_s: float = 5.0
    minimum_scan_points: int = 200
    minimum_score: float = 0.85
    minimum_endpoint_ratio: float = 0.85
    minimum_score_ratio: float = 1.05
    required_consistent_matches: int = 2
    consensus_position_m: float = 0.20
    consensus_yaw_deg: float = 8.0
    maximum_attempts: int = 5
    retry_interval_s: float = 2.0
    pause_after_failure_s: float = 10.0

    def __post_init__(self) -> None:
        for name in ("start_after_s", "retry_interval_s", "pause_after_failure_s"):
            value = getattr(self, name)
            if not (math.isfinite(value) and value >= 0):
                raise ValueError(f"{name} must be finite and not negative")
        for name in ("minimum_score", "minimum_endpoint_ratio"):
            if not 0 < getattr(self, name) <= 1:
                raise ValueError(f"{name} must be in (0, 1]")
        if not self.minimum_score_ratio > 1.0:
            raise ValueError("minimum_score_ratio must be greater than 1")
        if self.minimum_scan_points < 50:
            raise ValueError("minimum_scan_points must be at least 50")
        if not 1 <= self.required_consistent_matches <= self.maximum_attempts <= 10:
            raise ValueError("expected 1 <= required_consistent_matches <= maximum_attempts <= 10")
        if not (self.consensus_position_m > 0 and self.consensus_yaw_deg > 0):
            raise ValueError("consensus limits must be positive")


class SearchPlanner:
    """Attempts, consensus, and pauses of the global search. Times are monotonic seconds."""

    def __init__(self, config: SearchConfig) -> None:
        self.config = config
        self.state = STATE_IDLE
        self.attempts = 0
        self.rounds_failed = 0
        self.matches: List[ScanCandidate] = []
        self.next_attempt_at = 0.0
        self.last_reason = "not_started"

    def reset(self) -> None:
        """Forget everything, e.g. when the position is trusted again."""

        self.state = STATE_IDLE
        self.attempts = 0
        self.rounds_failed = 0
        self.matches = []
        self.next_attempt_at = 0.0
        self.last_reason = "not_started"

    def may_start(self, now: float, not_trusted_for_s: Optional[float], standing_still: bool,
                  scan_points: int) -> bool:
        """Whether a search attempt may start now.

        ``not_trusted_for_s`` is how long the position has not been trusted
        since the last attempt to set it; None means no position is known at
        all, and the search may start at once.
        """

        if self.state == STATE_SEARCHING or now < self.next_attempt_at:
            return False
        if not standing_still:
            self.last_reason = "robot_moving"
            return False
        if scan_points < self.config.minimum_scan_points:
            self.last_reason = "too_few_scan_points"
            return False
        if not_trusted_for_s is not None and self.attempts == 0 and not_trusted_for_s < self.config.start_after_s:
            return False
        return True

    def note_started(self) -> None:
        self.state = STATE_SEARCHING
        self.attempts += 1
        self.last_reason = f"searching, attempt {self.attempts}"

    def note_result(self, now: float, result: Optional[SearchResult],
                    error: Optional[str] = None) -> Optional[ScanCandidate]:
        """Record one finished attempt. Returns the pose to use, or None."""

        config = self.config
        accepted_candidate: Optional[ScanCandidate] = None
        if result is None:
            self.matches = []
            self.last_reason = error or "search_failed"
        else:
            accepted, reasons = result_is_accepted(
                result,
                minimum_score=config.minimum_score,
                minimum_endpoint_ratio=config.minimum_endpoint_ratio,
                minimum_score_ratio=config.minimum_score_ratio,
            )
            if not accepted:
                self.matches = []
                self.last_reason = "not_unique_or_weak: " + "; ".join(reasons)
            else:
                best = result.best
                if self.matches and scan_candidates_consistent(
                    self.matches[-1],
                    best,
                    maximum_position_error_m=config.consensus_position_m,
                    maximum_yaw_error_rad=math.radians(config.consensus_yaw_deg),
                ):
                    self.matches.append(best)
                else:
                    self.matches = [best]
                self.last_reason = f"match {len(self.matches)} of {config.required_consistent_matches}"
                if len(self.matches) >= config.required_consistent_matches:
                    accepted_candidate = best

        if accepted_candidate is not None:
            self.state = STATE_IDLE
            self.attempts = 0
            self.matches = []
            self.next_attempt_at = now
            self.last_reason = "found"
            return accepted_candidate
        if self.attempts >= config.maximum_attempts:
            self.state = STATE_PAUSED
            self.attempts = 0
            self.matches = []
            self.rounds_failed += 1
            self.next_attempt_at = now + config.pause_after_failure_s
        else:
            self.state = STATE_WAITING
            self.next_attempt_at = now + config.retry_interval_s
        return None
