"""Produce reviewable chopper/connector connectivity; does not prove a PCB."""
from pathlib import Path
import json

ROOT = Path(__file__).parent
parts = []

def add(ref, mpn, value, footprint, pins, source, notes='', **extra):
    parts.append(dict(ref=ref, mpn=mpn, value=value, footprint=footprint,
        pins={str(k): v for k, v in pins.items()}, source_url=source, notes=notes,
        sheet='09_connectors_testpoints' if ref.startswith('J') else '04_brake_chopper', **extra))

TI = 'https://www.ti.com/lit/ds/symlink/'
R_SOURCE = 'https://www.vishay.com/docs/28758/tnpw_e3.pdf'
def r(ref, value, a, b, code, tolerance='0.1%', notes=''):
    add(ref, 'TNPW0805'+code+('F' if tolerance=='1%' else 'B')+'EEA', value+' '+tolerance,
        'Resistor_SMD:R_0805_2012Metric', {1:a,2:b}, R_SOURCE, notes)

def c(ref, value, a, b, mpn='GRM188R71H104KA93D', footprint='Capacitor_SMD:C_0603_1608Metric', notes='', source='https://www.murata.com/en-us/products/capacitor/ceramiccapacitor'):
    add(ref, mpn, value, footprint, {1:a,2:b}, source, notes)

G='CHOP_GND'
add('U30','TPS7A4001DGNR','100V LDO, nominal 10V','Package_SO:Texas_DGN0008B_VSSOP-8-1EP_3x3mm_P0.65mm_EP2x3mm_Mask1.88x1.98mm_ThermalVias',
    {1:'CHOP_10V',2:'CHOP_FB',3:'NC_U30_3',4:G,5:'MOTION_BUS_P',6:'NC_U30_6',7:'NC_U30_7',8:'MOTION_BUS_P',9:G},TI+'tps7a4001.pdf',
    'Pins3/6/7 unconnected. EP internally ground. Motion-bus supply independent of ESP. Datasheet package appendix DGN0008B: exposed mask1.88x1.98mm; matched official KiCad DGN0008B footprint.')
r('R300','75.0k','CHOP_10V','CHOP_FB','75K0')
r('R301','10.0k','CHOP_FB',G,'10K0')
c('C300','1uF 100V','MOTION_BUS_P',G,'C3216X7R2A105K160AB','Capacitor_SMD:C_1206_3216Metric',source='https://product.tdk.com/en/search/capacitor/ceramic/mlcc/info?part_no=C3216X7R2A105K160AB')
c('C301','10uF 25V','CHOP_10V',G,'GRM32ER71E106KA12L','Capacitor_SMD:C_1210_3225Metric','Effective capacitance must stay >=4.7uF at10V.')
add('U31','REF5025IDR','2.5V high-grade reference','Package_SO:SOIC-8_3.9x4.9mm_P1.27mm',
    {1:'NC_U31_1',2:'CHOP_10V',3:'NC_U31_3',4:G,5:'NC_U31_5',6:'CHOP_REF2V5',7:'NC_U31_7',8:'NC_U31_8'},TI+'ref50.pdf',
    'High grade:0.05%/3ppm per C. Pins1/8 DNC; TEMP and TRIM/NR unused.')
c('C302','100nF 50V','CHOP_10V',G)
c('C303','1uF 25V','CHOP_REF2V5',G,'GRM21BR71E105KA99L','Capacitor_SMD:C_0805_2012Metric')
add('U32','LM339BIPWR','Independent analog chopper/OV/NTC window','Package_SO:TSSOP-14_4.4x5mm_P0.65mm',
    {1:'CHOP_OV_OK',2:'CHOP_REQUEST',3:'CHOP_10V',4:'CHOP_REF2V5',5:'CHOP_SENSE',6:'CHOP_OV_SENSE',7:'CHOP_REF2V5',8:'CHOP_TEMP_LOW',9:'CHOP_NTC',10:'CHOP_NTC',11:'CHOP_TEMP_HIGH',12:G,13:'CHOP_THERMAL_OK',14:'CHOP_THERMAL_OK'},
    TI+'lm339b.pdf','Ch1 on comparator; ch2 OV; ch3 hot/short; ch4 open. Open collectors ch3/4 wired together. Output low<=0.55V at<=4mA across -40..85C; TLV1704 rejected because its0.9V bound exceeds driver0.8V VIL.')
