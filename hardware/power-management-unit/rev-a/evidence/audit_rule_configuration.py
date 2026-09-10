"""Read-only native-project/rule/report snapshot for the independent review."""
from pathlib import Path
import sys,json,hashlib,collections
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from sexpr import parse,children,child,unquote
CAD=ROOT/'kicad'
pro=CAD/'HomeMy_PMU_RevA.kicad_pro';dru=CAD/'HomeMy_PMU_RevA.kicad_dru';pcb=CAD/'HomeMy_PMU_RevA.kicad_pcb'
d=json.loads(pro.read_text(encoding='utf-8'))
b=parse(pcb.read_text(encoding='utf-8'))
missing=[];mixed=[]
for f in children(b,'footprint'):
    props={unquote(p[1]):unquote(p[2]) for p in children(f,'property')}
    ref=props.get('Reference','?')
    attr=child(f,'attr') or[]
    shapes=[s for s in f if isinstance(s,list) and s and s[0].startswith('fp_')]
    courtyard=any(child(s,'layer') and 'CrtYd' in child(s,'layer')[1] for s in shapes)
    if not courtyard and 'exempt_from_courtyard_requirement' not in attr:missing.append(ref)
    types={p[2] for p in children(f,'pad')}
    if ('smd' in attr and 'thru_hole' in types) or ('through_hole' in attr and 'smd' in types):
        mixed.append({'ref':ref,'attributes':attr,'pad_types':sorted(types)})
rs=[]
for f in [ROOT/'reports'/'erc-final.json',ROOT/'reports'/'drc-final.json',ROOT/'evidence'/'erc-after-schematic-readability.json',ROOT/'reports'/'drc-initial.json',ROOT/'reports'/'drc-placement.json',ROOT/'reports'/'drc-upper-power.json']:
    v=json.loads(f.read_text(encoding='utf-8'))
    items=v.get('violations',[])+v.get('unconnected_items',[])+v.get('schematic_parity',[])+[a for s in v.get('sheets',[]) for a in s.get('violations',[])]
    rs.append({'path':f.relative_to(ROOT).as_posix(),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'date':v.get('date'),'kicad_version':v.get('kicad_version'),'counts_by_type':dict(collections.Counter(i['type'] for i in items)),'counts_by_severity':dict(collections.Counter(i['severity'] for i in items)),'ignored_checks':[i['key'] for i in v.get('ignored_checks',[])]})
report={'metadata':{'rev_a_engineering_prototype':True,'rev_b_production':False},'status':'Independent read-only configuration review; report hashes identify snapshots and do not imply hardware qualification',
        'source_files':{f.relative_to(ROOT).as_posix():hashlib.sha256(f.read_bytes()).hexdigest() for f in [pro,dru,pcb]},
        'drc_rule_severities':d['board']['design_settings']['rule_severities'],
        'drc_exclusions':d['board']['design_settings'].get('drc_exclusions',[]),
        'board_rules':d['board']['design_settings']['rules'],'erc_settings':d.get('erc',{}),
        'netclasses':d['net_settings']['classes'],
        'same_package_clearance_rule_count':dru.read_text().count('(rule '),
        'native_footprints_without_courtyard_screen':missing,
        'native_footprint_mixed_type_screen':mixed,
        'screen_limitation':'Simple attribute/presence screen does not check polygon courtyard validity or implement the native DRC type checker.',
        'reports':rs,
        'process_manifests':{p.name:json.loads(p.read_text()) for p in [ROOT/'reports'/'native-checks-both.json',ROOT/'reports'/'native-checks-drc.json'] if p.exists()},
        'upstream_default_sources':['https://raw.githubusercontent.com/KiCad/kicad/10.0/pcbnew/board_design_settings.cpp','https://raw.githubusercontent.com/KiCad/kicad/10.0/eeschema/erc/erc_settings.cpp']}
(ROOT/'evidence'/'reviewed-rule-configuration.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
# Keep the compact report index synchronized with the same current bytes.
# Historical reports have distinct paths; the replaceable *-final paths must
# never retain an earlier report hash or its ignored-check configuration.
snapshots=[{'path':r['path'],'date':r['date'],'sha256':r['sha256'],
            'version':r['kicad_version'],'count':sum(r['counts_by_type'].values()),
            'by_type':r['counts_by_type'],'by_severity':r['counts_by_severity'],
            'ignored':r['ignored_checks']} for r in rs]
(ROOT/'evidence'/'rule-review-report-snapshot.json').write_text(json.dumps(snapshots,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'rules':report['same_package_clearance_rule_count'],'missingcourtyard':missing,'mixedtype':mixed,'erc':report['erc_settings']},indent=2))
