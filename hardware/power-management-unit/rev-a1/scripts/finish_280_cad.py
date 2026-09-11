"""Lead-only CAD operations and read-only reload audit for fixed 280x220 task.

Geometry foundation is exclusively the immutable 275x210 board. Original Rev A
is consulted by the inherited audit for requirement definitions, never as a
replacement geometry source. No rule modification is performed.
"""
import argparse
from collections import Counter
import json
import sys
import pcbnew as pcb
from finish_280 import ROOT,OUT,SOURCE,BOARD,SCRATCH,read,guard,action,sha,write
from bounded_geometry import placement,force,critical,references,xy,point
from bounded_invariants import signature
from configure_power_rules import POWER_NETS
from sexpr import parse,child

def refill(board):
    guard(read());board.BuildConnectivity();filler=pcb.ZONE_FILLER(board);filler.Fill(board.Zones())
    pcb.SaveBoard(str(BOARD),board)
    return filler

def initialize():
    r=read();guard(r);assert not BOARD.exists() and sha(SOURCE)==r['source_sha256']
    board=pcb.LoadBoard(str(SOURCE));changed=[]
    for d in board.GetDrawings():
        if d.GetLayer()!=pcb.Edge_Cuts:continue
        for getter,setter in [(d.GetStart,d.SetStart),(d.GetEnd,d.SetEnd)]:
            x,y=xy(getter());X=280 if abs(x-275)<1e-6 else x;Y=220 if abs(y-210)<1e-6 else y
            setter(point(X,Y));changed.append({'before':[x,y],'after':[X,Y]})
    owners=refill(board)
    action('Outline-only source transfer',{'source_sha256':sha(SOURCE),'output_sha256':sha(BOARD),'edges':changed,
           'footprint_moves':0,'existing_tracks_vias_and_zone_contours_unchanged':True,
           'antenna_note':'Existing full four-layer antenna keepout extends to Y=224.15 mm, beyond new Y=220 edge; no new copper is introduced there.'})
    return board,owners

def invariants(board,source):
    errors=[];current={t.m_Uuid.AsString():t for t in board.GetTracks()};old={t.m_Uuid.AsString():t for t in source.GetTracks()}
    oldgroups={t.m_Uuid.AsString():g.GetName() for g in source.Groups() if g.GetName().startswith('PWR_') for t in g.GetItems()}
    newgroups={t.m_Uuid.AsString():g.GetName() for g in board.Groups() if g.GetName().startswith('PWR_') for t in g.GetItems()}
    if oldgroups!=newgroups:errors.append('Original reviewed power-tap group membership changed')
    for uid in oldgroups:
        if uid not in current or signature(current[uid])!=signature(old[uid]):errors.append('Original reviewed power tap changed: '+uid)
    counts=Counter();minimum={}
    for t in board.GetTracks():
        net=t.GetNetname()
        if net not in POWER_NETS or t.m_Uuid.AsString() in oldgroups:continue
        if isinstance(t,pcb.PCB_VIA):
            counts[net]+=1
            if t.GetWidth(pcb.F_Cu)<pcb.FromMM(.8) or t.GetDrillValue()<pcb.FromMM(.4):errors.append('Undersized power via '+t.m_Uuid.AsString())
        else:
            minimum[net]=min(minimum.get(net,999),pcb.ToMM(t.GetWidth()))
            if t.GetWidth()<pcb.FromMM(6 if net in ['ARM_L_N','ARM_R_N'] else 4):errors.append('Unapproved narrow power track '+t.m_Uuid.AsString())
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() in POWER_NETS and z.GetMinThickness()<pcb.FromMM(1.2):errors.append('Power fill minimum weakened')
    for ext in ['.kicad_sch','.kicad_dru']:
        if BOARD.with_suffix(ext).read_bytes()!=SOURCE.with_suffix(ext).read_bytes():errors.append('Changed source '+ext)
    pro=[]
    for p in [BOARD,SOURCE]:
        v=json.loads(p.with_suffix('.kicad_pro').read_text(encoding='utf-8'));v['meta']['filename']='project.kicad_pro'
        for s in v['schematic'].get('top_level_sheets',[]):
            if s['filename']==p.with_suffix('.kicad_sch').name:s['filename']='project.kicad_sch';s['name']='project'
        pro.append(v)
    if pro[0]!=pro[1]:errors.append('Project rules/settings differ from source')
    trees=[parse(p.read_text(encoding='utf-8')) for p in [BOARD,SOURCE]]
    same=child(child(trees[0],'setup'),'stackup')==child(child(trees[1],'setup'),'stackup')
    if not same or board.GetCopperLayerCount()!=4:errors.append('Stackup changed')
    if sha(SOURCE)!=read()['source_sha256']:errors.append('275 source bytes changed')
    return {'passed':not errors,'errors':errors,'unchanged_original_taps':len(oldgroups),'stackup_identical':same,'power_vias':dict(counts),'minimum_ungrouped_power_tracks_mm':minimum}

def audit(label):
    guard(read());digest=sha(BOARD);board=pcb.LoadBoard(str(BOARD));source=pcb.LoadBoard(str(SOURCE))
    board.BuildConnectivity();board.GetConnectivity().RecalculateRatsnest()
    old=json.loads((ROOT/'results/HomeMy_PMU_RevA_275x210.json').read_text(encoding='utf-8'))
    edgepts=[xy(p) for d in board.GetDrawings() if d.GetLayer()==pcb.Edge_Cuts for p in [d.GetStart(),d.GetEnd()]]
    size=[round(max(p[i] for p in edgepts)-min(p[i] for p in edgepts),6) for i in [0,1]]
    value={'pcb_sha256':digest,'audit_after_native_reload':True,'outline_exact_mm':size,
           'outline_note':'Physical Edge.Cuts centerlines, excluding the 0.05-mm drawing stroke included in KiCad display bounding box.',
           'native_ratsnest_connections':board.GetConnectivity().GetUnconnectedCount(False),
           'placement':placement(board,source),'invariants':invariants(board,source),
           'force':force(board),'critical':critical(board),'reference_stitches':references(board,{'cycles':{'1':{'critical_reference_seed':{'reference_stitches':[
               {'pad':r['pad'],'net':r['net'],'via_xy_mm':r['via_xy_mm']} for r in old['geometry']['reference_stitches']['unproven_stitches']
           ]}}}})}
    assert sha(BOARD)==digest
    write(OUT/(label+'-geometry.json'),value)
    print('AUDIT',label,'size',size,'opens',value['native_ratsnest_connections'],'placement',value['placement']['passed'],
          'invariants',value['invariants']['passed'],'force',value['force']['passed_pairs'],'critical',value['critical']['passed'],flush=True)
    return board,source

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['init','audit','refill']);p.add_argument('label',nargs='?',default='cycle-01');a=p.parse_args()
    if a.mode=='init':owners=initialize()
    elif a.mode=='audit':owners=audit(a.label)
    else:
        b=pcb.LoadBoard(str(BOARD));owners=(b,refill(b))
