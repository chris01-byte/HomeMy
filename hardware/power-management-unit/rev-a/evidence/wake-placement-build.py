import json,pathlib,math,pcbnew
root=pathlib.Path(__file__).resolve().parents[1]
parts=json.loads((root/'design/wake-io-parts.json').read_text())['components']
place=json.loads("{\"U10\":[325,280,180],\"U11\":[25,75,0],\"U12\":[288,242,0],\"U13\":[43,276,0],\"U14\":[98,276,0],\"U15\":[28,210,0],\"U16\":[66,234,0],\"U17\":[43,210,0],\"U18\":[43,224,0],\"U19\":[54,224,0],\"U20\":[25,236,0],\"U21\":[88,246,0],\"U22\":[103,234,0],\"U23\":[130,231,0],\"U24\":[118,218,0],\"U25\":[140,244,0],\"U26\":[304,245,0],\"U27\":[208,195,0],\"U28\":[165,190,0],\"U29\":[187,218,0],\"U50\":[190,195,0],\"U51\":[225,224,0],\"U53\":[129,210,0],\"U54\":[225,183,0],\"U55\":[110,248,0],\"U56\":[124,248,0],\"U57\":[133,248,0],\"U58\":[130,220,0],\"U59\":[34,236,0],\"U60\":[292,196,0],\"U61\":[269,243,0],\"U62\":[89,218,0],\"U63\":[105,218,0],\"U64\":[79,234,0],\"U65\":[289,271,0],\"Q20\":[137,231,0],\"Q21\":[90,276,0],\"R200\":[17,207,90],\"R201\":[17,216,90],\"R202\":[32,215,0],\"R203\":[28,219,0],\"C200\":[23,209,180],\"C201\":[33,209,0],\"R204\":[20,230,90],\"R205\":[20,236,0],\"C202\":[24,232,90],\"C203\":[62,238,180],\"C204\":[71,231,0],\"R206\":[72,239,90],\"R207\":[79,239,90],\"R208\":[84,250,180],\"R209\":[93,242,90],\"R210\":[94,250,0],\"R211\":[95,231,0],\"R212\":[98,234,90],\"R213\":[110,235,0],\"R214\":[116,235,90],\"R215\":[124,207,90],\"R216\":[140,251,90],\"R217\":[299,245,90],\"R218\":[309,249,0],\"R219\":[338,284,90],\"R220\":[312,269,0],\"R221\":[322,263,0],\"R222\":[320,258,90],\"C237\":[280,247,90],\"C238\":[295,242,0],\"C239\":[341,282,90],\"C240\":[340,286,0],\"R223\":[32,71,90],\"R224\":[36,72,90],\"C241\":[30,73.2,90],\"R225\":[36,76,180],\"C242\":[31,77,0],\"R226\":[314,263,90],\"R227\":[316.7,263,90],\"R228\":[23,81,90],\"R229\":[159,186,90],\"R230\":[159,190,90],\"R231\":[166,184,0],\"R232\":[170,184,0],\"R233\":[230,221,90],\"R234\":[222,177,90],\"R235\":[203,191,90],\"R236\":[230,226,90],\"R237\":[229,189,90],\"R238\":[263,245,90],\"R239\":[262,239,0],\"C243\":[265,241,90],\"R240\":[212,200,0],\"R241\":[37,273,90],\"R242\":[49,270,90],\"D40\":[25,276,90],\"R243\":[30,272,0],\"R244\":[30,280,0],\"C244\":[33,276,90],\"R245\":[21,285,0],\"C245\":[21,289,0],\"R246\":[95,272,90],\"R247\":[93,280,0],\"R248\":[103,278,0],\"R249\":[107,282,90],\"C246\":[117,279,0],\"R250\":[272,180,90],\"R251\":[272,185,90],\"R252\":[276,188,90],\"C247\":[280,190,0],\"R253\":[285,194,90],\"C248\":[286,191,0],\"R254\":[272,204,90],\"R255\":[272,199,90],\"R256\":[276,197,90],\"C249\":[280,199,0],\"R257\":[284,200,90],\"C250\":[288,202,0],\"R258\":[300,202,90],\"C251\":[300,198,0],\"R259\":[299,192,90],\"R260\":[62,53,0],\"TH20\":[68,50,90],\"C252\":[65,56,0],\"R261\":[162,72,90],\"TH21\":[164,65,90],\"C253\":[168,70,0],\"J20\":[16,246,0],\"J21\":[274,267,0],\"J22\":[257,234,0],\"J23\":[133,278,0],\"R262\":[83,215,90],\"C254\":[84,220,90],\"R263\":[283,266,90],\"R264\":[283,274,90]}")
lib=pathlib.Path('C:/Users/chrba/Documents/ChatGPT/HomeMy/tools-local/kicad/share/kicad/footprints')
place.update({'Q20':[140,231,0],'C201':[35.8,212,0],'R213':[111,237,0],'R219':[338,278,90],'C240':[340,276,0],'C242':[32,79,0],'C237':[280,250,90],'R259':[301,189,90]})
byref={c['ref']:c for c in parts}
place['C240']=[340,274,0]
place.update({'R223':[38,69,90],'R260':[69,54,0],'C252':[69,57,0],'R261':[164,75,0],'C253':[166,79,0],'C246':[132,270,0],'R249':[111,279,90]})
fps={}
for c in parts:
 if c['footprint'].startswith('PMU:'):continue
 a,b=c['footprint'].split(':')
 fps[c['ref']]=pcbnew.FootprintLoad(str(lib/(a+'.pretty')),b)
