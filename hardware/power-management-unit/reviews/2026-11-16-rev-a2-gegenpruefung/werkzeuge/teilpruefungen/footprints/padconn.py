import pcbnew, sys, math, collections
PCB='<SITZUNG>/pmu/hardware/power-management-unit/rev-a2-layout-280x260/kicad/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(PCB); mm=pcbnew.ToMM
zones=[z for z in b.Zones() if not z.GetIsRuleArea()]
bynet=collections.defaultdict(list)
for t in b.GetTracks(): bynet[t.GetNetname()].append(t)
def summarize(ref):
    f=b.FindFootprintByReference(ref)
    seen=set()
    for pad in f.Pads():
        num=pad.GetNumber()
        if num=='' : continue
        net=pad.GetNetname()
        bb=pad.GetBoundingBox()
        layers=[l for l in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.B_Cu) if pad.IsOnLayer(l)]
        zc=[]
        for z in zones:
            if z.GetNetname()!=net: continue
            for l in z.GetLayerSet().Seq():
                if l not in layers: continue
                poly=z.GetFilledPolysList(l); cnt=0; tot=0
                for i in range(7):
                    for j in range(7):
                        v=pcbnew.VECTOR2I(int(bb.GetLeft()+bb.GetWidth()*i/6), int(bb.GetTop()+bb.GetHeight()*j/6)); tot+=1
                        if poly.Contains(v): cnt+=1
                if cnt: zc.append(f"{b.GetLayerName(l)}:{cnt}/{tot}")
        tw=[]; vias=0
        for t in bynet[net]:
            if t.Type()==pcbnew.PCB_VIA_T:
                if bb.Contains(t.GetPosition()): vias+=1
            elif t.GetLayer() in layers and (bb.Contains(t.GetStart()) or bb.Contains(t.GetEnd())):
                tw.append(round(mm(t.GetWidth()),2))
        key=(num,net)
        print(f"   {ref}.{num:<3} {net:<18} pad {mm(pad.GetSize(pcbnew.F_Cu).x):.2f}x{mm(pad.GetSize(pcbnew.F_Cu).y):.2f}  zones[{', '.join(zc) or 'NONE'}]  tracks_w{sorted(tw)}  vias_in_pad={vias}")
for r in sys.argv[1:]: summarize(r)
