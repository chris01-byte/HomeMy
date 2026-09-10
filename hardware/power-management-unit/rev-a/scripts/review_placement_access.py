"""Read-only native geometry/access review; never fill, move, route or save CAD.

Default outputs are interim evidence. Use --final-snapshot only after routing
and assembly annotations are stable; that explicitly binds the final PCB hash.
The 3 mm probe and 20 mm connector envelopes are nominal 2D planning screens,
not measured tool, harness or enclosure volumes.
"""
from pathlib import Path
import argparse
import hashlib
import itertools
import json
import math
import traceback

import pcbnew as pcb
from build_board import force_exit

ROOT = Path(__file__).resolve().parents[1]
LAYERS = [pcb.F_Cu, pcb.In1_Cu, pcb.In2_Cu, pcb.B_Cu]
M5_FACES = {'J1':-1, 'J2':-1, 'J3':-1, 'J4':1, 'J5':-1, 'J6':1}
ANALOG_TPS = {'TP3':[44,91], 'TP4':[44,85.8], 'TP7':[150,91], 'TP8':[146.5,85.5]}


def xy(value):
    return [pcb.ToMM(value.x), pcb.ToMM(value.y)]


def outlines(poly):
    return [[xy(poly.COutline(i).CPoint(j)) for j in range(poly.COutline(i).PointCount())]
            for i in range(poly.OutlineCount())]


def bounds(lines):
    points=[v for line in lines for v in line]
    return [min(v[0] for v in points),min(v[1] for v in points),
            max(v[0] for v in points),max(v[1] for v in points)] if points else None


def boxes_intersect(a,b):
    return a and b and a[0] <= b[2] and a[2] >= b[0] and a[1] <= b[3] and a[3] >= b[1]


def native_bounds(item):
    b=item.GetBoundingBox()
    return [pcb.ToMM(v) for v in (b.GetX(),b.GetY(),b.GetRight(),b.GetBottom())]


def inside(point,line):
    result=False
    for a,b in zip(line,line[1:]+line[:1]):
        if (a[1]>point[1])!=(b[1]>point[1]) and point[0]<(b[0]-a[0])*(point[1]-a[1])/(b[1]-a[1])+a[0]:
            result=not result
    return result


