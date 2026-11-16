import sys, itertools
sys.path.insert(0,'<SITZUNG>/agents/footprints')
import gaps, sx
HV=gaps.HV
def cls(n):
    if n.startswith('unconnected-'): return 'NC'
    return 'HV' if n in HV else 'LV'
for ref in sys.argv[1:]:
    f=gaps.fps[ref]; x,y,rot=sx.fp_at(f)
    pads=[(pd,gaps.shapes(pd,rot)) for pd in sx.pads_of(f)]
    pads=[(pd,sh) for pd,sh in pads if sh and pd.num!='']
    rows=[]
    for (pa,sa),(pb,sb) in itertools.combinations(pads,2):
        if pa.num==pb.num: continue
        d=min(gaps.dist(u,v) for u in sa for v in sb)
        na,nb=gaps.netname(pa),gaps.netname(pb)
        if na==nb: continue
        ca,cb=cls(na),cls(nb)
        if 'HV' in (ca,cb) and d<0.61:
            rows.append((round(d,3),pa.num,na,ca,pb.num,nb,cb))
    rows.sort()
    print(f"== {ref} ({sx.S(f[1]).split(':')[-1][:40]}) pairs with an HV net and gap < 0.61 mm:")
    for r in rows[:14]:
        print(f"   {r[0]:.3f} mm  pad {r[1]}[{r[2]}|{r[3]}]  <->  pad {r[4]}[{r[5]}|{r[6]}]")
