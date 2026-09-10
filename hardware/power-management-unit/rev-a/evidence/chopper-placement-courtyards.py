import json,pathlib,pcbnew,math
root=pathlib.Path(__file__).resolve().parents[1]
parts=json.loads((root/'design/chopper-parts.json').read_text())['components'];place=json.loads((root/'design/placement-chopper.json').read_text());lib=pathlib.Path('C:/Users/chrba/Documents/ChatGPT/HomeMy/tools-local/kicad/share/kicad/footprints');boxes={}
for c in parts:
 x,y,angle=place[c['ref']]
 if c['footprint'].startswith('PMU:'):
  boxes[c['ref']]=(x-5.5,y-5.5,x+5.5,y+5.5);continue
 a,b=c['footprint'].split(':');f=pcbnew.FootprintLoad(str(lib/(a+'.pretty')),b);f.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y)));f.SetOrientationDegrees(angle)
 pts=[]
 for g in f.GraphicalItems():
  if g.GetLayer()==pcbnew.F_CrtYd:
   bb=g.GetBoundingBox();pts.extend([(pcbnew.ToMM(bb.GetLeft()),pcbnew.ToMM(bb.GetTop())),(pcbnew.ToMM(bb.GetRight()),pcbnew.ToMM(bb.GetBottom()))])
 if not pts:
  bb=f.GetBoundingBox(False,False);pts=[(pcbnew.ToMM(bb.GetLeft()),pcbnew.ToMM(bb.GetTop())),(pcbnew.ToMM(bb.GetRight()),pcbnew.ToMM(bb.GetBottom()))]
 boxes[c['ref']]=[min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)]
refs=list(boxes);coll=[]
for i,r in enumerate(refs):
 a=boxes[r]
 for s in refs[i+1:]:
  b=boxes[s];ox=min(a[2],b[2])-max(a[0],b[0]);oy=min(a[3],b[3])-max(a[1],b[1])
  if ox>0 and oy>0:
   # ESP courtyard is a stepped polygon, not its rectangular bounding box.
   # At 180deg and(325,280): body x315.25..334.75 y266.55..286.75;
   # antenna free region x301..349 y286.75..307.75.
   if 'U10' in (r,s):
    other=b if r=='U10' else a
    rects=[[315.225,266.525,334.775,286.775],[300.975,286.725,349.025,307.775]]
    if not any(min(q[2],other[2])>max(q[0],other[0]) and min(q[3],other[3])>max(q[1],other[1]) for q in rects):continue
   coll.append([r,s,round(ox,3),round(oy,3)])
(root/'evidence/chopper-placement-courtyard-check.json').write_text(json.dumps({'metadata':{'rev_a_engineering_prototype':True,'rev_b_production':False},'scope':'Own chopper parts only; integrated check remains required','component_count':len(parts),'courtyard_overlaps':coll},indent=2)+'\n')
print(json.dumps(coll),flush=True)
import os
os._exit(1 if coll else 0)
