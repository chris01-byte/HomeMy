"""Explicit local SYS capacitor pickups with regular 0.8/0.4-mm vias."""
from rebuild import *
import sys
sys.path.insert(0,str(BASE/'scripts'))
from cad_operations import zone,rect,corridor,merge_zones
import pcbnew as pcb
HOLD=[]
def main():
    guard();b=pcb.LoadBoard(str(BOARD));before=sha(BOARD);existing={z.m_Uuid.AsString() for z in b.Zones()}
    for y,top in [(129,125.625),(157,154)]:
        z=zone(b,'SYS_BUS_P',rect(44.6,y-.7,47.2,y+.7),pcb.F_Cu,5,.5);z.SetMinThickness(pcb.FromMM(1.2))
        corridor(b,'SYS_BUS_P',[(46.5,top),(46.5,y)],4,pcb.In2_Cu,5)
    additions=[z for z in b.Zones() if z.m_Uuid.AsString() not in existing]
    for z in additions:z.SetMinThickness(pcb.FromMM(1.2))
    source=pcb.LoadBoard(str(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'));oldids={t.m_Uuid.AsString() for t in source.GetTracks()}
    removed=[]
    for t in list(b.GetTracks()):
        if isinstance(t,pcb.PCB_VIA) and t.GetNetname()=='BATT_N' and not t.GetParentGroup() and t.m_Uuid.AsString() not in oldids and any(z.Outline().Collide(t.GetEffectiveShape(z.GetLayer()),pcb.FromMM(.5)) for z in additions):
            removed.append(t.m_Uuid.AsString());b.Remove(t);HOLD.append(t)
    vias=[]
    for y in [129,157]:
        v=pcb.PCB_VIA(b);v.SetPosition(pcb.VECTOR2I(pcb.FromMM(46.5),pcb.FromMM(y)));v.SetWidth(pcb.FromMM(.8));v.SetDrill(pcb.FromMM(.4));v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetNet(b.FindNet('SYS_BUS_P'));v.SetLocked(True);b.Add(v);HOLD.append(v);vias.append(v.m_Uuid.AsString())
    merge_zones(b);b.BuildConnectivity();f=pcb.ZONE_FILLER(b);f.Fill(b.Zones());pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'cycle-05-sys-cap-patches.json',{'input_sha256':before,'pcb_sha256':sha(BOARD),'retired_new_BATT_N_vias':removed,'new_SYS_vias':vias,'diameter_drill_mm':[.8,.4],'pickup_positions_mm':[[46.5,129],[46.5,157]]})
    print('SYS capacitor pickups; retired',len(removed),'new return vias',flush=True)
    return b,source,f
if __name__=='__main__':owners=main()
