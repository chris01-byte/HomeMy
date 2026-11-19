#!/usr/bin/env python3
"""Stand-in for the wireless controller, its radio link, and the person using it.

Simulation only. Publishes, at ``rate_hz`` while ``connected`` is true:

- ``sensor_msgs/Joy`` on ``/joy`` in the DualShock 4 layout of the ROS
  joystick driver (axis 6 direction pad left/right, left = +1; axis 7 up/down,
  up = +1; button 5 = R1);
- ``std_msgs/Bool`` on ``/homemy/controller/link``, the radio-link watchdog.

With ``link_frozen`` true the Joy messages keep repeating while the link
reports down, which is what a silent radio loss looks like on the robot.

What is pressed:

- ``follow_route`` true: a careful person drives the mapping route of the
  world file with the direction pad: turn on the spot towards the next
  waypoint, then drive straight, using the simulated ground-truth pose
  (``/homemy/sim/ground_truth``). Progress is published on
  ``/homemy/sim/operator_status``.
- otherwise ``driving`` true holds "forward" (the S1 behaviour), and false
  presses nothing.

Parameters can be changed at runtime, e.g.:

    ros2 param set /homemy_sim_controller link_frozen true
"""

from __future__ import annotations

import json
import math
from typing import List, Optional, Tuple

import rclpy
from geometry_msgs.msg import PoseStamped
from rclpy.node import Node
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool, String

AXIS_TURN = 6
AXIS_DRIVE = 7
BUTTON_TURBO = 5


class RouteFollower:
    """Direction-pad decisions of a careful person. Pure logic; no ROS."""

    def __init__(self, waypoints: List[Tuple[float, float]], tolerance_m: float = 0.12,
                 start_turn_deg: float = 12.0, stop_turn_deg: float = 4.0) -> None:
        self.waypoints = list(waypoints)
        self.index = 0
        self.tolerance_m = tolerance_m
        self.start_turn = math.radians(start_turn_deg)
        self.stop_turn = math.radians(stop_turn_deg)
        self.turning = True

    @property
    def done(self) -> bool:
        return self.index >= len(self.waypoints)

    def press(self, pose: Tuple[float, float, float]) -> Tuple[float, float]:
        """Return (turn axis, drive axis) for the current pose."""

        while not self.done:
            tx, ty = self.waypoints[self.index]
            if math.hypot(tx - pose[0], ty - pose[1]) > self.tolerance_m:
                break
            self.index += 1
            self.turning = True
        if self.done:
            return 0.0, 0.0
        tx, ty = self.waypoints[self.index]
        error = math.atan2(ty - pose[1], tx - pose[0]) - pose[2]
        error = math.atan2(math.sin(error), math.cos(error))
        if self.turning and abs(error) < self.stop_turn:
            self.turning = False
        elif not self.turning and abs(error) > self.start_turn:
            self.turning = True
        if self.turning:
            return (1.0 if error > 0 else -1.0), 0.0
        return 0.0, 1.0


def load_route(world_file: str) -> List[Tuple[float, float]]:
    with open(world_file, encoding="utf-8") as handle:
        data = json.load(handle)
    return [(float(x), float(y)) for x, y in data["mapping_route"]["waypoints"]]


class SimController(Node):
    def __init__(self, **node_options) -> None:
        super().__init__("homemy_sim_controller", **node_options)
        declare = self.declare_parameter
        declare("joy_topic", "/joy")
        declare("link_topic", "/homemy/controller/link")
        declare("ground_truth_topic", "/homemy/sim/ground_truth")
        declare("status_topic", "/homemy/sim/operator_status")
        declare("rate_hz", 20.0)
        declare("connected", True)
        declare("link_frozen", False)
        declare("driving", True)
        declare("follow_route", False)
        declare("world_file", "")
        declare("turbo_on_straights", True)
        declare("axis_count", 8)
        declare("button_count", 13)
        declare("drive_axis", AXIS_DRIVE)

        self.follower: Optional[RouteFollower] = None
        if self.get_parameter("follow_route").value:
            world_file = str(self.get_parameter("world_file").value)
            if not world_file:
                raise ValueError("follow_route needs world_file")
            self.follower = RouteFollower(load_route(world_file))
        self.pose: Optional[Tuple[float, float, float]] = None

        rate = float(self.get_parameter("rate_hz").value)
        self.joy_pub = self.create_publisher(Joy, self.get_parameter("joy_topic").value, 10)
        self.link_pub = self.create_publisher(Bool, self.get_parameter("link_topic").value, 10)
        self.status_pub = self.create_publisher(String, self.get_parameter("status_topic").value, 10)
        self.create_subscription(PoseStamped, self.get_parameter("ground_truth_topic").value, self._on_pose, 10)
        self.create_timer(1.0 / rate, self._on_tick)
        self.get_logger().warning("SIMULATION: simulierter Controller.")

    def _on_pose(self, message: PoseStamped) -> None:
        q = message.pose.orientation
        yaw = math.atan2(2.0 * (q.w * q.z + q.x * q.y), 1.0 - 2.0 * (q.y * q.y + q.z * q.z))
        self.pose = (message.pose.position.x, message.pose.position.y, yaw)

    def _on_tick(self) -> None:
        if not self.get_parameter("connected").value:
            return
        frozen = bool(self.get_parameter("link_frozen").value)
        self.link_pub.publish(Bool(data=not frozen))

        message = Joy()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = "sim_controller"
        message.axes = [0.0] * int(self.get_parameter("axis_count").value)
        message.buttons = [0] * int(self.get_parameter("button_count").value)
        if self.follower is not None:
            if self.pose is not None and self.get_parameter("driving").value:
                turn, drive = self.follower.press(self.pose)
                message.axes[AXIS_TURN] = turn
                message.axes[AXIS_DRIVE] = drive
                if drive and self.get_parameter("turbo_on_straights").value:
                    message.buttons[BUTTON_TURBO] = 1
            self.status_pub.publish(String(data=json.dumps({
                "waypoint_index": self.follower.index,
                "waypoints": len(self.follower.waypoints),
                "done": self.follower.done,
            })))
        else:
            axis = int(self.get_parameter("drive_axis").value)
            if self.get_parameter("driving").value and 0 <= axis < len(message.axes):
                message.axes[axis] = 1.0
        self.joy_pub.publish(message)


def main(args=None) -> None:
    rclpy.init(args=args)
    node = None
    try:
        node = SimController()
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
