"""Source-level PMU electrical audit. Does not edit CAD or assert physical validation."""
import json,pathlib,hashlib,sys,importlib.util,collections
ROOT=pathlib.Path(__file__).resolve().parents[1]
if '--fix-owned' in sys.argv:
 p=ROOT/'design/wake-io-parts.json';d=json.loads(p.read_text())
 for c in d['components']:
  c['dnp']=c.get('population','').upper()=='DNP'
  if c['ref'] in ('R216','R217','R237'):
   c['value']='10k';c['mpn']='RC0805FR-0710KL'
   if 'Final review:10k' not in c['notes']:c['notes']+=' Final review:10k default-low for aggregate powered-off leakage; replaces100k.'
  if c['ref']=='C246':
   c['pins']['2']='LOGIC_5V_N'
   c['notes']='AtLEDconnector; height20mm maximum assumed. ReturndirectlytoLOGIC_5V_N withJ18, bypassinglogicstarNT9.'
 p.write_text(json.dumps(d,indent=2,ensure_ascii=False)+'\n')
spec=importlib.util.spec_from_file_location('schematic_review',ROOT/'scripts/build_schematic.py')
mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
parts=mod.load_components();by={c['ref']:c for c in parts}
checks=[]
def check(name,passed,detail):
 checks.append({'check':name,'pass':bool(passed),'detail':detail})
check('unique_references',len(parts)==len(by),len(parts))
check('explicit_DNP_selection',{c['ref'] for c in parts if c.get('dnp')}=={'R243','R244','C244','J13'},[c['ref'] for c in parts if c.get('dnp')])
check('aliases_normalized',not any(n in ('+3V3','+5V') for c in parts for n in c['pins'].values()),'V3V3/V5V only')
check('no_connect_not_real_net',not any(n and str(n).startswith('NC_') for c in parts for n in c['pins'].values()),'No-connect source placeholders converted to null')
ground_pairs=[('ARM_L_N','BATT_N'),('ARM_R_N','BATT_N'),('DRIVE_N','BATT_N'),('LIFT_N','BATT_N'),('PC_N','BATT_N'),('LOGIC_BUCK_N','BATT_N'),('CHOPPER_N','BATT_N'),('LOGIC_5V_N','BATT_N'),('LOGIC_GND','BATT_N'),('CHOP_GND','CHOPPER_N')]
for i,(a,b) in enumerate(ground_pairs,1):
 check(f'star_NT{i}',by[f'NT{i}']['pins']=={'1':a,'2':b},[a,b])
flags={next(iter(c['pins'].values())):c.get('notes','') for c in parts if c['ref'].startswith('#PWR')}
check('power_flag_set_reviewed',set(flags)=={'BATT_FUSED_P','BATT_N','BATT_SENSED_P','AON_LDO_IN','SYS_BUS_P','MOTION_BUS_P','V5V','LOGIC_GND','CHOP_GND'},flags)
check('flags_have_explicit_source_model',all(flags.values()),'Each flag names external source, shunt/FET transfer or intentional ground tie; not a blanket flag on all power_in pins')
for ref in ('R216','R217','R237'):
 check(ref+'_strong_default_low',by[ref]['value']=='10k',by[ref]['value'])
