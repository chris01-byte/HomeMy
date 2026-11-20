#!/usr/bin/env python3
"""The LiDAR chain alone, with the unchanged vendor driver, against a simulated STL-27L.

The test stand sends the device's own serial packets through a pseudo-
terminal. The vendor driver ldlidar_stl_ros2 reads them as it would read the
real device; scan normalisation and blind-sector mask follow. Nothing drives.

Needs the vendor driver built and sourced (see
homemy_lidar_bringup/vendor/ldlidar_stl_ros2.repos).

    ros2 launch homemy_bringup lidar_sim.launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def share(package, *parts):
    return os.path.join(get_package_share_directory(package), *parts)


def generate_launch_description():
    port = ["/tmp/homemy_sim_lidar_", LaunchConfiguration("sim_id")]
    lidar_config = share("homemy_lidar_bringup", "config", "stl27l.yaml")
    sim_config = share("homemy_simulation", "config", "sim_lidar.yaml")
    return LaunchDescription(
        [
            DeclareLaunchArgument("sim_id", default_value="0"),
            DeclareLaunchArgument(
                "confirmed",
                default_value="true",
                description="false keeps the delivered lock: the scan goes only to /scan_unconfirmed.",
            ),
            DeclareLaunchArgument(
                "world_file", default_value=share("homemy_simulation", "worlds", "testwohnung.json")
            ),
            Node(
                package="homemy_simulation",
                executable="sim_base",
                name="homemy_sim_base",
                output="screen",
                parameters=[
                    sim_config,
                    {
                        "world_file": LaunchConfiguration("world_file"),
                        "geometry_file": share("homemy_description", "config", "geometry.yaml"),
                        "lidar_interface": "serial",
                        "lidar_port_link": port,
                    },
                ],
            ),
            # The unchanged vendor driver with HomeMy's delivered configuration.
            Node(
                package="ldlidar_stl_ros2",
                executable="ldlidar_stl_ros2_node",
                name="homemy_stl27l",
                output="screen",
                parameters=[lidar_config, {"port_name": port}],
                # The driver gives up if the device is not there yet; start it again.
                respawn=True,
                respawn_delay=2.0,
            ),
            Node(
                package="homemy_lidar_bringup",
                executable="scan_normalize",
                name="scan_normalize",
                output="screen",
                parameters=[
                    lidar_config,
                    sim_config,
                    {"alignment_confirmed": ParameterValue(LaunchConfiguration("confirmed"), value_type=bool)},
                ],
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(share("homemy_lidar_bringup", "launch", "scan_mask.launch.py"))
            ),
        ]
    )
