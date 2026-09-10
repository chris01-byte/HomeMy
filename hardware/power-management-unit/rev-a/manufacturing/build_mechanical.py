"""Reproducible mechanical proposal. Does not modify native PCB files."""
from pathlib import Path
import json, math, hashlib

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent
geometry_path=ROOT/'reports'/'board-pad-geometry.json'
geometry=json.loads(geometry_path.read_text())
parts={p['ref']:p for p in geometry}
def rect(x1,y1,x2,y2): return [[x1,y1],[x2,y1],[x2,y2],[x1,y2]]
bars=[]
contacts=[]
def contact(ref,net,x,y,bar):
    p={'ref':ref,'net':net,'x':x,'y':y,'rotation':0,'bar':bar,
       'pad_number':'1','pad_type':'thru_hole','pad_shape':'circle',
       'pad_diameter_mm':8.0,'finished_drill_mm':3.2,'drill_tolerance_mm':0.1,
       'minimum_barrel_copper_um':25,'layers':['*.Cu','*.Mask'],
       'mask_opening_diameter_mm':8.2,'paste':False,
       'copper_connection':'solid; no thermal relief',
       'top_fastener_keepout_diameter_mm':9.0,
       'notes':'Conductive M3 clamp on own net; annular Cu contact carries current, screw ampacity not credited.'}
    contacts.append(p)
    return ref
def bar(ref,net,poly,points,min_width):
    b={'ref':ref,'net':net,'material':'Cu-ETP / CW004A, conductivity certificate required',
       'thickness_mm':2.0,'thickness_tolerance_mm':0.1,'outline':poly,
       'outline_tolerance_mm':0.2,'hole_position_tolerance_mm':0.1,
       'mounting_side':'B.Cu underside','contact_refs':[],
       'holes':[],'cutouts':[],'minimum_unperforated_width_mm':min_width,
       'insulation':'0.20 mm PET/polyimide sheet, no adhesive in contact windows; Cu contact shim OD8/ID3.4/thickness0.25 mm bridges film stand-off; see assembly document'}
    for x,y in points:
        r='BC'+str(len(contacts)+1)
        b['contact_refs'].append(contact(r,net,x,y,ref))
        b['holes'].append({'x':x,'y':y,'diameter_mm':3.4,'function':r})
    bars.append(b)
    return b
bar('BB1','BATT_SENSED_P',rect(37,14,49,86),[(43,20),(43,78)],12)
bar('BB2','MAIN_COMMON',rect(65,14,75,86),[(70,26),(70,74)],10)
bar('BB3','SYS_BUS_P',rect(94,14,106,74),[(100,25),(100,55)],12)
bar('BB4','MOTION_SENSED_P',rect(129,19,141,79),[(135,25),(135,65)],12)
bar('BB5','MOTION_COMMON',rect(160,19,170,79),[(165,28),(165,48)],10)
b=bar('BB6','MOTION_BUS_P',[[188,8],[278,8],[278,32],[202,32],[202,87],[188,87]],[(195,42),(195,72),(235,20),(272,20)],12)
for ref in ('J3','J5'):
    p=parts[ref]
    b['cutouts'].append({'outline':rect(p['x']-6,p['y']-6,p['x']+6,p['y']+6),'reason':ref+' all eight pressfit tails; no bar contact to pin ends','corner_radius_mm':1})
b=bar('BB7','BATT_N',rect(8,105,356,136),[(27,110)],16)
for ref in ('J2','J4','J6'):
    p=parts[ref]
    b['cutouts'].append({'outline':rect(p['x']-6,p['y']-6,p['x']+6,p['y']+6),'reason':ref+' pressfit tails; never clamp on pin ends','corner_radius_mm':1})
nt_specs=[]
for i in range(1,9):
    p=parts['NT'+str(i)]
    pp={n['number']:n for n in p['pads']}
    a,d=pp['1'],pp['2']
    spec={'ref':p['ref'],'preserve_existing_net_tie_group':'1,2',
          'position':[p['x'],p['y']],
          'replace_pad_1_and_2_with':[
              {'number':q['number'],'net':q['net'],'x':q['x'],'y':q['y'],
               'pad_shape':'rect','pad_size_mm':[10,10],'finished_drill_mm':3.2,
               'drill_tolerance_mm':0.1,'pad_type':'thru_hole','layers':['*.Cu','*.Mask'],
               'minimum_barrel_copper_um':25,'paste':False,'mask_margin_mm':0.1,
               'copper_connection':'solid; retain intentional F.Cu bridge within net-tie footprint'} for q in (a,d)],
          'top_bridge':{'ref':'NB'+str(i),'outline':rect(p['x']-10,p['y']-5,p['x']+10,p['y']+5),
                        'material':'Cu-ETP / CW004A','thickness_mm':2,
                        'holes':[{'x':q['x'],'y':q['y'],'diameter_mm':3.4} for q in (a,d)]},
          'assembly':'Top copper bridge contacts both own net-tie pads. Branch-side screw clamps separate underside Cu washer OD8/ID3.4/thickness1 in BB7 cutout; BATT_N-side screw clamps BB7. No branch-side screw/washer contact to BB7.'}
    nt_specs.append(spec)
    b['cutouts'].append({'outline':rect(a['x']-6,a['y']-6,a['x']+6,a['y']+6),'reason':p['ref']+'.1 branch washer/nut isolated from BB7; bridge only on top','corner_radius_mm':1})
    b['holes'].append({'x':d['x'],'y':d['y'],'diameter_mm':3.4,'function':p['ref']+'.2'})
    b['contact_refs'].append(p['ref']+'.2')

