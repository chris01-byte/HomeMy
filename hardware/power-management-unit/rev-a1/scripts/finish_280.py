"""Bounded 280x220 task ledger and native validation, separate from the closed size study.

Run with ordinary Python. CAD edits and reload audits run separately in KiCad Python.
No command in this module changes PCB geometry or manufacturing release.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import subprocess
import time
from bounded_checks import input_hashes, sha, write

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'finish-280x220'
LEDGER = OUT / 'ledger.json'
SOURCE = ROOT / 'kicad/HomeMy_PMU_RevA_275x210.kicad_pcb'
BOARD = ROOT / 'kicad/HomeMy_PMU_RevA_280x220.kicad_pcb'
SCRATCH = ROOT.parents[3] / 'tools-local/finish-280x220'
CLI = r'C:\Program Files\KiCad\10.0\bin\kicad-cli.exe'

def now(): return datetime.now(timezone.utc).isoformat()
def read(): return json.loads(LEDGER.read_text(encoding='utf-8'))
def elapsed(r): return (datetime.now(timezone.utc)-datetime.fromisoformat(r['started_utc'])).total_seconds()/60

def guard(r):
    if r.get('stop_required') or r.get('closed') or elapsed(r) >= 180:
        raise RuntimeError('Hard task boundary reached; save, document, commit and push only')

def initialize():
    assert not LEDGER.exists() and not BOARD.exists()
    assert sha(SOURCE)=='1fed03fee50306971e381b0a862e38ba01ba24395e59430c27f37d2513381daa'
    OUT.mkdir(exist_ok=True); SCRATCH.mkdir(parents=True,exist_ok=True)
    r={'started_utc':'2026-09-11T14:48:00+00:00','branch':'codex/pmu-rev-a1-280x220-finish',
       'source_pcb':str(SOURCE.relative_to(ROOT)), 'source_sha256':sha(SOURCE),
       'limits':{'total_minutes':180,'cycles':6,'autorouter_calls':4,'router_seconds':600,'router_passes':250,
                 'attempts_per_unchanged_fault':2,'consecutive_no_progress':2,'identical_process_restarts':2},
       'cycle_counting':'Phase A outline/refill/baseline counts as cycle 1; five subsequent edit/check cycles remain.',
       'cycles':[], 'native_calls':[], 'router_calls':[], 'repair_attempts':{},'no_progress_streak':0,'closed':False}
    write(LEDGER,r)
    for ext in ['.kicad_sch','.kicad_dru','.kicad_pro']:
        shutil.copyfile(SOURCE.with_suffix(ext),BOARD.with_suffix(ext))
    pro=json.loads(BOARD.with_suffix('.kicad_pro').read_text(encoding='utf-8'))
    pro['meta']['filename']=BOARD.with_suffix('.kicad_pro').name
    for sheet in pro['schematic'].get('top_level_sheets',[]):
        if sheet['filename']==SOURCE.with_suffix('.kicad_sch').name:
            sheet['filename']=BOARD.with_suffix('.kicad_sch').name;sheet['name']=BOARD.stem
    write(BOARD.with_suffix('.kicad_pro'),pro)
    r=read();r['project_sha256']=sha(BOARD.with_suffix('.kicad_pro'));write(LEDGER,r)
    begin('Phase A: unchanged 275 source, fixed outline extension, refill and native baseline')

def begin(label):
    r=read();guard(r)
    assert len(r['cycles'])<6 and (not r['cycles'] or r['cycles'][-1]['status']=='completed')
    r['cycles'].append({'number':len(r['cycles'])+1,'label':label,'started_utc':now(),'status':'editing','actions':[]})
    write(LEDGER,r)

def action(label,details):
    r=read();guard(r);assert r['cycles'][-1]['status']=='editing'
    r['cycles'][-1]['actions'].append({'label':label,'details':details,'at_utc':now()});write(LEDGER,r)

def attempt(key,signature):
    r=read();guard(r);k=key+'|'+signature
    assert r['repair_attempts'].get(k,0)<2, 'Two attempts already spent on unchanged fault: '+key
    r['repair_attempts'][k]=r['repair_attempts'].get(k,0)+1;write(LEDGER,r)

def native(label):
    r=read();guard(r);before=input_hashes(BOARD);results={}
    # Refuse testing with defaults accidentally written by a scratch-board
    # load. The source configuration is mandatory, not a tunable parameter.
    if r.get('project_sha256'):
        assert sha(BOARD.with_suffix('.kicad_pro'))==r['project_sha256'], 'Project input changed; restore verified settings before native checks'
    for kind,domain,ext in [('erc','sch','.kicad_sch'),('drc','pcb','.kicad_pcb')]:
        guard(r);out=OUT/(label+'-'+kind+'.json');assert not out.exists()
        cmd=[CLI,domain,kind,'--format','json','--severity-all','--exit-code-violations','--output',str(out)]
        if kind=='drc':cmd+=['--all-track-errors','--schematic-parity']
        cmd.append(str(BOARD.with_suffix(ext)))
        event={'kind':kind,'label':label,'started_utc':now(),'command':cmd,'pcb_sha256':sha(BOARD)}
        r['native_calls'].append(event);write(LEDGER,r);start=time.monotonic()
        try:
            p=subprocess.run(cmd,capture_output=True,text=True,errors='replace',timeout=min(180,max(1,(180-elapsed(r))*60)))
            code,output=p.returncode,p.stdout+p.stderr
        except subprocess.TimeoutExpired:
            code,output=124,'Timed out: this is never a successful native completion.'
        event.update(exit_code=code,seconds=round(time.monotonic()-start,3))
        raw=json.loads(out.read_text(encoding='utf-8')) if out.exists() else {}
        required=['sheets','$schema'] if kind=='erc' else ['violations','unconnected_items','schematic_parity','$schema']
        complete=code in (0,5) and all(k in raw for k in required) and raw.get('$schema')=='https://schemas.kicad.org/'+kind+'.v1.json'
        rows=[v for s in raw.get('sheets',[]) for v in s.get('violations',[])] if kind=='erc' else raw.get('violations',[])
        counts=Counter((v['type'],v['severity']) for v in rows)
        v={'exit_code':code,'normal_completion':code in (0,5),'complete':complete,'report':out.name,
           'report_sha256':sha(out) if out.exists() else None,'seconds':event['seconds'],'process_output':output[-5000:],
           'counts':[{'type':k[0],'severity':k[1],'count':n} for k,n in sorted(counts.items())],
           'open_connections':len(raw.get('unconnected_items',[])), 'parity':len(raw.get('schematic_parity',[])),
           'counts_may_be_capped':any(n>=199 for n in counts.values()) or len(raw.get('unconnected_items',[]))>=499,
           'passed':complete and code==0 and not rows and not raw.get('unconnected_items') and not raw.get('schematic_parity')}
        results[kind]=v;event['report_sha256']=v['report_sha256'];write(LEDGER,r)
        print(kind,label,code,v['counts'],'opens',v['open_connections'],flush=True)
        if not complete:
            r['stop_required']='Native check missing, abnormal or incomplete';write(LEDGER,r);break
    assert input_hashes(BOARD)==before, 'Native checker changed input bytes'
    write(OUT/(label+'-native.json'),{'pcb_sha256':sha(BOARD),'input_hashes_sha256':before,'results':results})

def conclude(label):
    r=read();guard(r)
    n=json.loads((OUT/(label+'-native.json')).read_text(encoding='utf-8'))
    g=json.loads((OUT/(label+'-geometry.json')).read_text(encoding='utf-8'))
    assert n['pcb_sha256']==g['pcb_sha256']==sha(BOARD)
    er,dr=n['results']['erc'],n['results']['drc'];counts={x['type']:x['count'] for x in dr['counts']}
    forbidden=[x for x in dr['counts'] if x['type'] not in ['connection_width','track_dangling','via_dangling']]
    good=er['passed'] and dr['complete'] and not dr['parity'] and not forbidden and counts.get('connection_width',0)<=10 and g['placement']['passed'] and g['invariants']['passed'] and g['outline_exact_mm']==[280.0,220.0]
    m={'opens':g['native_ratsnest_connections'],'counts':counts,'force':g['force']['passed_pairs'],'critical':g['critical']['passed'],'pcb_sha256':sha(BOARD)}
    progressive=False;lost=[];reasons=[]
    if r.get('best'):
        old=json.loads((OUT/(r['best']['label']+'-geometry.json')).read_text(encoding='utf-8'));b=r['best']['metrics']
        for key,rows,predicate in [('force',g['force']['original_pair_checks'],'passed'),('critical',g['critical']['paths'],'path_found')]:
            prev=old[key]['original_pair_checks' if key=='force' else 'paths']
            lost.extend([a for a,z in zip(prev,rows) if a[predicate] and not z[predicate]])
        good=good and not lost
        if m['opens']<=b['opens']-5 or m['opens']<=b['opens']*.95:reasons.append('open connection reduction')
        if m['force']>b['force']:reasons.append('required force path restored')
        if m['critical']>b['critical']:reasons.append('critical path restored')
        if sum(counts.values())<sum(b['counts'].values()):reasons.append('DRC/dangling count reduction')
        if counts.get('connection_width',0)>b['counts'].get('connection_width',0) and m['opens']>=b['opens']:good=False
        progressive=good and bool(reasons)
    else:
        progressive=good;reasons=['validated Phase A WIP baseline']
    c=r['cycles'][-1];c.update(status='completed',finished_utc=now(),label_id=label,metrics=m,progress=progressive,progress_reasons=reasons,lost_paths=lost,eligible=good)
    if progressive:
        shutil.copyfile(BOARD,SCRATCH/'best.kicad_pcb');r['best']={'label':label,'metrics':m,'saved_utc':now()};r['no_progress_streak']=0
    else:
        r['no_progress_streak']+=1
        if r.get('best'):shutil.copyfile(SCRATCH/'best.kicad_pcb',BOARD)
    if r['no_progress_streak']>=2:r['stop_required']='Two successive cycles without safe measurable progress'
    if len(r['cycles'])>=6:r['stop_required']='Six complete edit/check cycles used'
    write(LEDGER,r);print(json.dumps({'cycle':c['number'],'metrics':m,'progress':progressive,'reasons':reasons,'stop':r.get('stop_required')},indent=2))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['init','begin','native','conclude']);p.add_argument('label',nargs='?',default='cycle-01');a=p.parse_args()
    {'init':initialize,'begin':lambda:begin(a.label),'native':lambda:native(a.label),'conclude':lambda:conclude(a.label)}[a.mode]()
