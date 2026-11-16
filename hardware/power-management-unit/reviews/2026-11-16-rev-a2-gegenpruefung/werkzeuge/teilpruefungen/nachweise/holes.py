import pcbnew as pcb, sys, collections, math
import numpy as np
S=sys.argv[1]
b=pcb.LoadBoard(S+'/a2/kicad/HomeMy_PMU_RevA.kicad_pcb')
H=[]
for f in b.GetFootprints():
    for p in f.Pads():
        d=p.GetDrillSize()
        if d.x>0: H.append((pcb.ToMM(p.GetPosition().x),pcb.ToMM(p.GetPosition().y),pcb.ToMM(d.x),f'{f.GetReference()}.{p.GetNumber()}',p.GetNetname(),'NPTH' if p.GetAttribute()==pcb.PAD_ATTRIB_NPTH else 'PTH'))
for t in b.GetTracks():
    if isinstance(t,pcb.PCB_VIA): H.append((pcb.ToMM(t.GetPosition().x),pcb.ToMM(t.GetPosition().y),pcb.ToMM(t.GetDrillValue()),'via',t.GetNetname(),'PTH'))
print('holes',len(H))
xy=np.array([[h[0],h[1]] for h in H]); r=np.array([h[2]/2 for h in H])
from itertools import combinations
# brute force with numpy
best=[]
for i in range(len(H)):
    d=np.hypot(xy[i+1:,0]-xy[i,0],xy[i+1:,1]-xy[i,1])-r[i+1:]-r[i]
    if len(d)==0: continue
    idx=np.where(d<0.35)[0]
    for j in idx: best.append((float(d[j]),i,i+1+int(j)))
best.sort()
print('hole pairs with edge-to-edge web < 0.35 mm:',len(best))
hist=collections.Counter(round(x[0],2) for x in best); print('web histogram (mm: count)',sorted(hist.items())[:20])
for w,i,j in best[:12]: print('   web %.3f'%w,H[i][2:],'@(%.2f,%.2f)'%(H[i][0],H[i][1]),'<->',H[j][2:],'@(%.2f,%.2f)'%(H[j][0],H[j][1]))
# coincident
co=[x for x in best if x[0]<0]; print('overlapping holes',len(co))
# edge distance
mins=[(min(h[0]-h[2]/2,280-h[0]-h[2]/2,h[1]-h[2]/2,260-h[1]-h[2]/2),h) for h in H]; mins.sort(key=lambda x:x[0])
print('min hole-edge to board-edge',[(round(m,3),h[2:]) for m,h in mins[:6]])
ds=b.GetDesignSettings()
print('design min: hole2hole',pcb.ToMM(ds.m_HoleToHoleMin),'hole clearance',pcb.ToMM(ds.m_HoleClearance),'min through hole',pcb.ToMM(ds.m_MinThroughDrill),'min via',pcb.ToMM(ds.m_ViasMinSize),'annular',pcb.ToMM(ds.m_ViasMinAnnularWidth),'min track',pcb.ToMM(ds.m_TrackMinWidth),'min clearance',pcb.ToMM(ds.m_MinClearance),'edge clearance',pcb.ToMM(ds.m_CopperEdgeClearance))
# pad property for press-fit
props=collections.Counter()
for f in b.GetFootprints():
    for p in f.Pads():
        if p.GetDrillSize().x>0: props[(pcb.ToMM(p.GetDrillSize().x),p.GetProperty())]+=1
print('pad fabrication property by drill',dict(props)); print([n for n in dir(pcb) if n.startswith('PAD_PROP')])
for ref in ['J1','U10','U30','BC1','NT1']:
    f=b.FindFootprintByReference(ref); print(ref,f.GetFPID().GetUniStringLibId(),f.GetValue(),[ (p.GetNumber(),pcb.ToMM(p.GetDrillSize().x),pcb.ToMM(p.GetSize(pcb.F_Cu).x),pcb.ToMM(p.GetSize(pcb.F_Cu).y)) for p in f.Pads()][:14])
# stackup
st=ds.GetStackupDescriptor()
for it in st.GetList():
    try: print('  stack',it.GetLayerName(),it.GetTypeName(),pcb.ToMM(it.GetThickness()),it.GetMaterial())
    except Exception as e: print('  stack err',e)
print('board thickness',pcb.ToMM(ds.GetBoardThickness()), 'finish',st.m_FinishType, 'castellated',st.m_CastellatedPads,'edge plating',st.m_EdgePlating, 'impedance',st.m_HasDielectricConstrains)
