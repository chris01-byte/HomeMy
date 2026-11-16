import sys; sys.path.insert(0,'<SITZUNG>/agents/mech/pylib'); sys.path.insert(0,'<SITZUNG>/agents/mech')
import json, collections
from shapely.geometry import Polygon
from shapely.strtree import STRtree
from shapely.ops import unary_union
D=json.load(open('<SITZUNG>/agents/mech/pads_exposed.json'))
P={'BATT_FUSED_P','BATT_SENSED_P','MAIN_COMMON','SYS_BUS_P','MOTION_SENSED_P','MOTION_COMMON','MOTION_BUS_P'}
N={'BATT_N','ARM_L_N','ARM_R_N','DRIVE_N','LIFT_N','PC_N','LOGIC_BUCK_N','CHOPPER_N','LOGIC_5V_N','LOGIC_GND','CHOP_GND','CHASSIS','LIFT_24V_N'}
for side in ['F','B']:
    items=[]
    for p in D['pads']:
        if side in p['sides']:
            for poly in p['sides'][side]:
                if len(poly)>=3:
                    items.append((Polygon(poly),p))
    geoms=[g for g,_ in items]
    tree=STRtree(geoms)
    print('=====',side,'side: exposed pads',len(items))
    pairs={}
    for i,(g,p) in enumerate(items):
        if p['net'] not in P: continue
        for j in tree.query(g.buffer(12)):
            q=items[j][1]
            if q['net']==p['net'] or q['net']=='' : continue
            d=g.distance(geoms[j])
            key=(p['net'],q['net'])
            if key not in pairs or d<pairs[key][0]:
                pairs[key]=(d,p['ref'],p['num'],q['ref'],q['num'],round(p['x'],2),round(p['y'],2),round(q['x'],2),round(q['y'],2))
    rows=sorted(pairs.items(),key=lambda t:t[1][0])
    print('  -- closest exposed-copper pairs: main +42V net vs return/GND nets')
    for (a,b_),v in rows:
        if b_ in N and v[0]<12: print('   %-16s - %-14s %6.2f mm   %s.%s (%.2f,%.2f) <-> %s.%s (%.2f,%.2f)'%(a,b_,v[0],v[1],v[2],v[5],v[6],v[3],v[4],v[7],v[8]))
    print('  -- closest pairs: main +42V net vs any other net (<2.0 mm)')
    for (a,b_),v in rows:
        if b_ not in N and v[0]<2.0: print('   %-16s - %-22s %6.2f mm   %s.%s (%.2f,%.2f) <-> %s.%s (%.2f,%.2f)'%(a,b_,v[0],v[1],v[2],v[5],v[6],v[3],v[4],v[7],v[8]))
