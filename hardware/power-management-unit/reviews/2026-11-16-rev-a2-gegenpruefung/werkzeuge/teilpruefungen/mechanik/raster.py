import pcbnew, numpy as np, json, sys, time
from PIL import Image, ImageDraw
B='<SITZUNG>/agents/mech/proj/HomeMy_PMU_RevA.kicad_pcb'
OUT='<SITZUNG>/agents/mech/'
RES=20
W,H=280*RES,260*RES
b=pcbnew.LoadBoard(B)
mm=pcbnew.ToMM
layers={'F.Cu':pcbnew.F_Cu,'In1.Cu':pcbnew.In1_Cu,'In2.Cu':pcbnew.In2_Cu,'B.Cu':pcbnew.B_Cu}
nets={}
for code,ni in b.GetNetsByNetcode().items():
    nets[int(code)]=ni.GetNetname()
json.dump(nets,open(OUT+'nets.json','w'))
NETTIE=60000
def poly_pts(chain):
    return [(mm(chain.CPoint(k).x)*RES, mm(chain.CPoint(k).y)*RES) for k in range(chain.PointCount())]
def draw_polyset(arr, ps, code):
    for i in range(ps.OutlineCount()):
        o=ps.Outline(i)
        pts=poly_pts(o)
        if len(pts)<3: continue
        xs=[p[0] for p in pts]; ys=[p[1] for p in pts]
        x0=max(int(min(xs))-2,0); y0=max(int(min(ys))-2,0); x1=min(int(max(xs))+3,W); y1=min(int(max(ys))+3,H)
        if x1<=x0 or y1<=y0: continue
        img=Image.new('1',(x1-x0,y1-y0),0)
        d=ImageDraw.Draw(img)
        d.polygon([(x-x0,y-y0) for x,y in pts],fill=1)
        for j in range(ps.HoleCount(i)):
            hp=poly_pts(ps.Hole(i,j))
            if len(hp)>=3:
                d.polygon([(x-x0,y-y0) for x,y in hp],fill=0)
        m=np.array(img,dtype=bool)
        arr[y0:y1,x0:x1][m]=code
def draw_circle(arr,x,y,dia,code):
    r=dia/2*RES; cx=x*RES; cy=y*RES
    x0=max(int(cx-r)-2,0); y0=max(int(cy-r)-2,0); x1=min(int(cx+r)+3,W); y1=min(int(cy+r)+3,H)
    yy,xx=np.mgrid[y0:y1,x0:x1]
    m=((xx-cx)**2+(yy-cy)**2)<=r*r
    arr[y0:y1,x0:x1][m]=code
def draw_seg(arr,x1,y1,x2,y2,w,code):
    r=w/2*RES
    ax,ay,bx,by=x1*RES,y1*RES,x2*RES,y2*RES
    x0=max(int(min(ax,bx)-r)-2,0); y0=max(int(min(ay,by)-r)-2,0); xe=min(int(max(ax,bx)+r)+3,W); ye=min(int(max(ay,by)+r)+3,H)
    if xe<=x0 or ye<=y0: return
    yy,xx=np.mgrid[y0:ye,x0:xe]
    dx,dy=bx-ax,by-ay
    L2=dx*dx+dy*dy
    if L2==0:
        t=np.zeros_like(xx,dtype=float)
    else:
        t=np.clip(((xx-ax)*dx+(yy-ay)*dy)/L2,0,1)
    px=ax+t*dx; py=ay+t*dy
    m=((xx-px)**2+(yy-py)**2)<=r*r
    arr[y0:ye,x0:xe][m]=code
