from pathlib import Path
import subprocess,json,hashlib,time,sys
from concurrent.futures import ThreadPoolExecutor
Q=Path('<SITZUNG>/agents/evidence/repro/tmp-power');B=Path('<SITZUNG>/agents/evidence/repro/hardware/power-management-unit/rev-a2-layout-280x260/kicad/HomeMy_PMU_RevA.kicad_pcb');PY='/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/3.9/bin/python3.9';tag=sys.argv[1];sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def run(kind):
 script=Q/(kind+'_audit.py');out=Q/(tag+'-'+kind+'.json');cmd=[PY,'-B',str(script),str(out)];st=time.monotonic();h=sha(B)
 try:
  p=subprocess.run(cmd,capture_output=True,text=True,timeout=90);r=dict(exit_code=p.returncode,timed_out=False,stdout=p.stdout,stderr=p.stderr)
 except subprocess.TimeoutExpired as ex:r=dict(exit_code=None,timed_out=True,error=str(ex))
 r.update(command=cmd,wall_seconds=round(time.monotonic()-st,3),input_pcb_sha256=h,output_pcb_sha256=sha(B),checker_sha256=sha(script),report_present=out.exists(),report_sha256=sha(out) if out.exists() else None);(Q/(tag+'-'+kind+'.log')).write_text(r.get('stdout','')+'\n'+r.get('stderr',''));return kind,r
with ThreadPoolExecutor(max_workers=2) as ex:rows=dict(ex.map(run,['power','critical']))
(Q/(tag+'-processes.json')).write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps({n:{k:v for k,v in r.items() if k not in ['stdout','stderr','command']} for n,r in rows.items()},indent=2));sys.exit(0 if all(r['exit_code']==0 and r['report_present'] and r['input_pcb_sha256']==r['output_pcb_sha256'] for r in rows.values()) else 2)
