import sys; sys.path.insert(0,'<SITZUNG>/agents/mech/pylib'); sys.path.insert(0,'<SITZUNG>/agents/mech')
from common import *
import numpy as np, math
r=R()
for H in ['H1','H2','H3','H4']:
    f=fps[H]; cx,cy=f['x'],f['y']
    p=f['pads'][0]
    print('==',H,(cx,cy),'pad',p['sx'],p['sy'],'drill',p['drill'],p['attr'],p['layers'],'net',repr(p['net']))
    for ln in ['F','I1','I2','B']:
        a=r[ln]
        x0=int((cx-12)*RES); x1=int((cx+12)*RES); y0=int((cy-12)*RES); y1=int((cy+12)*RES)
        x0=max(x0,0); y0=max(y0,0); x1=min(x1,280*RES); y1=min(y1,260*RES)
        sub=a[y0:y1,x0:x1]
        yy,xx=np.mgrid[y0:y1,x0:x1]
        d=np.hypot((xx+0.5)/RES-cx,(yy+0.5)/RES-cy)
        res=[]
        for c in np.unique(sub):
            if c==0: continue
            res.append((float(d[sub==c].min()),nets.get(int(c))))
        res.sort()
        print('   %-3s nearest copper from hole centre: %s'%(ln,', '.join('%s %.2f mm (%.2f from hole wall r=1.6)'%(n,dd,dd-1.6) for dd,n in res[:4])))
    # components within 8 mm
    near=[]
    for g in board['footprints']:
        if g['ref']==H: continue
        for q in g['pads']:
            dd=math.hypot(q['x']-cx,q['y']-cy)-max(q['sx'],q['sy'])/2
            if dd<8: near.append((round(dd,2),g['ref'],q['num'],q['net']))
    near.sort()
    print('   pads within 8 mm:',near[:6])
# copper to board edge per net (outer layers), min distance
print()
for ln in ['F','B','I1','I2']:
    a=r[ln]
    H_,W_=a.shape
    res={}
    band=int(3*RES)
    for name,sub,dist in [('left',a[:,:band],lambda yy,xx:(xx+0.5)/RES),('right',a[:,W_-band:],lambda yy,xx:(band-xx-0.5)/RES),('top',a[:band,:],lambda yy,xx:(yy+0.5)/RES),('bottom',a[H_-band:,:],lambda yy,xx:(band-yy-0.5)/RES)]:
        yy,xx=np.mgrid[0:sub.shape[0],0:sub.shape[1]]
        dm=dist(yy,xx)
        for c in np.unique(sub):
            if c==0: continue
            m=sub==c
            dmin=float(dm[m].min())
            k=(nets.get(int(c)),name)
            res[k]=dmin
    out=sorted(res.items(),key=lambda t:t[1])[:12]
    print(ln,'copper-to-edge minima:',', '.join('%s@%s %.2f'%(k[0],k[1],v) for k,v in out))
