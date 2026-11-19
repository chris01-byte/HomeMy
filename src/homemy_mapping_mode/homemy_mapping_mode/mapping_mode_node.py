#!/usr/bin/env python3
"""ROS 2 node for the HomeMy mapping mode (contracts/api/app-bridge.md).

The node publishes the mode for the app and as a plain Bool for the rest of
the robot. It never publishes a velocity or any other motion command. Turning
``off`` into zero motion is the job of the movement gate.
"""

from __future__ import annotations

import time
from typing import Optional

import rclpy
from rclpy.node import Node
from rclpy.qos import (
    DurabilityPolicy,
    HistoryPolicy,
    QoSProfile,
    ReliabilityPolicy,
    qos_profile_sensor_data,
)
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool, String

from homemy_mapping_mode.mapping_mode_core import (
    CommandError,
    ControllerTracker,
    MappingMode,
    block_reason_for_lifecycle,
    build_status,
    encode_status,
    parse_command,
)


LATCHED_QOS = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)
COMMAND_QOS = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.VOLATILE,
)


class MappingModeManager(Node):
    def __init__(self, **node_options) -> None:
        # node_options lets tests pass a context and parameter overrides.
        super().__init__("homemy_mapping_mode", **node_options)

        self.declare_parameter("command_topic", "/homemy/mapping_mode/command_json")
        self.declare_parameter("status_topic", "/homemy/mapping_mode/status_json")
        self.declare_parameter("active_topic", "/homemy/mapping_mode/active")
        self.declare_parameter("joy_topic", "/joy")
        self.declare_parameter("lifecycle_state_topic", "/homemy/lifecycle/state")
        self.declare_parameter("auto_end_timeout_s", 300.0)
        self.declare_parameter("controller_timeout_s", 0.5)
        self.declare_parameter("controller_deadzone", 0.2)
        self.declare_parameter("lifecycle_timeout_s", 3.0)
        self.declare_parameter("status_period_s", 0.5)
        self.declare_parameter("tick_period_s", 0.1)

        value = lambda name: self.get_parameter(name).value  # noqa: E731
        self.lifecycle_timeout_s = self._positive(value("lifecycle_timeout_s"), "lifecycle_timeout_s")
        self.status_period_s = self._positive(value("status_period_s"), "status_period_s")
        tick_period_s = self._positive(value("tick_period_s"), "tick_period_s")

        self.mode = MappingMode(self._positive(value("auto_end_timeout_s"), "auto_end_timeout_s"))
        self.controller = ControllerTracker(
            self._positive(value("controller_timeout_s"), "controller_timeout_s"),
            float(value("controller_deadzone")),
        )
        self.lifecycle_state: Optional[str] = None
        self.lifecycle_received_at: Optional[float] = None
        self.last_published_view: Optional[tuple] = None
        self.last_status_at = 0.0

        self.status_publisher = self.create_publisher(String, value("status_topic"), LATCHED_QOS)
        self.active_publisher = self.create_publisher(Bool, value("active_topic"), LATCHED_QOS)
        self.create_subscription(String, value("command_topic"), self._on_command, COMMAND_QOS)
        self.create_subscription(Joy, value("joy_topic"), self._on_joy, qos_profile_sensor_data)
        self.create_subscription(
            String, value("lifecycle_state_topic"), self._on_lifecycle, LATCHED_QOS
        )
        self.create_timer(tick_period_s, self._on_tick)

        self.get_logger().info(
            "Kartiermodus-Manager bereit; Modus ist aus. "
            f"Automatisches Ende nach {self.mode.auto_end_timeout_s:.0f} s ohne Eingabe."
        )
        self._publish(force=True)

    def _positive(self, raw: object, name: str) -> float:
        try:
            number = float(raw)
        except (TypeError, ValueError):
            raise RuntimeError(f"Parameter {name} ist keine Zahl.") from None
        if not number > 0 or number == float("inf"):
            raise RuntimeError(f"Parameter {name} muss positiv und endlich sein.")
        return number

    # ------------------------------------------------------------------ inputs

    def _current_lifecycle(self, now: float) -> Optional[str]:
        if self.lifecycle_received_at is None:
            return None
        if now - self.lifecycle_received_at > self.lifecycle_timeout_s:
            return None
        return self.lifecycle_state

    def _on_lifecycle(self, message: String) -> None:
        state = message.data.strip().upper()
        self.lifecycle_state = state or None
        self.lifecycle_received_at = time.monotonic()

    def _on_joy(self, message: Joy) -> None:
        now = time.monotonic()
        if self.controller.update(message.axes, message.buttons, now):
            self.mode.note_input(now)

    def _on_command(self, message: String) -> None:
        now = time.monotonic()
        try:
            command = parse_command(message.data)
        except CommandError as error:
            self.get_logger().warning(f"Befehl abgelehnt: {error}")
            self._publish(force=True, ok=False, request_id=error.request_id, message=str(error))
            return

        block = block_reason_for_lifecycle(self._current_lifecycle(now))
        was_active = self.mode.active
        ok, text = self.mode.handle(command, now, block)
        if command.kind == "stop":
            self.get_logger().warning(f"Stopp aus der App ({command.request_id}).")
        elif was_active != self.mode.active or not ok:
            self.get_logger().info(f"{command.kind} ({command.request_id}): {text}")
        self._publish(
            force=True,
            event=f"{command.kind}_result",
            ok=ok,
            request_id=command.request_id,
            message=text,
        )

    def _on_tick(self) -> None:
        now = time.monotonic()
        reason = self.mode.tick(now, self._current_lifecycle(now))
        if reason is not None:
            self.get_logger().info(f"Kartiermodus beendet: {reason}.")
        self._publish(force=False)

    # ----------------------------------------------------------------- outputs

    def _publish(
        self,
        *,
        force: bool,
        event: str = "status",
        ok: bool = True,
        request_id: Optional[str] = None,
        message: Optional[str] = None,
    ) -> None:
        now = time.monotonic()
        connected = self.controller.connected(now)
        block = block_reason_for_lifecycle(self._current_lifecycle(now))
        view = (self.mode.state, connected, self.mode.last_end_reason, block)
        changed = view != self.last_published_view
        periodic = now - self.last_status_at >= self.status_period_s
        if not (force or changed or periodic):
            return

        status = build_status(
            self.mode,
            now=now,
            wall_time=time.time(),
            controller_connected=connected,
            block_reason=block,
            event=event,
            ok=ok,
            request_id=request_id,
            message=message,
        )
        self.status_publisher.publish(String(data=encode_status(status)))
        self.active_publisher.publish(Bool(data=self.mode.active))
        self.last_published_view = view
        self.last_status_at = now


def main(args: Optional[list[str]] = None) -> None:
    rclpy.init(args=args)
    node: Optional[MappingModeManager] = None
    try:
        node = MappingModeManager()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if node is not None:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
