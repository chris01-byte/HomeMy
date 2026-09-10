"""Independent source/XML/physical-pad/BOM parity audit; never saves a PCB.

Use KiCad Python via run_tool.py. This checks named electrical connections and
part identities, not copper continuity, ERC, DRC or manufacturer correctness.
The two documented supply aliases and explicit NC conversion are independently
implemented here rather than importing any CAD-generation logic.
"""
import argparse
from collections import Counter, defaultdict
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import traceback
import xml.etree.ElementTree as ET
import pcbnew as pcb

ROOT = Path(__file__).resolve().parents[1]
ALIASES = {'+3V3':'V3V3', '+5V':'V5V'}
SOURCES = ['power-parts.json','wake-io-parts.json','chopper-parts.json','integration-parts.json']


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def force_exit(code):
    sys.stdout.flush()
    sys.stderr.flush()
    if os.name == 'nt':
        kernel=ctypes.windll.kernel32
        kernel.GetCurrentProcess.restype=ctypes.c_void_p
        kernel.TerminateProcess.argtypes=[ctypes.c_void_p,ctypes.c_uint]
        kernel.TerminateProcess(kernel.GetCurrentProcess(),code)
    raise SystemExit(code)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--netlist',type=Path,default=ROOT/'evidence/netlist-after-schematic-readability.xml')
    ap.add_argument('--board',type=Path,default=ROOT/'kicad/HomeMy_PMU_RevA.kicad_pcb')
    ap.add_argument('--output',type=Path,default=ROOT/'reports/electrical-parity-audit.json')
    ap.add_argument('--allow-unnamed-nc',action='store_true',
        help='Interim graph audit only: permit net-zero NC pads before sync_nc_nets is applied')
    args=ap.parse_args()
    hashes,errors,observations={},{},[]

    def issue(category,message):
        errors.setdefault(category,[]).append(message)

    def snapshot(path):
        path=path.resolve()
        hashes[path]=sha(path)
        return path

    def read(path):
        return json.loads(snapshot(path).read_text(encoding='utf-8-sig'))

    def metadata(doc,label):
        md=doc.get('metadata',doc)
        if md.get('rev_a_engineering_prototype') is not True or md.get('rev_b_production') is not False:
            issue('metadata',label+': expected Rev A true / Rev B false')

    source={}
    for filename in SOURCES:
        doc=read(ROOT/'design'/filename)
        metadata(doc,filename)
        for raw in doc['components']:
            c=dict(raw)
            ref=c['ref']
            if ref in source:
                issue('source_to_assembled','Duplicate source reference '+ref)
            c['dnp']=bool(c.get('dnp')) or str(c.get('population','')).upper()=='DNP'
            c['pins']={str(p):ALIASES.get(n,n) for p,n in c['pins'].items()}
            for p,n in c['pins'].items():
                if c.get('pin_types',{}).get(p)=='no_connect' and str(n).startswith('NC_'):
                    c['pins'][p]=None
            source[ref]=c
    assembled_doc=read(ROOT/'design/assembled-parts.json')
    metadata(assembled_doc,'assembled parts')
    assembled={c['ref']:c for c in assembled_doc['components']}
    if len(assembled)!=len(assembled_doc['components']):
        issue('source_to_assembled','Duplicate assembled reference')
    if set(source)!=set(assembled):
        issue('source_to_assembled','Reference-set mismatch: '+str(sorted(set(source)^set(assembled))))
    for ref,c in source.items():
        actual=assembled.get(ref,{})
        for key in ('mpn','value','footprint','pins','dnp','pin_names','pin_types'):
            if c.get(key)!=actual.get(key):
                issue('source_to_assembled',f'{ref}: {key} differs')
        for key in ('on_board','in_bom'):
            if c.get(key,True)!=actual.get(key,True):
                issue('source_to_assembled',f'{ref}: {key} differs')
    tree=ET.parse(snapshot(args.netlist)).getroot()
    xml_components={c.get('ref'):c for c in tree.findall('./components/comp')}
    virtual={ref for ref,c in source.items() if not c.get('on_board',True) and ref.startswith('#PWR')}
    expected_xml=set(source)-virtual
    if set(xml_components)!=expected_xml:
        issue('source_to_xml','Component references differ: '+str(sorted(set(xml_components)^expected_xml)))
    xml_nodes={}
    net_members=defaultdict(set)
    for net in tree.findall('./nets/net'):
        for node in net.findall('node'):
            key=(node.get('ref'),node.get('pin'))
            if key in xml_nodes:
                issue('source_to_xml',f'{key}: XML pin appears more than once')
            xml_nodes[key]=(net.get('name'),node.get('pintype',''))
            net_members[net.get('name')].add(key)
    intentional_nc=[]
    pin_types=Counter()
    for ref in sorted(expected_xml):
        c=source[ref]
        comp=xml_components.get(ref)
        if comp is None:
            continue
        properties={p.get('name'):p.get('value') for p in comp.findall('property')}
        for source_key,xml_value in [('mpn',properties.get('MPN','')),('value',comp.findtext('value','')),('footprint',comp.findtext('footprint',''))]:
            if (c.get(source_key) or '')!=xml_value:
                issue('source_to_xml',f'{ref}: {source_key} differs')
        if ('dnp' in properties)!=c['dnp']:
            issue('source_to_xml',f'{ref}: DNP differs')
        if properties.get('rev_a_engineering_prototype')!='true' or properties.get('rev_b_production')!='false':
            issue('metadata',f'{ref}: XML part metadata differs')
        actual_pins={p.get('num') for p in comp.findall('./units/unit/pins/pin')}
        if actual_pins!=set(c['pins']):
            issue('source_to_xml',f'{ref}: physical symbol pin numbers differ')
        for pin,expected in c['pins'].items():
            actual,kind=xml_nodes.get((ref,pin),(None,''))
            expected_kind=c.get('pin_types',{}).get(pin,'passive')
            if expected is None:
                valid=(actual is not None and actual.startswith('unconnected-') and
                       len(net_members[actual])==1 and 'no_connect' in kind)
                if not valid:
                    issue('source_to_xml',f'{ref}.{pin}: intentional NC is not a marked singleton ({actual!r}, {kind!r})')
                intentional_nc.append(ref+'.'+pin)
            elif actual!=expected:
                issue('source_to_xml',f'{ref}.{pin}: {actual!r} != {expected!r}')
            base_kind=kind.split('+')[0]
            pin_types[base_kind]+=1
            if base_kind!=expected_kind:
                issue('source_to_xml',f'{ref}.{pin}: electrical type {kind!r} != {expected_kind!r}')
    expected_nodes={(ref,p) for ref in expected_xml for p in source[ref]['pins']}
    if set(xml_nodes)!=expected_nodes:
        issue('source_to_xml','XML net-node set differs: '+str(sorted(set(xml_nodes)^expected_nodes)))
    board_path=snapshot(args.board)
    board=pcb.LoadBoard(str(board_path))
    fps={}
    for fp in board.GetFootprints():
        ref=fp.GetReference()
        if ref in fps:
            issue('source_to_board','Duplicate native footprint '+ref)
        fps[ref]=fp
    expected_board={ref for ref,c in source.items() if c.get('on_board',True)}
    mechanical_only={ref for ref in fps if re.fullmatch(r'H[1-4]',ref)}
    if set(fps)-mechanical_only!=expected_board:
        issue('source_to_board','Native footprint set differs: '+str(sorted((set(fps)-mechanical_only)^expected_board)))
    physical_pad_instances=0
    non_electrical_mounting_pads=[]
    for ref in sorted(expected_board):
        c=source[ref]
        fp=fps.get(ref)
        if fp is None:
            continue
        for label,expected,actual in [('footprint',c['footprint'],fp.GetFPIDAsString()),
                                      ('value',c['value'],fp.GetValue()),('DNP',c['dnp'],bool(fp.IsDNP()))]:
            if expected!=actual:
                issue('source_to_board',f'{ref}: {label} differs ({actual!r} != {expected!r})')
        pads=defaultdict(list)
        for pad in fp.Pads():
            physical_pad_instances+=1
            if ref in ('J16','J17') and pad.GetNumber()=='MP' and c['mpn']=='BM04B-GHS-TBT(LF)(SN)':
                if pad.GetNetname():
                    issue('source_to_board',f'{ref}.MP: mechanical mounting pad unexpectedly has an electrical net')
                non_electrical_mounting_pads.append(dict(ref=ref,pad='MP',net=pad.GetNetname(),
                    reason='JST GH footprint mounting tabs; four numbered signal contacts are checked separately'))
                continue
            if not pad.GetNumber():
                if pad.GetNetname():
                    issue('source_to_board',f'{ref}: unnumbered mechanical pad has a net')
                continue
            pads[pad.GetNumber()].append(pad.GetNetname())
        if set(pads)!=set(c['pins']):
            issue('source_to_board',f'{ref}: physical pad-number set differs ({sorted(set(pads)^set(c["pins"]))})')
        for pin,nets in pads.items():
            expected=c['pins'].get(pin)
            for actual in nets:
                if expected is None:
                    xml_nc=xml_nodes.get((ref,pin),(None,''))[0]
                    if actual!=xml_nc and not (args.allow_unnamed_nc and not actual):
                        issue('source_to_board',f'{ref}.{pin}: NC pad identity {actual!r} != authoritative XML {xml_nc!r}')
                elif actual!=expected:
                    issue('source_to_board',f'{ref}.{pin}: pad net {actual!r} != {expected!r}')
        if bool(fp.IsExcludedFromBOM())!=(not c.get('in_bom',True)):
            issue('source_to_board',f'{ref}: native BOM exclusion differs')
    bom=read(ROOT/'manufacturing/REV_A_BOM.json')
    ext=read(ROOT/'manufacturing/REV_A_EXTERNAL_BOM.json')
    bm=read(ROOT/'manufacturing/REV_A_BOM_MANIFEST.json')
    for label,doc in [('PCB BOM',bom),('external BOM',ext),('BOM manifest',bm)]:
        metadata(doc,label)
        if not doc['metadata'].get('validation_passed'):
            issue('bom',label+' builder validation has not passed')
    for item in bm['inputs']:
        path=ROOT/Path(item['path'].replace('\\','/'))
        if sha(snapshot(path))!=item['sha256']:
            issue('bom','Stale BOM input '+item['path'])
    for item in bm['outputs']:
        path=ROOT/'manufacturing'/item['path']
        if sha(snapshot(path))!=item['sha256']:
            issue('bom','BOM output hash mismatch '+item['path'])
    purchased={ref for ref,c in source.items() if c.get('in_bom',True) and c.get('on_board',True)}
    records={c['ref']:c for c in bom['components']}
    if set(records)!=purchased:
        issue('bom','Purchased-reference set differs: '+str(sorted(set(records)^purchased)))
    for ref in purchased & set(records):
        c,r=source[ref],records[ref]
        for field in ('mpn','footprint','dnp'):
            if c[field]!=r[field]:
                issue('bom',f'{ref}: BOM {field} differs')
        if not r.get('manufacturer') or not r.get('mpn'):
            issue('bom',f'{ref}: empty purchased manufacturer/MPN')
    bom_dnps={ref for ref,r in records.items() if r['dnp']}
    if bom_dnps!={'C244','J13','R243','R244'}:
        issue('bom','Unexpected default DNP set '+str(sorted(bom_dnps)))
    required_quantity=sum(row['quantity_required'] for row in bom['lines'])
    if required_quantity!=len(purchased-bom_dnps):
        issue('bom','Grouped required quantity differs from populated positions')
    catalog=read(ROOT/'manufacturing/MECHANICAL_CATALOG_BOM.json')
    interface=read(ROOT/'manufacturing/busbar-pcb-interface.json')
    catalog_quantity={x['mpn']:x['quantity'] for x in catalog['items']}
    external_quantity={x['mpn']:x['quantity_required'] for x in ext['lines'] if x['mpn'] in catalog_quantity}
    if catalog_quantity!=external_quantity:
        issue('bom','Mechanical catalogue purchase quantities differ')
    custom_refs={x['references'][0] for x in ext['lines'] if x['selection_status']=='custom_manufactured_to_project_drawing'}
    expected_custom={f'BB{i}' for i in range(1,8)}|{'NB1..NB8','EXT_CONTACT_SHIMS','EXT_BRANCH_BACKING_WASHERS'}
    if custom_refs!=expected_custom:
        issue('bom','Custom mechanical row references differ')
    bc={x['ref'] for x in interface['new_pcb_contacts']}
    if bc & purchased or bc!={f'BC{i}' for i in range(1,16)}:
        issue('bom','Bare BC contacts missing or wrongly purchased')
    for row in bom['lines']+ext['lines']:
        if row.get('supplier_stock_verified') is not False:
            issue('bom','Unexpected supplier-stock verification claim')
    requirements_path=snapshot(ROOT.parent/'requirements.yaml')
    trace_path=snapshot(ROOT.parent/'REQUIREMENTS_TRACEABILITY.md')
    requirement_text=requirements_path.read_text(encoding='utf-8')
    requirement_ids=set(re.findall(r'^\s{2}([A-Z]+-\d{3}):',requirement_text,re.M))
    requirement_statuses=dict(re.findall(r'^\s{2}([A-Z]+-\d{3}):\s*\n\s{4}status:\s*(\w+)',requirement_text,re.M))
    trace=trace_path.read_text(encoding='utf-8')
    missing_ids=sorted(x for x in requirement_ids if not re.search(r'\|\s*'+re.escape(x)+r'\s*\|',trace))
    if missing_ids:
        issue('traceability','Numbered requirement rows missing: '+str(missing_ids))
    for ref,status in requirement_statuses.items():
        row=re.search(r'^\|\s*'+re.escape(ref)+r'\s*\|\s*(\w+)\s*\|',trace,re.M)
        if row and row[1]!=status:
            issue('traceability',f'{ref}: requirement status {status} differs from traceability {row[1]}')
    release=read(ROOT/'release.json')
    metadata(release,'release.json')
    observations.extend([
        'Native XML omits nine ERC-only power flags; their source/assembled parity is checked independently.',
        f'{len(intentional_nc)} intentional NC pins remain separate marked singleton XML nets; physical NC names are checked unless the explicit interim --allow-unnamed-nc option is used.',
        'Same-number physical pads are checked individually against their one source pin; no blanket passive-pin conversion is used.',
        'This report checks identities and assigned net names, not copper continuity, clearance, gate/SOA guarantees, or safety-function behavior.',
        'release.json remains a separate project disposition. Hardware testing, ordering and production release are not established by this audit.'
    ])
    for path,initial in hashes.items():
        if not path.exists() or sha(path)!=initial:
            issue('snapshot','Input changed during audit: '+str(path))
    report=dict(metadata=dict(rev_a_engineering_prototype=True,rev_b_production=False,
        state='engineering_parity_review_not_order_release',checked_at_utc=datetime.now(timezone.utc).isoformat(),
        parity_passed=not errors,exact_nc_identity_required=not args.allow_unnamed_nc,
        erc_or_drc_claim=False,pcb_written=False),
        counts=dict(source_components=len(source),assembled_components=len(assembled),xml_components=len(xml_components),
            omitted_virtual_power_flags=len(virtual),xml_pin_nodes=len(xml_nodes),intentional_nc_pins=len(intentional_nc),
            connected_named_nets=len({n for c in source.values() for n in c['pins'].values() if n is not None}),
            native_footprints=len(fps),mechanical_mounting_holes=len(mechanical_only),physical_pad_instances=physical_pad_instances,
            purchased_pcb_positions=len(purchased),populated_pcb_positions=required_quantity,external_bom_rows=len(ext['lines']),
            numbered_requirements=len(requirement_ids)),
        dnp_references=sorted(bom_dnps),electrical_pin_types=dict(pin_types),mechanical_catalog_quantities=catalog_quantity,
        non_electrical_mounting_pad_exclusions=non_electrical_mounting_pads,
        intentional_nc_pins=intentional_nc,source_release=release,errors=errors,observations=observations,
        auditor=dict(path='scripts/audit_electrical_parity.py',sha256=sha(Path(__file__)),kicad_version=pcb.GetBuildVersion()),
        inputs=[dict(path=os.path.relpath(path,ROOT).replace('\\','/'),sha256=value) for path,value in sorted(hashes.items(),key=lambda x:str(x[0]))])
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(report['counts']))
    print('Parity errors:',sum(len(x) for x in errors.values()))
    for category,messages in errors.items():
        for message in messages:
            print(category+': '+message)
    print('No PCB saved; no ERC/DRC assertion.')
    return 2 if errors else 0


if __name__=='__main__':
    try:
        code=main()
    except BaseException:
        traceback.print_exc()
        force_exit(1)
    force_exit(code)
