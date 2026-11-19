"""Tests of the lifecycle bridge."""

import os
import time

import pytest
import rclpy
from rclpy.executors import SingleThreadedExecutor
from rclpy.parameter import Parameter
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy
from std_msgs.msg import Bool, String

from homemy_boot_manager.lifecycle_bridge_node import LifecycleBridge
from homemy_boot_manager.lifecycle_states import BRIDGE_STATES, LIFECYCLE_STATES, normalise_state

LATCHED = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL)


def test_states_follow_the_lifecycle_contract():
    assert set(BRIDGE_STATES) < set(LIFECYCLE_STATES)
    assert normalise_state(" ready ") == "READY"
    for bad in ("OFF", "BOOTING", "", "ok", None, 3):
        with pytest.raises(ValueError):
            normalise_state(bad)


@pytest.fixture
def harness():
    context = rclpy.Context()
    rclpy.init(context=context, domain_id=int(os.environ.get("ROS_DOMAIN_ID", "77")) % 100 + 120)
    nodes = []
    executor = SingleThreadedExecutor(context=context)

    def start(**overrides):
        bridge = LifecycleBridge(
            context=context,
            parameter_overrides=[Parameter(name, value=value) for name, value in overrides.items()],
        )
        listener = rclpy.create_node("bridge_listener", context=context)
        seen = {"state": [], "estop": []}
        listener.create_subscription(String, "/homemy/lifecycle/state", lambda m: seen["state"].append(m.data), LATCHED)
        listener.create_subscription(Bool, "/homemy/safety/estop", lambda m: seen["estop"].append(m.data), 10)
        for node in (bridge, listener):
            executor.add_node(node)
            nodes.append(node)

        def spin(seconds):
            end = time.monotonic() + seconds
            while time.monotonic() < end:
                executor.spin_once(timeout_sec=0.02)

        return bridge, seen, spin

    yield start
    executor.shutdown()
    for node in nodes:
        node.destroy_node()
    rclpy.shutdown(context=context)


def test_bridge_reports_ready_and_a_released_emergency_stop(harness):
    _bridge, seen, spin = harness()
    spin(1.0)
    assert seen["state"] and set(seen["state"]) == {"READY"}
    assert len(seen["estop"]) >= 3 and set(seen["estop"]) == {False}


def test_values_can_be_set_by_hand_and_invalid_ones_are_refused(harness):
    bridge, seen, spin = harness()
    spin(0.5)
    results = bridge.set_parameters([Parameter("state", value="fault")])
    assert results[0].successful
    results = bridge.set_parameters([Parameter("estop_pressed", value=True)])
    assert results[0].successful
    spin(0.6)
    assert seen["state"][-1] == "FAULT"
    assert seen["estop"][-1] is True

    refused = bridge.set_parameters([Parameter("state", value="GO")])
    assert not refused[0].successful
    spin(0.3)
    assert seen["state"][-1] == "FAULT"


def test_bridge_refuses_to_start_with_an_unknown_state(harness):
    with pytest.raises(ValueError):
        harness(state="RUNNING")
