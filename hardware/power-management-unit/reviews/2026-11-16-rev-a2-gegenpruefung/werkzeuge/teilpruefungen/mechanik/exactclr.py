import pcbnew, math, sys
B='<SITZUNG>/agents/mech/proj/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(B)
mm=pcbnew.ToMM; FromMM=pcbnew.FromMM
L={'F.Cu':pcbnew.F_Cu,'In1.Cu':pcbnew.In1_Cu,'In2.Cu':pcbnew.In2_Cu,'B.Cu':pcbnew.B_Cu}
def seg_dist(px,py,ax,ay,bx,by):
    dx,dy=bx-ax,by-ay; L2=dx*dx+dy*dy
    t=0 if L2==0 else max(0,min(1,((px-ax)*dx+(py-ay)*dy)/L2))
    return math.hypot(px-(ax+t*dx),py-(ay+t*dy))
def zone_dist(px,py,lid,skipnet=None,maxd=6.0):
    """min distance (mm) from point to filled zone copper outline of nets != skipnet on layer"""
    best={}
    P=pcbnew.VECTOR2I(FromMM(px),FromMM(py))
    for z in b.Zones():
        if z.GetIsRuleArea() or not z.IsOnLayer(lid): continue
        n=z.GetNetname()
        if n==skipnet: continue
        bb=z.GetBoundingBox()
        if px<mm(bb.GetLeft())-maxd or px>mm(bb.GetRight())+maxd or py<mm(bb.GetTop())-maxd or py>mm(bb.GetBottom())+maxd: continue
        ps=z.GetFilledPolysList(lid)
        for i in range(ps.OutlineCount()):
            o=ps.Outline(i)
            n_=o.PointCount()
            pts=[(mm(o.CPoint(k).x),mm(o.CPoint(k).y)) for k in range(n_)]
            d=min([seg_dist(px,py,pts[k][0],pts[k][1],pts[(k+1)%n_][0],pts[(k+1)%n_][1]) for k in range(n_)] or [1e9])
            inside=ps.Contains(P)
            if inside: d=-d
            if n not in best or d<best[n]: best[n]=d
    return best
if __name__=='__main__':
    for ref in ['J1','J3','J4','J2']:
        fp=[f for f in b.GetFootprints() if f.GetReference()==ref][0]
        for pad in list(fp.Pads())[:2]:
            p=pad.GetPosition(); px,py=mm(p.x),mm(p.y)
            for ln in ['In1.Cu','In2.Cu']:
                d=zone_dist(px,py,L[ln],skipnet=pad.GetNetname())
                print(ref,pad.GetNumber(),pad.GetNetname(),(px,py),ln,{k:round(v,3) for k,v in d.items() if v<5}, ' pad r=1.05 -> copper clearance; drill r=0.8 -> wall distance')
    # netclass / design rules
    ds=b.GetDesignSettings()
    print('min clearance',mm(ds.m_MinClearance),'hole clearance',mm(ds.m_HoleClearance),'hole2hole',mm(ds.m_HoleToHoleMin),'edge clr',mm(ds.m_CopperEdgeClearance),'min annular',mm(ds.m_ViasMinAnnularWidth))
