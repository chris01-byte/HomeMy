#!/usr/bin/env python3
"""Build the slotted acrylic LiDAR window ring ("freie Sicht fuer Lidar").

The STL-27L cannot see through the infrared acrylic ring, so a slot is milled
at scan height and six webs remain as load paths (decision record
docs/decisions/2026-11-16-lidar-slot-and-support-webs.md). This script builds
that ring as a solid in the coordinates of hardware/cad/homemy.step (V2),
checks it against the robot model, and writes:

  freie_sicht_fuer_lidar.step            ring body, robot coordinates, mm
  freie_sicht_fuer_lidar_abwicklung.dxf  flat development for milling, 1:1, mm
  freie_sicht_fuer_lidar.png             drawing sheet (top view, development)
  freie_sicht_fuer_lidar.json            geometry, positions and check results

Model frame: X to the robot's right, Y forward, Z up (Z 0 = top of the
aluminium base plate). The decision record uses X forward, Y left; model
X = -record Y, model Y = record X.

Requires: cadquery-ocp (OpenCascade), ezdxf, matplotlib.
usage: lidar_window_ring.py --model hardware/cad/homemy.step --out DIR
"""
import argparse
import json
import math
import time

from OCP.BRep import BRep_Builder, BRep_Tool
from OCP.BRepAdaptor import BRepAdaptor_Curve
from OCP.BRepAlgoAPI import BRepAlgoAPI_Common, BRepAlgoAPI_Cut, BRepAlgoAPI_Section
from OCP.BRepBndLib import BRepBndLib
from OCP.BRepCheck import BRepCheck_Analyzer
from OCP.BRepFilletAPI import BRepFilletAPI_MakeFillet
from OCP.BRepGProp import BRepGProp
from OCP.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCP.Bnd import Bnd_Box
from OCP.GProp import GProp_GProps
from OCP.GeomAbs import GeomAbs_Line
from OCP.IFSelect import IFSelect_RetDone
from OCP.Interface import Interface_Static
from OCP.Quantity import Quantity_Color, Quantity_TOC_RGB
from OCP.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCP.STEPControl import STEPControl_AsIs
from OCP.TCollection import TCollection_ExtendedString
from OCP.TDF import TDF_Label
from OCP.TDataStd import TDataStd_Name
from OCP.TDocStd import TDocStd_Document
from OCP.TopAbs import TopAbs_EDGE, TopAbs_SOLID, TopAbs_VERTEX
from OCP.TopExp import TopExp, TopExp_Explorer
from OCP.TopLoc import TopLoc_Location
from OCP.TopoDS import TopoDS
from OCP.XCAFApp import XCAFApp_Application
from OCP.XCAFDoc import XCAFDoc_ColorSurf, XCAFDoc_DocumentTool
from OCP.collections import IndexedMap_TopoDS_Shape_TopTools_ShapeMapHasher, Sequence_TDF_Label
from OCP.gp import gp_Dir, gp_Pln, gp_Pnt

BODY_NAME = "freie Sicht für Lidar"

# Ring, from homemy.step V2: ABS frame step at Z 89 (3 mm rebate up to the
# frame top at Z 99), shell underside at Z 189, outer outline 500 x 400 R100.
OUT_X, OUT_Y, OUT_R = 250.0, 200.0, 100.0
T = 3.0
Z_BOT, Z_TOP = 89.0, 189.0

# Slot, from the decision record: 40 mm high, centred on the scan plane.
# Scan plane = KEEP_CLEAR_optical_window ... scan_Z27.00 in the LiDAR
# component, whose Z 0 is model Z 95.
Z_SCAN = 122.0
SLOT_H = 40.0
Z_S0, Z_S1 = Z_SCAN - SLOT_H / 2, Z_SCAN + SLOT_H / 2
R_CORNER = 3.0  # slot corner radius, 6 mm end mill
LIDAR_XY = (0.0, 160.0)  # STL-27L rotation axis
FLOOR_Z = Z_SCAN - 163.8  # decision record: scan plane 163.8 mm above the floor

# Webs (material that stays), model coordinates: name, x0, x1, y0, y1.
# Record values: front/rear webs at record Y +-130..150, side webs at
# record X -110..-30.
WEBS = [
    ("Steg vorn links", -150, -130, 180, 220),
    ("Steg vorn rechts", 130, 150, 180, 220),
    ("Steg Seite links", -270, -230, -110, -30),
    ("Steg Seite rechts", 230, 270, -110, -30),
    ("Steg hinten links", -150, -130, -220, -180),
    ("Steg hinten rechts", 130, 150, -220, -180),
]

