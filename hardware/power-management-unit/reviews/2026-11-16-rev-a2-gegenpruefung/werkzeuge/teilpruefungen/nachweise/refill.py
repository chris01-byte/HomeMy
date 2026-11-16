import pcbnew as pcb, sys, hashlib
p=sys.argv[1]
b=pcb.LoadBoard(p)
def areas(b):
    out={}
    for z in b.Zones():
        if z.GetIsRuleArea(): continue
        for l in z.GetLayerSet().Seq():
            s=z.GetFilledPolysList(l)
            out[(z.m_Uuid.AsString(),b.GetLayerName(l))]=(s.Area()/1e12,s.OutlineCount(),z.GetNetname())
    return out
before=areas(b)
f=pcb.ZONE_FILLER(b); ok=f.Fill(b.Zones())
after=areas(b)
print('zones/layers',len(before),'fill returned',ok)
ch=[(k,before[k],after[k]) for k in before if abs(before[k][0]-after[k][0])>1e-6 or before[k][1]!=after[k][1]]
print('zone fills whose area/outline count changed after refill (KiCad %s):'%pcb.Version(),len(ch))
for k,a,c in sorted(ch,key=lambda x:-abs(x[1][0]-x[2][0]))[:12]: print('   ',a[2],k[1],'area %.4f -> %.4f mm2 (d=%.5f)'%(a[0],c[0],c[0]-a[0]),'outlines',a[1],'->',c[1])
print('max abs area delta mm2',max([abs(a[0]-c[0]) for k,a,c in ch],default=0), 'total area before %.3f after %.3f'%(sum(v[0] for v in before.values()),sum(v[0] for v in after.values())))
b.BuildConnectivity(); print('unconnected after refill',b.GetConnectivity().GetUnconnectedCount(False))
pcb.SaveBoard(p,b)
print('saved refilled copy sha',hashlib.sha256(open(p,'rb').read()).hexdigest()[:16])
