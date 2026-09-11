"""Bounded lead-owned new-layout runner. Original CAD is read-only input."""
from pathlib import Path
import datetime as dt
import hashlib,json,shutil,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];BASE=ROOT.parent/'rev-a'
CAD=ROOT/'kicad';OUT=ROOT/'reports';NAME='HomeMy_PMU_RevA1_Rebuild_280x220'
BOARD=CAD/(NAME+'.kicad_pcb');LEDGER=ROOT/'ledger.json'
SCRATCH=ROOT.parents[3]/'tools-local/rebuild-280x220'
START=dt.datetime(2026,9,11,16,27,tzinfo=dt.timezone.utc)
def now():return dt.datetime.now(dt.timezone.utc)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):p.write_text(json.dumps(v,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def read():return json.loads(LEDGER.read_text(encoding='utf-8'))
def normalize_project(v):
    v['meta']['filename']='project.kicad_pro'
    v['net_settings']['classes'].sort(key=lambda r:r['name'])
    for s in v['schematic'].get('top_level_sheets',[]):s['filename']='project.kicad_sch';s['name']='project'
    return v
def bind_project_metadata():
    source=json.loads((BASE/'kicad/HomeMy_PMU_RevA.kicad_pro').read_text(encoding='utf-8'))
    target=json.loads(BOARD.with_suffix('.kicad_pro').read_text(encoding='utf-8'))
    assert normalize_project(source)==normalize_project(target),'Nonmetadata project alteration'
    r=read();r['actions'].append({'name':'Bind renamed project after native metadata serialization','time':now().isoformat(),
         'prior_sha256':r['project_sha256'],'new_sha256':sha(BOARD.with_suffix('.kicad_pro')),
         'allowed_differences':'Project filename, top-level sheet filename/name, class array order only; priorities and every numerical rule unchanged'})
    r['project_sha256']=sha(BOARD.with_suffix('.kicad_pro'));write(LEDGER,r)
def guard():
    r=read();assert not r.get('closed') and not r.get('stop_required'), 'Closed/stopped task'
    assert (now()-START).total_seconds()<160*60,'Editing deadline reached'
    assert len(r['cycles'])<=6 and r['router_calls']<=4
    assert sha(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb')==r['baseline_pcb_sha256']
    assert sha(BOARD.with_suffix('.kicad_pro'))==r['project_sha256'],'Project settings changed'
    assert sha(BOARD.with_suffix('.kicad_dru'))==r['rules_sha256'],'Rules changed'
    return r

def read_only_guard():
    r=read()
    assert sha(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb')==r['baseline_pcb_sha256']
    assert sha(BOARD.with_suffix('.kicad_pro'))==r['project_sha256']
    assert sha(BOARD.with_suffix('.kicad_dru'))==r['rules_sha256']
    return r
def init():
    assert not LEDGER.exists()
    for p in (BASE/'kicad').glob('*.kicad_sch'):
        shutil.copyfile(p,CAD/(NAME+'.kicad_sch' if p.stem=='HomeMy_PMU_RevA' else p.name))
    for ext in ['.kicad_dru','.kicad_pro','.kicad_pcb']:
        shutil.copyfile(BASE/'kicad'/('HomeMy_PMU_RevA'+ext),CAD/(NAME+ext))
    for name in ['sym-lib-table','fp-lib-table']:
        s=(BASE/'kicad'/name).read_text(encoding='utf-8').replace('${KIPRJMOD}/','${KIPRJMOD}/../../rev-a/kicad/')
        (CAD/name).write_text(s,encoding='utf-8')
    write(LEDGER,{'started_at':START.isoformat(),'branch':'codex/pmu-rev-a1-280x220-rebuild',
       'baseline_pcb_sha256':sha(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'),
       'project_sha256':sha(BOARD.with_suffix('.kicad_pro')),'rules_sha256':sha(BOARD.with_suffix('.kicad_dru')),
       'cycles':[],'router_calls':0,'closed':False,'stop_required':False,'actions':[]})
    write(ROOT/'release.json',{'cad_complete':False,'orderable':False,'fabrication_release':False,'assembly_release':False,'production_release':False,'wip':True,'state':'new_layout_in_progress'})
def action(name,value):
    r=guard();r['actions'].append({'name':name,'time':now().isoformat(),**value});write(LEDGER,r)
def begin(label):
    r=guard();assert len(r['cycles'])<6 and (not r['cycles'] or r['cycles'][-1].get('completed'))
    r['cycles'].append({'number':len(r['cycles'])+1,'objective':label,'started_at':now().isoformat(),'completed':False});write(LEDGER,r)
def conclude(label,accepted,note):
    r=guard();c=r['cycles'][-1];assert not c['completed']
    g=json.loads((OUT/(label+'-geometry.json')).read_text(encoding='utf-8'))
    n=json.loads((OUT/(label+'-native.json')).read_text(encoding='utf-8'))
    c.update(completed=True,finished_at=now().isoformat(),accepted=accepted,note=note,pcb_sha256=sha(BOARD),
       opens=g['open_connections'],force=g['force']['passed_pairs'],critical=g['critical']['passed'],placement=g['placement']['passed'],native=n['checks'])
    if accepted:
        SCRATCH.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(BOARD,SCRATCH/'best.kicad_pcb');r['best_label']=label;r['no_progress']=0
    else:r['no_progress']=r.get('no_progress',0)+1
    if r.get('no_progress',0)>=2:r['stop_required']='Two consecutive cycles without admissible progress'
    write(LEDGER,r)
def native(label):
    check_guard=read_only_guard if label=='final' else guard
    r=check_guard();records={};inputs={str(p.relative_to(ROOT.parent)).replace('\\','/'):sha(p) for p in CAD.iterdir() if p.suffix in ['.kicad_sch','.kicad_pcb','.kicad_pro','.kicad_dru'] or p.name in ['sym-lib-table','fp-lib-table']}
    for p in (BASE/'kicad').rglob('*'):
        if p.is_file() and p.suffix in ['.kicad_sym','.kicad_mod']:
            inputs[str(p.relative_to(ROOT.parent)).replace('\\','/')]=sha(p)
    for kind in ['erc','drc']:
        dest=OUT/(label+'-'+kind+'.json')
        cmd=[r'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','sch' if kind=='erc' else 'pcb',kind,'--format','json','--severity-all','--exit-code-violations','--output',str(dest)]
        if kind=='drc':cmd+=['--schematic-parity','--all-track-errors']
        cmd+=[str(BOARD.with_suffix('.kicad_sch') if kind=='erc' else BOARD)]
        t=now();p=subprocess.run(cmd,capture_output=True,timeout=90)
        report=json.loads(dest.read_text(encoding='utf-8'));counts={}
        findings=report.get('violations',[]) if kind=='drc' else [v for s in report.get('sheets',[]) for v in s.get('violations',[])]
        for v in findings:
            key=v['severity']+':'+v['type'];counts[key]=counts.get(key,0)+1
        records[kind]={'command':cmd,'exit':p.returncode,'seconds':(now()-t).total_seconds(),'counts':counts,
                      'open_connections':len(report.get('unconnected_items',[])),'parity':len(report.get('schematic_parity',[])),
                      'sha256':sha(dest),'stdout':p.stdout.decode('utf-8','replace'),'stderr':p.stderr.decode('utf-8','replace')}
    check_guard();write(OUT/(label+'-native.json'),{'inputs':inputs,'checks':records});print(label,json.dumps(records),flush=True)
if __name__=='__main__':
    if sys.argv[1]=='init':init()
    elif sys.argv[1]=='bind-project-metadata':bind_project_metadata()
    elif sys.argv[1]=='begin':begin(sys.argv[2])
    elif sys.argv[1]=='native':native(sys.argv[2])
    elif sys.argv[1]=='conclude':conclude(sys.argv[2],sys.argv[3]=='accept',sys.argv[4])
