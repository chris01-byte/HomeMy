"""First targeted correction of diagnosed new-power findings; no rule edits."""
from rebuild import *
import sys,collections
sys.path.insert(0,str(BASE.parent/'rev-a1/scripts'))
from bounded_seed import Screen
from cad_operations import zone,rect,merge_zones,corridor
import pcbnew as pcb
HOLD=[]
def p(x,y):return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
def xy(v):return [pcb.ToMM(v.x),pcb.ToMM(v.y)]
def main():
    guard();b=pcb.LoadBoard(str(BOARD));inputsha=sha(BOARD)
    r=json.loads((OUT/'cycle-02-power-drc.json').read_text(encoding='utf-8'))
    bad={i['uuid'] for v in r['violations'] if v['type']=='hole_clearance' for i in v['items'] if i['description'].startswith('Via')}
    removed=[]
    for t in list(b.GetTracks()):
        if t.m_Uuid.AsString() in bad:
            assert isinstance(t,pcb.PCB_VIA) and t.GetNetname()=='BATT_N' and not t.GetParentGroup()
            b.Remove(t);HOLD.append(t);removed.append(t.m_Uuid.AsString())
    for net,poly in [('ARM_L_N',rect(260,139,275,153)),('ARM_R_N',rect(260,169,275,183))]:
        for l in [pcb.F_Cu,pcb.B_Cu]:
            z=zone(b,net,poly,l,4,.5);z.SetMinThickness(pcb.FromMM(1.2))
    # The eFuse's BATT_N reference pad was isolated by an inherited PC_OVP
    # signal escape. A dedicated inner return and native source-dimension tap
    # remain required; do not remove/reclassify the signal or reduce the rule.
    # Expand the continuous quiet reference; distinct chopper-reference zones
    # retain higher priority and meet CHOPPER_N only through NT10.
    zone(b,'LOGIC_GND',rect(3,3,277,218),pcb.In1_Cu,0,.3)
    merge_zones(b);b.BuildConnectivity();filler=pcb.ZONE_FILLER(b);filler.Fill(b.Zones())
    screen=Screen(b);stitches=[];failed=[]
    for f in b.GetFootprints():
        for pad in f.Pads():
            net=pad.GetNetname()
            if net not in ['LOGIC_GND','CHOP_GND'] or pad.GetDrillSize().x:continue
            # Existing copper to a connected reference is preserved. Additional
            # local stitches have explicit pad identity and final-layer audit.
            x,y=xy(pad.GetPosition());done=False
            for dx,dy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1),(1.5,0),(-1.5,0),(0,1.5),(0,-1.5)]:
                X,Y=x+dx,y+dy
                if not any(z.GetNetname()==net and z.GetLayer()==pcb.In1_Cu and z.GetFilledPolysList(pcb.In1_Cu).Contains(p(X,Y),-1,0,True) for z in b.Zones()):continue
                v=pcb.PCB_VIA(b);v.SetPosition(p(X,Y));v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetWidth(pcb.FromMM(.6));v.SetDrill(pcb.FromMM(.3));v.SetNet(b.FindNet(net));v.SetLocked(True)
                t=pcb.PCB_TRACK(b);t.SetStart(p(x,y));t.SetEnd(p(X,Y));t.SetLayer(pad.GetLayer());t.SetWidth(pcb.FromMM(.2));t.SetNet(b.FindNet(net));t.SetLocked(True);HOLD.extend([v,t])
                if screen.reason(v) or screen.reason(t):continue
                b.Add(v);b.Add(t);screen.index(v);screen.index(t);stitches.append({'pad':f.GetReference()+'.'+pad.GetNumber(),'net':net,'via_xy_mm':[X,Y],'via_uuid':v.m_Uuid.AsString()});done=True;break
            if not done:failed.append(f.GetReference()+'.'+pad.GetNumber())
    b.BuildConnectivity();filler.Fill(b.Zones());pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'cycle-03-power-corrections.json',{'input_sha256':inputsha,'output_sha256':sha(BOARD),'removed_new_keepout_conflicting_vias':removed,'reference_stitches':stitches,'reference_stitch_candidates_unresolved':failed,'rules_unchanged':True})
    print('Removed hole conflicts',len(removed),'added ground stitches',len(stitches),'unresolved',failed,flush=True)
    return b,filler,screen
if __name__=='__main__':owners=main()
