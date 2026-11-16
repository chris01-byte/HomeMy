import sys; sys.path.insert(0,'<SITZUNG>/agents/mech/pylib'); sys.path.insert(0,'<SITZUNG>/agents/mech')
from common import *
import math, numpy as np
from shapely.geometry import Polygon, Point, box
r=R()
def padrect(p):
    # axis-aligned approx using rotation multiples of 90
    sx,sy=p['sx'],p['sy']
    rot=p['rot']%180
    if abs(rot-90)<1: sx,sy=sy,sx
    return box(p['x']-sx/2,p['y']-sy/2,p['x']+sx/2,p['y']+sy/2)
for J in ['J1','J2','J3','J4','J5','J6']:
    f=fps[J]
    holes=[(p['x'],p['y']) for p in f['pads']]
    net=f['pads'][0]['net']
    body=box(f['x']-4.5,f['y']-4.5,f['x']+4.5,f['y']+4.5)
    print('=====',J,net,'centre',(f['x'],f['y']),'rot',f['rot'])
    # nearest other-footprint pads to any press-fit hole edge (hole radius 0.74) and to body
    rows=[]
    for g in board['footprints']:
        if g['ref']==J: continue
        for p in g['pads']:
            pr=padrect(p)
            dh=min(pr.distance(Point(h))-0.7375 for h in holes)
            db=pr.distance(body)
            if dh<6: rows.append((dh,db,g['ref'],p['num'],p['net'],p['x'],p['y'],p['sx'],p['sy'],g['layer'],g['fpid']))
    rows.sort()
    seen=set()
    for t in rows:
        if t[2] in seen: continue
        seen.add(t[2])
        print('   comp %-6s pad %-3s net %-18s at (%.2f,%.2f) %sx%s on %s: pad-edge to PF hole-edge %.2f mm, pad to 9x9 body %.2f mm [%s]'%(t[2],t[3],t[4],t[5],t[6],t[7],t[8],t[9],t[0],t[1],t[10]))
    # courtyard/bbox distance of other footprints to the terminal body
    rows=[]
    for g in board['footprints']:
        if g['ref']==J: continue
        cy=g['courtyard'] or g['bbox']
        gb=box(*cy)
        d=gb.distance(body)
        dh=min(gb.distance(Point(h))-0.7375 for h in holes)
        if dh<5: rows.append((dh,d,g['ref'],g['value'][:30],g['layer'],cy))
    rows.sort()
    for t in rows[:8]:
        print('   courtyard %-6s (%s) %s: to PF hole edge %.2f, to terminal body %.2f ; cy=%s'%(t[2],t[3],t[4],t[0],t[1],[round(v,2) for v in t[5]]))
    # vias of other nets near holes
    rows=[]
    for v in board['vias']:
        d=min(math.hypot(v['x']-h[0],v['y']-h[1]) for h in holes)
        if d<6 and v['net']!=net:
            rows.append((d-0.7375-v['w_B']/2,v['net'],v['x'],v['y']))
    rows.sort()
    print('   foreign vias within 6 mm of a PF hole:',len(rows),[ (round(a,2),n,x,y) for a,n,x,y in rows[:6]])
    nown=sum(1 for v in board['vias'] if v['net']==net and box(f['x']-7,f['y']-7,f['x']+7,f['y']+7).contains(Point(v['x'],v['y'])))
    print('   own-net vias within 14x14 mm box (support-die area):',nown)
    # inner-layer copper near holes: min distance from hole centre to foreign copper on each layer
    for lname in ['F','I1','I2','B']:
        a=r[lname]
        best={}
        for h in holes:
            x0=int((h[0]-4)*RES); x1=int((h[0]+4)*RES); y0=int((h[1]-4)*RES); y1=int((h[1]+4)*RES)
            sub=a[y0:y1,x0:x1]
            yy,xx=np.mgrid[y0:y1,x0:x1]
            d=np.hypot((xx+0.5)/RES-h[0],(yy+0.5)/RES-h[1])
            for c in np.unique(sub):
                if c==0: continue
                n=nets.get(int(c))
                if n==net: continue
                dm=float(d[sub==c].min())
                if n not in best or dm<best[n]: best[n]=dm
        own_area=0
        # own-net copper connected area around pins on this layer within body box +-3mm
        x0=int((f['x']-7.5)*RES); x1=int((f['x']+7.5)*RES); y0=int((f['y']-7.5)*RES); y1=int((f['y']+7.5)*RES)
        sub=a[y0:y1,x0:x1]
        own_area=(sub==code[net]).sum()/RES/RES
        print('   layer %-3s: own-net copper in 15x15 box %.1f mm2 (of 225); nearest foreign copper to a PF hole centre: %s'%(lname,own_area,', '.join('%s %.2f mm (=%.2f from drilled 1.6 wall)'%(n,d,d-0.8) for n,d in sorted(best.items(),key=lambda t:t[1])[:3])))
