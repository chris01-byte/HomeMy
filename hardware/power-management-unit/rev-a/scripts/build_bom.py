"""Build review BOMs from the final source records and assembled CAD record.

Python 3 standard library only. Run after build_schematic.py. The CSV/JSON
outputs are deterministic. Nonzero exit means source/CAD reconciliation or
part-identity validation failed; review files are still written with errors.
No CAD or source parts are mutated and no inventory/order request is made.
"""
from pathlib import Path
from collections import defaultdict
from urllib.parse import urlparse
import argparse
import csv
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]
DESIGN = ROOT / 'design'
STATE = 'engineering_review_not_order_release'
DATE = '2026-09-10'
READ_SNAPSHOTS = {}
MECHANICAL_COVERAGE = {}
PART_SOURCES = ['power-parts.json', 'wake-io-parts.json',
                'chopper-parts.json', 'integration-parts.json']
E96 = set('100 102 105 107 110 113 115 118 121 124 127 130 133 137 140 143 '
          '147 150 154 158 162 165 169 174 178 182 187 191 196 200 205 210 '
          '215 221 226 232 237 243 249 255 261 267 274 280 287 294 301 309 '
          '316 324 332 340 348 357 365 374 383 392 402 412 422 432 442 453 '
          '464 475 487 499 511 523 536 549 562 576 590 604 619 634 649 665 '
          '681 698 715 732 750 768 787 806 825 845 866 887 909 931 953 976'.split())
E24 = set('100 110 120 130 150 160 180 200 220 240 270 300 330 360 390 430 '
          '470 510 560 620 680 750 820 910'.split())
EXACT_RESISTOR_CATALOG_EVIDENCE = {
    'RT0805BRD0739K7L': 'https://www.ti.com/jp/lit/pdf/tidrpf6',
    'RT0805BRD0710K1L': 'https://e2e.ti.com/cfs-file/__key/communityserver-discussions-components-files/196/WBDesign417.pdf',
}


def natural(s):
    return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', s)]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    raw=path.read_bytes()
    READ_SNAPSHOTS[path.resolve()]=hashlib.sha256(raw).hexdigest()
    return json.loads(raw.decode('utf-8-sig'))


def dnp(c):
    return bool(c.get('dnp')) or str(c.get('population', '')).upper() == 'DNP'


def pcb_feature(c):
    ref = c['ref']
    return (not c.get('in_bom', True) or ref.startswith('#PWR') or
            (ref.startswith('TP') and c.get('footprint', '').startswith('TestPoint:')) or
            (ref.startswith('NT') and 'NetTie' in c.get('footprint', '')))


def manufacturer(c):
    mpn, url = c.get('mpn', ''), c.get('source_url', '').lower()
    if mpn.startswith('C3216'):
        return 'TDK'
    if mpn.startswith(('C0805C', 'C1206C', 'C1210C')):
        return 'KEMET (YAGEO Group)'
    for token, name in [('ti.com', 'Texas Instruments'), ('analog.com', 'Analog Devices'),
                        ('espressif.com', 'Espressif Systems'), ('nexperia.com', 'Nexperia'),
                        ('infineon.com', 'Infineon Technologies'), ('vishay.com', 'Vishay'),
                        ('murata.com', 'Murata Manufacturing'), ('yageo.com', 'YAGEO'),
                        ('bourns.com', 'Bourns'), ('wima.de', 'WIMA'),
                        ('chemi-con.co.jp', 'Nippon Chemi-Con'), ('panasonic.com', 'Panasonic'),
                        ('littelfuse.com', 'Littelfuse'), ('we-online.com', 'Wurth Elektronik'),
                        ('phoenixcontact.com', 'Phoenix Contact'), ('jst-mfg.com', 'JST'),
                        ('samtec.com', 'Samtec'), ('tdk.com', 'TDK')]:
        if token in url:
            return name
    return ''


