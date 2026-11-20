"""The simulation's parameter files must agree with each other."""

import pathlib

import yaml

CONFIG = pathlib.Path(__file__).resolve().parents[1] / "config"


def parameters(name, node):
    return yaml.safe_load((CONFIG / name).read_text())[node]["ros__parameters"]


def test_simulated_local_values_match_the_simulated_devices():
    local = "sim_robot_local.yaml"
    drive = parameters("sim_drivebase.yaml", "drivebase")
    for key, value in parameters(local, "drivebase").items():
        assert drive[key] == value, key
    assert set(drive) - set(parameters(local, "drivebase")) == {"publish_tf"}  # set by the launch file

    device = parameters("sim_lidar.yaml", "homemy_sim_base")
    assert parameters(local, "scan_normalize") == parameters("sim_lidar.yaml", "scan_normalize")
    assert parameters(local, "scan_normalize")["yaw_offset_deg"] == device["lidar_device_yaw_deg"]

    assert parameters(local, "yaw_rate") == parameters("sim_imu.yaml", "yaw_rate")


def test_every_simulation_file_says_that_it_is_simulation_only():
    for path in CONFIG.glob("sim_*.yaml"):
        assert path.read_text().startswith("# NUR SIMULATION"), path.name
