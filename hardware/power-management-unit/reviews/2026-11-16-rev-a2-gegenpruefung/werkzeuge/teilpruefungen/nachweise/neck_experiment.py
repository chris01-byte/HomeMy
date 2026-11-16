# Sensitivity experiment (reviewer's own, NOT part of the committed method):
# morphological opening of the checker's own copper model; a pair "survives width w" if both pads
# touch the same outline after removing every feature narrower than w.
import sys, json, math, collections, time
from power_native_reader import main, pcb
from build_board import point, mm
b,polys,paths,zones,tap_ids,digest=main()
fps={f.GetReference():f for f in b.GetFootprints()}
L={'F.Cu':pcb.F_Cu,'In1.Cu':pcb.In1_Cu,'In2.Cu':pcb.In2_Cu,'B.Cu':pcb.B_Cu}
def padobj(label):
    ref,num=label.split('.')
    return next(p for p in fps[ref].Pads() if p.GetNumber()==num)
def padpoly(p,layer):
    q=pcb.SHAPE_POLY_SET();p.TransformShapeToPolygon(q,layer,0,mm(.005),pcb.ERROR_INSIDE);return q
# variant B: fill via drills back in (webs between vias treated as solid copper)
viafill={}
for t in b.GetTracks():
    if isinstance(t,pcb.PCB_VIA):
        n=t.GetNetname()
        for ln,l in L.items():
            if (n,l) in polys and t.IsOnLayer(l):
                d=pcb.ToMM(t.GetDrillValue());x,y=pcb.ToMM(t.GetPosition().x),pcb.ToMM(t.GetPosition().y)
                h=pcb.SHAPE_POLY_SET();h.NewOutline()
                for k in range(40):h.Append(mm(x+(d/2+.01)*math.cos(2*math.pi*k/40)),mm(y+(d/2+.01)*math.sin(2*math.pi*k/40)))
                viafill.setdefault((n,l),pcb.SHAPE_POLY_SET()).Append(h)
needed={(r['net'],L[r['layer']]) for r in paths}
def opened(q,r):
    c=pcb.SHAPE_POLY_SET(q)
    c.Deflate(mm(r),pcb.CORNER_STRATEGY_ROUND_ALL_CORNERS,mm(.005))
    c.Inflate(mm(r),pcb.CORNER_STRATEGY_ROUND_ALL_CORNERS,mm(.005))
    c.Simplify();c.BuildBBoxCaches();return c
def touching(q,pp):
    ids=set()
    for i in range(q.OutlineCount()):
        one=pcb.SHAPE_POLY_SET(q.UnitSet(i)) if hasattr(q,'UnitSet') else None
        if one is None:
            one=pcb.SHAPE_POLY_SET();one.AddOutline(q.COutline(i))
            for h in range(q.HoleCount(i)):one.AddHole(q.CHole(i,h),0) if False else None
        x=pcb.SHAPE_POLY_SET(one);x.BooleanIntersection(pp)
        if x.OutlineCount()>0 and x.Area()>1e6*1e6*0.01: ids.add(i)   # >0.01 mm2 overlap
    return ids
widths=[0.3,0.5,1.0,1.5,2.0,3.0,4.0]
out={}
for variant in ['A_model_as_checked','B_via_drills_filled']:
    res=collections.defaultdict(dict)
    for w in widths:
        t0=time.time();cache={}
        for key in needed:
            q=pcb.SHAPE_POLY_SET(polys[key])
            if variant.startswith('B') and key in viafill:
                vf=pcb.SHAPE_POLY_SET(viafill[key]);vf.Simplify();q.BooleanAdd(vf);q.Simplify()
            cache[key]=opened(q,w/2)
        for idx,r in enumerate(paths):
            key=(r['net'],L[r['layer']]);q=cache[key]
            pa=padpoly(padobj(r['from_pad']),key[1]);pb=padpoly(padobj(r['to_pad']),key[1])
            ia=touching(q,pa);ib=touching(q,pb)
            res[idx][w]=bool(ia&ib)
        print(variant,'w>=',w,'mm: pairs surviving',sum(res[i][w] for i in res),'/',len(paths),'(%.1fs)'%(time.time()-t0),flush=True)
    out[variant]={i:res[i] for i in res}
rows=[]
for idx,r in enumerate(paths):
    rows.append(dict(net=r['net'],layer=r['layer'],from_pad=r['from_pad'],to_pad=r['to_pad'],
                     A={str(w):out['A_model_as_checked'][idx][w] for w in widths},B={str(w):out['B_via_drills_filled'][idx][w] for w in widths}))
json.dump(rows,open(sys.argv[1],'w'),indent=1)