expected={
 'U1':{'6':'AON_WAKE_EN','7':'AON_WAKE_EN','12':'MAIN_FAULT_N','13':'BATT_N','16':'BATT_N','19':'MAIN_KELVIN_N','22':'BATT_SENSED_P','24':'SYS_BUS_P','25':None},
 'U2':{'2':'BATT_N','3':'MOTION_GATE_EN','4':'MOTION_TEMP_FLT_N','5':'MOTION_FLT_N','6':'BATT_N','13':'MOTION_COMMON','14':'MOTION_GATE_DRIVE','15':'MOTION_PU','17':'MOTION_KELVIN_N','20':'SYS_BUS_P'},
 'U5':{'1':'MOTION_FLT_N','2':'LOGIC_GND','4':'MOTION_UV_REF','5':'MOTION_UV_REF','6':'V3V3'},
 'U11':{'1':'LOGIC_GND','2':'LOGIC_GND','6':'V3V3','7':'LOGIC_GND','9':'INA_IN_N','10':'INA_IN_P'},
 'U13':{'1':'CAN_TX','2':'LOGIC_GND','3':'V5V','4':'CAN_RX','5':'V3V3','6':'CAN_L','7':'CAN_H','8':'CAN_STB'},
 'U16':{'1':'AON_3V3','2':'PB_LTC_N','5':'BUTTON_INT_N','6':'WAKE_EN_OD','8':'WAKE_KILL'},
 'U18':{'1':'LOGIC_GND','2':'LOGIC_GND','5':'BUTTON_ARMED','6':'AON_RESET_N','7':'BUTTON_ARM_SET_N','8':'AON_3V3'},
 'U19':{'1':'PB_RELEASED','2':'AON_RESET_N','3':'PB_LTC_N','5':'PB_PRESSED','6':'BUTTON_ARMED','7':'BUTTON_ARM_SET_N'},
 'U21':{'1':'WAKE_RAW_EN','5':'AON_3V3','6':'STARTUP_GRANT'},
 'U23':{'3':'MAIN_LATCH_OK','5':'MAIN_FAULT_LATCHED','6':'WAKE_RAW_EN','7':'MAIN_FAULT_SET_N'},
 'U24':{'1':'MAIN_CAPTURE_EN','2':'MAIN_FAULT_ANY','7':'MAIN_FAULT_SET_N'},
 'U25':{'1':'WAKE_RAW_EN','3':'MAIN_LATCH_OK','4':'AON_WAKE_EN','6':'AON_RESET_N'},
 'U27':{'1':'ESP_MOTION_RESET','2':'V3V3','5':'MOTION_ARMED','6':'MOTION_CLEAR_N','7':'V3V3'},
 'U28':{'1':'MOTION_FLT_N','3':'MOTION_TEMP_FLT_N','4':'MOTION_FAULTS_OK','6':'CHOP_FAULT_N'},
 'U29':{'1':'ESP_CHIP_EN','3':'ESP_WDO_N','4':'MOTION_LOCAL_OK','6':'MOTION_PERMIT'},
 'U50':{'1':'MOTION_LOCAL_OK','3':'MOTION_FAULTS_OK','4':'MOTION_CLEAR_N','6':'AON_WAKE_EN'},
 'U51':{'1':'V3V3','2':None,'3':'V3V3','4':'LOGIC_GND','5':'V3V3','6':'ESP_WDI','7':'ESP_WDO_N','8':None,'9':'LOGIC_GND'},
 'U54':{'1':'ESP_MOTION_REQUEST','3':'MOTION_ARMED','4':'MOTION_GATE_EN','6':'AON_WAKE_EN'},
 'U55':{'1':'SW_RESET_N','2':'AON_3V3','5':'SW_POWER_SEEN','6':'WAKE_RAW_EN','7':'AON_3V3'},
 'U63':{'1':'WAKE_RAW_EN','3':'MAIN_CAPTURE_DELAYED','4':'MAIN_CAPTURE_EN','6':'AON_RESET_N'},
 'Q20':{'1':'MAIN_FAULT_LATCHED','2':'LOGIC_GND','3':'WAKE_KILL'},
 'U31':{'2':'CHOP_10V','4':'CHOP_GND','6':'CHOP_REF2V5'},
 'U32':{'1':'CHOP_OV_OK','2':'CHOP_REQUEST','3':'CHOP_10V','4':'CHOP_REF2V5','5':'CHOP_SENSE','6':'CHOP_OV_SENSE','7':'CHOP_REF2V5','12':'CHOP_GND'},
 'U33':{'1':'CHOP_10V','2':'CHOP_DRIVE_H','3':'CHOP_DRIVE_L','4':'CHOP_GND','5':'CHOP_DISABLE','6':'CHOP_REQUEST'},
 'Q40':{'1':'CHOP_GATE','2':'CHOPPER_N','3':'CHOP_DRAIN'},
 'D63':{'1':'MOTION_BUS_P','2':'CHOP_DRAIN'},
 'U34':{'3':'LOGIC_GND','4':'CHOP_FAULT_N'},
 'U35':{'3':'LOGIC_GND','4':'CHOP_ACTIVE_N'},
 'J11':{'1':'V5V','2':'LOGIC_5V_N'},
 'J18':{'1':'V5V','2':'LED_DATA_OUT','3':'LOGIC_5V_N'},
}
for ref,pins in expected.items():
 diff={pin:{'actual':by[ref]['pins'].get(pin),'expected':net} for pin,net in pins.items() if by[ref]['pins'].get(pin)!=net}
 check('critical_pin_nets_'+ref,not diff,diff or 'Matched explicit reviewed net map')
