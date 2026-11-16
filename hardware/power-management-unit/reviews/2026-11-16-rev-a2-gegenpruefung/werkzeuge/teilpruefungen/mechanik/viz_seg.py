import sys; sys.path.insert(0,'<SITZUNG>/agents/mech')
from sheet import *
import matplotlib; matplotlib.use('Agg')
import matplotlib.pyplot as plt
def pins(ref):
    out=[]
    for p in fps[ref]['pads']:
        out+=cells_ring(p['x'],p['y'],0.7,1.3)
    return out
def nt_strip(ref,padnum):
    f=fps[ref]; p1=[p for p in f['pads'] if p['num']=='1'][0]; p2=[p for p in f['pads'] if p['num']=='2'][0]
    xb=(p1['x']+p2['x'])/2
    y0,y1=p1['y']-5,p1['y']+5
    xa,xc=(xb-0.4,xb) if padnum=='1' else (xb,xb+0.4)
    return cells_rect(xa,y0,xc,y1)
def run(name,netl,terms,ref,crop,fn,bar=None,contact=0.0,vmaxJ=40):
    m=Model(netl,bar=bar,contact_uohm=contact)
    cur={}
    for tn,cells,lays,I in terms:
        m.terminal(tn,cells,layers=lays); cur[tn]=I
    V,P=m.solve(cur,ref)
    Iin=sum(I for *_,I in terms if I>0)
    print(name,'R=%.1f uOhm P=%.3f W'%(P/Iin**2*1e6,P))
    x0,y0,x1,y1=crop
    L=m.layers
    fig,axs=plt.subplots(2,len(L),figsize=(5.2*len(L),9))
    for i,ln in enumerate(L):
        ind=m.idx[ln]
        Vm=np.where(ind>=0,V[np.clip(ind,0,None)],np.nan)*1e3
        J=m.jmap(ln); J[ind<0]=np.nan
        sl=(slice(int(y0/CELL),int(y1/CELL)),slice(int(x0/CELL),int(x1/CELL)))
        ax=axs[0][i]; im=ax.imshow(Vm[sl],extent=[x0,x1,y1,y0],cmap='turbo'); ax.set_title('%s  V [mV]'%ln); plt.colorbar(im,ax=ax,shrink=0.6)
        ax=axs[1][i]; im=ax.imshow(J[sl],extent=[x0,x1,y1,y0],cmap='inferno',vmin=0,vmax=vmaxJ); ax.set_title('%s  |J| [A/mm2]'%ln); plt.colorbar(im,ax=ax,shrink=0.6)
    fig.suptitle('%s  R=%.0f uOhm, P=%.2f W'%(name,P/Iin**2*1e6,P))
    fig.tight_layout(); fig.savefig(OUT+fn,dpi=70); plt.close(fig)
    return m,V,P
if __name__=='__main__':
    I=50.0
    run('BATT_N pcb-only NT1.2+NT2.2 -> J2 @50A',['BATT_N'],[('NT1',nt_strip('NT1','2'),('F','I1','I2','B'),I/2),('NT2',nt_strip('NT2','2'),('F','I1','I2','B'),I/2),('J2',pins('J2'),('F','I2','B'),-I)],'J2',(0,95,280,160),'viz_BATTN.png')
