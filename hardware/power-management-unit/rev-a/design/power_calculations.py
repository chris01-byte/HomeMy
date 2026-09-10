"""Reproducible engineering estimates. Does not simulate hardware or prove SOA.

Run with Python3. Writes JSON to the power evidence directory. All bounds are
labelled either table-supported or conditional on explicit prototype assumptions.
"""
import itertools
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUT=HERE.parent/'evidence'/'power'/'calculated.json'
rtol=.001
rsh=.0005
# Initial tolerance1%, full-device100ppm/K across100K used conservatively.
shlo=rsh*.99*.99
shhi=rsh*1.01*1.01

def div_bounds(top,bottom,threshold,leak=0):
    lo,nom,hi=threshold
    return dict(nominal_v=nom*(1+top/bottom),
      minimum_v=lo*(1+top*(1-rtol)/(bottom*(1+rtol)))-leak*top*(1+rtol),
      maximum_v=hi*(1+top*(1+rtol)/(bottom*(1-rtol)))+leak*top*(1+rtol))

def timer_time(c,r,i,v,ileak=0):
    vfinal=r*(i-ileak)
    if vfinal<=v: return float('inf')
    return -r*c*math.log1p(-v/vfinal)

def timing(i,vt):
    nominal=timer_time(33e-6,100e3,i[1],vt[1])
    corners=[timer_time(c,r,src,v,leak)
      for c,r,src,v,leak in itertools.product(
        [33e-6*.9*.98,33e-6*1.1*1.02],
        [100e3*.999,100e3*1.001],
        [i[0],i[2]],[vt[0],vt[2]],[0,1e-6])]
    return dict(nominal_s=nominal,conditional_min_s=min(corners),conditional_max_s=max(corners),
      assumptions='C33uF10%, +/-2% additional drift, R100k0.1%, capacitor/PCB leakage0..1uA, local0..60C; fulltemperature not guaranteed')

