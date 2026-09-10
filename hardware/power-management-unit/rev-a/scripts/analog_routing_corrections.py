"""Deterministic local analog layout overlay; never saves a board in the API.

Main and motion Kelvin trunks occupy the gaps between the force-copper fields.
Local CS/ISCP capacitors use short top-layer connections at their IC pins. The
caller owns foreign-net rerouting, zone fill and native DRC after this overlay.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import traceback
import pcbnew as pcb
from review_critical_routing import exit_native

ROOT=Path(__file__).resolve().parents[1]
# KiCad 10 Windows SWIG wrappers for removed tracks must stay alive until the
# short-lived native worker exits (same lifetime rule as repair_postroute.py).
_DETACHED=[]
MOVES={
 'C4':(66,93.9,0),'C5':(69.2,94.9,90),'R21':(62.7,92.5,270),'R23':(72,97,270),
 'C11':(169,93.5,270),'C12':(170,90.2,0),'R30':(174,94,90),'R32':(174,88,90),
 'C241':(30,73.2,270),'R223':(33,71.5,270),'R224':(37,72.9,270),
 'TP3':(44,91,0),'TP4':(44,85.8,0),'TP7':(150,91,0),'TP8':(146.5,85.5,0),
}
OWNED={'MAIN_KELVIN_P','MAIN_KELVIN_N','MAIN_CS_P','MAIN_ISCP',
       'MOTION_KELVIN_P','MOTION_KELVIN_N','MOTION_CS_P','MOTION_ISCP','INA_IN_P','INA_IN_N'}


def p(x,y):return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
def xy(v):return (pcb.ToMM(v.x),pcb.ToMM(v.y))
def bbox(fp):
    b=fp.GetBoundingBox(False,False)
    return (pcb.ToMM(b.GetX()),pcb.ToMM(b.GetY()),pcb.ToMM(b.GetRight()),pcb.ToMM(b.GetBottom()))


def audit_new_copper(records):
    """Explicit pairwise check, including every layer crossed by a via.

    Crowded native short reports can name only a subset of multiple coincident
    foreign/owned conductors, so their absence is not this internal proof.
    """
    def point_segment(q,a,b):
        dx,dy=b[0]-a[0],b[1]-a[1];d=dx*dx+dy*dy
        t=max(0,min(1,((q[0]-a[0])*dx+(q[1]-a[1])*dy)/d)) if d else 0
        return math.hypot(q[0]-a[0]-t*dx,q[1]-a[1]-t*dy)
    def cross(a,b,c):return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
    def separation(a,b,c,d):
        if cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0:return 0
        return min(point_segment(a,c,d),point_segment(b,c,d),point_segment(c,a,b),point_segment(d,a,b))
    def unpack(r):
        if r['kind']=='via':return r['position_mm'],r['position_mm'],r['diameter_mm']/2,{'F.Cu','In1.Cu','In2.Cu','B.Cu'}
        return r['start_mm'],r['end_mm'],r['width_mm']/2,{r['layer']}
    failures=[]
    for i,a in enumerate(records):
        ap,aq,ar,al=unpack(a)
        for j,b in enumerate(records[i+1:],i+1):
            if a['net']==b['net']:continue
            bp,bq,br,bl=unpack(b)
            if not al.intersection(bl):continue
            gap=separation(ap,aq,bp,bq)-ar-br
            if gap<.2-.000001:failures.append(dict(first=i,second=j,nets=[a['net'],b['net']],edge_gap_mm=gap))
    return failures


def apply_analog_routing_corrections(board):
    """Apply to an in-memory board. Preserve all pre-existing locked copper.

    Returns movements and exact trace/via geometry for the review manifest.
    Existing unlocked tracks on OWNED nets are replaced completely, including
    the shared main shunt's independent INA branch and dedicated test stubs.
    No electrical nets, MPNs, values, pad numbers or source pins are changed.
    """
    fps={f.GetReference():f for f in board.GetFootprints()}
    anchors={'U1':(65,98),'U2':(164,94),'U11':(25,75),'RSH1':(30,45),'RSH2':(120,45)}
    for ref,position in anchors.items():
        if ref not in fps or any(abs(a-b)>.000001 for a,b in zip(xy(fps[ref].GetPosition()),position)) or abs(fps[ref].GetOrientationDegrees())>.000001:
            raise ValueError('Controller/shunt anchor changed; review overlay before use: '+ref)
    for ref in MOVES:
        if ref not in fps:raise ValueError('Missing moved footprint '+ref)
    for net in OWNED:
        if not board.FindNet(net):raise ValueError('Missing authoritative analog net '+net)
    before_locked={t.m_Uuid.AsString() for t in board.GetTracks() if t.IsLocked()}
    protected=[t.GetNetname() for t in board.GetTracks() if t.IsLocked() and t.GetNetname() in OWNED]
    if protected:raise ValueError('Owned net already has locked tracks; refusing duplicate overlay: '+str(sorted(set(protected))))
    movements=[]
    for ref,(x,y,angle) in MOVES.items():
        fp=fps[ref];movements.append(dict(ref=ref,before_mm=xy(fp.GetPosition()),before_rotation=fp.GetOrientationDegrees(),
                                         after_mm=[x,y],after_rotation=angle))
        fp.SetPosition(p(x,y));fp.SetOrientationDegrees(angle)
    # No moved-body collision may be silently handed to the global router.
    collisions=[]
    for ref in MOVES:
        a=bbox(fps[ref])
        for other,fp in fps.items():
            if other==ref or (other in MOVES and other<ref):continue
            b=bbox(fp)
            if min(a[2],b[2])-max(a[0],b[0])>.001 and min(a[3],b[3])-max(a[1],b[1])>.001:
                collisions.append([ref,other,a,b])
    if collisions:raise ValueError('Moved body/courtyard bounding boxes overlap: '+json.dumps(collisions))
    removed=0
    for t in list(board.GetTracks()):
        if t.GetNetname() in OWNED and not t.IsLocked():
            board.Remove(t);_DETACHED.append(t);removed+=1
    pads={f'{f.GetReference()}.{q.GetNumber()}':q for f in board.GetFootprints() for q in f.Pads()}
    records=[]
    def pin(label):return xy(pads[label].GetPosition())
    def line(net,points,layer=pcb.F_Cu,width=.2):
        for label in points:
            if isinstance(label,str) and pads[label].GetNetname()!=net:
                raise ValueError('Pin-net disagreement: '+label+' is not '+net)
        points=[pin(x) if isinstance(x,str) else x for x in points]
        for a,b in zip(points,points[1:]):
            if a==b:continue
            t=pcb.PCB_TRACK(board);t.SetStart(p(*a));t.SetEnd(p(*b));t.SetLayer(layer)
            t.SetWidth(pcb.FromMM(width));t.SetNet(board.FindNet(net));t.SetLocked(True);board.Add(t)
            records.append(dict(kind='track',net=net,start_mm=list(a),end_mm=list(b),layer=pcb.LayerName(layer),width_mm=width))
    def via(net,x,y):
        v=pcb.PCB_VIA(board);v.SetPosition(p(x,y));v.SetLayerPair(pcb.F_Cu,pcb.B_Cu)
        v.SetWidth(pcb.FromMM(.6));v.SetDrill(pcb.FromMM(.3));v.SetNet(board.FindNet(net));v.SetLocked(True);board.Add(v)
        records.append(dict(kind='via',net=net,position_mm=[x,y],diameter_mm=.6,drill_mm=.3))
    def pickup(net,label,at):line(net,[label,at]);via(net,*at)

    # Main local differential capacitor loops: no signal vias between cap and IC.
    line('MAIN_CS_P',['C4.1',(65.75,94.6),'U1.20'])
    line('MAIN_CS_P',['R21.2',(64.0875,93.9),'C4.1'])
    line('MAIN_KELVIN_N',['C4.2',(66.25,94.6),'U1.19'])
    line('MAIN_KELVIN_N',['C4.2',(67.8,94.7),(68.45,94.7),'C5.2'])
    line('MAIN_ISCP',['U1.18',(67.8,96.75),'C5.1'])
    line('MAIN_ISCP',['C5.1',(70.5,97.15),(70.5,97.9125),'R23.2'])
    # Independent main controller pickups and paired In2 corridor outside the
    # x<=28 input and x>=33 sensed force-copper fields / transfer-via columns.
    pickup('MAIN_KELVIN_P','RSH1.2',(26.5,40))
    pickup('MAIN_KELVIN_N','RSH1.3',(33.5,40))
    line('MAIN_KELVIN_P',[(26.5,40),(30.5,40),(30.5,87.5),(31.5,88.5),(61,88.5),(61.8,89.3),(61.8,91.6)],pcb.In2_Cu)
    line('MAIN_KELVIN_N',[(33.5,40),(31.15,40.65),(31.15,86.85),(32.15,87.85),(60.95,87.85),(67.8,94.7)],pcb.In2_Cu)
    pickup('MAIN_KELVIN_P','R21.1',(61.8,91.6))
    pickup('MAIN_KELVIN_N','C4.2',(67.8,94.7))
    # The ISCP programming resistor takes its own branch after the long pair.
    via('MAIN_KELVIN_P',73.2,95.3)
    line('MAIN_KELVIN_P',[(61.8,91.6),(68,91.6),(71.7,95.3),(73.2,95.3)],pcb.In1_Cu)
    line('MAIN_KELVIN_P',[(73.2,95.3),'R23.1'])
    pickup('MAIN_KELVIN_P','TP3.1',(44,90.1));line('MAIN_KELVIN_P',[(44,88.5),(44,90.1)],pcb.In2_Cu)
    pickup('MAIN_KELVIN_N','TP4.1',(44,86.9));line('MAIN_KELVIN_N',[(44,87.85),(44,86.9)],pcb.In2_Cu)

    # INA filter branches start independently at the four-terminal sense pads,
    # using separate vias and the other inner layer; no threshold resistor shared.
    pickup('MAIN_KELVIN_P','RSH1.2',(25.4,40))
    pickup('MAIN_KELVIN_N','RSH1.3',(34.6,40))
    line('MAIN_KELVIN_P',[(25.4,40),(29.3,40),(29.3,64.9),(31.2,66.8),(33,66.8),(33,68.8),(34.5,70.3)],pcb.In1_Cu)
    line('MAIN_KELVIN_N',[(34.6,40),(29.95,40.65),(29.95,64.05),(31.85,65.95),(37,65.95),(37,70.9)],pcb.In1_Cu)
    pickup('MAIN_KELVIN_P','R223.1',(34.5,70.3));pickup('MAIN_KELVIN_N','R224.1',(37,70.9))
    line('INA_IN_P',['R223.2',(32.8375,72.25),'C241.1'])
    line('INA_IN_P',['C241.1',(28.85,72.25),'U11.10'])
    line('INA_IN_N',['R224.2',(36.6625,74.15),'C241.2'])
    line('INA_IN_N',['C241.2',(28.65,74.15),(28.3,74.5),'U11.9'])

    # Motion local loops: CS+/CS- map in pin order onto the vertical capacitor.
    line('MOTION_CS_P',['U2.18',(168.4,92.75),(168.6,92.55),'C11.1'])
    line('MOTION_KELVIN_N',['U2.17',(167.2,93.25),(168.4,94.45),'C11.2'])
    line('MOTION_ISCP',['U2.19',(167.2,92.25),(168,91.45),(168,90.2),'C12.1'])
    line('MOTION_KELVIN_N',['C12.2',(170.95,94.45),'C11.2'])
    # Two short filtered-node feed branches cross the capacitor's common-negative
    # connection on In1; the capacitor-to-IC paths above remain wholly on top.
    pickup('MOTION_CS_P','R30.2',(174,91.8));pickup('MOTION_CS_P','C11.1',(170,91.5))
    line('MOTION_CS_P',[(174,91.8),(170.3,91.8),(170,91.5)],pcb.In1_Cu)
    pickup('MOTION_ISCP','R32.2',(174,86));pickup('MOTION_ISCP','C12.1',(168.9,88.7))
    line('MOTION_ISCP',[(174,86),(171.6,86),(168.9,88.7)],pcb.In1_Cu)
    # Motion pair stays between x118 SYS and x122 motion force copper, and then
    # below the y79 transfer field. It never enters the y109..133 power return.
    pickup('MOTION_KELVIN_P','RSH2.2',(115.975,40))
    pickup('MOTION_KELVIN_N','RSH2.3',(124.025,40))
    line('MOTION_KELVIN_P',[(115.975,40),(119.5,40),(119.5,86.4),(121.6,88.5),(165,88.5),(173,96.5),(175.3,96.5),(175.3,95.6)],pcb.In2_Cu)
    line('MOTION_KELVIN_N',[(124.025,40),(120.15,40.65),(120.15,85.75),(122.25,87.85),(165.26924,87.85),(172.41924,95)],pcb.In2_Cu)
    pickup('MOTION_KELVIN_P','R30.1',(175.3,95.6))
    pickup('MOTION_KELVIN_N','C11.2',(172.41924,95))
    pickup('MOTION_KELVIN_P','R32.1',(175.3,89.4))
    line('MOTION_KELVIN_P',[(175.3,95.6),(175.3,89.4)],pcb.In2_Cu)
    pickup('MOTION_KELVIN_P','TP7.1',(150,90.1));line('MOTION_KELVIN_P',[(150,88.5),(150,90.1)],pcb.In2_Cu)
    pickup('MOTION_KELVIN_N','TP8.1',(146.5,86.4));line('MOTION_KELVIN_N',[(146.5,87.85),(146.5,86.4)],pcb.In2_Cu)
    after_locked={t.m_Uuid.AsString() for t in board.GetTracks() if t.IsLocked()}
    if not before_locked.issubset(after_locked):raise AssertionError('Existing locked copper was removed')
    own_collisions=audit_new_copper(records)
    if own_collisions:raise ValueError('Explicit new-copper collision check failed: '+json.dumps(own_collisions))
    return dict(metadata=dict(rev_a_engineering_prototype=True,rev_b_production=False,
                state='geometry_overlay_requires_native_reroute_and_drc',api_saved_pcb=False),
                moved_footprints=movements,body_bbox_collisions=collisions,
                explicit_new_copper_collision_count=len(own_collisions),
                removed_unlocked_tracks=removed,preserved_preexisting_locked_items=len(before_locked),
                replaced_nets=sorted(OWNED),geometry=records,
                instructions=['Reroute foreign unlocked signal nets intersecting these locked routes or moved pads.',
                              'Refill zones and run native DRC/schematic parity. This manifest is not a DRC pass.',
                              'Apply overlay once to a fresh pre-overlay board; owned locked copper causes an explicit refusal.'])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,default=ROOT/'kicad/HomeMy_PMU_RevA.kicad_pcb')
    ap.add_argument('--report',type=Path,default=ROOT/'reports/analog-routing-corrections.json')
    ap.add_argument('--test-output',type=Path);a=ap.parse_args()
    digest=hashlib.sha256(a.board.read_bytes()).hexdigest();b=pcb.LoadBoard(str(a.board))
    result=apply_analog_routing_corrections(b)
    if digest!=hashlib.sha256(a.board.read_bytes()).hexdigest():raise ValueError('Input changed during overlay test')
    result['input_sha256']=digest;result['script_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if a.test_output:
        if a.test_output.resolve()==a.board.resolve():raise ValueError('CLI may only save a separate test copy')
        b.BuildConnectivity();pcb.ZONE_FILLER(b).Fill(b.Zones());pcb.SaveBoard(str(a.test_output),b)
        for suffix in ['.kicad_pro','.kicad_dru']:
            src=a.board.with_suffix(suffix)
            if src.exists():shutil.copy2(src,a.test_output.with_suffix(suffix))
        result['test_copy']=str(a.test_output.resolve())
    a.report.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print('Moved',len(MOVES),'footprints; body bounding boxes clear; added',len(result['geometry']),'locked items. Input board unchanged.')
    return 0


if __name__=='__main__':
    try:code=main()
    except BaseException:traceback.print_exc();exit_native(1)
    exit_native(code)
