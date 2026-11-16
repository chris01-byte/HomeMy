#!/usr/bin/python3
"""Geometrie-Pruefungen an der A2-Leiterplatte mit pcbnew (nur lesend).

Aufruf: /usr/bin/python3 pcb_checks.py   -> schreibt daten/pcb_checks.json und druckt eine Zusammenfassung.
Inhalt:
  inventory      Kontur, Lagenzahl, Footprints, Pads, Vias, Zonen
  pad_connection wie leistungsrelevante Bauteile angebunden sind (Flaeche oder nur duenne Leiterbahn)
  tvs_d1         Leiterbahnen/Vias des Netzes BATT_FUSED_P (Anbindung der Eingangsschutzdiode D1)
  tap_group      Inhalt der DRC-Ausnahmegruppen (PWR_TAP_CONTROL usw.)
  ground_tie     Geometrie der Netzbruecke NT9 (einzige Verbindung LOGIC_GND <-> BATT_N)
  cross_sections Kupferbreiten der Rueckleiter ARM_R_N, ARM_L_N und BATT_N je Lage
  busbar_vias    Vias fremder Netze unter den Kupferschienen BB1..BB7
  pad_gaps       kleinste Padabstaende feinrastriger ICs
  tvs_body_edge  Abstand Fremdkupfer zur Gehaeusekante von D1/D2
  antenna        Kupfer in der Sperrflaeche der ESP32-Antenne
"""
import collections, json, os
import pcbnew
import _common as C

b = pcbnew.LoadBoard(C.PCB)
mm, F = pcbnew.ToMM, pcbnew.FromMM
tracks = [t for t in b.GetTracks() if t.GetClass() != "PCB_VIA"]
vias = [t for t in b.GetTracks() if t.GetClass() == "PCB_VIA"]
zones = [b.GetArea(i) for i in range(b.GetAreaCount())]
CU = {"F.Cu": pcbnew.F_Cu, "In1.Cu": pcbnew.In1_Cu, "In2.Cu": pcbnew.In2_Cu, "B.Cu": pcbnew.B_Cu}
res = {"pcb": os.path.basename(C.PCB)}


def xy(p):
    return (round(mm(p.x), 2), round(mm(p.y), 2))


def inventory():
    bb = b.GetBoardEdgesBoundingBox()
    return {"outline_bbox_mm": [round(mm(bb.GetWidth()), 2), round(mm(bb.GetHeight()), 2)],
            "copper_layers": b.GetCopperLayerCount(), "footprints": len(list(b.GetFootprints())),
            "pads": sum(len(list(f.Pads())) for f in b.GetFootprints()), "track_segments": len(tracks),
            "vias": len(vias), "zones": len(zones),
            "via_sizes": {f"{mm(v.GetWidth(pcbnew.F_Cu))}/{mm(v.GetDrillValue())}": n for (v, n) in
                          [(next(x for x in vias if (mm(x.GetWidth(pcbnew.F_Cu)), mm(x.GetDrillValue())) == k), c)
                           for k, c in collections.Counter((mm(v.GetWidth(pcbnew.F_Cu)), mm(v.GetDrillValue())) for v in vias).items()]}}


def pad_connection(ref):
    f = b.FindFootprintByReference(ref)
    rows = collections.OrderedDict()
    for p in f.Pads():
        net, bb, c = p.GetNetname(), p.GetBoundingBox(), p.GetPosition()
        zl = sorted({b.GetLayerName(l) for z in zones if z.GetNetname() == net for l in z.GetLayerSet().Seq()
                     if l in CU.values() and p.IsOnLayer(l) and z.HitTestFilledArea(l, c, 0)})
        tw = collections.Counter(round(mm(t.GetWidth()), 2) for t in tracks if t.GetNetname() == net
                                 and p.IsOnLayer(t.GetLayer()) and (bb.Contains(t.GetStart()) or bb.Contains(t.GetEnd())))
        nv = sum(1 for v in vias if v.GetNetname() == net and bb.Contains(v.GetPosition()))
        rows.setdefault((net, tuple(zl), tuple(sorted(tw.items())), nv), []).append(p.GetNumber())
    return [{"pads": pads, "net": net, "zone_at_pad_centre": list(zl), "tracks_width_count": list(tw), "vias_in_pad": nv}
            for (net, zl, tw, nv), pads in rows.items() if net and not net.startswith("unconnected")]