owner={}
for c in parts:
 if c['ref'].startswith('C') and c['notes'].startswith('Local bypass forU'):
  owner[c['ref']]=c['notes'].replace('Local bypass for','')
owner.update({'C236':'U13','C255':'U62','C256':'U63','C257':'U64','C258':'U65'})
cap_evidence=[]
for cref,uref in owner.items():
 ic=byref[uref]; rail=byref[cref]['pins']['1']
 pin=next(k for k,v in ic['pins'].items() if v==rail and ic.get('pin_types',{}).get(k)=='power_in') if any(v==rail and ic.get('pin_types',{}).get(k)=='power_in' for k,v in ic['pins'].items()) else next(k for k,v in ic['pins'].items() if v==rail)
 if uref=='U51':
  p=next(p for p in ic['pad_geometry_mm']['pads'] if str(p['number'])==pin);px,py=p['x'],p['y']
 else:
  p=next(p for p in fps[uref].Pads() if p.GetNumber()==pin);px,py=pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y)
 x,y,a=place[uref];theta=math.radians(a)
 gx=x+px*math.cos(theta)+py*math.sin(theta);gy=y-px*math.sin(theta)+py*math.cos(theta)
 # Place capacitor radially outboard of package; power pad faces supply pin.
 side=1 if (gx-x)>=0 else -1
 offset=3.05 if uref=='U12' else 3.0 if uref=='U13' else 2.9
 cx=gx+side*offset;cy=gy;ca=0 if side>0 else 180
 place[cref]=[round(cx,4),round(cy,4),ca]
 cap=fps[cref];cap.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(cx),pcbnew.FromMM(cy)));cap.SetOrientationDegrees(ca)
 cp=next(p for p in cap.Pads() if p.GetNumber()=='1').GetPosition()
 distance=math.hypot(pcbnew.ToMM(cp.x)-gx,pcbnew.ToMM(cp.y)-gy)
 # Copper-edge distance is less than pad-center distance by at least the capacitor pad half-width.
 cap_evidence.append({'capacitor':cref,'owner':uref,'supply_pin':pin,'supply_pad_mm':[gx,gy],'capacitor_power_pad_center_distance_mm':round(distance,4),'upper_bound_copper_edge_distance_mm':round(distance-0.55,4)})
assert set(place)==set(byref),(set(byref)-set(place),set(place)-set(byref))
assert all(0<x<360 and 0<y<300 for x,y,a in place.values())
assert all(c['upper_bound_copper_edge_distance_mm']<2 for c in cap_evidence)
(root/'design/placement-wake.json').write_text(json.dumps(place,indent=2)+'\n')
(root/'evidence/wake-placement-bypass-check.json').write_text(json.dumps({'scope':'Initial placement; not a routed-board DRC or thermal validation','all_168_refs_placed':len(place),'bypasses':cap_evidence},indent=2)+'\n')
print(json.dumps({'placed':len(place),'bypasses':len(cap_evidence),'max_supply_copper_edge_distance_mm':max(c['upper_bound_copper_edge_distance_mm'] for c in cap_evidence)}),flush=True)
import os
os._exit(0)
