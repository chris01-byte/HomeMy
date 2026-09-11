"""Two explicitly located logic supplies, preserving expanded BATT_N corridors.

Local pad fanout examines a finite list once; no global routing/search/optimizer.
"""
from rebuild import *
import sys,math
sys.path.insert(0,str(BASE.parent/'rev-a1/scripts'));sys.path.insert(0,str(BASE/'scripts'))
from finish_280_routes import Controlled
from cad_operations import zone,rect
import pcbnew as pcb
def main():
    guard();b=pcb.LoadBoard(str(BOARD));before=sha(BOARD);c=Controlled(b);F,B,I2=pcb.F_Cu,pcb.B_Cu,pcb.In2_Cu
    c.route('V3V3 source array','V3V3',[
      (['U12.2',(223,168)],.8,F),([(223,166.4),(223,168),(223,169.6)],.8,F)],[(p,.8,.4) for p in [(223,166.4),(223,168),(223,169.6)]])
    c.route('ESP32 supply pickup','V3V3',[(['U10.2',(261.1,205.49),(262.3,205.49)],.5,F)],[(p,.8,.4) for p in [(261.1,205.49),(262.3,205.49)]])
    c.route('AON source pickup','AON_3V3',[(['U15.5','C210.1',(128.0875,161.75)],.4,F)],[((128.0875,161.75),.6,.3)])
    if not all(r['adopted'] for r in c.records):
        write(OUT/'cycle-05-logic-supply-rejected.json',{'pcb_sha256':before,'recipes':c.records,'saved':False});return b,c
    supply=zone(b,'V3V3',rect(3,3,277,218),I2,0,.3);supply.SetMinThickness(pcb.FromMM(.5));supply.SetZoneName('REBUILD/V3V3_LOGIC_DISTRIBUTION')
    aon=zone(b,'AON_3V3',rect(15,143,217,210),B,2,.3);aon.SetMinThickness(pcb.FromMM(.5));aon.SetZoneName('REBUILD/AON_LOGIC_DISTRIBUTION')
    avoided=[]
    for z in list(b.Zones()):
        if z.GetNetname()=='BATT_N' and z.GetLayer()==B and z.GetAssignedPriority()>=1:
            poly=z.Outline().CloneDropTriangulation();poly.Inflate(pcb.FromMM(.6),pcb.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcb.FromMM(.01));aon.Outline().BooleanSubtract(poly);avoided.append(z.m_Uuid.AsString())
    b.BuildConnectivity();filler=pcb.ZONE_FILLER(b);filler.Fill(b.Zones())
    stitches=[];blocked=[];owners=[]
    offsets=[(dx,dy) for r in [1,1.5,2,2.5] for dx,dy in [(r,0),(-r,0),(0,r),(0,-r),(r,r),(-r,r),(r,-r),(-r,-r)]]
    for f in b.GetFootprints():
        for pad in f.Pads():
            net=pad.GetNetname()
            if net not in ['V3V3','AON_3V3'] or pad.GetDrillSize().x:continue
            target=supply if net=='V3V3' else aon;layer=I2 if net=='V3V3' else B
            # Native/source local copper stays; additional finite pickups join
            # each physical supply pad to the already source-anchored plane.
            x,y=pcb.ToMM(pad.GetPosition().x),pcb.ToMM(pad.GetPosition().y);success=False
            width=.4 if min(pcb.ToMM(pad.GetSize().x),pcb.ToMM(pad.GetSize().y))>=.75 else .2
            for dx,dy in offsets:
                vxy=(x+dx,y+dy)
                if not all(target.GetFilledPolysList(layer).Contains(pcb.VECTOR2I(pcb.FromMM(vxy[0]+a),pcb.FromMM(vxy[1]+d)),-1,0,True) for a,d in [(0,0),(.5,0),(-.5,0),(0,.5),(0,-.5)]):continue
                v=c.via(net,vxy,.6,.3);t=c.segment(net,(x,y),vxy,width,F)
                if c.screen.reason(v) or c.screen.reason(t):continue
                b.Add(v);b.Add(t);c.screen.index(v);c.screen.index(t);stitches.append({'pad':f.GetReference()+'.'+pad.GetNumber(),'pad_uuid':pad.m_Uuid.AsString(),'net':net,'via_uuid':v.m_Uuid.AsString(),'xy_mm':vxy,'fanout_width_mm':width});success=True;break
            if not success:blocked.append(f.GetReference()+'.'+pad.GetNumber())
    b.BuildConnectivity();filler.Fill(b.Zones());b.GetConnectivity().RecalculateRatsnest();pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'cycle-05-logic-supplies.json',{'input_sha256':before,'pcb_sha256':sha(BOARD),'source_recipes':c.records,'BATT_N_outlines_preserved_with_06mm_margin':avoided,'stitches':stitches,'unresolved_local_pickups':blocked,'candidate_offsets_per_pad':len(offsets),'open_connections':b.GetConnectivity().GetUnconnectedCount(False),'limitations':'Connection/DRC and actual copper-width checks mandatory; source-island presence alone is not regulator stability or current-capacity proof.'})
    print('Logic supply pickups',len(stitches),'blocked',blocked,'opens',b.GetConnectivity().GetUnconnectedCount(False),flush=True)
    return b,c,filler,owners
if __name__=='__main__':owners=main()
