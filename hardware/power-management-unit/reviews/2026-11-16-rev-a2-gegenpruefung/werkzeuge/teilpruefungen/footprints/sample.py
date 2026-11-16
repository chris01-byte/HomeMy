import pcbnew, sys, math
PCB='<SITZUNG>/pmu/hardware/power-management-unit/rev-a2-layout-280x260/kicad/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(PCB); mm=pcbnew.ToMM
zones=[z for z in b.Zones() if not z.GetIsRuleArea() and z.IsOnLayer(pcbnew.F_Cu)]
def net_at(x,y):
    out=[]
    v=pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
    for z in zones:
        if z.GetFilledPolysList(pcbnew.F_Cu).Contains(v): out.append('Z:'+z.GetNetname())
    for f in b.GetFootprints():
        for p in f.Pads():
            if p.IsOnLayer(pcbnew.F_Cu) and p.HitTest(v): out.append(f"P:{f.GetReference()}.{p.GetNumber()}:{p.GetNetname()}")
    for t in b.GetTracks():
        if t.Type()!=pcbnew.PCB_VIA_T and t.GetLayer()==pcbnew.F_Cu and t.HitTest(v): out.append('T:'+t.GetNetname())
        if t.Type()==pcbnew.PCB_VIA_T and t.HitTest(v): out.append('V:'+t.GetNetname())
    return out or ['-']
def loc2abs(f,lx,ly):
    cx,cy=mm(f.GetPosition().x),mm(f.GetPosition().y); a=math.radians(f.GetOrientationDegrees())
    return cx+lx*math.cos(a)+ly*math.sin(a), cy-lx*math.sin(a)+ly*math.cos(a)
if __name__=='__main__':
    ref=sys.argv[1]
    f=b.FindFootprintByReference(ref)
    xs=[float(v) for v in sys.argv[2].split(',')]; ys=[float(v) for v in sys.argv[3].split(',')]
    print(ref,'rot',f.GetOrientationDegrees(),' rows=y local, cols=x local:',xs)
    for ly in ys:
        print(f"  y={ly:+.2f}: "+' | '.join(','.join(sorted(set(net_at(*loc2abs(f,lx,ly))))) for lx in xs))