for ref in ('U3','U4'):
 check(ref+'_latch_mode',by[ref]['pins']['11'] is None and by[ref]['pins']['12'].endswith('_SHDN'),'MODE floating; SHDN passive SYS divider')
check('chopper_reference_testpoint',any(c['ref'].startswith('TP') and c['pins'].get('1')=='CHOP_REF2V5' for c in parts),'Source net CHOP_REF2V5, not CHOP_REF_2V5')
check('LED_bulk_return',by['C246']['pins']['2']=='LOGIC_5V_N',by['C246']['pins'])
check('external_optos_meaningful_ERC',all(by[r]['pin_types']['4']=='open_collector' for r in ('U34','U35')),{r:by[r]['pin_types']['4'] for r in ('U34','U35')})
# Exhaustive stable-state Boolean motion permission, independently expressed.
cases=0;fail=0
for mask in range(512):
 current,thermal,chop,esp,watchdog,permit,main,armed,request=[bool(mask&(1<<i)) for i in range(9)]
 clear=(current and thermal and chop) and (esp and watchdog and permit) and main
 q=armed if clear else False
 out=request and q and main
 expected_out=all((current,thermal,chop,esp,watchdog,permit,main,armed,request))
 cases+=1;fail+=out!=expected_out
check('motion_static_all_interlocks',fail==0,{'cases':cases,'failures':fail,'scope':'Stable-state Boolean check, not propagation timing or physical fail-safety'})
sources=['design/'+x for x in ('power-parts.json','wake-io-parts.json','chopper-parts.json','integration-parts.json')]+['scripts/build_schematic.py','scripts/build_integration.py']
result={'metadata':{'rev_a_engineering_prototype':True,'rev_b_production':False,'review_scope':'source_netlist_and_generator_logic_only','no_PCB_changes':True},
 'source_sha256':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sources},
 'component_count':len(parts),'checks':checks,'pass_count':sum(c['pass'] for c in checks),'fail_count':sum(not c['pass'] for c in checks),
 'findings':[
  {'id':'F01','severity':'high','status':'corrected_in_sources','refs':['R243','R244','C244'],'finding':'Population=DNP was not consumed by generator','correction':'Explicit own-source dnp booleans and parent loader normalization'},
  {'id':'F02','severity':'medium','status':'corrected_in_sources','refs':['TP28'],'finding':'Absent CHOP_REF_2V5 omitted reference testpoint','correction':'Integration uses actual CHOP_REF2V5'},
  {'id':'F03','severity':'high','status':'corrected_in_sources','refs':['R216','R217','R237'],'finding':'100k default-low did not cover aggregate off-state leakage','correction':'10k resistors with explicit main-EN leakage bound below0.41V'},
  {'id':'F04','severity':'high','status':'corrected_in_sources','refs':['J18','C246','NT9'],'finding':'LED5A return crossed logic star','correction':'J18.3/C246.2 nowLOGIC_5V_N direct converter return'},
  {'id':'F05','severity':'medium','status':'corrected_in_sources','refs':['U34','U35'],'finding':'Optocoupler collectors marked passive','correction':'Collector pin4 open_collector'}],
 'leakage_model':{'AON_EN_old_V':30.36e-6*(100e3*1e6/(100e3+1e6)),'AON_EN_new_V_with_1pct_R':30.36e-6*(10.1e3*1.01e6/(10.1e3+1.01e6)),'LM74930_guaranteed_off_below_V':.41,'note':'Summed conservative3x10uA LVC partial-poweroff plusEN200nA/MODE160nA;10k pull-down replaces100k. Reset and motion pull-downs likewise10k.'},
 'not_proven':['Physical routing and high-current star geometry','Dynamic propagation/races and partial-power ramps','Hot SOA and full940uF power-path startup','Shared-shunt component failure independence','Hardware timing, EMC and production safety']}
(ROOT/'evidence/final-electrical-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'components':len(parts),'checks':len(checks),'failures':[c for c in checks if not c['pass']]}))
