"""Tests of the fixed angle grid (no ROS).

The first group follows Amadeus ``test_scan_gitter.py`` (Roboter_ws 05439c7);
the rest covers HomeMy's robot-aligned output grid and yaw offset.
"""

import math
import pathlib

import numpy as np
import pytest
import yaml

from homemy_lidar_bringup.scan_grid import FULL_TURN, grid_angles, grid_indices, to_grid

PACKAGE = pathlib.Path(__file__).resolve().parents[1]
BEAMS = 2160


def driver_increment(count):
    """The vendor driver: (N - 1) * increment is exactly 360 degrees."""

    return FULL_TURN / (count - 1)


def angle_error(a, b):
    return np.abs((a - b + math.pi) % FULL_TURN - math.pi)


@pytest.mark.parametrize("count_in", [2146, 2159, 2160, 2172, 2176])
def test_every_output_beam_gets_the_nearest_input_beam(count_in):
    increment = driver_increment(count_in)
    index, valid = grid_indices(count_in, 0.0, increment, BEAMS)
    assert valid.all()
    assert index.min() >= 0 and index.max() < count_in
    error = angle_error(grid_angles(BEAMS), index * increment)
    assert float(error.max()) <= increment / 2.0 + 1e-9


def test_output_grid_is_fixed_and_has_no_duplicate_direction():
    angles = grid_angles(BEAMS)
    assert len(angles) == BEAMS
    assert angles[0] == pytest.approx(-math.pi)
    assert angles[-1] + FULL_TURN / BEAMS == pytest.approx(math.pi)


def test_no_interpolation_only_existing_values():
    count_in = 2176
    values = np.arange(count_in, dtype=np.float32)
    index, valid = grid_indices(count_in, 0.0, driver_increment(count_in), BEAMS)
    assert np.all(np.isin(to_grid(values, index, valid), values))


def test_nan_from_the_driver_never_becomes_a_measurement():
    count_in = 2172
    values = np.full(count_in, 2.5, dtype=np.float32)
    degrees_per_beam = 360.0 / (count_in - 1)
    values[int(236.0 / degrees_per_beam): int(304.0 / degrees_per_beam) + 1] = np.nan
    index, valid = grid_indices(count_in, 0.0, driver_increment(count_in), BEAMS)
    out = to_grid(values, index, valid)
    assert float(np.isnan(out).mean()) == pytest.approx(float(np.isnan(values).mean()), abs=0.005)
    # The device's 236..304 degrees are -124..-56 degrees on the output grid.
    blind = np.degrees(grid_angles(BEAMS)[np.isnan(out)])
    assert blind.min() == pytest.approx(-124.0, abs=0.3)
    assert blind.max() == pytest.approx(-56.0, abs=0.3)


@pytest.mark.parametrize("yaw_deg", [0.0, 90.0, -90.0, 37.04, 180.0])
def test_yaw_offset_turns_the_scan_into_the_robot_frame(yaw_deg):
    """An object at device bearing b appears at robot bearing b + yaw."""

    count_in = 2163
    increment = driver_increment(count_in)
    device_bearing = math.radians(20.0)
    values = np.full(count_in, 5.0, dtype=np.float32)
    values[int(round(device_bearing / increment))] = 1.0
    index, valid = grid_indices(count_in, 0.0, increment, BEAMS, math.radians(yaw_deg))
    out = to_grid(values, index, valid)
    seen = grid_angles(BEAMS)[int(np.argmin(out))]
    assert math.degrees(float(angle_error(seen, device_bearing + math.radians(yaw_deg)))) < 0.2


def test_counter_clockwise_stays_counter_clockwise():
    """Rising input index means rising output angle: the rotation sense is kept."""

    count_in = 2150
    values = np.arange(count_in, dtype=np.float32)
    index, valid = grid_indices(count_in, 0.0, driver_increment(count_in), BEAMS, math.radians(90.0))
    out = to_grid(values, index, valid)
    steps = np.diff(out)
    assert (steps >= 0).sum() >= BEAMS - 2  # one wrap at the seam


def test_scan_without_duplicate_direction_wraps_to_its_first_beam():
    """The test stand's simple scan: N beams from -pi, N * increment = 360 degrees."""

    count_in = 720
    increment = FULL_TURN / count_in
    index, valid = grid_indices(count_in, -math.pi, increment, BEAMS)
    assert valid.all()
    assert index.min() == 0 and index.max() == count_in - 1
    error = angle_error(grid_angles(BEAMS), -math.pi + index * increment)
    assert float(error.max()) <= increment / 2.0 + 1e-9


def test_partial_scan_leaves_the_rest_invalid():
    count_in = 181  # 0..180 degrees in 1 degree steps
    index, valid = grid_indices(count_in, 0.0, math.radians(1.0), BEAMS)
    out = to_grid(np.full(count_in, 2.0, dtype=np.float32), index, valid)
    degrees = np.degrees(grid_angles(BEAMS))
    assert np.isnan(out[(degrees < -1.0) & (degrees > -179.0)]).all()
    assert np.isfinite(out[(degrees > 1.0) & (degrees < 179.0)]).all()


def test_same_input_layout_gives_the_same_mapping():
    a = grid_indices(2160, 0.0, driver_increment(2160), BEAMS)
    b = grid_indices(2160, 0.0, driver_increment(2160), BEAMS)
    np.testing.assert_array_equal(a[0], b[0])


@pytest.mark.parametrize(
    "arguments",
    [
        (0, 0.0, 0.001, BEAMS),
        (1, 0.0, 0.001, BEAMS),
        (2160, 0.0, 0.0, BEAMS),
        (2160, 0.0, -0.003, BEAMS),
        (2160, 0.0, float("nan"), BEAMS),
        (2160, float("inf"), 0.003, BEAMS),
        (2160, 0.0, 0.003, 1),
    ],
)
def test_unusable_input_is_rejected(arguments):
    with pytest.raises(ValueError):
        grid_indices(*arguments)


def test_empty_values_give_only_fill():
    index, valid = grid_indices(100, 0.0, driver_increment(100), 50)
    assert np.isnan(to_grid([], index, valid)).all()


def test_delivered_configuration_is_locked_and_unmeasured():
    config = yaml.safe_load((PACKAGE / "config" / "stl27l.yaml").read_text())
    driver = config["homemy_stl27l"]["ros__parameters"]
    normalize = config["scan_normalize"]["ros__parameters"]
    assert normalize["alignment_confirmed"] is False
    assert normalize["yaw_offset_deg"] == 0.0
    assert normalize["beams"] == BEAMS
    assert normalize["input_topic"] == "/" + driver["topic_name"]
    assert normalize["output_frame"] == "lidar_link"
    # The raw scan must not be placed in space by the robot model.
    assert driver["frame_id"] != "lidar_link"
    assert driver["port_name"] == "/dev/homemy_lidar"
    assert "ttyUSB" not in (PACKAGE / "launch" / "stl27l.launch.py").read_text().replace("never /dev/ttyUSB0", "")
    assert driver["enable_angle_crop_func"] is False
    assert driver["laser_scan_dir"] is True


def test_vendor_driver_is_pinned_to_a_full_commit():
    repos = yaml.safe_load((PACKAGE / "vendor" / "ldlidar_stl_ros2.repos").read_text())
    version = repos["repositories"]["ldlidar_stl_ros2"]["version"]
    assert len(version) == 40 and all(c in "0123456789abcdef" for c in version)
