"""Compile/run the bounded, checkpointed Freerouting 2.1 helper using Java 21.

Requires the exact existing Freerouting 2.1.0 jar and Eclipse ECJ 3.38.0 jar.
Does not install a runtime, modify a KiCad PCB, upload a design, or claim DRC.
Exit 0: helper reports zero router incompletes; 2: partial routing; 3: error.
Native KiCad import and DRC are mandatory regardless of exit status.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time


HERE = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    started=time.monotonic()
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--java', required=True, type=Path)
    ap.add_argument('--router-jar', required=True, type=Path)
    ap.add_argument('--compiler-jar', required=True, type=Path)
    ap.add_argument('--input', required=True, type=Path)
    ap.add_argument('--output', required=True, type=Path)
    ap.add_argument('--passes', type=int, default=2)
    ap.add_argument('--seconds', type=int, default=600)
    ap.add_argument('--ignore-net-classes', default='')
    args = ap.parse_args()
    if not 1 <= args.passes <= 250 or not 1 <= args.seconds <= 500:
        ap.error('Rebuild limits: max250 passes,500 engine seconds plus bounded startup/stop')
    args.output = args.output.resolve()
    args.output.mkdir(parents=True, exist_ok=True)
    for name in ('java', 'router_jar', 'compiler_jar', 'input'):
        setattr(args, name, getattr(args, name).resolve())
    if args.input.suffix.lower() != '.dsn':
        ap.error('Input must be a DSN export, never a native PCB')
    if args.input.parent == args.output and args.input.name in ('latest.dsn', 'best-incomplete-count.dsn'):
        ap.error('Resumed input needs a new run directory to preserve its snapshot')
    if (args.output/'run-manifest.json').exists():
        ap.error('Use a new output run directory; previous candidates are preserved')
    classes = args.output/'classes'
    classes.mkdir(exist_ok=True)
    source = HERE.parents[1]/'rev-a1/scripts/routing/CheckpointRouter.java'
    input_snapshot=args.output/'input.kicad.dsn'
    if input_snapshot==args.input:
        ap.error('Input needs a distinct run directory')
    shutil.copyfile(args.input,input_snapshot)
    snapshots = {str(p):sha(p) for p in (source, args.input, args.router_jar, args.compiler_jar)}
    flags = subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
    compile_command = [str(args.java), '-jar', str(args.compiler_jar), '-21', '-cp',
                       str(args.router_jar), '-d', str(classes), str(source)]
    build = subprocess.run(compile_command, capture_output=True, text=True, timeout=60, creationflags=flags)
    (args.output/'compile.log').write_text(build.stdout+build.stderr, encoding='utf-8')
    if build.returncode:
        print(build.stdout+build.stderr, file=sys.stderr)
        return 3
    command = [str(args.java), '-Djava.awt.headless=true', '-Xmx4g', '-cp',
               str(classes)+os.pathsep+str(args.router_jar), 'CheckpointRouter',
               str(input_snapshot), str(args.output), str(args.passes), str(args.seconds), args.ignore_net_classes]
    forced_stop = False
    with (args.output/'console.log').open('w', encoding='utf-8') as log:
        proc = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
        print(f'Routing PID {proc.pid}; checkpoints/log: {args.output}', flush=True)
        try:
            # Java helper has its own time bound plus a 45 s cooperative stop;
            # this outer bound also covers malformed-input/startup hangs.
            code = proc.wait(timeout=max(1,600-(time.monotonic()-started)))
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            forced_stop, code = True, 3
    changed = [path for path, previous in snapshots.items() if sha(Path(path)) != previous]
    console = (args.output/'console.log').read_text(encoding='utf-8', errors='replace')
    caught_errors = {name:len(re.findall(re.escape(name), console)) for name in
                     ('NullPointerException', 'ArrayIndexOutOfBoundsException', 'OutOfMemoryError')}
    outputs = [p for p in args.output.iterdir() if p.is_file() and p.suffix != '.tmp']
    manifest = dict(rev_a_engineering_prototype=True, rev_b_production=False,
        state='engineering_routing_candidate_not_order_release', total_seconds=time.monotonic()-started, hard_limit_seconds=600,
        date_utc=datetime.now(timezone.utc).isoformat(), compile_command=compile_command,
        command=command, exit_code=code, external_timeout_kill=forced_stop,
        engine_exception_log_occurrences=caught_errors,
        immutable_input_snapshot=dict(path=input_snapshot.name,sha256=sha(input_snapshot)),
        inputs=[dict(path=p, sha256=s) for p,s in snapshots.items()],
        changed_inputs=changed, native_pcb_modified=False, native_kicad_drc_performed=False,
        outputs=[dict(path=p.name, sha256=sha(p), bytes=p.stat().st_size) for p in outputs])
    (args.output/'run-manifest.json').write_text(json.dumps(manifest, indent=2)+'\n', encoding='utf-8')
    print(f'Router exit {code}; {len(outputs)} output files; changed inputs: {changed}', flush=True)
    return 3 if changed else code


if __name__ == '__main__':
    raise SystemExit(main())
