# Uses the embedded reader (unchanged logic) to obtain the same polygon model, then asks extra questions.
import sys, json, math, collections
from power_native_reader import main, pcb
from build_board import point, mm
b,polys,paths,zones,tap_ids,digest=main()
fps={f.GetReference():f for f in b.GetFootprints()}
L={'F.Cu':pcb.F_Cu,'In1.Cu':pcb.In1_Cu,'In2.Cu':pcb.In2_Cu,'B.Cu':pcb.B_Cu}
def pad_samples(ref,number):
    p=next(p for p in fps[ref].Pads() if p.GetNumber()==str(number))
    x,y=pcb.ToMM(p.GetPosition().x),pcb.ToMM(p.GetPosition().y)
    if p.GetDrillSize().x==0:return [[x,y]]
    d=pcb.ToMM(p.GetDrillSize().x)/2+.10
    return [[x+d,y],[x-d,y],[x,y+d],[x,y-d]]
def outline_ids(q,points):
    ids=set()
    if q is None:return ids
    for x,y in points:
        for i in range(q.OutlineCount()):
            if q.Contains(point(x,y),i,0,True):ids.add(i)
    return ids
print('--- extra same-layer pairs not in the 247 list (same criterion)')
extra=[('MOTION_BUS_P',('J7',1),('BC11',1)),('MOTION_BUS_P',('J8',1),('BC11',1)),('MOTION_BUS_P',('J12',1),('BC11',1)),
       ('MOTION_BUS_P',('C312',1),('BC11',1)),('MOTION_BUS_P',('C313',1),('BC11',1)),('MOTION_BUS_P',('C300',1),('BC11',1)),
       ('MOTION_BUS_P',('J7',1),('J3',1)),('MOTION_BUS_P',('J8',1),('J3',1)),('MOTION_BUS_P',('J12',1),('J3',1)),
       ('CHOPPER_N',('Q40',2),('NT7',1)),('CHOPPER_N',('NT10',2),('NT7',1)),
       ('PC_BUCK_IN_P',('J9',1),('U3',1)),('PC_N',('J9',2),('NT5',1)),('LOGIC_BUCK_N',('J10',2),('NT6',1)),('V5V',('J11',1),('J18',1)),
       ('BATT_N',('NT9',2),('BC15',1)),('BATT_N',('Q11',2),('BC15',1))]
for net,a,c in extra:
    row=[]
    for ln,l in L.items():
        q=polys.get((net,l))
        try:
            ia,ib=outline_ids(q,pad_samples(*a)),outline_ids(q,pad_samples(*c))
        except StopIteration:
            row.append((ln,'pad?')); continue
        row.append((ln, 'SAME' if ia&ib else ('from-only' if ia and not ib else ('to-only' if ib and not ia else ('both-but-different' if ia and ib else 'none')))))
    print(net,a,'->',c,row)
print('--- layers on which each MOTION_BUS_P branch pad has copper outline + outline count per layer')
for (net,l),q in sorted(polys.items(),key=lambda kv:(kv[0][0],kv[0][1])):
    if net in('MOTION_BUS_P','SYS_BUS_P','BATT_N','CHOPPER_N','DRIVE_N','LIFT_N'):
        areas=sorted([round(q.Outline(i).Area()/1e12,1) for i in range(q.OutlineCount())],reverse=True)
        print(net,b.GetLayerName(l),'outlines',q.OutlineCount(),'largest areas mm2',areas[:8])
