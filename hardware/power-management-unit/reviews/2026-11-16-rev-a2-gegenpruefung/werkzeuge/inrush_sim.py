#!/usr/bin/env python3
"""Abschaetzung: Einschalten des Motion-Gates (TPS48110, R34 = 180 k, kein Gate-Kondensator) in eine
kapazitive Last, verglichen mit der SOA des PSMN1R0-100ASF (Datenblatt Fig. 3, Tmb = 25 C, abgelesen).

Vereinfachungen: Sourcefolger-Modell, quadratische Kennlinie (25 A bei 4,3 V Plateau je FET),
Crss(V) stueckweise an Crss(50 V) und QGD angepasst, konservativ traegt EIN FET den gesamten Strom.
Kein Ersatz fuer eine Messung. Aufruf: python3 inrush_sim.py  (schreibt daten/inrush_sim.json)
"""
# Model: source follower. Gate current Ig=(Vbst-Vgs)/R34 - Vgs/Rbleed charges Cgs_tot and Miller cap of the 2 input-bank FETs.
import math
def crss(vds, c50=123e-12):
    # piecewise fit to PSMN1R0-100ASF: Crss(50V)=c50 typ, Qgd(0..50V)~69.5nC typ -> plateau 5nF below 8V then (8/V)^2.1
    scale=c50/107e-12
    return scale*(5e-9 if vds<8 else 5e-9*(8.0/vds)**2.1)
def soa_asf(vds,t):
    # read from datasheet Fig.3 (Tmb=25C): piecewise power laws, clipped
    def l100u(v): return 11000.0/v
    def l1m(v): return 440*(10.0/v)**2.1 if v>10 else 1400*(3.0/v)**0.96
    def l10m(v): return 1.7*(100.0/v)**1.752
    def l100m(v): return 0.95*(100.0/v)**1.477
    pts=[(1e-4,l100u(vds)),(1e-3,l1m(vds)),(1e-2,l10m(vds)),(1e-1,l100m(vds))]
    if t<=pts[0][0]: return pts[0][1]
    for (t0,i0),(t1,i1) in zip(pts,pts[1:]):
        if t<=t1:
            f=(math.log10(t)-math.log10(t0))/(math.log10(t1)-math.log10(t0))
            return 10**(math.log10(i0)+f*(math.log10(i1)-math.log10(i0)))
    return pts[-1][1]
def run(Cload, nshare=2, Vin=42.0, Vbst=12.0, R34=180e3, Vth=3.0, c50=123e-12, K1=14.8, Iload=0.0):
    Rbleed=10e6/4; Cgs=4*24e-9+2*5e-9
    vgs=0.0; vo=0.0; t=0.0; dt=2e-7
    ipk=0; ppk=0; e=0; t_on=None; t_end=None; worst=0; worst_at=None
    K=K1*nshare
    while t<0.2:
        vds=Vin-vo
        idf=K*max(0.0,vgs-Vth)**2
        if vds<=0.02: idf=min(idf,(Iload+1e-9)); 
        ig=(Vbst-vgs)/R34 - vgs/Rbleed
        cgd=2*crss(max(vds,0.0),c50)
        dvo=(idf-Iload)/Cload if (idf>Iload or vo>0) else 0.0
        if vds<=0.02: dvo=0.0
        dvgs=(ig - cgd*dvo)/(Cgs+cgd)
        vgs+=dvgs*dt; vo=min(Vin,max(0.0,vo+dvo*dt)); t+=dt
        if idf>0.05 and t_on is None: t_on=t
        p=idf*vds; e+=p*dt
        if idf>ipk: ipk=idf
        if p>ppk: ppk=p; 
        if t_on is not None and vds>1.0:
            # running check vs SOA for elapsed conduction time, per-FET current (worst: hogging by one FET)
            el=t-t_on
            for share,tag in ((1.0,'1FET'),):
                lim=soa_asf(vds,max(el,1e-4))
                r=(idf*share)/lim
                if r>worst: worst=r; worst_at=(round(el*1e3,2),round(vds,1),round(idf,1),round(lim,1))
        if vds<=0.02 and t_end is None and t_on is not None: t_end=t; break
    return dict(Cload_uF=Cload*1e6, t_delay_ms=round((t_on or 0)*1e3,2), ramp_ms=round(((t_end or t)-(t_on or 0))*1e3,2), Ipk_A=round(ipk,1), Ppk_W=round(ppk), E_J=round(e,2), worst_ratio_vs_SOA_singleFET=round(worst,2), at_ms_Vds_I_lim=worst_at)
if __name__=='__main__':
    import json, os, _common as C
    res={}
    print('C_rss check: Qgd(0..50V) =', round(sum(crss(v+0.05)*0.1 for v in [i*0.1 for i in range(500)])*1e9,1),'nC ; Crss(42V)=',round(crss(42)*1e12),'pF')
    for Cl in (752e-6,940e-6,1128e-6,2000e-6,4000e-6,8000e-6):
        r=run(Cl); res[f'C={Cl*1e6:.0f}uF']=r; print(r)
    print('-- Crss min/max corners at 940uF')
    res['940uF_Crss50_min_12pF']=run(940e-6,c50=12e-12); res['940uF_Crss50_max_321pF']=run(940e-6,c50=321e-12)
    print('c50=12pF :',res['940uF_Crss50_min_12pF']); print('c50=321pF:',res['940uF_Crss50_max_321pF'])
    res['940uF_Vth_2V']=run(940e-6,Vth=2.0); res['940uF_Vth_4V']=run(940e-6,Vth=4.0)
    print('-- Vth 2V/4V bei 940uF'); print(res['940uF_Vth_2V']); print(res['940uF_Vth_4V'])
    res['soa_asf_25C_A']={f'{v}V':{t:round(soa_asf(v,s),1) for t,s in (('100us',1e-4),('1ms',1e-3),('10ms',1e-2),('100ms',1e-1))} for v in (20,30,42)}
    json.dump(res,open(os.path.join(C.OUT,'inrush_sim.json'),'w'),indent=1)
