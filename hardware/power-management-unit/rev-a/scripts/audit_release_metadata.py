"""Read-only release-flag coverage audit; preserve native and keyed schemas."""
from pathlib import Path
import argparse
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
FLAGS = {'rev_a_engineering_prototype': True, 'rev_b_production': False}
KEYED_SCHEMAS = {
    'design/placement-busbar.json': 'Reference-to-placement mapping consumed by PCB builders',
    'design/placement-chopper.json': 'Reference-to-placement mapping consumed by PCB builders',
    'design/placement-wake.json': 'Reference-to-placement mapping consumed by PCB builders',
    'reports/connection-diagnostics.json': 'Net-keyed connection diagnostics',
}
ARRAY_SCHEMAS = {
    'reports/board-pad-geometry.json': 'Native footprint/pad geometry array',
    'manufacturing/source-pad-geometry.json': 'Frozen native footprint/pad geometry array',
    'evidence/filled-power-polygons.json': 'Filled polygon array used by rendering tools',
    'evidence/rule-review-report-snapshot.json': 'Report-hash snapshot array',
}


def flagged(value):
    return isinstance(value, dict) and all(value.get(k) is v for k,v in FLAGS.items())


def metadata_errors(value, path=''):
    found=[]
    if isinstance(value,dict):
        for key,item in value.items():
            if key=='metadata' and isinstance(item,dict) and not flagged(item):
                found.append(path+'/metadata')
            found.extend(metadata_errors(item,path+'/'+str(key)))
    elif isinstance(value,list):
        for i,item in enumerate(value):
            found.extend(metadata_errors(item,path+'/'+str(i)))
    return found


def classify(relative, value):
    if '/upstream-source/' in relative:
        return 'inherited', 'Upstream tool/source provenance, preserved as supplied'
    if isinstance(value,dict) and '$schema' in value:
        return 'inherited', 'Native schema-constrained report'
    if relative.endswith('-statistics.json'):
        return 'inherited', 'Native autorouter statistics schema'
    if relative.endswith('/freerouting.json'):
        return 'inherited', 'Autorouter configuration schema'
    if relative.startswith('scripts/routing/runs/') and relative.endswith('/geometry.json'):
        return 'inherited', 'Native pad/track geometry debug snapshot consumed by routing tools'
    if relative in KEYED_SCHEMAS:
        return 'inherited', KEYED_SCHEMAS[relative]
    if relative in ARRAY_SCHEMAS:
        return 'inherited', ARRAY_SCHEMAS[relative]
    if flagged(value):
        return 'explicit', 'Top-level release flags'
    if isinstance(value,dict) and flagged(value.get('metadata')):
        return 'explicit', 'Release flags in metadata'
    if isinstance(value,list) and value and all(flagged(item) for item in value):
        return 'explicit', 'Release flags on every authored manifest entry'
    return 'missing', 'Authored object lacks release flags and is not a declared schema exception'


def audit(root=ROOT):
    rows=[];errors=[]
    for path in sorted(root.rglob('*.json')):
        relative=path.relative_to(root).as_posix()
        # The generated coverage report is not an input to its own snapshot.
        if relative=='evidence/release-metadata-scope.json':
            continue
        try:
            value=json.loads(path.read_text(encoding='utf-8-sig'))
        except (ValueError,UnicodeError) as exc:
            errors.append({'path':relative,'error':str(exc)})
            continue
        status,reason=classify(relative,value)
        if status!='inherited':
            errors.extend({'path':relative,'error':'Missing flags at '+p}
                          for p in metadata_errors(value))
        if status=='missing':
            errors.append({'path':relative,'error':reason})
        rows.append({'path':relative,'coverage':status,'reason':reason,
                     'release_scope':'release.json',
                     'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    release=json.loads((root/'release.json').read_text(encoding='utf-8-sig'))
    if not flagged(release):
        errors.append({'path':'release.json','error':'Release authority must carry the two expected flags'})
    return {'metadata':FLAGS,'authority':'release.json',
            'scope':'All JSON artifacts under rev-a; native tool, upstream, array and keyed schemas inherit release scope without changing their payload.',
            'non_json_scope':'KiCad native CAD/project files, Gerber/drill, CSV, SVG/PNG and manufacturer PDFs retain their own formats and inherit project release status; manufacturer documents are evidence, not project production approvals.',
            'files':rows,'errors':errors,'passed':not errors,
            'counts':{name:sum(r['coverage']==name for r in rows) for name in ['explicit','inherited','missing']}}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report=audit(args.root)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'passed':report['passed'],'counts':report['counts'],'errors':report['errors']},indent=2))
    raise SystemExit(not report['passed'])


if __name__=='__main__':
    main()