c('C304','100nF 50V','CHOP_10V',G)
r('R302','160k','MOTION_BUS_P','CHOP_SENSE_TOP','160K')
r('R303','1.40k','CHOP_SENSE_TOP','CHOP_SENSE','1K40')
r('R304','10.0k','CHOP_SENSE',G,'10K0')
r('R305','1.00M','CHOP_GATE','CHOP_HYS_MID','1M00')
r('R306','1.00M','CHOP_HYS_MID','CHOP_HYS_MID2','1M00')
r('R331','690k','CHOP_HYS_MID2','CHOP_SENSE','690K')
c('C305','100pF 50V C0G','CHOP_SENSE',G,'GRM1885C1H101JA01D')
r('R307','10.0k','CHOP_10V','CHOP_REQUEST','10K0')
r('R308','174k','MOTION_BUS_P','CHOP_OV_SENSE','174K')
r('R309','10.0k','CHOP_OV_SENSE',G,'10K0')
c('C306','100pF 50V C0G','CHOP_OV_SENSE',G,'GRM1885C1H101JA01D')
r('R310','10.0k','CHOP_10V','CHOP_OV_OK','10K0')
r('R311','10.0k','CHOP_REF2V5','CHOP_NTC','10K0')
r('R312','90.9k','CHOP_REF2V5','CHOP_TEMP_LOW','90K9')
r('R313','10.0k','CHOP_TEMP_LOW',G,'10K0')
r('R314','1.00k','CHOP_REF2V5','CHOP_TEMP_HIGH','1K00')
r('R315','100k','CHOP_TEMP_HIGH',G,'100K')
c('C307','100nF 50V','CHOP_NTC',G)
r('R316','10.0k','CHOP_10V','CHOP_THERMAL_OK','10K0')
r('R317','100k','CHOP_THERMAL_OK',G,'100K')
r('R318','10.0k','CHOP_10V','CHOP_DISABLE','10K0')
add('Q41','2N7002,215','NTC healthy enables driver','Package_TO_SOT_SMD:SOT-23',
    {1:'CHOP_THERMAL_OK',2:'CHOP_QUALIFY_N',3:'CHOP_DISABLE'},'https://assets.nexperia.com/documents/data-sheet/2N7002.pdf')
add('U33','UCC27511DBVR','4A source/8A sink driver','Package_TO_SOT_SMD:SOT-23-6',
    {1:'CHOP_10V',2:'CHOP_DRIVE_H',3:'CHOP_DRIVE_L',4:G,5:'CHOP_DISABLE',6:'CHOP_REQUEST'},TI+'ucc27511.pdf')
c('C308','100nF 50V','CHOP_10V',G)
c('C309','1uF 25V','CHOP_10V',G,'GRM21BR71E105KA99L','Capacitor_SMD:C_0805_2012Metric')
r('R319','10.0','CHOP_DRIVE_H','CHOP_GATE','10R0')
r('R320','2.20','CHOP_DRIVE_L','CHOP_GATE','2R20',tolerance='1%',notes='TNPW0805 precision0.1% range starts at3.5ohm; this gate resistor uses supported1% grade.')
r('R321','47.0k','CHOP_GATE',G,'47K0')
add('Q40','IPT015N10N5ATMA1','100V chopper NMOS','Package_TO_SOT_SMD:Infineon_PG-HSOF-8-1',
    {1:'CHOP_GATE',2:'CHOPPER_N',3:'CHOP_DRAIN'},
    'https://www.infineon.com/assets/row/public/documents/24/49/infineon-ipt015n10n5-datasheet-en.pdf',
    'KiCad logical pads1=G,2=all source leads,3=drain tab. Manufacturer physical pin1=G,pins2..8=S,tab=D.6cm2 drain copper;no linear regulation.',
    physical_pin_map={'1':'G','2-8':'S','TAB':'D'},logical_to_physical={'1':['1'],'2':['2','3','4','5','6','7','8'],'3':['TAB']})
