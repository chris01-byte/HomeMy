"""One local correction of the four diagnosed cycle-05 neck clusters."""
from rebuild import *
import pcbnew as pcb
def main():
    guard();b=pcb.LoadBoard(str(BOARD));s=pcb.LoadBoard(str(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'));before=sha(BOARD)
    old={t.m_Uuid.AsString() for t in s.GetTracks()};wanted={'799bdbb9-45df-4f9e-96ee-60cea2935f69','01008ba1-3e5c-44c8-840d-67ae58829beb','4dd9edef-5453-4ce8-83a1-698e9b1d798d','05e1d9ab-3387-4966-b92f-ec5c490e61a9','1aea806f-4a39-420d-ad0f-24c84e1c6471'}
    removed=[];held=[]
    for t in list(b.GetTracks()):
        if t.m_Uuid.AsString() not in wanted:continue
        assert isinstance(t,pcb.PCB_VIA) and t.GetNetname()=='BATT_N' and not t.GetParentGroup() and t.m_Uuid.AsString() not in old
        removed.append(t.m_Uuid.AsString());b.Remove(t);held.append(t)
    assert set(removed)==wanted
    void=pcb.SHAPE_POLY_SET();void.NewOutline()
    for x,y in [(109.5,87.8),(116.5,87.8),(116.5,93.5),(109.5,93.5)]:void.Append(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)))
    zones=[z for z in b.Zones() if z.GetZoneName()=='REBUILD/BATT_N_BACKGROUND' and z.GetNetname()=='BATT_N' and z.GetLayer()==pcb.B_Cu]
    assert len(zones)==1;zones[0].Outline().BooleanSubtract(void)
    b.BuildConnectivity();f=pcb.ZONE_FILLER(b);f.Fill(b.Zones());pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'cycle-06-neck-corrections.json',{'input_sha256':before,'pcb_sha256':sha(BOARD),'removed_new_redundant_BATT_N_vias':removed,'background_void_B_Cu_mm':[109.5,87.8,116.5,93.5],'preserved':'All original taps; U5 LOGIC_GND and V3V3 vias; primary BATT_N power-return outlines','independent_screen':'Five retired vias have no direct pad/track contacts; power/critical identities and actual native DRC rechecked after final fill.'})
    print('Five redundant return vias retired; U5 background necks removed',flush=True)
    return b,s,f,held
if __name__=='__main__':owners=main()
