"""Start the HomeMy drive driver.

With the default parameter file the driver is non-moving: it only computes
and sends nothing to the motors.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    params = PathJoinSubstitution([FindPackageShare("homemy_drivebase"), "config", "homemy_drivebase.yaml"])
    return LaunchDescription(
        [
            DeclareLaunchArgument("drivebase_params_file", default_value=params),
            Node(
                package="homemy_drivebase",
                executable="drivebase",
                name="drivebase",
                output="screen",
                parameters=[LaunchConfiguration("drivebase_params_file")],
            ),
        ]
    )
