"""Deterministic threshold corner sweep and conservative conductor estimates."""
from pathlib import Path
from itertools import product
import json, math

ROOT=Path(__file__).parent
temp_delta=45 # prototype0..70C relative to25C
res_error=.001+25e-6*temp_delta
ref_error=.0005+3e-6*temp_delta+.0003 # initial+drift+aging/hysteresis allowance
vref=[2.5*(1-ref_error),2.5*(1+ref_error)]
rt=[161400*(1-res_error),161400*(1+res_error)]
rb=[10000*(1-res_error),10000*(1+res_error)]
rf=[2690000*(1-res_error),2690000*(1+res_error)]
# Both series upper resistors and all three feedback resistors can drift together.
gate_hi=[9.9705*(1-.027),9.9705*(1+.027)]
gate_lo=[0,.05]
offset=[-.0055,.0055]
ib=[-50e-9,50e-9] # conservative signed bias allowance
def bounds(gates):
    points=[(vr+vo)*(1+t/b+t/f)-vg*t/f+i*t
        for vr,vo,t,b,f,vg,i in product(vref,offset,rt,rb,rf,gates,ib)]
    return [min(points),max(points)]
ov=[(vr+vo)*(1+t/b)+i*t for vr,vo,t,b,i in product(vref,offset,
    [174000*(1-res_error),174000*(1+res_error)],rb,ib)]
rho=1.724e-8
hot=1+.00393*(100-20)
bar_r=rho*.1/(15e-3*2e-3)*hot
pour_r=rho*.1/(20e-3*70e-6*2)*hot
via_r=rho*1.6e-3/(math.pi*.4e-3*25e-6)*hot
rows=[]
for current in (25,45,50,60,120,150):
    rows.append({'current_A':current,'bar_100mm_loss_W':current**2*bar_r,
        'two_pours_100mm_loss_W':current**2*pour_r,
        '160_via_transfer_loss_W':current**2*via_r/160})
bank=[]
for voltage in (42.4,43,43.5,45,46):
    bank.append({'voltage_V':voltage,'nominal_current_A':voltage/5,
        'min_R_4_95ohm_current_A':voltage/4.95,
        'nominal_power_W':voltage**2/5,
        'max_power_at_minus1percent_R_W':voltage**2/4.95,
        'time_to_500J_at_max_power_s':500/(voltage**2/4.95)})
results={'metadata':{'rev_a_engineering_prototype':True,'rev_b_production':False},'status':'analytic_prototype_estimate_not_hardware_validation',
    'assumptions':{'resistor_fraction_error':res_error,'reference_fraction_error':ref_error,
        'comparator_offset_bound_V':.0055,'input_bias_bound_A':50e-9,
        'PCB_ambient_range_C':[0,70],'gate_high_V':gate_hi,
        'conductor_temperature_C':100,'rho_Cu_20C_ohm_m':rho},
    'thresholds_V':{'nominal_on':43.0,'nominal_off':43-.06*9.9705,
        'on_corner_bounds':bounds(gate_lo),'off_corner_bounds':bounds(gate_hi),
        'independent_OV_corner_bounds':[min(ov),max(ov)],
        'minimum_hysteresis_bound':.06*(1-res_error)/(1+res_error)*(min(gate_hi)-max(gate_lo))},
    'bank':bank,'conductors':{'bar_R_100C_ohm':bar_r,'two_pours_R_100C_ohm':pour_r,
        'single_via_R_100C_ohm':via_r,'current_rows':rows,
        'bar150A3s_adiabatic_delta_C':150**2*bar_r*3/(.1*.015*.002*8960*385),
        '160vias150A3s_adiabatic_delta_C':150**2*via_r/160*3/(160*math.pi*.4e-3*25e-6*1.6e-3*8960*385)},
    'supervisor':{'nominal_reference_valid_V':.405*(1+117/24.9),'qualification_ms':[12,20,28]},
    'motion_bulk':{'part':'EKYC101ELL471MK35S','quantity':2,
        'nominal_uF':940,'tolerance_only_min_uF':752,'tolerance_only_max_uF':1128,
        'nominal_energy_at42V_J':.5*940e-6*42**2,
        'max_energy_at42V_J':.5*1128e-6*42**2,
        'worst_hysteretic_frequency_Hz':(46/4.95)/(4*752e-6*(.06*(1-res_error)/(1+res_error)*(min(gate_hi)-max(gate_lo)))),
        'max_total_capacitor_ripple_RMS_A':46/4.95/2,
        'max_capacitor_ripple_balanced_RMS_A':46/4.95/4,
        'each_rating_1kHz105C_RMS_A':3.3*.85,
        'bleed_R_ohm':22000,'bleed_loss_at46V_W':46**2/22000,
        'max_RC_time42V_to5V_s':1128e-6*22000*1.01*math.log(42/5),
        'limits':'Capacitance bounds only20C120Hz initial. Frequency formula neglectsESR/inductance/delay. Measurecapacitance,ripple,sharing,ESR andinrush beforehigherenergy.'},
    'thermal':{'ntc_trip_resistance_ohm':10000*10000/90900,
        'trip_temperature_C_approx_from_manufacturer_table':84.0,
        'open_detection_R_ohm':1000000,'telemetry_at25C_V':1.65,
        'bank_500J_60s_average_W':500/60,
        'one_305x305x3_2mm_Al_plate_250J_adiabatic_delta_C':250/(.305*.305*.0032*2700*900)},
}
(ROOT/'chopper-calculations.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
print(json.dumps(results,indent=2))
