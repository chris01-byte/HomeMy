"""Start the STL-27L: vendor driver and scan normalisation.

Sensor only. As delivered, the normalised scan goes to /scan_unconfirmed
and nothing on /scan (see config/stl27l.yaml), so no consumer uses it.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    params = PathJoinSubstitution([FindPackageShare("homemy_lidar_bringup"), "config", "stl27l.yaml"])
    params_file = LaunchConfiguration("lidar_params_file")
    overlay = LaunchConfiguration("lidar_overlay_params_file")
    return LaunchDescription(
        [
            DeclareLaunchArgument("lidar_params_file", default_value=params),
            DeclareLaunchArgument(
                "lidar_overlay_params_file",
                default_value=params,
                description="Optional second parameter file laid over the first one: the robot's local values.",
            ),
            DeclareLaunchArgument(
                "lidar_port",
                default_value="/dev/homemy_lidar",
                description="Serial device of the LiDAR; the stable udev alias, never /dev/ttyUSB0.",
            ),
            DeclareLaunchArgument(
                "start_lidar_driver",
                default_value="true",
                description="false starts only the normalisation, for replayed or simulated raw scans.",
            ),
            Node(
                package="ldlidar_stl_ros2",
                executable="ldlidar_stl_ros2_node",
                name="homemy_stl27l",
                output="screen",
                parameters=[params_file, overlay, {"port_name": LaunchConfiguration("lidar_port")}],
                condition=IfCondition(LaunchConfiguration("start_lidar_driver")),
                # The driver ends itself if the device is missing at start;
                # start it again, so that a LiDAR plugged in late is found.
                respawn=True,
                respawn_delay=3.0,
            ),
            Node(
                package="homemy_lidar_bringup",
                executable="scan_normalize",
                name="scan_normalize",
                output="screen",
                parameters=[params_file, overlay],
            ),
        ]
    )
