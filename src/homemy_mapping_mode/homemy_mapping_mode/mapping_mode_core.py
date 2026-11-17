"""ROS-free core of the HomeMy mapping-mode manager.

The behavior follows ``contracts/api/app-bridge.md``:

* mapping mode is ``off`` after every start;
* ``enable`` is accepted only while the lifecycle state allows it;
* ``disable`` ends the mode normally;
* ``stop`` is accepted in every state and is idempotent;
* the mode ends by itself after a period without controller input;
* a lifecycle fault or shutdown ends the mode at once.

Switching mapping mode on never moves the robot. This module does not know
about motors; it only decides the mode and describes it for the app.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
import math
import re
from typing import Any, Optional, Sequence

SCHEMA_VERSION = 1
MAXIMUM_COMMAND_BYTES = 4096
COMMAND_KINDS = ("enable", "disable", "stop")
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")

STATE_OFF = "off"
STATE_ACTIVE = "active"

END_APP_DISABLE = "app_disable"
END_APP_STOP = "app_stop"
END_INACTIVITY = "inactivity_timeout"
END_FAULT = "fault"
END_SHUTDOWN = "shutdown"

BLOCK_NOT_READY = "not_ready"
BLOCK_FAULT = "fault"
BLOCK_SHUTTING_DOWN = "shutting_down"

LIFECYCLE_ACCEPTING = frozenset({"READY", "READY_LIMITED"})
LIFECYCLE_FAULT = "FAULT"
LIFECYCLE_SHUTTING_DOWN = "SHUTTING_DOWN"


class CommandError(ValueError):
    """A command was malformed. ``request_id`` is kept when it was valid."""

    def __init__(self, message: str, request_id: Optional[str] = None) -> None:
        super().__init__(message)
        self.request_id = request_id


@dataclass(frozen=True)
class Command:
    kind: str
    request_id: str


def valid_request_id(value: Any) -> bool:
    return isinstance(value, str) and REQUEST_ID_PATTERN.fullmatch(value) is not None


def parse_command(text: str) -> Command:
    """Parse one command JSON object strictly; unknown fields are refused."""

    if not isinstance(text, str):
        raise CommandError("Befehl ist kein Text.")
    if len(text.encode("utf-8", errors="replace")) > MAXIMUM_COMMAND_BYTES:
        raise CommandError("Befehl ist zu groß.")
    try:
        payload = json.loads(text)
    except (ValueError, RecursionError):
        raise CommandError("Befehl ist kein gültiges JSON.") from None
    if not isinstance(payload, dict):
        raise CommandError("Befehl muss ein JSON-Objekt sein.")

    request_id = payload.get("request_id")
    kept_id = request_id if valid_request_id(request_id) else None
    if set(payload) != {"command", "request_id"}:
        raise CommandError("Befehl enthält fehlende oder unbekannte Felder.", kept_id)
    if kept_id is None:
        raise CommandError("request_id ist ungültig.")
    kind = payload.get("command")
    if kind not in COMMAND_KINDS:
        raise CommandError("Unbekannter Befehl.", kept_id)
    return Command(kind=kind, request_id=kept_id)


def block_reason_for_lifecycle(state: Optional[str]) -> Optional[str]:
    """Why ``enable`` would be refused in this lifecycle state, or None."""

    if state in LIFECYCLE_ACCEPTING:
        return None
    if state == LIFECYCLE_FAULT:
        return BLOCK_FAULT
    if state == LIFECYCLE_SHUTTING_DOWN:
        return BLOCK_SHUTTING_DOWN
    return BLOCK_NOT_READY


def end_reason_for_lifecycle(state: Optional[str]) -> Optional[str]:
    """Lifecycle states that end an active mapping mode at once."""

    if state == LIFECYCLE_FAULT:
        return END_FAULT
    if state == LIFECYCLE_SHUTTING_DOWN:
        return END_SHUTDOWN
    return None


class ControllerTracker:
    """Connection and activity of the wireless controller, from Joy messages.

    The controller counts as connected while Joy messages keep arriving. This
    assumes that the joystick driver republishes its state at a fixed rate
    while the controller is connected (``autorepeat_rate`` of ``joy_node``).
    That assumption must be confirmed on the HomeMy computer.
    """

    def __init__(self, timeout_s: float, deadzone: float) -> None:
        if not math.isfinite(timeout_s) or timeout_s <= 0:
            raise ValueError("timeout_s must be positive")
        if not math.isfinite(deadzone) or not 0 <= deadzone < 1:
            raise ValueError("deadzone must be in [0, 1)")
        self.timeout_s = timeout_s
        self.deadzone = deadzone
        self.last_message_at: Optional[float] = None
        self.last_input_at: Optional[float] = None

    def update(self, axes: Sequence[float], buttons: Sequence[int], now: float) -> bool:
        """Record one Joy message. Returns True when it carried any input."""

        self.last_message_at = now
        active = any(
            math.isfinite(value) and abs(value) > self.deadzone for value in axes
        ) or any(button != 0 for button in buttons)
        if active:
            self.last_input_at = now
        return active

    def connected(self, now: float) -> bool:
        return (
            self.last_message_at is not None
            and 0 <= now - self.last_message_at <= self.timeout_s
        )


class MappingMode:
    """The mapping-mode state machine. Times are monotonic seconds."""

    def __init__(self, auto_end_timeout_s: float) -> None:
        if not math.isfinite(auto_end_timeout_s) or auto_end_timeout_s <= 0:
            raise ValueError("auto_end_timeout_s must be positive")
        self.auto_end_timeout_s = float(auto_end_timeout_s)
        self.state = STATE_OFF
        self.last_end_reason: Optional[str] = None
        self.last_activity_at: Optional[float] = None

    @property
    def active(self) -> bool:
        return self.state == STATE_ACTIVE

    def handle(
        self,
        command: Command,
        now: float,
        block_reason: Optional[str],
    ) -> tuple[bool, str]:
        """Apply a command. Returns (ok, message) for the result event."""

        if command.kind == "stop":
            if self.active:
                self._end(END_APP_STOP)
                return True, "Stopp ausgeführt. Kartiermodus ist aus."
            return True, "Stopp ausgeführt. Kartiermodus war bereits aus."

        if command.kind == "enable":
            if self.active:
                return True, "Kartiermodus ist bereits aktiv."
            if block_reason is not None:
                return False, f"Kartiermodus nicht möglich: {block_reason}"
            self.state = STATE_ACTIVE
            self.last_end_reason = None
            self.last_activity_at = now
            return True, "Kartiermodus ist aktiv."

        if not self.active:
            return True, "Kartiermodus ist bereits aus."
        self._end(END_APP_DISABLE)
        return True, "Kartiermodus beendet."

    def note_input(self, now: float) -> None:
        if self.active:
            self.last_activity_at = now

    def tick(self, now: float, lifecycle_state: Optional[str]) -> Optional[str]:
        """End the mode when required. Returns the end reason, if any."""

        if not self.active:
            return None
        reason = end_reason_for_lifecycle(lifecycle_state)
        if reason is not None:
            self._end(reason)
            return reason
        if self.remaining(now) <= 0:
            self._end(END_INACTIVITY)
            return END_INACTIVITY
        return None

    def remaining(self, now: float) -> Optional[float]:
        if not self.active or self.last_activity_at is None:
            return None
        left = self.auto_end_timeout_s - (now - self.last_activity_at)
        return min(self.auto_end_timeout_s, max(0.0, left))

    def _end(self, reason: str) -> None:
        self.state = STATE_OFF
        self.last_end_reason = reason
        self.last_activity_at = None


def build_status(
    mode: MappingMode,
    *,
    now: float,
    wall_time: float,
    controller_connected: bool,
    block_reason: Optional[str],
    event: str = "status",
    ok: bool = True,
    request_id: Optional[str] = None,
    message: Optional[str] = None,
) -> dict[str, Any]:
    """Describe the mode exactly as the app bridge contract requires."""

    if message is None:
        message = "Kartiermodus ist aktiv." if mode.active else "Kartiermodus ist aus."
    return {
        "schema_version": SCHEMA_VERSION,
        "event": event,
        "ok": bool(ok),
        "request_id": request_id,
        "message": message,
        "mapping_mode": {
            "state": mode.state,
            "controller_connected": bool(controller_connected),
            "auto_end_timeout_s": mode.auto_end_timeout_s,
            "auto_end_remaining_s": mode.remaining(now),
            "last_end_reason": mode.last_end_reason,
            "enable_block_reason": None if mode.active else block_reason,
        },
        "time": wall_time,
    }


def encode_status(status: dict[str, Any]) -> str:
    return json.dumps(status, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