add('D60','SMCJ43A','43V standoff TVS 1500W','Diode_SMD:D_SMC',
    {1:'MOTION_BUS_P',2:'CHOPPER_N'},'https://www.littelfuse.com/~/media/electronics/datasheets/tvs_diodes/littelfuse_tvs_diode_smcj_datasheet.pdf.pdf',
    'Pin1 cathode. Clamp69.4V at21.7A per10/1000us rating; not a braking resistor; local motion bus only.')
add('D61','SMCJ43A','43V drain spike clamp','Diode_SMD:D_SMC',
    {1:'CHOP_DRAIN',2:'CHOPPER_N'},'https://www.littelfuse.com/~/media/electronics/datasheets/tvs_diodes/littelfuse_tvs_diode_smcj_datasheet.pdf.pdf','Pin1 cathode.')
add('D62','BZT52H-C15,115','15V gate clamp','Diode_SMD:D_SOD-123F',
    {1:'CHOP_GATE',2:G},'https://assets.nexperia.com/documents/data-sheet/BZT52H_SER.pdf','Pin1 cathode.')
add('D63','MBR10100-M3/4W','100V 10A resistor cable freewheel','Package_TO_SOT_THT:TO-220-2_Vertical',
    {1:'MOTION_BUS_P',2:'CHOP_DRAIN'},'https://www.vishay.com/docs/89193/mbr10100.pdf',
    'Manufacturer pin1 and metal tab CATHODE, pin2 ANODE: verified visual page1. Keep exposed live tab isolated.')
add('D64','1N4148WS-E3-08','LDO reverse discharge path','Diode_SMD:D_SOD-323',
    {1:'MOTION_BUS_P',2:'CHOP_10V'},'https://www.vishay.com/docs/85751/1n4148ws.pdf','Cathode1,anode2.')
for ref, cath in [('D65','CHOP_OV_OK'),('D66','CHOP_THERMAL_OK')]:
    add(ref,'1N4148WS-E3-08','Analog fault OR','Diode_SMD:D_SOD-323',
        {1:cath,2:'CHOP_FAULT_LED_K'},'https://www.vishay.com/docs/85751/1n4148ws.pdf','Cathode1,anode2.')
r('R322','4.70k','CHOP_FAULT_PWR','CHOP_FAULT_LED_A','4K70')
add('U34','VOS618A-3T','Isolated analog fault','Package_SO:SSOP-4_4.4x2.6mm_P1.27mm',
    {1:'CHOP_FAULT_LED_A',2:'CHOP_FAULT_LED_K',3:'LOGIC_GND',4:'CHOP_FAULT_N'},
    'https://www.vishay.com/docs/83465/vos618a.pdf','A1 K2 E3 C4. OV or NTC fault activates LED and low fault. Unpowered is released.')
add('Q42','2N7002,215','Chopper gate status isolation driver','Package_TO_SOT_SMD:SOT-23',
    {1:'CHOP_GATE',2:G,3:'CHOP_ACTIVE_LED_K'},'https://assets.nexperia.com/documents/data-sheet/2N7002.pdf')
r('R323','4.70k','CHOP_10V','CHOP_ACTIVE_LED_A','4K70')
add('U35','VOS618A-3T','Isolated chopper active','Package_SO:SSOP-4_4.4x2.6mm_P1.27mm',
    {1:'CHOP_ACTIVE_LED_A',2:'CHOP_ACTIVE_LED_K',3:'LOGIC_GND',4:'CHOP_ACTIVE_N'},
    'https://www.vishay.com/docs/83465/vos618a.pdf')
