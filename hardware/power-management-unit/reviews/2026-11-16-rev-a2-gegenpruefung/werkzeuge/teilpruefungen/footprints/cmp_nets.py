import sys
sys.path.insert(0,'<SITZUNG>/tools')
sys.path.insert(0,'<SITZUNG>/agents/footprints')
import nl, sx, dump, collections
comps,nets,pins=nl.load()
root,fps=dump.board()
def show(ref, compact=True):
    f=fps[ref]
    x,y,rot=sx.fp_at(f)
    c=comps.get(ref)
    print(f"== {ref} {c['value'] if c else ''} mpn={c['fields'].get('MPN') if c else ''} fp={sx.S(f[1])} at ({x},{y}) rot {rot} {sx.fp_layer(f)}")
    by=collections.OrderedDict()
    for pd in sx.pads_of(f):
        nlnet=pins.get(ref,{}).get(pd.num,(None,None,None))
        bn=pd.net.split(' ',1)[-1] if pd.net and pd.net[0].isdigit() and ' ' in pd.net else pd.net
        flag='' if (nlnet[0]==bn or (nlnet[0] is None and bn=='')) else '  <<< MISMATCH board vs netlist'
        by.setdefault(pd.num,[]).append((bn,nlnet,flag,pd))
    for n,l in by.items():
        bn,nlnet,flag,pd=l[0]
        print(f"   pad {n:>3} x{len(l)} board_net={bn:<26} nl_net={str(nlnet[0]):<26} fn={str(nlnet[1]):<12} type={nlnet[2]}{flag}")
if __name__=='__main__':
    for r in sys.argv[1:]: show(r)
