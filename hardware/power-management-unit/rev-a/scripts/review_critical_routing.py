"""Read-only centerline geometry review of current protection and gate routing.

This deliberately does not replace native connectivity/clearance DRC. Reported
path lengths include straight pad-center-to-track-end leads inside pads. Plane
return paths, field coupling and propagation behavior are not inferred.
"""
import argparse
import collections
import ctypes
from datetime import datetime, timezone
import hashlib
import heapq
import itertools
import json
import math
import os
from pathlib import Path
import sys
import traceback
import pcbnew as pcb

ROOT=Path(__file__).resolve().parents[1]
LAYERS=[pcb.F_Cu,pcb.In1_Cu,pcb.In2_Cu,pcb.B_Cu]
NETS=['MAIN_KELVIN_P','MAIN_KELVIN_N','MAIN_CS_P','MAIN_ISCP',
      'MOTION_KELVIN_P','MOTION_KELVIN_N','MOTION_CS_P','MOTION_ISCP',
      'INA_IN_P','INA_IN_N','MAIN_HGATE','MAIN_DGATE','MAIN_CAP',
      'MOTION_PU','MOTION_GATE_DRIVE','MOTION_BST','MOTION_COMMON','V3V3']+['Q%d_G'%n for n in range(1,11)]
PAIRS=[('main_positive_sense','RSH1.2','R21.1'),
       ('main_negative_sense','RSH1.3','U1.19'),
       ('main_positive_short_circuit','RSH1.2','R23.1'),
       ('ina_positive_kelvin','RSH1.2','R223.1'),
       ('ina_negative_kelvin','RSH1.3','R224.1'),
       ('ina_positive_filter','R223.2','U11.10'),
       ('ina_negative_filter','R224.2','U11.9'),
       ('ina_positive_cap','C241.1','U11.10'),
       ('ina_negative_cap','C241.2','U11.9'),
       ('main_positive_filter','C4.1','U1.20'),
       ('main_negative_filter','C4.2','U1.19'),
       ('main_iscp_filter','C5.1','U1.18'),
       ('motion_positive_sense','RSH2.2','R30.1'),
       ('motion_negative_sense','RSH2.3','U2.17'),
       ('motion_positive_short_circuit','RSH2.2','R32.1'),
       ('motion_positive_filter','C11.1','U2.18'),
       ('motion_negative_filter','C11.2','U2.17'),
       ('motion_iscp_filter','C12.1','U2.19'),
       ('motion_boost_first','C9.1','U2.12'),
       ('motion_boost_second','C29.1','U2.12'),
       ('motion_source_first_boost','U2.13','C9.2'),
       ('motion_source_second_boost','U2.13','C29.2'),
       ('ina_supply_decoupling','C206.1','U11.6'),
       ('main_charge_pump_cap','C2.1','U1.23'),
       ('motion_pu_resistor','U2.15','R34.1'),
       ('motion_pull_down','U2.14','R34.2')]
PAIRS += [('main_gate_%d'%n,'U1.'+('14' if n<=3 else '1'),'R%d.1'%n) for n in range(1,7)]
PAIRS += [('motion_gate_%d'%n,'U2.14','R%d.1'%n) for n in range(7,11)]
PAIRS += [('local_gate_%d'%n,'R%d.2'%n,'Q%d.1'%n) for n in range(1,11)]


def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def pt(v): return (int(v.x),int(v.y))
def mm(v): return [round(x/1e6,6) for x in v]
def dist(a,b): return math.hypot(a[0]-b[0],a[1]-b[1])/1e6
def exit_native(code):
    sys.stdout.flush();sys.stderr.flush()
    if os.name=='nt':
        k=ctypes.windll.kernel32;k.GetCurrentProcess.restype=ctypes.c_void_p
        k.TerminateProcess(ctypes.c_void_p(k.GetCurrentProcess()),code)
    raise SystemExit(code)


