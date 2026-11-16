import sys
sys.path.insert(0,'<SITZUNG>/tools')
import nl, collections
comps,nets,pins=nl.load()
# group non-passive comps by footprint
byfp=collections.defaultdict(list)
for r,c in comps.items():
    byfp[c['footprint']].append(r)
for fp in sorted(byfp):
    refs=sorted(byfp[fp],key=nl.natkey)
    if fp.split(':')[-1].startswith(('R_0','C_0','C_12','R_12','TestPoint')): 
        continue
    print('###',fp)
    for r in refs:
        c=comps[r]
        print(f"   {r:<6} val={c['value'][:40]:<40} mpn={c['fields'].get('MPN')} mfr={c['fields'].get('Manufacturer')} dnp={c['dnp']}")
