import sys
sys.path.insert(0,'<SITZUNG>/tools')
import nl
comps,nets,pins=nl.load()
for n in sys.argv[1:]:
    print(n,':',' '.join(f"{r}.{p}({comps[r]['value'][:14]})" for r,p,_,_ in sorted(nets[n],key=lambda t: nl.natkey(t[0]))))
