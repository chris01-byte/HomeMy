"""Read-only final audit of unchanged sources, rules and frozen tap mappings."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys
from bounded_checks import ROOT, sha, write
BASE=ROOT.parent/'rev-a';sys.path.insert(0,str(BASE/'scripts'))
import pcbnew as pcb
from configure_power_rules import POWER_NETS
from sexpr import parse, dump, child, unquote

def signature(t):
    if isinstance(t,pcb.PCB_VIA):return ('via',t.GetNetname(),t.GetPosition().x,t.GetPosition().y,t.GetWidth(pcb.F_Cu),t.GetDrillValue(),tuple(t.IsOnLayer(l) for l in [pcb.F_Cu,pcb.In1_Cu,pcb.In2_Cu,pcb.B_Cu]))
    return ('track',t.GetNetname(),t.GetLayer(),t.GetWidth(),tuple(sorted(((t.GetStart().x,t.GetStart().y),(t.GetEnd().x,t.GetEnd().y)))))

def main(path):
    before=sha(path);board=pcb.LoadBoard(str(path));baselinepath=BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb';baseline=pcb.LoadBoard(str(baselinepath))
    reportpath=ROOT/'results'/(path.stem+'.json');result=json.loads(reportpath.read_text(encoding='utf-8'));errors=[];held=[]
    capturepath=BASE/'evidence/high-current-tap-capture.json';capture=json.loads(capturepath.read_text(encoding='utf-8'))
    original=parse(baselinepath.read_text(encoding='utf-8'))
    expressions={unquote(child(t,'uuid')[1]):t for t in original if isinstance(t,list) and t[0] in ('segment','via')}
    memberships={r['uuid']:name for name,rows in capture['groups'].items() for r in rows}
    for rows in capture['groups'].values():
        for row in rows:
            if row['uuid'] not in expressions or hashlib.sha256(dump(expressions[row['uuid']]).encode()).hexdigest()!=row['sexpr_sha256']:errors.append('Baseline capture geometry mismatch '+row['uuid'])
    sourceitems={t.m_Uuid.AsString():t for t in baseline.GetTracks()};items={t.m_Uuid.AsString():t for t in board.GetTracks()}
    cycle=result['cycles'][str(max(map(int,result['cycles'])))];adopted=cycle['original_tap_inheritance']['adopted'];expected={r['candidate_uuid']:r for r in adopted}
    actual={t.m_Uuid.AsString():g.GetName() for g in board.Groups() if g.GetName().startswith('PWR_') for t in g.GetItems()}
    if set(actual)!=set(expected):errors.append('Candidate tap group roster differs from explicit adoption receipt')
    for uid,record in expected.items():
        if uid not in items:errors.append('Missing inherited tap '+uid);continue
        if actual.get(uid)!=memberships.get(record['baseline_uuid']):errors.append('Invalid tap group membership '+uid)
        source=sourceitems[record['baseline_uuid']];n=source.Duplicate().Cast();held.append(n)
        angle,x,y=record['transform_deg_xy_mm'];n.Rotate(pcb.VECTOR2I(0,0),pcb.EDA_ANGLE(angle,pcb.DEGREES_T));n.Move(pcb.VECTOR2I(pcb.FromMM(x),pcb.FromMM(y)))
        if signature(n)!=signature(items[uid]):errors.append('Inherited tap geometry changed '+uid)
    power_counts=Counter();minima={}
    for t in board.GetTracks():
        net=t.GetNetname()
        if net not in POWER_NETS or t.m_Uuid.AsString() in expected:continue
        if isinstance(t,pcb.PCB_VIA):
            power_counts[net]+=1
            if t.GetWidth(pcb.F_Cu)<pcb.FromMM(.8) or t.GetDrillValue()<pcb.FromMM(.4):errors.append('Undersized power via '+t.m_Uuid.AsString())
        else:
            minimum=6 if net in {'ARM_L_N','ARM_R_N'} else 4
            minima[net]=min(minima.get(net,999),pcb.ToMM(t.GetWidth()))
            if t.GetWidth()<pcb.FromMM(minimum):errors.append('Unapproved thin power track '+t.m_Uuid.AsString())
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() in POWER_NETS and z.GetMinThickness()<pcb.FromMM(1.2):errors.append('Power fill minimum reduced '+z.m_Uuid.AsString())
    sources={}
    project_normalized_identical=False
    for ext in ['.kicad_dru','.kicad_pro','.kicad_sch']:
        same=path.with_suffix(ext).read_bytes()==(BASE/'kicad'/('HomeMy_PMU_RevA'+ext)).read_bytes();sources[ext]=same
        if ext=='.kicad_pro':
            a=json.loads(path.with_suffix(ext).read_text(encoding='utf-8'));b=json.loads((BASE/'kicad'/('HomeMy_PMU_RevA'+ext)).read_text(encoding='utf-8'))
            # Only explicit filename metadata and class-list serialization order
            # are irrelevant; retain each class's actual priority and rules.
            for value in [a,b]:
                value['meta']['filename']='HomeMy_PMU_RevA.kicad_pro'
                value['net_settings']['classes'].sort(key=lambda c:c['name'])
                for sheet in value['schematic'].get('top_level_sheets',[]):
                    if sheet['filename'] in [path.with_suffix('.kicad_sch').name,'HomeMy_PMU_RevA.kicad_sch']:
                        sheet['filename']='HomeMy_PMU_RevA.kicad_sch';sheet['name']='HomeMy_PMU_RevA'
            project_normalized_identical=a==b
            if a!=b:errors.append('Changed project settings beyond renamed project metadata/class serialization order')
        elif not same:errors.append('Changed baseline source '+ext)
    for p in path.parent.glob('*.kicad_sch'):
        if p.name.startswith('HomeMy_PMU_RevA_'):continue
        if p.read_bytes()!=(BASE/'kicad'/p.name).read_bytes():errors.append('Changed child schematic '+p.name)
    stackup=child(child(parse(path.read_text(encoding='utf-8')),'setup'),'stackup')
    originalstackup=child(child(original,'setup'),'stackup')
    if stackup!=originalstackup:errors.append('Stackup differs from baseline')
    if board.GetCopperLayerCount()!=4:errors.append('Copper layer count changed')
    value={'pcb_sha256':before,'baseline_pcb_sha256':sha(baselinepath),'capture_sha256':sha(capturepath),'baseline_source_bytes_identical':sources,'project_settings_normalized_identical':project_normalized_identical,'original_capture_items_verified':len(memberships),'inherited_original_taps_verified':len(expected),'power_via_counts':dict(power_counts),'ungrouped_power_tracks_min_mm':minima,'stackup_identical':stackup==originalstackup,'errors':errors,'passed':not errors,'note':'This validates scope and dimensions, not completed connectivity or thermal capability.'}
    assert before==sha(path);result['invariants']=value;write(reportpath,result)
    print(path.stem,'invariants',len(errors),'errors; tap mappings',len(expected),flush=True)
    for e in errors[:8]:print(e,flush=True)
    return board,baseline,held

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('board',type=Path);a=ap.parse_args();owners=main(a.board.resolve())
