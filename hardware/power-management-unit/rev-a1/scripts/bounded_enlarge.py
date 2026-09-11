"""Derive only the two permitted larger sizes from the clean compact placement.

Rigid component moves; unchanged force core; explicitly rebuilt wide external
power corridors. This creates the one active board for a size, not a release.
"""
from datetime import datetime, timezone
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]; BASE=ROOT.parent/'rev-a'; REPO=ROOT.parents[2]
sys.path.insert(0,str(BASE/'scripts'))
import pcbnew as pcb
from cad_operations import zone,rect,merge_zones
from configure_power_rules import POWER_NETS
from bounded_checks import LEDGER,minutes,sha,write

WIP='014632dd9d8c65689d6f62036c11b4d191d49fb4'
def point(x,y):return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
def xy(p):return (pcb.ToMM(p.x),pcb.ToMM(p.y))
def wip(path):
    return subprocess.check_output([str(REPO.parent/'tools-local/mingit-portable/cmd/git.exe'),'-c','safe.directory='+REPO.as_posix(),'show',WIP+':hardware/power-management-unit/rev-a1/'+path])

def load_wip(path):
    scratch=REPO.parent/'tools-local/bounded-shrink-native';scratch.mkdir(exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix='.kicad_pcb',dir=scratch,delete=False) as f:
        temporary=Path(f.name);f.write(wip(path))
    board=pcb.LoadBoard(str(temporary));temporary.unlink();return board

def corridor(board,net,points,width,layer,priority=3):
    # Constant-width rectangular sections; no coordinate scaling of a diagonal.
    for a,b in zip(points,points[1:]):
        dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
        nx,ny=-dy*width/2/length,dx*width/2/length
        zone(board,net,[(a[0]+nx,a[1]+ny),(b[0]+nx,b[1]+ny),(b[0]-nx,b[1]-ny),(a[0]-nx,a[1]-ny)],layer,priority)
    for x,y in points:zone(board,net,rect(x-width/2,y-width/2,x+width/2,y+width/2),layer,priority)