# Expected blind sectors of the record (degrees at the LiDAR axis, 0 ahead,
# positive towards the robot's left), used as acceptance check.
RECORD_WEB_SECTORS = {
    "Steg vorn links": (72.9, 76.1),
    "Steg vorn rechts": (-76.1, -72.9),
    "Steg hinten links": (157.2, 160.1),
    "Steg hinten rechts": (-160.1, -157.2),
}
RECORD_STRUT_SECTORS = {"links": (126.9, 137.9), "rechts": (-137.9, -126.9)}


# --------------------------------------------------------------- OCC helpers
def bbox(shape):
    b = Bnd_Box()
    BRepBndLib.Add_s(shape, b, True)
    if b.IsVoid():
        return None
    a, c = b.CornerMin(), b.CornerMax()
    return [round(v, 3) for v in (a.X(), a.Y(), a.Z(), c.X(), c.Y(), c.Z())]


def solids(shape):
    out = []
    ex = TopExp_Explorer(shape, TopAbs_SOLID)
    while ex.More():
        out.append(TopoDS.Solid(ex.Current()))
        ex.Next()
    return out


def volume(shape):
    p = GProp_GProps()
    BRepGProp.VolumeProperties_s(shape, p)
    return p.Mass()


def cut(a, b):
    op = BRepAlgoAPI_Cut(a, b)
    op.Build()
    assert op.IsDone()
    return op.Shape()


def vertices(shape):
    pts = []
    ex = TopExp_Explorer(shape, TopAbs_VERTEX)
    while ex.More():
        pts.append(BRep_Tool.Pnt_s(TopoDS.Vertex(ex.Current())))
        ex.Next()
    return pts


def rounded_prism(hx, hy, r, z0, z1):
    """Box centred on the Z axis with vertical edges rounded to radius r."""
    box = BRepPrimAPI_MakeBox(gp_Pnt(-hx, -hy, z0), 2 * hx, 2 * hy, z1 - z0).Shape()
    f = BRepFilletAPI_MakeFillet(box)
    emap = IndexedMap_TopoDS_Shape_TopTools_ShapeMapHasher()
    TopExp.MapShapes_s(box, TopAbs_EDGE, emap)
    for i in range(1, emap.Extent() + 1):
        e = TopoDS.Edge(emap.FindKey(i))
        p0, p1 = vertices(e)[:2]
        if abs(p0.X() - p1.X()) < 1e-9 and abs(p0.Y() - p1.Y()) < 1e-9:
            f.Add(r, e)
    f.Build()
    assert f.IsDone()
    return f.Shape()


def section_points(shape, z, n=200):
    sec = BRepAlgoAPI_Section(shape, gp_Pln(gp_Pnt(0, 0, z), gp_Dir(0, 0, 1)))
    sec.Build()
    pts = []
    ex = TopExp_Explorer(sec.Shape(), TopAbs_EDGE)
    while ex.More():
        c = BRepAdaptor_Curve(TopoDS.Edge(ex.Current()))
        for i in range(n + 1):
            p = c.Value(c.FirstParameter() + (c.LastParameter() - c.FirstParameter()) * i / n)
            pts.append((p.X(), p.Y()))
        ex.Next()
    return pts


def bearing(p):
    """Record convention: 0 deg straight ahead, positive towards the robot's left."""
    return math.degrees(math.atan2(-(p[0] - LIDAR_XY[0]), p[1] - LIDAR_XY[1]))


def sectors(pts, gap=0.5):
    if not pts:
        return []
    tagged = sorted((bearing(p), math.hypot(p[0] - LIDAR_XY[0], p[1] - LIDAR_XY[1])) for p in pts)
    groups, cur = [], [tagged[0]]
    for t in tagged[1:]:
        if t[0] - cur[-1][0] > gap:
            groups.append(cur)
            cur = [t]
        else:
            cur.append(t)
    groups.append(cur)
    return [
        {"von": round(g[0][0], 2), "bis": round(g[-1][0], 2), "breite": round(g[-1][0] - g[0][0], 2),
         "abstand_min": round(min(d for _, d in g)), "abstand_max": round(max(d for _, d in g))}
        for g in groups
    ]


