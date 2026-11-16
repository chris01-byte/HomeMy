import sys; sys.path.insert(0,'<SITZUNG>/agents/mech')
from common import *
from PIL import Image, ImageDraw
r=R()
def crop(layers,box,fn,scale=10,bars=True,grid=10,labels=True,vias=False):
    x0,y0,x1,y1=box
    ims=[]
    for layer in layers:
        a=r[layer][int(y0*RES):int(y1*RES),int(x0*RES):int(x1*RES)]
        step=RES//scale
        if step>=1:
            a=a[::step,::step]
            img=Image.fromarray(colorize(a))
        else:
            img=Image.fromarray(colorize(a)).resize((int((x1-x0)*scale),int((y1-y0)*scale)),Image.NEAREST)
        d=ImageDraw.Draw(img)
        def T(x,y): return ((x-x0)*scale,(y-y0)*scale)
        if grid:
            gx=int(x0//grid+1)*grid
            while gx<x1:
                d.line([T(gx,y0),T(gx,y1)],fill=(210,210,210),width=1); d.text(T(gx+0.2,y0+0.2),str(gx),fill=(90,90,90)); gx+=grid
            gy=int(y0//grid+1)*grid
            while gy<y1:
                d.line([T(x0,gy),T(x1,gy)],fill=(210,210,210),width=1); d.text(T(x0+0.2,gy+0.2),str(gy),fill=(90,90,90)); gy+=grid
        if bars:
            for bbr in A2J['busbars']:
                d.polygon([T(x,y) for x,y in bbr['outline']],outline=(0,0,0),width=2)
                for c in bbr['cutouts']:
                    d.polygon([T(x,y) for x,y in c['outline']],outline=(255,0,0),width=1)
            for nt in A2J['net_tie_modifications']:
                d.polygon([T(x,y) for x,y in nt['top_bridge']['outline']],outline=(0,0,255),width=1)
        if vias:
            for v in board['vias']:
                if x0<=v['x']<=x1 and y0<=v['y']<=y1:
                    c=PAL.get(v['net'],(255,255,255))
                    rr=v['w_B']/2*scale
                    X,Y=T(v['x'],v['y']); d.ellipse([X-rr,Y-rr,X+rr,Y+rr],outline=(0,0,0))
        if labels:
            for ref,f in fps.items():
                if x0<=f['x']<=x1 and y0<=f['y']<=y1 and (ref[0] in 'JHQ' or ref[:2] in('BC','NT','RS','TP') or ref in('C3','C10','C312','C313','C246','D63','U10')):
                    d.text(T(f['x'],f['y']),ref,fill=(0,0,0))
        d.text((3,3),layer,fill=(255,0,0))
        ims.append(img)
    W=sum(i.width for i in ims)+5*(len(ims)-1); H=max(i.height for i in ims)
    out=Image.new('RGB',(W,H),(255,255,255)); x=0
    for i in ims:
        out.paste(i,(x,0)); x+=i.width+5
    out.save(OUT+fn)
if __name__=='__main__':
    import ast
    args=sys.argv[1:]
    layers=args[0].split(','); box=[float(v) for v in args[1].split(',')]; fn=args[2]; scale=int(args[3]) if len(args)>3 else 10
    crop(layers,box,fn,scale,vias=(len(args)>4 and args[4]=='vias'))