def create(width,height):
    assert (width,height) in [(275,210),(300,220)]
    ledger=json.loads(LEDGER.read_text(encoding='utf-8'));assert minutes(ledger)<140 and not ledger.get('stop_required')
    previous='250x200' if width==275 else '275x210'
    completed=[c for c in ledger['cycles'] if c['size']==previous]
    assert completed and completed[-1]['status']=='completed' and completed[-1]['result']=='failed' and not completed[-1]['progress_permits_next_cycle']
    name=f'HomeMy_PMU_RevA_{width}x{height}';path=ROOT/'kicad'/(name+'.kicad_pcb');assert not path.exists()
    source='study/250x200-straight/HomeMy_PMU_RevA.kicad_pcb';board=load_wip(source)
    placement=json.loads(wip('study/250x200-straight/placement.json'))['placements'];dx=width-250;dy=height-200
    right={'J3','J4','J5','J6','J12','BC13','BC14','H2','NT1','NT2','NT10'}|{'TP'+str(n) for n in range(26,31)}
    moves={}
    for f in board.GetFootprints():
        ref=f.GetReference();x,y=xy(f.GetPosition());group=placement[ref]['group']
        if y>=146:tx,ty=(dx if x>=137 else 0),dy
        else:tx,ty=(dx if group=='chopper' or ref in right else 0),0
        f.Move(point(tx,ty));moves[ref]=[tx,ty]
    if width==300:
        # Single read-only-reviewed placement proposal clears the two original
        # eFuse input fanouts. Native courtyard/probe/copper checks still apply.
        fps={f.GetReference():f for f in board.GetFootprints()}
        for ref,target in [('R40',(29,184.75)),('R56',(34.5,204))]:
            x,y=xy(fps[ref].GetPosition());fps[ref].SetPosition(point(*target))
            moves[ref]=[moves[ref][0]+target[0]-x,moves[ref][1]+target[1]-y]
    owners=[]
    core={'BATT_FUSED_P','BATT_SENSED_P','MAIN_COMMON','SYS_BUS_P','MOTION_SENSED_P','MOTION_COMMON'}
    for z in list(board.Zones()):
        if not z.GetIsRuleArea() and z.GetNetname() not in core:board.Remove(z);owners.append(z)
    for t in board.GetTracks():
        net=t.GetNetname();x,y=xy(t.GetPosition())
        shift=dx if net in ['ARM_L_N','ARM_R_N','CHOPPER_N'] or net=='BATT_N' and x>=190 else 0
        if shift:t.Move(point(shift,0))
    for d in board.GetDrawings():
        if d.GetLayer()!=pcb.Edge_Cuts:continue
        for getter,setter in [(d.GetStart,d.SetStart),(d.GetEnd,d.SetEnd)]:
            x,y=xy(getter());setter(point(width if abs(x-250)<1e-5 else x,height if abs(y-200)<1e-5 else y))
    for l in [pcb.F_Cu,pcb.B_Cu]:
        zone(board,'MOTION_BUS_P',[(176.1,8),(width-1,8),(width-1,53),(214+dx,53),(214+dx,87),(176.1,87)],l,1)
        corridor(board,'MOTION_BUS_P',[(246.5+dx,42),(246.5+dx,74)],6,l,2)
        corridor(board,'MOTION_BUS_P',[(243.3+dx,74),(243.3+dx,179+dy)],12,l,2)
        for y in [68,149+dy,176+dy]:corridor(board,'MOTION_BUS_P',[(239+dx,y),(246+dx,y)],6,l,2)
        zone(board,'BATT_N',rect(5,122,width-1,153),l,1)
        zone(board,'BATT_N',rect(5,113,17,127),l,1)
        zone(board,'BATT_N',rect(199+dx,97,213+dx,135),l,1)
        corridor(board,'ARM_L_N',[(232+dx,86),(217+dx,103)],18,l,4)
        corridor(board,'ARM_R_N',[(232+dx,112),(217+dx,127)],18,l,4)
    zone(board,'CHOP_DRAIN',rect(210+dx,54,241.5+dx,88),pcb.F_Cu,3,.5)
    corridor(board,'CHOP_DRAIN',[(224+dx,66),(239+dx,62.92)],3,pcb.F_Cu,3)
    corridor(board,'MOTION_BUS_P',[(239+dx,68),(247+dx,68)],6,pcb.F_Cu,4)
    zone(board,'CHOPPER_N',rect(204.5+dx,69.7,209.5+dx,84),pcb.F_Cu,3)
    zone(board,'CHOPPER_N',rect(201+dx,69,226+dx,95),pcb.B_Cu,3)
    corridor(board,'CHOPPER_N',[(204+dx,37),(224+dx,37),(224+dx,50),(208+dx,73)],8,pcb.B_Cu,3)
    corridor(board,'CHOPPER_N',[(207+dx,73),(208+dx,91),(193,115),(193,127)],8,pcb.B_Cu,3)
    corridor(board,'DRIVE_N',[(239+dx,143.92+dy),(235+dx,144+dy),(231+dx,153+dy),(135,153+dy),(135,139)],8,pcb.B_Cu,3)
    for l in [pcb.In1_Cu,pcb.In2_Cu]:corridor(board,'LIFT_N',[(239+dx,170.92+dy),(232+dx,170.92+dy),(232+dx,149+dy),(159,149+dy),(159,139)],8,l,3)
    for z in board.Zones():
        if z.GetNetname() in POWER_NETS:z.SetMinThickness(pcb.FromMM(1.2))
    merge_zones(board)
    board.GetTitleBlock().SetRevision('A.1 bounded WIP');board.GetTitleBlock().SetComment(2,f'{width} x {height} mm; NOT RELEASED')
    board.SetFileName(str(path));board.BuildConnectivity();filler=pcb.ZONE_FILLER(board);filler.Fill(board.Zones());pcb.SaveBoard(str(path),board)
    for ext in ['.kicad_pro','.kicad_dru','.kicad_sch']:(path.with_suffix(ext)).write_bytes((BASE/'kicad'/('HomeMy_PMU_RevA'+ext)).read_bytes())
    out=ROOT/'results'/(name+'.json')
    import hashlib
    write(out,{'board':str(path.relative_to(ROOT)),'source':{'commit':WIP,'path':source,'sha256':hashlib.sha256(wip(source)).hexdigest()},
        'derivation':{'size_mm':[width,height],'rigid_footprint_translations_mm':moves,'prepared_pcb_sha256':sha(path),
        'method':'Fixed main/motion force core; rigid right/bottom component translations; constant-width rebuilt power/return corridors; original via geometry retained.'},'checks':{}})
    print('Created clean-derived',width,height,sha(path),flush=True)
    return board,filler,owners

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('width',type=int);ap.add_argument('height',type=int);a=ap.parse_args();owners=create(a.width,a.height)