# ------------------------------------------------------------------- build
def build_ring():
    ring = cut(rounded_prism(OUT_X, OUT_Y, OUT_R, Z_BOT, Z_TOP),
               rounded_prism(OUT_X - T, OUT_Y - T, OUT_R - T, Z_BOT - 1, Z_TOP + 1))
    v_plain = volume(ring)

    band = cut(rounded_prism(OUT_X + 10, OUT_Y + 10, OUT_R + 10, Z_S0, Z_S1),
               rounded_prism(OUT_X - 10, OUT_Y - 10, OUT_R - 10, Z_S0 - 1, Z_S1 + 1))
    for _, x0, x1, y0, y1 in WEBS:
        band = cut(band, BRepPrimAPI_MakeBox(gp_Pnt(x0, y0, Z_S0 - 5), x1 - x0, y1 - y0, SLOT_H + 10).Shape())
    pieces = solids(band)
    assert len(pieces) == 6, len(pieces)

    web_x = {w[1] for w in WEBS if abs(w[3]) > 150} | {w[2] for w in WEBS if abs(w[3]) > 150}
    web_y = {w[3] for w in WEBS if abs(w[1]) > 200} | {w[4] for w in WEBS if abs(w[1]) > 200}

    def slot_end_edge(e):
        """Horizontal straight edge at the top or bottom of a slot end face."""
        if BRepAdaptor_Curve(e).GetType() != GeomAbs_Line:
            return False
        pts = vertices(e)
        z = pts[0].Z()
        if not all(abs(p.Z() - z) < 1e-6 for p in pts) or min(abs(z - Z_S0), abs(z - Z_S1)) > 1e-6:
            return False
        same_x = all(abs(p.X() - pts[0].X()) < 1e-6 for p in pts)
        same_y = all(abs(p.Y() - pts[0].Y()) < 1e-6 for p in pts)
        return (same_x and any(abs(pts[0].X() - wx) < 1e-6 for wx in web_x)) or \
               (same_y and any(abs(pts[0].Y() - wy) < 1e-6 for wy in web_y))

    result = ring
    for pc in pieces:
        f = BRepFilletAPI_MakeFillet(pc)
        emap = IndexedMap_TopoDS_Shape_TopTools_ShapeMapHasher()
        TopExp.MapShapes_s(pc, TopAbs_EDGE, emap)
        n = 0
        for i in range(1, emap.Extent() + 1):
            e = TopoDS.Edge(emap.FindKey(i))
            if slot_end_edge(e):
                f.Add(R_CORNER, e)
                n += 1
        assert n == 4, n
        f.Build()
        assert f.IsDone()
        result = cut(result, f.Shape())

    assert BRepCheck_Analyzer(result).IsValid()
    rs = solids(result)
    assert len(rs) == 1, len(rs)
    return rs[0], v_plain


# ------------------------------------------------------------ model check
def load_model(path):
    app = XCAFApp_Application.GetApplication_s()
    doc = TDocStd_Document(TCollection_ExtendedString("MDTV-XCAF"))
    app.InitDocument(doc)
    r = STEPCAFControl_Reader()
    r.SetNameMode(True)
    assert r.ReadFile(path) == IFSelect_RetDone
    assert r.Transfer(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())

    def name_of(label):
        n = TDataStd_Name()
        return n.Get().ToExtString() if label.FindAttribute(TDataStd_Name.GetID_s(), n) else ""

    out = []

    def rec(label, loc, path):
        target = label
        if st.IsReference_s(label):
            target = TDF_Label()
            st.GetReferredShape_s(label, target)
            loc = loc.Multiplied(st.GetLocation_s(label))
        p = path + [name_of(label) or name_of(target)]
        if st.IsAssembly_s(target):
            children = Sequence_TDF_Label()
            st.GetComponents_s(target, children, False)
            for i in range(1, children.Length() + 1):
                rec(children.Value(i), loc, p)
        else:
            for s in solids(st.GetShape_s(target)):
                out.append(("/".join(p), s.Moved(loc)))

    free = Sequence_TDF_Label()
    st.GetFreeShapes(free)
    for i in range(1, free.Length() + 1):
        rec(free.Value(i), TopLoc_Location(), [])
    return out


