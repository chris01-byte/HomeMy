import sys; sys.path.insert(0,'<SITZUNG>/agents/mech')
from sheet import *
import json
bars={b['ref']:b for b in A2J['busbars']}
def pins(ref):
    out=[]
    for p in fps[ref]['pads']:
        out+=cells_ring(p['x'],p['y'],0.7,1.3)
    return out
def nt_strip(ref,padnum):
    f=fps[ref]; p1=[p for p in f['pads'] if p['num']=='1'][0]; p2=[p for p in f['pads'] if p['num']=='2'][0]
    xb=(p1['x']+p2['x'])/2
    sgn=1 if p2['x']>p1['x'] else -1
    y0,y1=p1['y']-5,p1['y']+5
    if padnum=='1':
        xa,xc=(xb-0.4,xb) if sgn>0 else (xb,xb+0.4)
    else:
        xa,xc=(xb,xb+0.4) if sgn>0 else (xb-0.4,xb)
    return cells_rect(xa,y0,xc,y1)
Itot=50.0
segs=[
 ('A BATT_FUSED_P  J1->RSH1.1',['BATT_FUSED_P'],[('J1',pins('J1'),('F','B'),Itot)],[('RSH1',pad_cells('RSH1',['1']),('F',),-Itot)],None),
 ('B BATT_SENSED_P RSH1.4->Q1-3 D',['BATT_SENSED_P'],[('RSH1',pad_cells('RSH1',['4']),('F',),Itot)],[(q,pad_cells(q,net='BATT_SENSED_P'),('F',),-Itot/3) for q in ['Q1','Q2','Q3']],'BB1'),
 ('C MAIN_COMMON   Q1-3 S->Q4-6 S',['MAIN_COMMON'],[(q,pad_cells(q,net='MAIN_COMMON'),('F',),Itot/3) for q in ['Q1','Q2','Q3']],[(q,pad_cells(q,net='MAIN_COMMON'),('F',),-Itot/3) for q in ['Q4','Q5','Q6']],'BB2'),
 ('D SYS_BUS_P     Q4-6 D->RSH2.1',['SYS_BUS_P'],[(q,pad_cells(q,net='SYS_BUS_P'),('F',),Itot/3) for q in ['Q4','Q5','Q6']],[('RSH2',pad_cells('RSH2',['1']),('F',),-Itot)],'BB3'),
 ('E MOTION_SENSED RSH2.4->Q7,8 D',['MOTION_SENSED_P'],[('RSH2',pad_cells('RSH2',['4']),('F',),Itot)],[(q,pad_cells(q,net='MOTION_SENSED_P'),('F',),-Itot/2) for q in ['Q7','Q8']],'BB4'),
 ('F MOTION_COMMON Q7,8 S->Q9,10 S',['MOTION_COMMON'],[(q,pad_cells(q,net='MOTION_COMMON'),('F',),Itot/2) for q in ['Q7','Q8']],[(q,pad_cells(q,net='MOTION_COMMON'),('F',),-Itot/2) for q in ['Q9','Q10']],'BB5'),
 ('G MOTION_BUS_P  Q9,10 D->J3,J5',['MOTION_BUS_P'],[(q,pad_cells(q,net='MOTION_BUS_P'),('F',),Itot/2) for q in ['Q9','Q10']],[(j,pins(j),('F','B'),-Itot/2) for j in ['J3','J5']],'BB6'),
 ('H1 ARM_L_N      J4->NT1.1',['ARM_L_N'],[('J4',pins('J4'),('F','B'),Itot/2)],[('NT1',nt_strip('NT1','1'),('F','I1','I2','B'),-Itot/2)],None),
 ('H2 ARM_R_N      J6->NT2.1',['ARM_R_N'],[('J6',pins('J6'),('F','B'),Itot/2)],[('NT2',nt_strip('NT2','1'),('F','I1','I2','B'),-Itot/2)],None),
 ('I BATT_N        NT1.2,NT2.2->J2',['BATT_N'],[('NT1',nt_strip('NT1','2'),('F','I1','I2','B'),Itot/2),('NT2',nt_strip('NT2','2'),('F','I1','I2','B'),Itot/2)],[('J2',pins('J2'),('F','I2','B'),-Itot)],'BB7'),
]
results=[]
for name,netl,srcs,sinks,barref in segs:
    for variant in (['pcb']+(['bar0','bar100'] if barref else [])):
        t0=time.time()
        bar=bars[barref] if variant!='pcb' else None
        m=Model(netl,bar=bar,contact_uohm=(100.0 if variant=='bar100' else 0.0))
        cur={}
        for (tn,cells,lays,I) in srcs+sinks:
            cnt=m.terminal(tn,cells,layers=lays)
            cur[tn]=I
        ref=sinks[0][0]
        V,P=m.solve(cur,ref)
        Iin=sum(I for (_,_,_,I) in srcs)
        Reff=P/Iin**2
        info={'seg':name,'variant':variant,'R_uohm':Reff*1e6,'P_W':P,'I':Iin,'nvia':m.nvia,'cells':{ln:int((m.idx[ln]>=0).sum()) for ln in m.layers}}
        # max current density per layer (ignore cells adjacent to terminals -> take 99.9 percentile and max)
        for ln in m.layers:
            J=m.jmap(ln)
            jj=J[m.idx[ln]>=0]
            yx=np.unravel_index(np.argmax(J),J.shape)
            info['J_'+ln]={'max':float(J.max()),'p999':float(np.percentile(jj,99.9)),'p99':float(np.percentile(jj,99)),'at':((yx[1]+0.5)*CELL,(yx[0]+0.5)*CELL)}
            if variant=='pcb' and ln in('F','B'):
                np.save(OUT+'J_%s_%s.npy'%(name.split()[0],ln),J.astype(np.float32))
        if variant!='pcb':
            # current share carried by the bar: current through contacts = sum over bar nodes? estimate as power fraction
            pass
        tv={tn:float(V[m.term[tn]]) for tn in cur}
        info['Vterm_mV']={k:v*1e3 for k,v in tv.items()}
        results.append(info)
        print('%-34s %-7s R=%7.1f uOhm  P@%2.0fA=%.3f W  vias=%d  t=%.1fs'%(name,variant,Reff*1e6,Iin,P,m.nvia,time.time()-t0))
        for ln in m.layers:
            j=info['J_'+ln]; print('      %-4s cells %7d  Jmax %.1f A/mm2 at (%.1f,%.1f)  p99.9 %.1f  p99 %.1f'%(ln,info['cells'][ln],j['max'],j['at'][0],j['at'][1],j['p999'],j['p99']))
        print('      Vterm mV',{k:round(v,3) for k,v in info['Vterm_mV'].items()})
json.dump(results,open(OUT+'sheet_results.json','w'),indent=1)
