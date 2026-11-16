import pcbnew as pcb, json, sys, re
S=sys.argv[1]
W='<SITZUNG>/pmu/hardware/power-management-unit/'
def padpos(path):
    b=pcb.LoadBoard(path); out={}
    for f in b.GetFootprints():
        r=f.GetReference()
        if re.match(r'(BC|NT|H|J[1-6]$)',r):
            for p in f.Pads():
                out[f'{r}.{p.GetNumber()}']=out.get(f'{r}.{p.GetNumber()}',[])+[(round(pcb.ToMM(p.GetPosition().x),3),round(pcb.ToMM(p.GetPosition().y),3))]
            out[r]=[(round(pcb.ToMM(f.GetPosition().x),3),round(pcb.ToMM(f.GetPosition().y),3))]
    return out
A=padpos(S+'/a2/kicad/HomeMy_PMU_RevA.kicad_pcb'); R=padpos(S+'/reva/kicad/HomeMy_PMU_RevA.kicad_pcb')
ext=json.load(open(W+'rev-a2-layout-280x260/manufacturing/REV_A_EXTERNAL_BOM.json'))
iface=json.load(open(W+'rev-a2-layout-280x260/manufacturing/busbar-pcb-interface.json'))
print('iface keys',list(iface.keys()))
for l in ext['lines']:
    if l['references'][0].startswith('BB'):
        c=l['constraints']; m=re.search(r'\{.*\}',c,re.S)
        try: j=json.loads(m.group(0))
        except Exception as e: print(l['references'],'parse fail',e, c[:200]); continue
        print(l['references'][0],'contact_refs',j.get('contact_refs'))
        for h in j['holes']:
            fn=h['function']; key=fn if '.' in fn else fn+'.1'
            pa=A.get(key) or A.get(fn); pr=R.get(key) or R.get(fn)
            print('    hole',fn,(h['x'],h['y']),'A2 pcb',pa,'rev-a pcb',pr,'=> matches', 'A2' if pa and (h['x'],h['y']) in [tuple(x) for x in pa] else ('REV-A' if pr and (h['x'],h['y']) in [tuple(x) for x in pr] else 'NEITHER'))
