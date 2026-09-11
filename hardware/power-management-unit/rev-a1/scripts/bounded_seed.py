"""One conservative seed stage for a clean-derived larger board.

Only whole pad-anchored rigid nets and original local reference geometry are
eligible. The 52-connection WIP supplies critical nets only; never its generic
autorouter paths. Collision screening does not replace final unchanged DRC.
"""
import argparse
from collections import defaultdict, Counter
import json
import math
from pathlib import Path
import sys
from bounded_enlarge import ROOT, BASE, load_wip, wip, corridor, point, xy
from bounded_checks import LEDGER, minutes, sha, write
sys.path.insert(0, str(BASE/'scripts'))
import pcbnew as pcb
from configure_power_rules import POWER_NETS
from cad_operations import zone, rect, merge_zones
from review_critical_routing import NETS

LAYERS=[pcb.F_Cu,pcb.In1_Cu,pcb.In2_Cu,pcb.B_Cu]
LOWER={'DRIVE_N','LIFT_N','CHOPPER_N','CHOP_DRAIN','PC_BUCK_IN_P','LOGIC_BUCK_IN_P','PC_N','LOGIC_BUCK_N','LOGIC_5V_N','V5V'}
CRITICAL=(set(NETS)-set(POWER_NETS)-{'V3V3'})|{'CHOP_GATE','CHOP_GATE_DRIVE'}

class Screen:
    def __init__(self, board):
        self.board=board;self.grid=defaultdict(list);self.shapes={};self.owners=[]
        self.rules=[z for z in board.Zones() if z.GetIsRuleArea()]+[z for f in board.GetFootprints() for z in f.Zones() if z.GetIsRuleArea()]
        for t in list(board.GetTracks())+[p for f in board.GetFootprints() for p in f.Pads()]:self.index(t)
    def cells(self,box):
        return [(i,j) for i in range(math.floor(pcb.ToMM(box.GetX())/3),math.floor(pcb.ToMM(box.GetRight())/3)+1) for j in range(math.floor(pcb.ToMM(box.GetY())/3),math.floor(pcb.ToMM(box.GetBottom())/3)+1)]
    def index(self,t):
        for l in LAYERS:
            if t.IsOnLayer(l):
                self.shapes[id(t),l]=t.GetEffectiveShape(l)
                for i,j in self.cells(t.GetBoundingBox()):self.grid[i,j,l].append(t)
        self.owners.append(t)
    def reason(self,t):
        box=t.GetBoundingBox();box.Inflate(pcb.FromMM(.51))
        if not self.board.GetBoardEdgesBoundingBox().Contains(box):return 'edge'
        for l in LAYERS:
            if not t.IsOnLayer(l):continue
            shape=t.GetEffectiveShape(l)
            for z in self.rules:
                if z.GetLayerSet().Contains(l) and (z.GetDoNotAllowVias() if isinstance(t,pcb.PCB_VIA) else z.GetDoNotAllowTracks()) and z.Outline().Collide(shape,0):return 'keepout'
            seen=set()
            for i,j in self.cells(box):
                for other in self.grid[i,j,l]:
                    if id(other) in seen:continue
                    seen.add(id(other))
                    if other.GetNetname()!=t.GetNetname() and shape.Collide(self.shapes[id(other),l],pcb.FromMM(.2)-10):return 'foreign copper'
                    if isinstance(t,pcb.PCB_VIA) and (isinstance(other,pcb.PCB_VIA) or isinstance(other,pcb.PAD) and other.GetDrillSize().x):
                        d=pcb.ToMM(other.GetDrillValue() if isinstance(other,pcb.PCB_VIA) else other.GetDrillSize().x)
                        if math.dist(xy(t.GetPosition()),xy(other.GetPosition())) < (pcb.ToMM(t.GetDrillValue())+d)/2+.25-1e-6:return 'drill clearance'
        return None

def seed(board,source,eligible,screen,label):
    fps={f.GetReference():f for f in board.GetFootprints()};old={f.GetReference():f for f in source.GetFootprints()}
    bynet=defaultdict(list);pads=defaultdict(list)
    for t in source.GetTracks():
        if t.GetNetname() in eligible:bynet[t.GetNetname()].append(t)
    for f in source.GetFootprints():
        for p in f.Pads():pads[p.GetNetname()].append(p)
    adopted=[];skipped=[];held=[]
    for net,items in sorted(bynet.items()):
        refs={p.GetParentFootprint().GetReference() for p in pads[net]};transforms=set()
        for ref in refs:
            a=(fps[ref].GetOrientationDegrees()-old[ref].GetOrientationDegrees())%360;c=math.cos(math.radians(a));s=math.sin(math.radians(a))
            x,y=xy(old[ref].GetPosition());X,Y=xy(fps[ref].GetPosition())
            transforms.add((round(a,6),round(X-c*x-s*y,6),round(Y+s*x-c*y,6)))
        if len(refs)<2 or len(transforms)!=1:
            skipped.append({'net':net,'reason':'No one rigid transform for all physical pad owners'});continue
        transform=next(iter(transforms));clones=[]
        for t in items:
            n=t.Duplicate().Cast();n.SetParentGroup(None);n.SetUuid(pcb.KIID(t.m_Uuid.AsString()))
            n.Rotate(point(0,0),pcb.EDA_ANGLE(transform[0],pcb.DEGREES_T));n.Move(point(*transform[1:]));n.SetNet(board.FindNet(net));n.SetLocked(True);clones.append(n)
        reasons=Counter(screen.reason(t) for t in clones);reasons.pop(None,None)
        # Reject existing source fragments: both ends of every segment must
        # physically touch another same-net conductor or pad on its layer.
        candidates=clones+[p for f in fps.values() for p in f.Pads() if p.GetNetname()==net]
        for t in clones:
            if isinstance(t,pcb.PCB_VIA):continue
            for p in (t.GetStart(),t.GetEnd()):
                if not any(o is not t and o.IsOnLayer(t.GetLayer()) and o.GetEffectiveShape(t.GetLayer()).Collide(p,pcb.FromMM(.001)) for o in candidates):reasons['source dangling endpoint']+=1
        if reasons:
            skipped.append({'net':net,'reason':dict(reasons)});held.extend(clones);continue
        for n in clones:board.Add(n);screen.index(n)
        held.extend(clones);adopted.append({'net':net,'items':len(clones),'source':label,'transform_deg_xy_mm':transform,'uuids':[t.m_Uuid.AsString() for t in clones]})
    return {'adopted':adopted,'rejected':skipped},held

