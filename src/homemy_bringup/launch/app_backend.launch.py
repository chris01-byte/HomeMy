#!/usr/bin/env python3
"""Robot side of the HomeMy app: map store, rooms, mapping mode, and bridge.

Starts no driver and sends no motion command. The bridge listens only on the
loopback interface unless ``bridge_address`` is set explicitly. It has no
authentication; open it only in a trusted laboratory network:

    ros2 launch homemy_bringup app_backend.launch.py bridge_address:=0.0.0.0
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue

# What the app may publish and subscribe to over the bridge. Everything else,
# in particular every velocity topic, is refused (contracts/api/app-bridge.md).
APP_PUBLISH_TOPICS = (
    "['/homemy/mapping_mode/command_json', "
    "'/homemy/map_manager/command_json', "
    "'/homemy/room_manager/command_json', "
    "'/homemy/mission/command_json']"
)
APP_SUBSCRIBE_TOPICS = (
    "['/homemy/mapping_mode/status_json', "
    "'/homemy/map_manager/status_json', "
    "'/homemy/room_manager/status_json', "
    "'/homemy/mission/status_json', "
    "'/map']"
)


def _config(package: str, name: str) -> str:
    return os.path.join(get_package_share_directory(package), "config", name)


def generate_launch_description():
    storage_root = LaunchConfiguration("storage_root")
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "bridge_address",
                default_value="127.0.0.1",
                description="Bind address of the app bridge. 0.0.0.0 opens it to the network.",
            ),
            DeclareLaunchArgument("bridge_port", default_value="9090"),
            DeclareLaunchArgument(
                "storage_root",
                default_value="~/.local/share/homemy",
                description="Folder for saved maps and rooms. Outside the repository.",
            ),
            DeclareLaunchArgument(
                "auto_end_timeout_s",
                default_value="300.0",
                description="Mapping mode ends after this many seconds without controller input.",
            ),
            Node(
                package="homemy_map_manager",
                executable="homemy_map_manager",
                name="homemy_map_manager",
                output="screen",
                parameters=[
                    _config("homemy_map_manager", "homemy_map_manager.yaml"),
                    {"storage_directory": [storage_root, "/maps"]},
                ],
            ),
            Node(
                package="homemy_room_manager",
                executable="homemy_room_manager",
                name="homemy_room_manager",
                output="screen",
                parameters=[
                    _config("homemy_room_manager", "homemy_room_manager.yaml"),
                    {"storage_directory": [storage_root, "/room_maps"]},
                ],
            ),
            Node(
                package="homemy_mapping_mode",
                executable="mapping_mode_manager",
                name="homemy_mapping_mode",
                output="screen",
                parameters=[
                    _config("homemy_mapping_mode", "homemy_mapping_mode.yaml"),
                    {
                        "auto_end_timeout_s": ParameterValue(
                            LaunchConfiguration("auto_end_timeout_s"), value_type=float
                        )
                    },
                ],
            ),
            Node(
                package="rosbridge_server",
                executable="rosbridge_websocket",
                name="homemy_app_bridge",
                output="screen",
                parameters=[
                    {
                        "address": LaunchConfiguration("bridge_address"),
                        "port": ParameterValue(LaunchConfiguration("bridge_port"), value_type=int),
                        "topics_pub_glob": APP_PUBLISH_TOPICS,
                        "topics_sub_glob": APP_SUBSCRIBE_TOPICS,
                        "services_glob": "[]",
                        "actions_glob": "[]",
                    }
                ],
            ),
        ]
    )
