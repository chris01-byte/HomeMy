"""Exact original short paths with common endpoint transforms; bounded list."""
from rebuild import *
import sys,math
sys.path.insert(0,str(BASE.parent/'rev-a1/scripts'))
from finish_280_routes import Controlled
from bounded_seed import Screen
from bounded_invariants import signature
from review_critical_routing import graph_for,shortest
import pcbnew as pcb
HOLD=[]
def p(x,y):return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
def xy(v):return [pcb.ToMM(v.x),pcb.ToMM(v.y)]
def main():
    guard();b=pcb.LoadBoard(str(BOARD));s=pcb.LoadBoard(str(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'))
    c=Controlled(b);fps={f.GetReference():f for f in b.GetFootprints()};old={f.GetReference():f for f in s.GetFootprints()}
    oldpads={f.GetReference()+'.'+v.GetNumber():v for f in s.GetFootprints() for v in f.Pads()};tracks=list(s.GetTracks());records=[]
    capture=json.loads((BASE/'evidence/high-current-tap-capture.json').read_text(encoding='utf-8'));membership={r['uuid']:g for g,rows in capture['groups'].items() for r in rows}
    receipt=json.loads((OUT/'local-copper-provenance.json').read_text(encoding='utf-8'));existing={t.m_Uuid.AsString():t for t in b.GetTracks()}
    def transform(ref):
        a=(fps[ref].GetOrientationDegrees()-old[ref].GetOrientationDegrees())%360;c0,s0=math.cos(math.radians(a)),math.sin(math.radians(a));x,y=xy(old[ref].GetPosition());X,Y=xy(fps[ref].GetPosition())
        return [round(a,6),round(X-c0*x-s0*y,6),round(Y+s0*x-c0*y,6)]
    for A,B in [('C4.2','U1.19'),('C11.2','U2.17'),('U2.13','C9.2'),('U2.13','C29.2'),('C206.1','U11.6')]:
        net=oldpads[A].GetNetname();tr=transform(A.split('.')[0]);assert tr==transform(B.split('.')[0])
        path=shortest(graph_for(net,tracks,oldpads),A,B);assert path['path_found']
        vs=[v if isinstance(v,str) else (pcb.FromMM(v['x_mm']),pcb.FromMM(v['y_mm']),s.GetLayerID(v['layer'])) for v in path['vertices']];needed={}
        for v,w in zip(vs,vs[1:]):
            if isinstance(v,str) or isinstance(w,str):continue
            for t in tracks:
                if t.GetNetname()!=net:continue
                if v[2]!=w[2]:hit=isinstance(t,pcb.PCB_VIA) and t.GetPosition().x==v[0] and t.GetPosition().y==v[1]
                else:hit=not isinstance(t,pcb.PCB_VIA) and t.GetLayer()==v[2] and t.GetEffectiveShape(v[2]).Collide(pcb.VECTOR2I(v[0],v[1]),0) and t.GetEffectiveShape(v[2]).Collide(pcb.VECTOR2I(w[0],w[1]),0)
                if hit:needed[t.m_Uuid.AsString()]=t
        proposed=[];blocked=[]
        for uid,t in needed.items():
            n=t.Duplicate().Cast();n.SetUuid(pcb.KIID(uid));n.SetParentGroup(None);n.Rotate(p(0,0),pcb.EDA_ANGLE(tr[0],pcb.DEGREES_T));n.Move(p(tr[1],tr[2]));n.SetNet(b.FindNet(net));n.SetLocked(True);HOLD.append(n)
            if uid in existing:
                if signature(existing[uid])!=signature(n):blocked.append({'uuid':uid,'reason':'Different source transform already exists'})
                continue
            if c.screen.reason(n):blocked.append({'uuid':uid,'obstacles':c.obstacles(n)})
            proposed.append((uid,n,t))
        if not blocked:
            groups={g.GetName():g for g in b.Groups()}
            for uid,n,t in proposed:
                b.Add(n);c.screen.index(n);existing[uid]=n
                if uid in membership:
                    name=membership[uid]
                    if name not in groups:g=pcb.PCB_GROUP(b);g.SetName(name);b.Add(g);groups[name]=g
                    groups[name].AddItem(n);receipt['tap_adopted'].append({'uuid':uid,'anchor':A,'additional_anchor':B,'group':name,'transform':tr,'source_signature':signature(t),'target_signature':signature(n)})
                    receipt['tap_retired'].remove(uid)
        records.append({'from':A,'to':B,'net':net,'transform':tr,'source_path_length_mm':path.get('centerline_with_pad_leads_mm'),'added':[] if blocked else [uid for uid,n,t in proposed],'blocked':blocked})
        print(A,B,'blocked' if blocked else 'adopted',len(proposed),flush=True)
    # One corrected high-driver escape, independently screened.
    c.route('Chopper high-drive corrected escape','CHOP_DRIVE_H',[(['U33.2',(227,49),(227,46),(228.5875,46),'R319.1'],.2,pcb.F_Cu)])
    b.BuildConnectivity();f=pcb.ZONE_FILLER(b);f.Fill(b.Zones());pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'local-copper-provenance.json',receipt);write(OUT/'cycle-03-critical-local.json',{'paths':records,'other_recipes':c.records,'pcb_sha256':sha(BOARD)})
    return b,s,c,f
if __name__=='__main__':owners=main()
