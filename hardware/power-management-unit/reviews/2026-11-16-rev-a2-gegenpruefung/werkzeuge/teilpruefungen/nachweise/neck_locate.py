import sys, json, math, os
from power_native_reader_param import main, pcb
from build_board import point, mm
b,polys,paths,zones,tap_ids,digest=main()
fps={f.GetReference():f for f in b.GetFootprints()}
L={'F.Cu':pcb.F_Cu,'In1.Cu':pcb.In1_Cu,'In2.Cu':pcb.In2_Cu,'B.Cu':pcb.B_Cu}
def bbox(q):
    bb=q.BBox(); return [round(pcb.ToMM(bb.GetX()),2),round(pcb.ToMM(bb.GetY()),2),round(pcb.ToMM(bb.GetRight()),2),round(pcb.ToMM(bb.GetBottom()),2)]
def padpoly(label,layer):
    ref,num=label.split('.');p=next(p for p in fps[ref].Pads() if p.GetNumber()==num)
    q=pcb.SHAPE_POLY_SET();p.TransformShapeToPolygon(q,layer,0,mm(.005),pcb.ERROR_INSIDE);return q,(round(pcb.ToMM(p.GetPosition().x),2),round(pcb.ToMM(p.GetPosition().y),2))
def viafilled(net,l):
    q=pcb.SHAPE_POLY_SET(polys[(net,l)])
    vf=pcb.SHAPE_POLY_SET()
    for t in b.GetTracks():
        if isinstance(t,pcb.PCB_VIA) and t.GetNetname()==net and t.IsOnLayer(l):
            d=pcb.ToMM(t.GetDrillValue());x,y=pcb.ToMM(t.GetPosition().x),pcb.ToMM(t.GetPosition().y)
            h=pcb.SHAPE_POLY_SET();h.NewOutline()
            for k in range(40):h.Append(mm(x+(d/2+.01)*math.cos(2*math.pi*k/40)),mm(y+(d/2+.01)*math.sin(2*math.pi*k/40)))
            vf.Append(h)
    if vf.OutlineCount(): vf.Simplify();q.BooleanAdd(vf);q.Simplify()
    return q
def opened(q,w):
    c=pcb.SHAPE_POLY_SET(q);c.Deflate(mm(w/2),pcb.CORNER_STRATEGY_ROUND_ALL_CORNERS,mm(.005));c.Inflate(mm(w/2),pcb.CORNER_STRATEGY_ROUND_ALL_CORNERS,mm(.005));c.Simplify();return c
cases=json.loads(os.environ['CASES'])
for net,layer,a,c_,w in cases:
    l=L[layer];q=viafilled(net,l)
    print('==',net,layer,a,'->',c_,'test width',w,'| net/layer polygon bbox',bbox(q),'outlines',q.OutlineCount(),'area mm2',round(q.Area()/1e12,1))
    pa,ca=padpoly(a,l);pb,cb=padpoly(c_,l);print('   pad centers',a,ca,c_,cb)
    o=opened(q,w)
    def comp(pp):
        ids=[]
        for i in range(o.OutlineCount()):
            x=pcb.SHAPE_POLY_SET(o.UnitSet(i));x.BooleanIntersection(pp)
            if x.OutlineCount()>0 and x.Area()>1e10: ids.append(i)
        return ids
    ia,ib=comp(pa),comp(pb);print('   opened outlines',o.OutlineCount(),'from in',ia,'to in',ib)
    for i in set(ia)|set(ib):
        u=pcb.SHAPE_POLY_SET(o.UnitSet(i));print('      component',i,'bbox',bbox(u),'area',round(u.Area()/1e12,1))
    # removed parts
    rem=pcb.SHAPE_POLY_SET(q);rem.BooleanSubtract(o);rem.Simplify()
    # removed pieces touching both a from-component and a to-component (inflate slightly)
    for j in range(rem.OutlineCount()):
        piece=pcb.SHAPE_POLY_SET(rem.UnitSet(j))
        if piece.Area()<1e12*0.5: continue
        g=pcb.SHAPE_POLY_SET(piece);g.Inflate(mm(0.02),pcb.CORNER_STRATEGY_ROUND_ALL_CORNERS,mm(.005))
        def touches(i):
            x=pcb.SHAPE_POLY_SET(o.UnitSet(i));x.BooleanIntersection(g);return x.OutlineCount()>0
        ta=[i for i in ia if touches(i)];tb=[i for i in ib if touches(i)]
        if ta and tb and set(ta)!=set(tb): print('      NECK piece bbox',bbox(piece),'area',round(piece.Area()/1e12,2),'joins',ta,tb)
