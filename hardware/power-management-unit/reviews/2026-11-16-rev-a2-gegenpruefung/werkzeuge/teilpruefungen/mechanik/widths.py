import sys; sys.path.insert(0,'<SITZUNG>/agents/mech')
from common import *
import numpy as np
r=R()
def runs(vec):
    # lengths of True runs
    out=[]; n=0
    for v in vec:
        if v: n+=1
        elif n: out.append(n); n=0
    if n: out.append(n)
    return out
print('net: layer area / bbox, and copper width across a cut line (sum and longest run, mm)')
cuts={ # net: list of (orientation, coordinate, range) 'v' = vertical cut line at x (measures extent in y)
 'BATT_FUSED_P':[('v',27.0,(35,65))],
 'BATT_SENSED_P':[('v',44.0,(15,95)),('v',50.0,(15,95))],
 'MAIN_COMMON':[('v',75.0,(15,95))],
 'SYS_BUS_P':[('v',100.0,(15,95)),('v',112.0,(15,95))],
 'MOTION_SENSED_P':[('v',135.0,(15,95)),('v',144.0,(15,95))],
 'MOTION_COMMON':[('v',168.0,(15,95))],
 'MOTION_BUS_P':[('v',196.0,(5,95)),('h',41.5,(180,265)),('v',215.0,(0,50)),('v',240.0,(0,50))],
 'ARM_L_N':[('h',75.0,(225,260)),('v',225.0,(95,125)),('h',125.0,(200,225))],
 'ARM_R_N':[('h',100.0,(240,262)),('h',125.0,(230,262))],
 'BATT_N':[('v',40.0,(100,160)),('v',100.0,(100,160)),('v',150.0,(100,160)),('v',200.0,(100,160)),('v',215.0,(100,160)),('v',230.0,(100,160))],
}
for net,cl in cuts.items():
    c=code[net]
    for ln in ['F','I1','I2','B']:
        m=r[ln]==c
        if m.sum()==0: continue
        ys,xs=np.where(m)
        print('%-16s %-2s area %7.0f mm2 bbox x %.1f..%.1f y %.1f..%.1f'%(net,ln,m.sum()/RES/RES,xs.min()/RES,xs.max()/RES,ys.min()/RES,ys.max()/RES))
        for (o,coord,(a,b)) in cl:
            if o=='v':
                vec=m[int(a*RES):int(b*RES),int(coord*RES)]
            else:
                vec=m[int(coord*RES),int(a*RES):int(b*RES)]
            rr=runs(vec)
            if rr: print('        cut %s=%.1f over %s: copper sum %.1f mm, longest run %.1f mm, runs %d'%('x' if o=='v' else 'y',coord,(a,b),sum(rr)/RES,max(rr)/RES,len(rr)))
