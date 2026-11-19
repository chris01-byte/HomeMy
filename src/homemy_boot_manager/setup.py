from glob import glob

from setuptools import setup


package_name = "homemy_boot_manager"

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
    description="Lifecycle state of HomeMy; until the PMU exists, a bridge with fixed values.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "lifecycle_bridge = homemy_boot_manager.lifecycle_bridge_node:main",
        ],
    },
)
