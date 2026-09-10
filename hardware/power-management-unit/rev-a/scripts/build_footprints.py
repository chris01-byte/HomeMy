"""Vendor footprints used by this design and construct documented custom lands.

All custom pads are explicit dimensions; there is no generic package fallback.
The pin-to-pad audit must pass before a board is built.
"""
from pathlib import Path
import argparse
import json
import shutil
from sexpr import parse, dump, child, children, unquote
from annotate_assembly import annotate_footprint_text

ROOT = Path(__file__).resolve().parents[1]
CAD = ROOT / 'kicad'


def q(s):
    return json.dumps(str(s))


def custom(name, pads, width, height, source, through=False, tie=False, courtyard_margin=0.5):
    lines = [f'(footprint {q(name)} (version 20260206) (generator "homemy_pmu_builder") (layer "F.Cu")',
             f'(descr {q(source)}) (attr {"through_hole" if through else "smd"})',
             f'(property "Reference" "REF**" (at 0 {-height/2-1.5}) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))',
             f'(property "Value" {q(name)} (at 0 {height/2+1.5}) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))',
             f'(fp_rect (start {-width/2} {-height/2}) (end {width/2} {height/2}) (stroke (width 0.1) (type default)) (fill none) (layer "F.Fab"))',
             f'(fp_rect (start {-width/2-courtyard_margin} {-height/2-courtyard_margin}) (end {width/2+courtyard_margin} {height/2+courtyard_margin}) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))']
    for number, x, y, sx, sy, drill in pads:
        if drill:
            kind, shape, layers = 'thru_hole', 'circle' if sx == sy else 'oval', '"*.Cu" "*.Mask"'
        else:
            kind, shape, layers = 'smd', 'rect', '"F.Cu" "F.Paste" "F.Mask"'
        if drill and tie:
            shape='rect'
        lines.append(f'(pad {q(number)} {kind} {shape} (at {x} {y}) (size {sx} {sy}) ' + (f'(drill {drill})' if drill else '') + f' (layers {layers}))')
    if tie:
        lines.append('(net_tie_pad_groups "1,2")')
        lines.append(f'(fp_rect (start {-width/2} {-height/2}) (end {width/2} {height/2}) (stroke (width 0) (type default)) (fill solid) (layer "F.Cu"))')
    lines.append(')')
    return '\n'.join(lines)


def write_custom(library, name, data):
    target = CAD / 'libraries' / (library + '.pretty')
    target.mkdir(parents=True, exist_ok=True)
    data, _ = annotate_footprint_text(data, library+':'+name)
    (target / (name + '.kicad_mod')).write_text(data, encoding='utf-8')


