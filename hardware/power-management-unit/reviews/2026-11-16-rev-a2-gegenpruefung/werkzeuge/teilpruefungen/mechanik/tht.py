import sys; sys.path.insert(0,'<SITZUNG>/agents/mech/pylib'); sys.path.insert(0,'<SITZUNG>/agents/mech')
from common import *
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
bars={}
for bar in A2J['busbars']:
    P=Polygon(bar['outline'])
    for c in bar['cutouts']:
        P=P.difference(Polygon(c['outline']))
    bars[bar['ref']]=(P,bar['net'])
# all THT pads (drill>0) incl. NPTH
tht=[]
for f in board['footprints']:
    for p in f['pads']:
        if p['drill'][0]>0:
            tht.append((f['ref'],p['num'],p['net'],p['x'],p['y'],p['sx'],p['sy'],p['drill'][0],f['value'],f['fpid']))
print('THT pads total',len(tht))
import collections
print(collections.Counter(t[9] for t in tht))
print()
for ref,(P,net) in bars.items():
    print('==',ref,net,'area %.1f mm2'%P.area,'bounds',P.bounds)
    rows=[]
    for t in tht:
        pt=Point(t[3],t[4])
        d=P.exterior.distance(pt) if not P.contains(pt) else -P.exterior.distance(pt)
        # distance from pad copper edge (approx circle of max dim)
        rad=max(t[5],t[6])/2
        dd=P.distance(pt)
        if dd-rad<8 :
            rows.append((dd-rad,dd,t))
    rows.sort(key=lambda r:r[0])
    for dd_edge,dd,t in rows[:40]:
        if t[0].startswith('BC') and t[2]==net and dd==0: continue
        print('   %-6s pad %-3s net %-18s at (%.2f,%.2f) pad %.2fx%.2f drill %.2f : centre-to-bar %.2f mm, pad-edge-to-bar %.2f mm  [%s]'%(t[0],t[1],t[2],t[3],t[4],t[5],t[6],t[7],dd,dd_edge,t[9]))
# bar to bar distances
print()
refs=list(bars)
for i in range(len(refs)):
    for j in range(i+1,len(refs)):
        d=bars[refs[i]][0].distance(bars[refs[j]][0])
        if d<40: print('bar-bar',refs[i],bars[refs[i]][1],refs[j],bars[refs[j]][1],'gap %.2f mm'%d)
# bars vs board edge & mounting holes
brd=box(0,0,280,260)
for ref,(P,net) in bars.items():
    print(ref,'min dist to board edge %.2f'%P.distance(brd.exterior),'inside' if brd.contains(P) else 'OUTSIDE')
