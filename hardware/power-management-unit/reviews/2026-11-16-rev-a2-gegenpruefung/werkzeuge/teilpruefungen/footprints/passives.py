import sys, re, collections
sys.path.insert(0,'<SITZUNG>/tools')
import nl
comps,nets,pins=nl.load()
g=collections.defaultdict(list)
for r,c in comps.items():
    if re.match(r'^(R|C|TH|L|F)\d',r):
        g[(c['fields'].get('MPN'),c['footprint'].split(':')[-1],c['value'][:28])].append(r)
for (mpn,fp,val),refs in sorted(g.items(), key=lambda kv:(kv[0][1],str(kv[0][0]))):
    m=re.search(r'(0402|0603|0805|1206|1210|2010|2512|1812)',str(mpn))
    fsz=re.search(r'_(\d{4})_',fp)
    flag=''
    if m and fsz and m.group(1)!=fsz.group(1): flag='  <<<< SIZE MISMATCH'
    if not m: flag='  (size not in MPN)'
    print(f"{fp[:30]:<30} {str(mpn):<26} {val:<28} n={len(refs):<3} {' '.join(sorted(refs,key=nl.natkey)[:6])}{flag}")
