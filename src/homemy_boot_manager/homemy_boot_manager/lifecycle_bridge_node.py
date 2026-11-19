"""Bridge for the lifecycle state while the PMU does not exist.

Owner decision of 2026-11-19: until the power management unit is built, the
program that determines the robot's overall state is bridged. This node
publishes two fixed values that the rest of the software waits for:

- ``/homemy/lifecycle/state`` (std_msgs/String, latched, once per second):
  ``READY`` unless set otherwise;
- ``/homemy/safety/estop`` (std_msgs/Bool, five times per second): ``false``,
  "emergency stop not pressed", because without the PMU the software
  receives no emergency-stop signal.

It checks nothing: no self-test, no battery, no hardware. The stop at the
robot must therefore work without software. If the bridge stops, the motion
gate closes by itself, because both values go stale.

Both values can be changed by hand while it runs, for example to block all
motion or to test a fault:

    ros2 param set /lifecycle_bridge state FAULT
    ros2 param set /lifecycle_bridge estop_pressed true

The same node serves the simulation and the laboratory robot.
"""

from __future__ import annotations

import rclpy
from rcl_interfaces.msg import SetParametersResult
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool, String

from homemy_boot_manager.lifecycle_states import normalise_state

LATCHED = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)


class LifecycleBridge(Node):
    def __init__(self, **node_options) -> None:
        super().__init__("lifecycle_bridge", **node_options)
        self.declare_parameter("state_topic", "/homemy/lifecycle/state")
        self.declare_parameter("estop_topic", "/homemy/safety/estop")
        self.declare_parameter("state", "READY")
        self.declare_parameter("estop_pressed", False)
        self.declare_parameter("state_period_s", 1.0)
        self.declare_parameter("estop_period_s", 0.2)

        self.state = normalise_state(self.get_parameter("state").value)
        self.estop_pressed = bool(self.get_parameter("estop_pressed").value)
        self.state_publisher = self.create_publisher(
            String, str(self.get_parameter("state_topic").value), LATCHED
        )
        self.estop_publisher = self.create_publisher(
            Bool, str(self.get_parameter("estop_topic").value), 10
        )
        self.add_on_set_parameters_callback(self._on_parameters)
        self.create_timer(float(self.get_parameter("state_period_s").value), self._publish_state)
        self.create_timer(float(self.get_parameter("estop_period_s").value), self._publish_estop)
        self.get_logger().warning(
            "ÜBERBRÜCKUNG: Roboterzustand und Not-Halt-Signal sind feste Werte, "
            "die PMU ist nicht angeschlossen. Nichts wird geprüft. "
            "Der Halt am Roboter muss ohne Software wirken."
        )
        self._publish_state()
        self._publish_estop()

    def _on_parameters(self, parameters) -> SetParametersResult:
        state, estop = self.state, self.estop_pressed
        for parameter in parameters:
            if parameter.name == "state":
                try:
                    state = normalise_state(parameter.value)
                except ValueError as error:
                    return SetParametersResult(successful=False, reason=str(error))
            elif parameter.name == "estop_pressed":
                if not isinstance(parameter.value, bool):
                    return SetParametersResult(successful=False, reason="estop_pressed must be true or false")
                estop = parameter.value
        if (state, estop) != (self.state, self.estop_pressed):
            self.state, self.estop_pressed = state, estop
            self.get_logger().warning(
                f"Überbrückung von Hand gesetzt: Zustand {state}, "
                f"Not-Halt {'gedrückt' if estop else 'nicht gedrückt'}."
            )
            self._publish_state()
            self._publish_estop()
        return SetParametersResult(successful=True)

    def _publish_state(self) -> None:
        self.state_publisher.publish(String(data=self.state))

    def _publish_estop(self) -> None:
        self.estop_publisher.publish(Bool(data=self.estop_pressed))


def main(args=None) -> None:
    rclpy.init(args=args)
    node = None
    try:
        node = LifecycleBridge()
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
