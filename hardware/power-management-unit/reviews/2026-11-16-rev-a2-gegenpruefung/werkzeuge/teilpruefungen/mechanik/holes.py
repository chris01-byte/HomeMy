import sys; sys.path.insert(0,'<SITZUNG>/agents/mech/pylib'); sys.path.insert(0,'<SITZUNG>/agents/mech')
from common import *
from shapely.geometry import Polygon, Point
import math
print('== JSON holes vs PCB pads, and hole edge distance in bar (need >=4.5 for D9 washer, >=4.0 for D8 shim)')
padpos={}
for f in board['footprints']:
    for p in f['pads']:
        padpos[(f['ref'],p['num'])]=(p['x'],p['y'],p['net'],p['drill'][0])
for bb in A2J['busbars']:
    P=Polygon(bb['outline'])
    for c in bb['cutouts']: P=P.difference(Polygon(c['outline']))
    for h in bb['holes']:
        fn=h['function']
        key=(fn,'1') if fn.startswith('BC') else (fn.split('.')[0],fn.split('.')[1])
        px,py,net,dr=padpos[key]
        dpos=math.hypot(px-h['x'],py-h['y'])
        pt=Point(h['x'],h['y'])
        ed=P.exterior.distance(pt) if P.contains(pt) else -P.exterior.distance(pt)
        flag=''
        if net!=bb['net']: flag+=' NET-MISMATCH'
        if dpos>1e-6: flag+=' POS-MISMATCH %.3f'%dpos
        if ed<4.5: flag+=' <4.5 (washer D9 overhangs bar edge by %.2f)'%(4.5-ed)
        print('  %s %-6s hole(%.2f,%.2f) pad(%.2f,%.2f) net %s drill %.1f | edge distance %.2f mm%s'%(bb['ref'],fn,h['x'],h['y'],px,py,net,dr,ed,flag))
print('== NB bridges vs NT pads')
for nt in A2J['net_tie_modifications']:
    o=nt['top_bridge']['outline']; P=Polygon(o)
    for h,pd in zip(nt['top_bridge']['holes'],nt['replace_pad_1_and_2_with']):
        key=(nt['ref'],pd['number']); px,py,net,dr=padpos[key]
        print('  ',nt['ref'],'NB outline',P.bounds,'hole',(h['x'],h['y']),'pad',(px,py),net,'pos diff %.3f'%math.hypot(px-h['x'],py-h['y']),'edge dist %.2f'%P.exterior.distance(Point(h['x'],h['y'])))
print('contacts listed in JSON new_pcb_contacts:',len(A2J['new_pcb_contacts']),' net-tie mods:',len(A2J['net_tie_modifications']))
for c in A2J['new_pcb_contacts']:
    px,py,net,dr=padpos[(c['ref'],'1')]
    if abs(px-c['x'])>1e-6 or abs(py-c['y'])>1e-6 or net!=c['net']: print('  MISMATCH',c['ref'])
