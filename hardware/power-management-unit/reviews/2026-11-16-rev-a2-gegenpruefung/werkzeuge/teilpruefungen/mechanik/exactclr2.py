import sys
sys.path.insert(0,'<SITZUNG>/agents/mech')
import exactclr as E
import pcbnew
b=E.b; mm=E.mm; L=E.L
def rep(ref,padnums=None,layers=('F.Cu','In1.Cu','In2.Cu','B.Cu')):
    fp=[f for f in b.GetFootprints() if f.GetReference()==ref][0]
    for pad in fp.Pads():
        if padnums and pad.GetNumber() not in padnums: continue
        p=pad.GetPosition(); px,py=mm(p.x),mm(p.y)
        for ln in layers:
            d=E.zone_dist(px,py,L[ln],skipnet=pad.GetNetname() or '___')
            d={k:round(v,3) for k,v in d.items() if v<8}
            print('  ',ref,pad.GetNumber(),repr(pad.GetNetname()),(px,py),ln,'zone copper distance from centre:',d)
print('J1'); rep('J1',['1','8'],('In1.Cu','In2.Cu'))
print('H1..H4'); 
for h in ['H1','H2','H3','H4']: rep(h)
print('BC2, BC4'); rep('BC2',None,('In1.Cu','In2.Cu')); rep('BC4',None,('In1.Cu','In2.Cu'))
print('NT7 pad1 F.Cu'); rep('NT7',['1'],('F.Cu',))
