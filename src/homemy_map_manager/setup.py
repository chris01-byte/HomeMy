from glob import glob
import os

from setuptools import setup


package_name = "homemy_map_manager"

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
        (
            os.path.join("share", package_name, "launch"),
            glob("launch/*.launch.py"),
        ),
        (
            os.path.join("share", package_name, "config"),
            glob("config/*.yaml"),
        ),
    ],
    install_requires=["setuptools"],
    extras_require={"test": ["pytest"]},
    zip_safe=True,
    maintainer="HomeMy",
    maintainer_email="homemy@example.com",
    description=(
        "Robuste OccupancyGrid-Aufnahme, atomare Kartenablage und "
        "map->base_link-Pose fuer HomeMy."
    ),
    license="MIT",
    entry_points={
        "console_scripts": [
            "homemy_map_manager = "
            "homemy_map_manager.homemy_map_manager_node:main",
        ],
    },
)