CRITICAL_RATINGS = {
 'LM74930QRGERQ1': '4..65V operating;70V absolute maximum; main gate, timer and transient limits in POWER_STAGE.md',
 'TPS48110AQDGXRQ1': '3.5..80V operating;100V absolute maximum; physical16 absent; remote temperature140..160C',
 'TPS26631RGER': '4.5..60V operating;67V absolute maximum;0.6..6A programmable; MODE floating latch-off',
 'TLV3011BIDBVR': '1.65..5.5V supply; integrated1.242V reference; open-drain; B version required',
 'PSMN1R0-100ASFJ': '100V; RDSmax0.99/1.6/2.3mOhm at25/100/175C and10Vgate; Qgmax539nC',
 'CSS4J-4026R-L500F': '0.5mOhm1%;four-terminal;10W at70C terminal;50W5s overload qualification, not arbitrary pulse rating',
 'PTVS1-043C-H': '43V standoff;48..53V breakdown;56V TYPICAL at1kA8/20us, not guaranteed maxclamp',
 'MKS4C053306D00KSSD': '33uF63V10% PET film;31.5x13x24mm;27.5mm pitch; leakage/timing assumptions in POWER_STAGE.md',
 'IPT015N10N5ATMA1': '100V N-MOS; gate/SOA/thermal limits in CHOPPER_MECHANICS.md',
 'EKYC101ELL471MK35S': '470uF100V20%;12.5mm dia35mm nominal length;5mm pitch;3.3Arms105C100kHz; pair required',
 '7461103': 'M5 press-fit160A component class;2.2Nm maximum; no soldering; qualified finished holes and insertion',
 '1776508': '2position5.08mm threaded-flange header;12A component rating; mate1777989',
 '1776511': '3position5.08mm threaded-flange header;12A component rating; mate1777992',
 'ESP32-S3-WROOM-1-N8': '3.3V;8MB quad flash;noPSRAM;PCB antenna keepout',
 'TLV1117LV33DCYR': '3.3V output;1A IC class;5.5V recommended input maximum; board thermal allowance differs',
 'TCAN1042HGVDRQ1': 'CAN;5V VCC and3.3V VIO; requires powered-off isolation as drawn',
}


def lifecycle(c):
    if c.get('lifecycle'):
        return c['lifecycle'] + ' [source-record observation]'
    m = c['mpn']
    if m in {'LM74930QRGERQ1', 'TPS48110AQDGXRQ1', 'TPS26631RGER', 'TLV3011BIDBVR',
             'TPS7A4001DGNR', 'REF5025IDR', 'LM339BIPWR', 'UCC27511DBVR', 'TPS3808G01DBVR'}:
        return 'Active/Production in reviewed manufacturer ordering evidence; recheck at order'
    if m == 'PSMN1R0-100ASFJ':
        return 'Production on manufacturer product page; recheck at order'
    if m == 'EKYC101ELL471MK35S':
        return 'In Production on manufacturer exact-part page; recheck at order'
    if m == 'IPT015N10N5ATMA1':
        return 'Active/preferred on manufacturer product page; recheck at order'
    return 'Manufacturer catalog/family evidence; exact lifecycle flag not independently established'


def evidence_index():
    result = defaultdict(list)
    paths = [ROOT/'evidence/power/sources.json', ROOT/'evidence/wake-io-sources.json',
             ROOT/'evidence/chopper/source_manifest.json', ROOT/'evidence/chopper/cross-review-sources.json']
    for path in paths:
        if not path.exists():
            continue
        raw = read(path)
        entries = raw.get('sources', []) if isinstance(raw, dict) else raw
        for e in entries:
            if not isinstance(e, dict):
                continue
            url = e.get('source_url', e.get('url', ''))
            status = e.get('status', 'source_record')
            item = dict(manifest=str(path.relative_to(ROOT)), status=status)
            if e.get('file') and status != 'failed':
                f = path.parent/e['file']
                if f.exists():
                    item.update(file=str(f.relative_to(ROOT)), sha256=digest(f))
            result[url].append(item)
    return result


