import sys, math
sys.path.insert(0,'<SITZUNG>/agents/footprints')
import sample
b=sample.b
def scan(ref, fixed_axis, fixed_val, lo, hi, step=0.01):
    f=b.FindFootprintByReference(ref)
    prev=None; out=[]
    n=int(round((hi-lo)/step))
    for i in range(n+1):
        v=lo+i*step
        lx,ly=(fixed_val,v) if fixed_axis=='x' else (v,fixed_val)
        nets=','.join(sorted(set(sample.net_at(*sample.loc2abs(f,lx,ly)))))
        if nets!=prev:
            out.append(f"{v:+.2f}:{nets}")
            prev=nets
    return ' -> '.join(out)
if __name__=='__main__':
    ref=sys.argv[1]
    for spec in sys.argv[2:]:
        ax,val,lo,hi=spec.split(':')
        print(f"{ref} local {ax}={val}, scanning {'y' if ax=='x' else 'x'} from {lo} to {hi}: ",scan(ref,ax,float(val),float(lo),float(hi)))