# Prototype dimension checks are explicit and limited: no DRC or enclosure proof.
near=[]
for c in contacts:
    for p in geometry:
        if p['ref']==c['ref']:
            continue
        for q in p['pads']:
            # Bounding-circle enlargement safely covers rotated rectangular pad geometry.
            radius=math.hypot(q['width'],q['height'])/2
            gap=math.hypot(c['x']-q['x'],c['y']-q['y'])-4.5-radius
            if gap<0.5:
                near.append({'contact':c['ref'],'part':p['ref'],'pad':q['number'],'net':q['net'],
                             'conservative_clearance_mm':round(gap,3)})
data={'metadata':{'rev_a_engineering_prototype':True,'rev_b_production':False,
                  'status':'Manufacturing proposal requiring CAD integration and checked first article; no 50/60 A or DRC release',
                  'units':'mm','coordinate_system':'PCB top-view origin upper-left, +x right, +y down; underside parts shown without mirroring',
                  'geometry_source':str(geometry_path.relative_to(ROOT)),
                  'geometry_sha256':hashlib.sha256(geometry_path.read_bytes()).hexdigest()},
      'contact_shim':{'material':'Cu-ETP','outer_diameter_mm':8,'inner_diameter_mm':3.4,'thickness_mm':0.25,'thickness_tolerance_mm':0.02,'quantity':23,'location':'All15 BC underside contacts and8 NT*.2 underside contacts; mandatory to clear0.20mm insulation sheet'},
      'mechanical_bom_source':'MECHANICAL_CATALOG_BOM.json',
      'film':{'manufacturer':'Goodfellow','mpn':'IM30-FM-000200','order_code':'312-663-72','grade':'DuPont Kapton HN','sheet_size_mm':[500,500],'sheet_thickness_mm':0.05,'layers_under_each_bar':4,'nominal_stack_mm':0.20,'incoming_maximum_stack_mm':0.22,'notes':'Cut all layers continuously per bar; reject overthick stack; Cu shim minimum0.23mm must stand proud.'},
      'board':{'size_mm':[360,300],'finished_thickness_mm':1.6,'finished_thickness_tolerance_mm':[0,0.1],
               'outer_copper_min_um':70,'inner_copper_min_um':35},
      'new_pcb_contacts':contacts,'net_tie_modifications':nt_specs,'busbars':bars,
      'component_pad_clearance_screen':near,
      'required_parent_cad_actions':[
          'Add all BC contacts to electrical source as testpoint/mechanical single-net parts, including BOM DNP/no purchased component notation.',
          'Replace NT1..NT8 pad holes as specified; preserve original net identities and explicit bridge.',
          'Keep B.Cu bars electrically insulated everywhere except listed contact lands; do not use PCB mask as sole insulation.',
          'Recompute full-current via groups after holes/keepouts; previous fields156/154/229/180/157/245 do not meet assumed160 in every field.',
          'CHOPPER_N must cover Q40 source west bank x295.35..298.15,y31.6..39.6, reach NT10(299,44), both capacitor negatives(299,17)/(316,17), and NT7.1(340,122). Existing x300..313 rectangle misses source.',
          'J18.3 and C246 negative use LOGIC_5V_N, direct broad return to NT8; no LED force current through NT9.',
          'Review horizontal M5 lug and tool access for all right-angle7461103 terminals; 9x9 footprint alone is not harness envelope.']}
(HERE/'busbar-pcb-interface.json').write_text(json.dumps(data,indent=2)+'\n')

rho=1.724e-8*(1+.00393*80)
calcs=[]
for name,length,width,t in [('BB1',72,12,2),('BB2',72,10,2),('BB3',60,12,2),('BB4',60,12,2),('BB5',60,10,2),('BB6 bounding path',160,12,2),('BB7 conservative neck',348,16,2),('NB1..8',10,10,2),('PCB local force neck one layer',6,5.6,.07),('PCB local force neck two layers ideal',6,5.6,.14),('PCB20mm dual outer',100,20,.14)]:
    R=rho*length/(width*t)*1000
    area=width*t
    heatcap=length*width*t/1000*8.96*.385
    calcs.append({'item':name,'length_mm':length,'width_mm':width,'thickness_mm':t,
                  'section_mm2':area,'R_100C_ohm':R,
                  'loss_W':{str(i):i*i*R for i in [25,50,60,150]},
                  'adiabatic_150A_3s_delta_K':150**2*R*3/heatcap})