def check_model(ring, model_path):
    t = time.time()
    model = load_model(model_path)
    report = {"model_solids": len(model), "load_seconds": round(time.time() - t, 1),
              "scan_plane_solids": [], "ring_overlap_mm3": [], "strut_sectors": []}
    strut_pts = []
    for path, s in model:
        b = bbox(s)
        if not b or b[5] < Z_BOT or b[2] > Z_TOP:
            continue
        if b[2] <= Z_SCAN <= b[5]:
            report["scan_plane_solids"].append(path)
            if "Aluminiumprofil" in path:
                strut_pts += section_points(s, Z_SCAN, 50)
        if max(abs(b[0]), abs(b[3])) < OUT_X - T - 0.5 and max(abs(b[1]), abs(b[4])) < OUT_Y - T - 0.5:
            continue
        com = BRepAlgoAPI_Common(ring, s)
        com.Build()
        report["ring_overlap_mm3"].append((path, round(volume(com.Shape()), 3)))
    report["strut_sectors"] = sectors(strut_pts)
    return report


# ----------------------------------------------------------------- export
def export_step(ring, path):
    doc = TDocStd_Document(TCollection_ExtendedString("MDTV-XCAF"))
    XCAFApp_Application.GetApplication_s().InitDocument(doc)
    st = XCAFDoc_DocumentTool.ShapeTool_s(doc.Main())
    ct = XCAFDoc_DocumentTool.ColorTool_s(doc.Main())
    label = st.AddShape(ring, False)
    TDataStd_Name.Set_s(label, TCollection_ExtendedString(BODY_NAME, True))
    ct.SetColor(label, Quantity_Color(0.25, 0.05, 0.05, Quantity_TOC_RGB), XCAFDoc_ColorSurf)
    Interface_Static.SetCVal_s("write.step.schema", "AP214IS")
    Interface_Static.SetCVal_s("write.step.unit", "MM")
    w = STEPCAFControl_Writer()
    w.SetNameMode(True)
    w.SetColorMode(True)
    assert w.Transfer(doc, STEPControl_AsIs)
    assert w.Write(path) == IFSelect_RetDone
    # OpenCascade writes names as raw UTF-8; ISO 10303-21 (and Fusion's own
    # export, e.g. K\X\F6rper) escapes non-ASCII characters.
    with open(path, encoding="utf-8") as f:
        text = f.read()
    text = "".join(c if ord(c) < 128 else ("\\X\\%02X" % ord(c) if ord(c) < 256 else "\\X2\\%04X\\X0\\" % ord(c))
                   for c in text)
    with open(path, "w", encoding="ascii", newline="\n") as f:
        f.write(text)


# ------------------------------------------------------------ development
# Mid-surface of the sheet: half sizes and corner radius.
MX, MY, MR = OUT_X - T / 2, OUT_Y - T / 2, OUT_R - T / 2
CX, CY = OUT_X - OUT_R, OUT_Y - OUT_R  # corner centres at (+-CX, +-CY)
QUARTER = MR * math.pi / 2
PERIMETER = 4 * CX + 4 * CY + 4 * QUARTER


def s_ccw(x, y):
    """Arc length on the mid-surface, counter-clockwise seen from above,
    starting at the front centre (towards the robot's left first)."""
    segs = [  # (start s, kind, data)
        (0.0, "line", (0, MY, -1, 0, CX)),                       # front, x 0 -> -CX
        (CX, "arc", (-CX, CY, 90)),                              # front left
        (CX + QUARTER, "line", (-MX, CY, 0, -1, 2 * CY)),        # left wall, y CY -> -CY
        (CX + 2 * CY + QUARTER, "arc", (-CX, -CY, 180)),         # rear left
        (CX + 2 * CY + 2 * QUARTER, "line", (-CX, -MY, 1, 0, 2 * CX)),   # rear
        (3 * CX + 2 * CY + 2 * QUARTER, "arc", (CX, -CY, 270)),  # rear right
        (3 * CX + 2 * CY + 3 * QUARTER, "line", (MX, -CY, 0, 1, 2 * CY)),  # right wall
        (3 * CX + 4 * CY + 3 * QUARTER, "arc", (CX, CY, 0)),     # front right
        (3 * CX + 4 * CY + 4 * QUARTER, "line", (CX, MY, -1, 0, CX)),    # front, x CX -> 0
    ]
    best = None
    for s0, kind, d in segs:
        if kind == "line":
            px, py, dx, dy, length = d
            u = (x - px) * dx + (y - py) * dy
            u = min(max(u, 0.0), length)
            dist = math.hypot(px + dx * u - x, py + dy * u - y)
            cand = (dist, s0 + u)
        else:
            cx, cy, a0 = d
            a = (math.degrees(math.atan2(y - cy, x - cx)) - a0) % 360
            if a > 90:
                a = 0 if a > 225 else 90
            px, py = cx + MR * math.cos(math.radians(a0 + a)), cy + MR * math.sin(math.radians(a0 + a))
            cand = (math.hypot(px - x, py - y), s0 + MR * math.radians(a))
        if best is None or cand[0] < best[0]:
            best = cand
    return best[1] % PERIMETER