r('R324','10.0k','+3V3','CHOP_TEMP_ADC','10K0')
c('C310','100nF 50V','CHOP_TEMP_ADC','LOGIC_GND')

# Reference qualification suppresses startup faults and keeps the driver off.
# CT must be OPEN for20ms: grounding CT is not the fixed20ms mode.
add('U36','TPS3808G01DBVR','Reference qualification 12..28ms','Package_TO_SOT_SMD:SOT-23-6',
    {1:'CHOP_REF_READY',2:G,3:'CHOP_REF2V5',4:'NC_U36_CT',5:'CHOP_REF_SENSE',6:'CHOP_REF2V5'},
    TI+'tps3808.pdf','SENSE threshold nominal0.405V; RESET_n1,SENSE5. CT4 left open gives20ms nominal,12..28ms. No firmware required.')
r('R325','117k','CHOP_REF2V5','CHOP_REF_SENSE','117K')
r('R326','24.9k','CHOP_REF_SENSE',G,'24K9')
r('R327','10.0k','CHOP_REF2V5','CHOP_REF_READY','10K0')
r('R328','1.00k','CHOP_REF_READY','CHOP_QUALIFY_BASE','1K00')
r('R329','100k','CHOP_QUALIFY_BASE',G,'100K')
r('R330','100k','CHOP_10V','CHOP_QUALIFY_N','100K')
add('Q43','BSS84,215','Qualified fault LED power','Package_TO_SOT_SMD:SOT-23',
    {1:'CHOP_QUALIFY_N',2:'CHOP_10V',3:'CHOP_FAULT_PWR'},'https://assets.nexperia.com/documents/data-sheet/BSS84.pdf','PMOS gate1,source2,drain3. Body diode points from qualified rail to10V.')
add('Q44','MMBT3904,215','Qualified local enable','Package_TO_SOT_SMD:SOT-23',
    {1:'CHOP_QUALIFY_BASE',2:G,3:'CHOP_QUALIFY_N'},'https://assets.nexperia.com/documents/data-sheet/MMBT3904.pdf',
    'B1 E2 C3. Provides return for thermal-enable Q41 and pulls fault-power PMOS gate low after reference qualification.')
c('C311','100nF 50V','CHOP_REF2V5',G)

for ref in ('C312','C313'):
    add(ref,'EKYC101ELL471MK35S','470uF 100V20% high-ripple MOTION bulk',
        'Capacitor_THT:CP_Radial_D12.5mm_P5.00mm',
        {1:'MOTION_BUS_P',2:'CHOPPER_N'},
        'https://www.chemi-con.co.jp/en/products/detail-condenser.php?part_number=EKYC101ELL471MK35S',
        'Positive1,negative2;D12.5mm,L35mm(max36.5),lead0.6mm,pitch5mm. Two parts parallel:940uFnom/752uFmin at20C. Each3.3Arms100kHz105C;0.85factorat1kHz.25mohmmaxESR100kHz. Symmetrical short copper,vent clearance,mechanical restraint. Motion first enable on1Acurrent-limited source;no full-battery inrush proof.')
add('R332','TNPW120622K0FEEA','22.0k1% motion-bulk discharge',
    'Resistor_SMD:R_1206_3216Metric',{1:'MOTION_BUS_P',2:'CHOPPER_N'},R_SOURCE,
    '0.52W family P70 maximum;0.096W at46V. With1128uF and+1%R,42Vto5V<54s;measure bus before service.')

# Connectors remain distinct branch-return nets until the parent board's star ties.
CON_SRC='https://www.phoenixcontact.com/en-us/products/pcb-header-mstb-25-2-gf-508-1776508'
def plug(ref,label,pins,notes='',dnp=False):
    add(ref,'1776508',label,'Connector_Phoenix_MSTB:PhoenixContact_MSTB_2,5_2-GF-5,08_1x02_P5.08mm_Horizontal_ThreadedFlange',pins,CON_SRC,
        '12A header; mating screw-flanged plug1777989. '+notes,dnp=dnp)

