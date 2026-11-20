#!/usr/bin/env python3
"""Only the drive driver against the simulated motors. Simulation only.

For tests of the driver's behaviour on its own, without the rest of the
stack: /cmd_vel is published by the test itself.

    ros2 launch homemy_bringup drivebase_sim.launch.py unlocked:=true

With unlocked:=false the driver runs with its delivered, non-moving
configuration.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition, UnlessCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def share(package, *parts):
    return os.path.join(get_package_share_directory(package), *parts)


def generate_launch_description():
    port = ["/tmp/homemy_sim_drive_", LaunchConfiguration("sim_id")]
    unlocked = LaunchConfiguration("unlocked")
    delivered = share("homemy_drivebase", "config", "homemy_drivebase.yaml")
    return LaunchDescription(
        [
            DeclareLaunchArgument("sim_id", default_value="driver_only"),
            DeclareLaunchArgument(
                "unlocked",
                default_value="false",
                description="true: unlock the driver against the simulated motors.",
            ),
            Node(
                package="homemy_simulation",
                executable="sim_base",
                name="homemy_sim_base",
                output="screen",
                parameters=[
                    {
                        "world_file": share("homemy_simulation", "worlds", "testwohnung.json"),
                        "geometry_file": share("homemy_description", "config", "geometry.yaml"),
                        "drive_interface": "modbus",
                        "modbus_port_link": port,
                    }
                ],
            ),
            Node(
                package="homemy_drivebase",
                executable="drivebase",
                name="drivebase",
                output="screen",
                condition=IfCondition(unlocked),
                parameters=[delivered, share("homemy_simulation", "config", "sim_drivebase.yaml"), {"rs485_port": port}],
            ),
            Node(
                package="homemy_drivebase",
                executable="drivebase",
                name="drivebase",
                output="screen",
                condition=UnlessCondition(unlocked),
                parameters=[delivered, {"rs485_port": port}],
            ),
        ]
    )
