"""New broad return and explicit SYS branch supply corridors; no tap edits."""
from rebuild import *
import sys
sys.path.insert(0,str(BASE.parent/'rev-a1/scripts'))
sys.path.insert(0,str(BASE/'scripts'))
from cad_operations import zone,rect,corridor,merge_zones
import pcbnew as pcb
HOLD=[]
def main():
    guard();before=sha(BOARD);b=pcb.LoadBoard(str(BOARD));s=pcb.LoadBoard(str(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'))
    originals={t.m_Uuid.AsString() for t in s.GetTracks()};oldzones={z.m_Uuid.AsString() for z in b.Zones()}
    paths=[[(100,70),(100,94.5),(59,94.5),(59,170),(164,170),(163.901,172.559)],
      [(59,112),(47.8425,112)],[(59,125.625),(41.7001,125.625)],
      [(59,141),(56.6777,141)],[(59,154),(41.7001,154)]]
    for pts in paths:corridor(b,'SYS_BUS_P',pts,4,pcb.In2_Cu,5)
    zones=[z for z in b.Zones() if z.m_Uuid.AsString() not in oldzones]
    for z in zones:z.SetMinThickness(pcb.FromMM(1.2));z.SetZoneName('REBUILD/SYS_BRANCH')
    removed=[];counts_before=sum(isinstance(t,pcb.PCB_VIA) and t.GetNetname()=='BATT_N' for t in b.GetTracks())
    for t in list(b.GetTracks()):
        if not isinstance(t,pcb.PCB_VIA) or t.GetNetname()!='BATT_N' or t.GetParentGroup() or t.m_Uuid.AsString() in originals:continue
        if any(z.Outline().Collide(t.GetEffectiveShape(pcb.In2_Cu),pcb.FromMM(.5)) for z in zones):
            removed.append({'uuid':t.m_Uuid.AsString(),'xy_mm':[pcb.ToMM(t.GetPosition().x),pcb.ToMM(t.GetPosition().y)]});b.Remove(t);HOLD.append(t)
    z=zone(b,'BATT_N',rect(3,3,277,218),pcb.B_Cu,0,.5);z.SetMinThickness(pcb.FromMM(1.2));z.SetZoneName('REBUILD/BATT_N_BACKGROUND')
    merge_zones(b);b.BuildConnectivity();f=pcb.ZONE_FILLER(b);f.Fill(b.Zones());b.GetConnectivity().RecalculateRatsnest();pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'cycle-05-branch-supplies.json',{'input_sha256':before,'pcb_sha256':sha(BOARD),'SYS_paths_mm':paths,'SYS_width_mm':4,'SYS_layer':'In2.Cu','clearance_mm':.5,'minimum_fill_mm':1.2,'removed_only_new_BATT_N_vias':removed,'BATT_N_vias_before':counts_before,'BATT_N_vias_after':counts_before-len(removed),'new_return':'B.Cu priority0 background; all separate returns/planes retained','open_connections_after_refill':b.GetConnectivity().GetUnconnectedCount(False),'qualification':'Via removal clears a branch corridor outside MOSFET transfer fields. No original items retired; actual force/thermal checks remain mandatory. No current rating inferred from total via count.'})
    print('SYS branch corridors; removed',len(removed),'new BATT_N vias; opens',b.GetConnectivity().GetUnconnectedCount(False),flush=True)
    return b,s,f
if __name__=='__main__':owners=main()
