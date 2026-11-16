import pcbnew, collections
PCB='<SITZUNG>/pmu/hardware/power-management-unit/rev-a2-layout-280x260/kicad/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(PCB)
mm=pcbnew.ToMM
d=collections.defaultdict(lambda: collections.defaultdict(int))
for f in b.GetFootprints():
    fp=str(f.GetFPID().GetUniStringLibId()).split(':')[-1]
    for p in f.Pads():
        ds=p.GetDrillSize()
        if ds.x>0:
            attr={pcbnew.PAD_ATTRIB_PTH:'PTH',pcbnew.PAD_ATTRIB_NPTH:'NPTH'}.get(p.GetAttribute(),'?')
            sz=p.GetSize(pcbnew.F_Cu)
            key=(fp[:60],attr,round(mm(ds.x),3),round(mm(ds.y),3),round(mm(sz.x),3),round(mm(sz.y),3))
            d[key][f.GetReference()]+=1
for k in sorted(d):
    refs=sorted(d[k])
    print(f"{k[0]:<62} {k[1]:<4} drill {k[2]}x{k[3]} pad {k[4]}x{k[5]}  n={sum(d[k].values())} refs={' '.join(refs[:10])}{' ...' if len(refs)>10 else ''}")
vias=collections.Counter()
for t in b.GetTracks():
    if t.Type()==pcbnew.PCB_VIA_T:
        vias[(round(mm(t.GetDrillValue()),3),round(mm(t.GetWidth(pcbnew.F_Cu)),3))]+=1
print('vias (drill,dia):',dict(vias))
