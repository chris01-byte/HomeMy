import pcbnew, sys, math
sys.path.insert(0,'<SITZUNG>/agents/footprints')
import near
b=near.b; mm=pcbnew.ToMM
def fabbox(ref, layer=pcbnew.F_Fab):
    f=b.FindFootprintByReference(ref)
    xs=[];ys=[]
    for g in f.GraphicalItems():
        if g.GetLayer()==layer and g.GetClass()=='PCB_SHAPE':
            bb=g.GetBoundingBox()
            xs+= [mm(bb.GetLeft()),mm(bb.GetRight())]; ys+=[mm(bb.GetTop()),mm(bb.GetBottom())]
    return (min(xs),min(ys),max(xs),max(ys))
for ref in sys.argv[1:]:
    f=b.FindFootprintByReference(ref)
    print('####',ref,'at',mm(f.GetPosition().x),mm(f.GetPosition().y),'rot',f.GetOrientationDegrees())
    for p in f.Pads():
        if p.GetNumber() in('1','7','13','2','25','9'):
            print('   pad',p.GetNumber(),'abs',round(mm(p.GetPosition().x),3),round(mm(p.GetPosition().y),3),p.GetNetname())
    box=fabbox(ref)
    near.report(ref+' F.Fab bbox',box,0.0)
