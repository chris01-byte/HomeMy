"""One correction of the three cycle-03 neck findings; original rules retained."""
from rebuild import *
import pcbnew as pcb
def main():
    guard();before=sha(BOARD);b=pcb.LoadBoard(str(BOARD));fps={f.GetReference():f for f in b.GetFootprints()}
    old=fps['TP6'].GetPosition();oldxy=[pcb.ToMM(old.x),pcb.ToMM(old.y)]
    assert oldxy==[44,152]
    fps['TP6'].SetPosition(pcb.VECTOR2I(pcb.FromMM(92),pcb.FromMM(74)))
    uid='94458d91-04bf-462c-a9a9-1272985ba913';v=next(t for t in b.GetTracks() if t.m_Uuid.AsString()==uid)
    assert isinstance(v,pcb.PCB_VIA) and v.GetNetname()=='BATT_N' and not v.GetParentGroup()
    b.Remove(v);b.BuildConnectivity();f=pcb.ZONE_FILLER(b);f.Fill(b.Zones());pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'cycle-04-neck-corrections.json',{'input_sha256':before,'output_sha256':sha(BOARD),'TP6':{'from_mm':oldxy,'to_mm':[92,74],'reason':'Full pad overlap with broad SYS field and clear 3mm probe access; no inherited anchor moved'},'retired_new_via':uid,'reason':'No direct pad/track contacts; neighboring vias at35.6/151.2 and35.6/154.4 join same broad F/B return polygons','rules_unchanged':True})
    print('TP6 moved; one redundant new via removed',flush=True)
    return b,v,f
if __name__=='__main__':owners=main()