for d,n in [(.4,160),(.4,154),(3.2,1)]:
    A=math.pi*d*.025
    r=rho*1.7/(A*n)*1000
    calcs.append({'item':f'{n} plated holes diameter{d}mm,25um,1.7mm PCB',
                  'R_100C_ohm':r,'loss_W':{str(i):i*i*r for i in [25,50,60,150]},
                  'assumption':'Uniform current sharing; excludes constriction resistance and annular-pad spreading.'})
(HERE/'busbar-calculations.json').write_text(json.dumps({'metadata':{'rev_a_engineering_prototype':True,'rev_b_production':False},'rho100_ohm_m':rho,'models':calcs,
 'thermal_note':'Convection and radiation not included in adiabatic estimate. Steady-state hot-spot limits require measured thermal resistance; losses alone are not ampacity.'},indent=2)+'\n')

svg=['<svg xmlns="http://www.w3.org/2000/svg" width="400mm" height="190mm" viewBox="-20 -18 400 190">',
 '<style>text{font-family:monospace;font-size:2.5px} .bar{fill:#dfa56b;stroke:#5e3517;stroke-width:.3} .cut{fill:white;stroke:#bd2b2b;stroke-width:.25} .hole{fill:white;stroke:#222;stroke-width:.25}</style>',
 '<text x="0" y="-12" style="font-size:4px">PMU Rev A — busbar manufacturing proposal, scale 1:1</text>',
 '<text x="0" y="-7">Top-view XY; underside parts NOT mirrored. mm. Cu-ETP 2.0±0.1. No electrical qualification.</text>',
 '<path d="M0,150 V0 H360 V150" fill="none" stroke="#444" stroke-width=".4"/>']
for b in bars:
    svg.append('<polygon class="bar" points="'+' '.join(f'{x},{y}' for x,y in b['outline'])+'"/>')
    for co in b['cutouts']:
        svg.append('<polygon class="cut" points="'+' '.join(f'{x},{y}' for x,y in co['outline'])+'"/>')
    for h in b['holes']:
        svg.append(f'<circle class="hole" cx="{h["x"]}" cy="{h["y"]}" r="1.7"/>')
    x,y=b['outline'][0]
    svg.append(f'<text x="{x+1}" y="{y+3}">{b["ref"]}</text>')
for n in nt_specs:
    x,y=n['position']
    svg.append(f'<rect x="{x-10}" y="{y-5}" width="20" height="10" fill="none" stroke="#266297" stroke-width=".3" stroke-dasharray="1,1"/>')
    svg.append(f'<text x="{x-8}" y="{y+9}">{n["top_bridge"]["ref"]}</text>')
for c in contacts:
    svg.append(f'<text x="{c["x"]+2}" y="{c["y"]-1}">{c["ref"]}</text>')
svg.extend(['<path d="M0,159 h100 m-100,-2 v4 m100,-4 v4" stroke="black" stroke-width=".3"/>',
            '<text x="25" y="165">100 mm calibration — print at100%, do not fit</text>',
            '<text x="160" y="158">HolesØ3.4±0.1; contour±0.2; hole position±0.1</text>',
            '<text x="160" y="163">Coordinates and cutouts: busbar-pcb-interface.json</text>',
            '<text x="160" y="168">Blue dashed: TOP net-tie bridges NB1..NB8</text>','</svg>'])
(HERE/'BUSBAR_TOP_VIEW_1to1.svg').write_text('\n'.join(svg),encoding='utf-8')
try:
    from PIL import Image, ImageDraw, ImageFont
    s=4
    im=Image.new('RGB',(1600,760),'white'); draw=ImageDraw.Draw(im)
    font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',12)
    def xy(x,y):return ((x+20)*s,(y+18)*s)
    draw.text(xy(0,-12),'PMU Rev A busbar proposal — XY top view, not mirrored',fill='black',font=font)
    draw.line([xy(0,150),xy(0,0),xy(360,0),xy(360,150)],fill='#444444',width=2)
    for b in bars:
        draw.polygon([xy(*p) for p in b['outline']],fill='#dfa56b',outline='#5e3517')
        for co in b['cutouts']:
            draw.polygon([xy(*p) for p in co['outline']],fill='white',outline='#bd2b2b')
        for h in b['holes']:
            x,y=h['x'],h['y'];draw.ellipse([xy(x-1.7,y-1.7),xy(x+1.7,y+1.7)],fill='white',outline='black')
        x,y=b['outline'][0];draw.text(xy(x+1,y+1),b['ref'],fill='black',font=font)
    for n in nt_specs:
        x,y=n['position'];draw.rectangle([xy(x-10,y-5),xy(x+10,y+5)],outline='#266297',width=2)
        draw.text(xy(x-8,y+6),n['top_bridge']['ref'],fill='#266297',font=font)
    for c in contacts:
        draw.text(xy(c['x']+2,c['y']-3),c['ref'],fill='black',font=font)
    draw.line([xy(0,159),xy(100,159)],fill='black',width=2)
    draw.text(xy(20,161),'100 mm calibration; SVG controls scale',fill='black',font=font)
    im.save(HERE/'BUSBAR_PREVIEW.png')
except ImportError:
    pass
print(json.dumps({'bars':len(bars),'contacts':len(contacts),'net_tie_bridges':len(nt_specs),'conservative_pad_near_hits':near},indent=2))
