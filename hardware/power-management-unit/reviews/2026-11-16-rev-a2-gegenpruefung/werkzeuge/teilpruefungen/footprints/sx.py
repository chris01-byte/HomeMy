"""Minimal S-expression parser + KiCad footprint pad extraction (library .kicad_mod and board-embedded)."""
import re, sys, os, math
TOK = re.compile(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+')
def parse(text):
    stack=[[]]
    for m in TOK.finditer(text):
        t=m.group(0)
        if t=='(':
            l=[]; stack[-1].append(l); stack.append(l)
        elif t==')':
            stack.pop()
        elif t[0]=='"':
            stack[-1].append(('s', t[1:-1].replace('\\"','"').replace('\\\\','\\')))
        else:
            stack[-1].append(t)
    return stack[0][0]
def S(x):
    return x[1] if isinstance(x,tuple) else x
def find(node, name):
    return [c for c in node if isinstance(c,list) and c and c[0]==name]
def find1(node,name):
    r=find(node,name)
    return r[0] if r else None
def num(x):
    return float(S(x))
class Pad:
    pass
def pads_of(fp):
    out=[]
    for p in find(fp,'pad'):
        pd=Pad()
        pd.num=S(p[1]); pd.type=S(p[2]); pd.shape=S(p[3])
        at=find1(p,'at'); pd.x=num(at[1]); pd.y=num(at[2]); pd.rot=num(at[3]) if len(at)>3 else 0.0
        sz=find1(p,'size'); pd.w=num(sz[1]); pd.h=num(sz[2])
        dr=find1(p,'drill')
        pd.drill=None
        if dr is not None:
            vals=[S(v) for v in dr[1:] if not isinstance(v,list)]
            off=find1(dr,'offset')
            pd.drill=vals
            pd.drill_off=(num(off[1]),num(off[2])) if off else None
        ly=find1(p,'layers'); pd.layers=[S(v) for v in ly[1:]] if ly else []
        net=find1(p,'net'); pd.net=' '.join(S(v) for v in net[1:]) if net else ''
        rr=find1(p,'roundrect_rratio'); pd.rr=num(rr[1]) if rr else None
        pf=find1(p,'pinfunction'); pd.pinfunction=S(pf[1]) if pf else ''
        pt=find1(p,'pintype'); pd.pintype=S(pt[1]) if pt else ''
        sm=find1(p,'solder_mask_margin'); pd.mask=num(sm[1]) if sm else None
        sp=find1(p,'solder_paste_margin'); pd.paste=num(sp[1]) if sp else None
        spr=find1(p,'solder_paste_margin_ratio'); pd.paste_ratio=num(spr[1]) if spr else None
        cl=find1(p,'clearance'); pd.clearance=num(cl[1]) if cl else None
        zc=find1(p,'zone_connect'); pd.zone_connect=S(zc[1]) if zc else None
        prop=find1(p,'property'); pd.prop=S(prop[1]) if prop else None
        pd.custom = find1(p,'primitives') is not None
        pd.raw=p
        out.append(pd)
    return out
def load_mod(path):
    return parse(open(path).read())
def board_footprints(path):
    root=parse(open(path).read())
    fps={}
    for f in find(root,'footprint'):
        ref=None
        for pr in find(f,'property'):
            if S(pr[1])=='Reference': ref=S(pr[2])
        fps[ref]=f
    return root,fps
def fp_at(f):
    at=find1(f,'at'); return num(at[1]),num(at[2]),(num(at[3]) if len(at)>3 else 0.0)
def fp_layer(f):
    return S(find1(f,'layer')[1])
def bbox_local(pd, fprot=0.0):
    """axis-aligned bbox of pad in footprint-local frame. In a board file pad rot includes the footprint rot."""
    r=(pd.rot - fprot) % 360
    w,h=pd.w,pd.h
    if abs(r-90)<1e-6 or abs(r-270)<1e-6: w,h=h,w
    elif not (abs(r)<1e-6 or abs(r-180)<1e-6):
        a=math.radians(r); w,h=abs(w*math.cos(a))+abs(h*math.sin(a)),abs(w*math.sin(a))+abs(h*math.cos(a))
    return (pd.x-w/2,pd.y-h/2,pd.x+w/2,pd.y+h/2)
def fmt_pad(pd,fprot=0.0):
    b=bbox_local(pd,fprot)
    s=f"pad {pd.num:>4} {pd.type:<12} {pd.shape:<9} at ({pd.x:8.4f},{pd.y:8.4f}) rot {pd.rot:6.1f} size {pd.w:.4f}x{pd.h:.4f} bbox x[{b[0]:.3f},{b[2]:.3f}] y[{b[1]:.3f},{b[3]:.3f}]"
    if pd.drill: s+=f" drill {pd.drill}"
    if pd.rr is not None: s+=f" rr {pd.rr}"
    s+=f" layers {','.join(pd.layers)}"
    if pd.net: s+=f" net [{pd.net}]"
    if pd.pinfunction: s+=f" fn [{pd.pinfunction}]"
    if pd.mask is not None: s+=f" mask {pd.mask}"
    if pd.paste is not None: s+=f" paste {pd.paste}"
    if pd.paste_ratio is not None: s+=f" paste_ratio {pd.paste_ratio}"
    if pd.clearance is not None: s+=f" clr {pd.clearance}"
    if pd.zone_connect is not None: s+=f" zc {pd.zone_connect}"
    if pd.custom: s+=" CUSTOM"
    if pd.prop: s+=f" prop {pd.prop}"
    return s
