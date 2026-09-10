"""Read-only footprint orientation evidence; creates documentation, no CAD edits."""
from pathlib import Path
import json,sys,math,hashlib,html,collections
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from sexpr import parse,children,child,unquote
board=ROOT/'kicad'/'HomeMy_PMU_RevA.kicad_pcb'
blob=board.read_bytes();ast=parse(blob.decode('utf-8'))
refs=[f'Q{i}' for i in range(1,11)]+['Q40','RSH1','RSH2','U1']+[f'J{i}' for i in range(1,7)]
out={}
for f in children(ast,'footprint'):
    properties={unquote(p[1]):unquote(p[2]) for p in children(f,'property')}
    ref=properties.get('Reference')
    if ref not in refs:continue
    at=child(f,'at');x,y=map(float,at[1:3]);rotation=float(at[3]) if len(at)>3 else 0
    c,s=math.cos(math.radians(rotation)),math.sin(math.radians(rotation))
    def xy(a,b):return [round(x+c*a+s*b,6),round(y-s*a+c*b,6)]
    pads=[]
    for p in children(f,'pad'):
        pa=child(p,'at');px,py=map(float,pa[1:3]);net=child(p,'net')
        size=child(p,'size');drill=child(p,'drill')
        pads.append({'number':unquote(p[1]),'xy_mm':xy(px,py),'local_xy_mm':[px,py],'local_size_mm':list(map(float,size[1:3])),'rotation_deg':float(pa[3]) if len(pa)>3 else 0,'net':unquote(net[-1]) if net else None,'drill_mm':float(drill[1]) if drill and len(drill)==2 else None})
    graphics=[]
    for g in f:
        if not isinstance(g,list) or not g or g[0] not in ['fp_line','fp_rect','fp_poly','fp_circle','fp_arc','fp_text']:continue
        layer=child(g,'layer')
        if not layer or unquote(layer[1]) not in ['F.Fab','F.SilkS']:continue
        graphics.append({'kind':g[0],'layer':unquote(layer[1]),'native_sexpr':g})
    out[ref]={'footprint':unquote(f[1]),'xy_mm':[x,y],'rotation_deg':rotation,'pads':pads,'graphics':graphics}
direction_notes=[]
for g in children(ast,'gr_text'):
    layer=child(g,'layer')
    if layer and unquote(layer[1])=='F.Fab':
        direction_notes.append({'text':unquote(g[1]),'at':child(g,'at')[1:]})
checks=[]
def texts(ref):
    return {unquote(g['native_sexpr'][2]) for g in out[ref]['graphics'] if g['kind']=='fp_text'}
def add(ref,description,passed):
    checks.append({'ref':ref,'check':description,'passed':bool(passed)})
for ref in [f'Q{i}' for i in range(1,11)]:
    gs=[g['native_sexpr'] for g in out[ref]['graphics'] if g['layer']=='F.Fab']
    body=any(g[0]=='fp_rect' and list(map(float,child(g,'start')[1:]))==[-6,-4.7] and list(map(float,child(g,'end')[1:]))==[6,4.7] for g in gs)
    index=any(g[0]=='fp_circle' and list(map(float,child(g,'center')[1:]))==[-5.3,4.05] for g in gs)
    add(ref,'12 × 9.4 mm body, gate index and explicit source/drain Fab labels',body and index and {'1 G','S 2-6','D 7-12 / 13'}<=texts(ref))
add('U1','Pin-1 Fab marker and floating exposed-pad/no-via labels',{'1','EP25 FLOAT','NO VIA'}<=texts('U1') and any(g['kind']=='fp_line' for g in out['U1']['graphics']))
for ref in ['RSH1','RSH2']:
    add(ref,'Sense/force Fab labels and split-terminal guides',{'SENSE 2 / 3','1 FORCE','4 FORCE'}<=texts(ref) and sum(g['kind']=='fp_line' for g in out[ref]['graphics'])>=4)
for ref in [f'J{i}' for i in range(1,7)]:
    face='+Y' if ref in ['J4','J6'] else '-Y'
    add(ref,'Generic screw axis plus board-specific M5 face '+face,'M5 AXIS' in texts(ref) and sum(g['kind']=='fp_line' for g in out[ref]['graphics'])>=6 and any(g['text']==f'{ref} M5 FACE {face}' for g in direction_notes))
