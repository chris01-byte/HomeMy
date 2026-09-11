"""Render the native-extracted placement for visual layout review."""
import json
from PIL import Image,ImageDraw,ImageFont
from rebuild import ROOT,OUT
data=json.loads((OUT/'current-footprints.json').read_text(encoding='utf-8'))
im=Image.new('RGB',(1740,1430),'#f5f7fa');d=ImageDraw.Draw(im)
font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',14)
large=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22)
scale=6;ox=30;oy=65
def pt(x,y):return (ox+x*scale,oy+y*scale)
d.text((30,18),'HomeMy PMU | new 280 x 220 mm placement | WIP - not orderable',font=large,fill='#162234')
d.rectangle([pt(0,0),pt(280,220)],fill='#e6ede8',outline='#163c31',width=3)
d.rectangle([pt(227,208.25),pt(275,220)],fill='#f1c7c7')
for ref,r in data.items():
    q=r['box'];color='#8eabc5' if ref.startswith('U') else '#dca95c' if ref.startswith(('J','NT','BC')) else '#a4bdad'
    if ref.startswith('Q'):color='#e39e89'
    if ref.startswith('TP'):color='#e8d07b'
    d.rectangle([pt(q[0],q[1]),pt(q[2],min(q[3],226))],outline='#4c6258',fill=color,width=1)
    if ref.startswith(('U','J','NT','BC','Q','H','RSH')):
        x,y=r['xy'];d.text(pt(x-2,y-1),ref,font=font,fill='#142321')
im.save(OUT/'placement-review.png')
