"""Mission logic of HomeMy without ROS: commands, preconditions, and the run.

V1 knows one mission, "drive to a room", and "cancel". Rules
(contracts/api/app-bridge.md, section Missions):

- one mission at a time;
- a mission starts only with mapping mode off, a ready lifecycle state, a
  trusted position, rooms bound to the loaded map, and navigation available;
- a failed drive is a pause, not the end: wait, then try again, up to a
  fixed number of attempts (healing ladder; owner decision 2026-11-17);
- a lost position stops the robot through the motion gate; the mission
  waits a bounded time for it to come back;
- cancel is always accepted and idempotent; starting mapping cancels too.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass, field
from typing import Optional

MAX_COMMAND_BYTES = 4096
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")
ROOM_REF_MAX = 128

STATE_IDLE = "idle"
STATE_RUNNING = "running"
STATE_SUCCEEDED = "succeeded"
STATE_FAILED = "failed"
STATE_CANCELED = "canceled"

PHASE_STARTING = "starting"
PHASE_DRIVING = "driving"
PHASE_WAITING_RETRY = "waiting_retry"
PHASE_WAITING_LOCALIZATION = "waiting_localization"
PHASE_CANCELING = "canceling"


class CommandError(ValueError):
    def __init__(self, message: str, request_id: Optional[str] = None) -> None:
        super().__init__(message)
        self.request_id = request_id


@dataclass(frozen=True)
class MissionCommand:
    command: str
    request_id: str
    room_id: Optional[str] = None
    room_name: Optional[str] = None


def parse_command(text: str) -> MissionCommand:
    if len(text.encode("utf-8")) > MAX_COMMAND_BYTES:
        raise CommandError("command too large")
    try:
        payload = json.loads(text)
    except ValueError as error:
        raise CommandError(f"not JSON: {error}") from None
    if not isinstance(payload, dict):
        raise CommandError("command must be a JSON object")
    request_id = payload.get("request_id")
    if not isinstance(request_id, str) or not REQUEST_ID_PATTERN.match(request_id):
        raise CommandError("request_id missing or invalid")
    command = payload.get("command")
    if command == "cancel":
        if set(payload) - {"command", "request_id"}:
            raise CommandError("cancel takes no further fields", request_id)
        return MissionCommand("cancel", request_id)
    if command == "go_to_room":
        if set(payload) - {"command", "request_id", "room_id", "room"}:
            raise CommandError("unknown fields in go_to_room", request_id)
        room_id, room = payload.get("room_id"), payload.get("room")
        for value in (room_id, room):
            if value is not None and (not isinstance(value, str) or not value.strip() or len(value) > ROOM_REF_MAX):
                raise CommandError("room_id and room must be non-empty strings", request_id)
        if room_id is None and room is None:
            raise CommandError("go_to_room needs room_id or room", request_id)
        return MissionCommand("go_to_room", request_id, room_id=room_id, room_name=room)
    raise CommandError("unknown command", request_id)


@dataclass(frozen=True)
class Preconditions:
    mapping_active: bool
    lifecycle_ready: bool
    localization_ready: bool
    localization_map_fingerprint: Optional[str]
    rooms_map_fingerprint: Optional[str]
    navigation_available: bool


def start_block_reason(running: bool, pre: Preconditions) -> Optional[str]:
    """Why go_to_room would be refused now; None when it may start."""

    if running:
        return "busy"
    if pre.mapping_active:
        return "mapping_active"
    if not pre.lifecycle_ready:
        return "not_ready"
    if pre.localization_map_fingerprint is None:
        return "no_map"
    if pre.rooms_map_fingerprint is None or pre.rooms_map_fingerprint != pre.localization_map_fingerprint:
        return "rooms_not_bound"
    if not pre.localization_ready:
        return "not_localized"
    if not pre.navigation_available:
        return "navigation_unavailable"
    return None


@dataclass(frozen=True)
class MissionPolicy:
    max_attempts: int = 3
    retry_wait_s: float = 3.0
    # Long enough for a search of the whole map: two searches on different
    # scans, then the scan check.
    localization_grace_s: float = 30.0

    def __post_init__(self) -> None:
        if self.max_attempts < 1:
            raise ValueError("max_attempts must be at least 1")
        for value in (self.retry_wait_s, self.localization_grace_s):
            if not (math.isfinite(value) and value >= 0):
                raise ValueError("waiting times must be finite and not negative")


@dataclass
class Mission:
    """One go_to_room run. Times are monotonic seconds."""

    room_id: str
    room_name: str
    goal: tuple  # x, y, yaw in the map frame
    policy: MissionPolicy
    started_at: float
    state: str = STATE_RUNNING
    phase: str = PHASE_STARTING
    attempt: int = 1
    distance_remaining_m: Optional[float] = None
    result: Optional[str] = None
    retry_at: Optional[float] = None
    localization_lost_at: Optional[float] = None
    history: list = field(default_factory=list)

    @property
    def running(self) -> bool:
        return self.state == STATE_RUNNING

    def note(self, now: float, event: str) -> None:
        self.history.append((round(now - self.started_at, 2), event))
        del self.history[:-20]

    def driving(self, now: float) -> None:
        self.phase = PHASE_DRIVING
        self.note(now, f"attempt {self.attempt} accepted")

    def arrived(self, now: float) -> None:
        self.state, self.phase, self.result = STATE_SUCCEEDED, "arrived", "arrived"
        self.distance_remaining_m = 0.0
        self.note(now, "arrived")

    def drive_failed(self, now: float, reason: str) -> None:
        """Nav2 gave up. Retry after a pause, or end the mission."""

        self.note(now, f"attempt {self.attempt} failed: {reason}")
        if self.attempt >= self.policy.max_attempts:
            self.state, self.phase, self.result = STATE_FAILED, "failed", reason
            return
        self.attempt += 1
        self.phase = PHASE_WAITING_RETRY
        self.retry_at = now + self.policy.retry_wait_s

    def retry_due(self, now: float) -> bool:
        return self.running and self.phase == PHASE_WAITING_RETRY and self.retry_at is not None and now >= self.retry_at

    def localization(self, ready: bool, now: float) -> bool:
        """Track the position; returns True when the grace time is used up."""

        if ready:
            if self.localization_lost_at is not None:
                self.note(now, "position trusted again")
            self.localization_lost_at = None
            return False
        if self.localization_lost_at is None:
            self.localization_lost_at = now
            self.note(now, "position not trusted; robot stops")
        return now - self.localization_lost_at > self.policy.localization_grace_s

    def cancel(self, now: float, reason: str) -> None:
        self.state, self.phase, self.result = STATE_CANCELED, "canceled", reason
        self.note(now, f"canceled: {reason}")

    def fail(self, now: float, reason: str) -> None:
        self.state, self.phase, self.result = STATE_FAILED, "failed", reason
        self.note(now, f"failed: {reason}")

    def as_dict(self) -> dict:
        return {
            "state": self.state,
            "command": "go_to_room",
            "room_id": self.room_id,
            "room_name": self.room_name,
            "phase": self.phase,
            "attempt": self.attempt,
            "max_attempts": self.policy.max_attempts,
            "distance_remaining_m": None if self.distance_remaining_m is None
            else round(self.distance_remaining_m, 2),
            "result": self.result,
        }


def idle_dict() -> dict:
    return {
        "state": STATE_IDLE,
        "command": None,
        "room_id": None,
        "room_name": None,
        "phase": None,
        "attempt": 0,
        "max_attempts": 0,
        "distance_remaining_m": None,
        "result": None,
    }
