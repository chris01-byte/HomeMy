import sys; sys.path.insert(0,'<SITZUNG>/agents/mech')
from common import *
import collections, math
r=R()
Bc=r['B']; BM=r['BM']
px=1.0/RES/RES  # mm2 per pixel
def inpoly(x,y,poly):
    n=len(poly); ins=False
    for i in range(n):
        x1,y1=poly[i]; x2,y2=poly[(i+1)%n]
        if (y1>y)!=(y2>y):
            xi=x1+(y-y1)*(x2-x1)/(y2-y1)
            if x<xi: ins=not ins
    return ins
def dist_to_poly_edge(x,y,poly):
    n=len(poly); best=1e9
    for i in range(n):
        x1,y1=poly[i]; x2,y2=poly[(i+1)%n]
        dx,dy=x2-x1,y2-y1; L2=dx*dx+dy*dy
        t=max(0,min(1,((x-x1)*dx+(y-y1)*dy)/L2)) if L2>0 else 0
        d=math.hypot(x-(x1+t*dx),y-(y1+t*dy)); best=min(best,d)
    return best
out={}
for bar in A2J['busbars']:
    ref=bar['ref']; net=bar['net']; poly=bar['outline']; cuts=[c['outline'] for c in bar['cutouts']]
    m=poly_mask(poly,cuts)
    area=m.sum()*px
    cnt=collections.Counter(Bc[m].tolist())
    print('\n=====',ref,net,'area %.0f mm2'%area)
    rows=[(nets.get(k,'?'),v*px) for k,v in cnt.items()]
    rows.sort(key=lambda t:-t[1])
    for n,a in rows:
        tag='' if n==net else ('  (no copper)' if n=='?' or n is None else '  FOREIGN')
        if n==nets.get(0): tag='  (no copper)'
        print('   B.Cu %-28s %9.2f mm2 %5.1f%%%s'%(n if n else '<none>',a,100*a/area,tag))
    # vias
    vc=collections.Counter(); vl=collections.defaultdict(list)
    for v in board['vias']:
        x,y=v['x'],v['y']
        inside=inpoly(x,y,poly) and not any(inpoly(x,y,c) for c in cuts)
        dedge=dist_to_poly_edge(x,y,poly)
        rad=v['w_B']/2
        if inside or dedge<rad:
            # check not fully within cutout
            if any(inpoly(x,y,c) and dist_to_poly_edge(x,y,c)>rad for c in cuts): continue
            vc[v['net']]+=1; vl[v['net']].append((x,y,v['w_B'],v['drill']))
    print('   vias under bar (B.Cu pad touching bar footprint): total',sum(vc.values()),' own-net',vc.get(net,0),' foreign',sum(c for n,c in vc.items() if n!=net))
    for n,c in sorted(vc.items(),key=lambda t:-t[1]):
        if n!=net:
            print('      %-28s %3d  %s'%(n,c,' '.join('(%.2f,%.2f)'%(x,y) for x,y,_,_ in vl[n][:12])+(' ...' if len(vl[n])>12 else '')))
    # THT / other pads on B.Cu within bar
    pc=[]
    for f in board['footprints']:
        for p in f['pads']:
            if 'B.Cu' not in p['layers']: continue
            x,y=p['x'],p['y']
            rad=max(p['sx'],p['sy'])/2
            inside=inpoly(x,y,poly)
            if (inside or dist_to_poly_edge(x,y,poly)<rad):
                incut=any(inpoly(x,y,c) for c in cuts)
                pc.append((f['ref'],p['num'],p['net'],x,y,p['sx'],p['sy'],p['drill'][0],incut,p['attr']))
    for t in pc:
        print('      PAD %s.%s net=%s at (%.2f,%.2f) size %.2fx%.2f drill %.2f incut=%s %s'%t)
    out[ref]={'vias':{n:l for n,l in vl.items()}}
json.dump(out,open(OUT+'underbar_vias.json','w'))
