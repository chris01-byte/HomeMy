from glob import glob

from setuptools import setup


package_name = "homemy_state_estimation"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        ("share/" + package_name, ["package.xml", "README.md"]),
        ("share/" + package_name + "/config", glob("config/*.yaml") + glob("config/*.example")),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    extras_require={"test": ["pytest"]},
    zip_safe=True,
    maintainer="HomeMy",
    maintainer_email="homemy@example.com",
    description="HWT601 IMU reader (read-only) and yaw-rate aid for the odometry of HomeMy.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "hwt601_imu = homemy_state_estimation.hwt601_imu_node:main",
            "yaw_rate = homemy_state_estimation.yaw_rate_node:main",
        ],
    },
)
