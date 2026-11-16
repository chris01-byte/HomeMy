import pcbnew, sys, math
PCB='<SITZUNG>/pmu/hardware/power-management-unit/rev-a2-layout-280x260/kicad/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(PCB); mm=pcbnew.ToMM
def padbox(f):
    xs=[];ys=[]
    for p in f.Pads():
        bb=p.GetBoundingBox(); xs+=[mm(bb.GetLeft()),mm(bb.GetRight())]; ys+=[mm(bb.GetTop()),mm(bb.GetBottom())]
    return min(xs),min(ys),max(xs),max(ys)
ref=sys.argv[1]; hx=float(sys.argv[2]); hy=float(sys.argv[3])   # half body size in board axes
f=b.FindFootprintByReference(ref); cx,cy=mm(f.GetPosition().x),mm(f.GetPosition().y)
body=(cx-hx,cy-hy,cx+hx,cy+hy)
print(ref,'centre',cx,cy,'body box',body)
rows=[]
for g in b.GetFootprints():
    if g.GetReference()==ref: continue
    x0,y0,x1,y1=padbox(g)
    dx=max(0,body[0]-x1,x0-body[2]); dy=max(0,body[1]-y1,y0-body[3])
    d=math.hypot(dx,dy)
    if d<float(sys.argv[4]) : rows.append((round(d,3),g.GetReference(),round(dx,3),round(dy,3),(round(x0,2),round(y0,2),round(x1,2),round(y1,2))))
for r in sorted(rows): print('  ',r)
