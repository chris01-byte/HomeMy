"""ROS-level tests of the mapping-mode node: topics, QoS, and timing.

They run the real node in this process with a helper node and need a ROS 2
installation. Each test uses its own DDS domain so that parallel runs do not
see each other.
"""

import json
import os
import time

import pytest
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Joy
from std_msgs.msg import Bool, String

from homemy_mapping_mode.mapping_mode_node import MappingModeManager

LATCHED = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=1,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.TRANSIENT_LOCAL,
)
COMMANDS = QoSProfile(
    history=HistoryPolicy.KEEP_LAST,
    depth=10,
    reliability=ReliabilityPolicy.RELIABLE,
    durability=DurabilityPolicy.VOLATILE,
)


class Harness:
    def __init__(self, overrides):
        domain = 150 + os.getpid() % 80
        self.context = rclpy.Context()
        rclpy.init(context=self.context, domain_id=domain)
        parameters = [Parameter(name, value=value) for name, value in overrides.items()]
        self.node = MappingModeManager(context=self.context, parameter_overrides=parameters)
        self.helper = Node("mapping_mode_test_helper", context=self.context)
        self.statuses = []
        self.active = []
        self.helper.create_subscription(
            String, "/homemy/mapping_mode/status_json",
            lambda m: self.statuses.append(json.loads(m.data)), LATCHED)
        self.helper.create_subscription(
            Bool, "/homemy/mapping_mode/active", lambda m: self.active.append(m.data), LATCHED)
        self.commands = self.helper.create_publisher(
            String, "/homemy/mapping_mode/command_json", COMMANDS)
        self.lifecycle = self.helper.create_publisher(String, "/homemy/lifecycle/state", LATCHED)
        self.joy = self.helper.create_publisher(Joy, "/joy", 10)
        self.executor = SingleThreadedExecutor(context=self.context)
        self.executor.add_node(self.node)
        self.executor.add_node(self.helper)

    def spin(self, seconds):
        end = time.monotonic() + seconds
        while time.monotonic() < end:
            self.executor.spin_once(timeout_sec=0.02)

    def spin_until(self, predicate, timeout=5.0, feed=None):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if feed is not None:
                feed()
            self.executor.spin_once(timeout_sec=0.02)
            found = predicate()
            if found:
                return found
        raise AssertionError("condition not reached in time")

    def send(self, kind, request_id):
        self.commands.publish(String(data=json.dumps({"command": kind, "request_id": request_id})))

    def result(self, request_id, feed=None, timeout=5.0):
        return self.spin_until(
            lambda: next((s for s in self.statuses if s["request_id"] == request_id), None),
            timeout=timeout,
            feed=feed,
        )

    def ready(self, state="READY"):
        self.lifecycle.publish(String(data=state))

    def joy_message(self, pressed=False):
        message = Joy()
        message.axes = [0.0] * 8
        message.buttons = [0] * 13
        if pressed:
            message.axes[7] = 1.0
        self.joy.publish(message)

    def close(self):
        self.executor.shutdown()
        self.node.destroy_node()
        self.helper.destroy_node()
        rclpy.shutdown(context=self.context)


@pytest.fixture
def harness():
    created = []

    def make(**overrides):
        instance = Harness(overrides)
        created.append(instance)
        return instance

    yield make
    for instance in created:
        instance.close()


def test_latched_status_reports_off_and_no_controller(harness):
    h = harness()
    first = h.spin_until(lambda: h.statuses[-1] if h.statuses else None)
    assert first["mapping_mode"]["state"] == "off"
    assert first["mapping_mode"]["controller_connected"] is False
    assert first["mapping_mode"]["enable_block_reason"] == "not_ready"
    assert h.spin_until(lambda: h.active) == [False] or h.active[-1] is False


def test_enable_requires_ready_lifecycle(harness):
    h = harness()
    h.spin(0.3)
    h.send("enable", "ios-mode-1")
    refused = h.result("ios-mode-1")
    assert refused["ok"] is False
    assert refused["mapping_mode"]["state"] == "off"

    h.ready()
    h.spin_until(lambda: h.statuses and h.statuses[-1]["mapping_mode"]["enable_block_reason"] is None)
    h.send("enable", "ios-mode-2")
    accepted = h.result("ios-mode-2")
    assert accepted["ok"] is True
    assert accepted["event"] == "enable_result"
    assert accepted["mapping_mode"]["state"] == "active"
    assert h.spin_until(lambda: h.active and h.active[-1] is True)


def test_controller_connection_and_input(harness):
    h = harness(controller_timeout_s=0.3)
    h.ready()
    h.spin_until(
        lambda: h.statuses and h.statuses[-1]["mapping_mode"]["controller_connected"],
        feed=h.joy_message,
    )
    # No more Joy messages: the controller counts as disconnected again.
    h.spin_until(lambda: h.statuses and not h.statuses[-1]["mapping_mode"]["controller_connected"])


def test_stop_ends_mapping_mode_from_any_state(harness):
    h = harness()
    h.ready()
    h.spin(0.3)
    h.send("enable", "ios-mode-1")
    assert h.result("ios-mode-1")["mapping_mode"]["state"] == "active"
    h.send("stop", "ios-stop-1")
    stopped = h.result("ios-stop-1")
    assert stopped["ok"] is True
    assert stopped["event"] == "stop_result"
    assert stopped["mapping_mode"]["state"] == "off"
    assert stopped["mapping_mode"]["last_end_reason"] == "app_stop"
    assert h.spin_until(lambda: h.active and h.active[-1] is False)


def test_mode_ends_by_itself_and_input_keeps_it_alive(harness):
    h = harness(auto_end_timeout_s=1.0)
    h.ready()
    h.spin(0.3)
    h.send("enable", "ios-mode-1")
    assert h.result("ios-mode-1")["mapping_mode"]["state"] == "active"
    mark = len(h.statuses)

    # Driving keeps the mode alive well past its timeout.
    end = time.monotonic() + 1.6
    while time.monotonic() < end:
        h.joy_message(pressed=True)
        h.spin(0.05)
    assert all(s["mapping_mode"]["state"] == "active" for s in h.statuses[mark:])
    assert len(h.statuses[mark:]) >= 2

    ended = h.spin_until(
        lambda: next((s for s in h.statuses[mark:]
                      if s["mapping_mode"]["state"] == "off"), None),
        timeout=3.0,
        feed=h.joy_message,
    )
    assert ended["mapping_mode"]["last_end_reason"] == "inactivity_timeout"


def test_fault_ends_mapping_mode(harness):
    h = harness()
    h.ready()
    h.spin(0.3)
    h.send("enable", "ios-mode-1")
    assert h.result("ios-mode-1")["mapping_mode"]["state"] == "active"
    h.ready("FAULT")
    ended = h.spin_until(
        lambda: next((s for s in reversed(h.statuses)
                      if s["mapping_mode"]["last_end_reason"] == "fault"), None))
    assert ended["mapping_mode"]["state"] == "off"
    assert ended["mapping_mode"]["enable_block_reason"] == "fault"


def test_malformed_command_is_refused(harness):
    h = harness()
    h.spin(0.3)
    count = len(h.statuses)
    h.commands.publish(String(data="{kaputt"))
    refused = h.spin_until(
        lambda: next((s for s in h.statuses[count:] if s["ok"] is False), None))
    assert refused["event"] == "status"
    assert refused["mapping_mode"]["state"] == "off"


def test_status_is_published_periodically(harness):
    h = harness(status_period_s=0.2)
    h.spin(1.2)
    assert len(h.statuses) >= 4