def mid_point_at_y_on_side(y, side):
    """Point on the mid-surface of a side wall or its rear corner with the given y."""
    sx = -1 if side == "links" else 1
    if y >= -CY:
        return sx * MX, y
    return sx * (CX + math.sqrt(MR ** 2 - (y + CY) ** 2)), y


def development():
    """Webs, slots and bend zones along the strip. The strip starts at the
    middle of the left side web and runs counter-clockwise seen from above,
    i.e. left to right when the outside of the ring is viewed."""
    s_start = s_ccw(*mid_point_at_y_on_side(-70, "links"))

    def u(s):
        return round((s - s_start) % PERIMETER, 2)

    webs = []
    for name, x0, x1, y0, y1 in WEBS:
        if abs(y0) > 150:  # front or rear wall
            y = MY if y0 > 0 else -MY
            a, b = u(s_ccw(x0, y)), u(s_ccw(x1, y))
        else:
            side = "links" if x0 < 0 else "rechts"
            a, b = u(s_ccw(*mid_point_at_y_on_side(y0, side))), u(s_ccw(*mid_point_at_y_on_side(y1, side)))
        a, b = min(a, b), max(a, b)
        if b - a > PERIMETER / 2:  # the left web is split by the strip start
            webs.append((name + " (Anfang)", 0.0, a))
            webs.append((name + " (Ende)", b, round(PERIMETER, 2)))
        else:
            webs.append((name, a, b))
    webs.sort(key=lambda w: w[1])
    slots = []
    for w0, w1 in zip(webs, webs[1:]):
        slots.append({"von": w0[2], "bis": w1[1], "laenge": round(w1[1] - w0[2], 2),
                      "zwischen": [w0[0], w1[0]]})
    bends = []
    for name, cx, cy in [("Ecke vorn links", -CX, CY), ("Ecke hinten links", -CX, -CY),
                         ("Ecke hinten rechts", CX, -CY), ("Ecke vorn rechts", CX, CY)]:
        sx, sy = (1 if cx > 0 else -1), (1 if cy > 0 else -1)
        p_side, p_end = (sx * MX, cy), (cx, sy * MY)
        a, b = sorted([u(s_ccw(*p_side)), u(s_ccw(*p_end))])
        bends.append({"name": name, "von": a, "bis": b})
    bends.sort(key=lambda b: b["von"])
    marks = {"vorn Mitte": u(s_ccw(0, MY)), "hinten Mitte": u(s_ccw(0, -MY))}
    return {"laenge": round(PERIMETER, 2), "hoehe": Z_TOP - Z_BOT,
            "schlitz_unten": Z_S0 - Z_BOT, "schlitz_oben": Z_S1 - Z_BOT,
            "webs": [{"name": n, "von": a, "bis": b, "breite": round(b - a, 2)} for n, a, b in webs],
            "slots": slots, "bends": bends, "marks": marks}


