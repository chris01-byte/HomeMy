import pcbnew as pcb, sys, collections
S=sys.argv[1]
for name,path in [('A2',S+'/a2/kicad/HomeMy_PMU_RevA.kicad_pcb'),('rev-a',S+'/reva/kicad/HomeMy_PMU_RevA.kicad_pcb')]:
    b=pcb.LoadBoard(path)
    print('=====',name)
    c=collections.Counter()
    for d in b.GetDrawings():
        c[(type(d).__name__,b.GetLayerName(d.GetLayer()))]+=1
        if isinstance(d,(pcb.PCB_TEXT,pcb.PCB_TEXTBOX)):
            t=d.GetText().replace('\n',' / ')
            if any(k in t.upper() for k in ['REV','RELEASE','DRAFT','WIP','HOMEMY','PMU','PROTO','NICHT','NOT ','280','360','300']):
                print('  ',b.GetLayerName(d.GetLayer()),'(%.1f,%.1f)'%(pcb.ToMM(d.GetPosition().x),pcb.ToMM(d.GetPosition().y)),'h=%.1f'%pcb.ToMM(d.GetTextHeight()),repr(t[:160]))
    print('  drawings by type/layer',dict(c))
