import sys, os, collections
sys.path.insert(0,'<SITZUNG>/agents/footprints')
import sx, dump
root,fps=dump.board()
LIB=dump.LIB
libcache={}
def lib(fpid):
    if fpid in libcache: return libcache[fpid]
    if ':' not in fpid:
        libcache[fpid]=None; return None
    l,n=fpid.split(':',1)
    p=os.path.join(LIB,l+'.pretty',n+'.kicad_mod')
    libcache[fpid]=sx.load_mod(p) if os.path.exists(p) else None
    return libcache[fpid]
def sig(pd,fprot):
    r=(pd.rot-fprot)%360
    # normalise 180-degree symmetric for rect/oval/roundrect/circle
    if pd.shape in('rect','oval','roundrect','circle') : r=r%180
    return (pd.num,pd.type,pd.shape,round(pd.x,4),round(pd.y,4),round(r,2),round(pd.w,4),round(pd.h,4),tuple(pd.drill or ()),tuple(sorted(pd.layers)),pd.rr,pd.mask,pd.paste,pd.paste_ratio,pd.clearance,pd.custom)
layers=collections.Counter()
bad=0
summary=collections.defaultdict(list)
for ref,f in sorted(fps.items(), key=lambda kv: str(kv[0])):
    fpid=sx.S(f[1]); x,y,rot=sx.fp_at(f); layers[sx.fp_layer(f)]+=1
    L=lib(fpid)
    if L is None:
        summary['NO LIB FILE: '+fpid].append(ref); continue
    a=sorted(sig(p,rot) for p in sx.pads_of(f)); b=sorted(sig(p,0) for p in sx.pads_of(L))
    if a!=b:
        bad+=1
        summary['DIFF '+fpid].append(ref)
        if len(summary['DIFF '+fpid])==1:
            print('--- DIFF',ref,fpid)
            sa=set(a); sb=set(b)
            for t in sorted(sa-sb): print('   board only:',t)
            for t in sorted(sb-sa): print('   lib only  :',t)
    else:
        summary['same '+fpid].append(ref)
print(layers)
for k in sorted(summary): print(k, len(summary[k]), ' '.join(str(r) for r in summary[k][:12]), '...' if len(summary[k])>12 else '')
