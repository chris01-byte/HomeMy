from glob import glob

from setuptools import setup


package_name = "homemy_manual_drive"

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
        ("share/" + package_name + "/config", glob("config/*.yaml")),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    extras_require={"test": ["pytest"]},
    zip_safe=True,
    maintainer="HomeMy",
    maintainer_email="homemy@example.com",
    description="Manual driving with the wireless controller: radio-link watchdog and teleop profile.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "controller_link = homemy_manual_drive.controller_link_node:main",
        ],
    },
)
