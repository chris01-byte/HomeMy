from pathlib import Path
import json,sys,hashlib,math
from power_native_reader import main,pcb
Q=Path('<SITZUNG>/agents/evidence/repro/tmp-power');R=Path('<SITZUNG>/agents/evidence/repro/hardware/power-management-unit/rev-a2-layout-280x260');historic=json.loads((R/'reports/power-and-critical.json').read_text());oldfill=json.loads((R/'reports/filled-copper-review.json').read_text());b,polys,paths,zones,tap_ids,digest=main();native_ids={t.m_Uuid.AsString() for t in b.GetTracks()}
key=lambda r:(r['net'],r['layer'],r['from_pad'],r['to_pad'])
assert [key(r) for r in paths]==[key(r) for r in historic['power']['paths']]
def rings(poly):
 out=[]
 for i in range(poly.OutlineCount()):
  for r in [poly.COutline(i)]+[poly.CHole(i,k) for k in range(poly.HoleCount(i))]:out.append([(r.CPoint(k).x/1e6,r.CPoint(k).y/1e6) for k in range(r.PointCount())])
 return out
def scan(lines,axis,lo,hi,w0,w1):
 a=0 if axis=='x' else 1;b=1-a;edges=[]
 for ring in lines:
  for u,v in zip(ring,ring[1:]+ring[:1]):
   if abs(u[a]-v[a])<1e-12:continue
   if u[a]>v[a]:u,v=v,u
   if v[a]<=lo or u[a]>hi:continue
   edges.append((u[a],v[a],u[b],(v[b]-u[b])/(v[a]-u[a])))
 edges.sort();active=[];idx=0;minimum=None;minlarge=None;zero=0;values=[]
 for k in range(round((hi-lo)/.01)+1):
  z=round(lo+k*.01,8)
  while idx<len(edges) and edges[idx][0]<=z:active.append(edges[idx]);idx+=1
  active=[e for e in active if e[1]>z];cuts=sorted(e[2]+(z-e[0])*e[3] for e in active);assert len(cuts)%2==0
  ints=[[max(w0,x),min(w1,y)] for x,y in zip(cuts[::2],cuts[1::2]) if min(w1,y)>max(w0,x)+1e-9];widths=[b-a for a,b in ints];total=sum(widths);largest=max(widths,default=0);values.append([z,round(total,7),round(largest,7)])
  if total<=1e-8:zero+=1
  row={'at_mm':z,'sum_mm':round(total,7),'largest_interval_mm':round(largest,7),'intervals_mm':[[round(a,7),round(b,7)] for a,b in ints]}
  if minimum is None or total<minimum['sum_mm']-1e-7:minimum=row
  if minlarge is None or largest<minlarge['largest_interval_mm']-1e-7:minlarge=row
 return dict(minimum_sum=minimum,minimum_largest_interval=minlarge,zero_sections=zero,sections=len(values))
regions=[];matches=[]
for old in oldfill['current']['regions']:
 row={k:old[k] for k in ['name','net','layer','scan_axis','scan_range_mm','window_mm']};poly=polys[(row['net'],b.GetLayerID(row['layer']))];row.update(scan(rings(poly),row['scan_axis'],*row['scan_range_mm'],*row['window_mm']));regions.append(row);matches.append(dict(name=row['name'],matches_historic_saved_geometry=row==old))
result=dict(pcb_sha256=digest,power_pairs=len(paths),power_passed=sum(r['same_continuous_copper_outline'] for r in paths),paths=paths,zones=zones,native_unconnected=b.GetConnectivity().GetUnconnectedCount(False),tap_inventory_uuid_count=len(tap_ids),tap_objects_actually_present_and_omitted=len(tap_ids&native_ids),required_pair_set_matches_source_and_historic=True,filled_regions=regions,historic_region_comparison=matches,method='Fresh KiCad native saved filled polygons plus effective pads/tracks, excluding enumerated tap UUID union and own drill interiors. Original source247 required pad pairs; new 0.01mm orthogonal scans reproduce18 recorded windows. Historic pass booleans are never used for fresh results.',limits=['Same-layer geometric continuity does not by itself establish minimum width, current capacity or physical contact quality.','Widths are sampled windows, not global all-angle minimum cuts or thermal/current measurements.','No external busbar is added to native copper geometry.','Tap inventory includes removed historic IDs; actual omitted native objects are separately counted.']);result['passed']=result['power_pairs']==result['power_passed']==247 and result['native_unconnected']==0 and all(x['matches_historic_saved_geometry'] for x in matches)
assert hashlib.sha256((R/'kicad/HomeMy_PMU_RevA.kicad_pcb').read_bytes()).hexdigest()==digest
Path(sys.argv[1]).write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['paths','zones','filled_regions','historic_region_comparison','method','limits']},indent=2));sys.exit(0 if result['passed'] else 2)
