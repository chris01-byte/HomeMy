import sys; sys.path.insert(0,'<SITZUNG>/agents/mech/pylib'); sys.path.insert(0,'<SITZUNG>/agents/mech')
from common import *
import numpy as np, collections
from scipy import ndimage as ndi
r=R()
F=r['F']; Bc=r['B']; FM=r['FM']; BM=r['BM']
def window(cx,cy,half):
    x0=int((cx-half)*RES); x1=int((cx+half)*RES); y0=int((cy-half)*RES); y1=int((cy+half)*RES)
    return slice(max(y0,0),min(y1,260*RES)),slice(max(x0,0),min(x1,280*RES)),x0,y0
def nearest_foreign(layer,cx,cy,own,half=15,shape=None):
    sy,sx,x0,y0=window(cx,cy,half)
    a=layer[sy,sx]
    yy,xx=np.mgrid[sy,sx]
    X=(xx+0.5)/RES; Y=(yy+0.5)/RES
    if shape is None:
        d=np.hypot(X-cx,Y-cy)
    else:
        hx,hy=shape
        dx=np.maximum(np.abs(X-cx)-hx,0); dy=np.maximum(np.abs(Y-cy)-hy,0); d=np.hypot(dx,dy)
    res={}
    for code_ in np.unique(a):
        if code_==0: continue
        n=nets.get(int(code_),'?')
        if n in own: continue
        res[n]=float(d[a==code_].min())
    return sorted(res.items(),key=lambda t:t[1])
print('=== BC lands: nearest foreign-net copper on F.Cu and B.Cu, distance from land centre (mm) [washer r=4.5, land r=4.0]')
for ref in ['BC%d'%i for i in range(1,16)]:
    f=fps[ref]; p=f['pads'][0]
    nfF=nearest_foreign(F,p['x'],p['y'],{p['net'],'<NETTIE_FCU_GRAPHIC>'})[:3]
    nfB=nearest_foreign(Bc,p['x'],p['y'],{p['net']})[:3]
    print(ref,p['net'],'(%.1f,%.1f)'%(p['x'],p['y']),' F.Cu:',', '.join('%s %.2f'%t for t in nfF),' | B.Cu:',', '.join('%s %.2f'%t for t in nfB))
print()
print('=== NT pads: nearest foreign copper to the 20x10 NB bridge outline on F.Cu (distance from bridge edge, mm; 0=under bridge)')
for nt in A2J['net_tie_modifications']:
    ref=nt['ref']; pos=nt['position']
    own={pd['net'] for pd in nt['replace_pad_1_and_2_with']}|{'<NETTIE_FCU_GRAPHIC>'}
    nf=nearest_foreign(F,pos[0],pos[1],own,half=20,shape=(10,5))[:4]
    # B side: bar BATT_N over pad1 etc. nearest foreign to pad1 washer
    print(ref,sorted(own-{'<NETTIE_FCU_GRAPHIC>'}),' F.Cu nearest foreign to NB outline:',', '.join('%s %.2f'%t for t in nf))
