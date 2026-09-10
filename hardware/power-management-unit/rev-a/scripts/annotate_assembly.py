"""Add assembly orientation graphics on F.Fab without native CAD mutation.

All footprint graphics use local coordinates and the same specification in the
vendored library and embedded board instances. Existing text outside changed
Fab primitives is copied literally; protected s-expression data and every
existing UUID are checked before a file can be written. No pcbnew dependency.

API: annotate_footprint_text(text, identifier=None) -> (text, summary)
     annotate_board_text(text) -> (text, summary)
     annotate_libraries(library_root) -> list[summary]
CLI requires an explicit output path or --in-place for the board. Pass the
matching copied libraries when testing; the supplied library directory is edited.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import uuid

from sexpr import TOKEN, parse, dump, child, children, unquote

NAMESPACE = uuid.UUID('06593d06-f424-501d-8294-460e1b2c239d')
TARGETS = {
    'CCPAK1212_SOT8000A': 'PMU_RevA',
    'VQFN_RGE24_4x4_P0.5_EP_FLOAT': 'PMU_RevA',
    'CSS4J_4026_Kelvin': 'PMU_RevA',
    'Wurth_7461103': 'PMU',
}
M5_FACES = {'J1': -1, 'J2': -1, 'J3': -1, 'J4': 1, 'J5': -1, 'J6': 1}
BODY_BOUNDS = {
    'CCPAK1212_SOT8000A': (-6, -4.7, 6, 4.7),
    'VQFN_RGE24_4x4_P0.5_EP_FLOAT': (-2, -2, 2, 2),
}


def q(value):
    return json.dumps(str(value))


def number(value):
    return format(float(value), '.9g')


def direct_forms(text):
    """Yield (start,end,head) for direct children, preserving source spans."""
    depth = 0
    start = None
    for token in TOKEN.finditer(text):
        value = token.group()
        if value == '(':
            depth += 1
            if depth == 2:
                start = token.start()
        elif value == ')':
            if depth == 2:
                match = re.match(r'\(\s*([^\s()]+)', text[start:token.end()])
                yield start, token.end(), match[1]
            depth -= 1
            if depth < 0:
                raise ValueError('Unbalanced s-expression')
    if depth:
        raise ValueError('Unbalanced s-expression')


def layer(node):
    value = child(node, 'layer')
    return unquote(value[1]) if value else None


def is_fab_graphic(node):
    return (isinstance(node, list) and node and
            node[0].startswith(('fp_', 'gr_')) and layer(node) == 'F.Fab')


def protected(node):
    if not isinstance(node, list):
        return node
    return [protected(item) for item in node if not is_fab_graphic(item)]


def all_uuids(node):
    if not isinstance(node, list):
        return []
    if node and node[0] == 'uuid':
        return [unquote(node[1])]
    return [value for item in node for value in all_uuids(item)]


def verify_preserved(before, after):
    old, new = parse(before), parse(after)
    protected_old, protected_new = protected(old), protected(new)
    if protected_old != protected_new:
        raise AssertionError('Annotation changed non-F.Fab s-expression data')
    old_ids, new_ids = all_uuids(old), all_uuids(new)
    if not set(old_ids).issubset(new_ids):
        raise AssertionError('Annotation removed an existing UUID')
    if len(new_ids) != len(set(new_ids)):
        raise AssertionError('Annotation introduced or retained duplicate UUIDs')
    return {'non_fab_data_preserved': True, 'all_existing_uuids_preserved': True,
            'non_fab_semantic_sha256':hashlib.sha256(dump(protected_old).encode('utf-8')).hexdigest(),
            'existing_uuid_count': len(old_ids), 'added_uuid_count': len(new_ids)-len(old_ids)}


def primitive(text, owner, marker):
    node = parse(text)
    node.append(['uuid', q(uuid.uuid5(NAMESPACE, owner+'|'+marker))])
    return node


def line(start, end, owner, marker, kind='fp_line'):
    return primitive(f'({kind} (start {number(start[0])} {number(start[1])}) '
                     f'(end {number(end[0])} {number(end[1])}) '
                     '(stroke (width 0.15) (type default)) (layer "F.Fab"))', owner, marker)


def label(value, x, y, size, owner, marker, board=False):
    kind = 'gr_text' if board else 'fp_text user'
    return primitive(f'({kind} {q(value)} (at {number(x)} {number(y)} 0) '
                     f'(layer "F.Fab") (effects (font (size {size} {size}) '
                     '(thickness 0.1))))', owner, marker)


def graphic_specs(name, owner):
    nodes = []
    if name == 'CCPAK1212_SOT8000A':
        nodes += [primitive('(fp_circle (center -5.3 4.05) (end -5 4.05) '
                            '(stroke (width 0.15) (type default)) (fill none) (layer "F.Fab"))', owner, 'pin1-index'),
                  label('1 G', -3.9, 4.05, .65, owner, 'pin1-label'),
                  label('S 2-6', 1.4, 4.05, .65, owner, 'source-label'),
                  label('D 7-12 / 13', 0, -3.8, .65, owner, 'drain-label')]
    elif name == 'VQFN_RGE24_4x4_P0.5_EP_FLOAT':
        nodes += [line((-1.95,-1.2), (-1.2,-1.95), owner, 'pin1-diagonal'),
                  label('1', -1.4, -1.25, .45, owner, 'pin1-label'),
                  label('EP25 FLOAT', 0, -.4, .42, owner, 'ep-float'),
                  label('NO VIA', 0, .4, .42, owner, 'ep-no-via')]
    elif name == 'CSS4J_4026_Kelvin':
        nodes.append(label('SENSE 2 / 3', 0, -1.2, .65, owner, 'sense-side'))
        for side in (-1,1):
            x1, x2 = sorted((side*2.75,side*5.3))
            nodes += [line((x1,-2.6),(x2,-2.6),owner,f'split-{side}'),
                      line((side*2.75,-3.6),(side*2.75,-1.9),owner,f'inner-{side}')]
        nodes += [label('1 FORCE',-3,1,.65,owner,'force1'),
                  label('4 FORCE',3,1,.65,owner,'force4')]
    elif name == 'Wurth_7461103':
        nodes += [line((0,-4.3),(0,-.7),owner,'axis'),
                  line((0,.7),(0,4.3),owner,'axis-south'),
                  line((0,-4.3),(-.7,-3.4),owner,'axis-n-left'),
                  line((0,-4.3),(.7,-3.4),owner,'axis-n-right'),
                  line((0,4.3),(-.7,3.4),owner,'axis-s-left'),
                  line((0,4.3),(.7,3.4),owner,'axis-s-right'),
                  label('M5 AXIS',0,0,.65,owner,'axis-label')]
    return nodes


def replace_spans(text, replacements):
    for start,end,value in sorted(replacements,reverse=True):
        text = text[:start]+value+text[end:]
    return text


def merge_graphics(text, graphics):
    existing = {}
    for start,end,head in direct_forms(text):
        if head.startswith(('fp_', 'gr_')):
            node = parse(text[start:end])
            identifier = child(node,'uuid')
            if identifier:
                existing[unquote(identifier[1])] = (start,end,node)
    replacements, additions = [], []
    for node in graphics:
        identifier = unquote(child(node,'uuid')[1])
        if identifier in existing:
            start,end,old = existing[identifier]
            if old != node:
                replacements.append((start,end,dump(node)))
        else:
            additions.append(node)
    if additions:
        end = text.rfind(')')
        replacements.append((end,end,'\n'+'\n'.join(dump(n) for n in additions)+'\n'))
    return replace_spans(text,replacements)


def annotate_footprint_text(text, identifier=None):
    ast = parse(text)
    identifier = identifier or unquote(ast[1])
    name = identifier.split(':')[-1]
    if name not in TARGETS:
        return text, {'footprint':identifier,'changed':False}
    fp_uuid = child(ast,'uuid')
    owner = unquote(fp_uuid[1]) if fp_uuid else TARGETS[name]+':'+name
    changed = text
    if name in BODY_BOUNDS:
        replacements = []
        for start,end,head in direct_forms(text):
            node = parse(text[start:end]) if head == 'fp_rect' else None
            if node and layer(node) == 'F.Fab':
                xmin,ymin,xmax,ymax = BODY_BOUNDS[name]
                child(node,'start')[1:] = [number(xmin),number(ymin)]
                child(node,'end')[1:] = [number(xmax),number(ymax)]
                if parse(text[start:end]) != node:
                    replacements.append((start,end,dump(node)))
                break
        changed = replace_spans(changed,replacements)
    specs = graphic_specs(name,owner)
    at = child(ast,'at')
    # KiCad embedded fp_text angles are board angles. Keep the same local text
    # orientation as the 0-degree library when the footprint itself is rotated.
    angle = float(at[3]) if at and len(at)>3 else 0
    for node in specs:
        if node[0] == 'fp_text':
            child(node,'at')[3] = number(angle)
    changed = merge_graphics(changed,specs)
    return changed, {'footprint':identifier,'changed':changed!=text,
                     **verify_preserved(text,changed)}


def annotate_board_text(text):
    replacements, summaries, face_graphics = [], [], []
    for start,end,head in direct_forms(text):
        if head != 'footprint':
            continue
        original = text[start:end]
        ast = parse(original)
        name = unquote(ast[1]).split(':')[-1]
        if name not in TARGETS:
            continue
        ref = next(unquote(p[2]) for p in children(ast,'property') if unquote(p[1])=='Reference')
        changed, summary = annotate_footprint_text(original)
        summary['reference'] = ref
        summaries.append(summary)
        if changed != original:
            replacements.append((start,end,changed))
        if name == 'Wurth_7461103' and ref in M5_FACES:
            at = child(ast,'at')
            x,y = map(float,at[1:3])
            angle = float(at[3]) if len(at)>3 else 0
            if angle % 360:
                raise AssertionError(f'{ref}: expected existing 0-degree M5 footprint')
            sign = M5_FACES[ref]
            owner = 'board-assembly-'+ref
            tip = (x,y+sign*10)
            face_graphics += [line((x,y+sign*4.5),tip,owner,'face-axis','gr_line'),
                              line(tip,(x-1,y+sign*8.5),owner,'face-left','gr_line'),
                              line(tip,(x+1,y+sign*8.5),owner,'face-right','gr_line'),
                              line((x-3,y+sign*4.5),(x+3,y+sign*4.5),owner,'flange-face','gr_line'),
                              label(ref+' M5 FACE '+('-Y' if sign<0 else '+Y'),x,y+sign*11.8,.8,owner,'face-label',True)]
    changed = merge_graphics(replace_spans(text,replacements),face_graphics)
    return changed, {'footprints':summaries,'m5_face_directions':M5_FACES,
                     'changed':changed!=text, **verify_preserved(text,changed)}


def annotate_libraries(library_root):
    results=[]
    for name,library in TARGETS.items():
        path = Path(library_root)/(library+'.pretty')/(name+'.kicad_mod')
        before = path.read_bytes().decode('utf-8')
        after,summary = annotate_footprint_text(before,library+':'+name)
        if before != after:
            path.write_bytes(after.encode('utf-8'))
        results.append({'path':str(path),**summary})
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board',required=True,type=Path)
    output = parser.add_mutually_exclusive_group(required=True)
    output.add_argument('--output',type=Path)
    output.add_argument('--in-place',action='store_true')
    parser.add_argument('--library-root',required=True,type=Path)
    parser.add_argument('--report',required=True,type=Path)
    args = parser.parse_args()
    before = args.board.read_bytes()
    after,summary = annotate_board_text(before.decode('utf-8'))
    repeat,_ = annotate_board_text(after)
    if after != repeat:
        raise AssertionError('Board annotation is not idempotent')
    libraries = annotate_libraries(args.library_root)
    dest = args.board if args.in_place else args.output
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(after.encode('utf-8'))
    report = {'metadata':{'rev_a_engineering_prototype':True,'rev_b_production':False,
                          'scope':'F.Fab orientation graphics only; no fabrication or bench release'},
              'input_board':str(args.board),'output_board':str(dest),
              'input_sha256':hashlib.sha256(before).hexdigest(),
              'output_sha256':hashlib.sha256(after.encode('utf-8')).hexdigest(),
              'idempotent':True,'board':summary,'libraries':libraries}
    args.report.parent.mkdir(parents=True,exist_ok=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'footprints':len(summary['footprints']),'changed':summary['changed'],
                      'added_uuid_count':summary['added_uuid_count'],'idempotent':True}))


if __name__ == '__main__':
    main()
