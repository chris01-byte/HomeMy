from glob import glob

from setuptools import setup


package_name = "homemy_lidar_bringup"

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
        ("share/" + package_name + "/vendor", glob("vendor/*")),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    extras_require={"test": ["pytest"]},
    zip_safe=True,
    maintainer="HomeMy",
    maintainer_email="homemy@example.com",
    description="STL-27L: driver configuration, scan normalisation, blind-sector mask, check tool.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "scan_mask = homemy_lidar_bringup.scan_mask_node:main",
            "scan_normalize = homemy_lidar_bringup.scan_normalize_node:main",
            "lidar_check = homemy_lidar_bringup.lidar_check:main",
        ],
    },
)
