"""Finite new power geometry and provenance-bound local copper reuse."""
import sys,math,json
from collections import defaultdict,Counter
from rebuild import *
sys.path.insert(0,str(BASE.parent/'rev-a1/scripts'))
from bounded_seed import Screen,seed
from bounded_invariants import signature
from cad_operations import zone,rect,corridor,merge_zones
from configure_power_rules import POWER_NETS
import pcbnew as pcb

HOLD=[]
def p(x,y):return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
def xy(v):return [pcb.ToMM(v.x),pcb.ToMM(v.y)]
def main():
    guard();b=pcb.LoadBoard(str(BOARD));source=pcb.LoadBoard(str(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'))
    assert not list(b.GetTracks()) and not list(b.Zones()),'Fresh placement only'
    fps={f.GetReference():f for f in b.GetFootprints()};old={f.GetReference():f for f in source.GetFootprints()}
    pads={f.GetReference()+'.'+v.GetNumber():v for f in b.GetFootprints() for v in f.Pads()}
    def pin(s):return xy(pads[s].GetPosition())
    def area(net,poly,layers=(pcb.F_Cu,pcb.B_Cu),priority=1):
        for l in layers:
            z=zone(b,net,poly,l,priority,.5 if net in POWER_NETS else .3)
            z.SetZoneName('REBUILD/'+net);z.SetMinThickness(pcb.FromMM(1.2 if net in POWER_NETS else .5))
    def path(net,points,width,layers=(pcb.F_Cu,pcb.B_Cu),priority=4):
        points=[pin(q) if isinstance(q,str) else q for q in points]
        points=[q for i,q in enumerate(points) if i==0 or math.dist(q,points[i-1])>1e-6]
        if len(points)<2:return
        for l in layers:corridor(b,net,points,width,l,priority)
    for net,box in [
        ('BATT_FUSED_P',(5,36,28,54)),('BATT_SENSED_P',(33,10,58.9,77)),('MAIN_COMMON',(59.2,10,80.8,77)),
        ('SYS_BUS_P',(81.1,10,110,77)),('MOTION_SENSED_P',(114,10,145.9,69)),('MOTION_COMMON',(146.2,10,167.8,69)),
        ('MOTION_BUS_P',(168.1,10,217,76))]:area(net,rect(*box))
    # Entire F/B returns are newly drawn around the outputs. Inner signal layers
    # remain available except for the short, local, original two-layer Lift return.
    area('BATT_N',[(5,89),(35,89),(35,99),(109,99),(109,104),(235,104),(235,184),(221,184),(221,133),(52,133),(52,174),(31,174),(31,124),(5,124)])
    area('BATT_N',rect(222,75,235,184))
    path('BATT_N',['BC15.1','J2.1'],12)
    for nt in [1,2,3,4,5,6,7,8]:path('BATT_N',[f'NT{nt}.2',(231,pin(f'NT{nt}.2')[1])] if nt in [1,2,3,4,7] else [f'NT{nt}.2',(42,pin(f'NT{nt}.2')[1])],10)
    path('BATT_N',['NT9.2',(75,128)],4)
    path('MOTION_BUS_P',[(206,12),(276,12),(276,114)],6)
    for ref in ['J3','J5','J7','J8','J12','C312','C313']:
        for pad in fps[ref].Pads():
            if pad.GetNetname()=='MOTION_BUS_P':
                x,y=xy(pad.GetPosition());path('MOTION_BUS_P',[(x,y),(276,y)],6 if ref.startswith('C') else 4)
    path('ARM_L_N',['NT1.1','J4.1'],12)
    path('ARM_R_N',['NT2.1','J6.1'],12)
    path('DRIVE_N',['NT3.1','J7.2'],8,(pcb.F_Cu,))
    path('LIFT_N',['NT4.1','J8.2'],8,(pcb.In1_Cu,pcb.In2_Cu))
    area('CHOP_DRAIN',rect(238,42.7,261,60),layers=(pcb.F_Cu,),priority=4)
    path('CHOP_DRAIN',[(258,48),'J12.2'],3,(pcb.F_Cu,))
    area('CHOPPER_N',rect(232.5,44.7,237.5,61),layers=(pcb.F_Cu,),priority=5)
    path('CHOPPER_N',[(235,57),(235,64),(256,64),(256,94),'NT7.1'],8,(pcb.B_Cu,),priority=5)
    for ref in ['C312','C313']:
        for pad in fps[ref].Pads():
            if pad.GetNetname()=='CHOPPER_N':path('CHOPPER_N',[xy(pad.GetPosition()),(235,xy(pad.GetPosition())[1]),(235,57)],6,(pcb.B_Cu,),priority=5)
    path('CHOPPER_N',['NT10.2',(235,63),(235,57)],3,(pcb.F_Cu,pcb.B_Cu),priority=5)
    path('PC_N',['NT5.1','J9.2'],3)
    path('LOGIC_BUCK_N',['NT6.1','J10.2'],3)
    path('LOGIC_5V_N',['NT8.1','J11.2',(18,194),(82,194),'J18.3'],6,(pcb.B_Cu,))
    # eFuse terminals use the original pinout and broad new output copper.
    for ref,net,con in [('U3','PC_BUCK_IN_P','J9.1'),('U4','LOGIC_BUCK_IN_P','J10.1')]:
        # Initial cycle 02 incorrectly used pin 9 (DVDT); local_corrections.py
        # repaired the executed candidate. Use the verified OUT pin on replay.
        assert pads[ref+'.17'].GetNetname()==net and pads[ref+'.18'].GetNetname()==net
        path(net,[ref+'.17',con],3,(pcb.F_Cu,pcb.B_Cu))
        for pad in fps[ref].Pads():
            if pad.GetNetname()==net:path(net,[xy(pad.GetPosition()),ref+'.17'],1.25,(pcb.F_Cu,))
    path('V5V',['J11.1',(62,182),(79,198),'J18.1'],5,(pcb.F_Cu,))
    area('LOGIC_GND',rect(16,151,278,218),layers=(pcb.In1_Cu,),priority=0)
    area('LOGIC_GND',rect(15,9,40,38),layers=(pcb.In1_Cu,),priority=0)
    path('LOGIC_GND',['NT9.1',(73,154)],3,(pcb.In1_Cu,),priority=0)
    area('CHOP_GND',rect(175,86,230,153),layers=(pcb.In1_Cu,),priority=1)
    area('CHOP_GND',rect(218,42,241,70),layers=(pcb.In1_Cu,),priority=1)
    path('CHOP_GND',['NT10.1',(225,65),(225,100)],3,(pcb.In1_Cu,),priority=1)
    merge_zones(b)
    for z in b.Zones():
        if z.GetNetname() in POWER_NETS:z.SetMinThickness(pcb.FromMM(1.2))
    screen=Screen(b)
    # Reuse only whole local nets with one identical pad-owner transform and
    # unchanged source geometry. Global power/ground/clock trunks are rebuilt.
    excluded=set(POWER_NETS)|{'LOGIC_GND','CHOP_GND','V3V3','V5V','CHOPPER_N','CHOP_DRAIN','PC_BUCK_IN_P','LOGIC_BUCK_IN_P','PC_N','LOGIC_BUCK_N','LOGIC_5V_N','DRIVE_N','LIFT_N'}
    eligible={t.GetNetname() for t in source.GetTracks()}-excluded
    local,held=seed(b,source,eligible,screen,'Original Rev A exact local net');HOLD.extend(held)
    # Whole original tap elements within a small anchored neighbourhood. The
    # selection radius is not an electrical exception; exact inverse geometry
    # and actual copper connectivity are independently audited after placement.
    items={t.m_Uuid.AsString():t for t in source.GetTracks()}
    capture=json.loads((BASE/'evidence/high-current-tap-capture.json').read_text(encoding='utf-8'))
    memberships={r['uuid']:name for name,rows in capture['groups'].items() for r in rows}
    adopted={};retired=[];groups={};oldpads=[v for f in source.GetFootprints() for v in f.Pads()]
    def transform(ref):
        a=(fps[ref].GetOrientationDegrees()-old[ref].GetOrientationDegrees())%360;c,s=math.cos(math.radians(a)),math.sin(math.radians(a));x,y=xy(old[ref].GetPosition());X,Y=xy(fps[ref].GetPosition())
        return (a,round(X-c*x-s*y,6),round(Y+s*x-c*y,6))
    for pad in oldpads:
        if pad.GetNetname() not in POWER_NETS:continue
        ref=pad.GetParentFootprint().GetReference();anchor=ref+'.'+pad.GetNumber();anchorxy=xy(pad.GetPosition());tr=transform(ref)
        near=[]
        for uid in memberships:
            t=items[uid]
            if t.GetNetname()!=pad.GetNetname():continue
            points=[xy(t.GetPosition())] if isinstance(t,pcb.PCB_VIA) else [xy(t.GetStart()),xy(t.GetEnd())]
            if max(math.dist(q,anchorxy) for q in points)<=8:near.append(t)
        frontier=[pad];selected=[]
        while frontier:
            a=frontier.pop()
            for t in list(near):
                if any(a.IsOnLayer(l) and t.IsOnLayer(l) and a.GetEffectiveShape(l).Collide(t.GetEffectiveShape(l),0) for l in [pcb.F_Cu,pcb.In1_Cu,pcb.In2_Cu,pcb.B_Cu]):
                    near.remove(t);selected.append(t);frontier.append(t)
        clones=[];conflict=False
        for t in selected:
            uid=t.m_Uuid.AsString()
            if uid in adopted:
                if adopted[uid]['transform']!=list(tr):conflict=True
                continue
            n=t.Duplicate().Cast();n.SetParentGroup(None);n.SetUuid(pcb.KIID(uid));n.Rotate(p(0,0),pcb.EDA_ANGLE(tr[0],pcb.DEGREES_T));n.Move(p(tr[1],tr[2]));n.SetNet(b.FindNet(t.GetNetname()));n.SetLocked(True);HOLD.append(n)
            if screen.reason(n):conflict=True
            clones.append((uid,n))
        if conflict:continue
        for uid,n in clones:
            group=memberships[uid]
            if group not in groups:g=pcb.PCB_GROUP(b);g.SetName(group);b.Add(g);groups[group]=g
            b.Add(n);groups[group].AddItem(n);screen.index(n)
            adopted[uid]={'uuid':uid,'anchor':anchor,'group':group,'transform':list(tr),'source_signature':signature(items[uid]),'target_signature':signature(n)}
    for uid in memberships:
        if uid not in adopted:retired.append(uid)
    b.BuildConnectivity();filler=pcb.ZONE_FILLER(b);filler.Fill(b.Zones())
    # Fill only within actual connected copper, with dimensions unchanged from
    # Rev A. Local vias avoid all placed pads and inherited sensitive traces.
    via_counts=Counter()
    fields=[('BATT_SENSED_P',40,48,12,74),('MAIN_COMMON',66,74,12,73),('SYS_BUS_P',96,108,12,73),
            ('MOTION_SENSED_P',124,134,12,66),('MOTION_COMMON',152,162,12,66),('MOTION_BUS_P',186,211,13,71),
            ('BATT_N',8,233,100,130),('BATT_N',224,232,132,180),('BATT_N',34,49,132,172),('CHOPPER_N',233.5,236.5,53,60)]
    for net,x0,x1,y0,y1 in fields:
        step=1.6 if net!='CHOPPER_N' else 1.2
        for ix in range(int((x1-x0)/step)+1):
            for iy in range(int((y1-y0)/step)+1):
                X,Y=x0+ix*step,y0+iy*step
                if not all(any(z.GetNetname()==net and z.GetLayer()==l and all(z.GetFilledPolysList(l).Contains(p(X+dx,Y+dy),-1,0,True) for dx,dy in [(0,0),(.5,0),(-.5,0),(0,.5),(0,-.5)]) for z in b.Zones()) for l in [pcb.F_Cu,pcb.B_Cu]):continue
                v=pcb.PCB_VIA(b);v.SetPosition(p(X,Y));v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetViaType(pcb.VIATYPE_THROUGH);v.SetWidth(pcb.FromMM(.8));v.SetDrill(pcb.FromMM(.4));v.SetNet(b.FindNet(net));v.SetLocked(True);HOLD.append(v)
                if screen.reason(v):continue
                b.Add(v);screen.index(v);via_counts[net]+=1
    b.BuildConnectivity();filler.Fill(b.Zones());pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'local-copper-provenance.json',{'source_sha256':sha(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'),'local_nets':local,'tap_adopted':list(adopted.values()),'tap_retired':retired,'power_vias':dict(via_counts),'all_original_taps_dispositioned':len(adopted)+len(retired)==492})
    action('New power skeleton and exact local blocks',{'pcb_sha256':sha(BOARD),'taps_adopted':len(adopted),'power_vias':dict(via_counts)})
    print('Local nets',len(local['adopted']),'original taps',len(adopted),'power vias',dict(via_counts),flush=True)
    return b,source,filler,screen
if __name__=='__main__':owners=main()
