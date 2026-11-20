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
            DeclareLaunchArgument("scan_mask_params_file", default_value=params),
            DeclareLaunchArgument(
                "scan_mask_overlay_params_file",
                default_value=params,
                description="Optional second parameter file laid over the first one: the robot's local values.",
            ),
            Node(
                package="homemy_lidar_bringup",
                executable="scan_mask",
                name="scan_mask",
                parameters=[
                    LaunchConfiguration("scan_mask_params_file"),
                    LaunchConfiguration("scan_mask_overlay_params_file"),
                ],
            ),
        ]
    )