def graph_for(net,tracks,pads):
    graph=collections.defaultdict(list)
    ends=collections.defaultdict(set)
    segments=[];vias=[]
    def edge(a,b,length,kind):
        graph[a].append((b,length,kind));graph[b].append((a,length,kind))
    for t in tracks:
        if t.GetNetname()!=net: continue
        if isinstance(t,pcb.PCB_VIA):
            p=pt(t.GetPosition());ls=[l for l in LAYERS if t.IsOnLayer(l)]
            vias.append((p,ls))
            for l in ls: ends[l].add(p)
        else:
            if isinstance(t,pcb.PCB_ARC):
                raise ValueError('Arc path metric requires arc handling; no silently approximated arc')
            a,b,l=pt(t.GetStart()),pt(t.GetEnd()),t.GetLayer()
            segments.append((a,b,l));ends[l].update([a,b])
    # Split at explicit track/via junction coordinates, including T junctions.
    for a,b,l in segments:
        dx,dy=b[0]-a[0],b[1]-a[1];den=dx*dx+dy*dy
        points=[]
        for p in ends[l]:
            f=((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den if den else 0
            if -.0000001<=f<=1.0000001 and abs((p[0]-a[0])*dy-(p[1]-a[1])*dx)<=10*math.sqrt(den):
                points.append((f,p))
        points.sort()
        for (_,p),(_,q) in zip(points,points[1:]):edge((*p,l),(*q,l),dist(p,q),'track')
    for p,ls in vias:
        for l,m in itertools.combinations(ls,2):edge((*p,l),(*p,m),0,'via')
    for label,pad in pads.items():
        if pad.GetNetname()!=net:continue
        center=pt(pad.GetPosition())
        for l in LAYERS:
            if not pad.IsOnLayer(l):continue
            for p in ends[l]:
                if pad.HitTest(pcb.VECTOR2I(*p),0,l):edge(label,(*p,l),dist(center,p),'pad_lead')
    return graph


def shortest(graph,start,end):
    queue=[(0,0,start)];d={start:0};prev={};serial=0
    while queue:
        cost,_,u=heapq.heappop(queue)
        if cost!=d[u]:continue
        if u==end:break
        for v,length,kind in graph[u]:
            nd=cost+length
            if nd<d.get(v,float('inf')):
                d[v]=nd;prev[v]=(u,length,kind);serial+=1;heapq.heappush(queue,(nd,serial,v))
    if end not in d:return dict(path_found=False)
    vertices=[end];steps=[];u=end
    while u!=start:
        p,length,kind=prev[u];steps.append((p,u,length,kind));vertices.append(p);u=p
    steps.reverse();vertices.reverse()
    coords=[v for v in vertices if not isinstance(v,str)]
    return dict(path_found=True,centerline_with_pad_leads_mm=round(d[end],4),
                copper_track_length_mm=round(sum(s[2] for s in steps if s[3]=='track'),4),
                via_transitions=sum(s[3]=='via' for s in steps),
                layers=sorted({pcb.LayerName(v[2]) for v in coords}),
                vertices=[v if isinstance(v,str) else dict(x_mm=v[0]/1e6,y_mm=v[1]/1e6,layer=pcb.LayerName(v[2])) for v in vertices])


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,default=ROOT/'kicad/HomeMy_PMU_RevA.kicad_pcb')
    ap.add_argument('--output',type=Path,default=ROOT/'reports/critical-routing-geometry.json');args=ap.parse_args()
    initial=sha(args.board);board=pcb.LoadBoard(str(args.board));tracks=list(board.GetTracks())
    pads={f'{fp.GetReference()}.{p.GetNumber()}':p for fp in board.GetFootprints() for p in fp.Pads()}
    nets={};graphs={}
    for net in NETS:
        rows=[];vi=[]
        for t in tracks:
            if t.GetNetname()!=net:continue
            if isinstance(t,pcb.PCB_VIA):
                vi.append(dict(position_mm=mm(pt(t.GetPosition())),diameter_mm=t.GetWidth(pcb.F_Cu)/1e6,
                               layers=[pcb.LayerName(l) for l in LAYERS if t.IsOnLayer(l)]))
            else:
                rows.append(dict(start_mm=mm(pt(t.GetStart())),end_mm=mm(pt(t.GetEnd())),
                                 layer=pcb.LayerName(t.GetLayer()),width_mm=t.GetWidth()/1e6,length_mm=t.GetLength()/1e6))
        graphs[net]=graph_for(net,tracks,pads)
        nets[net]=dict(total_track_length_mm=round(sum(x['length_mm'] for x in rows),4),
                       via_count=len(vi),layers=sorted({r['layer'] for r in rows}),segments=rows,vias=vi,
                       pads=[dict(pin=k,center_mm=mm(pt(p.GetPosition()))) for k,p in pads.items() if p.GetNetname()==net],
                       zone_count=sum(z.GetNetname()==net for z in board.Zones()))
    paths=[]
    for label,a,b in PAIRS:
        if a not in pads or b not in pads:raise ValueError('Missing endpoint '+a+' or '+b)
        net=pads[a].GetNetname()
        if pads[b].GetNetname()!=net:raise ValueError('Mismatched endpoint net '+label)
        result=shortest(graphs[net],a,b)
        paths.append(dict(name=label,start=a,end=b,net=net,direct_pad_distance_mm=round(dist(pt(pads[a].GetPosition()),pt(pads[b].GetPosition())),4),**result))
    from analog_routing_corrections import audit_new_copper, OWNED
    locked_analog=[]
    for t in tracks:
        if not t.IsLocked() or t.GetNetname() not in OWNED:continue
        if isinstance(t,pcb.PCB_VIA):
            locked_analog.append(dict(kind='via',net=t.GetNetname(),position_mm=mm(pt(t.GetPosition())),diameter_mm=t.GetWidth(pcb.F_Cu)/1e6))
        else:
            locked_analog.append(dict(kind='track',net=t.GetNetname(),start_mm=mm(pt(t.GetStart())),end_mm=mm(pt(t.GetEnd())),layer=pcb.LayerName(t.GetLayer()),width_mm=t.GetWidth()/1e6))
    own_errors=audit_new_copper(locked_analog)
    missing_paths=[row['name'] for row in paths if not row['path_found']]
    if initial!=sha(args.board):raise ValueError('Board changed while reviewing')
    report=dict(metadata=dict(rev_a_engineering_prototype=True,rev_b_production=False,
                state='read_only_geometry_review_not_order_release',checked_at_utc=datetime.now(timezone.utc).isoformat(),
                pcb_written=False,erc_or_drc_claim=False,all_required_explicit_paths_found=not missing_paths),board=dict(path=str(args.board.resolve()),sha256=initial),
                method='Shortest path of explicit same-net track centerlines, vias and pad-interior center leads. This excludes plane-return paths and field effects. Via vertical length is not included.',
                footprints=[dict(ref=fp.GetReference(),center_mm=mm(pt(fp.GetPosition())),rotation=fp.GetOrientationDegrees(),
                             pads=[dict(pin=p.GetNumber(),center_mm=mm(pt(p.GetPosition())),size_mm=mm(pt(p.GetSize())),net=p.GetNetname()) for p in fp.Pads()]) for fp in board.GetFootprints()],
                locked_analog_copper_check=dict(item_count=len(locked_analog),errors=own_errors,
                    scope='Pairwise centerline/copper-radius clearance only among locked analog items; pads, zones and foreign nets remain native DRC responsibilities.'),
                missing_explicit_paths=missing_paths,nets=nets,paths=paths)
    args.output.write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
    for row in paths:
        print(row['name'],row['start'],row['end'],row.get('centerline_with_pad_leads_mm','NO PATH'),row.get('via_transitions'),row.get('layers'))
    print('Locked analog items:',len(locked_analog),'pairwise collision errors:',len(own_errors))
    return 2 if missing_paths or own_errors else 0


if __name__=='__main__':
    try:code=main()
    except BaseException:traceback.print_exc();exit_native(1)
    exit_native(code)
