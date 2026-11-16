import sys
sys.path.insert(0,'<SITZUNG>/tools')
import nl
comps,nets,pins=nl.load()
for r in sys.argv[1:]:
    c=comps[r]
    print(f"{r:<4} {c['fields'].get('MPN'):<22} "+'  '.join(f"{p}={pins[r][p][1]}[{pins[r][p][0][:22]}]" for p in sorted(pins[r],key=nl.natkey)))
