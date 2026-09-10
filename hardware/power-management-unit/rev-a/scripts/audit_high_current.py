"""Check reviewed tap identity, enforceable rules and native power geometry."""
import hashlib
import json
from pathlib import Path
from sexpr import parse, dump, children, child, unquote
from configure_power_rules import CAD, ROOT, PROJECT, CLASSES, POWER_NETS, high_current_rules


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    board=CAD/(PROJECT+'.kicad_pcb');pro=CAD/(PROJECT+'.kicad_pro');dru=CAD/(PROJECT+'.kicad_dru')
    b=parse(board.read_text());p=json.loads(pro.read_text());errors=[]
    capture=json.loads((ROOT/'evidence/high-current-tap-capture.json').read_text())
    items={unquote(child(x,'uuid')[1]):x for x in b if isinstance(x,list) and child(x,'uuid')}
    expected_members=set()
    for name,rows in capture['groups'].items():
        group=next((g for g in children(b,'group') if unquote(g[1])==name),None)
        actual={unquote(x) for x in child(group,'members')[1:]} if group else set()
        expected={row['uuid'] for row in rows}
        if actual!=expected:errors.append('Changed reviewed tap membership: '+name)
        expected_members.update(expected)
        for row in rows:
            item=items.get(row['uuid'])
            if item is None or hashlib.sha256(dump(item).encode()).hexdigest()!=row['sexpr_sha256']:
                errors.append('Changed or missing reviewed tap geometry: '+row['uuid'])
    assigned={x['pattern']:x['netclass'] for x in p['net_settings']['netclass_patterns']}
    for cls,nets in CLASSES.items():
        for net in nets:
            if assigned.get(net)!=cls:errors.append('Wrong netclass: '+net)
    if any('KELVIN' in n or '_SENSE_' in n for n in assigned):
        errors.append('Kelvin/measurement net was assigned a power class')
    if high_current_rules() not in dru.read_text():errors.append('Power rule generator and actual rules differ')
    if p['board']['design_settings'].get('drc_exclusions'):errors.append('Item-level DRC exclusions present')
    widths={};vias={};zones=[]
    for item in b:
        if not isinstance(item,list):continue
        if item[0] in ['segment','via']:
            net=unquote(child(item,'net')[-1])
            if net not in POWER_NETS:continue
            uid=unquote(child(item,'uuid')[1])
            if uid in expected_members:continue
            if item[0]=='segment':
                w=float(child(item,'width')[1]);minimum=6 if assigned[net]=='PWR_ARM' else 4
                widths.setdefault(net,[]).append(w)
                if w<minimum:errors.append(f'{net}: unreviewed {w} mm power track')
            else:
                size=float(child(item,'size')[1]);hole=float(child(item,'drill')[1]);vias[net]=vias.get(net,0)+1
                if size<.8 or hole<.4:errors.append(net+': undersized power via')
        elif item[0]=='zone' and child(item,'net_name'):
            net=unquote(child(item,'net_name')[1])
            if net not in POWER_NETS:continue
            minimum=float(child(item,'min_thickness')[1]);zones.append({'net':net,'min_thickness_mm':minimum})
            if minimum<1.2:errors.append(net+': power fill sliver filter below 1.2 mm')
    power=json.loads((ROOT/'evidence/filled-power-copper-review.json').read_text())
    if power['board_sha256']!=sha(board):errors.append('Power geometry uses stale board')
    if power.get('low_current_tap_items_omitted_from_power_geometry')!=len(expected_members):errors.append('Tap copper was credited to power connectivity')
    paths=power['same_layer_path_checks']
    if len(paths)<247 or not all(x['same_continuous_copper_outline'] for x in paths):errors.append('Critical power endpoint connectivity failed')
    # Freeze the reviewed power-section measurements as part of the release;
    # even a DRC-clean routing change requires regenerating/reviewing this file.
    ledger=[]
    for s in power['cross_sections']:
        ledger.append({k:s[k] for k in ['label','net','layer','line_from_mm','line_to_mm','continuous_widths_mm','total_copper_width_mm']})
    out={'rev_a_engineering_prototype':True,'rev_b_production':False,
         'passed':not errors,'errors':errors,'board_sha256':sha(board),
         'inputs_sha256':{str(x.relative_to(ROOT)):sha(x) for x in [board,pro,dru,ROOT/'evidence/high-current-tap-capture.json',ROOT/'evidence/filled-power-copper-review.json']},
         'reviewed_tap_items':len(expected_members),'power_endpoint_checks':len(paths),
         'power_tracks_min_width_mm':{n:min(w) for n,w in widths.items()},'power_via_counts':vias,
         'power_zones':zones,'cross_section_ledger':ledger,
         'limits':['DRC widths are geometry rules, not a 50 A thermal rating.','1.0 mm zone choke screen and 1.2 mm fill filter reject thin slivers, but are not a permissible full-current trunk size.','PCB polygons alone do not model external busbars, contact resistance or unequal sharing.','Every changed power path requires new native checks and renewed bottleneck review.']}
    (ROOT/'evidence/high-current-audit.json').write_text(json.dumps(out,indent=2)+'\n')
    print('High-current audit:',len(errors),'errors;',len(paths),'power paths without',len(expected_members),'tap items')
    for e in errors[:10]:print('ERROR:',e)
    return bool(errors)


if __name__=='__main__':raise SystemExit(main())
