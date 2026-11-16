import sys; sys.path.insert(0,'<SITZUNG>/agents/mech')
from sheet import *
bars={b['ref']:b for b in A2J['busbars']}
def contact_currents(m):
    out={}
    ln,bb=m.bars[0]; V=m.V
    for h in bb['holes']:
        ring=cells_ring(h['x'],h['y'],1.7,4.0)
        ring=[(y,x) for (y,x) in ring if m.idx[ln][y,x]>=0 and m.idx['B'][y,x]>=0]
        gc=1.0/max(m.contact_R,0.2e-6)/len(ring)
        out[h['function']]=float(sum((V[m.idx['B'][y,x]]-V[m.idx[ln][y,x]])*gc for (y,x) in ring))
    return out
I=50.0
cases=[('BB2','MAIN_COMMON',[(q,pad_cells(q,net='MAIN_COMMON'),('F',),I/3) for q in ['Q1','Q2','Q3']]+[(q,pad_cells(q,net='MAIN_COMMON'),('F',),-I/3) for q in ['Q4','Q5','Q6']],'Q4'),
 ('BB3','SYS_BUS_P',[(q,pad_cells(q,net='SYS_BUS_P'),('F',),I/3) for q in ['Q4','Q5','Q6']]+[('RSH2',pad_cells('RSH2',['1']),('F',),-I)],'RSH2'),
 ('BB4','MOTION_SENSED_P',[('RSH2',pad_cells('RSH2',['4']),('F',),I)]+[(q,pad_cells(q,net='MOTION_SENSED_P'),('F',),-I/2) for q in ['Q7','Q8']],'Q7'),
 ('BB5','MOTION_COMMON',[(q,pad_cells(q,net='MOTION_COMMON'),('F',),I/2) for q in ['Q7','Q8']]+[(q,pad_cells(q,net='MOTION_COMMON'),('F',),-I/2) for q in ['Q9','Q10']],'Q9')]
for bref,net,terms,ref in cases:
    for Rc in (0.0,100.0):
        m=Model([net],bar=bars[bref],contact_uohm=Rc); m.contact_R=Rc*1e-6
        cur={}
        for tn,cells,lays,i in terms:
            m.terminal(tn,cells,layers=lays); cur[tn]=i
        V,P=m.solve(cur,ref)
        print(bref,net,'Rc=%3.0f uOhm: R=%.1f uOhm; contact currents [A] %s'%(Rc,P/I**2*1e6,{k:round(v,2) for k,v in contact_currents(m).items()}))
