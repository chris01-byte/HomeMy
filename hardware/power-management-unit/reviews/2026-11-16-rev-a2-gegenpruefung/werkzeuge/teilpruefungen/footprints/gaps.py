import sys, json, math, collections, itertools
sys.path.insert(0,'<SITZUNG>/agents/footprints')
import sx, dump
S='<SITZUNG>'
HV=set(json.load(open(S+'/out/hv_nets.json')))
root,fps=dump.board()
def shapes(pd,fprot):
    """return list of (x0,y0,x1,y1,r) inner rects + radius, in fp-local frame, for F.Cu copper."""
    if not any(l in ('F.Cu','*.Cu') for l in pd.layers): return []
    r=(pd.rot-fprot)%360
    w,h=pd.w,pd.h
    if abs(r-90)<1e-6 or abs(r-270)<1e-6: w,h=h,w
    out=[]
    if pd.shape=='circle':
        out.append((pd.x,pd.y,pd.x,pd.y,w/2))
    elif pd.shape=='oval':
        rad=min(w,h)/2
        out.append((pd.x-w/2+rad,pd.y-h/2+rad,pd.x+w/2-rad,pd.y+h/2-rad,rad))
    elif pd.shape=='roundrect':
        rad=(pd.rr or 0)*min(w,h)
        out.append((pd.x-w/2+rad,pd.y-h/2+rad,pd.x+w/2-rad,pd.y+h/2-rad,rad))
    elif pd.shape in('rect','custom'):
        out.append((pd.x-w/2,pd.y-h/2,pd.x+w/2,pd.y+h/2,0.0))
        if pd.custom:
            prim=sx.find1(pd.raw,'primitives')
            a=math.radians(pd.rot-fprot)
            for g in prim[1:]:
                if g[0]!='gr_poly': continue
                pts=sx.find1(g,'pts'); xy=[(sx.num(p[1]),sx.num(p[2])) for p in pts[1:] if p[0]=='xy']
                # primitives are in pad frame (rotate by pad-local rot). board file: pad rot includes fp rot -> use relative
                xs=[];ys=[]
                for (px,py) in xy:
                    # KiCad rotation convention (y down): x' = x cos + y sin ; y' = -x sin + y cos
                    rx=px*math.cos(a)+py*math.sin(a); ry=-px*math.sin(a)+py*math.cos(a)
                    xs.append(pd.x+rx); ys.append(pd.y+ry)
                out.append((min(xs),min(ys),max(xs),max(ys),0.0))
    else:
        out.append((pd.x-w/2,pd.y-h/2,pd.x+w/2,pd.y+h/2,0.0))
    return out
def dist(a,b):
    dx=max(0,a[0]-b[2],b[0]-a[2]); dy=max(0,a[1]-b[3],b[1]-a[3])
    return math.hypot(dx,dy)-a[4]-b[4]
def netname(pd):
    n=pd.net
    return n.split(' ',1)[-1] if n and n[0].isdigit() and ' ' in n else n
def analyse(ref):
    f=fps[ref]; x,y,rot=sx.fp_at(f)
    pads=[(pd,shapes(pd,rot)) for pd in sx.pads_of(f)]
    pads=[(pd,sh) for pd,sh in pads if sh and pd.num!='']
    best_any=(9e9,None); best_hv=(9e9,None); best_diff=(9e9,None)
    for (pa,sa),(pb,sb) in itertools.combinations(pads,2):
        if pa.num==pb.num: continue
        d=min(dist(u,v) for u in sa for v in sb)
        na,nb=netname(pa),netname(pb)
        if d<best_any[0]: best_any=(d,(pa.num,na,pb.num,nb))
        if na!=nb:
            if d<best_diff[0]: best_diff=(d,(pa.num,na,pb.num,nb))
            if (na in HV or nb in HV) and d<best_hv[0]: best_hv=(d,(pa.num,na,pb.num,nb))
    return best_any,best_diff,best_hv
if __name__=='__main__':
    refs=sys.argv[1:] or sorted([r for r in fps if r and (r[0] in 'UQDJ' or r.startswith('RSH'))], key=lambda r:(''.join(c for c in r if c.isalpha()), int(''.join(c for c in r if c.isdigit()) or 0)))
    rows=[]
    for r in refs:
        a,d,h=analyse(r)
        rows.append((r,sx.S(fps[r][1]).split(':')[-1],a,d,h))
    for r,fp,a,d,h in rows:
        def f(t): 
            return f"{t[0]:.3f} ({t[1][0]}:{t[1][1]} | {t[1][2]}:{t[1][3]})" if t[1] else '-'
        print(f"{r:<5} {fp[:34]:<34} any={a[0]:.3f}  diffnet={f(d)}   HV={f(h)}")
