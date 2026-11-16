import pcbnew as pcb, sys
b=pcb.LoadBoard(sys.argv[1]+'/a2/kicad/HomeMy_PMU_RevA.kicad_pcb')
f=b.FindFootprintByReference('U10')
print('U10 pos',pcb.ToMM(f.GetPosition().x),pcb.ToMM(f.GetPosition().y),'rot',f.GetOrientationDegrees())
f.BuildCourtyardCaches(); c=f.GetCourtyard(pcb.F_Cu); bb=c.BBox()
print('courtyard bbox mm',[round(pcb.ToMM(x),3) for x in (bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())],'board 0..280 x 0..260')
xs=[pcb.ToMM(p.GetPosition().x) for p in f.Pads()]; ys=[pcb.ToMM(p.GetPosition().y) for p in f.Pads()]
print('pad centre extents x',min(xs),max(xs),'y',min(ys),max(ys))
for z in f.Zones():
    o=z.Outline(); zb=o.BBox(); print('  footprint zone rule_area',z.GetIsRuleArea(),'layers',[b.GetLayerName(l) for l in z.GetLayerSet().Seq()],'bbox',[round(pcb.ToMM(x),3) for x in (zb.GetX(),zb.GetY(),zb.GetRight(),zb.GetBottom())],'no tracks/vias/pads/copper',z.GetDoNotAllowTracks(),z.GetDoNotAllowVias(),z.GetDoNotAllowPads(),z.GetDoNotAllowZoneFills() if hasattr(z,'GetDoNotAllowZoneFills') else z.GetDoNotAllowCopperPour())
fb=f.GetBoundingBox(False); print('fp bbox (no text)',[round(pcb.ToMM(x),3) for x in (fb.GetX(),fb.GetY(),fb.GetRight(),fb.GetBottom())])
