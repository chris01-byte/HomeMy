import sys, math, collections
sys.path.insert(0,'<SITZUNG>/agents/footprints')
import sample, pcbnew
b=sample.b; mm=pcbnew.ToMM
def scanbox(ref,hx,hy,step=0.1, layers=(pcbnew.F_Cu,)):
    f=b.FindFootprintByReference(ref)
    c=collections.Counter()
    nx=int(round(2*hx/step)); ny=int(round(2*hy/step))
    for i in range(nx+1):
        for j in range(ny+1):
            lx=-hx+i*step; ly=-hy+j*step
            for n in set(sample.net_at(*sample.loc2abs(f,lx,ly))):
                c[n.split(':')[-1] if n!='-' else '-none-']+=1
    return dict(c)
for spec in sys.argv[1:]:
    ref,hx,hy=spec.split(':')
    print(ref, 'F.Cu nets within local box ±%s x ±%s:'%(hx,hy), scanbox(ref,float(hx),float(hy)))
