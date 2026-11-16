import sys; sys.path.insert(0,'<SITZUNG>/agents/mech')
from sheet import *
def pins(ref):
    out=[]
    for p in fps[ref]['pads']: out+=cells_ring(p['x'],p['y'],0.7,1.3)
    return out
I=50.0
for lays in (('F',),('F','B'),('F','I1','I2','B')):
    m=Model(['BATT_FUSED_P'],layers=lays)
    m.terminal('J1',pins('J1'),layers=tuple(l for l in lays if l in('F','B')))
    m.terminal('RSH1',pad_cells('RSH1',['1']),layers=('F',))
    V,P=m.solve({'J1':I,'RSH1':-I},'RSH1')
    # local power near shunt pad (within 5 mm box of pad)
    J=m.jmap('F')
    print('layers',lays,'R=%.1f uOhm P=%.3f W; F.Cu Jmax %.0f A/mm2, p99 %.0f'%(P/I**2*1e6,P,J.max(),np.percentile(J[m.idx['F']>=0],99)))
# current through each J1 pin row on F.Cu: integrate J across x=27 line
m=Model(['BATT_FUSED_P'])
m.terminal('J1',pins('J1'),layers=('F','B')); m.terminal('RSH1',pad_cells('RSH1',['1']),layers=('F',))
V,P=m.solve({'J1':I,'RSH1':-I},'RSH1')
for ln in ['F','B']:
    ind=m.idx[ln]; g=m.t[ln]/RHO
    xi=int(27.0/CELL)
    a=ind[:,xi]; b=ind[:,xi+1]; k=(a>=0)&(b>=0)
    cur=((V[a[k]]-V[b[k]])*g).sum()
    print(ln,'current crossing x=27 mm toward RSH1: %.1f A'%cur)
