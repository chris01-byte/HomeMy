"""Turn the measured native-copper snapshot into a reviewable engineering report."""
from pathlib import Path
import json,hashlib,collections
ROOT=Path(__file__).resolve().parent
j=json.loads((ROOT/'filled-power-copper-review.json').read_text())
j.setdefault('metadata',{}).update(rev_a_engineering_prototype=True,rev_b_production=False)
def scan(label,layer):
    return next(s for s in j['cross_sections'] if s['label']==label and s['layer']==layer)
def old_or_new(label,old,layer):
    return next(s for s in j['cross_sections'] if s['label'] in [label,old] and s['layer']==layer)
def group(label,old):
    a=old_or_new(label,old,'F.Cu');b=old_or_new(label,old,'B.Cu')
    return f"| {label} | {a['line_from_mm']} → {a['line_to_mm']} | {a['total_copper_width_mm']:.2f} | {b['total_copper_width_mm']:.2f} |"
rows=[]
for label,old in [('RSH1 input approach','RSH1 input approach'),('RSH1 output approach','RSH1 output approach'),('RSH2 input approach','RSH2 input approach'),('RSH2 output approach','RSH2 output approach'),('Arm positive top rail','Armpositive top rail'),('Right positive rail at junction','Rightpositive rail atjunction'),('Star crossed by SYS feed','StarcrossedbySYSfeed'),('Left arm return approaching NT1','Leftarmreturn approachingNT1'),('Right arm return approaching NT2','Rightarmreturn approachingNT2'),('Q40 source below bank','Q40source belowbank'),('Q40 drain exit','Q40drain exit'),('Chopper drain connector neck','Chopperdrain connectorneck')]:rows.append(group(label,old))
fields=[]
for net,count in j['via_field_source']['counts'].items():
    a,b=[c for c in j['via_field_ideal_calculations'] if c['net']==net]
    fields.append(f"| {net} | {count} | {a['resistance_ohm']*1e6:.3f} / {b['resistance_ohm']*1e6:.3f} | {a['loss50A_W']:.4f} / {b['loss50A_W']:.4f} | {a['loss60A_W']:.4f} / {b['loss60A_W']:.4f} |")
local=[v for v in j['vias'] if v['net']=='CHOPPER_N' and 294<=v['x']<=300 and 39<=v['y']<=46 and v['drill_mm']==.4 and 'F.Cu' in v['layers_connected'] and 'B.Cu' in v['layers_connected']]
local_r=2.2660256e-8*.0016/(len(local)*3.141592653589793*.0004*.000025)
report_file=ROOT.parent/'reports'/'drc-final.json'
r=json.loads(report_file.read_text())
native={'path':'reports/drc-final.json','sha256':hashlib.sha256(report_file.read_bytes()).hexdigest(),'date':r.get('date'),'geometry_count':len(r.get('violations',[])),'unconnected_count':len(r.get('unconnected_items',[])),'schematic_parity_count':len(r.get('schematic_parity',[]))}
for filename in ['native-checks-both.json','native-checks-drc.json']:
    p=ROOT.parent/'reports'/filename
    if not p.exists():continue
    m=json.loads(p.read_text());check=m.get('checks',{}).get('drc',{})
    if check.get('report_sha256')!=native['sha256']:continue
    h=next((v for k,v in m.get('input_hashes_sha256',{}).items() if k.endswith('.kicad_pcb')),None)
    native['matching_process_manifest']={'path':'reports/'+filename,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'board_sha256':h,'matches_reviewed_board':h==j['board_sha256'],'process_exit_code':check.get('process_exit_code'),'process_passed':check.get('process_passed'),'report_complete':check.get('report_complete')}
