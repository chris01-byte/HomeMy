"""Install explicit prototype power rules and reviewed, frozen tap groups.

The initial capture is tied to the previously reviewed board. Subsequent runs
never automatically exempt newly added narrow tracks. Review the manifest and
the independent power-copper connectivity check before accepting a change.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import uuid
from sexpr import parse, dump, child, children, unquote

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / 'kicad'
PROJECT = 'HomeMy_PMU_RevA'
BASE_SHA = '70bb8eb588f2fc7200f718df0e11659aad3c40c7e9d5652228eb7a58d232065f'
CLASSES = {
    'PWR_BATTERY': ['BATT_FUSED_P', 'BATT_SENSED_P', 'MAIN_COMMON', 'BATT_N'],
    'PWR_SYS': ['SYS_BUS_P'],
    'PWR_MOTION': ['MOTION_SENSED_P', 'MOTION_COMMON', 'MOTION_BUS_P'],
    'PWR_ARM': ['ARM_L_N', 'ARM_R_N'],
}
POWER_NETS = {n for nets in CLASSES.values() for n in nets}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8')


def high_current_rules():
    rules = ['# High-current rules: netclass defaults alone are NOT DRC minimums.']
    for name in CLASSES:
        width = 6 if name == 'PWR_ARM' else 4
        rules.append(f'''(rule "{name} power copper"
  (condition "A.hasNetclass('{name}')")
  (constraint track_width (min {width}mm) (opt {max(width, 6)}mm)))''')
        rules.append(f'''(rule "{name} outer power connections"
  (layer outer)
  (condition "A.hasNetclass('{name}')")
  (constraint connection_width (min 1.0mm)))''')
        rules.append(f'''(rule "{name} power vias"
  (condition "A.Type == 'Via' && A.hasNetclass('{name}')")
  (constraint via_diameter (min 0.8mm))
  (constraint hole_size (min 0.4mm)))''')
    # Groups are a frozen list of reviewed copper, not a width-based exception:
    # adding a new 0.2 mm route to any power net still fails the general rule.
    for group, width in [('PWR_TAP_CONTROL', .2), ('PWR_SYS_BRANCH_SPINE', .8),
                         ('PWR_SYS_BRANCH_FANOUT', .25)]:
        rules.append(f'''(rule "Reviewed {group}"
  (condition "A.memberOfGroup('{group}')")
  (constraint track_width (min {width}mm))
  (constraint connection_width (min {width}mm))
  (constraint via_diameter (min 0.6mm))
  (constraint hole_size (min 0.3mm)))''')
    # Exact populated gate-reference, divider, pull-up/down and timing parts.
    # RSH1/RSH2 force pads are deliberately absent; no wildcard exemption.
    taps = [f'R{i}' for i in [11,12,13,14,15,16,17,18,19,20,24,25,26,27,28,29,
            31,33,35,36,39,40,41,42,43,44,45,46,48,50,51,52,53,54,55,56,58,59,
            61,62,64,200,225,250,254,302,308,332]] + ['C6']
    power_condition = '(' + ' || '.join(f"A.hasNetclass('{name}')" for name in CLASSES) + ')'
    for ref in taps:
        rules.append(f'''(rule "Bias/reference pad neck {ref}"
  (condition "A.Type == 'Pad' && A.memberOfFootprint('{ref}') && {power_condition}")
  (constraint connection_width (min 0.2mm)))''')
    return '\n'.join(rules) + '\n'


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--capture-initial-taps', action='store_true')
    args = ap.parse_args()
    board = CAD / (PROJECT + '.kicad_pcb')
    receipt = ROOT / 'evidence/high-current-tap-capture.json'
    before = sha(board)
    if args.capture_initial_taps:
        if receipt.exists() or before != BASE_SHA:
            raise RuntimeError('Initial tap capture requires the exact reviewed baseline and no existing receipt')
        source = board.read_text(encoding='utf-8')
        ast = parse(source)
        groups = {n: [] for n in ['PWR_TAP_CONTROL', 'PWR_SYS_BRANCH_SPINE', 'PWR_SYS_BRANCH_FANOUT']}
        for item in ast:
            if not isinstance(item, list) or item[0] not in ['segment', 'via']:
                continue
            net = unquote(child(item, 'net')[-1])
            if net not in POWER_NETS:
                continue
            if item[0] == 'via':
                if float(child(item, 'drill')[1]) >= .4:
                    continue
                group = 'PWR_TAP_CONTROL'
            else:
                width = float(child(item, 'width')[1])
                if width >= 4:
                    continue
                group = ('PWR_SYS_BRANCH_FANOUT' if width == .25 else 'PWR_SYS_BRANCH_SPINE') if net == 'SYS_BUS_P' and width >= .25 else 'PWR_TAP_CONTROL'
            groups[group].append({'uuid': unquote(child(item, 'uuid')[1]), 'net': net,
                                  'kind': item[0], 'sexpr_sha256': hashlib.sha256(dump(item).encode()).hexdigest()})
        additions = []
        for name, members in groups.items():
            identity = str(uuid.uuid5(uuid.NAMESPACE_URL, 'HomeMy RevA ' + name))
            ids = ' '.join(json.dumps(x['uuid']) for x in members)
            additions.append(f'(group "{name}" (uuid "{identity}") (members {ids}))')
        updated = source.rstrip()[:-1] + '\n' + '\n'.join(additions) + '\n)\n'
        old_geometry = [x for x in ast if not (isinstance(x, list) and x[0] == 'group')]
        new_geometry = [x for x in parse(updated) if not (isinstance(x, list) and x[0] == 'group')]
        assert old_geometry == new_geometry
        board.write_text(updated, encoding='utf-8')
        write_json(receipt, {'rev_a_engineering_prototype': True, 'rev_b_production': False,
            'input_board_sha256': before, 'output_board_sha256': sha(board),
            'copper_and_non_group_data_identical': True, 'groups': groups,
            'control_scope': 'Existing testpoint, divider, bias, gate-reference and control-return branches only. No new track is automatically exempted.',
            'sys_branch_scope': 'U3/U4 eFuse input spines and six short 0.25 mm package fanouts; at most 3 A/2 A branch design envelopes, not 50 A main current.',
            'requirement': 'All captured members must retain exact geometry; full-current pad connectivity must be independently checked without tap members.'})
    pro = CAD / (PROJECT + '.kicad_pro')
    project = json.loads(pro.read_text(encoding='utf-8'))
    project['board']['design_settings']['rule_severities']['connection_width'] = 'error'
    settings = project['net_settings']
    settings['classes'] = [c for c in settings['classes'] if c['name'] not in CLASSES]
    default = next(c for c in settings['classes'] if c['name'] == 'Default')
    for priority, (name, nets) in enumerate(CLASSES.items()):
        c = copy.deepcopy(default)
        c.update(name=name, priority=priority, track_width=6.0, via_diameter=.8, via_drill=.4)
        settings['classes'].append(c)
    settings['netclass_patterns'] = [x for x in settings['netclass_patterns'] if x.get('netclass') not in CLASSES]
    settings['netclass_patterns'] += [{'netclass': name, 'pattern': net} for name, nets in CLASSES.items() for net in nets]
    write_json(pro, project)
    dru = CAD / (PROJECT + '.kicad_dru')
    existing = dru.read_text(encoding='utf-8').split('# High-current rules:')[0]
    dru.write_text(existing.rstrip() + '\n' + high_current_rules(), encoding='utf-8')
    print('Installed four explicit power netclasses and enforceable minimums; geometry preserved except review groups.')


if __name__ == '__main__':
    main()
