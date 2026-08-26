#!/usr/bin/env python3
"""Build a bounded, task-specific context packet for an agent."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INDEX_PATH = ROOT / "context" / "index.json"


def load_index() -> dict:
    with INDEX_PATH.open(encoding="utf-8") as source:
        return json.load(source)


def selected_paths(index: dict, area: str | None) -> list[str]:
    paths = list(index["default_files"])
    if area is None:
        return paths

    areas = index["areas"]
    if area not in areas:
        choices = ", ".join(sorted(areas))
        raise ValueError(f"unknown area {area!r}; choose one of: {choices}")

    paths.extend(areas[area]["files"])
    return list(dict.fromkeys(paths))


def read_packet(paths: list[str], limit: int) -> tuple[str, list[str]]:
    sections: list[str] = []
    errors: list[str] = []

    for relative_path in paths:
        path = ROOT / relative_path
        if not path.is_file():
            errors.append(f"missing context file: {relative_path}")
            continue
        sections.append(f"# {relative_path}\n\n{path.read_text(encoding='utf-8').rstrip()}\n")

    packet = "\n".join(sections)
    if len(packet) > limit:
        errors.append(f"context packet has {len(packet)} characters; limit is {limit}")
    return packet, errors


def check_index(index: dict) -> list[str]:
    errors: list[str] = []
    limit = index["max_bundle_characters"]
    for area in index["areas"]:
        _, area_errors = read_packet(selected_paths(index, area), limit)
        errors.extend(f"{area}: {error}" for error in area_errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--area", help="context area from context/index.json")
    parser.add_argument("--check", action="store_true", help="validate every configured packet")
    args = parser.parse_args()

    try:
        index = load_index()
        errors = check_index(index) if args.check else []
        if errors:
            raise ValueError("\n".join(errors))
        packet, errors = read_packet(
            selected_paths(index, args.area), index["max_bundle_characters"]
        )
        if errors:
            raise ValueError("\n".join(errors))
    except (KeyError, ValueError, json.JSONDecodeError) as error:
        print(f"context error: {error}", file=sys.stderr)
        return 1

    if not args.check:
        print(packet)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
