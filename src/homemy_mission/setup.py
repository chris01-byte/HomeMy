from glob import glob

from setuptools import setup


package_name = "homemy_mission"

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
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    extras_require={"test": ["pytest"]},
    zip_safe=True,
    maintainer="HomeMy",
    maintainer_email="homemy@example.com",
    description="HomeMy missions: drive to a room on command from the app.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "mission_manager = homemy_mission.mission_node:main",
        ],
    },
)
