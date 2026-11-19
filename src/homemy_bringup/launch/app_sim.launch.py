#!/usr/bin/env python3
"""The robot side of the app in simulation, without any hardware.

Adds stand-ins for SLAM and the controller, and the lifecycle bridge. Maps and
rooms are stored in a separate simulation folder by default.

    ros2 launch homemy_bringup app_sim.launch.py

Then connect the app, for example from the iOS simulator, to ws://127.0.0.1:9090/.
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    backend = os.path.join(
        get_package_share_directory("homemy_bringup"), "launch", "app_backend.launch.py"
    )
    return LaunchDescription(
        [
            DeclareLaunchArgument("bridge_address", default_value="127.0.0.1"),
            DeclareLaunchArgument("bridge_port", default_value="9090"),
            DeclareLaunchArgument("storage_root", default_value="~/.local/share/homemy-sim"),
            DeclareLaunchArgument("auto_end_timeout_s", default_value="300.0"),
            DeclareLaunchArgument(
                "controller_driving",
                default_value="true",
                description="Whether the simulated controller reports driving input.",
            ),
            DeclareLaunchArgument(
                "initial_map",
                default_value="false",
                description="Publish a complete map at start instead of waiting for a mapping run.",
            ),
            IncludeLaunchDescription(
                PythonLaunchDescriptionSource(backend),
                launch_arguments={
                    "bridge_address": LaunchConfiguration("bridge_address"),
                    "bridge_port": LaunchConfiguration("bridge_port"),
                    "storage_root": LaunchConfiguration("storage_root"),
                    "auto_end_timeout_s": LaunchConfiguration("auto_end_timeout_s"),
                }.items(),
            ),
            Node(
                package="homemy_simulation",
                executable="synthetic_map",
                name="homemy_synthetic_map",
                output="screen",
                parameters=[
                    {
                        "initial_map": ParameterValue(
                            LaunchConfiguration("initial_map"), value_type=bool
                        )
                    }
                ],
            ),
            Node(
                package="homemy_simulation",
                executable="sim_controller",
                name="homemy_sim_controller",
                output="screen",
                parameters=[
                    {
                        "driving": ParameterValue(
                            LaunchConfiguration("controller_driving"), value_type=bool
                        )
                    }
                ],
            ),
            # The lifecycle state and the emergency-stop signal are bridged with
            # fixed values while the PMU does not exist (homemy_boot_manager).
            Node(
                package="homemy_boot_manager",
                executable="lifecycle_bridge",
                name="lifecycle_bridge",
                output="screen",
            ),
            # The map manager reports the robot pose from map -> base_link.
            Node(
                package="tf2_ros",
                executable="static_transform_publisher",
                name="homemy_sim_robot_pose",
                output="screen",
                arguments=["--frame-id", "map", "--child-frame-id", "base_link"],
            ),
        ]
    )