result={
 'scope':'Engineering calculations, not physical test results or a fabrication/energization approval',
 'shunt':dict(r_nominal_ohm=rsh,r_corner_ohm=[shlo,shhi],
    steady_w={str(i):i*i*rsh for i in [45,50,60,65,100,120,150]},
    pulse_150a_3s_j=150**2*rsh*3,
    bourns_qualification_50w_5s_j=50*5,
    note='250J is the stated5x10W5s short-time overload qualification atspecified conditions, not a shape-independent rating'),
 'thresholds':{
  'main_uv_falling':div_bounds(523e3,10.1e3,[.533,.55,.573],200e-9),
  'main_uv_rising':div_bounds(523e3,10.1e3,[.585,.6,.63],200e-9),
  'main_ov_rising':div_bounds(732e3,10e3,[.585,.6,.63],200e-9),
  'motion_uv_rising':div_bounds(226e3,10e3,[1.16,1.18,1.2],320e-9),
  'motion_native_uv_falling':div_bounds(226e3,10e3,[1.10,1.11,1.13],320e-9),
  'motion_external_latched_uv_nominal_v':1.242*(1+226000/10000),
  'motion_external_latched_uv_conservative_min_v':(1.223*.99-.009-.008-.0025-.0015)*(1+226000*.9965/(10000*1.0035)),
  'motion_external_latched_uv_conservative_max_v':(1.260*1.01+.009+.008+.0025+.0015)*(1+226000*1.0035/(10000*.9965)),
  'motion_external_uv_bound_notes':'Referenceinitial1.223..1.260V,100ppm/K100K,offset9mV,entire8mVhysteresis,2.5mVCMRRallowance,1.5mVPSRRallowance,R0.1%+25ppm/K100K; staticengineeringbounds not shortpulse immunity proof. Native EN fallingtable1.10..1.13V. U5OD joins externalmotionfaultlatch.',
  'motion_ov':'U2OV grounded. Independentchopper46V comparatorfeeds latchedmotioninhibit; nativeautorecoveringOVnotused.',
  'efuse_uv_rising':div_bounds(191e3,10e3,[1.176,1.2,1.224],150e-9),
  'efuse_ov_rising':div_bounds(374e3,10e3,[1.176,1.2,1.224],150e-9),
  'main_oc_equation_nominal_a':12*49.9/(18.4e3*rsh),
  'main_oc_bound_status':'No guaranteed65A window: published CSA error6..30mV does not cover nominal32.5mV, and mirror/OCP error correlation not specified',
  'main_scp_nominal_a':(.020+3650*11e-6)/rsh,
  'main_scp_min_a':(.0174+3650*.999*9.5e-6)/shhi,
  'main_scp_max_a':(.022+3650*1.001*12e-6)/shlo,
  'motion_oc_equation_nominal_a':11.9*100/(39700*rsh),
  'motion_oc_table_min_a':.0292*.999/1.001/shhi,
  'motion_oc_table_max_a':.0315*1.001/.999/shlo,
  'motion_scp_nominal_a':(2740+464)*15.6e-6/rsh,
  'motion_scp_conservative_min_a':(.035+(2740*.999-2100)*13.7e-6)/shhi,
  'motion_scp_conservative_max_a':(.045+(2740*1.001-2100)*17.6e-6)/shlo,
  'current_corner_notes':'Shunt1% plus100ppm/K100K. MotionOCP scales exactRSET100/RIWRN39.7k datasheet29.2..31.5mV table; SCP uses40+/-5mV table at2100ohm andspecifiedbias fordeltaR.'},
 'timers':{
  'main_FLT':timing([65e-6,85e-6,97e-6],[1.04,1.1,1.2]),
  'main_native_gate_off':timing([65e-6,85e-6,97e-6],[1.1,1.2,1.4]),
  'motion_FLT':timing([73e-6,82e-6,91e-6],[1.03,1.1,1.2]),
  'motion_native_gate_off':timing([73e-6,82e-6,91e-6],[1.112,1.2,1.3]),
  'external_latch_note':'External hardware latchesactonFLT, which precedes nativegate-off; useFLT bounds for actual disconnection.'},
 'conduction':[],
 'gate':{
   'mosfet_max_qg_c':539e-9,'mosfet_max_qgd_c':160e-9,
   'main_max_charge_time_s':3*539e-9/(39e-6-3*14.5/10e6-3*100e-9),
   'main_typical_miller_ramp_s':3*69.5e-9/55e-6,
   'main_min_miller_ramp_s_estimate':3*21e-9/75e-6,
   'motion_max_total_gate_c':4*539e-9,
   'motion_cap_min_for_1v_droop_f':4*539e-9,
   'motion_boost_startup_s_estimate':9.4e-6*12/80e-6,
   'motion_boost_effective_f_estimate':9.4e-6*.6*.9*.85*.9,
   'note':'Charge ratios are approximate startup estimates, not assured slew times; nonlinear gatecharge, idealdiode regulation and common-source trajectory require waveform review.'},
 'motion_bus_inrush':{
   'capacitor_nominal_f':940e-6,'capacitor_min_f':752e-6,'capacitor_max_f':1128e-6,
   'energy42v_nominal_j':.5*940e-6*42**2,'energy42v_max_j':.5*1128e-6*42**2,
   'RPU_ohm':180000,'each_gate_source_bleed_ohm':10e6,
   'miller_typical_gate_current_a':(12-4.3)/180000-4*4.3/10e6-4*100e-9,
   'miller_typical_ramp_s_estimate':2*69.5e-9/((12-4.3)/180000-4*4.3/10e6-4*100e-9),
   'nominal_average_inrush_a_estimate':940e-6*42/(2*69.5e-9/((12-4.3)/180000-4*4.3/10e6-4*100e-9)),
   'fast_table_point_ramp_s_estimate':2*21e-9/((13-2)/180000),
   'max_cap_average_at_fast_table_point_a_estimate':1128e-6*42/(2*21e-9/((13-2)/180000)),
   'steady_gate11vboost_nominal_parts_v':(11-180000*4*100e-9)/(1+180000*4/10e6),
   'steady_gate11vboost_RPUplus2percent_bleedsminus3percent_v':(11-180000*1.02*4*100e-9)/(1+180000*1.02*4/(10e6*.97)),
   'limitations':'Only2inputbankQgd credited: outputbank can followbodydiode andneednot contributeMiller. Qgd21/69.5/160nC specified50V25A25C,plateau4.3Vtyp; fastmodel2Vplateauassumed. Valuesareestimatesnot guaranteed42Vlowcurrentcold/hotinrushbounds. NoequalparallelSOAsharingcredit.1AsupplymaytripSYS/mainUV,not guaranteedfunctionalboot. FirstanalogchoptestusesseparatecurrentlimitedfixtureprechargingmotioncapacitorswithmotiongateOFF; powerpathinrushtestfollowswaveformreview.'},
 'bench_inrush':{
   'max_direct_bus_cap_f':100e-6,'max_supply_current_a':1,'max_start_voltage_v':42,
   'stored_capacitor_energy_j':.5*100e-6*42**2,
   'resistor_charge_upper_mosfet_energy_j':.5*100e-6*42**2,
   'no_parallel_linear_sharing_credit':True,
   'gate_off_25us_42v_120a_engineering_allowance_energy_j':42*120*25e-6,
   'line_L_2uh_120a_j':.5*2e-6*120**2,
   'limits':'Initial motorless supply1A, localambient20..30C, no externalconverter input untilcapacitance/inrush bounded; capturedstartup<=100ms. SOA visualbench check only.'},
 'efuses':{
   'pc_nominal_ilim_a':18000/6040,'logic_nominal_ilim_a':18000/9090,
   'current_limit_engineering_plusminus_percent':10,
   'pc_max_assumed_a':18000/(6040*.999)*1.10,
   'logic_max_assumed_a':18000/(9090*.999)*1.10,
   'pulse_overload_note':'TPS26631 can pass2x programmed current during overloadpulse window; branch harness/converter must tolerate thatpulse.',
   'dvdt_22nf_nominal_v_s':2e-6/22e-9*25,
   'ramp42v_nominal_s':42/(2e-6/22e-9*25),
   'ramp42v_min_s':42/((2.225e-6)/(22e-9*.95)*26),
   'ramp42v_max_s':42/((1.775e-6)/(22e-9*1.05)*23.5),
   'pc65w_current_at29v_a':65/29,
   'logic25w_current_at29v_85percent_a':25/(29*.85)},
 'motion_imon':{
   'load_resistance_ohm':1/(1/10000+1/(20000+10000)),
   'isolated_input_v_per_a_unloaded':.9*7500/100*rsh/3,
   'input_max_v_from_7p5v_abs_raw':7.5*(10000*1.001)/(20000*.999+10000*1.001),
   'with_wake_100k_adc_pulldown_v_per_a':.9/100*rsh*(1/(1/10000+1/(20000+1/(1/10000+1/100000))))*(1/(1/10000+1/100000))/(20000+1/(1/10000+1/100000)),
   'note':'FinalADCpulldown changes load/sensitivity; calibrate using completeintegratednetlist, not nominalunloadedgain.'},
 'selectivity':'NOT PROVEN: currentthreshold andtimerintervals overlap. Bothmain/motion maytrip. FuseBMS curves unknown. Final selectivity is RevBvalidation; external60Afuse identification remains prebattery energizationgate.'
}
for i in [45,50,60,65]:
    result['conduction'].append(dict(current_a=i,main_fet_w=i*i*2*.0023/3,
     motion_fet_w=i*i*2*.0023/2,main_shunt_w=i*i*rsh,
     motion_shunt_w=i*i*rsh,main_fet_w_3p2mR_assumption=i*i*2*.0032/3,
     motion_fet_w_3p2mR_assumption=i*i*.0032,
     note='2.3mR manufacturerhotmax requires10Vgate;3.2mR is an engineering fallbackassumption for mainminimum9.2V, not a guaranteedtablemax'))
OUT.parent.mkdir(parents=True,exist_ok=True)
OUT.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(json.dumps(result,indent=2))
