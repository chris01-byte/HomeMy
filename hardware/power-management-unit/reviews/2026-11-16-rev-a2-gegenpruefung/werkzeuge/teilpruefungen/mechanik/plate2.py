import sys; sys.path.insert(0,'<SITZUNG>/agents/mech/pylib'); sys.path.insert(0,'<SITZUNG>/agents/mech')
import numpy as np, scipy.linalg as sl
import plate as P   # reuses elem(); running plate prints its table again
def compliance(points,D=14.0,nu=0.15,supports=P.H):
    xs=sorted(set(list(np.arange(0,281,10.0))+[9.0,64.0,202.0,271.0,20.0,222.0,252.0,263.0]))
    ys=sorted(set(list(np.arange(0,261,10.0))+[9.0,251.0,112.0,138.0,18.0,82.0]))
    xs=np.array(xs)/1000; ys=np.array(ys)/1000
    nx,ny=len(xs),len(ys); nid=lambda i,j:j*nx+i; ndof=3*nx*ny
    K=np.zeros((ndof,ndof))
    for j in range(ny-1):
        for i in range(nx-1):
            Ke,Me,Fe=P.elem(xs[i+1]-xs[i],ys[j+1]-ys[j],D,nu,1.0)
            n=[nid(i,j),nid(i+1,j),nid(i+1,j+1),nid(i,j+1)]
            dofs=sum([[3*k,3*k+1,3*k+2] for k in n],[])
            K[np.ix_(dofs,dofs)]+=Ke
    fixed=[3*nid(int(np.argmin(abs(xs-x/1000))),int(np.argmin(abs(ys-y/1000)))) for x,y in supports]
    free=np.setdiff1d(np.arange(ndof),fixed)
    Kf=K[np.ix_(free,free)]
    for name,(x,y) in points.items():
        F=np.zeros(ndof); k=3*nid(int(np.argmin(abs(xs-x/1000))),int(np.argmin(abs(ys-y/1000)))); F[k]=10.0
        u=np.zeros(ndof); u[free]=np.linalg.solve(Kf,F[free])
        print('   10 N vertical at %-3s (%g,%g): deflection %.2f mm  (stiffness %.1f N/mm)'%(name,x,y,u[k]*1000,10/(u[k]*1000)))
print('--- point-load compliance at terminals, 4 mounting points, D=14 N.m')
compliance({'J1':(20,50),'J2':(20,112),'J3':(222,18),'J5':(252,18),'J4':(263,50),'J6':(263,82),'centre':(140,130)})
