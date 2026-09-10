"""Bind final CAD, BOM, manufacturing and review reports to one unchanged PCB.

This is an artifact-consistency audit. It retains native process failures and
does not establish an order, thermal, physical-test or production release.
"""
from datetime import datetime, timezone
import hashlib
import json
import zipfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    errors=[];files={};verified=[]
    def require(condition,message):
        if not condition:errors.append(message)
    def read(name):
        path=ROOT/name;files[name]=sha(path)
        return json.loads(path.read_text(encoding='utf-8'))
    def check_hash(path,expected,context):
        path=Path(path)
        match=path.is_file() and sha(path)==expected
        require(match,context+': stale or missing '+str(path))
        verified.append(dict(path=str(path.relative_to(ROOT)),context=context,matches=match))
    def entries(rows,base,context):
        for row in rows:check_hash(base/row['path'],row['sha256'],context)

    board=ROOT/'kicad/HomeMy_PMU_RevA.kicad_pcb';board_sha=sha(board)
    release=read('release.json')
    require(release['rev_a_engineering_prototype'] and not release['rev_b_production'],'Incorrect revision flags')
    require(release['schematic_complete'] and release['pcb_routed'],'CAD completion not recorded')
    require(not release['hardware_tests_performed'] and not release.get('production_release') and not release['rev_b_production'],
            'Prototype package must not claim physical/production qualification')
    require(release['fabrication_release'] and release['assembly_release'] and release['prototype_package_version']=='RevA-P1',
            'Missing explicitly scoped prototype PCB release')

    native=read('reports/native-checks-both.json')
    for name,expected in native['input_hashes_sha256'].items():check_hash(ROOT/name,expected,'native check input')
    require(not native['changed_inputs'],'Native check inputs changed')
    require(set(native['checks'])=={'erc','drc'},'Missing native ERC or DRC')
    require(native['all_processes_passed'] and native['reports_have_zero_findings'],'Native processes/reports did not both pass')
    require('--schematic-parity' in native['checks']['drc']['command'],'Full schematic parity was not requested')
    for name,row in native['checks'].items():
        require(row['report_complete'] and row['report_has_zero_findings'],name+' report is incomplete or has findings')
        require(row['process_exit_code']==0,name+' did not exit normally with zero')
        check_hash(ROOT/row['report_path'],row['report_sha256'],name+' native report')

    parity=read('reports/electrical-parity-audit.json')
    require(parity['metadata']['parity_passed'] and parity['metadata']['exact_nc_identity_required'],'Strict electrical parity did not pass')
    require(not parity['errors'],'Electrical parity errors remain')
    entries(parity['inputs'],ROOT,'electrical parity input')
    bom=read('manufacturing/REV_A_BOM_MANIFEST.json')
    require(bom['metadata']['validation_passed'] and not bom['metadata']['errors'],'BOM validation failed')
    entries(bom['inputs'],ROOT,'BOM input');entries(bom['outputs'],ROOT/'manufacturing','BOM output')
    package_dir=Path(release['manufacturing_package']).parent
    export=read((package_dir/'EXPORT_MANIFEST.json').as_posix())
    require(export['metadata']['coverage_validation_passed'] and not export['metadata']['errors'],'Manufacturing file coverage failed')
    require(export['board_state']['unconnected_ratsnest_edges']==0,'Exported PCB has open connections')
    require(export['board_state']['source_release']==release,'Export carries stale release disposition')
    entries(export['inputs'],ROOT,'manufacturing input')
    entries(export['outputs'],ROOT/package_dir,'manufacturing output')
    check_hash(ROOT/export['exporter']['path'],export['exporter']['sha256'],'manufacturing exporter')

    critical=read('reports/critical-routing-geometry.json')
    require(critical['board']['sha256']==board_sha,'Critical route review uses another board')
    require(not critical['missing_explicit_paths'] and not critical['locked_analog_copper_check']['errors'],'Critical routing review has findings')
    power=read('evidence/filled-power-copper-review.json')
    require(power['board_sha256']==board_sha and power['board_unchanged_during_review'],'Power review uses another board')
    require(all(x['same_continuous_copper_outline'] for x in power['same_layer_path_checks']),'Sampled power endpoints are disconnected')
    require(power['chopper_drain_copper']['target_geometrically_met'],'Chopper connected drain area misses design target')
    placement=read('evidence/placement-access-review.json')
    require(placement['source']['final_pcb_sha256']==board_sha and placement['source']['read_only_hash_stable'],'Placement review uses another board')
    require(not placement['critical_findings'],'Placement has critical findings')
    # The old annotation application receipt is historical. The current read-only
    # orientation check verifies the labels against the PCB after power-fill edits.
    assembly=read('manufacturing/assembly-orientation.json')
    require(assembly['input_board_sha256']==board_sha and assembly['board_unchanged'] and
            not assembly['required_graphical_improvements'] and all(x['passed'] for x in assembly['graphical_checks']),
            'Current assembly orientation/annotations failed')
    rendered=read('reports/rendered-review-manifest.json')
    require(rendered['board_sha256']==board_sha,'Rendered review identifies another PCB')
    for row in rendered['outputs']:
        check_hash(ROOT/row['source'],row['source_sha256'],'rendered source')
        check_hash(ROOT/row['target'],row['target_sha256'],'rendered image')
    rules=read('evidence/reviewed-rule-configuration.json')
    require(not rules['drc_exclusions'],'Item-level DRC exclusions are present')
    snapshots=read('evidence/rule-review-report-snapshot.json')
    for row in snapshots:check_hash(ROOT/row['path'],row['sha256'],'reviewed rule/report snapshot')
    high=read('evidence/high-current-audit.json')
    require(high['passed'] and high['power_endpoint_checks']>=247 and high['reviewed_tap_items']==492,'Power geometry review failed')
    for name,expected in high['inputs_sha256'].items():check_hash(ROOT/name,expected,'high-current evidence')
    package=read(release['manufacturing_package'])
    require(package['metadata']['fabrication_release'] and not package['metadata']['production_release'],'Wrong package release scope')
    require(package['board_sha256']==board_sha,'Package uses another PCB')
    entries(package['files'],ROOT/package_dir,'prototype delivery')
    for name,expected in package['source_inputs_sha256'].items():check_hash(ROOT/name,expected,'prototype delivery source')
    require(package['counts']['pressfit_holes']==48 and package['counts']['open_external_before_pcb_order']==0 and
            package['counts']['open_external_before_energization']==9,'Press-fit/open-order accounting differs')
    archive=(ROOT/package_dir).with_suffix('.zip')
    expected_zip=archive.with_suffix('.zip.sha256').read_text().split()[0]
    check_hash(archive,expected_zip,'prototype ZIP')
    with zipfile.ZipFile(archive) as z:
        require(z.testzip() is None,'ZIP integrity failed')
        for row in package['files']:
            require(hashlib.sha256(z.read(package_dir.name+'/'+row['path'])).hexdigest()==row['sha256'],'ZIP entry differs: '+row['path'])
    check_hash(board,board_sha,'final unchanged board')

    result=dict(metadata=dict(rev_a_engineering_prototype=True,rev_b_production=False,
                checked_at_utc=datetime.now(timezone.utc).isoformat(),
                scope='Current artifact identity and recorded CAD findings; no new native DRC or physical tests',
                cad_package_checks_passed=not errors,hardware_tests_performed=False,
                fabrication_release=True,assembly_release=True,production_release=False,
                release_scope='Bare/populated Rev A-P1 PCB engineering prototype only'),
                board_sha256=board_sha,counts=parity['counts'],board_state=export['board_state'],
                native_report_findings={name:{k:row[k] for k in ['report_complete','violations','unconnected_items',
                    'schematic_parity_issues','report_has_zero_findings','process_passed','process_exit_code']}
                    for name,row in native['checks'].items()},
                native_check_processes_passed=native['all_processes_passed'],
                native_process_limitation=release['native_check_process_limitation'],
                reviewed_power_paths=len(power['same_layer_path_checks']),
                chopper_connected_drain_area_mm2=power['chopper_drain_copper']['connected_FCu_area_mm2'],
                errors=errors,verified_hashes=verified,
                inputs=[dict(path=name,sha256=value) for name,value in sorted(files.items())],
                auditor=dict(path='scripts/audit_final_package.py',sha256=sha(Path(__file__))))
    (ROOT/'evidence/FINAL_REVIEW.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f'Final package: {len(errors)} consistency/findings errors; {len(verified)} recorded hashes verified; native processes passed: {native["all_processes_passed"]}')
    for error in errors:print('ERROR:',error)
    return 2 if errors else 0


if __name__=='__main__':raise SystemExit(main())
