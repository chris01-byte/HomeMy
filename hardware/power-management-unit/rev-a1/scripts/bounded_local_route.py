# Derived from WIP route_local_connections.py; restricted to one 480-second pass.
# Power/branch nets are excluded rather than routed with relaxed class widths.
"""Bounded four-layer local routing candidates against native copper shapes.

The search preserves pads, locked copper and keepouts. Optional rip-up is limited
to narrow unlocked conductors and records every removal. It adds 0.20mm control/
signal routes with explicitly configured vias, then fills the one active candidate. Native DRC and independent
power/critical-path reviews remain mandatory. This is not a release checker.
"""
from pathlib import Path
import argparse,collections,hashlib,heapq,itertools,json,math,sys,time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT.parent/'rev-a/scripts'))
import pcbnew as pcb
from build_board import force_exit,point,mm
from configure_power_rules import POWER_NETS
from review_critical_routing import NETS as CRITICAL_NETS
from bounded_checks import LEDGER, minutes, write
FORCE_NETS = set(POWER_NETS) | {"DRIVE_N","LIFT_N","CHOPPER_N","CHOP_DRAIN","PC_BUCK_IN_P","LOGIC_BUCK_IN_P","PC_N","LOGIC_BUCK_N","LOGIC_5V_N","V5V"}

LAYERS=[pcb.F_Cu,pcb.In1_Cu,pcb.In2_Cu,pcb.B_Cu]
STEP=.05
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def xy(p):return (pcb.ToMM(p.x),pcb.ToMM(p.y))
def ends(t):
    if isinstance(t,pcb.PCB_TRACK) and not isinstance(t,pcb.PCB_VIA):return [xy(t.GetStart()),xy(t.GetEnd())]
    return [xy(t.GetPosition())]
def projected(p,t):
    ep=ends(t)
    if len(ep)==1:return ep[0]
    a,b=ep;dx=b[0]-a[0];dy=b[1]-a[1];den=dx*dx+dy*dy
    f=max(0,min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/den)) if den else 0
    return (a[0]+f*dx,a[1]+f*dy)

