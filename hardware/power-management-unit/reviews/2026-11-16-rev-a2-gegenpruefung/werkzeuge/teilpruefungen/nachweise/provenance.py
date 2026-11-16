import pcbnew as pcb, json, sys, collections
S=sys.argv[1]
W='<SITZUNG>/pmu/hardware/power-management-unit/'
d=json.load(open(W+'rev-a2-layout-280x260/reports/copper-provenance.json'))
def items(path):
    b=pcb.LoadBoard(path); out={}
    for t in b.GetTracks():
        if isinstance(t,pcb.PCB_VIA):
            out[t.m_Uuid.AsString()]=dict(type='PCB_VIA',net=t.GetNetname(),xy=(pcb.ToMM(t.GetPosition().x),pcb.ToMM(t.GetPosition().y)),dia=pcb.ToMM(t.GetWidth(pcb.F_Cu)),drill=pcb.ToMM(t.GetDrillValue()))
        else:
            out[t.m_Uuid.AsString()]=dict(type='PCB_TRACK',net=t.GetNetname(),layer=b.GetLayerName(t.GetLayer()),a=(pcb.ToMM(t.GetStart().x),pcb.ToMM(t.GetStart().y)),b=(pcb.ToMM(t.GetEnd().x),pcb.ToMM(t.GetEnd().y)),w=pcb.ToMM(t.GetWidth()))
    for z in b.Zones():
        o=z.Outline(); pts=[(pcb.ToMM(o.CVertex(i).x),pcb.ToMM(o.CVertex(i).y)) for i in range(o.TotalVertices())]
        out[z.m_Uuid.AsString()]=dict(type='ZONE',net=z.GetNetname(),layer=b.GetLayerName(z.GetLayer()),pts=pts,mt=pcb.ToMM(z.GetMinThickness()),prio=z.GetAssignedPriority())
    return out
A=items(S+'/a2/kicad/HomeMy_PMU_RevA.kicad_pcb'); R=items(S+'/reva/kicad/HomeMy_PMU_RevA.kicad_pcb')
imp={x['target']['uuid']:x for x in d['imported']}; new={x['uuid']:x for x in d['new']}
print('final A2 copper objects',len(A),collections.Counter(v['type'] for v in A.values()))
print('provenance imported',len(imp),'new',len(new),'overlap',len(set(imp)&set(new)))
man=set(imp)|set(new)
print('A2 objects not in provenance',len(set(A)-man),'provenance entries not in A2',len(man-set(A)))
print('record pcb_sha256 field in copper-provenance.json:',d['pcb_sha256'])
# imported: uuid exists in rev-a?
inR=[u for u in imp if u in R]; print('imported uuids present in rev-a PCB',len(inR),'/',len(imp))
src_uuid_same=sum(1 for x in d['imported'] if x['source']['uuid']==x['target']['uuid']); print('source uuid == target uuid',src_uuid_same)
# geometry check: translation
bad=0;tr=collections.Counter();netbad=0
def close(p,q,tol=1e-4): return abs(p[0]-q[0])<tol and abs(p[1]-q[1])<tol
for u,x in imp.items():
    su=x['source']['uuid']
    if su not in R or u not in A: bad+=1; continue
    r=R[su];a=A[u];dx,dy=x['transform']['translation_mm'];rot=x['transform'].get('rotation_deg',0)
    tr[(dx,dy,rot)]+=1
    if r['net']!=a['net'] or r['type']!=a['type']: netbad+=1
    if rot!=0: continue
    if a['type']=='PCB_VIA': ok=close((r['xy'][0]+dx,r['xy'][1]+dy),a['xy']) and r['dia']==a['dia'] and r['drill']==a['drill']
    elif a['type']=='PCB_TRACK': ok=close((r['a'][0]+dx,r['a'][1]+dy),a['a']) and close((r['b'][0]+dx,r['b'][1]+dy),a['b']) and r['w']==a['w'] and r['layer']==a['layer']
    else: ok=len(r['pts'])==len(a['pts']) and all(close((p[0]+dx,p[1]+dy),q) for p,q in zip(r['pts'],a['pts'])) and r['mt']==a['mt']
    if not ok: bad+=1
print('transforms used',tr.most_common(10)); print('imported objects whose final geometry != rev-a geometry + stated translation:',bad,'net/type mismatches',netbad)
# new: none in rev-a?
print('"new" uuids that actually exist in rev-a',len([u for u in new if u in R]))
# widths of new tracks per net class
wn=collections.Counter((A[u]['net'],A[u]['w']) for u in new if u in A and A[u]['type']=='PCB_TRACK')
print('new track count',sum(wn.values()),'distinct nets',len({k[0] for k in wn}))
print('--- the mismatching imported objects')
doc=set()
for k in ['adjustments','geometry_changes']:
    for x in d[k]:
        for key in ['uuid']:
            if key in x: doc.add(x[key])
        for key in ['before','after']:
            if isinstance(x.get(key),dict) and 'uuid' in x[key]: doc.add(x[key]['uuid'])
for u,x in imp.items():
    su=x['source']['uuid']; r=R[su];a=A[u];dx,dy=x['transform']['translation_mm'];rot=x['transform'].get('rotation_deg',0)
    if rot!=0: continue
    if a['type']=='PCB_VIA': ok=close((r['xy'][0]+dx,r['xy'][1]+dy),a['xy'])
    elif a['type']=='PCB_TRACK': ok=close((r['a'][0]+dx,r['a'][1]+dy),a['a']) and close((r['b'][0]+dx,r['b'][1]+dy),a['b']) and r['w']==a['w']
    else: ok=len(r['pts'])==len(a['pts']) and all(close((p[0]+dx,p[1]+dy),q) for p,q in zip(r['pts'],a['pts'])) and r['mt']==a['mt']
    if not ok:
        print(u,a['type'],a['net'],'documented in adjustments/geometry_changes:',u in doc)
        if a['type']=='ZONE': print('    rev-a pts',r['pts'][:6],'-> A2 pts',a['pts'][:6],'transform',(dx,dy),'target record',x['target'].get('outlines_mm'))
        else: print('    rev-a',r,'A2',a,'transform',(dx,dy))
