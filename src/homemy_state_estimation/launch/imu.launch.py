"""Start the HWT601 reader and the yaw-rate aid; optionally the fused odometry.

Default (use_imu_fusion:=false): the gyro is only read and compared with the
wheels (shadow mode). The drive driver keeps /odom and odom -> base_link.

use_imu_fusion:=true: an EKF publishes /odom and odom -> base_link from wheel
speed and gyro yaw rate. The drive driver must then publish /wheel/odom and no
transform (see homemy_bringup).
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution, PythonExpression
from launch_ros.actions import Node
from launch_ros.substitutions import FindPackageShare


def generate_launch_description():
    share = FindPackageShare("homemy_state_estimation")
    params_file = LaunchConfiguration("imu_params_file")
    fusion = LaunchConfiguration("use_imu_fusion")
    wheel_topic = PythonExpression(["'/wheel/odom' if '", fusion, "'.lower() == 'true' else '/odom'"])
    return LaunchDescription(
        [
            DeclareLaunchArgument(
                "imu_params_file", default_value=PathJoinSubstitution([share, "config", "hwt601.yaml"])),
            DeclareLaunchArgument(
                "imu_ekf_params_file", default_value=PathJoinSubstitution([share, "config", "ekf_yaw_rate.yaml"])),
            DeclareLaunchArgument(
                "imu_overlay_params_file", default_value=PathJoinSubstitution([share, "config", "hwt601.yaml"]),
                description="Optional second parameter file laid over the first one: the robot's local values."),
            DeclareLaunchArgument(
                "imu_port", default_value="/dev/homemy_imu",
                description="Serial device of the IMU's own RS485 adapter; the stable udev alias."),
            DeclareLaunchArgument(
                "use_imu_fusion", default_value="false",
                description="true: the odometry uses the gyro's yaw rate. Only after steps I2 to I4."),
            DeclareLaunchArgument(
                "start_imu_reader", default_value="true",
                description="false starts only the yaw-rate aid, for replayed or simulated raw data."),
            Node(
                package="homemy_state_estimation",
                executable="hwt601_imu",
                name="hwt601_imu",
                output="screen",
                parameters=[
                    params_file,
                    LaunchConfiguration("imu_overlay_params_file"),
                    {"port": LaunchConfiguration("imu_port")},
                ],
                condition=IfCondition(LaunchConfiguration("start_imu_reader")),
            ),
            Node(
                package="homemy_state_estimation",
                executable="yaw_rate",
                name="yaw_rate",
                output="screen",
                parameters=[params_file, LaunchConfiguration("imu_overlay_params_file"), {"wheel_odom_topic": wheel_topic}],
            ),
            Node(
                package="robot_localization",
                executable="ekf_node",
                name="odometry_ekf",
                output="screen",
                parameters=[LaunchConfiguration("imu_ekf_params_file")],
                remappings=[("odometry/filtered", "/odom")],
                condition=IfCondition(fusion),
            ),
        ]
    )