def main():
    global STEP
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--drc',type=Path,required=True)
    ap.add_argument('--seconds-per-pair',type=float,default=8)
    ap.add_argument('--max-distance',type=float,default=45);ap.add_argument('--net',action='append')
    ap.add_argument('--component-endpoints',action='store_true',help='Search from all local anchors of the explicit same-net connected components, excluding zones')
    ap.add_argument('--grid-mm',type=float,default=.05)
    ap.add_argument('--ripup-unlocked',action='store_true',help='Allow only narrow unlocked signal/control copper to be rearranged; every removal is recorded')
    ap.add_argument('--signal-via-diameter',type=float,default=.6);ap.add_argument('--signal-via-drill',type=float,default=.3)
    ap.add_argument('--reviewed-power-control-vias',action='store_true',help='Use 0.60/0.30 mm vias only for explicitly selected low-current power-net control taps; never for force copper')
    args=ap.parse_args()
    if args.grid_mm not in [.05,.1,.2]:raise ValueError('Choose a supported routing grid')
    STEP=args.grid_mm
    if args.signal_via_diameter<.5 or args.signal_via_drill<.2 or (args.signal_via_diameter-args.signal_via_drill)/2<.1:
        raise ValueError('Via geometry violates the existing board manufacturing minimums')
    if args.reviewed_power_control_vias and (not args.net or any(n not in POWER_NETS for n in args.net)):
        raise ValueError('Explicit power-net control selection required')
    args.output=args.board
    ledger=json.loads(LEDGER.read_text(encoding='utf-8')); cycle=ledger['cycles'][-1]
    assert cycle['status']=='in_progress' and not cycle.get('local_routing_pass') and minutes(ledger)<140 and not ledger.get('stop_required')
    cycle['local_routing_pass']=1;write(LEDGER,ledger)
    pass_deadline=time.monotonic()+480
    board=pcb.LoadBoard(str(args.board));initial=sha(args.board)
    edge_box=board.GetBoardEdgesBoundingBox(); W=pcb.ToMM(edge_box.GetWidth()); H=pcb.ToMM(edge_box.GetHeight())
    items=list(board.GetTracks())+[p for f in board.GetFootprints() for p in f.Pads()]
    lookup={t.m_Uuid.AsString():t for t in items};shapes={};spatial=collections.defaultdict(list);via_cells=collections.defaultdict(list)
    created=[];records=[];failed=[];owners=[];removed=set();removal_records=[]
    def ripable(t):
        if not args.ripup_unlocked or isinstance(t,pcb.PAD) or t.IsLocked() or t.GetNetname() in FORCE_NETS or t.GetNetname() in CRITICAL_NETS:return False
        return pcb.ToMM(t.GetDrillValue())<=.4 if isinstance(t,pcb.PCB_VIA) else pcb.ToMM(t.GetWidth())<=.4
    def index(t):
        uid=t.m_Uuid.AsString();box=t.GetBoundingBox()
        x1=math.floor(pcb.ToMM(box.GetX())/2);x2=math.floor(pcb.ToMM(box.GetRight())/2)
        y1=math.floor(pcb.ToMM(box.GetY())/2);y2=math.floor(pcb.ToMM(box.GetBottom())/2)
        for li,layer in enumerate(LAYERS):
            if not t.IsOnLayer(layer):continue
            shapes[uid,li]=t.GetEffectiveShape(layer)
            for i in range(x1,x2+1):
                for j in range(y1,y2+1):spatial[i,j,li].append(t)
        if isinstance(t,pcb.PCB_VIA) or isinstance(t,pcb.PAD) and t.GetDrillSize().x>0:
            x,y=xy(t.GetPosition());via_cells[math.floor(x/2),math.floor(y/2)].append(t)
    for t in items:index(t)
    def component(seed):
        if not args.component_endpoints:return [seed]
        result={seed.m_Uuid.AsString():seed};pending=[seed];net=seed.GetNetname()
        while pending:
            t=pending.pop();box=t.GetBoundingBox();box.Inflate(10)
            for li,l in enumerate(LAYERS):
                if not t.IsOnLayer(l):continue
                shape=shapes[t.m_Uuid.AsString(),li];seen=set()
                for i in range(math.floor(pcb.ToMM(box.GetX())/2),math.floor(pcb.ToMM(box.GetRight())/2)+1):
                    for j in range(math.floor(pcb.ToMM(box.GetY())/2),math.floor(pcb.ToMM(box.GetBottom())/2)+1):
                        for other in spatial[i,j,li]:
                            uid=other.m_Uuid.AsString()
                            if uid in seen or uid in result or uid in removed or other.GetNetname()!=net:continue
                            seen.add(uid)
                            if box.Intersects(other.GetBoundingBox()) and shape.Collide(shapes[uid,li],1):result[uid]=other;pending.append(other)
        return list(result.values())
    keepouts=[z for f in board.GetFootprints() for z in f.Zones() if z.GetIsRuleArea()]+[z for z in board.Zones() if z.GetIsRuleArea()]
    def nearby(x,y,li,r=.8):
        seen=set()
        for i in range(math.floor((x-r)/2),math.floor((x+r)/2)+1):
            for j in range(math.floor((y-r)/2),math.floor((y+r)/2)+1):
                for t in spatial[i,j,li]:
                    uid=t.m_Uuid.AsString()
                    if uid not in seen and uid not in removed:seen.add(uid);yield t
    def at_clear(x,y,li,net,r=.1,via=False):
        if x<.501+r or x>W-.501-r or y<.501+r or y>H-.501-r:return False
        p=point(x,y)
        for z in keepouts:
            if z.GetLayerSet().Contains(LAYERS[li]) and (z.GetDoNotAllowVias() if via else z.GetDoNotAllowTracks()) and z.Outline().Collide(p,mm(r)):return False
        for t in nearby(x,y,li,r+.25):
            own=t.GetNetname()==net
            if via and (isinstance(t,pcb.PCB_VIA) or isinstance(t,pcb.PAD) and t.GetDrillSize().x>0):
                other_drill=pcb.ToMM(t.GetDrillValue() if isinstance(t,pcb.PCB_VIA) else t.GetDrillSize().x)
                new_drill=(.3 if args.reviewed_power_control_vias else .4) if net in POWER_NETS else args.signal_via_drill
                if math.dist((x,y),xy(t.GetPosition()))<(other_drill+new_drill)/2+.25001:return False
            if own:
                if not via or not isinstance(t,pcb.PAD) or t.GetDrillSize().x>0:continue
                # Ordinary vias stay outside the SMD lands, including own-net.
                clearance=r+.15
            else:clearance=r+.2
            if not own and ripable(t):continue
            if shapes[t.m_Uuid.AsString(),li].Collide(p,mm(clearance)-10):return False
        return True
    def segment(net,li,a,b):
        t=pcb.PCB_TRACK(board);t.SetStart(point(*a));t.SetEnd(point(*b));t.SetWidth(mm(.2));t.SetLayer(LAYERS[li]);t.SetNet(board.FindNet(net));return t
    def segment_clear(net,li,a,b):
        t=segment(net,li,a,b);shape=t.GetEffectiveShape(LAYERS[li]);bbox=t.GetBoundingBox();bbox.Inflate(mm(.201))
        for z in keepouts:
            if z.GetLayerSet().Contains(LAYERS[li]) and z.GetDoNotAllowTracks() and z.Outline().Collide(shape,0):return False
        seen=set()
        for i in range(math.floor(pcb.ToMM(bbox.GetX())/2),math.floor(pcb.ToMM(bbox.GetRight())/2)+1):
            for j in range(math.floor(pcb.ToMM(bbox.GetY())/2),math.floor(pcb.ToMM(bbox.GetBottom())/2)+1):
                for other in spatial[i,j,li]:
                    uid=other.m_Uuid.AsString()
                    if uid in seen or uid in removed or other.GetNetname()==net or ripable(other):continue
                    seen.add(uid)
                    if shape.Collide(shapes[uid,li],mm(.2)-10):return False
        return True
    def existing_transition(x,y,net):
        for i in range(math.floor((x-.4)/2),math.floor((x+.4)/2)+1):
            for j in range(math.floor((y-.4)/2),math.floor((y+.4)/2)+1):
                for t in via_cells[i,j]:
                    if t.m_Uuid.AsString() not in removed and t.GetNetname()==net and shapes[t.m_Uuid.AsString(),0].Collide(point(x,y),-mm(.1)):return True
        return False
    directions=[(1,0,1),(-1,0,1),(0,1,1),(0,-1,1),(1,1,math.sqrt(2)),(1,-1,math.sqrt(2)),(-1,1,math.sqrt(2)),(-1,-1,math.sqrt(2))]
    raw=json.loads(args.drc.read_text(encoding='utf-8'))['unconnected_items']
    pairs=[]
    for row in raw:
        ids=[x['uuid'] for x in row['items']]
        if len(ids)!=2 or any(i not in lookup for i in ids):continue
        a,b=(lookup[i] for i in ids);net=a.GetNetname()
        if net in FORCE_NETS or net in CRITICAL_NETS:continue
        if net!=b.GetNetname():raise ValueError('Different nets')
        if args.net and net not in args.net:continue
        candidates=[(p,projected(p,b)) for p in ends(a)]+[(projected(p,a),p) for p in ends(b)]
        p,q=min(candidates,key=lambda t:math.dist(*t));distance=math.dist(p,q)
        if distance<.00001:
            if not existing_transition(p[0],p[1],net) and all(at_clear(p[0],p[1],li,net,.3,True) for li in range(4)):
                v=pcb.PCB_VIA(board);v.SetPosition(point(*p));v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetWidth(mm(.6));v.SetDrill(mm(.3));v.SetNet(board.FindNet(net));v.SetLocked(True);board.Add(v);created.append(v);index(v)
                records.append({'net':net,'endpoint_uuids':ids,'kind':'explicit_cross_layer_junction','via_mm':p})
            else:failed.append({'net':net,'endpoint_uuids':ids,'reason':'Coincident endpoints lack a clearance-valid via site'})
            continue
        if distance>args.max_distance:continue
        pairs.append((distance,net,ids,p,q,a,b))
    # Finish short local connections before expensive long detours.
    pairs.sort(key=lambda r:r[0])
    for order,(distance,net,ids,p,q,a,b) in enumerate(pairs,1):
        if time.monotonic()>=pass_deadline or minutes(ledger)>=140:
            failed.append({'reason':'Single-pass time bound reached','remaining_pairs':len(pairs)-order+1});break
        if any(i in removed for i in ids):
            failed.append({'net':net,'endpoint_uuids':ids,'reason':'Endpoint changed by an earlier local repair; requires fresh native DRC'})
            continue
        started=time.monotonic();deadline=started+args.seconds_per_pair
        comp_a=component(a);comp_b=component(b)
        if {t.m_Uuid.AsString() for t in comp_a}&{t.m_Uuid.AsString() for t in comp_b}:
            print(order,'/',len(pairs),net,'already explicitly connected',flush=True);continue
        allowed_a=[i for i,l in enumerate(LAYERS) if a.IsOnLayer(l)];allowed_b=[i for i,l in enumerate(LAYERS) if b.IsOnLayer(l)]
        radius=(.3 if args.reviewed_power_control_vias else .4) if net in POWER_NETS else args.signal_via_diameter/2
        def grid_options(pt):return list(set(itertools.product([math.floor(pt[0]/STEP),math.ceil(pt[0]/STEP)],[math.floor(pt[1]/STEP),math.ceil(pt[1]/STEP)])))
        clear_cache={};via_cache={};soft_cache={}
        def clear(n):
            if n not in clear_cache:clear_cache[n]=at_clear(n[0]*STEP,n[1]*STEP,n[2],net)
            return clear_cache[n]
        def via_ok(i,j):
            if (i,j) not in via_cache:
                x,y=i*STEP,j*STEP
                via_cache[i,j]=existing_transition(x,y,net) or all(at_clear(x,y,li,net,radius,True) for li in range(4))
            return via_cache[i,j]
        def soft_cost(n):
            if not args.ripup_unlocked:return 0
            if n not in soft_cache:
                x,y,li=n[0]*STEP,n[1]*STEP,n[2];pnt=point(x,y)
                soft_cache[n]=.15*sum(t.GetNetname()!=net and ripable(t) and shapes[t.m_Uuid.AsString(),li].Collide(pnt,mm(.301)) for t in nearby(x,y,li))
            return soft_cache[n]
        # A broad local window permits routing around fixed power corridors.
        margin=7.;bounds=(math.floor((min(p[0],q[0])-margin)/STEP),math.ceil((max(p[0],q[0])+margin)/STEP),
                          math.floor((min(p[1],q[1])-margin)/STEP),math.ceil((max(p[1],q[1])+margin)/STEP))
        def anchor_nodes(comp,original_pt,original_layers):
            sites=[(original_pt,original_layers)]+[(pt,[li for li,l in enumerate(LAYERS) if item.IsOnLayer(l)]) for item in comp for pt in ends(item)]
            result={}
            for pt,ls in sites:
                if not bounds[0]*STEP<=pt[0]<=bounds[1]*STEP or not bounds[2]*STEP<=pt[1]<=bounds[3]*STEP:continue
                for i,j in grid_options(pt):
                    for li in ls:
                        n=i,j,li
                        if clear(n) and segment_clear(net,li,pt,(i*STEP,j*STEP)):result[n]=pt
            return result
        start_points=anchor_nodes(comp_a,p,allowed_a);goal_points=anchor_nodes(comp_b,q,allowed_b)
        starts=list(start_points);goals=set(goal_points)
        def h(n):return math.hypot(n[0]*STEP-q[0],n[1]*STEP-q[1])+(0 if n[2] in allowed_b else 1)
        queue=[];cost={};prev={};serial=0
        for n in starts:cost[n]=math.dist((n[0]*STEP,n[1]*STEP),start_points[n]);heapq.heappush(queue,(cost[n]+h(n),serial,cost[n],n));serial+=1
        found=None;expanded=0
        while queue and goals:
            _,_,queued_cost,n=heapq.heappop(queue)
            if queued_cost>cost[n]+1e-12:continue
            expanded+=1
            if expanded%64==0 and time.monotonic()>deadline:break
            if n in goals:found=n;break
            i,j,li=n;c=cost[n]
            for dx,dy,length in directions:
                v=(i+dx,j+dy,li)
                if not (bounds[0]<=v[0]<=bounds[1] and bounds[2]<=v[1]<=bounds[3]) or not clear(v):continue
                if dx and dy and (not clear((i+dx,j,li)) or not clear((i,j+dy,li))):continue
                nc=c+STEP*length+soft_cost(v)
                if nc<cost.get(v,float('inf')):
                    cost[v]=nc;prev[v]=n;heapq.heappush(queue,(nc+1.08*h(v),serial,nc,v));serial+=1
            if via_ok(i,j):
                for lj in range(4):
                    if lj==li:continue
                    v=(i,j,lj)
                    if not clear(v):continue
                    nc=c+(.08 if existing_transition(i*STEP,j*STEP,net) else 1.5)+soft_cost(v)
                    if nc<cost.get(v,float('inf')):
                        cost[v]=nc;prev[v]=n;heapq.heappush(queue,(nc+1.08*h(v),serial,nc,v));serial+=1
        if found is None:
            failed.append({'net':net,'endpoint_uuids':ids,'direct_mm':distance,'expanded_nodes':expanded,'start_nodes':len(starts),'goal_nodes':len(goals)})
            print(order,'/',len(pairs),net,'not completed',expanded,'nodes',flush=True);continue
        chain=[found]
        while chain[-1] in prev:chain.append(prev[chain[-1]])
        chain.reverse()
        first=start_points[chain[0]];last=goal_points[chain[-1]]
        vertices=[(first[0],first[1],chain[0][2])]+[(i*STEP,j*STEP,li) for i,j,li in chain]+[(last[0],last[1],chain[-1][2])]
        compact=[]
        for v in vertices:
            if compact and math.dist(v,compact[-1])<1e-8:continue
            if len(compact)>=2 and compact[-2][2]==compact[-1][2]==v[2]:
                u,w=compact[-2],compact[-1]
                if abs((w[0]-u[0])*(v[1]-w[1])-(w[1]-u[1])*(v[0]-w[0]))<1e-8:compact.pop()
            compact.append(v)
        # Shorten grid staircases only where the exact native capsule is clear.
        smooth=[];i=0
        while i<len(compact):
            smooth.append(compact[i]);j=i+1
            while j<len(compact) and compact[j][2]==compact[i][2]:j+=1
            next_i=i+1
            for k in range(j-1,i+1,-1):
                if segment_clear(net,compact[i][2],compact[i][:2],compact[k][:2]):next_i=k;break
            i=next_i
        compact=smooth
        segments=[(u[2],u[:2],v[:2]) for u,v in zip(compact,compact[1:]) if u[2]==v[2] and math.dist(u[:2],v[:2])>1e-6]
        if not all(segment_clear(net,li,u,v) for li,u,v in segments):
            failed.append({'net':net,'endpoint_uuids':ids,'reason':'Exact native segment collision after grid search'})
            print(order,'/',len(pairs),net,'rejected by exact native segment check',flush=True);continue
        new_vias=[]
        for u,v in zip(compact,compact[1:]):
            if u[2]==v[2] or existing_transition(u[0],u[1],net):continue
            if u[:2] in new_vias:continue
            new_vias.append(u[:2])
        pending=[segment(net,li,u,v) for li,u,v in segments]
        for x,y in new_vias:
            drill=(.3 if args.reviewed_power_control_vias else .4) if net in POWER_NETS else args.signal_via_drill
            v=pcb.PCB_VIA(board);v.SetPosition(point(x,y));v.SetLayerPair(pcb.F_Cu,pcb.B_Cu);v.SetWidth(mm(radius*2));v.SetDrill(mm(drill));v.SetNet(board.FindNet(net));pending.append(v)
        pair_removed=[]
        for new_item in pending:
            for li,layer in enumerate(LAYERS):
                if not new_item.IsOnLayer(layer):continue
                shape=new_item.GetEffectiveShape(layer);box=new_item.GetBoundingBox();box.Inflate(mm(.201))
                for i in range(math.floor(pcb.ToMM(box.GetX())/2),math.floor(pcb.ToMM(box.GetRight())/2)+1):
                    for j in range(math.floor(pcb.ToMM(box.GetY())/2),math.floor(pcb.ToMM(box.GetBottom())/2)+1):
                        for other in spatial[i,j,li]:
                            uid=other.m_Uuid.AsString()
                            if uid in removed or other.GetNetname()==net or not ripable(other):continue
                            if shape.Collide(shapes[uid,li],mm(.2)-10):
                                removal_records.append({'uuid':uid,'net':other.GetNetname(),'replaced_for':net,'kind':'via' if isinstance(other,pcb.PCB_VIA) else 'track'})
                                pair_removed.append(uid);removed.add(uid);board.Remove(other);owners.append(other)
        for t in pending:t.SetLocked(True);board.Add(t);created.append(t);index(t)
        records.append({'net':net,'endpoint_uuids':ids,'direct_mm':distance,'vertices_mm_layer_index':compact,'new_vias_mm':new_vias,
                        'removed_unlocked_conflicts':pair_removed,'track_length_mm':sum(math.dist(u,v) for _,u,v in segments),'elapsed_seconds':time.monotonic()-started})
        print(order,'/',len(pairs),net,'candidate added;',len(new_vias),'vias;',round(records[-1]['track_length_mm'],2),'mm',flush=True)
    board.BuildConnectivity();filler=pcb.ZONE_FILLER(board);filler.Fill(board.Zones());assert initial==sha(args.board),'Input changed during routing'
    pcb.SaveBoard(str(args.output),board)
    result={'fabrication_release':False,'input_sha256':initial,'output_sha256':sha(args.output),'drc_source_sha256':sha(args.drc),
            'grid_mm':STEP,'component_endpoints':args.component_endpoints,'signal_width_mm':.2,'signal_via_diameter_mm':args.signal_via_diameter,'signal_via_drill_mm':args.signal_via_drill,
            'added_connections':records,'not_completed':failed,'removed_unlocked_copper':removal_records,
            'note':'Routing candidate only. Locked copper and pads retained. Any permitted narrow unlocked signal/control removals are listed explicitly. Native DRC, schematic parity and force-path/thermal review required.'}
    out=ROOT/'results'/(args.board.stem+'.json'); summary=json.loads(out.read_text(encoding='utf-8'));summary.setdefault('cycles',{}).setdefault(str(cycle['cycle']),{})['single_local_pass']=result;write(out,summary)
    print('Local routing candidate:',len(records),'added;',len(failed),'not completed',flush=True)
    return board,filler,created,shapes,owners

if __name__=='__main__':
    owners=main()
