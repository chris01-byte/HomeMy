import pcbnew as pcb
mm=pcb.FromMM
def rect(x0,y0,x1,y1):
    q=pcb.SHAPE_POLY_SET();q.NewOutline()
    for x,y in [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]:q.Append(mm(x),mm(y))
    return q
print('has UnitSet',hasattr(pcb.SHAPE_POLY_SET,'UnitSet'))
for neck in [0.4,0.9,1.1,1.9,2.1,3.1]:
    q=rect(0,0,10,10);q.BooleanAdd(rect(20,0,30,10));q.BooleanAdd(rect(10,5-neck/2,20,5+neck/2));q.Simplify()
    res=[]
    for w in [0.5,1.0,2.0,3.0]:
        c=pcb.SHAPE_POLY_SET(q);c.Deflate(mm(w/2),pcb.CORNER_STRATEGY_ROUND_ALL_CORNERS,mm(.005));mid=c.OutlineCount();c.Inflate(mm(w/2),pcb.CORNER_STRATEGY_ROUND_ALL_CORNERS,mm(.005));c.Simplify()
        res.append((w,c.OutlineCount(),round(c.Area()/1e12,2)))
    print('neck',neck,'orig outlines',q.OutlineCount(),'area',round(q.Area()/1e12,2),'-> (w, outlines, area)',res)
