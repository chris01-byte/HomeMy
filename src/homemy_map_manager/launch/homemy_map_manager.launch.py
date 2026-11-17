#!/usr/bin/env python3
"""Startet den produktiven Kartenmanager mit seiner Standardkonfiguration."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory("homemy_map_manager")
    parameters = os.path.join(package_share, "config", "homemy_map_manager.yaml")

    return LaunchDescription(
        [
            Node(
                package="homemy_map_manager",
                executable="homemy_map_manager",
                name="homemy_map_manager",
                output="screen",
                parameters=[parameters],
            )
        ]
    )
