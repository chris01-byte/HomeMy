import pcbnew, sys, math
PCB='<SITZUNG>/pmu/hardware/power-management-unit/rev-a2-layout-280x260/kicad/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(PCB); mm=pcbnew.ToMM
zones=[z for z in b.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.F_Cu)]
def net_at(x,y):
    out=[]
    v=pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
    for z in zones:
        if z.GetFilledPolysList(pcbnew.F_Cu).Contains(v): out.append(z.GetNetname())
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.IsOnLayer(pcbnew.F_Cu) and p.HitTest(v): out.append(f"{f.GetReference()}.{p.GetNumber()}:{p.GetNetname()}")
    for t in b.GetTracks():
        if t.Type()!=pcbnew.PCB_VIA_T and t.GetLayer()==pcbnew.F_Cu and t.HitTest(v): out.append('trk:'+t.GetNetname())
    return out or ['-none-']
for i in range(1,11):
    ref=f"Q{i}"; f=b.FindFootprintByReference(ref)
    cx,cy=mm(f.GetPosition().x),mm(f.GetPosition().y); rot=f.GetOrientationDegrees()
    drain=[p.GetNetname() for p in f.Pads() if p.GetNumber()=='13'][0]
    src=[p.GetNetname() for p in f.Pads() if p.GetNumber()=='2'][0]
    res=[]
    for d in (5.7,6.05,6.3,6.6):
        for sgn in (-1,1):
            # local x axis -> board axis: rot +-90 => board y
            a=math.radians(rot)
            # KiCad: board = c + (lx*cos(a)+ly*sin(a), -lx*sin(a)+ly*cos(a))
            lx=sgn*d; ly=0
            x=cx+lx*math.cos(a)+ly*math.sin(a); y=cy-lx*math.sin(a)+ly*math.cos(a)
            res.append(f"{sgn*d:+.2f}:{','.join(net_at(x,y))}")
    print(ref,'rot',rot,'drain',drain,'src',src,'|',' '.join(res))
