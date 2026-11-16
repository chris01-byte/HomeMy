import os,sys,json
from power_native_reader_param import main,pcb
from build_board import point
b,polys,paths,zones,tap_ids,digest=main()
def scan(net,layer,y,x0,x1,step=0.01):
    q=polys[(net,layer)];xs=[];inside=False;start=None;out=[]
    n=int(round((x1-x0)/step))
    for i in range(n+1):
        x=x0+i*step;hit=q.Contains(point(x,y),-1,0,True)
        if hit and not inside: start=x;inside=True
        if inside and (not hit or i==n): out.append((round(start,2),round(x if not hit else x1,2)));inside=False
    return out
for net,layer,ys,x0,x1 in json.loads(os.environ['SCANS']):
    L={'F.Cu':pcb.F_Cu,'B.Cu':pcb.B_Cu,'In1.Cu':pcb.In1_Cu,'In2.Cu':pcb.In2_Cu}[layer]
    for y in ys:
        iv=scan(net,L,y,x0,x1); print(os.environ.get('LABEL'),net,layer,'y=%.1f'%y,'copper x-intervals',iv,'total %.2f mm'%sum(b_-a for a,b_ in iv))
