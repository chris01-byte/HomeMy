import pcbnew, sys, math, collections
PCB='<SITZUNG>/pmu/hardware/power-management-unit/rev-a2-layout-280x260/kicad/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(PCB); mm=pcbnew.ToMM
def key(p): return (round(mm(p.x),3),round(mm(p.y),3))
ref=sys.argv[1]; num=sys.argv[2]; maxsteps=int(sys.argv[3]) if len(sys.argv)>3 else 12
f=b.FindFootprintByReference(ref)
pad=[p for p in f.Pads() if p.GetNumber()==num][0]
net=pad.GetNetname()
tracks=[t for t in b.GetTracks() if t.GetNetname()==net]
print(f"## {ref}.{num} net {net}: pad centre {key(pad.GetPosition())} size {mm(pad.GetSize(pcbnew.F_Cu).x):.2f}x{mm(pad.GetSize(pcbnew.F_Cu).y):.2f}; net has {len(tracks)} track/via items")
# zones touching pad
for z in b.Zones():
    if z.GetIsRuleArea() or z.GetNetname()!=net: continue
    for layer in z.GetLayerSet().Seq():
        if not pad.IsOnLayer(layer): continue
        hit=z.GetFilledPolysList(layer).Contains(pad.GetPosition())
        # also sample pad bbox corners +- 
        bb=pad.GetBoundingBox(); cnt=0; tot=0
        for i in range(11):
            for j in range(11):
                v=pcbnew.VECTOR2I(int(bb.GetLeft()+bb.GetWidth()*i/10), int(bb.GetTop()+bb.GetHeight()*j/10)); tot+=1
                if z.GetFilledPolysList(layer).Contains(v): cnt+=1
        if cnt: print(f"   same-net ZONE on {b.GetLayerName(layer)} '{z.GetZoneName()}' covers {cnt}/{tot} pad-bbox sample points")
# tracks starting inside pad
bb=pad.GetBoundingBox()
def inpad(p): return bb.Contains(p)
front=[]; seen=set()
for t in tracks:
    if t.Type()==pcbnew.PCB_VIA_T:
        if inpad(t.GetPosition()): print(f"   VIA in pad at {key(t.GetPosition())} dia {mm(t.GetWidth(pcbnew.F_Cu)):.2f}/{mm(t.GetDrillValue()):.2f}")
    elif t.GetLayer()==pcbnew.F_Cu and (inpad(t.GetStart()) or inpad(t.GetEnd())):
        print(f"   TRACK leaving pad: {key(t.GetStart())}->{key(t.GetEnd())} w={mm(t.GetWidth()):.2f} len={mm(t.GetLength()):.2f}")
        front.append((t, t.GetEnd() if inpad(t.GetStart()) else t.GetStart())); seen.add(id(t))
# follow chain
steps=0
while front and steps<maxsteps:
    t,pt=front.pop(0); steps+=1
    for u in tracks:
        if id(u) in seen: continue
        if u.Type()==pcbnew.PCB_VIA_T:
            if key(u.GetPosition())==key(pt):
                seen.add(id(u)); print(f"      -> VIA at {key(pt)} dia {mm(u.GetWidth(pcbnew.F_Cu)):.2f}/{mm(u.GetDrillValue()):.2f}")
                # continue on other layers
                for w in tracks:
                    if id(w) in seen or w.Type()==pcbnew.PCB_VIA_T: continue
                    if key(w.GetStart())==key(pt) or key(w.GetEnd())==key(pt):
                        seen.add(id(w)); other=w.GetEnd() if key(w.GetStart())==key(pt) else w.GetStart()
                        print(f"         -> TRACK {b.GetLayerName(w.GetLayer())} {key(w.GetStart())}->{key(w.GetEnd())} w={mm(w.GetWidth()):.2f} len={mm(w.GetLength()):.2f}")
                        front.append((w,other))
                # zones at via
                for z in b.Zones():
                    if z.GetIsRuleArea() or z.GetNetname()!=net: continue
                    for layer in z.GetLayerSet().Seq():
                        if z.GetFilledPolysList(layer).Contains(u.GetPosition()): print(f"         -> via lands in same-net ZONE on {b.GetLayerName(layer)} '{z.GetZoneName()}'")
        elif u.GetLayer()==t.GetLayer() and (key(u.GetStart())==key(pt) or key(u.GetEnd())==key(pt)):
            seen.add(id(u)); other=u.GetEnd() if key(u.GetStart())==key(pt) else u.GetStart()
            print(f"      -> TRACK {b.GetLayerName(u.GetLayer())} {key(u.GetStart())}->{key(u.GetEnd())} w={mm(u.GetWidth()):.2f} len={mm(u.GetLength()):.2f}")
            front.append((u,other))
    # zone at point on F.Cu
    for z in b.Zones():
        if z.GetIsRuleArea() or z.GetNetname()!=net: continue
        if z.IsOnLayer(t.GetLayer()) and z.GetFilledPolysList(t.GetLayer()).Contains(pt): print(f"      (point {key(pt)} lies in same-net ZONE on {b.GetLayerName(t.GetLayer())} '{z.GetZoneName()}')")
