"""Single explicit power stage for the final permitted size.

Keep 6/8 mm load-return spines from later signal cuts. Rebuild bounded lower
power routes at the documented Rev-A load envelopes. Never remove foreign
power vias or add exemptions when a corridor collides with existing copper.
"""
import argparse
import json
import math
from pathlib import Path
from bounded_checks import ROOT, LEDGER, minutes, sha, write
from bounded_seed import Screen, point, xy, pcb, BASE, load_wip
from bounded_enlarge import corridor
from cad_operations import zone,rect,merge_zones

def main(path):
    ledger=json.loads(LEDGER.read_text(encoding='utf-8'));cycle=ledger['cycles'][-1]
    assert cycle['size']=='300x220' and cycle['status']=='in_progress' and not cycle.get('explicit_final_power_stage') and minutes(ledger)<140 and not ledger.get('stop_required')
    cycle['explicit_final_power_stage']=1;write(LEDGER,ledger)
    board=pcb.LoadBoard(str(path));before=sha(path);screen=Screen(board);owners=[];records=[]
    fps={f.GetReference():f for f in board.GetFootprints()};pads={f.GetReference()+'.'+p.GetNumber():p for f in fps.values() for p in f.Pads()};dy=20;dx=50
    def loc(p):return xy(pads[p].GetPosition()) if isinstance(p,str) else p
    def line(net,a,b,width,l):
        t=pcb.PCB_TRACK(board);t.SetNet(board.FindNet(net));t.SetStart(point(*loc(a)));t.SetEnd(point(*loc(b)));t.SetLayer(l);t.SetWidth(pcb.FromMM(width));t.SetLocked(True);owners.append(t);return t
    def route(net,parts,label):
        proposed=[line(net,a,b,w,l) for pts,w,l in parts for a,b in zip(pts,pts[1:]) if math.dist(loc(a),loc(b))>1e-6]
        blockers=[{'uuid':t.m_Uuid.AsString(),'reason':screen.reason(t)} for t in proposed if screen.reason(t)]
        if blockers:records.append({'label':label,'net':net,'adopted':False,'blockers':blockers});return False
        for t in proposed:board.Add(t);screen.index(t)
        for pts,w,l in parts:corridor(board,net,[loc(p) for p in pts],w+.2,l,20)
        records.append({'label':label,'net':net,'adopted':True,'tracks':len(proposed),'parts':[{'points_mm':[loc(p) for p in pts],'width_mm':w,'layer':board.GetLayerName(l)} for pts,w,l in parts]});return True
    route('LIFT_N',[( ['J8.2',(235+dx,170.92+dy)],6,l) for l in [pcb.In1_Cu,pcb.In2_Cu]]+[( [(235+dx,170.92+dy),(232+dx,170.92+dy),(232+dx,149+dy),(159,149+dy),'NT4.1'],8,l) for l in [pcb.In1_Cu,pcb.In2_Cu]],'Protected lift return on both inner layers')
    route('DRIVE_N',[(['J7.2',(235+dx,144+dy),(231+dx,153+dy)],6,pcb.B_Cu), ([(231+dx,153+dy),(135,153+dy),'NT3.1'],8,pcb.B_Cu)],'Protected drive return')
    route('SYS_BUS_P',[([(105,84),(110,89),(110,158+dy)],4,pcb.F_Cu)],'Four-ampere combined eFuse feed at unchanged >=4mm rule')
    route('PC_N',[(['NT5.1',(17,140),(17,160.08+dy),'J9.2'],4,pcb.F_Cu)],'PC converter return')
    route('LOGIC_BUCK_N',[(['NT6.1',(43,136),(43,169+dy),(17,169+dy),(17,187.08+dy),'J10.2'],4,pcb.F_Cu)],'Logic converter return')
    # Same-net rigid translation for the two original converter output feeds.
    # Explicit source power copper only; no automatic signal paths are carried.
    source=load_wip('reports/routing-round-003/HomeMy_PMU_RevA.kicad_pcb');old={f.GetReference():f for f in source.GetFootprints()}
    for net in ['PC_BUCK_IN_P','LOGIC_BUCK_IN_P']:
        refs={f.GetReference() for f in source.GetFootprints() if any(p.GetNetname()==net for p in f.Pads())}
        rigid=all(abs(fps[r].GetOrientationDegrees()-old[r].GetOrientationDegrees())<1e-6 and math.dist(xy(fps[r].GetPosition()),[xy(old[r].GetPosition())[0],xy(old[r].GetPosition())[1]+dy])<1e-5 for r in refs)
        if not rigid:records.append({'net':net,'adopted':False,'reason':'Output feed pad owners do not share the proposed rigid translation'});continue
        proposed=[]
        for t in source.GetTracks():
            if t.GetNetname()!=net or not t.IsLocked():continue
            n=t.Duplicate().Cast();n.SetParentGroup(None);n.SetUuid(pcb.KIID(t.m_Uuid.AsString()));n.Move(point(0,dy));n.SetNet(board.FindNet(net));n.SetLocked(True);proposed.append(n);owners.append(n)
        blockers=[screen.reason(t) for t in proposed if screen.reason(t)]
        if blockers:records.append({'net':net,'adopted':False,'reason':blockers});continue
        for t in proposed:board.Add(t);screen.index(t)
        nz=0
        for z in source.Zones():
            if z.GetIsRuleArea() or z.GetNetname()!=net:continue
            n=pcb.Cast_to_ZONE(z.Duplicate(False));n.SetParentGroup(None);n.Move(point(0,dy));n.SetNet(board.FindNet(net));board.Add(n);owners.append(n);nz+=1
        records.append({'net':net,'adopted':True,'source':'WIP52 locked dedicated output copper and filled-corridor definitions','translation_mm':[0,dy],'tracks_vias':len(proposed),'zones':nz})
    # Output connector and LED return rails keep their 70um outer layer.
    route('LOGIC_5V_N',[(['J11.2',(48.08,196+dy)],3,pcb.B_Cu), ([(48.08,196+dy),(142.5,196+dy),(142.5,165+dy),(75,165+dy)],6,pcb.B_Cu)],'5V output return distribution')
    route('LOGIC_5V_N',[(['J18.3',(120.16,196+dy)],3,pcb.B_Cu),(['C246.2',(135,196+dy)],3,pcb.B_Cu)],'Short LED/capacitor return pickups')
    route('V5V',[(['J11.1',(43,181.5+dy)],3,pcb.B_Cu), ([(43,181.5+dy),(135,181.5+dy),'C246.1'],6,pcb.B_Cu), ([(110,181.5+dy),'J18.1'],3,pcb.B_Cu)],'5V five-ampere output rail and short connector pickups')
    # No narrow SYS fanouts or new power-control exemptions are synthesized.
    for z in board.Zones():
        if z.GetNetname()=='SYS_BUS_P':z.SetMinThickness(pcb.FromMM(1.2))
    merge_zones(board);board.BuildConnectivity();filler=pcb.ZONE_FILLER(board);filler.Fill(board.Zones());pcb.SaveBoard(str(path),board)
    out=ROOT/'results'/(path.stem+'.json');r=json.loads(out.read_text(encoding='utf-8'));r['cycles'][str(cycle['cycle'])]['explicit_power_stage']={'input_sha256':before,'output_sha256':sha(path),'recipes':records,'note':'A rejected corridor stays open. No foreign power via removal, geometry exception or power class relaxation.'};write(out,r)
    print('Explicit power stage',sum(x['adopted'] for x in records),'adopted recipes,',sum(not x['adopted'] for x in records),'rejected',flush=True)
    return board,source,filler,screen,owners

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('board',type=Path);a=ap.parse_args();owners=main(a.board.resolve())
