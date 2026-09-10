"""Explicit PCB star junctions, accessible measurements, and ERC source models."""
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[1]
components = []


def add(ref, value, footprint, pins, **kwargs):
    components.append(dict(ref=ref, value=value, mpn='', footprint=footprint,
                           pins=pins, sheet='09b_star_and_measurements',
                           source_url='', in_bom=False, **kwargs))


# One intentional physical junction per return branch. Each high-current tie is
# reinforced by the removable copper star plate; LOGIC_GND has a separate neck.
for i, net in enumerate(['ARM_L_N', 'ARM_R_N', 'DRIVE_N', 'LIFT_N', 'PC_N',
                         'LOGIC_BUCK_N', 'CHOPPER_N', 'LOGIC_5V_N', 'LOGIC_GND'], 1):
    add(f'NT{i}', f'{net} to BATT_N at star',
        'PMU_RevA:NetTie_Power_2' if i < 9 else 'PMU_RevA:NetTie_Logic_2',
        {'1': net, '2': 'BATT_N'}, notes='Physical star, not a populated resistor.')
add('NT10', 'Chopper local analog reference', 'PMU_RevA:NetTie_Logic_2',
    {'1': 'CHOP_GND', '2': 'CHOPPER_N'}, notes='Join beside chopper FET source, outside resistor return current.')

busbars=json.loads((ROOT/'manufacturing'/'busbar-pcb-interface.json').read_text())
bar_placements={}
for contact in busbars['new_pcb_contacts']:
    add(contact['ref'], contact['bar']+' copper clamp contact', 'PMU_RevA:Busbar_Contact_M3_D8',
        {'1':contact['net']}, pin_types={'1':'passive'},
        notes='Bare PCB feature; separate Cu bar and clamping hardware in external BOM.')
    bar_placements[contact['ref']]=[contact['x'],contact['y'],contact['rotation']]
(ROOT/'design'/'placement-busbar.json').write_text(json.dumps(bar_placements,indent=2))

testnets = [
    'BATT_FUSED_P', 'BATT_SENSED_P', 'MAIN_KELVIN_P', 'MAIN_KELVIN_N',
    'MAIN_COMMON', 'SYS_BUS_P', 'MOTION_KELVIN_P', 'MOTION_KELVIN_N',
    'MOTION_COMMON', 'MOTION_BUS_P', 'PC_BUCK_IN_P', 'LOGIC_BUCK_IN_P',
    'V5V', 'V3V3', 'BATT_N', 'LOGIC_GND', 'AON_3V3', 'AON_WAKE_EN',
    'MAIN_FAULT_N', 'MAIN_TMR', 'MOTION_GATE_EN', 'MOTION_FLT_N',
    'MOTION_TEMP_FLT_N', 'MOTION_TMR', 'MOTION_IMON_INPUT', 'CHOP_GATE',
    'CHOP_10V', 'CHOP_REF2V5', 'CHOP_FAULT_N', 'CHOP_ACTIVE_N',
    'CAN_TX', 'CAN_RX', 'ESP_MAIN_HOLD', 'ESP_MOTION_RESET',
    'LIFT_24V_SAMPLE', 'LIFT_24V_N', 'PC_EFUSE_FAULT_N', 'PC_EFUSE_PGOOD',
    'LOGIC_EFUSE_FAULT_N', 'LOGIC_EFUSE_PGOOD',
]
all_nets = {n for name in ['power-parts.json', 'wake-io-parts.json', 'chopper-parts.json']
            for c in json.loads((ROOT/'design'/name).read_text(encoding='utf-8'))['components']
            for n in c['pins'].values() if n}
all_nets |= {'V5V', 'V3V3'}
for i, net in enumerate(testnets, 1):
    if net not in all_nets:
        print(f'Not adding a disconnected test point for absent net {net}')
        continue
    add(f'TP{i}', net, 'TestPoint:TestPoint_Pad_D2.0mm', {'1': net},
        notes='Bare labelled PCB probe pad; not a purchased part.')

# ERC cannot infer power transfer through shunts/FETs/net ties. Declare sources
# only where the documented external source or controlled power path exists.
for i, (net, reason) in enumerate([
    ('BATT_FUSED_P', 'External fused positive bench/battery input at J1'),
    ('BATT_N', 'External supply return at J2'),
    ('BATT_SENSED_P', 'BATT_FUSED_P through four-terminal RSH1'),
    ('AON_LDO_IN', 'BATT_FUSED_P through current-limiting AON input resistor chain R200/R201'),
    ('SYS_BUS_P', 'Main controlled back-to-back FET power path'),
    ('MOTION_BUS_P', 'SYS_BUS_P through RSH2 and controlled motion FET path'),
    ('V5V', 'External regulated five-volt converter input connector'),
    ('LOGIC_GND', 'Passive star junction NT9 to BATT_N'),
    ('CHOP_GND', 'NT10 local Kelvin reference then NT7 power star'),
], 1):
    add(f'#PWR{i:03}', f'ERC source: {net}', '', {'1': net}, on_board=False,
        pin_names={'1': 'PWR_FLAG'}, pin_types={'1': 'power_out'}, notes=reason)

(ROOT/'design'/'integration-parts.json').write_text(json.dumps({
    'metadata': {'rev_a_engineering_prototype': True, 'rev_b_production': False,
                 'status': 'integration_circuit_features'},
    'components': components}, indent=2), encoding='utf-8')
print(f'Wrote {len(components)} integration features.')