def check_mpn(c, errors):
    """Validate identity fields and the actually used resistor coding families.

    This does not claim individual live stock or lifetime qualification. Exact
    source evidence is carried alongside every result, including family-only
    evidence instead of falsely claiming a per-part lookup.
    """
    mpn = c.get('mpn', '')
    if not mpn or re.search(r'TBD|UNKNOWN|PLACEHOLDER|TODO|<|>', mpn, re.I):
        errors.append(f'{c["ref"]}: missing or placeholder manufacturer part number')
        return 'identity_error'
    if not c.get('source_url', '').startswith('https://'):
        errors.append(f'{c["ref"]}: missing HTTPS manufacturer source')
    if not c.get('footprint'):
        errors.append(f'{c["ref"]}: purchased PCB part lacks exact footprint')
    if mpn in {'RT0805BRD0718K4L', 'RT0805BRD07224KL'}:
        errors.append(f'{c["ref"]}: superseded unverified resistor order code {mpn}')
    if mpn.startswith(('RC0805', 'RC1206', 'RC2010', 'RT0805')):
        match = re.fullmatch(r'(?:RC(?:0805|1206)FR-|RC2010FK-|RT0805BRD)07(\d+(?:[RKM]\d*)?)L', mpn)
        if not match:
            errors.append(f'{c["ref"]}: unrecognized YAGEO order-code grammar {mpn}')
        else:
            digits = re.sub('[RKM]', '', match[1]).lstrip('0')
            norm = (digits+'000')[:3]
            if norm not in E24 | E96 and mpn not in EXACT_RESISTOR_CATALOG_EVIDENCE:
                errors.append(f'{c["ref"]}: nonstandard resistor value requires exact catalog evidence: {mpn}')
        return ('Exact code supported by manufacturer-authored design BOM: '+EXACT_RESISTOR_CATALOG_EVIDENCE[mpn] if mpn in EXACT_RESISTOR_CATALOG_EVIDENCE
                else 'YAGEO selected-family order coding and preferred value checked; individual stock unverified')
    if mpn.startswith('TNPW'):
        if not re.fullmatch(r'TNPW(?:0805|1206)\d+[RKM]\d*[BF]EEA', mpn):
            errors.append(f'{c["ref"]}: unrecognized Vishay TNPW order-code grammar {mpn}')
        return 'Vishay family coding/range reviewed in CHOPPER_PROCUREMENT.md; individual stock unverified'
    return 'Preserved exact source-record MPN; manufacturer evidence linked; supplier stock unverified'


