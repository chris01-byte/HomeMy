import pcbnew, sys, math, collections
PCB='<SITZUNG>/pmu/hardware/power-management-unit/rev-a2-layout-280x260/kicad/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(PCB); mm=pcbnew.ToMM
zonesF=[z for z in b.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.F_Cu)]
tracksF=[t for t in b.GetTracks() if t.Type()!=pcbnew.PCB_VIA_T and t.GetLayer()==pcbnew.F_Cu]
vias=[t for t in b.GetTracks() if t.Type()==pcbnew.PCB_VIA_T]
def loc2abs(f,lx,ly):
    cx,cy=mm(f.GetPosition().x),mm(f.GetPosition().y); a=math.radians(f.GetOrientationDegrees())
    return cx+lx*math.cos(a)+ly*math.sin(a), cy-lx*math.sin(a)+ly*math.cos(a)
def under(ref,hx,hy,step=0.1,ox=0.0,oy=0.0):
    f=b.FindFootprintByReference(ref)
    corners=[loc2abs(f,ox+sx*hx,oy+sy*hy) for sx in(-1,1) for sy in(-1,1)]
    x0=min(c[0] for c in corners); x1=max(c[0] for c in corners); y0=min(c[1] for c in corners); y1=max(c[1] for c in corners)
    def inter(bb,m=0.0):
        return mm(bb.GetRight())>=x0-m and mm(bb.GetLeft())<=x1+m and mm(bb.GetBottom())>=y0-m and mm(bb.GetTop())<=y1+m
    res=collections.defaultdict(set)
    for t in tracksF:
        if inter(t.GetBoundingBox()): res['track'].add(t.GetNetname())
    for v in vias:
        if inter(v.GetBoundingBox()): res['via'].add(v.GetNetname())
    for g in b.GetFootprints():
        for p in g.Pads():
            if p.IsOnLayer(pcbnew.F_Cu) and inter(p.GetBoundingBox()):
                res['pad'].add(f"{g.GetReference()}.{p.GetNumber()}:{p.GetNetname()}" if g.GetReference()!=ref else f"self:{p.GetNetname()}")
    zc=collections.Counter()
    nx=max(1,int(round(2*hx/step))); ny=max(1,int(round(2*hy/step)))
    for i in range(nx+1):
        for j in range(ny+1):
            px,py=loc2abs(f,ox-hx+2*hx*i/nx,oy-hy+2*hy*j/ny)
            v=pcbnew.VECTOR2I(pcbnew.FromMM(px),pcbnew.FromMM(py))
            for z in zonesF:
                if z.GetFilledPolysList(pcbnew.F_Cu).Contains(v): zc[z.GetNetname()]+=1
    res['zone']=dict(zc)
    return {k:(sorted(v) if isinstance(v,set) else v) for k,v in res.items()}
if __name__=='__main__':
    for spec in sys.argv[1:]:
        parts=spec.split(':'); ref=parts[0]; hx=float(parts[1]); hy=float(parts[2])
        print(ref,f"F.Cu within local ±{hx} x ±{hy}:",under(ref,hx,hy,0.2))
