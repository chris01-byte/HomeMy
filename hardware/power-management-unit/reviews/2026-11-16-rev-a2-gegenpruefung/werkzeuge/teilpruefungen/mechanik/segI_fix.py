import sys; sys.path.insert(0,'<SITZUNG>/agents/mech')
from sheet import *
def pins(ref):
    out=[]
    for p in fps[ref]['pads']: out+=cells_ring(p['x'],p['y'],0.7,1.3)
    return out
def nt_strip(ref,padnum):
    f=fps[ref]; p1=[p for p in f['pads'] if p['num']=='1'][0]; p2=[p for p in f['pads'] if p['num']=='2'][0]
    xb=(p1['x']+p2['x'])/2; y0,y1=p1['y']-5,p1['y']+5
    xa,xc=(xb-0.4,xb) if padnum=='1' else (xb,xb+0.4)
    return cells_rect(xa,y0,xc,y1)
I=50.0
def run(label,extra=None,layers=('F','I1','I2','B')):
    m=Model(['BATT_N'],extra_masks=extra,layers=layers)
    cur={}
    for tn,cells,lays,i in [('NT1',nt_strip('NT1','2'),('F','I1','I2','B'),I/2),('NT2',nt_strip('NT2','2'),('F','I1','I2','B'),I/2),('J2',pins('J2'),('F','I2','B'),-I)]:
        m.terminal(tn,cells,layers=lays); cur[tn]=i
    V,P=m.solve(cur,'J2')
    print('%-62s R=%.0f uOhm  P@50A=%.2f W  V(NT1)=%.1f mV V(NT2)=%.1f mV'%(label,P/I**2*1e6,P,V[m.term['NT1']]*1e3,V[m.term['NT2']]*1e3))
run('as drawn (PCB only)')
ex=np.zeros((NY,NX),dtype=bool)
ex[int(143.6/CELL):int(153.9/CELL),int(205.6/CELL):int(207.8/CELL)]=True
run('B.Cu band restored at x=206.5 (MOTION_GATE_EN track moved)',extra={'B':ex})
ex2=ex.copy()
# also hypothetically give BATT_N the F.Cu strip y 143.6..153.9 from x 205..259 (where DRIVE_N F.Cu pour is) -> not realistic; skip
run('without In2 (F+B only, as drawn)',layers=('F','B'))