def main(path):
    ledger=json.loads(LEDGER.read_text(encoding='utf-8'));cycle=ledger['cycles'][-1]
    assert cycle['status']=='in_progress' and not cycle.get('critical_reference_seed') and minutes(ledger)<140 and not ledger.get('stop_required')
    cycle['critical_reference_seed']=1;write(LEDGER,ledger)
    before=sha(path);board=pcb.LoadBoard(str(path));screen=Screen(board);owners=[]
    srcpath='reports/routing-round-003/HomeMy_PMU_RevA.kicad_pcb';critical=load_wip(srcpath)
    details,held=seed(board,critical,CRITICAL,screen,'WIP52 selected critical nets');owners.extend(held)
    baseline=pcb.LoadBoard(str(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'))
    eligible={t.GetNetname() for t in baseline.GetTracks()}-set(POWER_NETS)-LOWER-CRITICAL-{'LOGIC_GND','CHOP_GND','V3V3'}
    local,held=seed(board,baseline,eligible,screen,'Rev A complete rigid local nets');owners.extend(held)
    box=board.GetBoardEdgesBoundingBox();W=pcb.ToMM(box.GetWidth());H=pcb.ToMM(box.GetHeight());dx=W-250;dy=H-200
    z=zone(board,'BATT_N',rect(3,3,W-3,153),pcb.In2_Cu,0,.5);z.SetMinThickness(pcb.FromMM(1.2))
    z=zone(board,'BATT_N',rect(3,148,18,190+dy),pcb.In2_Cu,0,.5);z.SetMinThickness(pcb.FromMM(1.2))
    zone(board,'LOGIC_GND',rect(3,154+dy,W-3,H-1),pcb.In1_Cu,0,.3)
    zone(board,'LOGIC_GND',rect(14,10,40,34),pcb.In1_Cu,0,.3)
    corridor(board,'LOGIC_GND',[(95.5,145),(95.5,160+dy)],3,pcb.In1_Cu,0)
    zone(board,'CHOP_GND',rect(148+dx,86,233+dx,122),pcb.In1_Cu,0,.3)
    # Reference stitches are explicit pads-to-vias; no inference from proximity.
    stitches=[];fps={f.GetReference():f for f in board.GetFootprints()}
    for ref in sorted(fps):
        for pad in fps[ref].Pads():
            net=pad.GetNetname()
            if net not in {'LOGIC_GND','CHOP_GND'} or pad.GetDrillSize().x:continue
            x,y=xy(pad.GetPosition());target=pcb.In1_Cu
            if not any(z.GetNetname()==net and z.GetLayer()==target and z.Outline().Contains(point(x,y)) for z in board.Zones()):continue
            for ox,oy in [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,1),(1,-1),(-1,-1)]:
                v=pcb.PCB_VIA(board);v.SetViaType(pcb.VIATYPE_THROUGH);v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetPosition(point(x+ox,y+oy));v.SetWidth(pcb.FromMM(.6));v.SetDrill(pcb.FromMM(.3));v.SetNet(board.FindNet(net));v.SetLocked(True)
                t=pcb.PCB_TRACK(board);t.SetStart(point(x,y));t.SetEnd(point(x+ox,y+oy));t.SetLayer(pad.GetLayer());t.SetWidth(pcb.FromMM(.2));t.SetNet(board.FindNet(net));t.SetLocked(True)
                owners.extend([v,t])
                if screen.reason(v) or screen.reason(t):continue
                board.Add(v);board.Add(t);screen.index(v);screen.index(t);stitches.append({'pad':ref+'.'+pad.GetNumber(),'net':net,'via_xy_mm':[x+ox,y+oy]});break
    merge_zones(board);board.BuildConnectivity();filler=pcb.ZONE_FILLER(board);filler.Fill(board.Zones());board.GetConnectivity().RecalculateRatsnest()
    count=board.GetConnectivity().GetUnconnectedCount(False);pcb.SaveBoard(str(path),board)
    resultpath=ROOT/'results'/(path.stem+'.json');result=json.loads(resultpath.read_text(encoding='utf-8'))
    import hashlib
    result['cycles'][str(cycle['cycle'])]['critical_reference_seed']={'input_sha256':before,'output_sha256':sha(path),'source_52_sha256':hashlib.sha256(wip(srcpath)).hexdigest(),'baseline_sha256':sha(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'),'critical':details,'local':local,'reference_stitches':stitches,'native_ratsnest_connections':count,'note':'Rigid source preservation plus native collision/dangling screen. Full final DRC, neck and reference integrity audits remain mandatory.'}
    write(resultpath,result);print('Seeded critical nets',len(details['adopted']),'local nets',len(local['adopted']),'reference stitches',len(stitches),'native opens',count,flush=True)
    return board,critical,baseline,filler,owners,screen

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('board',type=Path);args=ap.parse_args();owners=main(args.board.resolve())
