"""Checks of the HomeMy robot model against the CAD geometry file."""

import math
import pathlib
import subprocess
import xml.etree.ElementTree as ET

import pytest
import yaml

PACKAGE = pathlib.Path(__file__).resolve().parents[1]
GEOMETRY = PACKAGE / "config" / "geometry.yaml"
MODEL = PACKAGE / "urdf" / "homemy.urdf.xacro"


def render(oak_tilt_deg="0.0"):
    out = subprocess.run(
        [
            "xacro",
            str(MODEL),
            f"geometry_file:={GEOMETRY}",
            f"oak_tilt_deg:={oak_tilt_deg}",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    return ET.fromstring(out.stdout)


def joint(root, name):
    for element in root.findall("joint"):
        if element.get("name") == name:
            return element
    raise AssertionError(f"joint {name} missing")


def xyz(element):
    origin = element.find("origin")
    return [float(v) for v in origin.get("xyz", "0 0 0").split()]


def rpy(element):
    origin = element.find("origin")
    return [float(v) for v in origin.get("rpy", "0 0 0").split()]


@pytest.fixture(scope="module")
def geometry():
    return yaml.safe_load(GEOMETRY.read_text())


@pytest.fixture(scope="module")
def model():
    return render()


def test_model_has_the_frames_navigation_needs(model):
    links = {link.get("name") for link in model.findall("link")}
    for name in [
        "base_link",
        "lidar_link",
        "imu_link",
        "left_wheel_link",
        "right_wheel_link",
        "oak_link",
        "oak_optical_frame",
    ]:
        assert name in links


def test_lidar_sits_in_the_slot(model, geometry):
    x, y, z = xyz(joint(model, "lidar_joint"))
    outline = geometry["base_outline"]
    assert outline["z_slot_bottom"] < z < outline["z_slot_top"]
    assert z == pytest.approx(0.1638)
    assert outline["x_min"] < x < outline["x_max"]
    # 40 mm behind the front wall, as in the LiDAR slot decision.
    assert outline["x_max"] - x == pytest.approx(0.040)
    assert y == 0.0


def test_drive_wheels_are_symmetric_on_the_axle(model, geometry):
    left = xyz(joint(model, "left_wheel_joint"))
    right = xyz(joint(model, "right_wheel_joint"))
    wheels = geometry["drive_wheels"]
    assert left[0] == right[0] == 0.0
    assert left[1] - right[1] == pytest.approx(wheels["separation"])
    assert left[2] == right[2] == pytest.approx(wheels["radius"])
    assert joint(model, "left_wheel_joint").get("type") == "continuous"


def test_axle_is_108_mm_behind_the_front_edge(geometry):
    # Software concept, section 11: no caster in front of the axle.
    assert geometry["base_outline"]["x_max"] == pytest.approx(0.1094)
    assert geometry["casters"]["x"] < 0.0


def test_parts_lie_inside_the_base_outline(model, geometry):
    outline = geometry["base_outline"]
    for name in ["left_caster_joint", "right_caster_joint", "imu_joint"]:
        x, y, _ = xyz(joint(model, name))
        assert outline["x_min"] < x < outline["x_max"]
        assert abs(y) < outline["y_half"]


def test_webs_lie_on_the_outline(geometry):
    outline = geometry["base_outline"]
    for name, (x0, x1, y0, y1) in geometry["slot_webs"].items():
        on_side = abs(abs(y0) - outline["y_half"]) < 1e-9 and y0 == y1
        on_front_or_rear = x0 == x1 and x0 in (outline["x_min"], outline["x_max"])
        assert on_side or on_front_or_rear, name


def test_oak_tilt_looks_down_for_positive_angles():
    tilted = render("25")
    pitch = rpy(joint(tilted, "oak_tilt_joint"))[1]
    assert pitch == pytest.approx(math.radians(25))
    # A positive pitch about +Y turns the camera's forward axis towards -Z.
    forward_z = -math.sin(pitch)
    assert forward_z < 0.0


def test_geometry_file_says_it_holds_cad_values():
    text = GEOMETRY.read_text()
    assert "not measurements" in text
