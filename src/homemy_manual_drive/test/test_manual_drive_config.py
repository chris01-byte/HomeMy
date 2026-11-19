"""Static checks of the manual-drive profile against the contract."""

import pathlib

import yaml

PACKAGE = pathlib.Path(__file__).resolve().parents[1]
CONFIG = yaml.safe_load((PACKAGE / "config" / "manual_drive.yaml").read_text())
LAUNCH = (PACKAGE / "launch" / "manual_drive.launch.py").read_text()
GATE = yaml.safe_load(
    (PACKAGE.parent / "homemy_motion_gate" / "config" / "motion_gate.yaml").read_text()
)["motion_gate"]["ros__parameters"]


def teleop():
    return CONFIG["teleop_twist_joy_node"]["ros__parameters"]


def test_teleop_goes_to_the_motion_gate_only():
    assert "/homemy/cmd_vel/teleop" in LAUNCH
    assert '"/cmd_vel")' not in LAUNCH.replace('("/cmd_vel", "/homemy/cmd_vel/teleop")', "")


def test_direction_pad_without_dead_man_button():
    params = teleop()
    assert params["axis_linear"]["x"] == 7
    assert params["axis_angular"]["yaw"] == 6
    assert params["require_enable_button"] is False
    assert params["enable_turbo_button"] == 5


def test_teleop_speeds_fit_inside_the_gate_mapping_limits():
    params = teleop()
    for key in ("scale_linear", "scale_linear_turbo"):
        assert 0 < params[key]["x"] <= GATE["mapping_max_linear_mps"]
    for key in ("scale_angular", "scale_angular_turbo"):
        assert 0 < params[key]["yaw"] <= GATE["mapping_max_angular_rps"]


def test_joystick_repeats_and_ignores_small_deflections():
    joy = CONFIG["joy_node"]["ros__parameters"]
    assert joy["autorepeat_rate"] >= 10.0
    assert joy["deadzone"] >= 0.2


def test_a_held_direction_outlasts_the_gate_command_timeout():
    # The joystick repeats faster than the gate lets a command go stale, so a
    # held direction keeps driving and a released one stops.
    joy = CONFIG["joy_node"]["ros__parameters"]
    assert 1.0 / joy["autorepeat_rate"] < GATE["command_timeout_s"] / 2


def test_the_profile_starts_only_joystick_and_teleop():
    assert LAUNCH.count("Node(") == 2
    assert 'package="joy"' in LAUNCH and 'package="teleop_twist_joy"' in LAUNCH
