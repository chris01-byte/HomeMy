"""Capture native ERC/DRC reports, input hashes, and process status separately.

A complete report is usable diagnostic evidence even if this portable Windows
KiCad process hangs while closing its denied registry settings. Such a process
is never recorded as a successful exit. No PCB is saved by these checks.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from build_schematic import ROOT, CAD, PROJECT


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def violations(value):
    if isinstance(value,dict):
        return len(value.get('violations',[]))+sum(violations(x) for k,x in value.items() if k!='violations')
    if isinstance(value,list):
        return sum(violations(x) for x in value)
    return 0


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--kicad-root',required=True,type=Path)
    parser.add_argument('--timeout',type=int,default=180)
    parser.add_argument('--only',choices=['erc','drc','both'],default='both')
    args=parser.parse_args()
    reports=ROOT/'reports';reports.mkdir(exist_ok=True)
    inputs=sorted([*CAD.glob('*.kicad_sch'),*CAD.glob('*.kicad_pcb'),
                   *CAD.glob('*.kicad_pro'),*CAD.glob('*.kicad_dru'),
                   *CAD.glob('*-lib-table'),*CAD.rglob('*.kicad_mod'),
                   *CAD.rglob('*.kicad_sym')])
    before={str(p.relative_to(ROOT)):sha(p) for p in inputs}
    summary={'rev_a_engineering_prototype':True,'rev_b_production':False,
             'started_at_utc':datetime.now(timezone.utc).isoformat(),
             'checks':{},'input_hashes_sha256':before,
             'interpretation':'Report acceptance and process exit are separate. Hardware validation is not performed.'}
    for name,domain,suffix in [('erc','sch','.kicad_sch'),('drc','pcb','.kicad_pcb')]:
        if args.only not in ['both',name]:
            continue
        pending=reports/(name+'-pending.json')
        final=reports/(name+'-final.json')
        if pending.exists():
            pending.unlink()
        executable=args.kicad_root.resolve()/'bin'/('kicad-cli.exe' if os.name=='nt' else 'kicad-cli')
        command=[str(executable),domain,name,'--format','json',
                 '--severity-all','--exit-code-violations','--output',str(pending)]
        if name=='drc':
            command+=['--all-track-errors','--schematic-parity']
        command.append(str(CAD/(PROJECT+suffix)))
        started=time.time()
        try:
            run=subprocess.run(command,capture_output=True,text=True,errors='replace',timeout=args.timeout)
        except subprocess.TimeoutExpired as exc:
            decode=lambda s:s.decode('utf-8',errors='replace') if isinstance(s,bytes) else (s or '')
            run=subprocess.CompletedProcess(command,124,decode(exc.stdout),decode(exc.stderr)+'\nTimeout: native process did not exit normally.\n')
        output=run.stdout+run.stderr
        (reports/(name+'-final-process.log')).write_text(output,encoding='utf-8')
        result={'command':command,'process_exit_code':run.returncode,'process_passed':run.returncode==0,
                'wall_seconds':round(time.time()-started,3),'report_complete':False}
        if pending.exists() and pending.stat().st_mtime>=started-1:
            report=json.loads(pending.read_text(encoding='utf-8'))
            expected='erc' if name=='erc' else 'drc'
            if expected not in report.get('$schema',''):
                raise ValueError('Unexpected native report schema: '+str(pending))
            pending.replace(final)
            result.update(report_complete=True,report_path=str(final.relative_to(ROOT)),
                          report_sha256=sha(final),violations=violations(report),
                          unconnected_items=len(report.get('unconnected_items',[])),
                          schematic_parity_issues=len(report.get('schematic_parity',[])),
                          ignored_checks=report.get('ignored_checks',[]))
            result['report_has_zero_findings']=all(result[k]==0 for k in ['violations','unconnected_items','schematic_parity_issues'])
        else:
            result['report_has_zero_findings']=False
        summary['checks'][name]=result
        print(name, json.dumps({k:v for k,v in result.items() if k not in ['command','ignored_checks']}),flush=True)
    summary['changed_inputs']=[str(p.relative_to(ROOT)) for p in inputs if sha(p)!=before[str(p.relative_to(ROOT))]]
    summary['reports_have_zero_findings']=not summary['changed_inputs'] and all(x['report_has_zero_findings'] for x in summary['checks'].values())
    summary['all_processes_passed']=all(x['process_passed'] for x in summary['checks'].values())
    (reports/('native-checks-'+args.only+'.json')).write_text(json.dumps(summary,indent=2)+'\n',encoding='utf-8')
    return 0 if summary['reports_have_zero_findings'] and summary['all_processes_passed'] else 2


if __name__=='__main__':
    raise SystemExit(main())
