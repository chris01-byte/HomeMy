import sys, collections, re
sys.path.insert(0,'<SITZUNG>/tools')
import nl
comps,nets,pins=nl.load()
g=collections.defaultdict(list)
for r,c in comps.items():
    if len(pins[r])>=3 or r[0] in 'DQ':
        g[(c['fields'].get('MPN'),c['footprint'].split(':')[-1])].append(r)
for (mpn,fp),refs in sorted(g.items(), key=lambda kv: str(kv[0])):
    sigs=collections.defaultdict(list)
    for r in refs:
        sig=tuple((p,re.sub(r'_%s$'%re.escape(p),'',str(pins[r][p][1]))) for p in sorted(pins[r],key=nl.natkey))
        sigs[sig].append(r)
    flag='' if len(sigs)==1 else '   <<<<< INCONSISTENT PIN FUNCTIONS'
    for sig,rr in sigs.items():
        print(f"{str(mpn):<24} {fp[:28]:<28} {','.join(sorted(rr,key=nl.natkey))[:60]:<60} "+' '.join(f"{p}:{f}" for p,f in sig)[:260]+flag)
