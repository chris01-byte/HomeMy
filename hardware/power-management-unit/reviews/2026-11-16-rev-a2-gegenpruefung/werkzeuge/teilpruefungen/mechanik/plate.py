import sys; sys.path.insert(0,'<SITZUNG>/agents/mech/pylib'); sys.path.insert(0,'<SITZUNG>/agents/mech')
import numpy as np, scipy.linalg as sl, json, math
from common import *
# ---- ACM 12-dof rectangular Kirchhoff plate element (w, w_x, w_y per node), numerically built
def basis(x,y):
    return np.array([1,x,y,x*x,x*y,y*y,x**3,x*x*y,x*y*y,y**3,x**3*y,x*y**3])
def dbx(x,y):  return np.array([0,1,0,2*x,y,0,3*x*x,2*x*y,y*y,0,3*x*x*y,y**3])
def dby(x,y):  return np.array([0,0,1,0,x,2*y,0,x*x,2*x*y,3*y*y,x**3,3*x*y*y])
def dxx(x,y):  return np.array([0,0,0,2,0,0,6*x,2*y,0,0,6*x*y,0])
def dyy(x,y):  return np.array([0,0,0,0,0,2,0,0,2*x,6*y,0,6*x*y])
def dxy(x,y):  return np.array([0,0,0,0,1,0,0,2*x,2*y,0,3*x*x,3*y*y])
def elem(a,b,D,nu,m_area):
    nodes=[(0,0),(a,0),(a,b),(0,b)]
    C=np.zeros((12,12))
    for i,(x,y) in enumerate(nodes):
        C[3*i]=basis(x,y); C[3*i+1]=dbx(x,y); C[3*i+2]=dby(x,y)
    Ci=np.linalg.inv(C)
    Dm=D*np.array([[1,nu,0],[nu,1,0],[0,0,(1-nu)/2]])
    gp,gw=np.polynomial.legendre.leggauss(4)
    K=np.zeros((12,12)); Mm=np.zeros((12,12)); F=np.zeros(12)
    for xi,wx in zip(gp,gw):
        for eta,wy in zip(gp,gw):
            x=(xi+1)*a/2; y=(eta+1)*b/2; w=wx*wy*a*b/4
            Bm=np.vstack([dxx(x,y),dyy(x,y),2*dxy(x,y)])@Ci
            N=basis(x,y)@Ci
            K+=w*Bm.T@Dm@Bm; Mm+=w*m_area*np.outer(N,N); F+=w*N
    return K,Mm,F
