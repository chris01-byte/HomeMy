"""Replay reviewed local completion repairs on the frozen routing002 candidate.

The API modifies only the loaded board. The CLI writes a separate test copy.
Native DRC, zone fill, final netlist parity and manufacturing regeneration remain
required. Nothing changes source electrical nets or component placements.
"""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import shutil
import traceback
import pcbnew as pcb
from build_board import force_exit

ROOT=Path(__file__).resolve().parents[1]
_DETACHED=[]


def xy(p):return [round(pcb.ToMM(p.x),6),round(pcb.ToMM(p.y),6)]
def point(p):return pcb.VECTOR2I(pcb.FromMM(p[0]),pcb.FromMM(p[1]))
def key(net,layer,a,b,width):return (net,layer,tuple(sorted((tuple(round(v,5) for v in a),tuple(round(v,5) for v in b)))),round(width,5))


def apply_final_routing_repairs(board,plan_path=None):
    plan_path=Path(plan_path or ROOT/'design/FINAL_ROUTING_REPAIRS.json')
    plan=json.loads(plan_path.read_text(encoding='utf-8'))
    protected={t.m_Uuid.AsString() for t in board.GetTracks() if t.IsLocked()}
    lookup=collections.defaultdict(list)
    for t in board.GetTracks():
        if isinstance(t,pcb.PCB_VIA):continue
        lookup[key(t.GetNetname(),pcb.LayerName(t.GetLayer()),xy(t.GetStart()),xy(t.GetEnd()),pcb.ToMM(t.GetWidth()))].append(t)
    required=collections.Counter(key(r['net'],r['layer'],r['start_mm'],r['end_mm'],r['width_mm']) for r in plan['remove_unlocked_segments'])
    for k,n in required.items():
        if len(lookup[k])!=n or any(t.IsLocked() for t in lookup[k]):
            raise ValueError('Candidate geometry/lock differs from the reviewed frozen import: '+str(k))
    for k in required:
        for t in lookup[k]:board.Remove(t);_DETACHED.append(t)
    layer={'F.Cu':pcb.F_Cu,'In1.Cu':pcb.In1_Cu,'In2.Cu':pcb.In2_Cu,'B.Cu':pcb.B_Cu}
    added=[]
    for r in plan['tracks']:
        for a,b in zip(r['points'],r['points'][1:]):
            t=pcb.PCB_TRACK(board);t.SetStart(point(a));t.SetEnd(point(b));t.SetLayer(layer[r['layer']])
            t.SetWidth(pcb.FromMM(r['width_mm']));t.SetNet(board.FindNet(r['net']));t.SetLocked(True);board.Add(t)
            added.append(t.m_Uuid.AsString())
    for r in plan['vias']:
        v=pcb.PCB_VIA(board);v.SetPosition(point(r['position_mm']));v.SetLayerPair(pcb.F_Cu,pcb.B_Cu)
        v.SetWidth(pcb.FromMM(r['diameter_mm']));v.SetDrill(pcb.FromMM(r['drill_mm']));v.SetNet(board.FindNet(r['net']));v.SetLocked(True);board.Add(v)
        added.append(v.m_Uuid.AsString())
    after={t.m_Uuid.AsString() for t in board.GetTracks() if t.IsLocked()}
    if not protected.issubset(after):raise AssertionError('Pre-existing locked copper was removed')
    return dict(metadata=dict(rev_a_engineering_prototype=True,rev_b_production=False,state='completion_candidate_requires_native_drc',api_saved_board=False),
                plan_sha256=hashlib.sha256(plan_path.read_bytes()).hexdigest(),preserved_locked_items=len(protected),
                removed_unlocked_segments=sum(required.values()),added_locked_items=len(added),added_uuids=added)


def main():
    ap=argparse.ArgumentParser();ap.add_argument('--board',type=Path,required=True);ap.add_argument('--output-dir',type=Path,required=True);a=ap.parse_args()
    source=a.board.resolve();out=a.output_dir.resolve()
    if out==source.parent or out==ROOT/'kicad':raise ValueError('CLI only writes a separate test directory')
    out.mkdir(parents=True,exist_ok=True)
    board=pcb.LoadBoard(str(source));initial=hashlib.sha256(source.read_bytes()).hexdigest()
    result=apply_final_routing_repairs(board)
    board.BuildConnectivity();filler=pcb.ZONE_FILLER(board);filler.Fill(board.Zones())
    target=out/source.name;pcb.SaveBoard(str(target),board)
    for name in [source.with_suffix('.kicad_pro').name,source.with_suffix('.kicad_dru').name,'fp-lib-table']:
        if (source.parent/name).exists():shutil.copy2(source.parent/name,out/name)
    if initial!=hashlib.sha256(source.read_bytes()).hexdigest():raise ValueError('Input changed')
    result.update(input_sha256=initial,temporary_board=str(target),temporary_board_sha256=hashlib.sha256(target.read_bytes()).hexdigest())
    (out/'repair-manifest.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result),flush=True)
    return board,filler


if __name__=='__main__':
    try:owners=main()
    except BaseException:traceback.print_exc();force_exit(1)
    force_exit(0)