def external_items(source_parts, errors):
    """Selected external parts and explicitly unresolved assembly materials."""
    rows=[]
    def add(ref,mpn,mfr,qty,desc,source,constraints='',selection='exact_part_selected',dnp_value=False,unit='each'):
        rows.append(dict(references=[ref],quantity_positions=qty,
            quantity_required=0 if dnp_value else qty,unit=unit,mpn=mpn,
            manufacturer=mfr,description=desc,dnp=dnp_value,selection_status=selection,
            source_url=source,constraints=constraints,
            lifecycle=('Catalog/source evidence; verify exact lifecycle at ordering' if mpn else 'Not applicable until manufacturer part selected'),
            supplier_stock_verified=False,stock_status='unverified_at_build',state=STATE))
    rh='https://www.vishay.com/docs/30201/rhnh.pdf'
    ntc='https://www.vishay.com/docs/29049/ntcle100.pdf'
    gh='https://www.jst-mfg.com/product/pdf/eng/eGH.pdf'
    add('EXT_RBANK','RH10010R00FE01','Vishay',2,'10ohm100W1% aluminum-housed resistor',rh,
        'Two in parallel. Each on separate305x305x3.2mm aluminum panel for prototype.500J bank initialtest, coldstart and repetition constraints apply.')
    add('EXT_NTC','NTCLE100E3103GB0','Vishay',2,'10kohm2% external NTCs',ntc,
        'Independent analog and telemetry sensors on resistor assembly; do not combine their circuits.')
    headers=[c for c in source_parts if c.get('mpn')=='1776508']
    for optional in [False,True]:
        n=sum(dnp(c)==optional for c in headers)
        if n:
            add('EXT_MATE_2P_DNP' if optional else 'EXT_MATE_2P','1777989','Phoenix Contact',n,
                'MSTB2.5/2-STF-5.08 screw-flanged mating plug',
                'https://www.phoenixcontact.com/en-dk/products/pcb-connector-mstb-25-2-stf-508-1777989',
                'Mechanically code distinct voltage/input/output branches; no live-mating interrupt rating credited.',dnp_value=optional)
    add('EXT_MATE_LED','1777992','Phoenix Contact',1,'3position5.08mm flanged mating plug forJ18',
        'https://www.phoenixcontact.com/en-us/products/pcb-connector-mstb-25-3-stf-508-1777992',
        '1mm2 power/return;0.25mm2 data;5A LED branch envelope.')
    jst_count=sum(c.get('mpn')=='BM04B-GHS-TBT(LF)(SN)' and not dnp(c) for c in source_parts)
    add('EXT_CAN_HOUSING','GHR-04V-S','JST',jst_count,'4position GH cable housing',gh)
    add('EXT_CAN_CONTACT','SSHL-002T-P0.2','JST',4*jst_count,'GH female crimp contact',gh,
        '0.14..0.2mm2 wire range; compatible qualified crimp tooling required; quantity excludes assembly spares.')
    local='design/CHOPPER_MECHANICS.md'
    add('EXT_AL_PANELS',None,None,2,'Aluminum heat-spreader panel305x305x3.2mm',local,
        'Material grade, mounting holes, insulation/guards and fasteners need released assembly drawing.',selection='raw_stock_specification_only')
    mechanical_path=ROOT/'manufacturing/MECHANICAL_CATALOG_BOM.json'
    interface_path=ROOT/'manufacturing/busbar-pcb-interface.json'
    if mechanical_path.exists() and interface_path.exists():
        mechanical=read(mechanical_path)
        interface=read(interface_path)
        bc_count=len(interface['new_pcb_contacts'])
        nt_count=len(interface['net_tie_modifications'])
        clamp_count=bc_count+2*nt_count
        coverage=dict(busbars=len(interface['busbars']),bare_pcb_bc_contacts=bc_count,
            top_nb_bridges=nt_count,contact_shims=interface['contact_shim']['quantity'],
            separate_cu_branch_backing_washers=nt_count,clamp_screws=clamp_count)
        MECHANICAL_COVERAGE.update(coverage)
        if coverage != dict(busbars=7,bare_pcb_bc_contacts=15,top_nb_bridges=8,
            contact_shims=23,separate_cu_branch_backing_washers=8,clamp_screws=31):
            errors.append('Mechanical interface counts differ from current31-clamp prototype BOM: '+str(coverage))
        for ref in [f'BC{i}' for i in range(1,16)]:
            candidates=[c for c in source_parts if c['ref']==ref]
            if len(candidates)!=1 or not pcb_feature(candidates[0]):
                errors.append(ref+': expected exactly one excluded bare PCB contact feature')
        catalog_qty={item['mpn']:item['quantity'] for item in mechanical['items']}
        expected_qty={'SSCF-M3-12-A2-P80':clamp_count,'HPN-M3-A2':clamp_count,
            'HDTW-M3-A4-BL':clamp_count+bc_count,'660001':3*clamp_count,'IM30-FM-000200':1}
        if catalog_qty != expected_qty:
            errors.append('Mechanical catalogue quantities differ from clamp/interface counts')
        for i,item in enumerate(mechanical['items'],1):
            add(f'EXT_MECH_CATALOG_{i}',item['mpn'],item['manufacturer'],item['quantity'],
                item['description'],item['source_url'],
                'Order code: '+str(item.get('order_code',item['mpn']))+'; '+item.get('notes','')+
                '; dimensions/acceptance: '+json.dumps(item.get('dimensions',{}),sort_keys=True)+
                '; coupon acceptance in manufacturing/MECHANICAL_CATALOG_BOM.json; stock unverified.')
        for bar in interface['busbars']:
            ref=bar.get('ref',bar.get('id','CUSTOM_BB'))
            add(ref,None,'Fabricate to HomeMy drawing',1,
                'Custom Cu-ETP underside busbar '+ref,'manufacturing/busbar-pcb-interface.json',
                'Geometry, cutouts, contact coordinates and thickness are controlled by the JSON and companion mechanical drawing; '
                'no shunt/FET bypass; coupon and first-article acceptance required. '+json.dumps(bar,sort_keys=True),
                selection='custom_manufactured_to_project_drawing')
        add('NB1..NB8',None,'Fabricate to HomeMy drawing',8,'Custom Cu-ETP20x10x2mm top star bridges',
            'manufacturing/MECHANICAL_BUILD.md','Two3.4mm holes at10mm centers; one perNT; drawing and coupon acceptance required.',
            selection='custom_manufactured_to_project_drawing')
        shim=interface['contact_shim']
        add('EXT_CONTACT_SHIMS',None,'Fabricate to HomeMy drawing',shim['quantity'],
            'Custom Cu-ETP contact shim8mmOD/3.4mmID/0.25mm thickness',
            'manufacturing/busbar-pcb-interface.json',json.dumps(shim,sort_keys=True),
            selection='custom_manufactured_to_project_drawing')
        add('EXT_BRANCH_BACKING_WASHERS',None,'Fabricate to HomeMy drawing',8,
            'Custom separate Cu branch backing washers8mmOD/3.4mmID/1mm thickness',
            'manufacturing/MECHANICAL_BUILD.md','One perNT*.1 inBB7cutouts; must remain electrically separate fromBB7.',
            selection='custom_manufactured_to_project_drawing')
        for row in rows:
            if row['selection_status']=='custom_manufactured_to_project_drawing':
                row['lifecycle']='Custom part controlled by HomeMy mechanical drawing; catalogue lifecycle not applicable'
    else:
        add('EXT_CU_BARS',None,None,1,'Copper reinforcement stock15x2mm cross-section',local,
            'One stock lot; total length/cut list unselected. Calculated segment<=100mm. Split at everyshunt, FETbank and bus boundary; never bypass protection.',selection='raw_stock_cut_list_unreleased',unit='lot')
    add('EXT_LUG_BATT',None,None,2,'M5 ring lug for6mm2 battery cable',local,
        'Exact lug insulation/material/crimp system unselected; tightening<=2.2Nm and cable restraint required.',selection='manufacturer_part_not_selected')
    add('EXT_LUG_ARMS',None,None,4,'M5 ring lug for4mm2 arm cable',local,
        'Exact lug/crimp tooling unselected;25A per-arm planning envelope, temperature validation required.',selection='manufacturer_part_not_selected')
    add('EXT_CABLES',None,None,1,'Harness cable, ferrules and strain-relief materials',local,
        'Lengths and insulation grades unselected. Battery6mm2;arms4mm2;drive/chopper1.5mm2;lift/5V1mm2;PC0.75mm2;NTC0.25mm2. Chopper pair neither terminal isground.',selection='harness_cut_list_unreleased',unit='lot')
    add('EXT_COVERS',None,None,1,'Insulated live-bus covers and mechanical restraint',local,
        'No dimensions/ordercode released. Independent mechanical support;>=15mmclearance belowPCB forbar/clamp stack;>=25mm screwdriver/lug access. See manufacturing/MECHANICAL_BUILD.md.',selection='mechanical_drawing_unreleased',unit='lot')
    add('EXT_BUTTON',None,None,1,'Normally-open momentary power button and harness','design/WAKE_IO.md',
        'Dry contact toJ20; noexternal voltage; exactswitch andmatingharness unselected.',selection='manufacturer_part_not_selected')
    add('EXT_PERMISSION',None,None,1,'Deenergized-open motion permission relay/contact and harness','design/WAKE_IO.md',
        'J22 loop3.3V only; no24V injection orpermanent actuator-test jumper. Final emergency-stop design unaccepted.',selection='commissioning_interface_unreleased')
    add('EXT_FUSE',None,None,1,'External60A fuse and holder','design/POWER_STAGE.md',
        'Exact fuse family/interrupt rating/time-current curve andholder unselected; must close beforebattery attachment.',selection='manufacturer_part_not_selected')
    add('EXT_CONVERTERS',None,None,1,'External PC,5V andlift converters','design/POWER_STAGE.md',
        'Actual converters and inputcapacitance/transient ratings unselected; not included inon-board eFuse ordercodes.',selection='external_system_parts_not_selected',unit='set')
    return rows