for ref,net in [('J1','BATT_FUSED_P'),('J2','BATT_N')]:
    add(ref,'7461103','Battery M5 160A class','PMU:Wurth_7461103',
        {i:net for i in range(1,9)},'https://www.we-online.com/components/products/datasheet/7461103.pdf',
        'All8 pins same potential; exact qualified press-fit drill; lug6mm2; insulated cover;2.2Nm maximum torque.')
for ref,net,label in [('J3','MOTION_BUS_P','Left arm +'),('J4','ARM_L_N','Left arm return'),('J5','MOTION_BUS_P','Right arm +'),('J6','ARM_R_N','Right arm return')]:
    add(ref,'7461103',label+' M5 160A class','PMU:Wurth_7461103',
        {i:net for i in range(1,9)},'https://www.we-online.com/components/products/datasheet/7461103.pdf',
        'Same qualified M5 press-fit terminal as battery.4mm2 cable with M5 ring lug;25A prototype envelope,temperature validation. KDSP4/1 1714029 is an alternate requiring another footprint.')
plug('J7','Drive 8A peak',{1:'MOTION_BUS_P',2:'DRIVE_N'},'1.5mm2 trunk.')
plug('J8','24V lift-buck INPUT',{1:'MOTION_BUS_P',2:'LIFT_N'},'1.0mm2;5A provisional input.')
plug('J9','12V PC-buck INPUT',{1:'PC_BUCK_IN_P',2:'PC_N'},'0.75mm2;3A input.')
plug('J10','5V logic-buck INPUT',{1:'LOGIC_BUCK_IN_P',2:'LOGIC_BUCK_N'},'1.0mm2;2A provisional input.')
plug('J11','5V converter OUTPUT return',{1:'+5V',2:'LOGIC_5V_N'},'1.0mm2;5A input to board; key separately fromJ10.')
plug('J12','External resistor bank',{1:'MOTION_BUS_P',2:'CHOP_DRAIN'},'1.5mm2 high-temp twisted pair; neither pin is ground.')
plug('J13','24V lift clamp DNP',{1:'LIFT_24V_SAMPLE',2:'LIFT_24V_N'},'Sample external converter OUTPUT only; separately keyed.',dnp=True)
plug('J14','Analog bank NTC',{1:'CHOP_NTC',2:G},'NTCLE100E3103GB0,10k2%; electrically insulated to hotter resistor chassis.')
plug('J15','Telemetry bank NTC',{1:'CHOP_TEMP_ADC',2:'LOGIC_GND'},'Second NTCLE100E3103GB0; no shared sensor or local wiring withJ14. Grounds ultimately join at the systemstar.')
for ref,label in [('J16','CAN backbone IN'),('J17','CAN backbone OUT')]:
    add(ref,'BM04B-GHS-TBT(LF)(SN)',label,
        'Connector_JST:JST_GH_BM04B-GHS-TBT_1x04-1MP_P1.25mm_Vertical',
        {1:'CAN_H',2:'CAN_L',3:'LOGIC_GND',4:'CHASSIS'},
        'https://www.jst-mfg.com/product/pdf/eng/eGH.pdf',
        'Mating GHR-04V-S housing and SSHL-002T-P0.2 contacts. Linear CAN backbone; short parallel link across board; shield to CHASSIS strategy in CAN sheet.')
add('J18','1776511','5V LED strip 5A',
    'Connector_Phoenix_MSTB:PhoenixContact_MSTB_2,5_3-GF-5,08_1x03_P5.08mm_Horizontal_ThreadedFlange',
    {1:'+5V',2:'LED_DATA_OUT',3:'LOGIC_5V_N'},
    'https://www.phoenixcontact.com/en-au/products/pcb-header-mstb-25-3-gf-508-1776511',
    '12A rated; mating1777992 screw-flanged plug. 1mm2 power/return;0.25mm2 data. LED return is LOGIC_5V_N direct broad copper toJ11.2/NT8; data reference meetsLOGIC_GND atsystemstar, never viaNT9 smallsignalneck.')

