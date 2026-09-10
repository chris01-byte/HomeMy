"""Generate the reviewed power-stage connectivity record; no CAD side effects."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
components = []
MAIN = '02_main_switch_lm74930'
MOTION = '03_motion_gate_tps48110'
EFUSE = '05_pc_and_5v_efuses'
GND = 'BATT_N'
SOURCES = {
    'lm': 'https://www.ti.com/lit/ds/symlink/lm74930-q1.pdf',
    'tps': 'https://www.ti.com/lit/ds/symlink/tps4811-q1.pdf',
    'efuse': 'https://www.ti.com/lit/ds/symlink/tps2663.pdf',
    'fet': 'https://assets.nexperia.com/documents/data-sheet/PSMN1R0-100ASF.pdf',
    'shunt': 'https://www.bourns.com/docs/product-datasheets/css4j-4026.pdf',
    'tvs': 'https://www.bourns.com/docs/Product-Datasheets/PTVS1-xxxC-H.pdf',
}

def part(ref, mpn, value, footprint, sheet, pins, source_url, notes='', pin_names=None, pin_types=None, **extra):
    components.append(dict(ref=ref, mpn=mpn, value=value, footprint=footprint,
        sheet=sheet, pins={str(k):v for k,v in pins.items()}, source_url=source_url,
        notes=notes, pin_names={str(k):v for k,v in (pin_names or {}).items()},
        pin_types={str(k):v for k,v in (pin_types or {}).items()}, **extra))

def resistor(ref, value, a, b, sheet, precision=False, notes=''):
    code = value.replace(' ', '')
    mpn = ('RT0805BRD07' if precision else 'RC0805FR-07') + code + 'L'
    part(ref, mpn, value + (' 0.1% 25ppm/K' if precision else ' 1%'),
         'Resistor_SMD:R_0805_2012Metric', sheet, {1:a,2:b},
         'https://www.yageo.com/en/Product/Index/chip-resistors', notes,
         tolerance_percent=0.1 if precision else 1)

def cap(ref, mpn, value, a, b, sheet, footprint='Capacitor_SMD:C_0805_2012Metric', notes=''):
    part(ref,mpn,value,footprint,sheet,{1:a,2:b},
         ('https://www.wima.de/en/our-product-range/metallized-capacitors/mks-4/' if mpn.startswith('MKS') else
          'https://yageogroup.com/download/specsheet/'+mpn if mpn.startswith('C0') or mpn.startswith('C1') else
          'https://www.murata.com/en-global/products/capacitor/ceramiccapacitor'),notes)

lm_names = dict(enumerate(['DGATE','A','SW','UVLO','OV','EN','MODE','NC','TMR','IMON','ILIM','FLT_N','GND','HGATE','OUT','OVCLAMP','NC','ISCP','CS-','CS+','NC','VS','CAP','C','EP_FLOAT'],1))
lm_pins={1:'MAIN_DGATE',2:'MAIN_COMMON',3:None,4:'MAIN_UVLO',5:'MAIN_OV',6:'AON_WAKE_EN',7:'AON_WAKE_EN',8:None,9:'MAIN_TMR',10:None,11:'MAIN_ILIM',12:'MAIN_FAULT_N',13:GND,14:'MAIN_HGATE',15:'MAIN_COMMON',16:GND,17:None,18:'MAIN_ISCP',19:'MAIN_KELVIN_N',20:'MAIN_CS_P',21:None,22:'BATT_SENSED_P',23:'MAIN_CAP',24:'SYS_BUS_P',25:None}
lm_types={p:('no_connect' if lm_pins[p] is None else 'input') for p in lm_pins}
lm_types.update({1:'output',9:'passive',10:'output',11:'passive',12:'open_collector',13:'power_in',14:'output',22:'power_in',23:'output'})
part('U1','LM74930QRGERQ1','LM74930-Q1','PMU_RevA:VQFN_RGE24_4x4_P0.5_EP_FLOAT',MAIN,lm_pins,SOURCES['lm'],
    'Datasheet pp3-4: exposed pad must FLOAT. SW unused; independent input dividers avoid common-source startup UV deadlock. Positive-polarity bench input only; this wiring does not claim negative-battery tolerance.',lm_names,lm_types)

tp_names={1:'EN_UVLO',2:'OV',3:'INP',4:'FLT_T_N',5:'FLT_I_N',6:'GND',7:'IMON',8:'IWRN',9:'TMR',10:'DIODE',11:'NC',12:'BST',13:'SRC',14:'PD',15:'PU',17:'CS-',18:'CS+',19:'ISCP',20:'VS'}
tp_pins={1:'MOTION_UVLO',2:GND,3:'MOTION_GATE_EN',4:'MOTION_TEMP_FLT_N',5:'MOTION_FLT_N',6:GND,7:'MOTION_IMON_RAW',8:'MOTION_IWRN',9:'MOTION_TMR',10:'MOTION_TEMP_DIODE',11:None,12:'MOTION_BST',13:'MOTION_COMMON',14:'MOTION_GATE_DRIVE',15:'MOTION_PU',17:'MOTION_KELVIN_N',18:'MOTION_CS_P',19:'MOTION_ISCP',20:'SYS_BUS_P'}
tp_types={p:'input' for p in tp_pins};tp_types.update({4:'open_collector',5:'open_collector',6:'power_in',7:'output',9:'passive',11:'no_connect',12:'output',13:'passive',14:'output',15:'output',20:'power_in'})
part('U2','TPS48110AQDGXRQ1','TPS48110-Q1','PMU_RevA:VSSOP_DGX19_3x5.1_P0.5_Missing16',MOTION,tp_pins,SOURCES['tps'],
    'Physical pin16 absent. Pin11 no-connect. External fault latch must capture both FLT_I and FLT_T; native thermal behavior retries after512ms. OV grounded: external chopper46V comparator supplies latched OV inhibit. IMON combined load including wake100k ADC pulldown provides0.627906V at60A; unloaded interface0.675V.',tp_names,tp_types)

for i in range(1,11):
    sheet=MAIN if i<=6 else MOTION
    common='MAIN_COMMON' if i<=6 else 'MOTION_COMMON'
    drain=('BATT_SENSED_P' if i<=3 else 'SYS_BUS_P') if i<=6 else ('MOTION_SENSED_P' if i<=8 else 'MOTION_BUS_P')
    gate='Q'+str(i)+'_G'
    pins={1:gate,**{p:common for p in range(2,7)},**{p:drain for p in range(7,14)}}
    names={1:'G',**{p:'S' for p in range(2,7)},**{p:'D' for p in range(7,14)}}
    types={1:'input',**{p:'passive' for p in range(2,14)}}
    part('Q'+str(i),'PSMN1R0-100ASFJ','100V N-MOS .99mR@25C/2.3mR@175C 10V',
        'PMU_RevA:CCPAK1212_SOT8000A',sheet,pins,SOURCES['fet'],
        'Manufacturer mounting-base mb is library pad13 and is D. Top-view1 bottom-left,1..6 left-to-right bottom;12..7 top. Separate gate resistor per die. No assumption of equal current sharing during linear startup.',names,types)
    drv=('MAIN_HGATE' if i<=3 else 'MAIN_DGATE') if i<=6 else 'MOTION_GATE_DRIVE'
    resistor('R'+str(i),'10R',drv,gate,sheet)
    resistor('R'+str(10+i),'10M',gate,common,sheet,
             notes='Main HGATE only39uA minimum: do not substitute ordinary10k/100k pull-downs.')

for ref,sheet,forcep,forcen,kp,kn in [
 ('RSH1',MAIN,'BATT_FUSED_P','BATT_SENSED_P','MAIN_KELVIN_P','MAIN_KELVIN_N'),
 ('RSH2',MOTION,'SYS_BUS_P','MOTION_SENSED_P','MOTION_KELVIN_P','MOTION_KELVIN_N')]:
    part(ref,'CSS4J-4026R-L500F','0.5mR 1% four-terminal10W@70C terminal',
        'PMU_RevA:CSS4J_4026_Kelvin',sheet,{1:forcep,2:kp,3:kn,4:forcen},SOURCES['shunt'],
        'Footprint pad numbers are project-defined, not manufacturer lead numbers:1left-force,2left-sense,3right-sense,4right-force. Sense pads must stay separate from power copper until inside resistor.',
        {1:'FORCE_P',2:'SENSE_P',3:'SENSE_N',4:'FORCE_N'}, {p:'passive' for p in range(1,5)},
        pad_geometry_mm={'1':[-4.025,0.85,2.55,5.6],'2':[-4.025,-3.25,2.55,0.8],'3':[4.025,-3.25,2.55,0.8],'4':[4.025,0.85,2.55,5.6]},
        qualification={'continuous_power_w':10,'terminal_temperature_c':70,'short_overload_power_w':50,'short_overload_duration_s':5,'short_overload_energy_j':250,'not_universal_pulse_energy_rating':True})

# Main: nominal65A overcurrent; nominal120A short circuit; approximate0.5s timer.
resistor('R21','49R9','MAIN_KELVIN_P','MAIN_CS_P',MAIN,True)
resistor('R22','18K2','MAIN_ILIM','MAIN_ILIM_TAIL',MAIN,True,
    notes='R22 plus R64=18.4k effective. Standard catalog values replace unverified18.4k single-part ordercode.')
resistor('R64','200R','MAIN_ILIM_TAIL',GND,MAIN,True)
resistor('R23','3K65','MAIN_KELVIN_P','MAIN_ISCP',MAIN,True)
resistor('R24','100K','MAIN_TMR',GND,MAIN,True)
resistor('R25','523K','BATT_SENSED_P','MAIN_UVLO',MAIN,True)
resistor('R26','10K1','MAIN_UVLO',GND,MAIN,True)
resistor('R27','732K','BATT_SENSED_P','MAIN_OV',MAIN,True)
resistor('R28','10K','MAIN_OV',GND,MAIN,True)
resistor('R29','1M','AON_WAKE_EN',GND,MAIN)
cap('C1','GRM21BR72A104KA01L','100nF100V X7R','BATT_SENSED_P',GND,MAIN)
cap('C2','C1206C105K3RACTU','1uF25V X7R','MAIN_CAP','BATT_SENSED_P',MAIN,'Capacitor_SMD:C_1206_3216Metric')
cap('C3','MKS4C053306D00KSSD','33uF63V10% PET film','MAIN_TMR',GND,MAIN,'PMU_RevA:C_Rect_L31.5mm_W13mm_P27.5mm',
    'Non-polar. Body31.5x13x24mm;0.8mm leads,27.5mm pitch. Manufacturer insulationRC>=3000s at20C. Prototype calculations include2% thermal capacitance drift and1uA leakage allowance; verify at local0..60C. No unbounded high-temp tantalum leakage.')
cap('C4','C0805C102J5GACTU','1nF50V5% C0G','MAIN_CS_P','MAIN_KELVIN_N',MAIN)
cap('C5','C0805C102J5GACTU','1nF50V5% C0G','MAIN_ISCP','MAIN_KELVIN_N',MAIN)
cap('C6','C0805C102J5GACTU','1nF50V5% C0G','MAIN_UVLO',GND,MAIN)
cap('C7','C0805C102J5GACTU','1nF50V5% C0G','MAIN_OV',GND,MAIN)
for ref,net in [('D1','BATT_FUSED_P'),('D2','SYS_BUS_P')]:
    part(ref,'PTVS1-043C-H','43V bidirectional low-clamp TVS',
         'PMU_RevA:PTVS1_DFN8x6',MAIN,{1:net,2:GND},SOURCES['tvs'],
         '56V at1kA8/20us is TYPICAL, not guaranteed maximum. See explicit transient design envelope and limitation inPOWER_STAGE.md. Pin1narrowpad andpin2widepad; bidirectional.',
         {1:'TVS_A',2:'TVS_B'},{1:'passive',2:'passive'},
         pad_geometry_mm={'1':[-2.87,0,1.19,4.93],'2':[0.945,0,5.04,4.93]})

# Motion current settings; hardware latching timer, independent temperature diode.
resistor('R30','100R','MOTION_KELVIN_P','MOTION_CS_P',MOTION,True)
resistor('R31','39K7','MOTION_IWRN',GND,MOTION,True)
resistor('R32','2K74','MOTION_KELVIN_P','MOTION_ISCP',MOTION,True)
resistor('R33','100K','MOTION_TMR',GND,MOTION,True)
resistor('R34','180K','MOTION_PU','MOTION_GATE_DRIVE',MOTION,
    notes='Slow turn-on for940uF motor-bus capacitor. Two input-bank Miller charges govern ramp estimate; four totalQg govern reservoir. DirectPD path still provides fastfaultturnoff. Four10M gatebleeds preserve>=10V steady gate under stated11Vboostmodel.')
resistor('R35','226K','SYS_BUS_P','MOTION_UVLO',MOTION,True)
resistor('R36','10K','MOTION_UVLO',GND,MOTION,True)
resistor('R39','100K','MOTION_GATE_EN',GND,MOTION)
cap('C8','GRM21BR72A104KA01L','100nF100V X7R','SYS_BUS_P',GND,MOTION)
cap('C9','C1206C475K3RACTU','4.7uF25V X7R','MOTION_BST','MOTION_COMMON',MOTION,'Capacitor_SMD:C_1206_3216Metric',
    'C9andC29 inparallel. YAGEOgeneratedspecsheet9/10/2026 p2 shows~40% DC-biasloss12V. Two partsretain~3.6uF with tolerance/temp/aging allowance, above2.156uF for1Vgatecharge droop.')
cap('C29','C1206C475K3RACTU','4.7uF25V X7R','MOTION_BST','MOTION_COMMON',MOTION,'Capacitor_SMD:C_1206_3216Metric',
    'Second populatedboostcapacitor; totalnominal9.4uF. Approx1.41s unladen12Vcharging at80uA. Motion remainsinhibitedthroughboot.')
cap('C10','MKS4C053306D00KSSD','33uF63V10% PET film','MOTION_TMR',GND,MOTION,'PMU_RevA:C_Rect_L31.5mm_W13mm_P27.5mm',
    'Same film timing/insulation assumptions asC3; configurable component, not firmware timing.')
cap('C11','C0805C102J5GACTU','1nF50V5% C0G','MOTION_CS_P','MOTION_KELVIN_N',MOTION)
cap('C12','C0805C102J5GACTU','1nF50V5% C0G','MOTION_ISCP','MOTION_KELVIN_N',MOTION)
cap('C13','C0805C102J5GACTU','1nF50V5% C0G','MOTION_TEMP_DIODE',GND,MOTION)
resistor('R59','10K','MOTION_IMON_RAW',GND,MOTION,True)
resistor('R60','20K','MOTION_IMON_RAW','MOTION_IMON_INPUT',MOTION,True)
resistor('R61','10K','MOTION_IMON_INPUT',GND,MOTION,True)
cap('C28','C0805C103J5GACTU','10nF50V5% C0G','MOTION_IMON_INPUT',GND,MOTION)
part('Q11','MMBT3904,215','Remote temperature diode','Package_TO_SOT_SMD:SOT-23',MOTION,
    {1:'MOTION_TEMP_DIODE',2:GND,3:'MOTION_TEMP_DIODE'},
    'https://assets.nexperia.com/documents/data-sheet/MMBT3904.pdf',
    'Base1 and collector3 tied; emitter2 GND. Place at hottest motion-bank copper. TPS remote temperature trip150Ctyp/140..160C table; separate board NTC protection acts earlier.',
    {1:'B',2:'E',3:'C'},{1:'input',2:'passive',3:'passive'})

# Independent system UV capture: native TPS EN UVLO auto-recovers without FLT.
# An open-drain comparator may share FLT_I with the existing external fault latch.
part('U5','TLV3011BIDBVR','Latched motion SYS undervoltage detector','Package_TO_SOT_SMD:SOT-23-6',MOTION,
    {1:'MOTION_FLT_N',2:'LOGIC_GND',3:'MOTION_LATCH_UV_SENSE',4:'MOTION_UV_REF',5:'MOTION_UV_REF',6:'V3V3'},
    'https://www.ti.com/lit/ds/symlink/tlv3011.pdf',
    'B version required: integrated reference,2..8mV internal hysteresis,fail-safe input. Open-drain OUT wired-OR with U2 FLT_I and existing wake10k pullup. POR output is high-Z; externalmotionlatch starts unarmed. NativeTPS EN falling threshold26.2V is backed by independent~29V latched UV. No RC sense delay.',
    {1:'OUT_OD',2:'GND',3:'IN+',4:'IN-',5:'REF',6:'VCC'},
    {1:'open_collector',2:'power_in',3:'input',4:'input',5:'output',6:'power_in'})
resistor('R62','226K','SYS_BUS_P','MOTION_LATCH_UV_SENSE',MOTION,True)
resistor('R63','10K','MOTION_LATCH_UV_SENSE','LOGIC_GND',MOTION,True)
cap('C30','GRM21BR72A104KA01L','100nF100V X7R','V3V3','LOGIC_GND',MOTION)
cap('C31','C0805C102J5GACTU','1nF50V5% C0G','MOTION_UV_REF','LOGIC_GND',MOTION)

# PC and5V converters: TPS26631 internal switching, no B_GATE external FET.
en={1:'IN',2:'IN',3:'B_GATE',4:'DRV',5:'IN_SYS',6:'UVLO',7:'OVP',8:'GND',9:'DVDT',10:'ILIM',11:'MODE',12:'SHDN',13:'IMON',14:'FLT_N',15:'PGTH',16:'PGOOD',17:'OUT',18:'OUT',19:'NC',20:'NC',21:'NC',22:'NC',23:'NC',24:'NC',25:'EP_GND'}
for idx,prefix,ilim in [(3,'PC','6K04'),(4,'LOGIC','9K09')]:
    p={1:'SYS_BUS_P',2:'SYS_BUS_P',3:None,4:None,5:'SYS_BUS_P',6:prefix+'_UVLO',7:prefix+'_OVP',8:GND,9:prefix+'_DVDT',10:prefix+'_ILIM',11:None,12:prefix+'_SHDN',13:None,14:prefix+'_EFUSE_FAULT_N',15:prefix+'_PGTH',16:prefix+'_EFUSE_PGOOD',17:prefix+'_BUCK_IN_P',18:prefix+'_BUCK_IN_P',19:None,20:None,21:None,22:None,23:None,24:None,25:GND}
    ty={n:'input' for n in p};ty.update({1:'power_in',2:'power_in',3:'no_connect',4:'no_connect',5:'power_in',8:'power_in',9:'passive',10:'passive',11:'no_connect',13:'no_connect',14:'open_collector',16:'open_collector',17:'power_out',18:'passive',25:'power_in',**{n:'no_connect' for n in range(19,25)}})
    part('U'+str(idx),'TPS26631RGER','TPS26631 eFuse latch-off','Package_DFN_QFN:Texas_RGE0024H_VQFN-24-1EP_4x4mm_P0.5mm_EP2.7x2.7mm',EFUSE,p,SOURCES['efuse'],
         'MODE MUST float for latch-off; GND would select auto-retry. TPS26631 supports2x overload pulses; neither branch precisely enforces65W. Passive divider powersSHDN enable directly fromSYS_BUS; deliberate main power cycle resets eFuse latch. OUT17isERCpower_out; internallycommonOUT18ispassive toavoidself-conflictingstackedoutputwithoutmaskingcross-ICoutputcontention.',en,ty)
    rbase=40+(idx-3)*10
    for off,val,a,b,prec in [(0,ilim,prefix+'_ILIM',GND,True),(1,'191K','SYS_BUS_P',prefix+'_UVLO',True),(2,'10K',prefix+'_UVLO',GND,True),(3,'374K','SYS_BUS_P',prefix+'_OVP',True),(4,'10K',prefix+'_OVP',GND,True),(5,'1M','SYS_BUS_P',prefix+'_SHDN',False),(6,'68K',prefix+'_SHDN',GND,False),(7,'191K',prefix+'_BUCK_IN_P',prefix+'_PGTH',True),(8,'10K',prefix+'_PGTH',GND,True)]:
        resistor('R'+str(rbase+off),val,a,b,EFUSE,prec)
    cbase=20+(idx-3)*5
    cap('C'+str(cbase),'C0805C223J5GACTU','22nF50V5% C0G',prefix+'_DVDT',GND,EFUSE)
    cap('C'+str(cbase+1),'GRM21BR72A104KA01L','100nF100V X7R','SYS_BUS_P',GND,EFUSE)
    cap('C'+str(cbase+2),'C1210C105K1RACTU','1uF100V X7R',prefix+'_BUCK_IN_P',GND,EFUSE,'Capacitor_SMD:C_1210_3225Metric')

data=dict(metadata=dict(rev_a_engineering_prototype=True,rev_b_production=False,
    date='2026-09-10',connectivity_status='engineering_design_not_energization_release',
    notes='null nets are explicit NC/unused pins, not omitted connections; PIN_TYPES distinguish electrical ERC intent.'),
    components=components,sources=SOURCES,
    unresolved_design_items=['Main UV0.5s absent: native fastUV selected; documented provisional deviation.',
       'Guaranteed44-45V inputOV window cannot be obtained with nativeLM comparator tolerance.',
       'Film timer calculations cover stated0..60C prototype envelope and1uA allowance, not unverified full-temperature timing.',
       'Main DGATE minimum9.2V does not directly inherit10V hotRds guaranteed table.',
       'System TVS and external buck55V limit need coordinated transient envelope.',
       'Full-load main inrush remains RevB measurement; conservative bench envelope inPOWER_STAGE.md.'])
(HERE/'power-parts.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print(f'Wrote {len(components)} components')