def write_csv(path, rows, fields):
    with path.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields,lineterminator='\n',extrasaction='ignore')
        w.writeheader()
        for row in rows:
            out={}
            for k in fields:
                val=row.get(k,'')
                if isinstance(val,list):
                    val='; '.join(json.dumps(x,ensure_ascii=False,sort_keys=True) if isinstance(x,dict) else str(x) for x in val)
                elif isinstance(val,dict):
                    val=json.dumps(val,ensure_ascii=False,sort_keys=True)
                elif val is None:
                    val=''
                elif isinstance(val,bool):
                    val=str(val).lower()
                out[k]=val
            w.writerow(out)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output-dir',type=Path,default=ROOT/'manufacturing')
    args=ap.parse_args()
    out=args.output_dir
    out.mkdir(parents=True,exist_ok=True)
    errors=[];warnings=[];source_by_ref={};input_paths=[]
    for name in PART_SOURCES:
        path=DESIGN/name;input_paths.append(path);doc=read(path)
        for c in doc['components']:
            ref=c['ref']
            if ref in source_by_ref:
                errors.append(f'Duplicate source reference {ref}')
            source_by_ref[ref]={**c,'source_record':str(path.relative_to(ROOT))}
    assembled_path=DESIGN/'assembled-parts.json';input_paths.append(assembled_path)
    assembled=read(assembled_path)['components']
    cad={c['ref']:c for c in assembled}
    if len(cad)!=len(assembled):
        errors.append('Duplicate reference in assembled-parts.json')
    evidence=evidence_index()
    alt_path=DESIGN/'critical-alternatives.json';input_paths.append(alt_path)
    alt=defaultdict(list)
    for a in read(alt_path)['alternatives']:
        alt[a['selected_mpn']].append(a)
    for selected,alternate,kind,note in [
        ('TPS7A4001DGNR','TPS7A4001DGNT','same_silicon_packaging_alternative','Smaller reel; same DGN package'),
        ('REF5025IDR','REF5025ID','same_silicon_packaging_alternative','Tube instead of reel; preserve I accuracy grade'),
        ('UCC27511DBVR','UCC27511DBVT','same_silicon_packaging_alternative','Smaller reel; same DBV package'),
        ('TPS3808G01DBVR','TPS3808G01DBVT','same_silicon_packaging_alternative','Smaller reel; retain adjustable G01 threshold'),
        ('LM339BIPWR','LM2901BIPWR','engineering_candidate_only','Recheck full-temperature offset/bias and output-low bounds before substitution')]:
        alt[selected].append(dict(alternative_mpn=alternate,classification=kind,same_source=True,
            automatic_substitution_approved=kind=='same_silicon_packaging_alternative',
            evidence_document='design/CHOPPER_PROCUREMENT.md',notes=note))
    excluded=[];records=[]
    for ref,c in sorted(source_by_ref.items(),key=lambda x:natural(x[0])):
        if pcb_feature(c):
            excluded.append(dict(ref=ref,reason='PCB feature or ERC-only object; not purchased',footprint=c.get('footprint','')))
            continue
        if not c.get('on_board',True):
            errors.append(f'{ref}: unclassified off-board source part; add explicit external BOM mapping')
            continue
        if ref not in cad:
            errors.append(f'{ref}: final source part missing from assembled CAD record')
            a={}
        else:
            a=cad[ref]
            for field in ['mpn','footprint','value']:
                if c.get(field)!=a.get(field):
                    errors.append(f'{ref}: stale assembled {field}: {a.get(field)!r} != finalsource {c.get(field)!r}')
            if dnp(a)!=dnp(c):
                errors.append(f'{ref}: source/CAD DNP state differs')
        mfr=manufacturer(c)
        if not mfr:
            errors.append(f'{ref}: manufacturer identity not resolved')
        if mfr=='TDK' and 'murata.com' in c.get('source_url',''):
            errors.append(f'{ref}: TDK MPN has incorrect Murata source URL')
        code_check=check_mpn(c,errors)
        url=c.get('source_url','')
        ev=evidence.get(url,[])
        rating=CRITICAL_RATINGS.get(c['mpn'],c.get('value',''))
        record=dict(ref=ref,mpn=c['mpn'],manufacturer=mfr,footprint=c['footprint'],
            description=c.get('value',''),ratings=rating,qualification=c.get('qualification',{}),
            dnp=dnp(c),population='DNP' if dnp(c) else 'POPULATE',
            lifecycle=lifecycle(c),source_url=url,source_record=c['source_record'],
            evidence=ev,evidence_document=('design/POWER_STAGE.md' if 'power-parts' in c['source_record']
                else 'design/WAKE_IO.md' if 'wake-io-parts' in c['source_record'] else 'design/CHOPPER_PROCUREMENT.md'),
            order_code_review=code_check,alternatives=alt.get(c['mpn'],[]),
            notes=c.get('notes',''),sheet=a.get('effective_sheet',c.get('sheet','')),
            supplier_stock_verified=False,stock_status='unverified_at_build',state=STATE)
        records.append(record)
    for ref,c in cad.items():
        if ref not in source_by_ref and not pcb_feature(c):
            errors.append(f'{ref}: purchased CAD part has no final source record')
    groups=defaultdict(list)
    for r in records:
        groups[(r['mpn'],r['footprint'],r['dnp'])].append(r)
    rows=[]
    for key,items in sorted(groups.items(),key=lambda x:(x[0][0],x[0][1],x[0][2])):
        first=items[0]
        unique=lambda field: sorted({str(i[field]) for i in items if i.get(field)},key=natural)
        rows.append(dict(references=sorted([x['ref'] for x in items],key=natural),
            quantity_positions=len(items),quantity_required=0 if first['dnp'] else len(items),unit='each',
            mpn=first['mpn'],manufacturer=first['manufacturer'],footprint=first['footprint'],
            descriptions=unique('description'),ratings=unique('ratings'),dnp=first['dnp'],
            population=first['population'],lifecycle=unique('lifecycle'),
            source_urls=unique('source_url'),evidence_documents=unique('evidence_document'),
            source_records=unique('source_record'),notes=unique('notes'),sheets=unique('sheet'),
            alternatives=first['alternatives'],order_code_review=unique('order_code_review'),
            supplier_stock_verified=False,stock_status='unverified_at_build',state=STATE))
    ext=external_items(list(source_by_ref.values()),errors)
    # Independent readback totals make loss, duplicate grouping, and DNP leakage visible.
    grouped_refs=[x for row in rows for x in row['references']]
    if len(grouped_refs)!=len(set(grouped_refs)) or set(grouped_refs)!={x['ref'] for x in records}:
        errors.append('Grouped BOM reference reconciliation failed')
    for path,initial_hash in READ_SNAPSHOTS.items():
        if digest(path)!=initial_hash:
            errors.append(f'Input changed during BOM generation: {path.relative_to(ROOT).as_posix()}; rerun after source generation')
    metadata=dict(rev_a_engineering_prototype=True,rev_b_production=False,state=STATE,
        date=DATE,stock_verification='No live stock query or reservation made by builder',
        quantity_basis='One PCB assembly, no placement waste or spares; DNP positions retained with zero required quantity',
        purchased_pcb_positions=len(records),populated_pcb_quantity=sum(not r['dnp'] for r in records),
        dnp_pcb_positions=sum(r['dnp'] for r in records),grouped_pcb_line_count=len(rows),
        excluded_pcb_feature_count=len(excluded),external_bom_line_count=len(ext),
        external_unselected_line_count=sum(r['selection_status'] not in ('exact_part_selected','custom_manufactured_to_project_drawing') for r in ext),
        external_custom_drawing_line_count=sum(r['selection_status']=='custom_manufactured_to_project_drawing' for r in ext),
        mechanical_interface_coverage=MECHANICAL_COVERAGE,
        validation_passed=not errors,errors=errors,warnings=warnings,
        claim_limit='Identity/coding and source/CAD consistency review; not every individual passive was queried for stock or formal lifecycle')
    body=dict(metadata=metadata,lines=rows,components=records,excluded_features=excluded)
    (out/'REV_A_BOM.json').write_text(json.dumps(body,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    fields=['references','quantity_positions','quantity_required','unit','mpn','manufacturer','footprint',
            'descriptions','ratings','dnp','population','lifecycle','source_urls','evidence_documents',
            'alternatives','order_code_review','supplier_stock_verified','stock_status','notes','sheets','state']
    write_csv(out/'REV_A_BOM.csv',rows,fields)
    (out/'REV_A_EXTERNAL_BOM.json').write_text(json.dumps(dict(metadata=metadata,lines=ext),indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    write_csv(out/'REV_A_EXTERNAL_BOM.csv',ext,['references','quantity_positions','quantity_required','unit',
        'mpn','manufacturer','description','dnp','selection_status','lifecycle','source_url','constraints',
        'supplier_stock_verified','stock_status','state'])
    with (out/'REV_A_BOM.csv').open(encoding='utf-8-sig',newline='') as f:
        rr=list(csv.DictReader(f))
    if sum(int(x['quantity_required']) for x in rr)!=metadata['populated_pcb_quantity']:
        raise RuntimeError('Saved CSV population total mismatch')
    products=['REV_A_BOM.csv','REV_A_BOM.json','REV_A_EXTERNAL_BOM.csv','REV_A_EXTERNAL_BOM.json']
    manifest=dict(metadata=metadata,builder=dict(path=str(Path(__file__).relative_to(ROOT)),sha256=digest(Path(__file__))),
        inputs=[dict(path=p.relative_to(ROOT).as_posix(),sha256=sha) for p,sha in sorted(READ_SNAPSHOTS.items(),key=lambda x:str(x[0]))],
        outputs=[dict(path=n,sha256=digest(out/n),bytes=(out/n).stat().st_size) for n in products])
    (out/'REV_A_BOM_MANIFEST.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
    print(f'{len(records)} purchased PCB positions; {metadata["populated_pcb_quantity"]} populated; '
          f'{metadata["dnp_pcb_positions"]} DNP; {len(rows)} grouped lines; {len(ext)} external lines; {len(errors)} errors')
    for e in errors:
        print('ERROR:',e)
    return 2 if errors else 0


if __name__=='__main__':
    raise SystemExit(main())
