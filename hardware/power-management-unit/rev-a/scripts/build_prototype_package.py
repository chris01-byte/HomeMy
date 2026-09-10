"""Assemble the versioned PCB prototype delivery and its SHA-256 manifest.

Run after the native export and final reviews. The package is never an
authorization to energize hardware or a series-production qualification.
"""
import csv
from datetime import datetime, timezone
import hashlib
import html
import json
import math
from pathlib import Path
import re
import shutil
import subprocess
from urllib.parse import quote
import zipfile
from prepare_prototype_release import ROOT, VERSION, PACKAGE
from sexpr import parse, children, child, unquote


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write_json(p,value):p.write_text(json.dumps(value,indent=2,ensure_ascii=False)+'\n',encoding='utf-8')
def write_csv(p,rows,fields):
    with p.open('w',encoding='utf-8-sig',newline='') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows(rows)


def main():
    out=ROOT/PACKAGE
    release=read(ROOT/'release.json')
    assert release['prototype_package_version']==VERSION and release['fabrication_release'] and not release['production_release']
    export=read(out/'EXPORT_MANIFEST.json')
    assert export['metadata']['coverage_validation_passed'] and export['board_state']['source_release']==release
    for row in export['inputs']:assert sha(ROOT/row['path'])==row['sha256'],row['path']
    for row in export['outputs']:assert sha(out/row['path'])==row['sha256'],row['path']
    inputs={str((out/'EXPORT_MANIFEST.json').relative_to(ROOT)):sha(out/'EXPORT_MANIFEST.json')}
    markdown_sources={}
    def copy(source,destination):
        p=ROOT/source;q=out/destination;q.parent.mkdir(parents=True,exist_ok=True)
        inputs[source]=sha(p);shutil.copyfile(p,q)
        if q.suffix=='.md':markdown_sources[q]=p
    for folder in ['fabrication','mechanical','evidence','integration']:(out/folder).mkdir(exist_ok=True)
    for name in ['PCB_STACKUP_PRESSFIT.md','MECHANICAL_BUILD.md','CONNECTOR_ASSEMBLY.md',
                 'ASSEMBLY_ORIENTATION.md','ASSEMBLY_ORIENTATION.svg','assembly-orientation.json',
                 'BUSBAR_TOP_VIEW_1to1.svg','MECHANICAL_CATALOG_BOM.json']:
        folder='fabrication' if name=='PCB_STACKUP_PRESSFIT.md' else ('assembly' if 'ORIENTATION' in name or 'orientation' in name or name=='CONNECTOR_ASSEMBLY.md' else 'mechanical')
        copy('manufacturing/'+name,folder+'/'+name)
    for name in ['erc-final.json','drc-final.json','erc-final-process.log','drc-final-process.log','native-checks-both.json','electrical-parity-audit.json']:
        copy('reports/'+name,'evidence/'+name)
    for name in ['high-current-audit.json','high-current-tap-capture.json','filled-power-copper-review.json','filled-power-copper-review.md','placement-access-review.json']:
        copy('evidence/'+name,'evidence/'+name)
    copy('design/HIGH_CURRENT_RULES.md','evidence/HIGH_CURRENT_RULES.md')
    copy('design/external-integration-gates.json','integration/external-integration-gates.json')
    copy('release.json','RELEASE.json')
    # The two upstream documents are copied under explicit package names, with
    # source hashes; they remain the governing staged energization/qualification gates.
    copy('../DESIGN_REVIEW_AND_BRINGUP.md','integration/DESIGN_REVIEW_AND_BRINGUP.md')
    copy('../REV_B_VALIDATION.md','integration/REV_B_VALIDATION.md')
    copy('reports/assembly-orientation-review.png','assembly/ASSEMBLY_ORIENTATION.png')

    # Keep assembly files local. Further source evidence remains available at
    # immutable repository URLs, even when this ZIP is unpacked on its own.
    repo=ROOT.parents[2]
    source_commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    external_source_links=[]
    for destination,source in markdown_sources.items():
        def relink(match):
            target=match.group(1)
            if target.startswith(('https:','http:','#')):return match.group(0)
            local,separator,anchor=target.partition('#')
            if (destination.parent/local).exists():return match.group(0)
            original=(source.parent/local).resolve()
            relative=original.relative_to(repo.resolve()).as_posix()
            committed=subprocess.check_output(['git','show',source_commit+':'+relative],cwd=repo)
            current=original.read_bytes()
            assert committed==current or (original.suffix=='.md' and
                committed.decode('utf-8').splitlines()==current.decode('utf-8').splitlines()),'Uncommitted linked source: '+relative
            url='https://github.com/chris01-byte/HomeMy/blob/'+source_commit+'/'+quote(relative,safe='/')
            if separator:url+='#'+anchor
            external_source_links.append({'document':destination.relative_to(out).as_posix(),'source':relative,'url':url})
            return ']('+url+')'
        destination.write_text(re.sub(r'\]\(([^)]+)\)',relink,destination.read_text(encoding='utf-8')),encoding='utf-8')

    orientation=read(ROOT/'manufacturing/assembly-orientation.json')
    board=ROOT/'kicad/HomeMy_PMU_RevA.kicad_pcb'
    assert orientation['input_board_sha256']==sha(board)
    holes=[]
    for number in range(1,7):
        ref=f'J{number}'
        for pad in orientation['components'][ref]['pads']:
            assert abs(pad['drill_mm']-1.475)<1e-6
            holes.append(dict(reference=ref,pin=pad['number'],net=pad['net'],x_mm=pad['xy_mm'][0],y_mm=pad['xy_mm'][1],
                finished_diameter_mm=1.475,finished_tolerance_plus_minus_mm=.05,raw_drill_mm=1.6,raw_tolerance_plus_mm=0,
                raw_tolerance_minus_mm=.03,barrel_copper_min_um=25,barrel_copper_max_um=60,minimum_annular_ring_mm=.10,
                origin='F.Cu view; X right; Y down; absolute PCB origin',terminal_face='-Y' if number in [1,2,3,5] else '+Y'))
    assert len(holes)==48 and len({(r['x_mm'],r['y_mm']) for r in holes})==48
    write_csv(out/'fabrication/PRESSFIT_HOLES.csv',holes,list(holes[0]))
    (out/'fabrication/FABRICATION_NOTES.md').write_text('''# Rev A-P1 fabrication order notes

Engineering prototype – not production qualified.

Supply the bare 360 x 300 mm four-layer PCB to the Gerbers, separate PTH/NPTH
Excellon files and PCB_STACKUP_PRESSFIT.md. Copper is at least 70/35/35/70 um
finished; thickness is 1.60-1.70 mm between outer copper faces, excluding mask.
ENIG; specified FR-4 Tg125-135 C press-fit baseline. No implicit Tg170 substitute.

PRESSFIT_HOLES.csv identifies all 48 special J1-J6 holes in top-view PCB
coordinates. Excellon carries FINISHED dimensions. Do not replace its 1.475 mm
tool value by the 1.60 mm raw drill value. The fabricator must meet finished
size, raw drill, plating and annular ring jointly. Do not solder or paste these
holes. BC/NT clamp holes are a separate 3.2 mm PTH class, never press-fit holes.

Before accepting the order, the supplier must confirm the special laminate,
thickness, finished copper and bore/plating process. Include representative
press-fit and clamp coupons; their quantity/cost is additional to the one-PCB
BOM and must be stated in the quote. Coupon measurement and insertion-force
acceptance precede pressing the delivered PCB assemblies. No evidence of such
physical acceptance is claimed by this CAD package.

Electrical bare-board testing, outline dimensions, hole measurement, coating
and cleanliness inspection belong to lot acceptance. Do not change nets,
footprints, copper or stackup to meet a supplier's default process. A required
design change creates a new package version and new native checks.
''',encoding='utf-8')
    bom=read(ROOT/'manufacturing/REV_A_BOM.json')
    dnps=[c for c in bom['components'] if c['dnp']]
    assert {c['ref'] for c in dnps}=={'C244','J13','R243','R244'}
    (out/'assembly/DNP.md').write_text('# Rev A-P1 DNP list\n\nDo not populate these four positions in the default prototype.\n\n| Ref | MPN | Description |\n|---|---|---|\n'+''.join(f"| {c['ref']} | {c['mpn']} | {c['description']} |\n" for c in dnps)+'\nDNP placements have zero required quantity. The separate position file preserves their coordinates for review. No optional population without a new assembly variant.\n',encoding='utf-8')

    integration=read(ROOT/'design/external-integration-gates.json')
    text='# Open external order positions — Rev A-P1\n\n## Required before PCB ordering\n\nNone of the nine unresolved external BOM rows requires a PCB footprint change under the frozen interfaces below. Supplier acceptance of special PCB fabrication requirements is still required.\n\n## Required before energization\n\n| Item | Frozen PCB/external boundary | Evidence required before use |\n|---|---|---|\n'
    for row in integration['before_energization']:text+=f"| {row['reference']} | {row['interface']} | {row['closure']} |\n"
    text+='\nA nonconforming external selection is rejected or requires a new CAD/package revision. These open items do not authorize bypasses, permanent permission jumpers, connector substitution or battery connection.\n'
    (out/'integration/OPEN_ORDER_ITEMS.md').write_text(text,encoding='utf-8')
    audit=read(ROOT/'evidence/high-current-audit.json')
    assert audit['passed'] and audit['board_sha256']==sha(board)
    sections=[]
    for row in audit['cross_section_ledger']:
        sections.append({k:(json.dumps(v) if isinstance(v,list) else v) for k,v in row.items()})
    write_csv(out/'evidence/POWER_CROSS_SECTIONS.csv',sections,list(sections[0]))

    # Mechanical dimensions are derived from controlled drawings and verified
    # against actual PCB contact centers, rather than inferred from SVG pixels.
    ast=parse(board.read_text());fps={}
    for fp in children(ast,'footprint'):
        ref=next(unquote(x[2]) for x in children(fp,'property') if unquote(x[1])=='Reference')
        at=child(fp,'at');x,y=map(float,at[1:3]);angle=float(at[3]) if len(at)>3 else 0
        c=math.cos(math.radians(angle));s=math.sin(math.radians(angle));pads=[]
        for pad in children(fp,'pad'):
            a,b=map(float,child(pad,'at')[1:3]);net=child(pad,'net')
            pads.append({'pin':unquote(pad[1]),'x':round(x+c*a+s*b,6),'y':round(y-s*a+c*b,6),'net':unquote(net[-1]) if net else ''})
        fps[ref]={'x':x,'y':y,'pads':pads}
    interface=read(ROOT/'manufacturing/busbar-pcb-interface.json')
    inputs['manufacturing/busbar-pcb-interface.json']=sha(ROOT/'manufacturing/busbar-pcb-interface.json')
    for bar in interface['busbars']:
        for hole in bar['holes']:
            label=hole['function'];ref,_,pin=label.partition('.')
            pad=next(p for p in fps[ref]['pads'] if p['pin']==(pin or '1'))
            assert abs(pad['x']-hole['x'])<1e-6 and abs(pad['y']-hole['y'])<1e-6,label
            assert pad['net']==bar['net'],label+' net'
    mechanical={'metadata':{'rev_a_engineering_prototype':True,'rev_b_production':False,'package_version':VERSION},
        'coordinate_system':'F.Cu view, X right and Y down, absolute mm; underside bars are not mirrored',
        'board_sha256':sha(board),'busbars':interface['busbars'],
        'top_bridges':[n['top_bridge'] for n in interface['net_tie_modifications']],
        'contact_shim':interface['contact_shim'],'film':interface['film'],
        'clamp_stack_document':'MECHANICAL_BUILD.md','verified_busbar_to_pcb_holes':True}
    for bar in mechanical['busbars']:
        bar['insulation']='Four 0.05 mm Kapton HN layers, total nominal 0.20 mm / maximum 0.22 mm; selected film and 0.25 mm Cu contact shims mandatory.'
        # Hole location tolerances exist in the source drawing; specify bore size
        # explicitly for this prototype, leaving PCB finished holes at 3.2 mm.
        bar['hole_diameter_tolerance_plus_minus_mm']=.10
        bar['edge_requirement']='Deburr and break sharp edges; no conductive burrs against insulation; cutout inside radius 1 mm as dimensioned.'
    write_json(out/'mechanical/BUSBAR_DIMENSIONS.json',mechanical)
    for bar in mechanical['busbars']:
        parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="220mm" viewBox="0 0 420 220"><rect width="420" height="220" fill="white"/>',
               f'<g font-family="Arial,sans-serif" fill="#17232a"><text x="10" y="12" font-size="6">{bar["ref"]} — {VERSION} — {bar["net"]}</text>',
               '<text x="10" y="19" font-size="3.4">Engineering prototype – not production qualified. Scale 1:1. F.Cu coordinate view; underside NOT mirrored.</text>',
               '<g transform="translate(15 25)">',
               '<polygon points="'+' '.join(f'{x},{y}' for x,y in bar['outline'])+'" fill="#efc17f" stroke="#262626" stroke-width="0.2"/>']
        for cut in bar['cutouts']:
            xs=[p[0] for p in cut['outline']];ys=[p[1] for p in cut['outline']]
            parts.append(f'<rect x="{min(xs)}" y="{min(ys)}" width="{max(xs)-min(xs)}" height="{max(ys)-min(ys)}" rx="{cut["corner_radius_mm"]}" fill="white" stroke="#262626" stroke-width="0.2"/>')
        for hole in bar['holes']:parts.append(f'<circle cx="{hole["x"]}" cy="{hole["y"]}" r="{hole["diameter_mm"]/2}" fill="white" stroke="#262626" stroke-width="0.2"/>')
        parts+=['</g>',f'<text x="10" y="173" font-size="3.6">Cu-ETP / CW004A; thickness 2.00 +/-0.10 mm; outline +/-0.20 mm; hole centers +/-0.10 mm.</text>',
                '<text x="10" y="180" font-size="3.6">Holes diameter 3.40 +/-0.10 mm. Cutout radius R1. Deburr. Exact vertices/holes: BUSBAR_DIMENSIONS.json.</text>',
                '<text x="10" y="187" font-size="3.6">4 x 0.05 mm Kapton HN underneath; 0.25 mm Cu contact shims. No shunt or FET-bank bypass.</text>',
                '<path d="M10 203H110M10 201V205M110 201V205" fill="none" stroke="black" stroke-width="0.3"/><text x="45" y="200" font-size="3.6">100 mm check</text></g></svg>']
        (out/'mechanical'/f'{bar["ref"]}_1to1.svg').write_text('\n'.join(parts),encoding='utf-8')

    refs=['C246','C312','C313','D60','D61','D62','D63','D64','D65','D66','D1','D2']
    parts=['<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297"><rect width="420" height="297" fill="white"/><g font-family="Arial,sans-serif" fill="#17232a">',
           '<text x="10" y="13" font-size="6">Rev A-P1 — polarity / mounting detail</text>',
           '<text x="10" y="21" font-size="3.5">F.Cu view. Pad coordinates in mm. Details enlarged; body marks checked against manufacturer drawings.</text>']
    for i,ref in enumerate(refs):
        fp=fps[ref];left=10+(i%4)*102;top=32+(i//4)*77
        parts.append(f'<rect x="{left}" y="{top}" width="97" height="71" rx="2" fill="#f5f6f7" stroke="#ccd1d5" stroke-width="0.3"/><text x="{left+4}" y="{top+8}" font-size="5">{ref}</text>')
        pads=fp['pads'];scale=3;cx=left+48;cy=top+30
        for p in pads:
            px=cx+(p['x']-fp['x'])*scale;py=cy+(p['y']-fp['y'])*scale
            label=('+' if p['pin']=='1' else '-') if ref.startswith('C') else (p['pin'] if ref in ['D1','D2'] else ('K' if p['pin']=='1' else 'A'))
            parts.append(f'<circle cx="{px}" cy="{py}" r="3" fill="{"#d46a59" if p["pin"]=="1" else "#637c91"}"/><text x="{px}" y="{py+1}" text-anchor="middle" font-size="3" fill="white">{label}</text>')
        for j,p in enumerate(pads):parts.append(f'<text x="{left+4}" y="{top+48+j*5}" font-size="3">{p["pin"]}: {p["net"]}  ({p["x"]:g}, {p["y"]:g})</text>')
        note='Stripe = minus (pin 2)' if ref.startswith('C') else ('Bidirectional TVS; no K/A polarity' if ref in ['D1','D2'] else ('Pin 1 and live tab = cathode' if ref=='D63' else 'Cathode body band = pin 1 (K)'))
        parts.append(f'<text x="{left+4}" y="{top+64}" font-size="3">{html.escape(note)}</text>')
    parts+=['<text x="10" y="281" font-size="3.3">Q1-Q10 / Q40 / U1 and M5-face directions: ASSEMBLY_ORIENTATION.svg. Connector pinout: CONNECTOR_PINOUT.csv.</text>',
            '<text x="10" y="289" font-size="3.3">DNP: C244, J13, R243, R244. Engineering prototype – not production qualified. No power applied for assembly inspection.</text></g></svg>']
    (out/'assembly/POLARITY.svg').write_text('\n'.join(parts),encoding='utf-8')
    connectors=[{'reference':ref,**p} for ref,f in fps.items() if ref.startswith('J') for p in f['pads']]
    write_csv(out/'assembly/CONNECTOR_PINOUT.csv',connectors,['reference','pin','x','y','net'])

    native=read(ROOT/'reports/native-checks-both.json')
    hashes='\n'.join(f"- {name.upper()}: exit {row['process_exit_code']}, SHA-256 `{row['report_sha256']}`." for name,row in native['checks'].items())
    (out/'README.md').write_text(f'''# HomeMy PMU {VERSION} — prototype order package

**Engineering prototype – not production qualified**

This version is orderable as a **bare PCB or populated PCB engineering prototype**
to the enclosed requirements. `fabrication_release` and `assembly_release`
apply only to that scope. Production, a validated 50 A operating rating,
firmware, external system integration and permission to energize are excluded.
No physical board has been ordered, built or tested by this release process.

Package version: {VERSION}, dated 2026-09-10. PCB SHA-256: `{sha(board)}`.
Use PACKAGE_MANIFEST.json and SHA256SUMS.txt to verify this exact delivery.
Source release: RELEASE.json. An altered file invalidates this version.
Further source references in copied documents use immutable repository links;
internet access is required for those supporting references. Manufacturing
drawings and order data are enclosed locally.

| Delivery | Files |
|---|---|
| Bare PCB | gerbers/: 11 X2 layers + job; drill/: separate PTH/NPTH Excellon + maps |
| Complete PCB BOM | bom/REV_A_BOM.csv + JSON; 356 positions, 352 populated, 4 DNP |
| Placement | assembly/: all, SMD and manual positions; units/origin/rotation in EXPORT_README.md |
| DNP | assembly/DNP.md and separate DNP position file |
| Stackup and bores | fabrication/PCB_STACKUP_PRESSFIT.md, PRESSFIT_HOLES.csv (48 holes), FABRICATION_NOTES.md |
| Copper hardware | mechanical/: BB1-BB7 drawings, combined 1:1 drawing, BUSBAR_DIMENSIONS.json, clamp BOM and build sequence |
| Assembly and polarity | assembly/: front/back Fab drawings, ASSEMBLY_ORIENTATION.svg, POLARITY.svg and connector pinout |
| Open external positions | integration/OPEN_ORDER_ITEMS.md: 0 before PCB order; 9 before energization |
| Verification | evidence/: native ERC/DRC, process exits/hashes, exact parity and high-current/neck review |

## Order and assembly conditions

The supplier must accept the specified finished press-fit holes and plating,
1.60-1.70 mm board thickness, finished 70/35/35/70 um copper, laminate and ENIG.
Order representative process coupons with the prototype; confirm their
quantity and insertion/clamp process in the quote. If these requirements cannot
be met, stop and revise the design/package; do not substitute a standard stackup.

The BOM quantities cover one PCB without placement waste or spares. Stocks are
unverified. Use exact selected PCB parts and only explicitly approved packaging
aliases. Pick-and-place coordinates are footprint anchors in the top-view
board frame; the assembler maps its machine origin, centroid and rotation.
Manual/THT and press-fit operations are separate. Complete soldering and
cleaning before pressing J1-J6; do not reflow the press-fit connections.

Seven underside busbars, eight top star bridges, contact shims and specified
insulation/clamp hardware are required for the designed high-current assembly.
They must never bypass shunts or FET banks. External fuse, converters, cables,
lugs, support/guards and permission circuit may be finalized later only within
the frozen interfaces. All nine external integration items and the staged
bring-up gates must be closed before their respective powered use.

## Recorded final native checks

Both checks used all severities; DRC used all-track-errors and full schematic
parity. Zero findings, zero open connections and zero parity differences.
Processes ended normally in the user's installed KiCad 10.0.6 session:

{hashes}

The old timeout-124 reports remain historical evidence in the source repository.
Their status is not reused as a passing result. The separate geometric audits
and 247 power-pad paths do not replace current-sharing, contact, thermal, SOA,
transient or real press-fit measurements. See integration/REV_B_VALIDATION.md.
''',encoding='utf-8')
    files=[{'path':p.relative_to(out).as_posix(),'bytes':p.stat().st_size,'sha256':sha(p)}
           for p in sorted(out.rglob('*')) if p.is_file() and p.name not in ['PACKAGE_MANIFEST.json','SHA256SUMS.txt']]
    manifest={'metadata':{'rev_a_engineering_prototype':True,'rev_b_production':False,'package_version':VERSION,
        'fabrication_release':True,'assembly_release':True,'production_release':False,
        'scope':'Bare/populated Rev A-P1 PCB engineering prototype only','notice':'Engineering prototype – not production qualified'},
        'board_sha256':sha(board),'created_at_utc':datetime.now(timezone.utc).isoformat(),
        'native_process_exit_codes':{k:v['process_exit_code'] for k,v in native['checks'].items()},
        'native_report_hashes':{k:v['report_sha256'] for k,v in native['checks'].items()},
        'counts':{'gerbers':11,'populated_pcb_positions':352,'dnp_positions':4,'pressfit_holes':48,
                  'busbars':7,'top_star_bridges':8,'open_external_before_pcb_order':0,'open_external_before_energization':9},
        'source_inputs_sha256':inputs,'files':files,'builder_sha256':sha(Path(__file__)),
        'external_source_commit':source_commit,'external_source_links':external_source_links}
    write_json(out/'PACKAGE_MANIFEST.json',manifest)
    checks=files+[{'path':'PACKAGE_MANIFEST.json','sha256':sha(out/'PACKAGE_MANIFEST.json')}]
    (out/'SHA256SUMS.txt').write_text(''.join(f"{r['sha256']}  {r['path']}\n" for r in checks),encoding='utf-8')
    archive=out.with_suffix('.zip')
    with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
        for p in sorted(out.rglob('*')):
            if p.is_file():z.write(p,arcname=out.name+'/'+p.relative_to(out).as_posix())
    archive.with_suffix('.zip.sha256').write_text(sha(archive)+'  '+archive.name+'\n',encoding='utf-8')
    with zipfile.ZipFile(archive) as z:assert z.testzip() is None
    print(f'{VERSION}: {len(files)} delivery files plus manifests; 48 press-fit coordinates; ZIP {archive.stat().st_size} bytes; SHA256 {sha(archive)}')


if __name__=='__main__':main()
