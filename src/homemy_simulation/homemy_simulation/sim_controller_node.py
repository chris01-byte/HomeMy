#!/usr/bin/env python3
"""Stand-in for the wireless controller and joy_node. Simulation only.

Publishes ``sensor_msgs/Joy`` at ``rate_hz`` while ``connected`` is true. With
``driving`` true the direction pad reports "forward" (axis 7, as on the
Amadeus DualShock layout). Both parameters can be changed at runtime:

    ros2 param set /homemy_sim_controller driving false
    ros2 param set /homemy_sim_controller connected false
"""

from __future__ import annotations

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy


class SimController(Node):
    def __init__(self, **node_options) -> None:
        super().__init__("homemy_sim_controller", **node_options)
        self.declare_parameter("joy_topic", "/joy")
        self.declare_parameter("rate_hz", 20.0)
        self.declare_parameter("connected", True)
        self.declare_parameter("driving", True)
        self.declare_parameter("axis_count", 8)
        self.declare_parameter("button_count", 13)
        self.declare_parameter("drive_axis", 7)

        rate = float(self.get_parameter("rate_hz").value)
        self.publisher = self.create_publisher(Joy, self.get_parameter("joy_topic").value, 10)
        self.create_timer(1.0 / rate, self._on_tick)
        self.get_logger().warning("SIMULATION: simulierter Controller.")

    def _on_tick(self) -> None:
        if not self.get_parameter("connected").value:
            return
        message = Joy()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = "sim_controller"
        message.axes = [0.0] * int(self.get_parameter("axis_count").value)
        message.buttons = [0] * int(self.get_parameter("button_count").value)
        axis = int(self.get_parameter("drive_axis").value)
        if self.get_parameter("driving").value and 0 <= axis < len(message.axes):
            message.axes[axis] = 1.0
        self.publisher.publish(message)


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
