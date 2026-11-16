import pcbnew, json
B='<SITZUNG>/agents/mech/proj/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(B)
mm=pcbnew.ToMM
out=[]
for fp in b.GetFootprints():
    for pad in fp.Pads():
        rec={'ref':fp.GetReference(),'num':pad.GetNumber(),'net':pad.GetNetname(),'netclass':pad.GetNetClassName() if hasattr(pad,'GetNetClassName') else '', 'sides':{}}
        for side,cu,mk in (('F',pcbnew.F_Cu,pcbnew.F_Mask),('B',pcbnew.B_Cu,pcbnew.B_Mask)):
            if pad.IsOnLayer(cu) and pad.IsOnLayer(mk):
                ps=pcbnew.SHAPE_POLY_SET()
                pad.TransformShapeToPolygon(ps,cu,0,2000,pcbnew.ERROR_INSIDE)
                polys=[]
                for i in range(ps.OutlineCount()):
                    o=ps.Outline(i)
                    polys.append([(mm(o.CPoint(k).x),mm(o.CPoint(k).y)) for k in range(o.PointCount())])
                rec['sides'][side]=polys
        d=pad.GetDrillSize()
        rec['drill']=mm(d.x)
        p=pad.GetPosition(); rec['x']=mm(p.x); rec['y']=mm(p.y)
        out.append(rec)
# netclasses
nc={}
for code,ni in b.GetNetsByNetcode().items():
    try:
        nc[ni.GetNetname()]=ni.GetNetClass().GetName()
    except Exception as e:
        nc[ni.GetNetname()]='?'
json.dump({'pads':out,'netclass':nc},open('<SITZUNG>/agents/mech/pads_exposed.json','w'))
import collections
print(collections.Counter(nc.values()))
for k in ['PWR_BATTERY','PWR_SYS','PWR_MOTION','PWR_ARM']:
    print(k,[n for n,c in nc.items() if k in c])