def net_tracks(net):
    out = []
    for t in b.GetTracks():
        if t.GetNetname() != net:
            continue
        if t.GetClass() == "PCB_VIA":
            out.append({"via": [mm(t.GetWidth(pcbnew.F_Cu)), mm(t.GetDrillValue())], "at": xy(t.GetPosition())})
        else:
            out.append({"track_w": mm(t.GetWidth()), "layer": b.GetLayerName(t.GetLayer()),
                        "len": round(mm(t.GetLength()), 2), "from": xy(t.GetStart()), "to": xy(t.GetEnd())})
    return out


def tap_groups():
    out = {}
    for g in b.Groups():
        nets = collections.Counter()
        for it in g.GetItems():
            try:
                nets[it.GetNetname()] += 1
            except Exception:
                nets["?"] += 1
        out[g.GetName()] = {"items": sum(nets.values()), "by_net": dict(nets.most_common())}
    return out


def ground_tie(ref="NT9"):
    f = b.FindFootprintByReference(ref)
    out = {"footprint": str(f.GetFPID().GetLibItemName()), "at": xy(f.GetPosition()), "pads": [], "tracks": [], "vias": []}
    for p in f.Pads():
        out["pads"].append({"pad": p.GetNumber(), "net": p.GetNetname(), "at": xy(p.GetPosition()),
                            "size": [round(mm(p.GetSize().x), 2), round(mm(p.GetSize().y), 2)]})
        bb = p.GetBoundingBox()
        bb.Inflate(F(0.3))
        for t in tracks:
            if t.GetNetname() == p.GetNetname() and (bb.Contains(t.GetStart()) or bb.Contains(t.GetEnd())):
                out["tracks"].append({"net": p.GetNetname(), "w": mm(t.GetWidth()), "layer": b.GetLayerName(t.GetLayer()),
                                      "len": round(mm(t.GetLength()), 2), "from": xy(t.GetStart()), "to": xy(t.GetEnd())})
    c, R = f.GetPosition(), F(3)
    for v in vias:
        q = v.GetPosition()
        if v.GetNetname() in ("LOGIC_GND", "BATT_N") and abs(q.x - c.x) < R and abs(q.y - c.y) < R:
            out["vias"].append({"net": v.GetNetname(), "size": [mm(v.GetWidth(pcbnew.F_Cu)), mm(v.GetDrillValue())], "at": xy(q)})
    return out


def width(net, layer, axis, const, lo, hi, step=0.05):
    zs = [z for z in zones if z.GetNetname() == net and z.IsOnLayer(CU[layer])]
    tot, segs, cur, v = 0.0, [], None, lo
    while v <= hi:
        p = pcbnew.VECTOR2I(F(const), F(v)) if axis == "x" else pcbnew.VECTOR2I(F(v), F(const))
        if any(z.HitTestFilledArea(CU[layer], p, 0) for z in zs):
            tot += step
            cur = [v, v] if cur is None else [cur[0], v]
        elif cur is not None:
            segs.append(cur)
            cur = None
        v += step
    if cur is not None:
        segs.append(cur)
    return {"total_mm": round(tot, 2), "intervals": [[round(a, 1), round(c, 1)] for a, c in segs if c - a > 0.3]}


def cross_sections():
    out = {"ARM_R_N_cut_y": {}, "ARM_L_N_cut_y": {}, "BATT_N_cut_x": {}}
    for y in (86, 92, 100, 110, 118, 124, 132):
        out["ARM_R_N_cut_y"][y] = {l: width("ARM_R_N", l, "y", y, 230, 278) for l in ("F.Cu", "B.Cu")}
    for y in (60, 90, 100, 112, 124, 132):
        out["ARM_L_N_cut_y"][y] = {l: width("ARM_L_N", l, "y", y, 200, 278) for l in ("F.Cu", "B.Cu")}
    for x in (30, 60, 95, 110, 115, 120, 150, 190, 205, 207, 210, 215, 225, 245):
        out["BATT_N_cut_x"][x] = {l: width("BATT_N", l, "x", x, 100, 160) for l in ("F.Cu", "B.Cu", "In2.Cu")}
    return out


