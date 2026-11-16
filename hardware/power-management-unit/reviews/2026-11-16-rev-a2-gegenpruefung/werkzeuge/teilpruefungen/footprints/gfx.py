import sys, os
sys.path.insert(0,'<SITZUNG>/agents/footprints')
import sx, dump
path=sys.argv[1]
if not os.path.exists(path): path=os.path.join(dump.LIB,path)
want=sys.argv[2:] or ['F.Fab','F.CrtYd','F.SilkS']
f=sx.load_mod(path)
for g in f:
    if not isinstance(g,list): continue
    k=g[0]
    if k not in ('fp_line','fp_rect','fp_circle','fp_arc','fp_poly','fp_text'): continue
    ly=sx.find1(g,'layer'); L=sx.S(ly[1]) if ly else '?'
    if L not in want: continue
    if k in('fp_line','fp_rect'):
        s=sx.find1(g,'start'); e=sx.find1(g,'end')
        print(f"{L:8} {k:8} ({sx.num(s[1]):.3f},{sx.num(s[2]):.3f}) -> ({sx.num(e[1]):.3f},{sx.num(e[2]):.3f})")
    elif k=='fp_circle':
        c=sx.find1(g,'center'); e=sx.find1(g,'end')
        import math
        r=math.hypot(sx.num(e[1])-sx.num(c[1]),sx.num(e[2])-sx.num(c[2]))
        print(f"{L:8} {k:8} c=({sx.num(c[1]):.3f},{sx.num(c[2]):.3f}) r={r:.3f}")
    elif k=='fp_arc':
        s=sx.find1(g,'start'); m=sx.find1(g,'mid'); e=sx.find1(g,'end')
        print(f"{L:8} {k:8} ({sx.num(s[1]):.3f},{sx.num(s[2]):.3f}) mid ({sx.num(m[1]):.3f},{sx.num(m[2]):.3f}) -> ({sx.num(e[1]):.3f},{sx.num(e[2]):.3f})")
    elif k=='fp_poly':
        pts=sx.find1(g,'pts'); xy=[(sx.num(p[1]),sx.num(p[2])) for p in pts[1:] if p[0]=='xy']
        print(f"{L:8} {k:8} {[(round(a,3),round(b,3)) for a,b in xy]}")
    elif k=='fp_text':
        at=sx.find1(g,'at')
        print(f"{L:8} {k:8} '{sx.S(g[2])}' at ({sx.num(at[1])},{sx.num(at[2])})")
