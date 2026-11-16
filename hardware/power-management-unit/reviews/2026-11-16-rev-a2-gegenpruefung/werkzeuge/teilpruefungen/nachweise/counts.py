import pcbnew as pcb, json, collections, sys
S=sys.argv[1]
b=pcb.LoadBoard(S+'/a2/kicad/HomeMy_PMU_RevA.kicad_pcb')
fps=list(b.GetFootprints())
pads=[p for f in fps for p in f.Pads()]
tracks=list(b.GetTracks())
vias=[t for t in tracks if isinstance(t,pcb.PCB_VIA)]
arcs=[t for t in tracks if isinstance(t,pcb.PCB_ARC)]
segs=[t for t in tracks if not isinstance(t,pcb.PCB_VIA) and not isinstance(t,pcb.PCB_ARC)]
print('footprints',len(fps),'pads',len(pads),'vias',len(vias),'segments',len(segs),'arcs',len(arcs),'tracks total',len(tracks))
print('nets (incl. net 0)',b.GetNetCount(),'-> real nets',b.GetNetCount()-1)
print('copper layers',b.GetCopperLayerCount())
print('zones',len(list(b.Zones())))
# pads by attribute
c=collections.Counter()
for p in pads:
    c[{pcb.PAD_ATTRIB_PTH:'PTH',pcb.PAD_ATTRIB_SMD:'SMD',pcb.PAD_ATTRIB_CONN:'CONN',pcb.PAD_ATTRIB_NPTH:'NPTH'}[p.GetAttribute()]]+=1
print('pad attrs',dict(c))
# holes
holes=collections.Counter()
for p in pads:
    d=p.GetDrillSize()
    if d.x>0:
        shape='slot' if d.x!=d.y else 'round'
        holes[('pad',{pcb.PAD_ATTRIB_PTH:'PTH',pcb.PAD_ATTRIB_NPTH:'NPTH'}.get(p.GetAttribute(),'?'),pcb.ToMM(d.x),pcb.ToMM(d.y),shape)]+=1
for v in vias:
    holes[('via','PTH',pcb.ToMM(v.GetDrillValue()),pcb.ToMM(v.GetDrillValue()),'round',v.GetViaType())]+=1
for k,v in sorted(holes.items(),key=lambda kv:str(kv[0])): print('  hole',k,v)
pth=sum(v for k,v in holes.items() if k[1]=='PTH'); npth=sum(v for k,v in holes.items() if k[1]=='NPTH')
print('PTH total',pth,'NPTH total',npth)
# which footprints own 1.475 holes / 3.2 holes
own=collections.defaultdict(collections.Counter)
for f in fps:
    for p in f.Pads():
        d=p.GetDrillSize()
        if d.x>0: own[(pcb.ToMM(d.x),{pcb.PAD_ATTRIB_PTH:'PTH',pcb.PAD_ATTRIB_NPTH:'NPTH'}.get(p.GetAttribute(),'?'))][f.GetReference()]+=1
for k in sorted(own): print('  drill',k,'count',sum(own[k].values()),'refs',dict(sorted(own[k].items(),key=lambda kv:kv[0]))) if len(own[k])<40 else print('  drill',k,'count',sum(own[k].values()),'nrefs',len(own[k]))
# via sizes
vc=collections.Counter((pcb.ToMM(v.GetWidth(pcb.F_Cu)),pcb.ToMM(v.GetDrillValue()),v.GetViaType()) for v in vias)
print('via size/drill/type',dict(vc))
# footprint attribute classes
fa=collections.Counter()
for f in fps:
    a=f.GetAttributes()
    kind='SMD' if a&pcb.FP_SMD else ('THT' if a&pcb.FP_THROUGH_HOLE else 'other')
    fa[(kind,'excl_pos' if f.IsExcludedFromPosFiles() else 'pos','excl_bom' if f.IsExcludedFromBOM() else 'bom','DNP' if f.IsDNP() else 'fit', b.GetLayerName(f.GetLayer()))]+=1
for k,v in sorted(fa.items()): print('  fp class',k,v)
tp=[f.GetReference() for f in fps if f.GetReference().startswith('TP')]
print('testpoints',len(tp)); print('mounting H',[f.GetReference() for f in fps if f.GetReference().startswith('H')])
# board outline bbox
bb=b.GetBoardEdgesBoundingBox()
print('edge bbox mm',pcb.ToMM(bb.GetX()),pcb.ToMM(bb.GetY()),pcb.ToMM(bb.GetWidth()),pcb.ToMM(bb.GetHeight()))
edges=[d for d in b.GetDrawings() if d.GetLayer()==pcb.Edge_Cuts]
for d in edges: print('   edge',d.GetShapeStr() if hasattr(d,'GetShapeStr') else type(d).__name__, pcb.ToMM(d.GetStart().x),pcb.ToMM(d.GetStart().y),pcb.ToMM(d.GetEnd().x),pcb.ToMM(d.GetEnd().y),'w',pcb.ToMM(d.GetWidth()))
b.BuildConnectivity(); print('unconnected',b.GetConnectivity().GetUnconnectedCount(False))
# title block
tb=b.GetTitleBlock(); print('title',tb.GetTitle(),'| rev',tb.GetRevision(),'| date',tb.GetDate(),'| company',tb.GetCompany(),'| comments',[tb.GetComment(i) for i in range(4)])
