import sys; sys.path.insert(0,'<SITZUNG>/agents/mech/pylib'); sys.path.insert(0,'<SITZUNG>/agents/mech')
from common import *
import math
from shapely.geometry import Point, box
def padbox(p):
    sx,sy=p['sx'],p['sy']
    if abs((p['rot']%180)-90)<1: sx,sy=sy,sx
    return box(p['x']-sx/2,p['y']-sy/2,p['x']+sx/2,p['y']+sy/2)
print('== BC top-side: nearest other component pad / courtyard to the land centre (washer r=4.5, tool r=4.5..5)')
for i in range(1,16):
    ref='BC%d'%i; f=fps[ref]; c=Point(f['x'],f['y'])
    rows=[]
    for g in board['footprints']:
        if g['ref']==ref: continue
        dpad=min((padbox(p).distance(c),p['num'],p['net']) for p in g['pads']) if g['pads'] else (1e9,'','')
        cy=g['courtyard'] or g['bbox']
        dcy=box(*cy).distance(c)
        if min(dpad[0],dcy)<9: rows.append((round(min(dpad[0],dcy),2),g['ref'],round(dpad[0],2),dpad[1],dpad[2],round(dcy,2),g['fpid'][:28]))
    rows.sort()
    print(ref,f['pads'][0]['net'],(f['x'],f['y']),'->',rows[:4])
print()
print('== NB bridges (top): nearest other component pad/courtyard to 20x10 outline')
for nt in A2J['net_tie_modifications']:
    ref=nt['ref']; o=nt['top_bridge']['outline']
    B_=box(min(p[0] for p in o),min(p[1] for p in o),max(p[0] for p in o),max(p[1] for p in o))
    rows=[]
    for g in board['footprints']:
        if g['ref']==ref: continue
        dpad=min((padbox(p).distance(B_),p['num'],p['net']) for p in g['pads']) if g['pads'] else (1e9,'','')
        cy=g['courtyard'] or g['bbox']
        dcy=box(*cy).distance(B_)
        if min(dpad[0],dcy)<6: rows.append((round(min(dpad[0],dcy),2),g['ref'],round(dpad[0],2),dpad[1],dpad[2],round(dcy,2),g['fpid'][:28]))
    rows.sort()
    print(ref,B_.bounds,'->',rows[:5])
# vias near NB outlines on top (tented) of other nets within 1.5mm
print()
for nt in A2J['net_tie_modifications']:
    ref=nt['ref']; o=nt['top_bridge']['outline']
    B_=box(min(p[0] for p in o),min(p[1] for p in o),max(p[0] for p in o),max(p[1] for p in o))
    own={pd['net'] for pd in nt['replace_pad_1_and_2_with']}
    vs=[(round(B_.distance(Point(v['x'],v['y']))-v['w_F']/2,2),v['net'],v['x'],v['y']) for v in board['vias'] if B_.distance(Point(v['x'],v['y']))-v['w_F']/2<2.5 and v['net'] not in own]
    print(ref,'foreign vias within 2.5mm of NB outline:',sorted(vs)[:6])
