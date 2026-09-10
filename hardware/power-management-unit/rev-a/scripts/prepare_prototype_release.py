"""Record a PCB-only Rev A prototype release from fresh passing evidence."""
import hashlib
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
VERSION='RevA-P1'
PACKAGE='manufacturing/HomeMy_PMU_RevA-P1_2026-09-10'


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def read(name):return json.loads((ROOT/name).read_text(encoding='utf-8'))


def main():
    n=read('reports/native-checks-both.json')
    assert n['all_processes_passed'] and n['reports_have_zero_findings'] and not n['changed_inputs']
    assert set(n['checks'])=={'erc','drc'}
    for name,expected in n['input_hashes_sha256'].items():
        assert sha(ROOT/name)==expected, 'Stale native input: '+name
    for name,row in n['checks'].items():
        assert row['process_exit_code']==0 and row['report_complete'] and row['report_has_zero_findings'],name
        assert sha(ROOT/row['report_path'])==row['report_sha256'],name+' report hash'
    assert '--schematic-parity' in n['checks']['drc']['command']
    power=read('evidence/high-current-audit.json')
    assert power['passed'] and power['power_endpoint_checks']>=247
    for name,expected in power['inputs_sha256'].items():assert sha(ROOT/name)==expected,name
    bom=read('manufacturing/REV_A_BOM_MANIFEST.json')
    assert bom['metadata']['validation_passed'] and bom['metadata']['external_open_before_pcb_order']==0
    for row in bom['inputs']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
    assembly=read('manufacturing/assembly-orientation.json')
    assert assembly['input_board_sha256']==power['board_sha256'] and not assembly['required_graphical_improvements']
    assert all(x['passed'] for x in assembly['graphical_checks'])
    release=read('release.json')
    release.update(design_state='rev_a_pcb_prototype_order_release',
        native_check_processes_passed=True,native_check_process_exit_codes={'erc':0,'drc':0},
        native_erc_report_complete=True,native_erc_report_has_zero_findings=True,
        native_drc_report_complete=True,native_drc_report_has_zero_findings=True,
        native_drc_unconnected_items=0,native_schematic_parity_issues=0,
        native_check_process_limitation=None,native_check_started_at_utc=n['started_at_utc'],
        prototype_package_version=VERSION,manufacturing_package=PACKAGE+'/PACKAGE_MANIFEST.json',
        prototype_order_review='CAD, scoped power geometry and prototype documentation checked; supplier process acceptance required',
        fabrication_release=True,assembly_release=True,production_release=False,
        fabrication_release_scope='Bare Rev A-P1 engineering prototype PCB only; not production qualification',
        assembly_release_scope='Populated Rev A-P1 PCB, DNP state and defined manual/press-fit operations only; no energization or complete-system release',
        hardware_tests_performed=False,rev_b_production=False,firmware_implemented=False,
        prototype_notice='Engineering prototype – not production qualified',
        unresolved_external_items=9,unresolved_external_before_pcb_order=0,unresolved_external_before_energization=9,
        external_integration_gates='design/external-integration-gates.json',
        high_current_review='evidence/high-current-audit.json',
        supplier_order_acceptance=['Accept specified press-fit finished holes, raw drill and plating together',
          'Accept finished 70/35/35/70 um copper and 1.60-1.70 mm thickness excluding masks',
          'Accept specified laminate/ENIG and coupon/insertion process; no silent material or footprint substitutions'],
        release_excludes=['Series production','50 A thermal qualification','Battery/actuator operation','Firmware and complete robot integration'])
    (ROOT/'release.json').write_text(json.dumps(release,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(VERSION,'PCB prototype release recorded; production and energization remain unqualified.')


if __name__=='__main__':main()
