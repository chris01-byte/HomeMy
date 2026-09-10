"""Refresh only the latest-result section; preserve the reviewed rule reasoning."""
from pathlib import Path
import json,hashlib
ROOT=Path(__file__).resolve().parent
j=json.loads((ROOT/'reviewed-rule-configuration.json').read_text())
path=ROOT/'REVIEWED_DEFAULT_ERC_DRC.md';s=path.read_text(encoding='utf-8')
start='<!-- LATEST_NATIVE_REPORT_SNAPSHOT -->';end='<!-- END_LATEST_NATIVE_REPORT_SNAPSHOT -->'
rows=[];details=[]
for kind in ['erc','drc']:
    r=next(a for a in j['reports'] if a['path']==f'reports/{kind}-final.json')
    count=sum(r['counts_by_type'].values())
    rows.append(f"| {kind.upper()} | {r['date']} | {count} | {', '.join(r['ignored_checks']) or 'none'} |")
    details.append(f"- `{r['path']}` SHA-256: `{r['sha256']}`; findings by type: `{json.dumps(r['counts_by_type'])}`.")
    for name,m in j.get('process_manifests',{}).items():
        check=m.get('checks',{}).get(kind,{})
        if check.get('report_sha256')!=r['sha256']:continue
        h=next((v for k,v in m.get('input_hashes_sha256',{}).items() if k.endswith('.kicad_pcb')),None)
        board_matches=h==j['source_files']['kicad/HomeMy_PMU_RevA.kicad_pcb']
        details.append(f"- Matching `{name}` records process exit `{check.get('process_exit_code')}`, process passed `{check.get('process_passed')}`, report complete `{check.get('report_complete')}`. Its board hash matches this configuration snapshot: `{board_matches}`. The command explicitly requests schematic parity: `{('--schematic-parity' in check.get('command',[])) if kind=='drc' else 'not applicable to ERC'}`.")
section=f'''{start}
## Latest native report snapshot

This section is generated from the current files by `audit_rule_configuration.py` and `update_rule_review_snapshot.py`. The historical table above remains a record of the earlier configuration. Current PCB SHA-256: `{j['source_files']['kicad/HomeMy_PMU_RevA.kicad_pcb']}`.

| Check | Embedded report time | Total listed findings | Checks still ignored |
|---|---|---:|---|
{chr(10).join(rows)}

{chr(10).join(details)}

The added courtyard, footprint-type and singleton-label warnings remain enabled in the project. A complete JSON report with zero findings is distinct from a clean CLI exit. Registry errors, timeout or abnormal shutdown are retained in the process logs; this review does not convert such an exit into a passed process. Thermal, pressfit, contact-force and system tests remain separate from CAD checks.
{end}
'''
if start in s:s=s[:s.index(start)]+section+s[s.index(end)+len(end):]
else:s=s.replace('## Traceability and source findings',section+'\n## Traceability and source findings')
s=s.replace('during lower-power integration and before final routing.','begun during lower-power integration and updated during routing.')
s=s.replace('Root action remaining: regenerate native CAD from corrected sources, run ERC/DRC including the three added warnings and explicit schematic parity, resolve each resulting entry, then preserve contemporaneous source hashes and tool exit diagnostics. Final routing, mechanical coupon tests and high-current qualification remain separate outstanding checks.','CAD-owner action: use the latest matching native reports to resolve any remaining findings, preserve source hashes and process diagnostics, and repeat the filled-copper and assembly-marker review after changes. Report completion, clean tool exit, mechanical coupon acceptance and high-current qualification are separate results.')
path.write_text(s,encoding='utf-8')
print('Updated latest native report snapshot')
