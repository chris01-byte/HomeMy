# Reviewer's own sensitivity experiment: per-pair widest-corridor bottleneck in the checker's copper model.
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
base={'A':{},'B':{}}
for key in {(r['net'],L[r['layer']]) for r in paths}:
    base['A'][key]=pcb.SHAPE_POLY_SET(polys[key])
    q=pcb.SHAPE_POLY_SET(polys[key])
    if key in viafill:
        vf=pcb.SHAPE_POLY_SET(viafill[key]);vf.Simplify();q.BooleanAdd(vf);q.Simplify()
    base['B'][key]=q
cache={}
def opened(var,key,w):
    k=(var,key,round(w,3))
    if k not in cache:
        c=pcb.SHAPE_POLY_SET(base[var][key])
        if w>0:
            c.Deflate(mm(w/2),pcb.CORNER_STRATEGY_ROUND_ALL_CORNERS,mm(.005));c.Inflate(mm(w/2),pcb.CORNER_STRATEGY_ROUND_ALL_CORNERS,mm(.005))
        c.Simplify();c.BuildBBoxCaches();cache[k]=c
    return cache[k]
def touching(q,pp):
    ids=set()
    for i in range(q.OutlineCount()):
        x=pcb.SHAPE_POLY_SET(q.UnitSet(i));x.BooleanIntersection(pp)
        if x.OutlineCount()>0 and x.Area()>1e10: ids.add(i)
    return ids
grid=[round(0.1*i,1) for i in range(0,201)]  # 0..20 mm
def survive(var,r,w):
    key=(r['net'],L[r['layer']]);q=opened(var,key,w)
    pa=padpoly(padobj(r['from_pad']),key[1]);pb=padpoly(padobj(r['to_pad']),key[1])
    return bool(touching(q,pa)&touching(q,pb))
rows=[]
for idx,r in enumerate(paths):
    row=dict(net=r['net'],layer=r['layer'],from_pad=r['from_pad'],to_pad=r['to_pad'])
    for var in 'AB':
        lo,hi=0,len(grid)-1
        if not survive(var,r,grid[0]): row[var]=None; continue
        if survive(var,r,grid[hi]): row[var]=grid[hi]; continue
        while hi-lo>1:
            mid=(lo+hi)//2
            if survive(var,r,grid[mid]): lo=mid
            else: hi=mid
        row[var]=grid[lo]
    rows.append(row)
    if idx%40==0: print(idx,row,flush=True)
json.dump(rows,open(sys.argv[1],'w'),indent=1)
