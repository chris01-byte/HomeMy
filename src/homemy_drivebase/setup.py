from glob import glob

from setuptools import setup


package_name = "homemy_drivebase"

setup(
    name=package_name,
    version="0.1.0",
    packages=[package_name],
    data_files=[
        (
            "share/ament_index/resource_index/packages",
            ["resource/" + package_name],
        ),
        ("share/" + package_name, ["package.xml", "README.md", "requirements-modbus.txt"]),
        ("share/" + package_name + "/config", glob("config/*.yaml") + glob("config/*.example")),
        ("share/" + package_name + "/launch", glob("launch/*.launch.py")),
    ],
    install_requires=["setuptools"],
    extras_require={"test": ["pytest"]},
    zip_safe=True,
    maintainer="HomeMy",
    maintainer_email="homemy@example.com",
    description="ESS23-RS differential drive of HomeMy over RS485 (Modbus RTU). Non-moving by default.",
    license="MIT",
    entry_points={
        "console_scripts": [
            "drivebase = homemy_drivebase.drivebase_node:main",
            "ess23_readonly_check = homemy_drivebase.ess23_readonly_check:main",
        ],
    },
)
