import pcbnew, sys, math
PCB='<SITZUNG>/pmu/hardware/power-management-unit/rev-a2-layout-280x260/kicad/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(PCB); mm=pcbnew.ToMM
def abs2loc(f,x,y):
    cx,cy=mm(f.GetPosition().x),mm(f.GetPosition().y); a=math.radians(f.GetOrientationDegrees())
    dx,dy=x-cx,y-cy
    # inverse of: X=lx*cos+ly*sin ; Y=-lx*sin+ly*cos
    return dx*math.cos(a)-dy*math.sin(a), dx*math.sin(a)+dy*math.cos(a)
ref=sys.argv[1]; hx=float(sys.argv[2]); hy=float(sys.argv[3])
f=b.FindFootprintByReference(ref)
print('##',ref,'local frame; items within ±%.2f x ±%.2f (F.Cu tracks, all vias)'%(hx,hy))
for t in b.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T:
        lx,ly=abs2loc(f,mm(t.GetPosition().x),mm(t.GetPosition().y)); r=mm(t.GetWidth(pcbnew.F_Cu))/2
        if abs(lx)<=hx+r and abs(ly)<=hy+r: print(f"   VIA {t.GetNetname():<16} local ({lx:+.3f},{ly:+.3f}) dia {2*r:.2f} drill {mm(t.GetDrillValue()):.2f}")
    elif t.GetLayer()==pcbnew.F_Cu:
        s=abs2loc(f,mm(t.GetStart().x),mm(t.GetStart().y)); e=abs2loc(f,mm(t.GetEnd().x),mm(t.GetEnd().y)); w=mm(t.GetWidth())
        if min(s[0],e[0])<=hx and max(s[0],e[0])>=-hx and min(s[1],e[1])<=hy and max(s[1],e[1])>=-hy:
            print(f"   TRK {t.GetNetname():<16} local ({s[0]:+.3f},{s[1]:+.3f})->({e[0]:+.3f},{e[1]:+.3f}) w {w:.2f}")
