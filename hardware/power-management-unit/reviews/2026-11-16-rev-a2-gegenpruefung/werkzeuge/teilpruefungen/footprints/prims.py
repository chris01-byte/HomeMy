import sys
sys.path.insert(0,'<SITZUNG>/agents/footprints')
import sx, dump, os
path=sys.argv[1]
if not os.path.exists(path): path=os.path.join(dump.LIB,path)
f=sx.load_mod(path)
for pd in sx.pads_of(f):
    if not pd.custom: continue
    print('PAD',pd.num,'at',pd.x,pd.y,'rot',pd.rot,'anchor size',pd.w,pd.h, 'layers',pd.layers)
    opt=sx.find1(pd.raw,'options')
    if opt: print('  options',[[sx.S(v) for v in o] for o in opt[1:]])
    prim=sx.find1(pd.raw,'primitives')
    for g in prim[1:]:
        kind=g[0]
        if kind=='gr_poly':
            pts=sx.find1(g,'pts')
            xy=[(sx.num(p[1]),sx.num(p[2])) for p in pts[1:] if p[0]=='xy']
            w=sx.find1(g,'width'); fill=sx.find1(g,'fill')
            xs=[p[0]+pd.x for p in xy]; ys=[p[1]+pd.y for p in xy]
            print('  poly n=%d width=%s fill=%s  bbox(local fp coords) x[%.3f,%.3f] y[%.3f,%.3f]'%(len(xy),sx.S(w[1]) if w else None, sx.S(fill[1]) if fill else None,min(xs),max(xs),min(ys),max(ys)))
            print('     pts(fp coords):',[(round(p[0]+pd.x,3),round(p[1]+pd.y,3)) for p in xy])
        else:
            print('  ',kind,[[sx.S(v) if not isinstance(v,list) else [sx.S(u) for u in v] for v in c] if isinstance(c,list) else sx.S(c) for c in g[1:]])
