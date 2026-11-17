#!/usr/bin/env python3
"""Startet nur den semantischen Kartenmanager; keinerlei Aktoren/Nav2."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    package_share = get_package_share_directory("homemy_room_manager")
    parameters = os.path.join(
        package_share,
        "config",
        "homemy_room_manager.yaml",
    )
    return LaunchDescription(
        [
            Node(
                package="homemy_room_manager",
                executable="homemy_room_manager",
                name="homemy_room_manager",
                output="screen",
                parameters=[parameters],
            )
        ]
    )
