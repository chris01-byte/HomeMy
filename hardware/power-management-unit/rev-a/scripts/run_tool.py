"""Run a local KiCad command with all writable settings inside the workspace.

Usage: python run_tool.py --kicad-root PATH [--timeout SECONDS] COMMAND ...
COMMAND can be kicad-cli or python (the KiCad PCB Python environment).
"""
import argparse
import os
from pathlib import Path
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--kicad-root', required=True, type=Path)
    parser.add_argument('--timeout', type=float, default=180)
    parser.add_argument('command', choices=['kicad-cli', 'python'])
    parser.add_argument('args', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    root = args.kicad_root.resolve()
    settings = root.parent / 'kicad-local-settings'
    env = os.environ.copy()
    for key, folder in [('KICAD_CONFIG_HOME', 'config'),
                        ('KICAD_DOCUMENTS_HOME', 'documents'),
                        ('KICAD_CACHE_HOME', 'cache')]:
        target = settings / folder
        target.mkdir(parents=True, exist_ok=True)
        env[key] = str(target)
    for key, folder in [('KICAD10_FOOTPRINT_DIR', 'footprints'),
                        ('KICAD10_SYMBOL_DIR', 'symbols'),
                        ('KICAD10_TEMPLATE_DIR', 'template')]:
        env[key] = str(root / 'share' / 'kicad' / folder)
    if os.name == 'nt':
        cache = settings / 'font-cache'
        cache.mkdir(exist_ok=True)
        config = settings / 'fonts.conf'
        config.write_text('<?xml version="1.0"?><!DOCTYPE fontconfig SYSTEM "fonts.dtd"><fontconfig><dir>C:/Windows/Fonts</dir><cachedir>' + cache.as_posix() + '</cachedir></fontconfig>', encoding='utf-8')
        env['FONTCONFIG_FILE'] = str(config)
    suffix = '.exe' if os.name == 'nt' else ''
    command = [str(root / 'bin' / (args.command + suffix))] + args.args
    proc = subprocess.Popen(command, env=env)
    try:
        return proc.wait(timeout=args.timeout)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()
        print('ERROR: tool timed out; this run is NOT a passed check.', file=sys.stderr)
        return 124


if __name__ == '__main__':
    raise SystemExit(main())