result = {
    'metadata': {'rev_a_engineering_prototype': True, 'rev_b_production': False,
        'status':'reviewable_circuit_candidate_not_hardware_validated',
        'net_ties_required':[['CHOP_GND','CHOPPER_N'],['CHOPPER_N','BATT_N'],['ARM_L_N','BATT_N'],['ARM_R_N','BATT_N'],['DRIVE_N','BATT_N'],['LIFT_N','BATT_N'],['PC_N','BATT_N'],['LOGIC_BUCK_N','BATT_N'],['LOGIC_5V_N','BATT_N']],
        'external_components':[{'mpn':'RH10010R00FE01','quantity':2,'description':'10ohm100W1% aluminum-housed resistor;parallel bank'},
            {'mpn':'NTCLE100E3103GB0','quantity':2,'description':'10k2% external thermistors, independent analog and telemetry circuits'},
            {'mpn':'1777989','quantity':8,'description':'Mating two-position screw-flanged plugs;add1 forDNPJ13 when fitted'}]},
    'components':parts,
}
for component in parts:
    component['pin_names'] = dict(component['pins'])
    component['pin_types'] = {p:'passive' for p in component['pins']}
    if component['ref'].startswith('D'):
        component['pin_names'] = {'1':'K','2':'A'}
    if component['ref'] in ('Q41','Q42','Q43'):
        component['pin_names'] = {'1':'G','2':'S','3':'D'}
        component['pin_types']['1'] = 'input'
    if component['ref'] == 'Q44':
        component['pin_names'] = {'1':'B','2':'E','3':'C'}
        component['pin_types']['1'] = 'input'
    if component['ref'] == 'Q40':
        component['pin_names'] = {'1':'G','2':'S_LEADS_2_TO_8','3':'D_TAB'}
        component['pin_types']['1'] = 'input'
    for p,net in component['pins'].items():
        if net.startswith('NC_'):
            component['pin_types'][p] = 'no_connect'
names = {
    'U30': ['OUT','FB','NC','GND','EN','NC','NC','IN','EP'],
    'U31': ['DNC','VIN','TEMP','GND','TRIM_NR','VOUT','NC','DNC'],
    'U32': ['OUT2','OUT1','VCC','IN1-','IN1+','IN2-','IN2+','IN3-','IN3+','IN4-','IN4+','GND','OUT4','OUT3'],
    'U33': ['VDD','OUTH','OUTL','GND','IN-','IN+'],
    'U34': ['A','K','E','C'], 'U35':['A','K','E','C'],
    'U36': ['RESET_N','GND','MR_N','CT','SENSE','VDD'],
}
for component in parts:
    if component['ref'] in names:
        component['pin_names'] = {str(p):name for p,name in enumerate(names[component['ref']],1)}
        if component['ref'] == 'U30':
            component['pin_types'] = {'1':'power_out','2':'input','3':'no_connect','4':'power_in','5':'input','6':'no_connect','7':'no_connect','8':'power_in','9':'power_in'}
        if component['ref'] == 'U31':
            component['pin_types'] = {'1':'no_connect','2':'power_in','3':'no_connect','4':'power_in','5':'no_connect','6':'power_out','7':'no_connect','8':'no_connect'}
        if component['ref'] == 'U32':
            component['pin_types'] = {str(p):('power_in' if p in(3,12) else 'open_collector' if p in(1,2,13,14) else 'input') for p in range(1,15)}
        if component['ref'] == 'U33':
            component['pin_types'] = {'1':'power_in','2':'output','3':'output','4':'power_in','5':'input','6':'input'}
        if component['ref'] == 'U36':
            component['pin_types'] = {'1':'open_collector','2':'power_in','3':'input','4':'no_connect','5':'input','6':'power_in'}
        if component['ref'] in ('U34','U35'):
            component['pin_types']['4'] = 'open_collector'

(ROOT/'chopper-parts.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
print(f'{len(parts)} parts written')
