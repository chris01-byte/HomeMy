"""Start the motion gate with the robot outline from homemy_description."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    params = PathJoinSubstitution([FindPackageShare("homemy_motion_gate"), "config", "motion_gate.yaml"])
    geometry = PathJoinSubstitution([FindPackageShare("homemy_description"), "config", "geometry.yaml"])
    return LaunchDescription(
        [
            DeclareLaunchArgument("params_file", default_value=params),
            Node(
                package="homemy_motion_gate",
                executable="motion_gate",
                name="motion_gate",
                parameters=[LaunchConfiguration("params_file"), {"geometry_file": geometry}],
                output="screen",
            ),
        ]
    )
