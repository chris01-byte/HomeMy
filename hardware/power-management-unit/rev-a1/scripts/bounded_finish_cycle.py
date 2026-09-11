"""Record the hard progress gate; never alter CAD or start another cycle."""
import argparse
from collections import Counter
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from bounded_checks import ROOT, LEDGER, sha, write, minutes, input_hashes

def main(board, phase):
    path = ROOT/'results'/(board.stem+'.json'); result=json.loads(path.read_text(encoding='utf-8'))
    ledger=json.loads(LEDGER.read_text(encoding='utf-8'));cycle=ledger['cycles'][-1]
    assert cycle['status']=='in_progress'
    number=cycle['cycle']; previous='initial' if number==1 else 'cycle-'+str(number-1)
    before=result['checks'][previous]['drc']; after=result['checks'][phase]['drc']
    geometry=result['geometry'][phase]
    before_api=result.get('geometry',{}).get(previous,{}).get('native_ratsnest_connections')
    after_api=geometry.get('native_ratsnest_connections')
    before_open=before_api if before_api is not None else before['open_connections']
    after_open=after_api if after_api is not None else after['open_connections']
    before_is_lower_bound=before_api is None and before['open_connections']>=499
    def errors(v):return sum(r['count'] for r in v['counts'] if r['severity']=='error')
    def count(v,t):return sum(r['count'] for r in v['counts'] if r['type']==t)
    decrease=before_open-after_open
    criterion=(decrease>=10 or decrease>=.2*before_open) and errors(after)<=errors(before)
    criterion=criterion and all(count(after,t)<=count(before,t) for t in ['shorting_items','clearance']) and after['parity_findings']<=before['parity_findings']
    erc=result['checks'][phase].get('erc')
    if phase == 'cycle-1': erc=result['checks'].get('cycle-1-library-path',{}).get('erc',erc)
    current = input_hashes(board)
    for checked in (erc, after):
        assert checked and checked['report_complete'] and checked['process_normal'], 'Missing complete native evidence'
        assert checked['input_hashes_sha256'] == current, 'Native evidence is stale or covers different inputs'
    if any(r['count'] >= 199 for r in before['counts']+after['counts']) or (after_api is None and after['open_connections'] >= 499):
        criterion=False  # Censored totals cannot establish the complete progress gate.
    networks=Counter()
    for row in after['native_report']['unconnected_items']:
        names={n for item in row['items'] for n in re.findall(r'\[([^\]]+)\]',item['description'])}
        for name in names:networks[name]+=1
    assert geometry['pcb_sha256'] == sha(board), 'Geometry audit is stale'
    summary={'pcb_sha256':sha(board),'open_connections':after_open,'native_drc_reported_open_connections':after['open_connections'],'affected_nets':len(networks),'open_networks':dict(sorted(networks.items())),
        'open_network_inventory_may_be_capped':after['open_connections']>=499,
        'drc_counts':after['counts'],'drc_errors':errors(after),'drc_exit_code':after['process_exit_code'],
        'counts_may_be_capped':after.get('counts_may_be_capped',False),
        'native_ratsnest_connections':geometry.get('native_ratsnest_connections'),
        'erc_counts':erc['counts'],'erc_exit_code':erc['process_exit_code'],'schematic_parity':after['parity_findings'],
        'placement_passed':geometry['placement']['passed'],'force_pairs_passed':geometry['force']['passed_pairs'],
        'force_pairs_total':geometry['force']['total_pairs'],'compact_drive_return':geometry['force']['compact_drive_return'],
        'critical_paths':geometry.get('critical'),
        'progress':{'before_open':before_open,'after_open':after_open,'decrease':decrease,'before_open_is_lower_bound':before_is_lower_bound,'decrease_is_lower_bound':before_is_lower_bound,'before_drc_errors':errors(before),'after_drc_errors':errors(after),'criteria_met':criterion},
        'passed':False,'fabrication_release':False,'assembly_release':False,'production_release':False}
    # A complete pass additionally needs neck, via, busbar/contact and thermal
    # geometry review. Never infer those unimplemented gates from zero DRC.
    summary['remaining_geometric_qualification']='Local minimum-section and complete lower-power/busbar qualification remain explicit gates.'
    result.setdefault('cycle_summaries',{})[str(number)]=summary;write(path,result)
    cycle.update(status='completed',ended_utc=datetime.now(timezone.utc).isoformat(),output_sha256=sha(board),open_connections=after_open,drc_errors=errors(after),
                 progress_permits_next_cycle=bool(criterion and number<ledger['limits']['cycles'][cycle['size']]),
                 result='failed',progress=summary['progress'])
    ledger['elapsed_minutes_at_last_cycle']=round(minutes(ledger),3);write(LEDGER,ledger)
    print(cycle['size'],number,json.dumps(summary['progress']), 'next_cycle',cycle['progress_permits_next_cycle'],flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('board',type=Path);ap.add_argument('phase');args=ap.parse_args();main(args.board.resolve(),args.phase)
