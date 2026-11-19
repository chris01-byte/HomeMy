"""ROS node of the mission manager: drive to a room on command from the app.

Inputs: ``/homemy/mission/command_json`` (app), the room overlay status, the
localization status and ready signal, mapping mode, and the lifecycle state.
Outputs: ``/homemy/mission/status_json`` (latched) for the app and
``/homemy/mission/drive_active`` (latched Bool) for the motion gate. Drive
goals go to Nav2 (``navigate_to_pose``) with the recovery-free tree; the
motion gate decides whether its commands reach the drive.
"""

from __future__ import annotations

import json
import math
import time
from typing import Optional

import rclpy
from action_msgs.msg import GoalStatus
from nav2_msgs.action import NavigateToPose
from rclpy.action import ActionClient
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool, String

from homemy_mission.mission_core import (
    CommandError,
    Mission,
    MissionPolicy,
    Preconditions,
    idle_dict,
    parse_command,
    start_block_reason,
)
from homemy_mission.room_goal import decode_semantic_map_status, resolve_room_goal, semantic_snapshot_is_fresh

LATCHED = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL)
COMMANDS = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE)
READY_STATES = {"READY", "READY_LIMITED"}  # to start; a running mission ends only on FAULT or SHUTTING_DOWN


class MissionManager(Node):
    def __init__(self, **node_options) -> None:
        super().__init__("mission_manager", **node_options)
        declare = self.declare_parameter
        declare("command_topic", "/homemy/mission/command_json")
        declare("status_topic", "/homemy/mission/status_json")
        declare("drive_active_topic", "/homemy/mission/drive_active")
        declare("room_status_topic", "/homemy/room_manager/status_json")
        declare("localization_status_topic", "/homemy/localization/status_json")
        declare("localization_ready_topic", "/homemy/localization/ready")
        declare("mapping_active_topic", "/homemy/mapping_mode/active")
        declare("lifecycle_state_topic", "/homemy/lifecycle/state")
        declare("navigate_action", "/navigate_to_pose")
        declare("bt_xml", "")
        declare("max_attempts", 3)
        declare("retry_wait_s", 3.0)
        declare("localization_grace_s", 30.0)
        declare("room_status_timeout_s", 6.0)
        declare("input_timeout_s", 3.0)
        declare("status_period_s", 0.5)

        def value(name):
            return self.get_parameter(name).value

        self.policy = MissionPolicy(int(value("max_attempts")), float(value("retry_wait_s")),
                                    float(value("localization_grace_s")))
        self.bt_xml = str(value("bt_xml"))
        self.room_timeout = float(value("room_status_timeout_s"))
        self.input_timeout = float(value("input_timeout_s"))
        self.status_period = float(value("status_period_s"))

        self.mission: Optional[Mission] = None
        self.goal_handle = None
        self.goal_future = None
        self.goal_epoch = 0
        self.cancel_pending = False
        self.room_status_raw: Optional[str] = None
        self.room_status_at: Optional[float] = None
        self.localization_fp: Optional[str] = None
        self.localization_at: Optional[float] = None
        self.ready: Optional[bool] = None
        self.ready_at: Optional[float] = None
        self.mapping_active: Optional[bool] = None
        self.mapping_at: Optional[float] = None
        self.lifecycle: Optional[str] = None
        self.lifecycle_at: Optional[float] = None
        self.last_status = None
        self.last_status_at = 0.0

        self.nav = ActionClient(self, NavigateToPose, str(value("navigate_action")))
        self.status_pub = self.create_publisher(String, str(value("status_topic")), LATCHED)
        self.active_pub = self.create_publisher(Bool, str(value("drive_active_topic")), LATCHED)
        self.create_subscription(String, str(value("command_topic")), self._on_command, COMMANDS)
        self.create_subscription(String, str(value("room_status_topic")), self._on_rooms, LATCHED)
        self.create_subscription(String, str(value("localization_status_topic")), self._on_localization, LATCHED)
        self.create_subscription(Bool, str(value("localization_ready_topic")), self._on_ready, 10)
        self.create_subscription(Bool, str(value("mapping_active_topic")), self._on_mapping, LATCHED)
        self.create_subscription(String, str(value("lifecycle_state_topic")), self._on_lifecycle, LATCHED)
        self.create_timer(0.1, self._tick)
        self._publish(force=True)

    # ------------------------------------------------------------ inputs

    def _on_rooms(self, message: String) -> None:
        self.room_status_raw = message.data
        self.room_status_at = time.monotonic()

    def _on_localization(self, message: String) -> None:
        try:
            status = json.loads(message.data)
            fingerprint = (status.get("map") or {}).get("fingerprint") if status.get("mode") == "navigation" else None
            self.localization_fp = fingerprint if isinstance(fingerprint, str) else None
            self.localization_at = time.monotonic()
        except (ValueError, AttributeError):
            self.localization_fp = None

    def _on_ready(self, message: Bool) -> None:
        self.ready, self.ready_at = bool(message.data), time.monotonic()

    def _on_mapping(self, message: Bool) -> None:
        self.mapping_active, self.mapping_at = bool(message.data), time.monotonic()

    def _on_lifecycle(self, message: String) -> None:
        self.lifecycle, self.lifecycle_at = message.data.strip().upper(), time.monotonic()

    def _fresh(self, at: Optional[float], timeout: Optional[float] = None) -> bool:
        return at is not None and 0 <= time.monotonic() - at <= (timeout or self.input_timeout)

    def _snapshot(self):
        if self.room_status_raw is None or not semantic_snapshot_is_fresh(
                self.room_status_at, time.monotonic(), self.room_timeout):
            return None, "room overlay status missing or stale"
        return decode_semantic_map_status(self.room_status_raw)

    def _preconditions(self) -> Preconditions:
        snapshot, _ = self._snapshot()
        return Preconditions(
            mapping_active=bool(self.mapping_active) or not self._fresh(self.mapping_at),
            lifecycle_ready=self._fresh(self.lifecycle_at) and self.lifecycle in READY_STATES,
            localization_ready=bool(self.ready) and self._fresh(self.ready_at, 1.0),
            localization_map_fingerprint=self.localization_fp if self._fresh(self.localization_at) else None,
            rooms_map_fingerprint=None if snapshot is None else snapshot.fingerprint,
            navigation_available=self.nav.server_is_ready(),
        )

    # ------------------------------------------------------------ commands

    def _on_command(self, message: String) -> None:
        try:
            command = parse_command(message.data)
        except CommandError as error:
            self._publish(force=True, event="command_result", ok=False, request_id=error.request_id,
                          message=f"Befehl abgelehnt: {error}")
            return
        if command.command == "cancel":
            self._cancel("app_cancel")
            self._publish(force=True, event="cancel_result", ok=True, request_id=command.request_id,
                          message="Auftrag abgebrochen." if self.mission is not None else "Kein Auftrag aktiv.")
            return
        running = self.mission is not None and self.mission.running
        reason = start_block_reason(running, self._preconditions())
        if reason is not None:
            self._publish(force=True, event="go_to_room_result", ok=False, request_id=command.request_id,
                          message=f"Fahrt nicht möglich: {reason}", block_reason=reason)
            return
        snapshot, error = self._snapshot()
        goal, error = (None, error) if snapshot is None else resolve_room_goal(
            snapshot, room_name=command.room_name, room_id=command.room_id)
        if goal is None:
            self._publish(force=True, event="go_to_room_result", ok=False, request_id=command.request_id,
                          message=f"Raum nicht anfahrbar: {error}", block_reason="room_invalid")
            return
        now = time.monotonic()
        self.mission = Mission(goal.room_id, goal.room_name, (goal.x, goal.y, goal.yaw), self.policy, now)
        self.mission.note(now, f"go_to_room {goal.room_name}")
        self._send_goal()
        self._publish(force=True, event="go_to_room_result", ok=True, request_id=command.request_id,
                      message=f"Fahrt zu {goal.room_name} gestartet.")

    # ------------------------------------------------------------ Nav2

    def _send_goal(self) -> None:
        mission = self.mission
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = "map"
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        x, y, yaw = mission.goal
        goal.pose.pose.position.x, goal.pose.pose.position.y = float(x), float(y)
        goal.pose.pose.orientation.z, goal.pose.pose.orientation.w = math.sin(yaw / 2), math.cos(yaw / 2)
        goal.behavior_tree = self.bt_xml
        self.goal_epoch += 1
        epoch = self.goal_epoch
        self.goal_handle = None
        self.goal_future = self.nav.send_goal_async(goal, feedback_callback=lambda f: self._on_feedback(epoch, f))
        self.goal_future.add_done_callback(lambda future: self._on_goal_response(epoch, future))

    def _on_goal_response(self, epoch: int, future) -> None:
        if epoch != self.goal_epoch or self.mission is None:
            return
        handle = future.result()
        now = time.monotonic()
        if handle is None or not handle.accepted:
            if self.mission.running:
                self.mission.drive_failed(now, "goal_rejected")
            return
        self.goal_handle = handle
        if self.cancel_pending or not self.mission.running:
            handle.cancel_goal_async()
            return
        self.mission.driving(now)
        handle.get_result_async().add_done_callback(lambda f: self._on_result(epoch, f))

    def _on_feedback(self, epoch: int, feedback) -> None:
        if epoch == self.goal_epoch and self.mission is not None and self.mission.running:
            distance = feedback.feedback.distance_remaining
            if math.isfinite(distance):
                self.mission.distance_remaining_m = float(distance)

    def _on_result(self, epoch: int, future) -> None:
        if epoch != self.goal_epoch or self.mission is None:
            return
        self.goal_handle = None
        result = future.result()
        now = time.monotonic()
        if not self.mission.running:
            return
        status = None if result is None else result.status
        if status == GoalStatus.STATUS_SUCCEEDED:
            self.mission.arrived(now)
        elif status == GoalStatus.STATUS_CANCELED:
            self.mission.cancel(now, "navigation_canceled")
        else:
            code = getattr(getattr(result, "result", None), "error_code", 0)
            self.mission.drive_failed(now, f"navigation_failed:{code}")
        self._publish(force=True)

    def _cancel(self, reason: str, failed: bool = False) -> None:
        if self.mission is None or not self.mission.running:
            return
        if failed:
            self.mission.fail(time.monotonic(), reason)
        else:
            self.mission.cancel(time.monotonic(), reason)
        if self.goal_handle is not None:
            self.goal_handle.cancel_goal_async()
        else:
            self.cancel_pending = True
        self.goal_epoch += 1  # late callbacks of the old goal are ignored

    # ------------------------------------------------------------ loop

    def _tick(self) -> None:
        now = time.monotonic()
        mission = self.mission
        if mission is not None and mission.running:
            if self.mapping_active:
                self._cancel("mapping_started")
            elif self._fresh(self.lifecycle_at) and self.lifecycle in {"FAULT", "SHUTTING_DOWN"}:
                self._cancel("lifecycle_" + self.lifecycle.lower(), failed=True)
            elif mission.localization(bool(self.ready) and self._fresh(self.ready_at, 1.0), now):
                self._cancel("localization_lost", failed=True)
            elif mission.retry_due(now):
                self._send_goal()
        if mission is not None and not mission.running:
            self.cancel_pending = self.cancel_pending and self.goal_handle is None
        self.active_pub.publish(Bool(data=bool(mission is not None and mission.running)))
        self._publish()

    def _publish(self, force: bool = False, event: str = "status", ok: bool = True,
                 request_id: Optional[str] = None, message: str = "", block_reason: Optional[str] = None) -> None:
        now = time.monotonic()
        mission = self.mission.as_dict() if self.mission is not None else idle_dict()
        running = self.mission is not None and self.mission.running
        current_block = start_block_reason(running, self._preconditions())
        view = (json.dumps(mission, sort_keys=True), current_block)
        if not force and view == self.last_status and now - self.last_status_at < self.status_period:
            return
        self.last_status, self.last_status_at = view, now
        if not message:
            message = {
                "idle": "Kein Auftrag.",
                "running": "Auftrag läuft.",
                "succeeded": "Ziel erreicht.",
                "failed": "Auftrag nicht erfüllt.",
                "canceled": "Auftrag abgebrochen.",
            }[mission["state"]]
        payload = {
            "schema_version": 1,
            "event": event,
            "ok": ok,
            "request_id": request_id,
            "message": message,
            "mission": mission,
            "start_block_reason": block_reason if event == "go_to_room_result" and not ok else current_block,
            "time": time.time(),
        }
        self.status_pub.publish(String(data=json.dumps(payload, ensure_ascii=False, allow_nan=False)))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = MissionManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
