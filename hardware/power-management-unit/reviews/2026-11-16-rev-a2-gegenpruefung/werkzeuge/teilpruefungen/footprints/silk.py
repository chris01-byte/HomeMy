import pcbnew, collections, sys
PCB='<SITZUNG>/pmu/hardware/power-management-unit/rev-a2-layout-280x260/kicad/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(PCB)
mm=pcbnew.ToMM
for ref in sys.argv[1:]:
    f=b.FindFootprintByReference(ref)
    c=collections.Counter()
    for g in f.GraphicalItems():
        c[(b.GetLayerName(g.GetLayer()), g.GetClass())]+=1
    print(ref, dict(c), 'RefDes layer:', b.GetLayerName(f.Reference().GetLayer()), 'visible' if f.Reference().IsVisible() else 'hidden')
# board-level silk drawings count
c=collections.Counter()
for d in b.GetDrawings():
    c[(b.GetLayerName(d.GetLayer()), d.GetClass())]+=1
print('board drawings:',dict(c))
