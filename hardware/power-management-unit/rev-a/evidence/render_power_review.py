"""Render saved native copper polygons for the read-only engineering review."""
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent
data=json.loads((ROOT/'filled-power-polygons.json').read_text())
colors=['#c67a20','#c95342','#90892e','#924ead','#337ec4','#317c5b','#c64e9c','#797f84','#45a3ae','#b7885a','#8baa47','#b7658e','#518fb9','#cc663f','#625dc6','#497f66','#ad742b','#4579a5','#538742','#aa479e']
nets=list(dict.fromkeys(p['net'] for p in data)); palette=dict(zip(nets,colors))
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',17)
def render(name,bounds,scale,layers):
    x0,y0,x1,y1=bounds; w=round((x1-x0)*scale);h=round((y1-y0)*scale)
    out=Image.new('RGB',(w*len(layers),h+160),'white');d=ImageDraw.Draw(out)
    for n,layer in enumerate(layers):
        panel=Image.new('RGB',(w,h),'#f6f5ef');pd=ImageDraw.Draw(panel)
        def pts(poly):return [(round((x-x0)*scale),round((y-y0)*scale)) for x,y in poly]
        for p in data:
            if p['layer']!=layer:continue
            for q in p['outlines']:
                if max(x for x,y in q['outer'])<x0 or min(x for x,y in q['outer'])>x1 or max(y for x,y in q['outer'])<y0 or min(y for x,y in q['outer'])>y1:continue
                pd.polygon(pts(q['outer']),fill=palette[p['net']])
                for hole in q['holes']:pd.polygon(pts(hole),fill='#f6f5ef')
        out.paste(panel,(n*w,32))
        d.text((n*w+6,6),f'{layer}  x={x0}..{x1}, y={y0}..{y1} mm',font=font,fill='black')
    for i,net in enumerate(nets):
        xx=(i%5)*(out.width//5)+6;yy=h+42+(i//5)*25
        d.rectangle([xx,yy,xx+12,yy+12],fill=palette[net]);d.text((xx+18,yy-3),net,font=font,fill='black')
    out.save(ROOT/name)
render('power-upper-review.png',(0,5,360,142),5,['F.Cu','B.Cu'])
render('power-shunt2-review.png',(108,35,142,55),24,['F.Cu','B.Cu'])
render('power-chopper-review.png',(289,10,360,57),14,['F.Cu','B.Cu'])
