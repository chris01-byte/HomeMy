"""Read-only diagnostic for isolated power-plane islands."""
import pcbnew as p
from configure_power_rules import CAD, PROJECT
from build_board import force_exit
b=p.LoadBoard(str(CAD/(PROJECT+'.kicad_pcb')))
for z in b.Zones():
    if z.GetNetname()!='BATT_N' or z.GetIsRuleArea():continue
    q=z.GetFilledPolysList(z.GetLayer())
    print(b.GetLayerName(z.GetLayer()),q.OutlineCount(),flush=True)
    for i in range(q.OutlineCount()):
        pts=[q.COutline(i).CPoint(k) for k in range(q.COutline(i).PointCount())]
        bbox=[p.ToMM(min(v.x for v in pts)),p.ToMM(min(v.y for v in pts)),p.ToMM(max(v.x for v in pts)),p.ToMM(max(v.y for v in pts))]
        inside=[(p.ToMM(t.GetPosition().x),p.ToMM(t.GetPosition().y)) for t in b.GetTracks() if isinstance(t,p.PCB_VIA) and t.GetNetname()=='BATT_N' and q.Contains(t.GetPosition(),i,0,True)]
        print(i,bbox,'vias',len(inside),inside if len(inside)<10 else '',flush=True)
force_exit(0)
