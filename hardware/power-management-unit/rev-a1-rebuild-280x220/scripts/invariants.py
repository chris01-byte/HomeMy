"""Read-only, input-bound original-rule and exact adopted-tap verification."""
from rebuild import *
from collections import Counter,defaultdict
import sys,math
sys.path.insert(0,str(BASE.parent/'rev-a1/scripts'))
from bounded_invariants import signature
from sexpr import parse,dump,child,unquote
from configure_power_rules import POWER_NETS
import pcbnew as pcb
LAYERS=[pcb.F_Cu,pcb.In1_Cu,pcb.In2_Cu,pcb.B_Cu]

def main(label):
    before=sha(BOARD);receipt_path=OUT/'local-copper-provenance.json';receipt_sha=sha(receipt_path)
    b=pcb.LoadBoard(str(BOARD));source=pcb.LoadBoard(str(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'))
    capturepath=BASE/'evidence/high-current-tap-capture.json';capture=json.loads(capturepath.read_text(encoding='utf-8'))
    receipt=json.loads(receipt_path.read_text(encoding='utf-8'));errors=[];held=[]
    src=parse((BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb').read_text(encoding='utf-8'));dst=parse(BOARD.read_text(encoding='utf-8'))
    expressions={unquote(child(t,'uuid')[1]):t for t in src if isinstance(t,list) and t[0] in ('segment','via')}
    memberships={r['uuid']:g for g,rows in capture['groups'].items() for r in rows}
    adopted=receipt['tap_adopted'];retired=receipt['tap_retired'];adopted_ids=[r['uuid'] for r in adopted]
    if len(adopted_ids)!=len(set(adopted_ids)) or len(retired)!=len(set(retired)):errors.append('Duplicate disposition')
    if set(adopted_ids)&set(retired) or set(adopted_ids)|set(retired)!=set(memberships):errors.append('Disposition is not an exact disjoint partition of original capture')
    for rows in capture['groups'].values():
        for row in rows:
            if hashlib.sha256(dump(expressions[row['uuid']]).encode()).hexdigest()!=row['sexpr_sha256']:errors.append('Source capture mismatch '+row['uuid'])
    old={t.m_Uuid.AsString():t for t in source.GetTracks()};actual={t.m_Uuid.AsString():t for t in b.GetTracks()}
    grouped={t.m_Uuid.AsString():g.GetName() for g in b.Groups() if g.GetName().startswith('PWR_') for t in g.GetItems()}
    if set(grouped)!=set(adopted_ids):errors.append('Actual power-group roster differs from adopted roster')
    if set(retired)&set(actual):errors.append('Retired item still present')
    fps={f.GetReference():f for f in b.GetFootprints()};oldfps={f.GetReference():f for f in source.GetFootprints()}
    pads={f.GetReference()+'.'+p.GetNumber():p for f in b.GetFootprints() for p in f.Pads()}
    by_transform=defaultdict(list)
    def vec(x,y):return pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y))
    for row in adopted:
        uid=row['uuid'];a,x,y=row['transform'];by_transform[tuple(row['transform'])].append(row)
        if uid not in actual:errors.append('Missing adopted '+uid);continue
        if grouped.get(uid)!=memberships[uid] or row['group']!=memberships[uid]:errors.append('Wrong group '+uid)
        n=old[uid].Duplicate().Cast();held.append(n);n.Rotate(vec(0,0),pcb.EDA_ANGLE(a,pcb.DEGREES_T));n.Move(vec(x,y))
        if signature(n)!=signature(actual[uid]):errors.append('Changed rigid geometry '+uid)
        if isinstance(n,pcb.PCB_VIA) and (n.GetViaType()!=actual[uid].GetViaType() or any(n.GetWidth(l)!=actual[uid].GetWidth(l) for l in LAYERS)):errors.append('Changed via type/layer geometry '+uid)
        for anchor in [row['anchor']]+([row['additional_anchor']] if row.get('additional_anchor') else []):
            ref=anchor.split('.')[0];q=oldfps[ref].GetPosition();c,s=math.cos(math.radians(a)),math.sin(math.radians(a))
            target=vec(c*pcb.ToMM(q.x)+s*pcb.ToMM(q.y)+x,-s*pcb.ToMM(q.x)+c*pcb.ToMM(q.y)+y)
            if abs(target.x-fps[ref].GetPosition().x)>2 or abs(target.y-fps[ref].GetPosition().y)>2 or abs((fps[ref].GetOrientationDegrees()-oldfps[ref].GetOrientationDegrees()-a+180)%360-180)>1e-6:errors.append('Pad owner transform mismatch '+anchor)
    # Reach each stated pad anchor through only same-transform adopted native
    # shapes. No filled plane or unrelated copper may rescue a detached stub.
    components=0
    for tr,rows in by_transform.items():
        pool={r['uuid']:actual[r['uuid']] for r in rows if r['uuid'] in actual};pending=set(pool)
        shapes={(u,l):t.GetEffectiveShape(l) for u,t in pool.items() for l in LAYERS if t.IsOnLayer(l)}
        def touches(t,u):return t.GetNetname()==u.GetNetname() and any(t.IsOnLayer(l) and u.IsOnLayer(l) and t.GetEffectiveShape(l).Collide(u.GetEffectiveShape(l),0) for l in LAYERS)
        while pending:
            seed=pending.pop();comp={seed};todo=[seed]
            while todo:
                u=todo.pop();near=[v for v in pending if touches(pool[u],pool[v])]
                for v in near:pending.remove(v);comp.add(v);todo.append(v)
            components+=1
            for row in rows:
                if row['uuid'] in comp and not any(touches(pool[u],pads[row['anchor']]) for u in comp):errors.append('No same-transform copper path to anchor '+row['uuid']+' '+row['anchor'])
    power_vias=Counter()
    for uid,t in actual.items():
        if t.GetNetname() not in POWER_NETS or uid in set(adopted_ids):continue
        if isinstance(t,pcb.PCB_VIA):
            power_vias[t.GetNetname()]+=1
            if t.GetWidth(pcb.F_Cu)<pcb.FromMM(.8) or t.GetDrillValue()<pcb.FromMM(.4):errors.append('New undersized power via '+uid)
        elif t.GetWidth()<pcb.FromMM(6 if t.GetNetname() in ['ARM_L_N','ARM_R_N'] else 4):errors.append('New undersized power track '+uid)
    for z in b.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() in POWER_NETS and z.GetMinThickness()<pcb.FromMM(1.2):errors.append('Reduced power fill minimum')
    project_ok=normalize_project(json.loads(BOARD.with_suffix('.kicad_pro').read_text(encoding='utf-8')))==normalize_project(json.loads((BASE/'kicad/HomeMy_PMU_RevA.kicad_pro').read_text(encoding='utf-8')))
    if not project_ok:errors.append('Changed numerical project settings')
    if BOARD.with_suffix('.kicad_dru').read_bytes()!=(BASE/'kicad/HomeMy_PMU_RevA.kicad_dru').read_bytes():errors.append('Changed original rules')
    for p in CAD.glob('*.kicad_sch'):
        q=BASE/'kicad'/('HomeMy_PMU_RevA.kicad_sch' if p.stem==NAME else p.name)
        if p.read_bytes()!=q.read_bytes():errors.append('Changed schematic '+p.name)
    stackup_ok=child(child(src,'setup'),'stackup')==child(child(dst,'setup'),'stackup') and b.GetCopperLayerCount()==4
    if not stackup_ok:errors.append('Changed stackup')
    assert before==sha(BOARD) and receipt_sha==sha(receipt_path)
    write(OUT/(label+'-invariants.json'),{'pcb_sha256':before,'receipt_sha256':receipt_sha,'capture_sha256':sha(capturepath),'original_items':len(memberships),'adopted':len(adopted),'retired':len(retired),'same_transform_components':components,'new_power_via_counts':dict(power_vias),'project_settings_identical':project_ok,'stackup_identical':stackup_ok,'errors':errors,'passed':not errors,'limitations':'Geometric provenance and frozen rules; no electrical or thermal qualification.'})
    print('Invariants',len(errors),'errors',len(adopted),'adopted',len(retired),'retired',flush=True)
    for e in errors[:10]:print(e,flush=True)
    return b,source,held
if __name__=='__main__':owners=main(sys.argv[1])
