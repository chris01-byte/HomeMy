"""Original force audit with rebuild-specific additional measurement axes.
Copied primitive implementation from rev-a1/scripts/bounded_geometry.py, SHA256 7fba25f85bc7ea189e10c9860089f00dfe1ef378431a01076dd6e252ea0b807a.
Tap omission, hole subtraction and the 247 original same-layer identities are unchanged.
"""
from bounded_geometry import *

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
                   "note": "Informational only: optional B.Cu path; original F.Cu requirement is authoritative."}
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
    from new_sections import definitions as rebuild_sections
    definitions += rebuild_sections(board)
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
