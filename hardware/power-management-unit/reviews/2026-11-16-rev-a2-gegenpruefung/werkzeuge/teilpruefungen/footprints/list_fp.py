import pcbnew, sys, collections
p = sys.argv[1]
b = pcbnew.LoadBoard(p)
d = collections.defaultdict(list)
for f in b.GetFootprints():
    d[str(f.GetFPID().GetUniStringLibId())].append(f.GetReference())
import re
def key(r):
    m = re.match(r'([A-Za-z_]+)(\d+)', r)
    return (m.group(1), int(m.group(2))) if m else (r, 0)
for k in sorted(d):
    refs = sorted(d[k], key=key)
    print(f"{k}  [{len(refs)}]: {' '.join(refs)}")
