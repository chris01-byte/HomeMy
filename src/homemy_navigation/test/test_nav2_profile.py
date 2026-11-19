"""Static checks of the Nav2 profile against the robot model and the motion gate."""

import ast
import math
import pathlib
import xml.etree.ElementTree as ET

import yaml

PACKAGE = pathlib.Path(__file__).resolve().parents[1]
SRC = PACKAGE.parent
NAV2 = yaml.safe_load((PACKAGE / "config" / "nav2.yaml").read_text())
GEOMETRY = yaml.safe_load((SRC / "homemy_description" / "config" / "geometry.yaml").read_text())
GATE = yaml.safe_load((SRC / "homemy_motion_gate" / "config" / "motion_gate.yaml").read_text())[
    "motion_gate"]["ros__parameters"]
LAUNCH = (PACKAGE / "launch" / "navigation.launch.py").read_text()


def footprints():
    for costmap in ("local_costmap", "global_costmap"):
        params = NAV2[costmap][costmap]["ros__parameters"]
        yield costmap, ast.literal_eval(params["footprint"]), params["footprint_padding"]


def rounded_outline_distance(x, y):
    o = GEOMETRY["base_outline"]
    r = o["corner_radius"]
    cx = (o["x_max"] + o["x_min"]) / 2
    hx = (o["x_max"] - o["x_min"]) / 2 - r
    hy = o["y_half"] - r
    qx, qy = abs(x - cx) - hx, abs(y) - hy
    outside = math.hypot(max(qx, 0.0), max(qy, 0.0))
    inside = min(max(qx, qy), 0.0)
    return outside + inside - r


def test_footprint_vertices_lie_on_the_rounded_outline():
    for name, polygon, padding in footprints():
        assert len(polygon) >= 8, name
        for x, y in polygon:
            assert abs(rounded_outline_distance(x, y)) < 1e-3, (name, x, y)
        # The chords of the rounded corners cut at most 1 cm into the outline;
        # the padding covers that.
        assert padding >= 0.01


def test_footprint_spans_the_whole_base():
    o = GEOMETRY["base_outline"]
    for name, polygon, _ in footprints():
        xs = [p[0] for p in polygon]
        ys = [p[1] for p in polygon]
        assert math.isclose(min(xs), o["x_min"], abs_tol=1e-4), name
        assert math.isclose(max(xs), o["x_max"], abs_tol=1e-4), name
        assert math.isclose(max(ys), o["y_half"], abs_tol=1e-4), name


def test_unknown_space_is_never_free():
    planner = NAV2["planner_server"]["ros__parameters"]["GridBased"]
    assert planner["allow_unknown"] is False
    assert NAV2["global_costmap"]["global_costmap"]["ros__parameters"]["track_unknown_space"] is True


def test_obstacles_come_from_the_masked_scan():
    for costmap in ("local_costmap", "global_costmap"):
        scan = NAV2[costmap][costmap]["ros__parameters"]["obstacle_layer"]["scan"]
        assert scan["topic"] == "/scan_masked"
        assert scan["inf_is_valid"] is False
    assert NAV2["amcl"]["ros__parameters"]["scan_topic"] == "/scan_masked"


def test_the_tree_has_no_recovery_behaviours():
    tree = ET.parse(PACKAGE / "config" / "navigate_to_pose_no_recovery.xml")
    tags = {element.tag for element in tree.iter()}
    for forbidden in ("Spin", "BackUp", "Wait", "DriveOnHeading", "ClearEntireCostmap", "RecoveryNode"):
        assert forbidden not in tags
    assert {"ComputePathToPose", "FollowPath"} <= tags


def test_speeds_stay_inside_the_gate_mission_limits():
    smoother = NAV2["velocity_smoother"]["ros__parameters"]
    assert smoother["max_velocity"][0] <= GATE["mission_max_linear_mps"]
    assert smoother["max_velocity"][2] <= GATE["mission_max_angular_rps"]
    controller = NAV2["controller_server"]["ros__parameters"]["FollowPath"]
    assert controller["desired_linear_vel"] <= GATE["mission_max_linear_mps"]
    assert controller["allow_reversing"] is False


def test_navigation_commands_go_to_the_motion_gate_only():
    assert '("cmd_vel_smoothed", "/homemy/cmd_vel/nav")' in LAUNCH
    assert '("cmd_vel", "cmd_vel_nav_raw")' in LAUNCH
    assert '"/cmd_vel"' not in LAUNCH


def test_server_timeout_follows_the_amadeus_lesson():
    assert NAV2["bt_navigator"]["ros__parameters"]["default_server_timeout"] >= 1000
