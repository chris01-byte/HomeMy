import sys; sys.path.insert(0,'<SITZUNG>/agents/mech')
from common import *
from PIL import Image, ImageDraw, ImageFont
r=R()
def render(layer,fn,scale=5,bars=True,refs=True,crop=None):
    arr=r[layer]
    step=RES//scale
    a=arr[::step,::step]
    img=Image.fromarray(colorize(a))
    d=ImageDraw.Draw(img)
    if bars:
        for bbr in A2J['busbars']:
            pts=[(x*scale,y*scale) for x,y in bbr['outline']]
            d.polygon(pts,outline=(0,0,0),width=2)
            for c in bbr['cutouts']:
                d.polygon([(x*scale,y*scale) for x,y in c['outline']],outline=(255,0,0),width=1)
            d.text((pts[0][0]+3,pts[0][1]+3),bbr['ref'],fill=(0,0,0))
        for nt in A2J['net_tie_modifications']:
            d.polygon([(x*scale,y*scale) for x,y in nt['top_bridge']['outline']],outline=(0,0,255),width=1)
    if refs:
        for ref,f in fps.items():
            if ref[0] in 'JHQ' or ref.startswith('BC') or ref.startswith('NT') or ref.startswith('RSH') or ref in('C3','C10','C312','C313','C246','D63','U10'):
                d.text((f['x']*scale+2,f['y']*scale+2),ref,fill=(0,0,0))
    if crop:
        img=img.crop([c*scale for c in crop])
    img.save(OUT+fn)
render('B','ov_B.png'); render('F','ov_F.png'); render('I1','ov_I1.png',bars=False); render('I2','ov_I2.png',bars=False)
print('ok')
