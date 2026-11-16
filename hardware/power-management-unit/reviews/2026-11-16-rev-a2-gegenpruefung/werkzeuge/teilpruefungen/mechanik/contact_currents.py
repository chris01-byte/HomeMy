import sys; sys.path.insert(0,'<SITZUNG>/agents/mech')
from sheet import *
bars={b['ref']:b for b in A2J['busbars']}
def pins(ref):
    out=[]
    for p in fps[ref]['pads']: out+=cells_ring(p['x'],p['y'],0.7,1.3)
    return out
def nt_strip(ref,padnum):
    f=fps[ref]; p1=[p for p in f['pads'] if p['num']=='1'][0]; p2=[p for p in f['pads'] if p['num']=='2'][0]
    xb=(p1['x']+p2['x'])/2; y0,y1=p1['y']-5,p1['y']+5
    xa,xc=(xb-0.4,xb) if padnum=='1' else (xb,xb+0.4)
    return cells_rect(xa,y0,xc,y1)
def contact_currents(m):
    out={}
    ln,bb=m.bars[0]
    V=m.V
    for h in bb['holes']:
        ring=cells_ring(h['x'],h['y'],1.7,4.0)
        ring=[(y,x) for (y,x) in ring if m.idx[ln][y,x]>=0 and m.idx['B'][y,x]>=0]
        gc=1.0/max(m.contact_R,0.2e-6)/len(ring)
        I=sum((V[m.idx['B'][y,x]]-V[m.idx[ln][y,x]])*gc for (y,x) in ring)
        out[h['function']]=I
    return out
I=50.0
for Rc in (0.0,100.0,300.0):
    m=Model(['BATT_N'],bar=bars['BB7'],contact_uohm=Rc); m.contact_R=Rc*1e-6
    cur={}
    for tn,cells,lays,i in [('NT1',nt_strip('NT1','2'),('F','I1','I2','B'),I/2),('NT2',nt_strip('NT2','2'),('F','I1','I2','B'),I/2),('J2',pins('J2'),('F','I2','B'),-I)]:
        m.terminal(tn,cells,layers=lays); cur[tn]=i
    V,P=m.solve(cur,'J2')
    cc=contact_currents(m)
    print('BB7 Rc=%3.0f uOhm: R=%.0f uOhm P=%.2f W ; contact currents PCB->bar [A]: %s'%(Rc,P/I**2*1e6,P,{k:round(v,1) for k,v in cc.items()}))
for Rc in (0.0,100.0,300.0):
    m=Model(['MOTION_BUS_P'],bar=bars['BB6'],contact_uohm=Rc); m.contact_R=Rc*1e-6
    cur={}
    for tn,cells,lays,i in [(q,pad_cells(q,net='MOTION_BUS_P'),('F',),I/2) for q in ['Q9','Q10']]+[(j,pins(j),('F','B'),-I/2) for j in ['J3','J5']]:
        m.terminal(tn,cells,layers=lays); cur[tn]=i
    V,P=m.solve(cur,'J3')
    cc=contact_currents(m)
    print('BB6 Rc=%3.0f uOhm: R=%.0f uOhm P=%.2f W ; contact currents PCB->bar [A]: %s'%(Rc,P/I**2*1e6,P,{k:round(v,1) for k,v in cc.items()}))
# BB1 for reference
for Rc in (0.0,100.0):
    m=Model(['BATT_SENSED_P'],bar=bars['BB1'],contact_uohm=Rc); m.contact_R=Rc*1e-6
    cur={}
    for tn,cells,lays,i in [('RSH1',pad_cells('RSH1',['4']),('F',),I)]+[(q,pad_cells(q,net='BATT_SENSED_P'),('F',),-I/3) for q in ['Q1','Q2','Q3']]:
        m.terminal(tn,cells,layers=lays); cur[tn]=i
    V,P=m.solve(cur,'Q1')
    print('BB1 Rc=%3.0f: contact currents'%Rc,{k:round(v,2) for k,v in contact_currents(m).items()})
