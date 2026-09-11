"""Read-only candidate geometry and original 247 force-pair audit.

Geometry screens never grant manufacturing or thermal qualification. Narrow
control conductors and external busbars are never credited to main power paths.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
import math
import re
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent / "rev-a"
sys.path.insert(0, str(BASE / "scripts"))
import pcbnew as pcb
from review_placement_access import outlines, bounds, boxes_intersect, intersection_area, point_polygon, rectangle
from configure_power_rules import POWER_NETS
from review_critical_routing import PAIRS, graph_for, shortest

LAYERS = [pcb.F_Cu, pcb.In1_Cu, pcb.In2_Cu, pcb.B_Cu]
def xy(p): return [pcb.ToMM(p.x), pcb.ToMM(p.y)]
def point(x, y): return pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()


def critical(board):
    pads = {f.GetReference()+"."+p.GetNumber():p for f in board.GetFootprints() for p in f.Pads()}
    tracks = list(board.GetTracks()); graphs = {}; paths = []
    for name, a, b in PAIRS:
        net = pads[a].GetNetname()
        assert pads[b].GetNetname() == net
        if net not in graphs: graphs[net] = graph_for(net, tracks, pads)
        value = shortest(graphs[net], a, b); value.pop("vertices", None)
        paths.append({"name":name,"from_pad":a,"to_pad":b,"net":net,**value})
    return {"paths": paths, "total": len(paths), "passed": sum(p["path_found"] for p in paths),
            "limitations": "Explicit centerlines and actual pad/via links only; excludes plane return paths and EM coupling."}


def references(board,result):
    latest=result.get('cycles',{}).get(str(max(map(int,result.get('cycles',{'0':{}})))),{})
    stitches=latest.get('critical_reference_seed',{}).get('reference_stitches',[])
    tracks=list(board.GetTracks());pads=[p for f in board.GetFootprints() for p in f.Pads()]
    vias={(t.GetNetname(),tuple(round(v,5) for v in xy(t.GetPosition()))):t for t in tracks if isinstance(t,pcb.PCB_VIA)}
    rows=[]
    for r in stitches:
        net=r['net'];key=(net,tuple(round(x,5) for x in r['via_xy_mm']));v=vias.get(key);layers=[]
        if v:
            x,y=xy(v.GetPosition());radius=pcb.ToMM(v.GetDrillValue())/2+.05
            samples=[point(x+radius,y),point(x-radius,y),point(x,y+radius),point(x,y-radius)]
            for l in LAYERS:
                zone_hit=any(z.GetNetname()==net and not z.GetIsRuleArea() and z.GetLayer()==l and any(z.GetFilledPolysList(l).Contains(p,-1,0,True) for p in samples) for z in board.Zones())
                conductor_hit=any(t.m_Uuid.AsString()!=v.m_Uuid.AsString() and t.GetNetname()==net and t.IsOnLayer(l) and t.GetBoundingBox().Intersects(v.GetBoundingBox()) and t.GetEffectiveShape(l).Collide(v.GetEffectiveShape(l),0) for t in tracks+pads)
                if zone_hit or conductor_hit:layers.append(board.GetLayerName(l))
        rows.append({**r,'via_exists':bool(v),'attached_copper_layers':layers,'at_least_two_layers':len(layers)>=2})
    return {'stitches_checked':len(rows),'at_least_two_layers':sum(r['at_least_two_layers'] for r in rows),'lookup_coordinate_rounding_mm':.00001,'unproven_stitches':[r for r in rows if not r['at_least_two_layers']],
            'limitation':'Local via-to-copper attachment only. Global reference integrity also requires zero native opens; no inference from a nearby zone outline.'}


def placement(board, baseline):
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    old = {f.GetReference(): f for f in baseline.GetFootprints()}
    size = board.GetBoardEdgesBoundingBox()
    width, height = pcb.ToMM(size.GetWidth()), pcb.ToMM(size.GetHeight())
    courts, boxes = {}, {}
    errors = []
    if len(fps) != 425 or set(fps) != set(old): errors.append("Footprint roster is not the original 425")
    def land_signature(f):
        a=math.radians(f.GetOrientationDegrees());c,s=math.cos(a),math.sin(a);x,y=xy(f.GetPosition())
        def local(p):
            X,Y=xy(p.GetPosition());return (round(c*(X-x)-s*(Y-y),5),round(s*(X-x)+c*(Y-y),5))
        return sorted((p.GetNumber(), p.GetNetname(), tuple(xy(p.GetSize())), tuple(xy(p.GetDrillSize())),
                       p.GetShape(), p.GetLayerSet().FmtHex(),local(p),p.GetDrillShape(),round((p.GetOrientationDegrees()-f.GetOrientationDegrees())%360,5)) for p in f.Pads())
    for ref, f in fps.items():
        f.BuildCourtyardCaches()
        courts[ref] = f.GetCourtyard(pcb.F_Cu).CloneDropTriangulation()
        boxes[ref] = bounds(outlines(courts[ref]))
        if ref not in old or f.GetFPIDAsString() != old[ref].GetFPIDAsString() or f.GetValue() != old[ref].GetValue() or land_signature(f) != land_signature(old[ref]):
            errors.append("Changed footprint/pad/net identity: " + ref)
        b = boxes[ref]
        if b and ref != "U10" and (b[0] < -.001 or b[1] < -.001 or b[2] > width+.001 or b[3] > height+.001):
            errors.append("Off-board courtyard: " + ref)
    overlaps = [[a, b] for a, b in itertools.combinations(fps, 2)
                if boxes_intersect(boxes[a], boxes[b]) and intersection_area(courts[a], courts[b]) > 1e-6]
    probes = []
    for ref, f in fps.items():
        if not ref.startswith("TP"): continue
        pos = xy(f.GetPosition())
        gap, other = min((point_polygon(pos, outlines(poly))-1.5, r) for r, poly in courts.items()
                         if r != ref and not r.startswith("TP") and poly.OutlineCount())
        probes.append({"ref": ref, "3mm_probe_gap_mm": gap, "nearest_body": other})
    if len(probes) != 40: errors.append("Expected 40 test points")
    ports = []
    for ref, f in fps.items():
        if not ref.startswith("J"): continue
        b = boxes[ref]; x, y = xy(f.GetPosition()); corridor = None
        if ref in ("J1", "J2"): corridor = [-25, y-6, x-4.5, y+6]
        elif ref in ("J3", "J4", "J5", "J6"): corridor = [x+4.5, y-6, width+25, y+6]
        elif "PhoenixContact" in f.GetFPIDAsString():
            angle = round(f.GetOrientationDegrees()) % 360
            corridor = ([-20, b[1], b[0], b[3]] if angle == 270 else
                        [b[2], b[1], width+20, b[3]] if angle == 90 else
                        [b[0], -20, b[2], b[1]] if angle == 180 else [b[0], b[3], b[2], height+20])
        hits = [] if corridor is None else [r for r in fps if r != ref and boxes_intersect(boxes[r], corridor)
                                            and intersection_area(courts[r], rectangle(corridor)) > 1e-6]
        ports.append({"ref": ref, "corridor_mm": corridor, "blocked_by": hits})
    antenna = []
    all_items = [p for f in fps.values() for p in f.Pads()] + list(board.GetTracks())
    for z in fps["U10"].Zones():
        if not z.GetIsRuleArea(): continue
        keep = z.Outline(); keep_box = bounds(outlines(keep)); copper = []
        active = [l for l in LAYERS if z.GetLayerSet().Contains(l)]
        for t in all_items:
            b = t.GetBoundingBox(); bb = [pcb.ToMM(v) for v in (b.GetX(), b.GetY(), b.GetRight(), b.GetBottom())]
            if not boxes_intersect(bb, keep_box): continue
            for l in active:
                if not t.IsOnLayer(l): continue
                q = pcb.SHAPE_POLY_SET(); t.TransformShapeToPolygon(q, l, 0, pcb.FromMM(.005), pcb.ERROR_INSIDE)
                if intersection_area(q, keep) > 1e-6: copper.append(t.m_Uuid.AsString())
        for area in board.Zones():
            if area.GetIsRuleArea(): continue
            for l in active:
                if area.GetLayerSet().Contains(l) and intersection_area(area.GetFilledPolysList(l), keep) > 1e-6:
                    copper.append(area.m_Uuid.AsString())
        antenna.append({"layers": [board.GetLayerName(l) for l in active], "bounds_mm": keep_box,
                        "edge_reached": keep_box[3] >= height-.001,
                        "prohibitions": all([z.GetDoNotAllowTracks(), z.GetDoNotAllowVias(), z.GetDoNotAllowPads(), z.GetDoNotAllowZoneFills(), z.GetDoNotAllowFootprints()]),
                        "copper_intersections": sorted(set(copper)),
                        "foreign_courtyards": [r for r in fps if r != "U10" and boxes_intersect(boxes[r], keep_box) and intersection_area(courts[r], keep) > 1e-6]})
    pressfit = []
    for ref in ("J1", "J2", "J3", "J4", "J5", "J6"):
        pads = list(fps[ref].Pads())
        valid = len(pads) == 8 and all(abs(pcb.ToMM(p.GetSize().x)-2.10) < 1e-6 and abs(pcb.ToMM(p.GetDrillSize().x)-1.475) < 1e-6 for p in pads)
        pressfit.append({"ref": ref, "pads": len(pads), "geometry_unchanged": valid})
    return {"footprints": len(fps), "testpoints": len(probes), "size_mm": [width, height],
            "identity_errors": errors, "courtyard_overlaps": overlaps, "probes": probes, "ports": ports,
            "antenna": antenna, "pressfit": pressfit,
            "mounting_holes_mm": {r: xy(fps[r].GetPosition()) for r in ("H1", "H2", "H3", "H4")},
            "passed": not errors and not overlaps and len(probes) == 40 and all(p["3mm_probe_gap_mm"] >= -1e-6 for p in probes)
                and all(not p["blocked_by"] for p in ports) and bool(antenna)
                and all(a["prohibitions"] and len(a["layers"]) == 4 and a["edge_reached"] and not a["copper_intersections"] and not a["foreign_courtyards"] for a in antenna)
                and all(p["geometry_unchanged"] for p in pressfit),
            "limitations": ["2D probe/cable/body screens; no measured 3D harness, cover or press-tool model."]}


def force(board):
    original = json.loads((BASE / "evidence/filled-power-copper-review.json").read_text(encoding="utf-8"))
    paths = original["same_layer_path_checks"]
    nets = {p["net"] for p in paths}
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    pads = {f.GetReference()+"."+p.GetNumber(): p for f in fps.values() for p in f.Pads()}
    polys = {}; zone_rows = []; omitted = 0
    def add(net, layer, q):
        polys.setdefault((net, layer), pcb.SHAPE_POLY_SET()).BooleanAdd(q)
    for z in board.Zones():
        if z.GetIsRuleArea() or z.GetNetname() not in nets: continue
        add(z.GetNetname(), z.GetLayer(), z.GetFilledPolysList(z.GetLayer()))
        zone_rows.append({"net": z.GetNetname(), "layer": board.GetLayerName(z.GetLayer()), "fill_min_mm": pcb.ToMM(z.GetMinThickness()), "area_mm2": z.GetFilledPolysList(z.GetLayer()).Area()/1e12})
    tracks = []
    for t in board.GetTracks():
        if t.GetNetname() not in nets: continue
        group = t.GetParentGroup()
        threshold = 6 if t.GetNetname() in ("ARM_L_N", "ARM_R_N") else 4
        allowed = (pcb.ToMM(t.GetDrillValue()) >= .4-1e-6 and pcb.ToMM(t.GetWidth(pcb.F_Cu)) >= .8-1e-6) if isinstance(t, pcb.PCB_VIA) else pcb.ToMM(t.GetWidth()) >= threshold-1e-6
        if group or not allowed: omitted += 1; continue
        tracks.append(t)
    copper = [p for p in pads.values() if p.GetNetname() in nets] + tracks
    for t in copper:
        for l in LAYERS:
            if not t.IsOnLayer(l): continue
            q = pcb.SHAPE_POLY_SET(); t.TransformShapeToPolygon(q, l, 0, pcb.FromMM(.005), pcb.ERROR_INSIDE)
            add(t.GetNetname(), l, q)
    holes = {}
    for t in copper:
        diameter = pcb.ToMM(t.GetDrillValue()) if isinstance(t, pcb.PCB_VIA) else pcb.ToMM(t.GetDrillSize().x) if isinstance(t, pcb.PAD) else 0
        if diameter <= 0: continue
        x, y = xy(t.GetPosition()); h = pcb.SHAPE_POLY_SET(); h.NewOutline()
        for k in range(40): h.Append(point(x+diameter/2*math.cos(k*math.pi/20), y+diameter/2*math.sin(k*math.pi/20)))
        for l in LAYERS:
            if t.IsOnLayer(l): holes.setdefault((t.GetNetname(), l), pcb.SHAPE_POLY_SET()).Append(h)
    for k, h in holes.items(): h.Simplify(); polys[k].BooleanSubtract(h)
    for q in polys.values(): q.Simplify(); q.BuildBBoxCaches()
    def outline_ids(label, net, layer):
        p = pads[label]; x, y = xy(p.GetPosition()); d = pcb.ToMM(p.GetDrillSize().x)
        samples = [[x, y]] if not d else [[x+d/2+.1, y], [x-d/2-.1, y], [x, y+d/2+.1], [x, y-d/2-.1]]
        q = polys.get((net, layer))
        return set() if q is None else {i for i in range(q.OutlineCount()) if any(q.Contains(point(*p), i, 0, True) for p in samples)}
    checks = []
    for row in paths:
        layer = board.GetLayerID(row["layer"])
        ok = bool(outline_ids(row["from_pad"], row["net"], layer) & outline_ids(row["to_pad"], row["net"], layer))
        checks.append({k: row[k] for k in ("net", "layer", "from_pad", "to_pad")} | {"passed": ok})
    alternative = {"net": "DRIVE_N", "layer": "B.Cu", "from_pad": "J7.2", "to_pad": "NT3.1",
                   "passed": bool(outline_ids("J7.2", "DRIVE_N", pcb.B_Cu) & outline_ids("NT3.1", "DRIVE_N", pcb.B_Cu)),
                   "note": "Additional compact return proof; does not replace original F.Cu result."}
    windows = []
    for ref in ["Q"+str(n) for n in range(1, 11)]+["Q40"]:
        f = fps[ref]; x, y = xy(f.GetPosition()); window = rectangle([x-20, y-20, x+20, y+20])
        for net in {p.GetNetname() for p in f.Pads()} & nets:
            for l in (pcb.F_Cu, pcb.B_Cu):
                q = polys.get((net, l))
                windows.append({"ref": ref, "net": net, "layer": board.GetLayerName(l), "area_40mm_window_mm2": intersection_area(q, window) if q else 0})
    # Fixed sections are physical measurements, not a global minimum-cut proof.
    baseline=pcb.LoadBoard(str(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'))
    oldfps={f.GetReference():f for f in baseline.GetFootprints()}
    definitions=[]
    for row in original['cross_sections']:
        match=re.match(r'^(RSH[12]|Q\d+)\b',row['label'])
        if not match:continue
        ref=match.group(1);a=math.radians(fps[ref].GetOrientationDegrees()-oldfps[ref].GetOrientationDegrees());c,s=math.cos(a),math.sin(a)
        x,y=xy(oldfps[ref].GetPosition());X,Y=xy(fps[ref].GetPosition())
        def moved(p):return [X+c*(p[0]-x)+s*(p[1]-y),Y-s*(p[0]-x)+c*(p[1]-y)]
        definitions.append((row['label'],row['net'],board.GetLayerID(row['layer']),moved(row['line_from_mm']),moved(row['line_to_mm'])))
    edge=board.GetBoardEdgesBoundingBox();W,H=pcb.ToMM(edge.GetWidth()),pcb.ToMM(edge.GetHeight());dx,dy=W-250,H-200
    for l in [pcb.F_Cu,pcb.B_Cu]:
        definitions += [('Motion right spine','MOTION_BUS_P',l,[W-14,100],[W-1,100]),('Battery return under core','BATT_N',l,[110,113],[110,153]),('Left arm approach','ARM_L_N',l,[217+dx,90],[217+dx,116]),('Right arm approach','ARM_R_N',l,[217+dx,113],[217+dx,140])]
    definitions += [('Drive return horizontal','DRIVE_N',pcb.B_Cu,[180,147+dy],[180,159+dy])]
    for l in [pcb.In1_Cu,pcb.In2_Cu]:definitions.append(('Lift return horizontal','LIFT_N',l,[180,143+dy],[180,155+dy]))
    sections=[]
    for label,net,l,a,b in definitions:
        length=math.dist(a,b);N=max(1,math.ceil(length/.025));step=length/N;q=polys.get((net,l));runs=[];start=None
        for i in range(N+1):
            occupied=i<N and q is not None and q.Contains(point(a[0]+(b[0]-a[0])*(i+.5)/N,a[1]+(b[1]-a[1])*(i+.5)/N),-1,0,True)
            if occupied and start is None:start=i
            if not occupied and start is not None:runs.append(round((i-start)*step,4));start=None
        sections.append({'label':label,'net':net,'layer':board.GetLayerName(l),'line_from_mm':a,'line_to_mm':b,'continuous_widths_mm':runs,'total_copper_width_mm':round(sum(runs),4),'sampling_step_mm':step})
    contacts={}
    for ref,f in fps.items():
        if ref.startswith('BC'):
            for net in {p.GetNetname() for p in f.Pads()}:contacts.setdefault(net,[]).append(ref)
    busbars=[]
    for net,refs in sorted(contacts.items()):
        for a,b in itertools.combinations(sorted(refs),2):
            busbars.append({'net':net,'contacts':[a,b],'center_span_mm':round(math.dist(xy(fps[a].GetPosition()),xy(fps[b].GetPosition())),4),'baseline_center_span_mm':round(math.dist(xy(oldfps[a].GetPosition()),xy(oldfps[b].GetPosition())),4)})
    return {"original_pair_checks": checks, "passed_pairs": sum(p["passed"] for p in checks), "total_pairs": len(checks),
            "failed_pairs": [p for p in checks if not p["passed"]], "compact_drive_return": alternative,
            "omitted_tap_or_undersized_copper_items": omitted, "zones": zone_rows, "thermal_windows": windows,
            "power_vias": dict(Counter(t.GetNetname() for t in tracks if isinstance(t, pcb.PCB_VIA))),
            "fixed_cross_sections":sections,"busbar_contact_spans":busbars,
            "limitations": ["Same-layer polygon continuity, not a minimum-cut or current-sharing simulation.", "All grouped and undersized conductors omitted. No busbar credit, no thermal hardware validation."]}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("board", type=Path); ap.add_argument("phase"); ap.add_argument("--placement-only", action="store_true"); args = ap.parse_args()
    board = pcb.LoadBoard(str(args.board)); digest = sha(args.board)
    baseline = pcb.LoadBoard(str(BASE / "kicad/HomeMy_PMU_RevA.kicad_pcb"))
    value = {"pcb_sha256": digest, "placement": placement(board, baseline)}
    board.BuildConnectivity(); board.GetConnectivity().RecalculateRatsnest()
    value['native_ratsnest_connections'] = board.GetConnectivity().GetUnconnectedCount(False)
    if not args.placement_only:
        value["force"] = force(board)
        value["critical"] = critical(board)
    assert sha(args.board) == digest, "Read-only audit changed PCB"
    out = ROOT / "results" / (args.board.stem+".json")
    result = json.loads(out.read_text(encoding="utf-8")) if out.exists() else {"board": str(args.board.relative_to(ROOT))}
    if not args.placement_only:value['reference_stitches']=references(board,result)
    result.setdefault("geometry", {})[args.phase] = value
    out.write_text(json.dumps(result, indent=2, ensure_ascii=False)+"\n", encoding="utf-8")
    print("Geometry", args.phase, "placement", value["placement"]["passed"], "force", value.get("force", {}).get("passed_pairs"), flush=True)
