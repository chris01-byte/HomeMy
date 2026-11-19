"""Start the blind-sector mask for the STL-27L scan."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    params = PathJoinSubstitution([FindPackageShare("homemy_lidar_bringup"), "config", "scan_mask.yaml"])
    return LaunchDescription(
        [
            DeclareLaunchArgument("params_file", default_value=params),
            Node(
                package="homemy_lidar_bringup",
                executable="scan_mask",
                name="scan_mask",
                parameters=[LaunchConfiguration("params_file")],
            ),
        ]
    )
