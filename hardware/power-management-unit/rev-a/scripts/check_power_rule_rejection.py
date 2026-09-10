"""Inject undersized copper into an isolated project copy and inspect DRC.

The authoritative project is never changed. Native process success/failure is
recorded honestly, separately from detection of the intentional violations.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import uuid
from configure_power_rules import ROOT, CAD, PROJECT


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--kicad-root',type=Path,required=True)
    ap.add_argument('--scratch',type=Path,required=True)
    ap.add_argument('--timeout',type=int,default=30)
    args=ap.parse_args()
    folder=Path(tempfile.mkdtemp(prefix='pmu-negative-',dir=args.scratch.resolve()))
    shutil.copytree(CAD,folder/'kicad')
    board=folder/'kicad'/(PROJECT+'.kicad_pcb')
    text=board.read_text();track=str(uuid.uuid4());via=str(uuid.uuid4())
    injected=f'''(segment (start 133 30) (end 137 30) (width 0.2) (layer "F.Cu") (net "MOTION_SENSED_P") (uuid "{track}"))
(via (at 133 32) (size 0.6) (drill 0.3) (layers "F.Cu" "B.Cu") (net "MOTION_SENSED_P") (uuid "{via}"))'''
    board.write_text(text.rstrip()[:-1]+'\n'+injected+'\n)\n')
    report=folder/'negative-drc.json'
    command=[str(args.kicad_root.resolve()/'bin/kicad-cli.exe'),'pcb','drc','--format','json','--severity-all','--all-track-errors','--exit-code-violations','--schematic-parity','--output',str(report),str(board)]
    try:
        run=subprocess.run(command,capture_output=True,timeout=args.timeout)
        code=run.returncode;log=run.stdout+run.stderr
    except subprocess.TimeoutExpired as e:
        code=124;log=(e.stdout or b'')+(e.stderr or b'')+b'\nTimeout is not a successful process exit.\n'
    native=json.loads(report.read_text()) if report.exists() else {}
    detected=[v for v in native.get('violations',[]) if any(i['uuid'] in [track,via] for i in v['items'])]
    kinds={v['type'] for v in detected}
    out={'rev_a_engineering_prototype':True,'rev_b_production':False,'source_board_sha256':hashlib.sha256((CAD/(PROJECT+'.kicad_pcb')).read_bytes()).hexdigest(),
         'injected_track_uuid':track,'injected_via_uuid':via,'native_process_exit_code':code,'expected_native_exit_code':5,
         'normal_expected_process_exit':code==5,'undersized_track_detected':'track_width' in kinds,
         'undersized_via_detected':bool(kinds & {'via_diameter','via_drill','hole_size','drill_out_of_range'}),
         'detected_violations':detected,'native_report_sha256':hashlib.sha256(report.read_bytes()).hexdigest() if report.exists() else None,
         'limitation':'Detection evidence is separate from process completion. The actual board is checked independently with native exit code zero.'}
    (ROOT/'reports/power-rule-negative-control.json').write_text(json.dumps(out,indent=2)+'\n')
    (ROOT/'reports/power-rule-negative-control.log').write_bytes(log)
    if report.exists():shutil.copyfile(report,ROOT/'reports/power-rule-negative-drc.json')
    print(json.dumps({k:v for k,v in out.items() if k not in ['detected_violations']},indent=2))
    return 0 if out['undersized_track_detected'] and out['undersized_via_detected'] else 2


if __name__=='__main__':raise SystemExit(main())
