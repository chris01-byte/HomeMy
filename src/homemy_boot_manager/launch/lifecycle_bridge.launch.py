"""Start the lifecycle bridge (fixed robot state while the PMU does not exist)."""

from launch import LaunchDescription
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription(
        [
            Node(
                package="homemy_boot_manager",
                executable="lifecycle_bridge",
                name="lifecycle_bridge",
                output="screen",
            ),
        ]
    )
