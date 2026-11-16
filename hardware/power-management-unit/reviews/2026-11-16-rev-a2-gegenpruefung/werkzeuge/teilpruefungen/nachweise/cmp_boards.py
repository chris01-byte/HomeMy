import pcbnew, sys, json, collections
S=sys.argv[1]
def load(p):
    b=pcbnew.LoadBoard(p)
    fps={}
    for f in b.GetFootprints():
        ref=f.GetReference()
        pads=[]
        for p in f.Pads():
            pads.append(dict(num=p.GetNumber(),net=p.GetNetname(),uuid=p.m_Uuid.AsString(),
                             attr=p.GetAttribute(),drill=(p.GetDrillSize().x,p.GetDrillSize().y),
                             size=(p.GetSize(pcbnew.F_Cu).x if hasattr(p,'GetSize') else 0),
                             shape=p.GetShape(pcbnew.F_Cu) if True else None,
                             pinfn=p.GetPinFunction(),pintype=p.GetPinType(),
                             layers=sorted(p.GetLayerSet().Seq()) if hasattr(p.GetLayerSet(),'Seq') else None,
                             local=(p.GetFPRelativePosition().x,p.GetFPRelativePosition().y) if hasattr(p,'GetFPRelativePosition') else None))
        d=dict(ref=ref,value=f.GetValue(),fpid=f.GetFPID().GetUniStringLibId() if hasattr(f.GetFPID(),'GetUniStringLibId') else str(f.GetFPID().GetLibItemName()),
               uuid=f.m_Uuid.AsString(),dnp=f.IsDNP(),excl_bom=f.IsExcludedFromBOM(),excl_pos=f.IsExcludedFromPosFiles(),
               attrs=f.GetAttributes(),layer=b.GetLayerName(f.GetLayer()),pads=pads,
               path=f.GetPath().AsString(),sheetfile=f.GetSheetfile(),sheetname=f.GetSheetname(),
               fields={fld.GetName():fld.GetText() for fld in f.GetFields()})
        assert ref not in fps, ref
        fps[ref]=d
    return b,fps
ba,A=load(S+'/reva/kicad/HomeMy_PMU_RevA.kicad_pcb')
bb,B=load(S+'/a2/kicad/HomeMy_PMU_RevA.kicad_pcb')
print('rev-a footprints',len(A),'A2 footprints',len(B))
print('refs only rev-a',sorted(set(A)-set(B)),'only A2',sorted(set(B)-set(A)))
issues=collections.Counter(); detail=[]
for ref in sorted(set(A)&set(B)):
    a,b=A[ref],B[ref]
    for k in ['value','fpid','uuid','dnp','excl_bom','excl_pos','attrs','layer','path','sheetfile','sheetname','fields']:
        if a[k]!=b[k]:
            issues[k]+=1; detail.append((ref,k,a[k] if k!='fields' else {x:(a[k].get(x),b[k].get(x)) for x in set(a[k])|set(b[k]) if a[k].get(x)!=b[k].get(x)},b[k] if k!='fields' else ''))
    if len(a['pads'])!=len(b['pads']):
        issues['padcount']+=1; detail.append((ref,'padcount',len(a['pads']),len(b['pads']))); continue
    pa={p['uuid']:p for p in a['pads']}; pb={p['uuid']:p for p in b['pads']}
    if set(pa)!=set(pb):
        issues['pad_uuid_set']+=1; detail.append((ref,'pad_uuid_set'))
        # fallback: by order
        for x,y in zip(a['pads'],b['pads']):
            for k in ['num','net','attr','drill','size','shape','pinfn','pintype','layers','local']:
                if x[k]!=y[k]: issues['pad_'+k]+=1; detail.append((ref,x['num'],k,x[k],y[k]))
    else:
        for u in pa:
            x,y=pa[u],pb[u]
            for k in ['num','net','attr','drill','size','shape','pinfn','pintype','layers','local']:
                if x[k]!=y[k]: issues['pad_'+k]+=1; detail.append((ref,x['num'],k,x[k],y[k]))
print('issue counts',dict(issues))
for d in detail[:60]: print('  ',d)
na=sum(len(a['pads']) for a in A.values()); nb=sum(len(a['pads']) for a in B.values())
print('pads rev-a',na,'pads A2',nb)
print('nets rev-a',ba.GetNetCount(),'A2',bb.GetNetCount())
neta={n for n in ba.GetNetsByName().keys()}; netb={n for n in bb.GetNetsByName().keys()}
neta={str(n) for n in neta}; netb={str(n) for n in netb}
print('net names equal',neta==netb, 'only a',sorted(neta-netb)[:10],'only b',sorted(netb-neta)[:10])
print('DNP A2',sorted(r for r,b in B.items() if b['dnp']))
print('excl_bom A2',sorted(r for r,b in B.items() if b['excl_bom']))
print('excl_pos A2',len([r for r,b in B.items() if b['excl_pos']]))
json.dump(B,open(S+'/a2_fps.json','w'),indent=1,default=str)
json.dump(A,open(S+'/reva_fps.json','w'),indent=1,default=str)
