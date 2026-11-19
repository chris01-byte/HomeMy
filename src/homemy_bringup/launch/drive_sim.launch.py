#!/usr/bin/env python3
"""Stage S2 in simulation: HomeMy drives in the test stand.

The test stand replaces only the devices (drive, LiDAR, odometry, IMU) and
the person with the controller. Everything else is the real HomeMy code:
robot model, blind-sector mask, motion gate with obstacle protection, the
controller profile (teleop_twist_joy), mapping mode, slam_toolbox, the map
store, the room overlay, and the app bridge.

    ros2 launch homemy_bringup drive_sim.launch.py
    ros2 launch homemy_bringup drive_sim.launch.py operator_route:=true

Then connect the app to ws://127.0.0.1:9090/ and switch on mapping mode.
With operator_route:=true the simulated person drives the mapping route of
the test apartment as soon as mapping mode is on.
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
    geometry = share("homemy_description", "config", "geometry.yaml")
    world = LaunchConfiguration("world_file")
    return LaunchDescription(
        [
            DeclareLaunchArgument("bridge_address", default_value="127.0.0.1"),
            DeclareLaunchArgument("bridge_port", default_value="9090"),
            DeclareLaunchArgument("storage_root", default_value="~/.local/share/homemy-sim"),
            DeclareLaunchArgument("auto_end_timeout_s", default_value="300.0"),
            DeclareLaunchArgument(
                "world_file", default_value=share("homemy_simulation", "worlds", "testwohnung.json")
            ),
            DeclareLaunchArgument(
                "operator_route",
                default_value="false",
                description="The simulated person drives the mapping route of the world file.",
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(share("homemy_bringup", "launch", "app_backend.launch.py")),
                launch_arguments={
                    "bridge_address": LaunchConfiguration("bridge_address"),
                    "bridge_port": LaunchConfiguration("bridge_port"),
                    "storage_root": LaunchConfiguration("storage_root"),
                    "auto_end_timeout_s": LaunchConfiguration("auto_end_timeout_s"),
                }.items(),
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(share("homemy_description", "launch", "description.launch.py"))
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(share("homemy_lidar_bringup", "launch", "scan_mask.launch.py"))
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(share("homemy_motion_gate", "launch", "motion_gate.launch.py"))
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(share("homemy_navigation", "launch", "slam.launch.py"))
            ),
            Node(
                package="homemy_mapping_mode",
                executable="mapping_run_coordinator",
                name="mapping_run_coordinator",
                output="screen",
            ),
            # The real teleop profile; only joy_node and the radio-link
            # watchdog are replaced by the simulated controller.
            Node(
                package="teleop_twist_joy",
                executable="teleop_node",
                name="teleop_twist_joy_node",
                parameters=[share("homemy_manual_drive", "config", "manual_drive.yaml")],
                remappings=[("/cmd_vel", "/homemy/cmd_vel/teleop"), ("cmd_vel", "/homemy/cmd_vel/teleop")],
            ),
            Node(
                package="homemy_simulation",
                executable="sim_base",
                name="homemy_sim_base",
                output="screen",
                parameters=[{"world_file": world, "geometry_file": geometry}],
            ),
            Node(
                package="homemy_simulation",
                executable="sim_controller",
                name="homemy_sim_controller",
                output="screen",
                parameters=[
                    {
                        "world_file": world,
                        "follow_route": ParameterValue(LaunchConfiguration("operator_route"), value_type=bool),
                        # Without a route the simulated controller is connected but idle.
                        "driving": ParameterValue(LaunchConfiguration("operator_route"), value_type=bool),
                    }
                ],
            ),
            Node(
                package="homemy_simulation",
                executable="lifecycle_stub",
                name="homemy_lifecycle_stub",
                output="screen",
            ),
        ]
    )