def point_segment(point,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    size=dx*dx+dy*dy
    t=max(0,min(1,((point[0]-a[0])*dx+(point[1]-a[1])*dy)/size)) if size else 0
    return math.hypot(point[0]-a[0]-t*dx,point[1]-a[1]-t*dy)


def point_polygon(point,lines):
    if any(inside(point,line) for line in lines):
        return 0.
    return min(point_segment(point,a,b) for line in lines for a,b in zip(line,line[1:]+line[:1]))


def polygon(points):
    result=pcb.SHAPE_POLY_SET();result.NewOutline()
    for x,y in points:
        result.Append(pcb.FromMM(x),pcb.FromMM(y))
    return result


def rectangle(box):
    x1,y1,x2,y2=box
    return polygon([(x1,y1),(x2,y1),(x2,y2),(x1,y2)])


def intersection_area(a,b):
    result=a.CloneDropTriangulation();result.BooleanIntersection(b)
    return result.Area()/1e12


def polygon_gap(a,b):
    if intersection_area(a,b)>1e-9:
        return 0.
    aa,bb=outlines(a),outlines(b)
    return min([point_polygon(p,bb) for line in aa for p in line]+
               [point_polygon(p,aa) for line in bb for p in line])


def review(board,path,final_snapshot):
    fps={f.GetReference():f for f in board.GetFootprints()}
    courts={};polys={}
    for ref,f in fps.items():
        f.BuildCourtyardCaches()
        polys[ref]=f.GetCourtyard(pcb.F_Cu).CloneDropTriangulation()
        courts[ref]=outlines(polys[ref])
    boxes={r:bounds(lines) for r,lines in courts.items()}
    mechanical_bytes=(ROOT/'manufacturing/busbar-pcb-interface.json').read_bytes()
    integration_bytes=(ROOT/'design/integration-parts.json').read_bytes()
    mechanical=json.loads(mechanical_bytes.decode('utf-8-sig'))
    source={c['ref']:c for c in json.loads(integration_bytes.decode('utf-8-sig'))['components']}
    testpoints=[]
    for ref in sorted((r for r in fps if r.startswith('TP')),key=lambda r:int(r[2:])):
        f=fps[ref];pad=list(f.Pads())[0];center=xy(pad.GetPosition());radius=pcb.ToMM(pad.GetSize().x)/2
        distances=sorted((point_polygon(center,lines),r) for r,lines in courts.items() if r!=ref and lines)
        body_distance,body_ref=next((d,r) for d,r in distances if not r.startswith('TP'))
        foreign=[]
        for other,ff in fps.items():
            if other==ref:
                continue
            for pp in ff.Pads():
                if not pp.IsOnLayer(pcb.F_Cu) or pp.GetNetname()==pad.GetNetname():
                    continue
                x1,y1,x2,y2=native_bounds(pp)
                distance=math.hypot(max(x1-center[0],0,center[0]-x2),max(y1-center[1],0,center[1]-y2))
                foreign.append((distance-radius,other,pp.GetNumber(),pp.GetNetname()))
        nearest_pad=min(foreign)
        bridge_distance=min(point_polygon(center,[x['top_bridge']['outline']]) for x in mechanical['net_tie_modifications'])
        screw_distance=min(math.dist(center,[x['x'],x['y']])-x['top_fastener_keepout_diameter_mm']/2 for x in mechanical['new_pcb_contacts'])
        expected=source.get(ref,{}).get('pins',{}).get('1')
        testpoints.append({'ref':ref,'net':pad.GetNetname(),'expected_source_net':expected,'source_net_matches':pad.GetNetname()==expected,
            'position_mm':center,'pad_size_mm':xy(pad.GetSize()),'top_mask_open':pad.IsOnLayer(pcb.F_Mask),
            'reference_visible':f.Reference().IsVisible(),'reference_position_mm':xy(f.Reference().GetPosition()),
            'nearest_component_body_courtyard':{'ref':body_ref,'center_distance_mm':body_distance,'copper_edge_gap_mm':body_distance-radius},
            'centered_3mm_probe_to_body_courtyard_gap_mm':body_distance-1.5,
            'nearest_foreign_pad_bbox_lower_bound':{'edge_gap_mm':nearest_pad[0],'ref':nearest_pad[1],'pin':nearest_pad[2],'net':nearest_pad[3]},
            'nearest_top_bridge_pad_edge_gap_mm':bridge_distance-radius,'nearest_top_bridge_probe_gap_mm':bridge_distance-1.5,
            'nearest_top_fastener_pad_edge_gap_mm':screw_distance-radius,'nearest_top_fastener_probe_gap_mm':screw_distance-1.5})
    overlaps=[]
    for a,b in itertools.combinations(sorted(fps),2):
        if boxes_intersect(boxes[a],boxes[b]):
            area=intersection_area(polys[a],polys[b])
            if area>1e-6:
                overlaps.append({'references':[a,b],'intersection_area_mm2':area})
    esp=[]
    for ref in ['C205','C239','C240','R219','R220']:
        esp.append({'pair':[ref,'U10'],'intersection_area_mm2':intersection_area(polys[ref],polys['U10']),
                    'courtyard_gap_mm':polygon_gap(polys[ref],polys['U10'])})
    module=fps['U10'];antenna=[]
    for z in module.Zones():
        if not z.GetIsRuleArea():
            continue
        keep=z.Outline();keep_bounds=bounds(outlines(keep));active=[l for l in LAYERS if z.GetLayerSet().Contains(l)]
        foreign_courts=[r for r in fps if r!='U10' and boxes_intersect(boxes[r],keep_bounds) and intersection_area(polys[r],keep)>1e-6]
        bars=[x['ref'] for x in mechanical['busbars'] if intersection_area(polygon(x['outline']),keep)>1e-6]
        copper=[]
        items=[(ref+'.'+pad.GetNumber(),pad) for ref,f in fps.items() for pad in f.Pads()]
        items += [('via' if isinstance(t,pcb.PCB_VIA) else 'track',t) for t in board.GetTracks()]
        for ref,item in items:
            if not boxes_intersect(native_bounds(item),keep_bounds):
                continue
            for layer in active:
                if not item.IsOnLayer(layer):
                    continue
                shape=pcb.SHAPE_POLY_SET()
                item.TransformShapeToPolygon(shape,layer,0,pcb.FromMM(.005),pcb.ERROR_INSIDE)
                area=intersection_area(shape,keep)
                if area>1e-6:
                    copper.append({'item':ref,'net':item.GetNetname(),'layer':board.GetLayerName(layer),'intersection_area_mm2':area})
        for zone in board.Zones():
            if zone.GetIsRuleArea():
                continue
            for layer in active:
                if zone.GetLayerSet().Contains(layer):
                    area=intersection_area(zone.GetFilledPolysList(layer),keep)
                    if area>1e-6:
                        copper.append({'item':'saved_zone_fill','net':zone.GetNetname(),'layer':board.GetLayerName(layer),'intersection_area_mm2':area})
        antenna.append({'polygons_mm':outlines(keep),'layers':[board.GetLayerName(l) for l in active],
                        'tracks_prohibited':z.GetDoNotAllowTracks(),'vias_prohibited':z.GetDoNotAllowVias(),
                        'pads_prohibited':z.GetDoNotAllowPads(),'zone_fill_prohibited':z.GetDoNotAllowZoneFills(),
                        'footprints_prohibited':z.GetDoNotAllowFootprints(),'foreign_courtyard_intersections':foreign_courts,
                        'busbar_intersections':bars,'actual_copper_intersections':copper,
                        'mounting_hole_gaps_mm':{r:polygon_gap(polys[r],keep) for r in fps if r.startswith('H')}})
    connectors=[]
    for ref in sorted((r for r in fps if r.startswith('J')),key=lambda r:int(r[1:])):
        f=fps[ref];box=boxes[ref];pos=xy(f.GetPosition());angle=f.GetOrientationDegrees()
        entry={'ref':ref,'position_mm':pos,'rotation_deg':angle,'footprint':f.GetFPIDAsString(),
               'dnp':f.IsDNP(),'courtyard_bounds_mm':box,'access_basis':'Vertical mating/top access; mated housing/grip volume absent'}
        corridor=None
        if 'PhoenixContact' in f.GetFPIDAsString():
            if angle==-90:
                corridor=[box[0]-20,box[1],box[0],box[3]];entry['access_basis']='Left-edge horizontal mating'
            elif angle==90:
                corridor=[box[2],box[1],box[2]+20,box[3]];entry['access_basis']='Right-edge horizontal mating'
            elif angle==0:
                corridor=[box[0],box[3],box[2],box[3]+20];entry['access_basis']='Bottom-edge horizontal mating'
        elif ref in M5_FACES:
            sign=M5_FACES[ref];x,y=pos
            near=y+sign*4.5;far=near+sign*20
            corridor=[x-4.5,min(near,far),x+4.5,max(near,far)]
            entry.update(access_basis='M5 face '+('-Y' if sign<0 else '+Y')+' from assembly specification; 9 mm wide projected 20 mm tool corridor',required_face_direction_y=sign,
                         three_dimensional_tool_clearance_verified=False)
        if corridor:
            region=rectangle(corridor)
            entry['nominal_20mm_planar_access_bounds_mm']=corridor
            entry['planar_access_courtyard_hits']=[r for r in fps if r!=ref and boxes_intersect(boxes[r],corridor) and intersection_area(polys[r],region)>1e-6]
            entry['planar_access_top_bridge_hits']=[x['top_bridge']['ref'] for x in mechanical['net_tie_modifications'] if intersection_area(polygon(x['top_bridge']['outline']),region)>1e-6]
            entry['planar_access_limitation']='Projection only: screw-axis height, selected tool, mated plug, lug, counterhold and cable bend envelope require physical fixture verification.'
        connectors.append(entry)
    critical=[]
    if len(testpoints)!=40 or not all(t['source_net_matches'] and t['top_mask_open'] and t['reference_visible'] and t['pad_size_mm']==[2.,2.] for t in testpoints):
        critical.append('Testpoint count, source mapping, mask opening or label visibility requires correction')
    if any(not lines for lines in courts.values()):
        critical.append('A footprint lacks its native front courtyard; geometric coverage is incomplete')
    if overlaps:
        critical.append('Native front-courtyard intersections found')
    if any(t['nearest_component_body_courtyard']['copper_edge_gap_mm']<0 for t in testpoints):
        critical.append('Testpoint copper overlaps a component courtyard')
    if any(min(t['nearest_top_bridge_pad_edge_gap_mm'],t['nearest_top_fastener_pad_edge_gap_mm'])<0 for t in testpoints):
        critical.append('Testpoint copper overlaps the defined top bridge or fastener envelope')
    required_layers={board.GetLayerName(l) for l in LAYERS}
    if not antenna or any(set(a['layers'])!=required_layers or not all(a[k] for k in ['tracks_prohibited','vias_prohibited','pads_prohibited','zone_fill_prohibited','footprints_prohibited']) for a in antenna):
        critical.append('Antenna rule area is absent or lacks required four-layer prohibitions')
    if any(a['actual_copper_intersections'] or a['foreign_courtyard_intersections'] or a['busbar_intersections'] for a in antenna):
        critical.append('Antenna keepout geometry/copper intersection found')
    changed_tps={ref:{'expected_mm':point,'actual_mm':next(t['position_mm'] for t in testpoints if t['ref']==ref),
                       'matches':math.dist(point,next(t['position_mm'] for t in testpoints if t['ref']==ref))<1e-5} for ref,point in ANALOG_TPS.items()}
    if not all(x['matches'] for x in changed_tps.values()):
        critical.append('Saved PCB does not contain all four requested analog TP moves')
    if any(c['ref'] in M5_FACES and c['rotation_deg']%360 for c in connectors):
        critical.append('M5 footprint rotation no longer matches the specified native +/-Y screw axis')
    return {'metadata':{'rev_a_engineering_prototype':True,'rev_b_production':False,'final_snapshot':final_snapshot,
                         'scope':'Native read-only placement and 2D access review; no PCB edits, zone refill, connectivity approval or physical tool measurements'},
            'testpoints':testpoints,'analog_testpoint_moves':changed_tps,
            'geometry_inputs_sha256':{'manufacturing/busbar-pcb-interface.json':hashlib.sha256(mechanical_bytes).hexdigest(),
                                      'design/integration-parts.json':hashlib.sha256(integration_bytes).hexdigest()},
            'all_front_courtyard_intersections':overlaps,'footprints_without_front_courtyard':[r for r in fps if not courts[r]],
            'esp_bbox_false_positive_review':esp,'antenna':{'module_position_mm':xy(module.GetPosition()),'rotation_deg':module.GetOrientationDegrees(),'rule_areas':antenna},
            'connectors':connectors,'critical_findings':critical,
            'probe_access_basis':{'pad_diameter_mm':2,'centered_vertical_probe_nose_diameter_mm':3,
                                  'minimum_3mm_nose_to_body_courtyard_gap_mm':min(t['centered_3mm_probe_to_body_courtyard_gap_mm'] for t in testpoints),
                                  'limited_probe_access_refs':[t['ref'] for t in testpoints if min(t['centered_3mm_probe_to_body_courtyard_gap_mm'],t['nearest_top_bridge_probe_gap_mm'],t['nearest_top_fastener_probe_gap_mm'])<0],
                                  'limitation':'No probe shroud/tilt, installed cable or enclosure volume is modeled.'}},polys


def markdown(data,json_name):
    tp=data['testpoints'];worst=min(tp,key=lambda t:t['nearest_component_body_courtyard']['copper_edge_gap_mm'])
    near=worst['nearest_component_body_courtyard'];probe=data['probe_access_basis']
    state='Final stable placement snapshot' if data['metadata']['final_snapshot'] else 'Interim geometry snapshot; final routing/assembly hash binding is pending'
    lines=['# Placement and access review after analog changes','',
           '`rev_a_engineering_prototype: true`  ','`rev_b_production: false`','',state+'. No PCB data was changed.',
           'The [JSON evidence]('+json_name+') records actual native geometry. This review does not establish final routing connectivity or a 3D tool/harness envelope.','',
           f'All {len(tp)} testpoints were checked against their source nets, front mask openings and reference visibility. The smallest test-pad edge to component-courtyard gap is **{near["copper_edge_gap_mm"]:.3f} mm at {worst["ref"]}/{near["ref"]}**. A centered 3 mm probe nose has a minimum body-courtyard margin of **{probe["minimum_3mm_nose_to_body_courtyard_gap_mm"]:.3f} mm**. Negative margins are reported as access limitations, not silently accepted.','',
           '| Ref | Net | X | Y | Nearest body / pad-edge gap mm | 3 mm probe margin mm |',
           '|---|---|---:|---:|---|---:|']
    for t in tp:
        n=t['nearest_component_body_courtyard']
        lines.append(f'| {t["ref"]} | {t["net"]} | {t["position_mm"][0]:g} | {t["position_mm"][1]:g} | {n["ref"]} / {n["copper_edge_gap_mm"]:.3f} | {t["centered_3mm_probe_to_body_courtyard_gap_mm"]:.3f} |')
    lines += ['',f'Native front-courtyard intersections: **{len(data["all_front_courtyard_intersections"])}**. These use actual polygons, including the ESP32 stepped outline.','',
              '| ESP32 candidate | Intersection mm² | Actual courtyard gap mm |','|---|---:|---:|']
    for item in data['esp_bbox_false_positive_review']:
        lines.append(f'| {item["pair"][0]} / U10 | {item["intersection_area_mm2"]:.6g} | {item["courtyard_gap_mm"]:.3f} |')
    lines += ['','The antenna check reads every native rule area, its prohibitions/layers, actual pad/track/via copper, saved filled polygons, foreign courtyards and the defined busbars. Copper curves are polygonized at 0.005 mm; this screen complements native DRC.']
    for area in data['antenna']['rule_areas']:
        lines.append(f'Bounds {bounds(area["polygons_mm"])} mm; layers {area["layers"]}. Foreign courtyard hits {area["foreign_courtyard_intersections"]}; busbar hits {area["busbar_intersections"]}; actual copper intersections {len(area["actual_copper_intersections"])}. Mounting-hole courtyard gaps: {area["mounting_hole_gaps_mm"]}.')
    lines += ['','| Connector | Access basis | 20 mm projected courtyard hits | Top bridge hits |','|---|---|---|---|']
    for c in data['connectors']:
        hits=(', '.join(c['planar_access_courtyard_hits']) or 'none') if 'nominal_20mm_planar_access_bounds_mm' in c else 'top access; no horizontal corridor modeled'
        lines.append(f'| {c["ref"]} | {c["access_basis"]} | {hits} | {", ".join(c.get("planar_access_top_bridge_hits",[])) or "none"} |')
    lines += ['','M5 directions come from the assembly specification: J1/J2/J3/J5 face −Y; J4/J6 face +Y. A projected overlap is an unresolved 3D fixture check because screw-axis and nearby hardware heights are not modeled here. A clear projection also does not prove tool access. Confirm actual wrench, lug stack, counterhold and cable-bend clearance at the first article.','',
              'Critical geometric findings: '+('; '.join(data['critical_findings']) if data['critical_findings'] else 'none detected in this snapshot')+'.',
              'Limited 3 mm probe positions: '+(', '.join(probe['limited_probe_access_refs']) or 'none')+'.','']
    return '\n'.join(lines)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--board',type=Path,default=ROOT/'kicad/HomeMy_PMU_RevA.kicad_pcb')
    ap.add_argument('--output-base',type=Path,default=ROOT/'evidence/placement-access-review-interim')
    ap.add_argument('--final-snapshot',action='store_true')
    args=ap.parse_args()
    before=hashlib.sha256(args.board.read_bytes()).hexdigest()
    board=pcb.LoadBoard(str(args.board))
    data,polys=review(board,args.board,args.final_snapshot)
    after=hashlib.sha256(args.board.read_bytes()).hexdigest()
    if before!=after:
        raise RuntimeError('PCB changed during read-only review; rerun against a stable snapshot')
    data['source']={'pcb_path':str(args.board),'observed_interim_sha256':None if args.final_snapshot else before,
                    'final_pcb_sha256':before if args.final_snapshot else None,'read_only_hash_stable':True,
                    'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}
    args.output_base.parent.mkdir(parents=True,exist_ok=True)
    json_path=args.output_base.with_suffix('.json');md_path=args.output_base.with_suffix('.md')
    json_path.write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
    md_path.write_text(markdown(data,json_path.name),encoding='utf-8')
    print(json.dumps({'testpoints':len(data['testpoints']),'critical_findings':data['critical_findings'],
                      'probe_access':data['probe_access_basis'],'analog_tps':data['analog_testpoint_moves'],
                      'connector_projected_hits':{c['ref']:c.get('planar_access_courtyard_hits') for c in data['connectors'] if c.get('planar_access_courtyard_hits')},
                      'read_only_hash_stable':True},indent=2),flush=True)
    return board,polys


if __name__=='__main__':
    try:
        native_owners=main()
    except BaseException:
        traceback.print_exc();force_exit(1)
    force_exit(0)
