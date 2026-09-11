"""Explicit local placement/power corrections after the first power check."""
from rebuild import *
import sys,math
sys.path.insert(0,str(BASE.parent/'rev-a1/scripts'))
from finish_280_routes import Controlled
from cad_operations import zone,rect,corridor,merge_zones
import pcbnew as pcb
HOLD=[]
def p(x,y):return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
def xy(v):return [pcb.ToMM(v.x),pcb.ToMM(v.y)]
def main():
    guard();b=pcb.LoadBoard(str(BOARD));fps={f.GetReference():f for f in b.GetFootprints()}
    originalsha=sha(BOARD);moves={r:(x,y) for r,x,y in [('R319',229.5,47),('R320',229.5,49.6),('R321',229,42),('D62',222,43)]}
    stitches=json.loads((OUT/'cycle-03-power-corrections.json').read_text(encoding='utf-8'))['reference_stitches']
    removevias={s['via_uuid'] for s in stitches if s['pad'].split('.')[0] in moves}
    oldpads=[pad for ref in moves for pad in fps[ref].Pads()]
    removed=[]
    for t in list(b.GetTracks()):
        belongs=t.m_Uuid.AsString() in removevias or not isinstance(t,pcb.PCB_VIA) and any(t.GetNetname()==v.GetNetname() and t.IsOnLayer(v.GetLayer()) and t.GetEffectiveShape(v.GetLayer()).Collide(v.GetEffectiveShape(v.GetLayer()),0) for v in oldpads)
        if belongs:
            assert not t.GetParentGroup(),'Cannot alter reviewed power tap'
            b.Remove(t);HOLD.append(t);removed.append(t.m_Uuid.AsString())
    before={r:xy(fps[r].GetPosition()) for r in moves}
    for r,q in moves.items():fps[r].SetPosition(p(*q))
    # Regenerate eFuse output zones from correct OUT17/18 pad identities.
    for z in list(b.Zones()):
        if z.GetNetname() in ['PC_BUCK_IN_P','LOGIC_BUCK_IN_P']:b.Remove(z);HOLD.append(z)
    for ref,net,con in [('U3','PC_BUCK_IN_P','J9'),('U4','LOGIC_BUCK_IN_P','J10')]:
        pads={v.GetNumber():v for v in fps[ref].Pads()};out=next(v for v in fps[con].Pads() if v.GetNumber()=='1')
        assert out.GetNetname()==net and pads['17'].GetNetname()==net and pads['18'].GetNetname()==net
        for layer in [pcb.F_Cu,pcb.B_Cu]:
            corridor(b,net,[xy(pads['17'].GetPosition()),xy(out.GetPosition())],3,layer,4)
            corridor(b,net,[xy(pads['18'].GetPosition()),xy(out.GetPosition())],3,layer,4)
    # Actual top-layer copper void leaves the known thin bias wiring as the
    # eFuse reference pickup. B.Cu carries the wide return underneath.
    void=pcb.SHAPE_POLY_SET();void.NewOutline()
    for x,y in rect(34,114,62,131):void.Append(p(x,y))
    for z in b.Zones():
        if z.GetNetname()=='BATT_N' and z.GetLayer()==pcb.F_Cu:z.Outline().BooleanSubtract(void)
    z=zone(b,'CHOP_DRAIN',[(238,36),(266,36),(266,68),(242,68),(242,61),(238,61)],pcb.F_Cu,4,.5)
    merge_zones(b);c=Controlled(b)
    # Tight driver resistors now sit between the UCC27511 and Q40.
    c.route('Chopper high drive','CHOP_DRIVE_H',[(['U33.2',(228,49),(228,47),'R319.1'],.2,pcb.F_Cu)])
    c.route('Chopper low drive','CHOP_DRIVE_L',[(['U33.3',(227.2,48.05),(227.2,50.8),(228.4,50.8),'R320.1'],.2,pcb.F_Cu)])
    c.route('Chopper gate local','CHOP_GATE',[(['R319.2',(232,47),(232,43.8),'Q40.1'],.3,pcb.F_Cu),(['R320.2',(232,49.6),(232,47)],.3,pcb.F_Cu),(['R321.1',(228.1,43.8),(232,43.8)],.2,pcb.F_Cu),(['D62.1',(220.6,40),(228.1,40),'R321.1'],.2,pcb.F_Cu)])
    c.route('INA local 3V3 decoupling','V3V3',[(['C206.1','U11.6'],.2,pcb.F_Cu)])
    b.BuildConnectivity();filler=pcb.ZONE_FILLER(b);filler.Fill(b.Zones());pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'cycle-03-local-corrections.json',{'input_sha256':originalsha,'output_sha256':sha(BOARD),'moves':[{'ref':r,'from_mm':before[r],'to_mm':q} for r,q in moves.items()],'removed_nonpower_local_items':removed,'recipes':c.records,'efuse_output_pads':['17','18']})
    return b,c,filler
if __name__=='__main__':owners=main()
