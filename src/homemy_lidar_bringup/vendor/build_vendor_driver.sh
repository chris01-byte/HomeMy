#!/usr/bin/env bash
# Fetches the pinned vendor driver for the STL-27L and builds it in its own
# workspace. The driver's source is not changed.
#
#   source /opt/ros/jazzy/setup.bash
#   src/homemy_lidar_bringup/vendor/build_vendor_driver.sh [workspace]
#   source <workspace>/install/setup.bash
#
# Default workspace: ~/homemy_lidar_ws
set -euo pipefail

here="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
workspace="${1:-$HOME/homemy_lidar_ws}"
repos="$here/ldlidar_stl_ros2.repos"

url="$(sed -n 's/^ *url: *//p' "$repos")"
version="$(sed -n 's/^ *version: *//p' "$repos")"
if [[ -z "$url" || ! "$version" =~ ^[0-9a-f]{40}$ ]]; then
  echo "Cannot read url and pinned commit from $repos" >&2
  exit 1
fi

source_dir="$workspace/src/ldlidar_stl_ros2"
mkdir -p "$source_dir"
cd "$source_dir"
if [[ ! -d .git ]]; then
  git init -q
fi
git fetch -q --depth 1 "$url" "$version"
git checkout -q --detach FETCH_HEAD
if [[ "$(git rev-parse HEAD)" != "$version" ]]; then
  echo "Fetched commit is not the pinned one." >&2
  exit 1
fi

cd "$workspace"
# The driver's logger uses pthread functions without including their header;
# newer compilers (GCC 13, Ubuntu 24.04) refuse that. The header is handed to
# the compiler here instead of changing the vendor's source.
colcon build --packages-select ldlidar_stl_ros2 \
  --cmake-args -DCMAKE_BUILD_TYPE=Release "-DCMAKE_CXX_FLAGS=-include pthread.h"
echo "Built ldlidar_stl_ros2 at $version in $workspace"
