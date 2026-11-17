#!/usr/bin/env python3
"""Startet nur den Kartiermodus-Manager. Er sendet keine Fahrbefehle."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    parameters = os.path.join(
        get_package_share_directory("homemy_mapping_mode"),
        "config",
        "homemy_mapping_mode.yaml",
    )
    return LaunchDescription(
        [
            Node(
                package="homemy_mapping_mode",
                executable="mapping_mode_manager",
                name="homemy_mapping_mode",
                output="screen",
                parameters=[parameters],
            )
        ]
    )