def generate_custom(parts):
    for c in parts:
        if c.get('pad_geometry_mm'):
            lib, name = c['footprint'].split(':')
            geometry = c['pad_geometry_mm']
            if 'pads' in geometry:
                pads = [(p['number'], p['x'], p['y'], p['width'], p['height'], 0) for p in geometry['pads']]
            else:
                pads = [(k, *geom, 0) for k, geom in geometry.items()]
            w = max(abs(p[1])+p[3]/2 for p in pads)*2
            h = max(abs(p[2])+p[4]/2 for p in pads)*2
            if name == 'PTVS1_DFN8x6':
                w, h = max(w, 8.1), max(h, 6.1)
            text = custom(name, pads, w, h, c['source_url'])
            if geometry.get('exposed_pad_paste_coverage_target'):
                import math
                ast = parse(text)
                for pad in children(ast, 'pad'):
                    if unquote(pad[1]) == '9':
                        pad.append(['solder_paste_margin_ratio', str((math.sqrt(geometry['exposed_pad_paste_coverage_target'])-1)/2)])
                text = dump(ast)
            write_custom(lib, name, text)
    name = 'CCPAK1212_SOT8000A'
    # Nexperia package drawing, terminal numbering viewed from top. Body 12x9.4,
    # lead span 12; mb 10.8x7.25. Land toe allowance is +0.6 mm each outside edge.
    pads = []
    for idx, x in enumerate([-5, -3, -1, 1, 3, 5]):
        pads += [(str(idx+1), x, 5.65, 1.2, 1.9, 0),
                 (str(12-idx), x, -5.65, 1.2, 1.9, 0)]
    pads.append(('13', 0, 0, 10.8, 7.25, 0))
    write_custom('PMU_RevA', name, custom(name, pads, 12, 13.2,
        'Nexperia PSMN1R0-100ASF datasheet 2025-10-20 p10; project pad13=mb/drain. Land toe allowances require assembly review.'))
    name = 'VSSOP_DGX19_3x5.1_P0.5_Missing16'
    pads = [(str(i+1), -2.2, -2.25+0.5*i, 1.45, 0.3, 0) for i in range(10)]
    pads += [(str(20-i), 2.2, -2.25+0.5*i, 1.45, 0.3, 0) for i in range(10) if 20-i != 16]
    write_custom('PMU_RevA', name, custom(name, pads, 5.85, 5.1,
        'TI TPS4811-Q1 DGX0019A land pattern; physical pin16 absent.'))
    name = 'C_Rect_L31.5mm_W13mm_P27.5mm'
    write_custom('PMU_RevA', name, custom(name,
        [('1', -13.75, 0, 2.6, 2.6, 1.1), ('2', 13.75, 0, 2.6, 2.6, 1.1)],
        31.5, 13, 'WIMA MKS4C053306D00KSSD 31.5x13x24mm; pitch27.5,lead0.8mm', True))
    for name, w, h in [('NetTie_Power_2', 20, 10), ('NetTie_Logic_2', 2, 1)]:
        drill = 3.2 if w == 20 else 0
        pads = [('1', -w/4, 0, w/2, h, drill), ('2', w/4, 0, w/2, h, drill)]
        ast=parse(custom(name, pads, w, h,
            'Intentional star net tie; power ties need specified 2mm Cu clamp bridge, M3 holes.', through=bool(drill), tie=True))
        if drill:
            for pad in children(ast,'pad'):
                pad.append(['solder_mask_margin','0.1'])
        write_custom('PMU_RevA', name, dump(ast))
    name='Busbar_Contact_M3_D8'
    ast=parse(custom(name,[('1',0,0,8,8,3.2)],8,8,
        'Bare PCB annular contact for specified Cu-ETP bar; finished hole3.2, maskopening8.2; M3 clamp hardware.',True))
    child(ast,'pad').append(['solder_mask_margin','0.1'])
    write_custom('PMU_RevA',name,dump(ast))
    source = json.loads((ROOT/'design'/'chopper-footprint-specs.json').read_text())
    for identifier, s in source['footprint_specs'].items():
        lib, name = identifier.split(':')
        pads = [(p['number'], p['x'], p['y'], s['pad_diameter'], s['pad_diameter'],
                 s['finished_hole_diameter']) for p in s['pads']]
        write_custom(lib, name, custom(name, pads, s['body']['width'],
            s['body']['depth'],
            source['metadata']['source'] + '; FINISHED HOLE 1.475+/-0.05mm ENIG, copper25..60um, qualified press-fit process. Drill CAM must compensate plating.', True, courtyard_margin=1.0))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--library-root', required=True, type=Path)
    args = parser.parse_args()
    data = json.loads((ROOT/'design'/'assembled-parts.json').read_text(encoding='utf-8'))
    parts = data['components']
    generate_custom(parts)
    # LM74930 RGE0024T recommended land pattern: 24 x 0.6 x 0.25 mm,
    # 0.5 mm pitch, opposite land centers 3.8 mm; 2.1 mm FLOATING EP.
    # No thermal vias or ground connection are permissible on this EP.
    name = 'VQFN_RGE24_4x4_P0.5_EP_FLOAT'
    pads = []
    for i in range(6):
        pads.extend([(str(1+i), -1.9, -1.25+i*.5, .6, .25, 0),
                     (str(7+i), -1.25+i*.5, 1.9, .25, .6, 0),
                     (str(13+i), 1.9, 1.25-i*.5, .6, .25, 0),
                     (str(19+i), 1.25-i*.5, -1.9, .25, .6, 0)])
    pads.append(('25', 0, 0, 2.1, 2.1, 0))
    write_custom('PMU_RevA', name, custom(name, pads, 4.4, 4.4,
        'TI LM74930-Q1 RGE0024T recommended land pattern, EP25 floating, no thermal vias.'))
    errors, libraries, audit = [], set(), []
    holes = CAD/'libraries'/'MountingHole.pretty'
    holes.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(args.library_root/'MountingHole.pretty'/'MountingHole_3.2mm_M3.kicad_mod', holes/'MountingHole_3.2mm_M3.kicad_mod')
    libraries.add('MountingHole')
    for c in parts:
        if not c.get('on_board', True):
            continue
        lib, name = c['footprint'].split(':')
        libraries.add(lib)
        target = CAD/'libraries'/(lib+'.pretty')/(name+'.kicad_mod')
        if not target.exists():
            source = args.library_root/(lib+'.pretty')/(name+'.kicad_mod')
            if not source.exists():
                errors.append(f'{c["ref"]}: footprint missing: {c["footprint"]}')
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        ast = parse(target.read_text(encoding='utf-8'))
        pad_numbers = {unquote(p[1]) for p in children(ast, 'pad') if unquote(p[1])}
        expected = set(c['pins'])
        absent = expected - pad_numbers
        unexpected = pad_numbers - expected - {'MP'}
        if absent or unexpected:
            errors.append(f'{c["ref"]} {c["footprint"]}: absent{sorted(absent)} extra{sorted(unexpected)}')
        audit.append({'ref': c['ref'], 'footprint': c['footprint'],
                      'schematic_pins': sorted(expected), 'footprint_pads': sorted(pad_numbers),
                      'pin_mapping_passed': not absent and not unexpected})
    text = '(fp_lib_table (version 7)\n' + '\n'.join(
        f'(lib (name {q(lib)}) (type "KiCad") (uri {q("${KIPRJMOD}/libraries/"+lib+".pretty")}) (options "") (descr "Project-vendored footprint"))'
        for lib in sorted(libraries)) + ')'
    (CAD/'fp-lib-table').write_text(text, encoding='utf-8')
    (ROOT/'design'/'footprint-pin-audit.json').write_text(json.dumps({
        'rev_a_engineering_prototype': True, 'rev_b_production': False,
        'errors': errors, 'components': audit}, indent=2), encoding='utf-8')
    for error in errors:
        print(error)
    print(f'{len(audit)} footprints audited; {len(errors)} unresolved mappings.')
    raise SystemExit(bool(errors))


if __name__ == '__main__':
    main()
