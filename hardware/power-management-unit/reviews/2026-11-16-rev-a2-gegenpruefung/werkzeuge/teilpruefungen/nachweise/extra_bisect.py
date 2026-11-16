import sys, json, math, os
from power_native_reader_param import main, pcb
from build_board import point, mm
b,polys,paths,zones,tap_ids,digest=main()
fps={f.GetReference():f for f in b.GetFootprints()}
L={'F.Cu':pcb.F_Cu,'In1.Cu':pcb.In1_Cu,'In2.Cu':pcb.In2_Cu,'B.Cu':pcb.B_Cu}
def padobj(label):
    ref,num=label.split('.');return next(p for p in fps[ref].Pads() if p.GetNumber()==num)
def padpoly(p,layer):
    q=pcb.SHAPE_POLY_SET();p.TransformShapeToPolygon(q,layer,0,mm(.005),pcb.ERROR_INSIDE);return q
def base(net,l):
    q=pcb.SHAPE_POLY_SET(polys[(net,l)]);vf=pcb.SHAPE_POLY_SET()
    for t in b.GetTracks():
        if isinstance(t,pcb.PCB_VIA) and t.GetNetname()==net and t.IsOnLayer(l):
            d=pcb.ToMM(t.GetDrillValue());x,y=pcb.ToMM(t.GetPosition().x),pcb.ToMM(t.GetPosition().y)
            h=pcb.SHAPE_POLY_SET();h.NewOutline()
            for k in range(40):h.Append(mm(x+(d/2+.01)*math.cos(2*math.pi*k/40)),mm(y+(d/2+.01)*math.sin(2*math.pi*k/40)))
            vf.Append(h)
    if vf.OutlineCount(): vf.Simplify();q.BooleanAdd(vf);q.Simplify()
    return q
cache={}
def opened(net,l,w):
    k=(net,l,w)
    if k not in cache:
        if (net,l,'base') not in cache: cache[(net,l,'base')]=base(net,l)
        c=pcb.SHAPE_POLY_SET(cache[(net,l,'base')])
        if w>0: c.Deflate(mm(w/2),pcb.CORNER_STRATEGY_ROUND_ALL_CORNERS,mm(.005));c.Inflate(mm(w/2),pcb.CORNER_STRATEGY_ROUND_ALL_CORNERS,mm(.005))
        c.Simplify();cache[k]=c
    return cache[k]
def touching(q,pp):
    ids=set()
    for i in range(q.OutlineCount()):
        x=pcb.SHAPE_POLY_SET(q.UnitSet(i));x.BooleanIntersection(pp)
        if x.OutlineCount()>0 and x.Area()>1e10: ids.add(i)
    return ids
def survive(net,l,a,c,w):
    q=opened(net,l,w);return bool(touching(q,padpoly(padobj(a),l))&touching(q,padpoly(padobj(c),l)))
grid=[round(0.1*i,1) for i in range(0,201)]
for net,a,c in json.loads(os.environ['PAIRS']):
    row=[]
    for ln,l in L.items():
        if (net,l) not in polys or not survive(net,l,a,c,0): row.append((ln,None)); continue
        lo,hi=0,len(grid)-1
        if survive(net,l,a,c,grid[hi]): row.append((ln,'>=20')); continue
        while hi-lo>1:
            mid=(lo+hi)//2
            if survive(net,l,a,c,grid[mid]): lo=mid
            else: hi=mid
        row.append((ln,grid[lo]))
    pa=padobj(a).GetPosition(); pc=padobj(c).GetPosition()
    print(net,a,'(%.0f,%.0f)'%(pcb.ToMM(pa.x),pcb.ToMM(pa.y)),'->',c,'(%.0f,%.0f)'%(pcb.ToMM(pc.x),pcb.ToMM(pc.y)),'widest same-layer corridor mm (None = not connected on that layer):',row)