add('Q40','Existing gate silk triangle and chamfered Fab outline',any(g['kind']=='fp_poly' and g['layer']=='F.SilkS' for g in out['Q40']['graphics']) and sum(g['kind']=='fp_line' and g['layer']=='F.Fab' for g in out['Q40']['graphics'])==5)
data={'metadata':{'rev_a_engineering_prototype':True,'rev_b_production':False},'input_board_sha256':hashlib.sha256(blob).hexdigest(),'board_unchanged':hashlib.sha256(board.read_bytes()).hexdigest()==hashlib.sha256(blob).hexdigest(),'view':'Top/component side; +X right, +Y down; KiCad rotation copied from native board.','components':out,'board_fab_direction_notes':direction_notes,'graphical_checks':checks,'required_graphical_improvements':[c['ref']+': '+c['check'] for c in checks if not c['passed']],'limitation':'Read-only drawing and pad-orientation review; no assembly, process or physical thermal qualification.'}
(ROOT/'manufacturing'/'assembly-orientation.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
# Supplemental magnified top-view pad plan, deliberately separate from native FP.
sv=['<svg xmlns="http://www.w3.org/2000/svg" width="420mm" height="297mm" viewBox="0 0 420 297">','<rect width="420" height="297" fill="white"/>','<style>text{font-family:Arial,sans-serif;fill:#17232e}.title{font-size:6px;font-weight:bold}.note{font-size:3px}.pad{font-size:2.5px;font-weight:bold;text-anchor:middle;dominant-baseline:middle}</style>','<text x="10" y="10" class="title">Rev A assembly orientation — supplemental top-view pad plan</text>','<text x="10" y="17" class="note">Magnified documentation; not a stencil, copper layer or replacement footprint. +X right, +Y down.</text>']
samples=['Q1','Q4','Q7','Q9','Q40','RSH1','RSH2','U1','J1','J4']
for i,ref in enumerate(samples):
    d=out[ref];col=i%5;row=i//5;ox=42+col*83;oy=80+row*119
    scale=4 if ref!='U1' else 8
    sv.append(f'<text x="{ox-33}" y="{oy-46}" class="title">{ref} · {d["rotation_deg"]:g}°</text>')
    sv.append(f'<text x="{ox-33}" y="{oy-40}" class="note">Origin {d["xy_mm"][0]:g}, {d["xy_mm"][1]:g} mm</text>')
    # Draw physical pad rectangles at their native orientation. Q40's custom
    # source/drain polygons are simplified to main pad rectangles in this view.
    for p in sorted(d['pads'],key=lambda p:-(p['local_size_mm'][0]*p['local_size_mm'][1])):
        if not p['number']:continue
        px=ox+(p['xy_mm'][0]-d['xy_mm'][0])*scale;py=oy+(p['xy_mm'][1]-d['xy_mm'][1])*scale
        w,h=p['local_size_mm'];w*=scale;h*=scale
        angle=-p['rotation_deg']
        fill='#f4cb91' if p['number']!='1' else '#e98076'
        if p['number']=='25':fill='#d9d9df'
        if p['drill_mm'] and abs(w-h)<.01:
            sv.append(f'<circle cx="{px:.3f}" cy="{py:.3f}" r="{w/2:.3f}" fill="{fill}" stroke="#735a37" stroke-width="0.18"/>')
        else:
            sv.append(f'<rect x="{px-w/2:.3f}" y="{py-h/2:.3f}" width="{w:.3f}" height="{h:.3f}" fill="{fill}" stroke="#735a37" stroke-width="0.18" transform="rotate({angle:g} {px:.3f} {py:.3f})"/>')
        if p['drill_mm']:sv.append(f'<circle cx="{px:.3f}" cy="{py:.3f}" r="{p["drill_mm"]*scale/2:.3f}" fill="white" stroke="#735a37" stroke-width="0.15"/>')
        sv.append(f'<text x="{px:.3f}" y="{py:.3f}" class="pad">{p["number"]}</text>')
    note={'Q1':'G1 east/south; source east; drain west','Q4':'G1 west/north; source west; drain east','Q7':'G1 east/south; source east; drain west','Q9':'G1 west/north; source west; drain east','Q40':'G1 upper left; S2 left; D3 right','RSH1':'Sense 2/3 north; force 1/4 south','RSH2':'Sense 2/3 north; force 1/4 south','U1':'Pin 1 upper left; pad 25 FLOAT','J1':'Manual screw face −Y (north)','J4':'Manual screw face +Y (south)'}[ref]
    sv.append(f'<text x="{ox-37}" y="{oy+38}" class="note">{html.escape(note)}</text>')
sv.extend(['<text x="10" y="287" class="note">Q40 custom land contours are simplified here. Use native pad-number view for exact land shape; use manufacturer drawing for body index.</text>',f'<text x="10" y="292" class="note">Board SHA-256: {data["input_board_sha256"]}</text>','</svg>'])
svg='\n'.join(sv)
svg=svg.replace('class="title"','font-family="Arial,sans-serif" font-size="6" font-weight="bold"')
svg=svg.replace('class="note"','font-family="Arial,sans-serif" font-size="3"')
svg=svg.replace('class="pad"','font-family="Arial,sans-serif" font-size="2.5" font-weight="bold" text-anchor="middle" dominant-baseline="middle"')
(ROOT/'manufacturing'/'ASSEMBLY_ORIENTATION.svg').write_text(svg,encoding='utf-8')
print(json.dumps({r:{'xy':d['xy_mm'],'rotation':d['rotation_deg'],'pin1':next(p['xy_mm'] for p in d['pads'] if p['number']=='1'),'graphics':dict(collections.Counter(g['layer']+'/'+g['kind'] for g in d['graphics']))} for r,d in out.items()},indent=2))
