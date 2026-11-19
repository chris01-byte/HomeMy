from glob import glob
import os

from setuptools import setup


package_name = "homemy_mapping_mode"

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
        (os.path.join("share", package_name, "launch"), glob("launch/*.launch.py")),
        (os.path.join("share", package_name, "config"), glob("config/*.yaml")),
    ],
    install_requires=["setuptools"],
    extras_require={"test": ["pytest"]},
    zip_safe=True,
    maintainer="HomeMy",
    maintainer_email="homemy@example.com",
    description="Mapping-mode manager for HomeMy (contracts/api/app-bridge.md).",
    license="MIT",
    entry_points={
        "console_scripts": [
            "mapping_mode_manager = homemy_mapping_mode.mapping_mode_node:main",
            "mapping_run_coordinator = homemy_mapping_mode.mapping_run_node:main",
        ],
    },
)
