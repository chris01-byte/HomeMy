"""Launch arguments are global across included launch files.

Two included files that declare the same argument name share one value: the
first declaration wins, and the second file silently gets the wrong
parameters. This happened once with "params_file" (motion gate and Nav2
received the LiDAR mask's file). Every HomeMy launch file therefore uses
argument names that no other HomeMy launch file declares, except for the
shared names listed below that mean the same thing everywhere.
"""

import pathlib
import re
from collections import defaultdict

SRC = pathlib.Path(__file__).resolve().parents[2]
SHARED = {
    "bridge_address", "bridge_port", "storage_root", "auto_end_timeout_s",
    "use_sim_time", "oak_tilt_deg", "world_file", "sim_id",
    # One decision for the whole composition: the drive driver and the IMU
    # launch must agree on who owns /odom.
    "use_imu_fusion",
}


def test_no_two_launch_files_declare_the_same_argument():
    declared = defaultdict(set)
    for path in SRC.glob("homemy_*/launch/*.launch.py"):
        for name in re.findall(r'DeclareLaunchArgument\(\s*"([^"]+)"', path.read_text()):
            declared[name].add(path.relative_to(SRC).as_posix())
    clashes = {name: sorted(files) for name, files in declared.items() if len(files) > 1 and name not in SHARED}
    assert clashes == {}