def run(label,D=14.0,nu=0.15,m_board=3.9,extra_masses=None,area_masses=None,supports=None,verbose=True):
    xs=sorted(set(list(np.arange(0,281,10.0))+[9.0,64.0,202.0,271.0,20.0]))
    ys=sorted(set(list(np.arange(0,261,10.0))+[9.0,251.0,112.0,138.0]))
    xs=np.array(xs)/1000; ys=np.array(ys)/1000
    nx,ny=len(xs),len(ys)
    nid=lambda i,j: j*nx+i
    ndof=3*nx*ny
    K=np.zeros((ndof,ndof)); Mg=np.zeros((ndof,ndof)); Fg=np.zeros(ndof)
    for j in range(ny-1):
        for i in range(nx-1):
            a=xs[i+1]-xs[i]; b=ys[j+1]-ys[j]
            xc=(xs[i]+xs[i+1])/2*1000; yc=(ys[j]+ys[j+1])/2*1000
            m=m_board
            if area_masses:
                for (x0,y0,x1,y1,mass_kg) in area_masses:
                    # smear mass over rectangle
                    if x0<=xc<=x1 and y0<=yc<=y1:
                        m+=mass_kg/((x1-x0)*(y1-y0)*1e-6)
            Ke,Me,Fe=elem(a,b,D,nu,m)
            n=[nid(i,j),nid(i+1,j),nid(i+1,j+1),nid(i,j+1)]
            dofs=sum([[3*k,3*k+1,3*k+2] for k in n],[])
            K[np.ix_(dofs,dofs)]+=Ke; Mg[np.ix_(dofs,dofs)]+=Me; Fg[dofs]+=Fe*m*9.81
    if extra_masses:
        for (x,y,mk) in extra_masses:
            i=int(np.argmin(abs(xs-x/1000))); j=int(np.argmin(abs(ys-y/1000)))
            Mg[3*nid(i,j),3*nid(i,j)]+=mk; Fg[3*nid(i,j)]+=mk*9.81
    fixed=[]
    for (x,y) in supports:
        i=int(np.argmin(abs(xs-x/1000))); j=int(np.argmin(abs(ys-y/1000)))
        fixed.append(3*nid(i,j))
    free=np.setdiff1d(np.arange(ndof),fixed)
    Kf=K[np.ix_(free,free)]; Mf=Mg[np.ix_(free,free)]
    w,v=sl.eigh(Kf,Mf,subset_by_index=[0,5])
    f=np.sqrt(np.maximum(w,0))/(2*np.pi)
    u=np.zeros(ndof); u[free]=np.linalg.solve(Kf,Fg[free])
    wdisp=u[0::3].reshape(ny,nx)
    jmax=np.unravel_index(np.argmax(np.abs(wdisp)),wdisp.shape)
    mtot=Fg[0::3].sum()/9.81
    if verbose:
        print('%-58s total mass %.0f g | f1..f4 = %s Hz | 1g sag max %.2f mm at (%.0f,%.0f) mm'%(label,mtot*1000,', '.join('%.1f'%x for x in f[:4]),abs(wdisp[jmax])*1000,xs[jmax[1]]*1000,ys[jmax[0]]*1000))
    return f,wdisp
H=[(9,9),(271,9),(202,251),(64,251)]
bars=[]
for bb in A2J['busbars']:
    xs_=[p[0] for p in bb['outline']]; ys_=[p[1] for p in bb['outline']]
    from shapely.geometry import Polygon
    P=Polygon(bb['outline'])
    for c in bb['cutouts']: P=P.difference(Polygon(c['outline']))
    mass=P.area*2.0*8.96e-6  # kg
    bars.append((min(xs_),min(ys_),max(xs_),max(ys_),mass,bb['ref']))
    print(bb['ref'],'area %.0f mm2 mass %.1f g'%(P.area,mass*1000))
nb=8*20*10*2*8.96e-6
print('NB bridges total %.1f g; bars total %.1f g'%(nb*1000,sum(b[4] for b in bars)*1000))
area_m=[b[:5] for b in bars]+[(16,133,258,143,nb+0.070)]   # NB + ~70 g hardware smeared along NT row (approx)
lumps=[(20,50,0.0068),(20,112,0.0068),(222,18,0.0068),(252,18,0.0068),(263,50,0.0068),(263,82,0.0068),   # REDCUBE
       (48,151,0.013),(138,151,0.013),(255,178,0.0065),(255,195,0.0065),(149,245,0.004),                 # film caps, electrolytics
       (244,232,0.002)]
lumps+=[(x,y,0.003) for (x,y) in [(269,108),(269,134),(11,159),(11,185),(11,211),(269,160),(269,212),(269,186),(110,249)]]  # MSTB
lumps+=[(x,y,0.0012) for (x,y) in [(60,30),(60,55),(60,80),(90,30),(90,55),(90,80),(155,35),(155,70),(185,35),(185,70)]]
print('lumped component mass %.0f g'%(sum(l[2] for l in lumps)*1000))
run('bare PCB (D=14 Nm, 3.9 kg/m2), 4 M3 points',supports=H)
run('PCB + components (no bars)',supports=H,extra_masses=lumps)
run('PCB + components + bars/hardware as dead mass',supports=H,extra_masses=lumps,area_masses=area_m)
run('same, FR-4-only stiffness D=7.7 Nm (pessimistic)',D=7.7,supports=H,extra_masses=lumps,area_masses=area_m)
run('same, D=14, +2 extra supports at (20,81),(140,130)',supports=H+[(20,81),(140,130)],extra_masses=lumps,area_masses=area_m)
