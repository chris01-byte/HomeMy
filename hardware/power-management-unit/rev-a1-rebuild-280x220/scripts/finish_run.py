"""One bounded follow-up run; historical rebuild ledger/reports remain evidence."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess,shutil,sys

ROOT=Path(__file__).resolve().parents[1]
CAD=ROOT/'kicad'; NAME='HomeMy_PMU_RevA1_Rebuild_280x220'
BOARD=CAD/(NAME+'.kicad_pcb'); OUT=ROOT/'reports/finish'
LEDGER=ROOT/'finish-ledger.json'
SCRATCH=ROOT.parents[3]/'.pmu-tools/finish-rebuild-20260913'
CLI='C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
START=dt.datetime(2026,9,13,11,36,tzinfo=dt.timezone.utc)
EXPECTED='9f329b44bf0fece059550d2f4a07b94af8fb52cfec7d26c4796aeed230193f99'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8',newline='\n')
def now():return dt.datetime.now(dt.timezone.utc)
def read():return json.loads(LEDGER.read_text(encoding='utf-8'))
def inputs():
    paths=[p for p in CAD.iterdir() if p.suffix in ('.kicad_pcb','.kicad_pro','.kicad_dru','.kicad_sch') or p.name in ('sym-lib-table','fp-lib-table')]
    paths += [p for p in (ROOT.parent/'rev-a/kicad').rglob('*') if p.suffix in ('.kicad_sym','.kicad_mod')]
    return {p.relative_to(ROOT.parent).as_posix():sha(p) for p in paths}
def guard(edit=False):
    r=read();assert not r['closed'] or not edit
    assert all(sha(CAD/f)==h for f,h in r['fixed_settings'].items()),'Fixed settings changed'
    if edit:
        assert not r.get('stop_reason'),'Stopped run'
        assert (now()-START).total_seconds()<155*60,'Editing deadline'
        assert len(r['cycles'])<=8 and r['router_calls']<=1
    return r
def init():
    assert not LEDGER.exists() and sha(BOARD)==EXPECTED
    OUT.mkdir();SCRATCH.mkdir(parents=True,exist_ok=False)
    snap=SCRATCH/'start';snap.mkdir()
    for p in CAD.iterdir():
        if p.suffix in ('.kicad_pcb','.kicad_pro','.kicad_dru','.kicad_sch') or p.name in ('sym-lib-table','fp-lib-table'):shutil.copyfile(p,snap/p.name)
    write(LEDGER,{'started_at':START.isoformat(),'editing_deadline':(START+dt.timedelta(minutes=155)).isoformat(),'hard_deadline':(START+dt.timedelta(minutes=180)).isoformat(),
      'branch':'codex/pmu-rev-a1-280x220-rebuild','authorized_source_commit':'0dd4a3b4a81ef42925506c995fb0fcbda171ecb0','start_pcb_sha256':EXPECTED,
      'fixed_settings':{p.name:sha(p) for p in CAD.iterdir() if p.suffix in ('.kicad_pro','.kicad_dru','.kicad_sch')},
      'cycles':[],'router_calls':0,'native_restarts':{},'closed':False,'stop_reason':None,'events':[]})
    print('Follow-up initialized from exact committed PCB',flush=True)
def command(label,cmd,timeout=90,direct_log=False):
    t=now();record={'command':cmd,'started_at':t.isoformat()}
    from finish_environment import environment
    env=environment();record['fontconfig_environment_sha256']=sha(OUT/'fontconfig-environment.json')
    if direct_log:
        # One final diagnostic: wait on the owned process, not pipe EOF.
        stdout=SCRATCH/(label+'-stdout.log');stderr=SCRATCH/(label+'-stderr.log')
        with stdout.open('wb') as out,stderr.open('wb') as err:
            p=subprocess.Popen(cmd,stdout=out,stderr=err,creationflags=subprocess.CREATE_NO_WINDOW,env=env)
            record.update(pid=p.pid,output_transport='workspace files; Popen.wait on native process')
            try:
                record.update(exit=p.wait(timeout=timeout),timed_out=False)
            except subprocess.TimeoutExpired:
                record.update(exit=None,timed_out=True,poll_at_timeout=p.poll())
                if p.poll() is None:p.kill()
                record['terminated_returncode']=p.wait(timeout=10)
        record.update(stdout=stdout.read_bytes().decode('utf-8','replace'),stderr=stderr.read_bytes().decode('utf-8','replace'))
    else:
      try:
        p=subprocess.run(cmd,capture_output=True,timeout=timeout,creationflags=subprocess.CREATE_NO_WINDOW,env=env)
        record.update(exit=p.returncode,timed_out=False,stdout=p.stdout.decode('utf-8','replace'),stderr=p.stderr.decode('utf-8','replace'))
      except subprocess.TimeoutExpired as e:
        record.update(exit=None,timed_out=True,stdout=(e.stdout or b'').decode('utf-8','replace'),stderr=(e.stderr or b'').decode('utf-8','replace'))
    record['seconds']=(now()-t).total_seconds();write(OUT/(label+'-process.json'),record)
    return record
def native(label,kind='drc',refill=False,direct_log=False):
    assert not guard(edit=refill)['closed'],'This bounded run is closed'
    before=inputs();dest=OUT/(label+'-'+kind+'.json')
    assert not dest.exists()
    cmd=[CLI,'pcb' if kind=='drc' else 'sch',kind,'--format','json','--severity-all','--exit-code-violations','--output',str(dest)]
    if kind=='drc':cmd+=['--schematic-parity','--all-track-errors']
    if refill:assert kind=='drc';cmd+=['--refill-zones','--save-board']
    cmd+=[str(BOARD if kind=='drc' else BOARD.with_suffix('.kicad_sch'))]
    result=command(label+'-'+kind,cmd,direct_log=direct_log)
    after=inputs();assert refill or before==after
    record={'inputs_before':before,'inputs_after':after,'process':result,'report_sha256':sha(dest) if dest.exists() else None}
    if dest.exists():
        d=json.loads(dest.read_text(encoding='utf-8'));v=d.get('violations',[]) if kind=='drc' else [v for s in d['sheets'] for v in s.get('violations',[])]
        from collections import Counter
        record.update(counts=dict(Counter(x['severity']+':'+x['type'] for x in v)),opens=len(d.get('unconnected_items',[])),parity=len(d.get('schematic_parity',[])))
    write(OUT/(label+'-'+kind+'-receipt.json'),record)
    r=read();r['events'].append({'operation':kind,'label':label,'exit':result['exit'],'timed_out':result['timed_out'],'pcb_sha256':sha(BOARD),'refill_saved':refill});write(LEDGER,r)
    print(label,kind,'exit',result['exit'],'timeout',result['timed_out'],'counts',record.get('counts'),'opens',record.get('opens'),flush=True)
    return record
if __name__=='__main__':
    if sys.argv[1]=='init':init()
    elif sys.argv[1]=='native':native(sys.argv[2],sys.argv[3],'refill' in sys.argv[4:],'direct-log' in sys.argv[4:])
