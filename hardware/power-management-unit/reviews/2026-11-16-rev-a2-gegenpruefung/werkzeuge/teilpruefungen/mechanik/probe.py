import pcbnew
B='<SITZUNG>/agents/mech/proj/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(B)
mm=pcbnew.ToMM
zs=list(b.Zones())
z=zs[0]
print([m for m in dir(z) if 'Fill' in m or 'Poly' in m])
for z in zs[:5]:
    for l in z.GetLayerSet().Seq():
        ps=z.GetFilledPolysList(l)
        print(z.GetNetname(), b.GetLayerName(l), 'outlines',ps.OutlineCount(), 'holes',[ps.HoleCount(i) for i in range(min(ps.OutlineCount(),5))], 'area mm2', ps.Area()/1e12)
pad=[p for fp in b.GetFootprints() if fp.GetReference()=='NT1' for p in fp.Pads()][0]
print([m for m in dir(pad) if 'Poly' in m or 'Mask' in m or 'Shape' in m])
fp=[f for f in b.GetFootprints() if f.GetReference()=='NT1'][0]
for g in fp.GraphicalItems():
    print(g.GetClass(), b.GetLayerName(g.GetLayer()), g.ShowShape() if hasattr(g,'ShowShape') else '', g.IsFilled() if hasattr(g,'IsFilled') else '')
print('board drawings on Cu:')
for g in b.GetDrawings():
    if g.GetLayer() in (pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.F_Mask,pcbnew.B_Mask):
        print(g.GetClass(), b.GetLayerName(g.GetLayer()))
print('dwg layers', __import__('collections').Counter(b.GetLayerName(g.GetLayer()) for g in b.GetDrawings()))
# footprints with graphic items on copper/mask
import collections
c=collections.Counter()
for f in b.GetFootprints():
    for g in f.GraphicalItems():
        if g.GetLayer() in (pcbnew.F_Cu,pcbnew.B_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.F_Mask,pcbnew.B_Mask):
            c[(f.GetReference(),b.GetLayerName(g.GetLayer()),g.GetClass())]+=1
print(c)
# zones inside footprints?
for f in b.GetFootprints():
    if len(list(f.Zones()))>0:
        print('fp zones', f.GetReference(), [(zz.GetIsRuleArea(), [b.GetLayerName(l) for l in zz.GetLayerSet().Seq()]) for zz in f.Zones()])