t0=time.time()
res={}
for lname,lid in layers.items():
    arr=np.zeros((H,W),dtype=np.uint16)
    # zones
    for z in b.Zones():
        if z.GetIsRuleArea(): continue
        if not z.IsOnLayer(lid): continue
        ps=z.GetFilledPolysList(lid)
        draw_polyset(arr,ps,z.GetNetCode())
    # footprint graphics on copper
    for fp in b.GetFootprints():
        for g in fp.GraphicalItems():
            if g.GetClass()=='PCB_SHAPE' and g.GetLayer()==lid:
                ps=pcbnew.SHAPE_POLY_SET()
                g.TransformShapeToPolygon(ps,lid,0,5000,pcbnew.ERROR_INSIDE)
                draw_polyset(arr,ps,NETTIE)
    # tracks
    for t in b.GetTracks():
        if t.GetClass()=='PCB_VIA': continue
        if t.GetLayer()!=lid: continue
        s=t.GetStart(); e=t.GetEnd()
        draw_seg(arr,mm(s.x),mm(s.y),mm(e.x),mm(e.y),mm(t.GetWidth()),t.GetNetCode())
    # pads
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if not pad.IsOnLayer(lid): continue
            try:
                if not pad.FlashLayer(lid): continue
            except Exception as ex:
                pass
            ps=pcbnew.SHAPE_POLY_SET()
            pad.TransformShapeToPolygon(ps,lid,0,5000,pcbnew.ERROR_INSIDE)
            code=pad.GetNetCode()
            if code==0: code=59999  # unconnected pad copper
            draw_polyset(arr,ps,code)
    # vias
    for t in b.GetTracks():
        if t.GetClass()!='PCB_VIA': continue
        if not t.IsOnLayer(lid): continue
        try:
            if not t.FlashLayer(lid): continue
        except Exception: pass
        p=t.GetPosition()
        draw_circle(arr,mm(p.x),mm(p.y),mm(t.GetWidth(lid)),t.GetNetCode())
    res[lname]=arr
    print(lname,'done',time.time()-t0,'copper frac',(arr>0).mean())
# holes
hole=np.zeros((H,W),dtype=np.uint8)
for fp in b.GetFootprints():
    for pad in fp.Pads():
        d=pad.GetDrillSize()
        if d.x>0:
            p=pad.GetPosition()
            if d.x==d.y:
                draw_circle(hole,mm(p.x),mm(p.y),mm(d.x),1)
            else:
                print('oval hole',fp.GetReference(),pad.GetNumber(),mm(d.x),mm(d.y))
                draw_circle(hole,mm(p.x),mm(p.y),max(mm(d.x),mm(d.y)),1)
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA':
        p=t.GetPosition()
        draw_circle(hole,mm(p.x),mm(p.y),mm(t.GetDrillValue()),1)
# mask openings
masks={}
for mname,mid in {'F.Mask':pcbnew.F_Mask,'B.Mask':pcbnew.B_Mask}.items():
    arr=np.zeros((H,W),dtype=np.uint8)
    for fp in b.GetFootprints():
        for pad in fp.Pads():
            if not pad.IsOnLayer(mid): continue
            ps=pcbnew.SHAPE_POLY_SET()
            try:
                exp=pad.GetSolderMaskExpansion(mid)
            except TypeError:
                exp=pad.GetSolderMaskExpansion()
            cul=pcbnew.F_Cu if mid==pcbnew.F_Mask else pcbnew.B_Cu
            pad.TransformShapeToPolygon(ps,cul if pad.IsOnLayer(cul) else mid,exp,5000,pcbnew.ERROR_OUTSIDE)
            draw_polyset(arr,ps,1)
        for g in fp.GraphicalItems():
            if g.GetClass()=='PCB_SHAPE' and g.GetLayer()==mid:
                ps=pcbnew.SHAPE_POLY_SET()
                g.TransformShapeToPolygon(ps,mid,0,5000,pcbnew.ERROR_INSIDE)
                draw_polyset(arr,ps,1)
    masks[mname]=arr
    print(mname,'open frac',arr.mean())
np.savez_compressed(OUT+'raster.npz',F=res['F.Cu'],I1=res['In1.Cu'],I2=res['In2.Cu'],B=res['B.Cu'],hole=hole,FM=masks['F.Mask'],BM=masks['B.Mask'])
print('saved',time.time()-t0)
