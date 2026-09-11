"""One finite, footprint-preserving placement construction from original Rev A.

No WIP geometry and no inherited global routing. Local component groups retain
relative positions where specified; remaining passives use a finite grid search.
"""
import json,math,sys
from collections import Counter
import pcbnew as pcb
from rebuild import *
sys.path.insert(0,str(BASE/'scripts'))
from cad_operations import drawing,label
from review_placement_access import outlines,bounds

HOLD=[]
def p(x,y):return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
def xy(v):return [pcb.ToMM(v.x),pcb.ToMM(v.y)]
def box(f):
    f.BuildCourtyardCaches();return bounds(outlines(f.GetCourtyard(pcb.F_Cu)))
def overlap(a,b,gap=.05):return bool(a and b and min(a[2],b[2])+gap>max(a[0],b[0]) and min(a[3],b[3])+gap>max(a[1],b[1]))

FIXED={
 'J1':(12,45,90),'J2':(12,95,90),'RSH1':(30,45,0),'RSH2':(112,45,0),
 'U1':(65,84,0),'U2':(156,78,0),'U11':(25,24,0),'U5':(112,91,0),
 'J3':(213,12,0),'J5':(256,12,0),'J4':(268,146,90),'J6':(268,176,90),
 'J7':(269,80,90),'J8':(269,109,90),'J12':(269,43,90),
 'NT1':(236,145,180),'NT2':(236,175,180),'NT3':(236,79,180),'NT4':(236,110,180),
 'NT5':(28,112,0),'NT6':(28,140,0),'NT7':(236,94,180),'NT8':(28,168,0),'NT9':(75,149,0),'NT10':(239,63,0),
 'U3':(39,122,180),'U4':(39,150,180),'C3':(85,120,0),'C10':(157,119,0),
 'Q40':(240,48,0),'C312':(232,22,180),'C313':(254,31,180),'U33':(225,49,180),
 'U30':(211,111,0),'U31':(197,108,180),'U32':(180,112,0),'U34':(187,133,0),'U35':(209,132,0),'U36':(220,149,0),
 'J9':(11,124,270),'J10':(11,151,270),'J11':(11,178,270),'J13':(11,205,270),
 'J14':(137,207,0),'J15':(166,207,0),'J16':(35,212,0),'J17':(50,212,0),'J18':(94,208,0),
 'J20':(17,184,0),'J21':(220,197,0),'J22':(201,195,0),'J23':(208,204,0),
 'U10':(251,201.5,180),'U12':(216,168,0),'U26':(246,184,0),'U61':(215,177,0),'U65':(214,188,0),
 'U13':(43,201,0),'U14':(94,198,0),'U60':(184,186,0),
 'U28':(138,160,0),'U50':(155,160,0),'U27':(173,161,0),'U54':(197,158,0),'U29':(155,180,0),'U51':(197,178,0),
 'H1':(8,8,0),'H2':(272,8,0),'H3':(218,214,0),'H4':(20,215,0),
 'BC1':(43,20,0),'BC2':(43,65,0),'BC3':(70,20,0),'BC4':(70,61,0),'BC5':(100,25,0),'BC6':(100,58,0),
 'BC7':(127,20,0),'BC8':(127,60,0),'BC9':(157,20,0),'BC10':(157,51,0),'BC11':(187,25,0),'BC12':(187,65,0),
 'BC13':(209,37,0),'BC14':(209,65,0),'BC15':(28,95,0),
}
AON=['U15','U17','U18','U19','U62','U63','U20','U59','U16','U64','U22','U24','U21','U23','U53','U58','U25','U55','U56','U57']
for i,ref in enumerate(AON):FIXED[ref]=(28+(i%7)*14,166+(i//7)*12,0)
FIXED['U15']=(125,164,0)
for i in range(1,7):FIXED['Q'+str(i)]=(55 if i<=3 else 85,22+20*((i-1)%3),90 if i<=3 else 270)
for i in range(7,11):FIXED['Q'+str(i)]=(142 if i<=8 else 172,22+30*((i-7)%2),90 if i<=8 else 270)
GROUPS={
 'U1':['U1','C1','C2','C4','C5','C6','C7']+['R'+str(i) for i in range(21,30)]+['R64'],
 'U2':['U2','C8','C9','C11','C12','C13','C28','C29','C30','C31']+['R'+str(i) for i in range(30,37)]+['R39'],
 'U11':['U11','C206','C241','C242','R223','R224','R225','R228'],
 'U3':['U3','C20','C21','C22']+['R'+str(i) for i in range(40,49)],
 'U4':['U4','C25','C26','C27']+['R'+str(i) for i in range(50,59)],
}
for i in range(1,11):GROUPS['Q'+str(i)]=['Q'+str(i),'R'+str(i),'R'+str(i+10)]

def main():
    guard();b=pcb.LoadBoard(str(BOARD));original=pcb.LoadBoard(str(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'))
    fps={f.GetReference():f for f in b.GetFootprints()};old={f.GetReference():f for f in original.GetFootprints()}
    original_groups={t.m_Uuid.AsString():g.GetName() for g in original.Groups() for t in g.GetItems()}
    for g in list(b.Groups()):
        for item in list(g.GetItems()):g.RemoveItem(item)
        b.Remove(g);HOLD.append(g)
    for item in list(b.GetTracks())+list(b.Zones())+list(b.GetDrawings()):b.Remove(item);HOLD.append(item)
    for a,c in [((0,0),(280,0)),((280,0),(280,220)),((280,220),(0,220)),((0,220),(0,0))]:drawing(b,a,c,pcb.Edge_Cuts,.05)
    occupied={};placed={};assignments={}
    def locate(ref,target,group):
        f=fps[ref];f.SetPosition(p(*target[:2]));f.SetOrientationDegrees(target[2]);occupied[ref]=box(f);placed[ref]=target;assignments[ref]=group
    for ref,target in FIXED.items():locate(ref,target,ref)
    def target_for(ref,anchor):
        delta=math.radians(FIXED[anchor][2]-old[anchor].GetOrientationDegrees());c,s=math.cos(delta),math.sin(delta)
        x,y=xy(old[ref].GetPosition());ox,oy=xy(old[anchor].GetPosition());X,Y,A=FIXED[anchor]
        return (X+c*(x-ox)+s*(y-oy),Y-s*(x-ox)+c*(y-oy),(old[ref].GetOrientationDegrees()+math.degrees(delta))%360)
    for anchor,refs in GROUPS.items():
        for ref in refs:
            if ref in fps and ref not in placed:locate(ref,target_for(ref,anchor),anchor)
    # Ports face external space. Explicit corridors use the rotated physical
    # screw/cable axes, not the old compact audit's hard-coded board sides.
    ports={}
    for ref in ['J1','J2','J3','J4','J5','J6','J7','J8','J9','J10','J11','J12','J13','J14','J15','J18']:
        q=occupied[ref];x,y,_=FIXED[ref]
        if ref in ['J1','J2']:ports[ref]=[-20,y-6,q[0],y+6]
        elif ref in ['J3','J5']:ports[ref]=[x-6,-20,x+6,q[1]]
        elif ref in ['J4','J6','J7','J8','J12']:ports[ref]=[q[2],q[1],300,q[3]]
        elif ref in ['J9','J10','J11','J13']:ports[ref]=[-20,q[1],q[0],q[3]]
        else:ports[ref]=[q[0],q[3],q[2],240]
    rf=[227,208.25,275,235]
    reserved=[([36,10,110,74],'MAIN'),([119,10,201,71],'MOTION'),([221,119,235,185],'STAR')]
    parts={r['ref']:r for r in json.loads((BASE/'design/assembled-parts.json').read_text(encoding='utf-8'))['components'] if r.get('on_board',True)}
    ics=[r for r in FIXED if r.startswith('U')]
    def fail(ref,bb):
        if not bb or bb[0]<1 or bb[1]<1 or bb[2]>279 or bb[3]>219:return True
        if overlap(bb,rf,0) or any(overlap(bb,v,0) for v in ports.values()):return True
        if any(overlap(bb,q) for r,q in occupied.items() if r!=ref):return True
        if any(overlap(bb,q,0) for q,name in reserved):return True
        return False
    def order(ref):
        q=box(fps[ref]);return -(q[2]-q[0])*(q[3]-q[1])
    unresolved=[];auto=[]
    for ref in sorted(set(fps)-set(placed),key=order):
        if ref.startswith('TP'):continue
        source=parts.get(ref,{});sheet=source.get('sheet','');oldxy=xy(old[ref].GetPosition())
        candidates=[r for r in ics if parts.get(r,{}).get('sheet')==sheet] or ics
        anchor=min(candidates,key=lambda r:math.dist(oldxy,xy(old[r].GetPosition())))
        target=target_for(ref,anchor);tx,ty=target[:2]
        # Fixed finite candidate list; local first, then constrained functional region.
        if sheet.startswith('04'):region=(174,87,230,153)
        elif sheet.startswith('02'):region=(17,72,111,108)
        elif sheet.startswith('03'):region=(107,73,173,110)
        elif sheet.startswith('07'):region=(17,10,39,36) if oldxy[1]<100 else (173,180,211,197)
        elif sheet.startswith('05'):region=(19,112,66,161)
        else:region=(18,154,224,211)
        points=[(tx,ty)]+[(tx+dx,ty+dy) for radius in [2,4,6,8,10,12] for dx in range(-radius,radius+1,2) for dy in [-radius,radius]]
        points += [(x,y) for y in range(region[1],region[3],2) for x in range(region[0],region[2],2)]
        points=sorted(set(points),key=lambda q:math.dist(q,(tx,ty)))
        found=False
        for x,y in points:
            if not(region[0]<=x<=region[2] and region[1]<=y<=region[3]):continue
            fps[ref].SetPosition(p(x,y));fps[ref].SetOrientationDegrees(target[2]);bb=box(fps[ref])
            if not fail(ref,bb):locate(ref,(x,y,target[2]),anchor);auto.append(ref);found=True;break
        if not found:unresolved.append(ref)
    # Testpoints require a genuine 3-mm probe disk; grid is finite, each location
    # scores distance to pads of the same net and avoids mechanical obstructions.
    for ref in sorted(r for r in fps if r.startswith('TP')):
        net=next(iter(fps[ref].Pads())).GetNetname();matches=[xy(pad.GetPosition()) for f in fps.values() if not f.GetReference().startswith('TP') for pad in f.Pads() if pad.GetNetname()==net and f.GetReference() in placed]
        center=[sum(v[i] for v in matches)/len(matches) for i in range(2)] if matches else [140,150]
        points=sorted([(x,y) for y in range(5,216,3) for x in range(5,277,3)],key=lambda q:min((math.dist(q,p0) for p0 in matches),default=math.dist(q,center)))
        for x,y in points:
            bb=[x-1.55,y-1.55,x+1.55,y+1.55]
            if not fail(ref,bb):locate(ref,(x,y,0),'testpoint');break
        else:unresolved.append(ref)
    overlaps=[[a,c] for i,a in enumerate(occupied) for c in list(occupied)[i+1:] if overlap(occupied[a],occupied[c],0)]
    blocked={r:[a for a,q in occupied.items() if a!=r and overlap(q,c,0)] for r,c in ports.items()}
    # Retain locations for unresolved refs solely to make an explicitly failed
    # placement inspectable; no routing follows until this gate passes.
    report={'source':sha(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'),'new_global_copper_items':0,'inherited_global_copper_items':0,
      'placed':len(placed),'unplaced':unresolved,'courtyard_overlaps':overlaps,'blocked_ports':{r:v for r,v in blocked.items() if v},
      'assignments':assignments,'positions':{r:list(v) for r,v in placed.items()},'ports':ports,'reserved':reserved,
      'antenna':rf,'passed':not unresolved and not overlaps and not any(blocked.values())}
    previous=OUT/'placement-construction.json'
    if previous.exists() and not (OUT/'placement-initial-screen.json').exists():
        shutil.copyfile(previous,OUT/'placement-initial-screen.json')
    write(previous,report)
    b.GetTitleBlock().SetTitle('HomeMy PMU Rev A.1 — 280x220 REBUILD — WIP')
    b.GetTitleBlock().SetRevision('A.1 REBUILD WIP');pcb.SaveBoard(str(BOARD),b);guard()
    action('Fresh placement construction',{'pcb_sha256':sha(BOARD),'placement_passed':report['passed'],'unplaced':unresolved,'overlaps':overlaps})
    print('Placement',report['placed'],'unplaced',unresolved,'overlaps',overlaps,'ports',report['blocked_ports'],flush=True)
    return b,original
if __name__=='__main__':owners=main()