def rounded_rect_path(x0, x1, y0, y1, r, n=8):
    pts = []
    for cx, cy, a0 in [(x1 - r, y0 + r, 270), (x1 - r, y1 - r, 0), (x0 + r, y1 - r, 90), (x0 + r, y0 + r, 180)]:
        for i in range(n + 1):
            a = math.radians(a0 + 90 * i / n)
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def export_dxf(dev, path):
    import ezdxf
    doc = ezdxf.new("R2010", setup=True)
    doc.units = ezdxf.units.MM
    for name, color in [("KONTUR", 7), ("SCHLITZE", 1), ("BIEGEZONEN", 8), ("TEXT", 3)]:
        doc.layers.add(name, color=color)
    doc.layers.get("BIEGEZONEN").dxf.linetype = "DASHED"
    msp = doc.modelspace()
    L, H = dev["laenge"], dev["hoehe"]
    msp.add_lwpolyline([(0, 0), (L, 0), (L, H), (0, H)], close=True, dxfattribs={"layer": "KONTUR"})
    y0, y1, r = dev["schlitz_unten"], dev["schlitz_oben"], R_CORNER
    for s in dev["slots"]:
        x0, x1 = s["von"], s["bis"]
        # straight segments with bulge arcs for the R3 corners
        bulge = math.tan(math.radians(90) / 4)
        msp.add_lwpolyline([
            (x0 + r, y0, 0), (x1 - r, y0, bulge), (x1, y0 + r, 0), (x1, y1 - r, bulge),
            (x1 - r, y1, 0), (x0 + r, y1, bulge), (x0, y1 - r, 0), (x0, y0 + r, bulge),
        ], format="xyb", close=True, dxfattribs={"layer": "SCHLITZE"})
    for b in dev["bends"]:
        for x in (b["von"], b["bis"]):
            msp.add_line((x, 0), (x, H), dxfattribs={"layer": "BIEGEZONEN"})
        msp.add_text(b["name"], height=4, dxfattribs={"layer": "TEXT"}).set_placement(
            ((b["von"] + b["bis"]) / 2, H + 4), align=ezdxf.enums.TextEntityAlignment.BOTTOM_CENTER)
    for w in dev["webs"]:
        msp.add_text(w["name"], height=3, dxfattribs={"layer": "TEXT", "rotation": 90}).set_placement(
            ((w["von"] + w["bis"]) / 2, (y0 + y1) / 2), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
    for name, x in dev["marks"].items():
        msp.add_line((x, H), (x, H + 12), dxfattribs={"layer": "TEXT"})
        msp.add_text(name, height=4, dxfattribs={"layer": "TEXT"}).set_placement(
            (x, H + 14), align=ezdxf.enums.TextEntityAlignment.BOTTOM_CENTER)
    msp.add_text("UNTERKANTE = Rahmenfalz (Z 89). Abwicklung auf Blechmitte, Aussenseite sichtbar, 1:1 mm",
                 height=4, dxfattribs={"layer": "TEXT"}).set_placement((0, -10))
    doc.saveas(path)


def export_drawing(ring, dev, sector_report, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon, Rectangle  # noqa: F401

    fig = plt.figure(figsize=(16.5, 11.7))
    fig.suptitle("HomeMy – Körper „freie Sicht für Lidar“: Acrylring 3 mm mit LiDAR-Schlitz und 6 Stegen\n"
                 "aus homemy.step V2 gebaut, Werte aus der Stegberechnung vom 16.11.2026 – CAD-Vorhersage, nicht gemessen",
                 x=0.03, ha="left", fontsize=13)

    # top view
    ax = fig.add_axes([0.03, 0.40, 0.40, 0.48])
    ax.set_aspect("equal")
    ax.axis("off")
    ax.set_title("Draufsicht in Höhe der Scanebene (Z 122) – Fahrtrichtung nach oben", fontsize=10, loc="left")
    outer = [(p[0], p[1]) for p in rounded_rect_path(-OUT_X, OUT_X, -OUT_Y, OUT_Y, OUT_R, 16)]
    ax.add_patch(Polygon(outer, closed=True, fill=False, ec="#bbbbbb", lw=1, ls="--"))
    sec = section_points(ring, Z_SCAN, 40)
    ax.plot([p[0] for p in sec], [p[1] for p in sec], ".", ms=2.5, color="black")
    for name, x0, x1, y0, y1 in WEBS:
        tx = (x0 + x1) / 2 if abs(y0) > 150 else (x0 + x1) / 2 * 1.13
        ty = (y0 + y1) / 2 * (1.13 if abs(y0) > 150 else 1)
        ax.text(tx, ty, name.replace("Steg ", "") + "\n%d mm" % round(math.hypot(x1 - x0, 0) if abs(y0) > 150 else y1 - y0),
                ha="center", va="center", fontsize=7.5)
    for sx in (-1, 1):
        ax.add_patch(Rectangle((sx * 204.0 - 20, -46.17), 40, 40, color="#888888"))
    ax.plot(*LIDAR_XY, "o", color="#c0392b")
    ax.text(LIDAR_XY[0], LIDAR_XY[1] - 22, "LiDAR", ha="center", fontsize=8, color="#c0392b")
    for s in sector_report:
        for b in (s["von"], s["bis"]):
            a = math.radians(b)
            ax.plot([LIDAR_XY[0], LIDAR_XY[0] - 420 * math.sin(a)], [LIDAR_XY[1], LIDAR_XY[1] + 420 * math.cos(a)],
                    color="#e67e22", lw=0.6)
    ax.annotate("", xy=(0, 280), xytext=(0, 230), arrowprops=dict(arrowstyle="->"))
    ax.text(8, 255, "vorn", fontsize=8)
    ax.set_xlim(-330, 330)
    ax.set_ylim(-300, 300)

    # tables
    ax2 = fig.add_axes([0.47, 0.40, 0.52, 0.48])
    ax2.axis("off")
    lines = [
        "Ring: außen 500 × 400 mm, Eckradius R100 außen / R97 innen, 3 mm, Höhe 100 mm",
        "      Z 89 (sitzt auf dem 3-mm-Falz des ABS-Rahmens, 10 mm Überdeckung) bis Z 189 (Schale)",
        "Schlitz: Z 102 bis 142 = 13 bis 53 mm über der Ringunterkante, 40 mm hoch,",
        "      mittig auf der Scanebene Z 122 (≈ 164 mm über Boden); Ecken R3 (Fräser Ø 6)",
        "",
        "Stege (Robotermaße, Mittellinie = Mitte zwischen links und rechts):",
        "  vorn links/rechts    130 bis 150 mm links/rechts der Mittellinie, Breite 20 mm",
        "  hinten links/rechts  130 bis 150 mm links/rechts der Mittellinie, Breite 20 mm",
        "  Seite links/rechts   230 bis 310 mm hinter der Vorderkante, Breite 80 mm",
        "                       (endet 10 mm im Bogen der hinteren Ecke)",
        "",
        "Blinde Winkel der Stege an der LiDAR-Achse (0° = vorn, + = links):",
    ]
    for s in sector_report:
        lines.append("  %+7.1f° bis %+7.1f°  (%.1f°)  Abstand %d–%d mm" % (s["von"], s["bis"], s["breite"],
                                                                      s["abstand_min"], s["abstand_max"]))
    lines += ["  Seitenstege liegen im Schatten der Alu-Streben (±126,9° bis ±137,9°).", "",
              "Draufsicht: gestrichelt = offener Schlitz, schwarz = Steg, grau = Alu-Strebe,",
              "            orange = Grenzen der blinden Winkel der Stege"]
    ax2.text(0, 1, "\n".join(lines), va="top", family="DejaVu Sans Mono", fontsize=8.6)

    # development, split in the middle of the right side web
    L, H = dev["laenge"], dev["hoehe"]
    w_right = next(w for w in dev["webs"] if w["name"] == "Steg Seite rechts")
    split = (w_right["von"] + w_right["bis"]) / 2
    rows = [(0.0, split), (split, L)]
    longest = max(r1 - r0 for r0, r1 in rows)
    for row, (a0, a1) in enumerate(rows):
        width = 0.95 * (a1 - a0 + 10) / (longest + 10)
        ax3 = fig.add_axes([0.03, 0.20 - row * 0.17, width, 0.14])
        ax3.set_aspect("equal", anchor="W")
        ax3.set_xlim(a0 - 5, a1 + 5)
        ax3.set_ylim(-16, H + 18)
        ax3.axis("off")

        def txt(x, y, t, **kw):
            if a0 - 2 <= x <= a1 + 2:
                ax3.text(x, y, t, **kw)

        ax3.add_patch(Rectangle((0, 0), L, H, fill=False, lw=1))
        for b in dev["bends"]:
            ax3.add_patch(Rectangle((b["von"], 0), b["bis"] - b["von"], H, color="#eeeeee", zorder=0))
            txt((max(b["von"], a0) + min(b["bis"], a1)) / 2, H + 3, b["name"], ha="center", fontsize=7,
                color="#666666")
        for sl in dev["slots"]:
            pts = rounded_rect_path(sl["von"], sl["bis"], dev["schlitz_unten"], dev["schlitz_oben"], R_CORNER)
            ax3.add_patch(Polygon(pts, closed=True, fc="white", ec="#c0392b", lw=1))
            txt((max(sl["von"], a0) + min(sl["bis"], a1)) / 2, dev["schlitz_oben"] + 3,
                "Schlitz %.1f" % sl["laenge"], ha="center", fontsize=7, color="#c0392b")
        for w in dev["webs"]:
            for x in (w["von"], w["bis"]):
                txt(x, -3, "%.1f" % x, ha="center", va="top", fontsize=6.5, rotation=90)
            txt((max(w["von"], a0) + min(w["bis"], a1)) / 2, (dev["schlitz_unten"] + dev["schlitz_oben"]) / 2,
                w["name"].replace("Steg ", ""), ha="center", va="center", fontsize=6.5, rotation=90)
        for name, x in dev["marks"].items():
            if a0 <= x <= a1:
                ax3.plot([x, x], [H, H + 9], color="black", lw=0.8)
                txt(x, H + 10, name, ha="center", fontsize=7)
        if row == 0:
            ax3.set_title("Abwicklung auf Blechmitte, Länge %.1f mm, Höhe %d mm, Außenseite sichtbar, Unterkante unten "
                          "(liegt auf dem Rahmenfalz). Start = Mitte Steg Seite links; Maße in mm ab Start; "
                          "graue Felder = Biegezonen R98,5" % (L, H), fontsize=9, loc="left")
    fig.savefig(path, dpi=110)


# -------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", required=True, help="hardware/cad/homemy.step (Git LFS)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    ring, v_plain = build_ring()
    v = volume(ring)
    web_sectors = sectors(section_points(ring, Z_SCAN))
    edge_sectors = {z: sectors(section_points(ring, z)) for z in (Z_S0 + 0.5, Z_S1 - 0.5)}
    model = check_model(ring, args.model)

    # acceptance checks against the decision record
    assert len(web_sectors) == 6
    for name, (lo, hi) in RECORD_WEB_SECTORS.items():
        assert any(abs(s["von"] - lo) < 0.1 and abs(s["bis"] - hi) < 0.1 for s in web_sectors), (name, web_sectors)
    struts = sorted((s["von"], s["bis"]) for s in model["strut_sectors"])
    assert len(struts) == 2
    for s in web_sectors + [x for z in edge_sectors.values() for x in z]:
        if 100 < abs(s["von"]) < 150:  # side web: must stay inside the strut shadow
            assert any(a <= s["von"] and s["bis"] <= b for a, b in struts), (s, struts)
    assert all(v_ <= 1e-3 for _, v_ in model["ring_overlap_mm3"]), model["ring_overlap_mm3"]

    dev = development()
    export_step(ring, args.out + "/freie_sicht_fuer_lidar.step")
    export_dxf(dev, args.out + "/freie_sicht_fuer_lidar_abwicklung.dxf")
    export_drawing(ring, dev, web_sectors, args.out + "/freie_sicht_fuer_lidar.png")
    report = {
        "body": BODY_NAME,
        "model": "hardware/cad/homemy.step V2",
        "ring": {"aussen_x": 2 * OUT_X, "aussen_y": 2 * OUT_Y, "eckradius_aussen": OUT_R, "dicke": T,
                 "z_unten": Z_BOT, "z_oben": Z_TOP},
        "schlitz": {"z_unten": Z_S0, "z_oben": Z_S1, "z_scan": Z_SCAN, "eckradius": R_CORNER,
                    "ueber_boden": [round(Z_S0 - FLOOR_Z, 1), round(Z_S1 - FLOOR_Z, 1)]},
        "stege_modellkoordinaten": [{"name": n, "x": [x0, x1], "y": [y0, y1]} for n, x0, x1, y0, y1 in WEBS],
        "volumen_mm3": {"ring_ohne_schlitz": round(v_plain), "ring_mit_schlitz": round(v)},
        "masse_g_pmma": round(v * 1.19e-3),
        "blinde_winkel_stege_scanebene": web_sectors,
        "blinde_winkel_stege_schlitzrand": {str(k): x for k, x in edge_sectors.items()},
        "blinde_winkel_streben": model["strut_sectors"],
        "modellpruefung": {"solids": model["model_solids"], "in_scanebene": model["scan_plane_solids"],
                           "ueberlappung_mit_ring_mm3": model["ring_overlap_mm3"]},
        "abwicklung": dev,
    }
    with open(args.out + "/freie_sicht_fuer_lidar.json", "w") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
    print(json.dumps({k: report[k] for k in ("volumen_mm3", "blinde_winkel_stege_scanebene",
                                             "blinde_winkel_streben")}, indent=1, ensure_ascii=False))
    print("slots on the strip:", [(s["von"], s["bis"]) for s in dev["slots"]])


if __name__ == "__main__":
    main()
