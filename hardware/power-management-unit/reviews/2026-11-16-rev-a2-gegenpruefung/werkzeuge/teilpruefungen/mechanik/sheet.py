import sys; sys.path.insert(0,'<SITZUNG>/agents/mech/pylib'); sys.path.insert(0,'<SITZUNG>/agents/mech')
from common import *
import numpy as np, math, time
import scipy.sparse as sp
import scipy.sparse.linalg as spl
r=R()
DS=4                    # downsample factor -> 0.2 mm cells
CELL=DS/RES             # mm
NX,NY=280*RES//DS,260*RES//DS
RHO=1.724e-8            # ohm m at 20C
LAYERS=[('F',70e-6),('I1',35e-6),('I2',35e-6),('B',70e-6)]
ZPOS={'F':0.0,'I1':0.2025e-3,'I2':1.3275e-3,'B':1.53e-3}   # centre z of each foil
def down(a_bool):
    h,w=a_bool.shape
    return a_bool.reshape(h//DS,DS,w//DS,DS).mean(axis=(1,3))>=0.5
_cache={}
def netmask(layer,netname):
    k=(layer,netname)
    if k not in _cache:
        m=(r[layer]==code[netname])
        if layer=='F':   # the net-tie F.Cu graphic belongs to both pads; treat as copper of any net touching it -> handled by caller
            pass
        _cache[k]=down(m)
    return _cache[k]
bighole=None
def big_holes():
    """cells inside drilled holes >=1.0 mm (component/PTH holes): no foil there"""
    global bighole
    if bighole is None:
        m=np.zeros((NY,NX),dtype=bool)
        for f in board['footprints']:
            for p in f['pads']:
                d=p['drill'][0]
                if d>=1.0:
                    cx,cy=p['x']/CELL,p['y']/CELL; rr=d/2/CELL
                    x0,x1=int(cx-rr)-1,int(cx+rr)+2; y0,y1=int(cy-rr)-1,int(cy+rr)+2
                    yy,xx=np.mgrid[y0:y1,x0:x1]
                    mm_=((xx+0.5-cx)**2+(yy+0.5-cy)**2)<=rr*rr
                    m[y0:y1,x0:x1]|=mm_
        bighole=m
    return bighole
def cells_rect(x0,y0,x1,y1):
    xs=np.arange(int(math.floor(x0/CELL)),int(math.ceil(x1/CELL)))
    ys=np.arange(int(math.floor(y0/CELL)),int(math.ceil(y1/CELL)))
    return [(y,x) for y in ys for x in xs]
def cells_ring(cx,cy,r_in,r_out):
    out=[]
    for y in range(int((cy-r_out)/CELL)-1,int((cy+r_out)/CELL)+2):
        for x in range(int((cx-r_out)/CELL)-1,int((cx+r_out)/CELL)+2):
            d=math.hypot((x+0.5)*CELL-cx,(y+0.5)*CELL-cy)
            if r_in<=d<=r_out: out.append((y,x))
    return out
def pad_cells(ref,nums=None,net=None):
    f=fps[ref]; out=[]
    for p in f['pads']:
        if nums is not None and p['num'] not in nums: continue
        if net is not None and p['net']!=net: continue
        sx,sy=p['sx'],p['sy']
        if abs((p['rot']%180)-90)<1: sx,sy=sy,sx
        out+=cells_rect(p['x']-sx/2,p['y']-sy/2,p['x']+sx/2,p['y']+sy/2)
    return out
class Model:
    def __init__(self,netnames,layers=('F','I1','I2','B'),bar=None,contact_uohm=None,extra_masks=None,temp_factor=1.0):
        """netnames: list of nets treated as one conductor. bar: busbar dict from A2J (adds 2 mm layer) or list of dicts"""
        self.layers=[]; self.t={}
        self.idx={}
        n=0
        hole=big_holes()
        for ln,t in LAYERS:
            if ln not in layers: continue
            m=np.zeros((NY,NX),dtype=bool)
            for nn in netnames:
                m|=netmask(ln,nn)
            if extra_masks and ln in extra_masks: m|=extra_masks[ln]
            m&=~hole
            if m.sum()==0: continue
            ind=-np.ones((NY,NX),dtype=np.int64)
            ind[m]=np.arange(n,n+m.sum()); n+=m.sum()
            self.idx[ln]=ind; self.t[ln]=t; self.layers.append(ln)
        self.bars=[]
        if bar is not None:
            bl=bar if isinstance(bar,list) else [bar]
            for bi,bb in enumerate(bl):
                from PIL import Image, ImageDraw
                img=Image.new('1',(NX,NY),0); d=ImageDraw.Draw(img)
                d.polygon([(x/CELL,y/CELL) for x,y in bb['outline']],fill=1)
                for c in bb['cutouts']: d.polygon([(x/CELL,y/CELL) for x,y in c['outline']],fill=0)
                m=np.array(img,dtype=bool)
                for h in bb['holes']:
                    for (y,x) in cells_ring(h['x'],h['y'],0,h['diameter_mm']/2): m[y,x]=False
                ind=-np.ones((NY,NX),dtype=np.int64); ind[m]=np.arange(n,n+m.sum()); n+=m.sum()
                ln='BAR%d'%bi
                self.idx[ln]=ind; self.t[ln]=bb['thickness_mm']*1e-3; self.layers.append(ln); self.bars.append((ln,bb))
        self.n=n; self.extra=0
        self.rows=[]; self.cols=[]; self.vals=[]
        self.tf=temp_factor
        for ln in self.layers:
            ind=self.idx[ln]; g=self.t[ln]/(RHO*self.tf)   # sheet conductance S (per square)
            a=ind[:,:-1]; b=ind[:,1:]; k=(a>=0)&(b>=0); self._add(a[k],b[k],g)
            a=ind[:-1,:]; b=ind[1:,:]; k=(a>=0)&(b>=0); self._add(a[k],b[k],g)
        # vias
        self.nvia=0
        for v in board['vias']:
            if v['net'] not in netnames: continue
            y,x=int(v['y']/CELL),int(v['x']/CELL)
            self._vertical(y,x,v['drill'],25e-6)
            self.nvia+=1
        # plated component holes of these nets (BC lands, NT pads, THT): barrel links via ring cells
        for f in board['footprints']:
            for p in f['pads']:
                d=p['drill'][0]
                if d>=1.0 and p['net'] in netnames and len([l for l in p['layers'] if l.endswith('.Cu')])>=2 and p['attr']=='PTH':
                    ring=cells_ring(p['x'],p['y'],d/2,d/2+0.45)
                    # distribute barrel conductance over ring cells
                    for (y,x) in ring:
                        self._vertical(y,x,d,25e-6,share=1.0/len(ring))
        # bar contacts
        if self.bars:
            for ln,bb in self.bars:
                for h in bb['holes']:
                    ring=cells_ring(h['x'],h['y'],1.7,4.0)
                    ring=[(y,x) for (y,x) in ring if self.idx[ln][y,x]>=0 and 'B' in self.idx and self.idx['B'][y,x]>=0]
                    if not ring: print('WARNING no contact cells',bb['ref'],h); continue
                    Rc=(contact_uohm if contact_uohm is not None else 0.0)*1e-6
                    # shim 0.25mm Cu resistance negligible: rho*0.25e-3/41.2e-6 = 0.1 uohm
                    Rc=max(Rc,0.2e-6)
                    gc=1.0/Rc/len(ring)
                    for (y,x) in ring:
                        self._add(np.array([self.idx[ln][y,x]]),np.array([self.idx['B'][y,x]]),gc)
        self.term={}
    def _add(self,a,b,g):
        a=np.asarray(a).ravel(); b=np.asarray(b).ravel()
        gv=np.full(a.shape,g,dtype=float)
        self.rows+=[a,b,a,b]; self.cols+=[a,b,b,a]; self.vals+=[gv,gv,-gv,-gv]
    def _vertical(self,y,x,drill,plating,share=1.0):
        present=[ln for ln in ['F','I1','I2','B'] if ln in self.idx and self.idx[ln][y,x]>=0]
        if len(present)<2: return
        area=math.pi*(drill-plating*1e3)*1e-3*plating
        for a,b in zip(present[:-1],present[1:]):
            L=ZPOS[b]-ZPOS[a]
            g=area/(RHO*self.tf*L)*share
            self._add(np.array([self.idx[a][y,x]]),np.array([self.idx[b][y,x]]),g)
    def terminal(self,name,cells,layers=('F',),g_link=2e3):
        """equipotential electrode tied to given cells on given layers"""
        nid=self.n+self.extra; self.extra+=1
        cnt=0
        for ln in layers:
            if ln not in self.idx: continue
            for (y,x) in cells:
                if 0<=y<NY and 0<=x<NX and self.idx[ln][y,x]>=0:
                    self._add(np.array([nid]),np.array([self.idx[ln][y,x]]),g_link); cnt+=1
        self.term[name]=nid
        if cnt==0: print('WARNING terminal',name,'has no cells')
        return cnt
    def solve(self,currents,ref):
        N=self.n+self.extra
        rows=np.concatenate(self.rows); cols=np.concatenate(self.cols); vals=np.concatenate(self.vals)
        G=sp.coo_matrix((vals,(rows,cols)),shape=(N,N)).tocsr()
        I=np.zeros(N)
        for name,cur in currents.items(): I[self.term[name]]+=cur
        # connected component containing ref
        nc,lab=sp.csgraph.connected_components(G,directed=False)
        keep=lab==lab[self.term[ref]]
        for name in currents:
            if not keep[self.term[name]]: print('WARNING terminal',name,'not connected to ref component')
        keep[self.term[ref]]=False
        ids=np.where(keep)[0]
        Gk=G[ids][:,ids].tocsc()
        V=np.zeros(N)
        t0=time.time()
        V[ids]=spl.spsolve(Gk,I[ids])
        self.V=V; self.G=G
        P=float(V@(G@V))
        return V,P
    def jmap(self,ln):
        """current density magnitude map (A/mm2) on layer"""
        ind=self.idx[ln]; g=self.t[ln]/(RHO*self.tf); V=self.V
        Vm=np.where(ind>=0,V[np.clip(ind,0,None)],np.nan)
        jx=np.zeros((NY,NX)); jy=np.zeros((NY,NX))
        dx=(Vm[:,:-1]-Vm[:,1:])*g   # A through a cell edge (cell width CELL)
        dy=(Vm[:-1,:]-Vm[1:,:])*g
        dx=np.nan_to_num(dx); dy=np.nan_to_num(dy)
        jx[:,:-1]+=dx/2; jx[:,1:]+=dx/2; jy[:-1,:]+=dy/2; jy[1:,:]+=dy/2
        J=np.hypot(jx,jy)/(CELL*1e-3)/self.t[ln]/1e6   # A/mm2
        J[ind<0]=0
        return J
