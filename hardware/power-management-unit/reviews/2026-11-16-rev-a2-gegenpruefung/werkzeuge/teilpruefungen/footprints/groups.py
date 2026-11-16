import pcbnew, collections
PCB='<SITZUNG>/pmu/hardware/power-management-unit/rev-a2-layout-280x260/kicad/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(PCB); mm=pcbnew.ToMM
for g in b.Groups():
    items=list(g.GetItems())
    nets=collections.Counter()
    for it in items:
        try: nets[it.GetNetname()]+=1
        except Exception: nets['?']+=1
    print('GROUP',g.GetName(),'items',len(items),dict(nets.most_common(14)))
    if g.GetName()=='PWR_TAP_CONTROL':
        # is D1's track in it?
        hit=[]
        for it in items:
            if it.Type()==pcbnew.PCB_TRACE_T:
                s=it.GetStart(); e=it.GetEnd()
                pts={(round(mm(s.x),3),round(mm(s.y),3)),(round(mm(e.x),3),round(mm(e.y),3))}
                if (35.0,72.87) in pts or (35.0,69.055) in pts or (108.0,84.055) in pts or (258.4,212.0) in pts or (225.0,192.4) in pts:
                    hit.append((it.GetNetname(),sorted(pts),mm(it.GetWidth())))
        print('   tracks ending at D1/D2/D60/D61 pad centres that are members:',hit)
