"""Controller driving on the real robot: joystick driver, teleop, radio-link watchdog.

The teleop output goes to the motion gate (/homemy/cmd_vel/teleop), never to
the drive. Without mapping mode, a fresh radio link, and the other gate
conditions, nothing moves. Not used in simulation (see homemy_simulation).
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    params = PathJoinSubstitution([FindPackageShare("homemy_manual_drive"), "config", "manual_drive.yaml"])
    params_file = LaunchConfiguration("params_file")
    return LaunchDescription(
        [
            DeclareLaunchArgument("params_file", default_value=params),
            Node(package="joy", executable="joy_node", name="joy_node", parameters=[params_file]),
            Node(
                package="teleop_twist_joy",
                executable="teleop_node",
                name="teleop_twist_joy_node",
                parameters=[params_file],
                remappings=[("/cmd_vel", "/homemy/cmd_vel/teleop"), ("cmd_vel", "/homemy/cmd_vel/teleop")],
            ),
            Node(
                package="homemy_manual_drive",
                executable="controller_link",
                name="controller_link",
                parameters=[params_file],
            ),
        ]
    )