def busbar_vias():
    def inpoly(x, y, poly):
        c, j = False, len(poly) - 1
        for i in range(len(poly)):
            xi, yi = poly[i]
            xj, yj = poly[j]
            if ((yi > y) != (yj > y)) and (x < (xj - xi) * (y - yi) / (yj - yi) + xi):
                c = not c
            j = i
        return c
    out = {}
    for bb in json.load(open(C.BUSBAR_JSON))["busbars"]:
        foreign = collections.defaultdict(list)
        for v in vias:
            x, y = mm(v.GetPosition().x), mm(v.GetPosition().y)
            r = mm(v.GetWidth(pcbnew.B_Cu)) / 2
            if v.GetNetname() != bb["net"] and any(inpoly(x + dx, y + dy, bb["outline"]) for dx, dy in ((0, 0), (r, 0), (-r, 0), (0, r), (0, -r))):
                foreign[v.GetNetname()].append([round(x, 2), round(y, 2)])
        out[bb["ref"]] = {"net": bb["net"], "foreign_vias": dict(foreign)}
    return out


def pad_gaps(ref):
    pads = list(b.FindFootprintByReference(ref).Pads())
    best = (9, None)
    for i in range(len(pads)):
        for j in range(i + 1, len(pads)):
            a, c = pads[i], pads[j]
            if a.GetNumber() == c.GetNumber():
                continue
            ba, bc = a.GetBoundingBox(), c.GetBoundingBox()
            dx = max(0, max(ba.GetX(), bc.GetX()) - min(ba.GetRight(), bc.GetRight()))
            dy = max(0, max(ba.GetY(), bc.GetY()) - min(ba.GetBottom(), bc.GetBottom()))
            g = mm((dx * dx + dy * dy) ** 0.5)
            if g < best[0]:
                best = (round(g, 3), [a.GetNumber(), a.GetNetname(), c.GetNumber(), c.GetNetname()])
    return {"min_gap_mm": best[0], "between": best[1]}


def fill_range(net, const_y, lo, hi):
    hit, v = [], lo
    while v <= hi:
        if any(z.GetNetname() == net and z.IsOnLayer(pcbnew.F_Cu) and z.HitTestFilledArea(pcbnew.F_Cu, pcbnew.VECTOR2I(F(v), F(const_y)), 0) for z in zones):
            hit.append(round(v, 2))
        v += 0.01
    return [hit[0], hit[-1]] if hit else None


def antenna():
    u = b.FindFootprintByReference("U10")
    out = []
    for z in u.Zones():
        zb = z.GetBoundingBox()
        n = sum(1 for t in b.GetTracks() if any(z.Outline().Contains(pcbnew.VECTOR2I(p.x, p.y)) for p in
                ([t.GetPosition()] if t.GetClass() == "PCB_VIA" else [t.GetStart(), t.GetEnd()])))
        out.append({"keepout_bbox_mm": [round(mm(zb.GetX()), 1), round(mm(zb.GetY()), 1), round(mm(zb.GetRight()), 1), round(mm(zb.GetBottom()), 1)],
                    "tracks_or_vias_inside": n})
    return out


res["inventory"] = inventory()
res["pad_connection"] = {r: pad_connection(r) for r in ("D1", "D2", "D60", "D61", "D63", "U12", "NT9", "NT10", "U3", "U4", "RSH1", "RSH2", "J1", "J2", "Q1", "Q7", "C312", "C313")}
res["tvs_d1_net_BATT_FUSED_P"] = net_tracks("BATT_FUSED_P")
res["tap_groups"] = tap_groups()
res["ground_tie_NT9"] = ground_tie("NT9")
res["cross_sections"] = cross_sections()
res["busbar_foreign_vias"] = busbar_vias()
res["pad_gaps"] = {r: pad_gaps(r) for r in ("U1", "U2", "U11", "U16", "U18", "U27")}
res["tvs_body_edge"] = {"D1_BATT_SENSED_P_fill_x_at_y69 (Gehaeusekante x=38.0)": fill_range("BATT_SENSED_P", 69.0, 37.0, 39.5),
                        "D2_SYS_BUS_P_fill_x_at_y84 (Gehaeusekante x=105.0)": fill_range("SYS_BUS_P", 84.0, 104.0, 106.0)}
res["antenna_keepout"] = antenna()
os.makedirs(C.OUT, exist_ok=True)
json.dump(res, open(os.path.join(C.OUT, "pcb_checks.json"), "w"), indent=1, ensure_ascii=False)
print(json.dumps({k: res[k] for k in ("inventory", "tap_groups", "busbar_foreign_vias", "pad_gaps", "tvs_body_edge", "antenna_keepout")}, indent=1)[:2600])