paths=j.get('same_layer_path_checks',[])
manifest=native.get('matching_process_manifest',{})
manifest_prose=(f"Matching process manifest: `{manifest['path']}`; its recorded board hash matches this review: **{manifest['matches_reviewed_board']}**. Process exit code: **{manifest['process_exit_code']}**; process passed: **{manifest['process_passed']}**; JSON report complete: **{manifest['report_complete']}**." if manifest else 'No matching process manifest was found for this report hash; report-to-board correspondence remains unconfirmed.')
rsh_ok=any(p['from_pad']=='RSH2.4' and p['same_continuous_copper_outline'] for p in paths)
lift_ok=sum(p['net']=='LIFT_N' and p['same_continuous_copper_outline'] for p in paths)==2
drain_pad=next(p for p in j['power_pad_connectivity'] if p['ref']=='Q40' and p['pad']=='3')
drain_area=sum(a.get('area_mm2_excluding_holes',0) for a in drain_pad.get('containing_copper_outlines',[]) if a['layer']=='F.Cu')
j['chopper_drain_copper']={'connected_FCu_area_mm2':drain_area,'target_mm2':600,'target_geometrically_met':drain_area>=600,'limitation':'Area includes same-net pad/track/zone copper connected to Q40 drain on F.Cu, with drill/clearance holes removed. This is not a thermal-resistance measurement.'}
j['observed_drc_report']=native
j['local_chopper_transfer']={'count':len(local),'assumptions':'Same barrel formula as field table; all local barrels ideally share 9.3 A.','resistance_ohm_100C':local_r,'loss_W_9p3A':local_r*9.3**2,'vias':local}
j['engineering_findings']=[
 {'id':'COPPER-01','finding':'RSH2 force-pad island found in the first routed snapshot a5fda347cb9910f0fb1f6774115fe7ddc8b8b0febc5a2a40d5e64ee023662d6b; a broad locked force link and rerouting were requested.','status':'Geometric connection restored in this snapshot; repeat after any routing changes.' if rsh_ok else 'Unresolved in this snapshot.'},
 {'id':'COPPER-02','finding':f"BATT_N F.Cu is interrupted by SYS feed at x = 110 mm; B.Cu has {scan('Star crossed by SYS feed','B.Cu')['total_copper_width_mm']} mm in the limited sampling window. Rev A-P1 extends the lower return to y=137 mm. BB7 reinforcement remains required.",'status':'Documented geometry; current capacity unqualified.'},
 {'id':'COPPER-03','finding':'Large via-field totals do not establish local current sharing; shunt force pads and FET leads enter from F.Cu only.','status':'Measurement gate retained.'},
 {'id':'COPPER-04','finding':'LIFT_N inner pours were severed by signal routes in the first routed snapshot; protected centerline paths were requested.','status':'Both inner paths are geometrically restored in this snapshot; repeat after routing changes.' if lift_ok else 'Unresolved in this snapshot.'}
]
(ROOT/'filled-power-copper-review.json').write_text(json.dumps(j,indent=2)+'\n',encoding='utf-8')
text=f'''# Filled power copper review — Rev A engineering prototype

This is a read-only review of the actual saved native KiCad board, including the effects of signal routing on the filled copper. It does **not** establish a 50 A continuous rating, a 60 A pulse rating, thermal qualification or manufacturing release.

- Input PCB SHA-256: `{j['board_sha256']}`.
- PCB unchanged during the native geometry analysis: `{j['board_unchanged_during_review']}`.
- Evidence: `filled-power-copper-review.json`, `filled-power-polygons.json` and the PNG views generated by `render_power_review.py`.
- Reproduction: run `review_filled_power.py` with the bundled KiCad Python through `scripts/run_tool.py`, then run `render_power_review.py` and `write_power_review.py` with the workspace Python. The native script does not refill or save the PCB.

## Method and limits

The measurement unions saved filled polygons with actual same-net pad, via and track copper on each layer. It removes circular drill interiors and samples defined transects at no more than 0.02 mm intervals. Outer layers use the specified 70 µm copper; inner layers use 35 µm. Width sums can contain several separate intervals around holes and are **not** global minimum cuts. A cross-section with copper does not prove end-to-end continuity: this was demonstrated by the isolated RSH2 force-pad island found in the first routed board.

Native per-layer connection flags record local contact with copper. They do not independently prove connection to the whole net. In addition, the JSON checks whether selected endpoint pads share the same continuous copper outline on a layer. The current snapshot has {sum(p['same_continuous_copper_outline'] for p in paths)} successful checks out of {len(paths)} tested paths. External busbars, clamp contacts, component internal conductors and the resistance of footprint net-tie bridges are not incorporated into this polygon resistance model. No finite-element current-density or thermal solution was performed.

## Measured paths

All 48 pressfit pads on J1–J6 contact copper on both outer layers in the inspected snapshot. These are solid zone connections; there is no four-spoke thermal connection credited for their current path. This verifies local PCB attachment of all eight pins per terminal. It does not replace the manufacturer's bore, plating, pressfit-force or tightening requirements.

| Transect | Board coordinates, mm | F.Cu total width, mm | B.Cu total width, mm |
|---|---|---:|---:|
{chr(10).join(rows)}

The scan endpoints deliberately limit several widths, so a full-width result is a lower bound within that window. The two arm-return samples are 12.5 mm rather than the earlier generic 20 mm strip assumption. At 100 °C, a hypothetical 20 mm long, 12.5 mm wide pair of 70 µm copper strips would have approximately 259 µΩ resistance and dissipate 0.162 W at 25 A. That strip calculation omits the diagonal taper, holes and spreading resistance. Actual arm paths must be checked by four-wire voltage drop and temperature in the assembled board.

RSH1 and RSH2 are SMD four-terminal shunts: force pads 1 and 4 touch F.Cu; Kelvin pads 2 and 3 have separate sense nets. A wide B.Cu polygon beneath a shunt pad is not a direct second pad connection. Current must first spread in F.Cu to plated transfers. Preserve the force/sense separation at the component and include local force-pad heating in qualification. Q1–Q10 likewise enter their source and drain lands from F.Cu only. The JSON samples every source and drain bank when regenerated with the current script; bank width alone does not prove equal current sharing among the five source leads or among parallel MOSFETs.

At x = 110 mm the SYS feed interrupts BATT_N on F.Cu. B.Cu has {scan('Star crossed by SYS feed','B.Cu')['total_copper_width_mm']:.2f} mm of copper within the limited sampling window. Rev A-P1 extends the return's lower edge to y=137 mm and restores a broad route below NT1/NT2 after sliver filtering. Near J4/J6 the return copper still splits around separate branch regions and holes. The specified BB7 bar and NB branch bridges, contact shims, film and spring clamps remain mandatory. This is not a uniform pair of unbroken strips. The 10 × 10 mm PTH star lands are power attachment points; signal net ties NT9/NT10 are not substitutes.

Q40's source joins the local CHOPPER_N F.Cu area, transfers through **{len(local)} observed 0.4 mm vias** to B.Cu, and reaches the capacitor-negative trunk and the return spine. C312/C313 negative pins contact the B.Cu trunk. The approximately 9.3 A worst initial chopper-bank current gives an ideal local-array loss of {local_r*9.3**2:.4f} W at 100 °C, before spreading and unequal sharing. The B.Cu return is 8 mm wide, and the sampled F.Cu drain exit is {scan('Q40 drain exit','F.Cu')['total_copper_width_mm']:.2f} mm wide; the drain narrows to 3 mm at J12. These geometries do not establish loop inductance, switching overshoot or closed-loop stability. Record Q40 VDS, gate voltage, bus ripple and resistor energy during staged pulse commissioning. NT10 must preserve the short source reference connection without carrying resistor current.

Connected F.Cu copper associated with Q40's drain measures **{drain_area:.2f} mm² ({drain_area/100:.3f} cm²)** after removing holes. The 600 mm² prototype target is geometrically met: **{drain_area>=600}**. The first routed snapshot had approximately 452 mm² and the CAD owner enlarged the pour to address that mismatch. Infineon's published 40 K/W value belongs to its separate 40 × 40 × 1.5 mm vertical still-air test board with one 70 µm, 6 cm² drain-copper layer; it is not automatically transferable to this assembly. See `chopper/ipt015n10n5-primary-source.json`.

DRIVE_N uses an 8 mm F.Cu corridor. LIFT_N uses an 8 mm corridor on each inner layer, with 3 mm terminal approaches. The first routed snapshot severed inner LIFT_N pours with signal traces; protected centerline paths and rerouting were requested. Both inner endpoint paths are restored in the current geometric check: **{lift_ok}**. The lower V5V and LOGIC_5V_N samples retain broad B.Cu paths, and the LED return reaches its dedicated power star rather than NT9.

## Actual via-field arithmetic

The authoritative counts are copied from `design/via-field-counts.json`, not from the earlier 160-via example. Use finished hole diameter d = 0.4 mm, minimum plating t = 0.025 mm, barrel length L = 1.6 mm and rho20 = 1.724 × 10⁻⁸ Ω·m with temperature coefficient 0.00393/K. The thin-wall conservative expression is `R = rho(T) × L / (N × pi × d × t)`. One such barrel is approximately 878 µΩ at 20 °C or 1154 µΩ at 100 °C.

Each table cell gives **20 °C / 100 °C** values. The 50 A and 60 A columns apply that entire current to an ideal parallel field solely for arithmetic comparison.

| Net field | Count | R, µΩ | Loss at 50 A, W | Loss at 60 A, W |
|---|---:|---:|---:|---:|
{chr(10).join(fields)}

The smallest main positive/common field is 104 vias. These low ideal totals do not prove that all barrels participate near one SMD force pad. Contact and spreading resistance can dominate; a single nearest via can carry disproportionate current. A 1.70 mm finished board would increase barrel resistance and these losses by 6.25% with the other assumptions unchanged. Plating coupons, local thermal imaging and four-wire voltage measurements remain release gates.

## Findings and report status

The first routed board, SHA-256 `a5fda347cb9910f0fb1f6774115fe7ddc8b8b0febc5a2a40d5e64ee023662d6b`, contained an isolated RSH2.4 F.Cu force-pad island. Its x = 126 mm sample still showed 3.29 mm of copper, illustrating why width alone was misleading. This was reported to the CAD owner, who protected the force link and the LIFT_N corridors. RSH2.4 and the Q7 drain now share one continuous F.Cu outline: **{rsh_ok}**. The endpoint checks and cross-sections must be refreshed after subsequent routing changes.

Observed `reports/drc-final.json` at `{native['date']}` contains {native['geometry_count']} geometric entries, {native['unconnected_count']} unconnected entries and {native['schematic_parity_count']} parity entries. Its SHA-256 is `{native['sha256']}`.

{manifest_prose}

A complete JSON report and a clean process exit are separate results. The filename alone is not a release declaration. This reviewer did not run ERC/DRC or modify the board. Final native checks, the resolved geometry review, mechanical coupon acceptance and current/temperature qualification are distinct requirements.
'''
(ROOT/'filled-power-copper-review.md').write_text(text,encoding='utf-8')
print('Wrote filled-power-copper-review.md; board',j['board_sha256'])
