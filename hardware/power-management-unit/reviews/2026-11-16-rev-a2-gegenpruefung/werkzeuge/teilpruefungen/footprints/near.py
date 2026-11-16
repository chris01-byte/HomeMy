import pcbnew, sys, math
PCB='<SITZUNG>/pmu/hardware/power-management-unit/rev-a2-layout-280x260/kicad/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(PCB)
mm=pcbnew.ToMM
def box_of_pad(ref,num):
    f=b.FindFootprintByReference(ref)
    out=[]
    for p in f.Pads():
        if p.GetNumber()==num:
            bb=p.GetBoundingBox()
            out.append((mm(bb.GetLeft()),mm(bb.GetTop()),mm(bb.GetRight()),mm(bb.GetBottom())))
    x0=min(o[0] for o in out); y0=min(o[1] for o in out); x1=max(o[2] for o in out); y1=max(o[3] for o in out)
    return (x0,y0,x1,y1)
def report(name,box,margin=0.0):
    x0,y0,x1,y1=box; x0-=margin;y0-=margin;x1+=margin;y1+=margin
    print(f"## {name}: region x[{x0:.3f},{x1:.3f}] y[{y0:.3f},{y1:.3f}] (margin {margin})")
    n=0
    for t in b.GetTracks():
        if t.Type()==pcbnew.PCB_VIA_T:
            p=t.GetPosition(); r=mm(t.GetWidth(pcbnew.F_Cu))/2
            px,py=mm(p.x),mm(p.y)
            if px+r>=x0 and px-r<=x1 and py+r>=y0 and py-r<=y1:
                print(f"   VIA net={t.GetNetname()} at ({px:.3f},{py:.3f}) dia {2*r:.2f} drill {mm(t.GetDrillValue()):.2f}"); n+=1
        else:
            s=t.GetStart(); e=t.GetEnd(); w=mm(t.GetWidth())/2
            sx,sy,ex,ey=mm(s.x),mm(s.y),mm(e.x),mm(e.y)
            # bbox test
            if max(sx,ex)+w>=x0 and min(sx,ex)-w<=x1 and max(sy,ey)+w>=y0 and min(sy,ey)-w<=y1:
                # finer: sample points along segment
                hit=False
                L=math.hypot(ex-sx,ey-sy); k=max(2,int(L/0.02)+1)
                for i in range(k+1):
                    px=sx+(ex-sx)*i/k; py=sy+(ey-sy)*i/k
                    if px+w>=x0 and px-w<=x1 and py+w>=y0 and py-w<=y1: hit=True;break
                if hit:
                    print(f"   TRACK net={t.GetNetname()} layer={b.GetLayerName(t.GetLayer())} ({sx:.3f},{sy:.3f})->({ex:.3f},{ey:.3f}) w={2*w:.2f}"); n+=1
    # zones: sample grid points inside region and test fills
    for z in b.Zones():
        if z.GetIsRuleArea(): continue
        for layer in z.GetLayerSet().Seq():
            poly=z.GetFilledPolysList(layer)
            hit=0; tot=0
            nx=max(2,int((x1-x0)/0.05)); ny=max(2,int((y1-y0)/0.05))
            for i in range(nx+1):
                for j in range(ny+1):
                    px=x0+(x1-x0)*i/nx; py=y0+(y1-y0)*j/ny
                    tot+=1
                    if poly.Contains(pcbnew.VECTOR2I(pcbnew.FromMM(px),pcbnew.FromMM(py))): hit+=1
            if hit:
                print(f"   ZONE net={z.GetNetname()} layer={b.GetLayerName(layer)} name={z.GetZoneName()} covers {hit}/{tot} sample pts"); n+=1
    for f in b.GetFootprints():
        for p in f.Pads():
            bb=p.GetBoundingBox()
            if mm(bb.GetRight())>=x0 and mm(bb.GetLeft())<=x1 and mm(bb.GetBottom())>=y0 and mm(bb.GetTop())<=y1:
                print(f"   PAD {f.GetReference()}.{p.GetNumber()} net={p.GetNetname()} layers={'F' if p.IsOnLayer(pcbnew.F_Cu) else ''}{'B' if p.IsOnLayer(pcbnew.B_Cu) else ''} bbox x[{mm(bb.GetLeft()):.3f},{mm(bb.GetRight()):.3f}] y[{mm(bb.GetTop()):.3f},{mm(bb.GetBottom()):.3f}]"); n+=1
    if n==0: print("   (nothing)")
if __name__=='__main__':
    ref=sys.argv[1]; num=sys.argv[2]; margin=float(sys.argv[3]) if len(sys.argv)>3 else 0.0
    report(f"{ref} pad {num}", box_of_pad(ref,num), margin)
