"""Protect measured force-current bottlenecks and remove router dead stubs.

This is a reviewed, placement-specific post-import repair. Foreign signal nets
crossing the added force-current corridors are removed for a fresh native DSN
routing pass. Locked existing routes are never silently removed.
"""
import hashlib
import json
import math
import traceback
from collections import Counter
import pcbnew as pcb
from build_board import force_exit, point, mm
from build_schematic import ROOT, CAD, PROJECT


def xy(p):
    return (pcb.ToMM(p.x),pcb.ToMM(p.y))


def point_distance(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    length=dx*dx+dy*dy
    t=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/length)) if length else 0
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)


def segment_distance(a,b,c,d):
    def cross(p,q,r):
        return (q[0]-p[0])*(r[1]-p[1])-(q[1]-p[1])*(r[0]-p[0])
    if cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0:
        return 0
    return min(point_distance(a,c,d),point_distance(b,c,d),point_distance(c,a,b),point_distance(d,a,b))


def main():
    filename=CAD/(PROJECT+'.kicad_pcb')
    before=hashlib.sha256(filename.read_bytes()).hexdigest()
    board=pcb.LoadBoard(str(filename))
    print('Loaded routing candidate.',flush=True)
    specifications=[
        ('MOTION_SENSED_P',[(124.025,45),(135,45)],4,pcb.F_Cu),
        ('CHOPPER_N',[(299.5,44),(299.5,42),(298,42)],.3,pcb.F_Cu),
        ('LOGIC_GND',[(308.7875,245),(308.7875,243.4),(303.0625,243.4),(303.0625,244.05)],.25,pcb.F_Cu),
    ]
    for layer in (pcb.In1_Cu,pcb.In2_Cu):
        specifications.extend([
            ('LIFT_N',[(349,85.92),(341.5,85.92)],3,layer),
            ('LIFT_N',[(341.5,85.92),(341.5,112),(310,112),(310,122)],8,layer)])
    detached=[]
    for t in list(board.GetTracks()):
        if t.GetNetname()=='LIFT_N' and t.IsLocked():
            board.Remove(t);detached.append(t)
    conflict_nets=set()
    collisions=[]
    for net,path,width,layer in specifications:
        for t in board.GetTracks():
            if t.GetNetname()==net or not t.IsOnLayer(layer):
                continue
            tw=pcb.ToMM(t.GetWidth(layer) if isinstance(t,pcb.PCB_VIA) else t.GetWidth())
            if any(segment_distance(a,b,xy(t.GetStart()),xy(t.GetEnd()))<(width+tw)/2+.205
                   for a,b in zip(path,path[1:])):
                if t.IsLocked():
                    raise RuntimeError('New power route conflicts with locked '+t.GetNetname())
                conflict_nets.add(t.GetNetname())
                collisions.append({'new_net':net,'foreign_net':t.GetNetname(),'uuid':t.m_Uuid.AsString()})
    print('Conflicting signal nets:',sorted(conflict_nets),flush=True)
    removed=Counter()
    dead_stubs=[]
    for t in list(board.GetTracks()):
        # The router wrote the same open-ended segment in both directions on
        # each of two layers. All four are redundant branches from a real via.
        stub=t.GetNetname()=='MAIN_CS_P' and not isinstance(t,pcb.PCB_VIA) and {
            tuple(round(v,4) for v in xy(t.GetStart())),
            tuple(round(v,4) for v in xy(t.GetEnd()))}=={(71.144,98.7036),(69.8572,97.4168)}
        if stub:
            dead_stubs.append(t.m_Uuid.AsString());board.Remove(t);detached.append(t)
        elif t.GetNetname() in conflict_nets and not t.IsLocked():
            removed[t.GetNetname()]+=1;board.Remove(t);detached.append(t)
    print('Removed signal items:',dict(removed),flush=True)
    added=[]
    for net,path,width,layer in specifications:
        for a,b in zip(path,path[1:]):
            if any(t.GetNetname()==net and t.GetLayer()==layer and not isinstance(t,pcb.PCB_VIA)
                   and {xy(t.GetStart()),xy(t.GetEnd())}=={a,b} for t in board.GetTracks()):
                continue
            t=pcb.PCB_TRACK(board);t.SetStart(point(*a));t.SetEnd(point(*b))
            t.SetLayer(layer);t.SetWidth(mm(width));t.SetNet(board.FindNet(net))
            t.SetLocked(True);board.Add(t)
            added.append({'net':net,'start':a,'end':b,'width_mm':width,'layer':board.GetLayerName(layer)})
    print('Added locked force segments; rebuilding connectivity.',flush=True)
    board.BuildConnectivity()
    print('Filling native zones.',flush=True)
    filler=pcb.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    print('Saving repaired board.',flush=True)
    pcb.SaveBoard(str(filename),board)
    result={'rev_a_engineering_prototype':True,'rev_b_production':False,
            'board_sha256_before':before,'board_sha256_after':hashlib.sha256(filename.read_bytes()).hexdigest(),
            'added_locked_segments':added,'removed_router_dead_stubs':dead_stubs,
            'removed_signal_items_by_net':dict(removed),'collision_basis':collisions,
            'required_next_step':'Native DRC, fresh native DSN routing, import/refill and final native DRC.'}
    (ROOT/'reports/postroute-repair.json').write_text(json.dumps(result,indent=2))
    print('Added',len(added),'locked segments; removed',len(dead_stubs),'dead stubs; reroute nets:',dict(removed),flush=True)
    # Keep native owners alive until the CLI's force_exit. In this portable
    # SWIG build, dropping detached track proxies during main() scope cleanup
    # emits leak diagnostics and can enter the native DLL shutdown deadlock.
    return board, detached, filler


if __name__=='__main__':
    try:
        native_owners = main()
    except BaseException:
        traceback.print_exc();force_exit(1)
    force_exit(0)
