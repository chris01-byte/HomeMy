"""Generate native, hierarchical KiCad schematics from reviewed pin-level records.

Symbols deliberately retain electrical pin types: ERC is not bypassed by marking
all pins passive. Global net labels make cross-sheet connectivity explicit.
No manufacturing-release flag is changed by this generator.
"""
from collections import defaultdict
from pathlib import Path
import csv
import json
import math
import re
import uuid

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / 'kicad'
PROJECT = 'HomeMy_PMU_RevA'
NS = uuid.UUID('1f394355-692f-40be-a05c-df7cd87a661a')


def uid(key):
    return str(uuid.uuid5(NS, key))


def q(text):
    return json.dumps(str(text), ensure_ascii=False)


def effect(size=1.0, extra=''):
    return f'(effects (font (size {size} {size})) {extra})'


def txt(text, x, y, size=1.3):
    return f'(text {q(text)} (at {x:.3f} {y:.3f} 0) {effect(size,"(justify left)")} (uuid {uid(f"text:{text}:{x}:{y}")}))'


def prop(key, value, x, y, hidden=False):
    return f'(property {q(key)} {q(value)} (at {x:.3f} {y:.3f} 0) {effect(1.0,"(hide yes)" if hidden else "")})'


def natural(value):
    return [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', value)]


ALIASES = {'+3V3': 'V3V3', '+5V': 'V5V'}


def load_components():
    parts = []
    for filename in ('power-parts.json', 'wake-io-parts.json', 'chopper-parts.json', 'integration-parts.json'):
        path = ROOT / 'design' / filename
        data = json.loads(path.read_text(encoding='utf-8'))
        for item in data['components']:
            c = dict(item)
            c['dnp'] = bool(c.get('dnp', False) or str(c.get('population', '')).upper() == 'DNP')
            c['source_file'] = str(path.relative_to(ROOT)).replace('\\', '/')
            c['pins'] = {str(p): ALIASES.get(n, n) for p, n in c['pins'].items()}
            for pin, net in c['pins'].items():
                if c.get('pin_types', {}).get(pin) == 'no_connect' and str(net).startswith('NC_'):
                    c['pins'][pin] = None
            if 'sheet' not in c:
                raise ValueError(f'{c["ref"]}: missing sheet in {path.name}')
            parts.append(c)
    seen = set()
    for c in parts:
        if c['ref'] in seen:
            raise ValueError(f'Duplicate reference {c["ref"]}')
        seen.add(c['ref'])
        if c.get('on_board', True) and not c.get('footprint'):
            raise ValueError(f'{c["ref"]}: missing footprint')
    return sorted(parts, key=lambda c: natural(c['ref']))


def symbol_definition(c):
    ref = c['ref']
    pins = sorted(c['pins'], key=natural)
    count = len(pins)
    half = math.ceil(count / 2)
    height = max(7.62, (half + 1) * 2.54)
    width = 27.94 if count > 4 else 10.16
    simple_resistor = ref.startswith('R') and count == 2
    simple_capacitor = ref.startswith('C') and count == 2
    simple_passive = simple_resistor or simple_capacitor
    # A small connector can have long, meaningful pin names on both sides.
    # Reserve body width for those names without changing any pin identifiers.
    if not simple_passive:
        names = [str(c.get('pin_names', {}).get(p, p)) for p in pins]
        left_chars = max((len(n) for n in names[:half]), default=0)
        right_chars = max((len(n) for n in names[half:]), default=0)
        # Full body width must be a2.54mm multiple so both edges/pins remain
        # on the1.27mm schematic connection grid.
        width = max(width, math.ceil(((left_chars + right_chars) * 0.60 + 4.0) / 2.54) * 2.54)
    name = f'PMU_RevA:{ref}'
    pin_names = '(pin_names (offset 0.8) hide)' if simple_passive else '(pin_names (offset 0.8))'
    body = []
    if simple_passive:
        row_y = height / 2 - 2.54
        if simple_resistor:
            body.append(f'(rectangle (start -3.81 {row_y+1.27}) (end 3.81 {row_y-1.27}) (stroke (width 0.254) (type default)) (fill (type none)))')
            inner = 3.81
        else:
            inner = 1.27
            for plate_x in (-inner, inner):
                body.append(f'(polyline (pts (xy {plate_x} {row_y-2.54}) (xy {plate_x} {row_y+2.54})) (stroke (width 0.254) (type default)) (fill (type none)))')
            if 'CP_' in c.get('footprint', ''):
                body.append(f'(text "+" (at -2.54 {row_y+3.81} 0) {effect(1.27)})')
        for sign in (-1, 1):
            body.append(f'(polyline (pts (xy {sign*width/2} {row_y}) (xy {sign*inner} {row_y})) (stroke (width 0.254) (type default)) (fill (type none)))')
    else:
        body.append(f'(rectangle (start {-width/2} {height/2}) (end {width/2} {-height/2}) (stroke (width 0.254) (type default)) (fill (type background)))')
    lines = [f'(symbol {q(name)} {pin_names} (in_bom {"yes" if c.get("in_bom",True) else "no"}) (on_board {"yes" if c.get("on_board",True) else "no"})',
             prop('Reference', ref, 0, height / 2 + 3),
             prop('Value', c['value'], 0, height / 2 + 5),
             prop('Footprint', c['footprint'], 0, 0, True),
             f'(symbol {q(ref+"_0_1")} ' + ' '.join(body) + ')',
             f'(symbol {q(ref+"_1_1")}']
    geometry = {}
    for idx, pin in enumerate(pins):
        left = idx < half
        row = idx if left else idx - half
        x = -(width / 2 + 5.08) if left else width / 2 + 5.08
        y = height / 2 - 2.54 * (row + 1)
        angle = 0 if left else 180
        name = c.get('pin_names', {}).get(pin, pin)
        kind = c.get('pin_types', {}).get(pin)
        if not kind:
            if ref.startswith(('R', 'C', 'D', 'J', 'TP', 'NT', 'H')):
                kind = 'passive'
            else:
                raise ValueError(f'{ref}.{pin}: electrical pin type missing')
        lines.append(f'(pin {kind} line (at {x} {y} {angle}) (length 5.08) (name {q(name)} {effect(0.95)}) (number {q(pin)} {effect(0.85)}))')
        geometry[pin] = (x, y, left)
    lines.append('))')
    return '\n'.join(lines), geometry, width, height


def sheet_header(name, sheet_id, libraries):
    display_titles = {
        '00': 'Power tree', '01': 'Battery and shunt', '02': 'Main switch',
        '03': 'Motion gate', '04': 'Brake chopper', '05': 'PC and 5V eFuses',
        '06a': 'Wake and main latch', '06b': 'Motion interlocks', '06c': 'ESP32 and logic',
        '07': 'INA228 and analog', '08': 'CAN and LED', '09': 'Connectors',
        '09b': 'Star and test points',
    }
    prefix = name.split('_')[0].split(' ')[0]
    title = 'PMU A / ' + display_titles.get(prefix, name.replace('_', ' '))
    page = re.search(r'_p(\d+)$', name)
    if page:
        title += ' / ' + page.group(1)
    return [f'(kicad_sch (version 20250114) (generator "homemy_pmu_builder") (uuid {sheet_id}) (paper "A2")',
            f'(title_block (title {q(title)}) (date "2026-09-10") (rev "A") (company "HomeMy") (comment 1 "rev_a_engineering_prototype: true") (comment 2 "rev_b_production: false") (comment 3 "Review before ordering; see release.json"))',
            '(lib_symbols ' + '\n'.join(libraries) + ')']


def place_component(c, x, y, path, geometry):
    ref = c['ref']
    lines = []
    sid = uid('component:' + ref)
    lines.append(f'(symbol (lib_id {q("PMU_RevA:"+ref)}) (at {x:.3f} {y:.3f} 0) (unit 1) (in_bom {"yes" if c.get("in_bom",True) else "no"}) (on_board {"yes" if c.get("on_board",True) else "no"}) (dnp {"yes" if c.get("dnp") else "no"}) (uuid {sid})')
    top = min(y - v[1] for v in geometry.values()) - 6
    lines.extend([prop('Reference', ref, x, top), prop('Value', c['value'], x, top + 2),
                  prop('Footprint', c['footprint'], x, y, True),
                  prop('Datasheet', c.get('source_url', ''), x, y, True),
                  prop('MPN', c.get('mpn', ''), x, y, True),
                  prop('rev_a_engineering_prototype', 'true', x, y, True),
                  prop('rev_b_production', 'false', x, y, True)])
    for pin in c['pins']:
        lines.append(f'(pin {q(pin)} (uuid {uid(ref+":"+pin)}))')
    lines.append(f'(instances (project {q(PROJECT)} (path {q(path)} (reference {q(ref)}) (unit 1)))))')
    for pin, net in c['pins'].items():
        dx, dy, left = geometry[pin]
        px, py = round(x + dx, 3), round(y - dy, 3)
        if net is None:
            lines.append(f'(no_connect (at {px} {py}) (uuid {uid(ref+":"+pin+":nc")}))')
            continue
        lx = round(px + (-3.81 if left else 3.81), 3)
        lines.append(f'(wire (pts (xy {px} {py}) (xy {lx} {py})) (stroke (width 0) (type default)) (uuid {uid(ref+":"+pin+":wire")}))')
        angle = 0 if left else 180
        justification = '(justify right)' if left else '(justify left)'
        lines.append(f'(global_label {q(net)} (shape bidirectional) (at {lx} {py} {angle}) {effect(0.9,justification)} (uuid {uid(ref+":"+pin+":label")}) {prop("Intersheetrefs","${INTERSHEET_REFS}",lx,py,True)})')
    return lines


def main():
    CAD.mkdir(exist_ok=True)
    parts = load_components()
    groups = defaultdict(list)
    for c in parts:
        groups[c['sheet']].append(c)
    paged = {}
    for name, group in groups.items():
        ordered = sorted(group, key=lambda c: (-len(c['pins']), natural(c['ref'])))
        for start in range(0, len(ordered), 40):
            actual = name if len(ordered) <= 40 else f'{name}_p{start//40+1}'
            paged[actual] = ordered[start:start+40]
            for c in paged[actual]:
                c['effective_sheet'] = actual
    groups = paged
    root_id = uid('root')
    top = sheet_header('00 top power tree', root_id, [])
    top.extend([txt('REVISION A - ENGINEERING PROTOTYPE', 25, 20, 3),
                txt('BATT_FUSED_P -> RSH1 -> BATT_SENSED_P -> main back-to-back banks -> SYS_BUS_P', 25, 30),
                txt('SYS_BUS_P -> PC eFuse | 5 V eFuse | RSH2 -> motion banks -> MOTION_BUS_P', 25, 37),
                txt('MOTION_BUS_P -> passive arms / drive / lift converter / independent analog brake chopper', 25, 44),
                txt('High-current returns meet BATT_N only at the documented star; motion defaults OFF.', 25, 51),
                txt('No physical tests performed. release.json records actual completion and check state.', 25, 58)])
    lib_defs = []
    for page, (name, group) in enumerate(sorted(groups.items()), start=2):
        sheet_id = uid('sheet:' + name)
        path = '/' + root_id + '/' + sheet_id
        defs, geometries = [], {}
        for c in group:
            definition, geom, width, height = symbol_definition(c)
            defs.append(definition)
            lib_defs.append(definition.replace('"PMU_RevA:', '"', 1))
            geometries[c['ref']] = (geom, width, height)
        lines = sheet_header(name, sheet_id, defs)
        lines.append(txt(name.replace('_', ' '), 18, 13, 2))
        # ICs first, then support components; each cell reserves space for labels.
        group.sort(key=lambda c: (-len(c['pins']), natural(c['ref'])))
        x, y, row_height = 70.0, 35.0, 0.0
        for c in group:
            geom, width, height = geometries[c['ref']]
            cell_width = 135.0 if len(c['pins']) > 4 else 107.0
            cell_height = height + 22.0
            if x + cell_width / 2 > 575:
                x, y, row_height = 70.0, y + row_height, 0.0
            if y + cell_height > 383:
                raise ValueError(f'Sheet {name} is too full: split circuit into more hierarchical sheets')
            gx = round(x / 1.27) * 1.27
            gy = round((y + height / 2 + 7) / 1.27) * 1.27
            lines += place_component(c, gx, gy, path, geom)
            x += cell_width
            row_height = max(row_height, cell_height)
        lines.append(')')
        (CAD / (name + '.kicad_sch')).write_text('\n'.join(lines), encoding='utf-8')
        idx = page - 2
        sx, sy = 25 + (idx % 3) * 182, 80 + (idx // 3) * 52
        top.append(f'(sheet (at {sx} {sy}) (size 163 34) (stroke (width 0.3) (type default)) (fill (color 0 0 0 0)) (uuid {sheet_id}) (property "Sheetname" {q(name)} (at {sx} {sy-2} 0) {effect(1.3,"(justify left)")}) (property "Sheetfile" {q(name+".kicad_sch")} (at {sx} {sy+37} 0) {effect(1.0,"(justify left)")}) (instances (project {q(PROJECT)} (path {q("/"+root_id)} (page {q(page)})))))')
    top.extend(['(sheet_instances (path "/" (page "1")))', ')'])
    (CAD / (PROJECT + '.kicad_sch')).write_text('\n'.join(top), encoding='utf-8')
    (CAD / 'PMU_RevA.kicad_sym').write_text('(kicad_symbol_lib (version 20241209) (generator "homemy_pmu_builder")\n' + '\n'.join(lib_defs) + ')', encoding='utf-8')
    (CAD / 'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "PMU_RevA") (type "KiCad") (uri "${KIPRJMOD}/PMU_RevA.kicad_sym") (options "") (descr "Verified pin maps in ../design")))', encoding='utf-8')
    if not (CAD / (PROJECT + '.kicad_pro')).exists():
        project = {'meta': {'filename': PROJECT + '.kicad_pro', 'version': 3},
                   'text_variables': {'rev_a_engineering_prototype': 'true', 'rev_b_production': 'false'},
                   'board': {'design_settings': {'rules': {'min_clearance': 0.25, 'min_track_width': 0.25, 'min_via_diameter': 0.7, 'min_through_hole_diameter': 0.3}}},
                   'erc': {'erc_exclusions': [], 'meta': {'version': 0}},
                   'net_settings': {'classes': [{'name': 'Default', 'clearance': 0.25, 'track_width': 0.3, 'via_diameter': 0.8, 'via_drill': 0.4}], 'meta': {'version': 4}}}
        (CAD / (PROJECT + '.kicad_pro')).write_text(json.dumps(project, indent=2), encoding='utf-8')
    (ROOT / 'design' / 'assembled-parts.json').write_text(json.dumps({'metadata': {'rev_a_engineering_prototype': True, 'rev_b_production': False}, 'components': parts}, indent=2), encoding='utf-8')
    print(f'Generated {len(groups)} child sheets and {len(parts)} components. ERC not yet run.')


if __name__ == '__main__':
    main()
