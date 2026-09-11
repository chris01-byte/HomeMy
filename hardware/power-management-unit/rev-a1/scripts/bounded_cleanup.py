"""Single bounded pruning of unlocked dangling fragments, followed by refill."""
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT.parent / "rev-a/scripts"))
import pcbnew as pcb
from configure_power_rules import POWER_NETS
from bounded_checks import LEDGER, minutes, sha, write


def main(path):
    ledger = json.loads(LEDGER.read_text(encoding="utf-8")); cycle = ledger["cycles"][-1]
    assert cycle["status"] == "in_progress" and not cycle.get("fragment_cleanup") and minutes(ledger) < 140
    cycle["fragment_cleanup"] = "One fixed 12-pass maximum dead-end pruning operation"; write(LEDGER, ledger)
    board = pcb.LoadBoard(str(path)); before = sha(path); items = list(board.GetTracks())+[p for f in board.GetFootprints() for p in f.Pads()]
    spatial = defaultdict(list); shapes = {}; removed = set(); owners = []; records = []
    layers = [pcb.F_Cu, pcb.In1_Cu, pcb.In2_Cu, pcb.B_Cu]
    for t in items:
        b=t.GetBoundingBox()
        for l in layers:
            if not t.IsOnLayer(l): continue
            shapes[id(t),l]=t.GetEffectiveShape(l)
            for i in range(math.floor(pcb.ToMM(b.GetX())/3),math.floor(pcb.ToMM(b.GetRight())/3)+1):
                for j in range(math.floor(pcb.ToMM(b.GetY())/3),math.floor(pcb.ToMM(b.GetBottom())/3)+1):spatial[i,j,l].append(t)
    def connected(t,p):
        l=t.GetLayer();x,y=pcb.ToMM(p.x),pcb.ToMM(p.y)
        for i in range(math.floor((x-.5)/3),math.floor((x+.5)/3)+1):
            for j in range(math.floor((y-.5)/3),math.floor((y+.5)/3)+1):
                for other in spatial[i,j,l]:
                    if id(other)!=id(t) and id(other) not in removed and other.GetNetname()==t.GetNetname() and shapes[id(other),l].Collide(p,1):return True
        return any(not z.GetIsRuleArea() and z.GetNetname()==t.GetNetname() and z.GetLayerSet().Contains(l) and z.GetFilledPolysList(l).Contains(p,-1,0,True) for z in board.Zones())
    for sweep in range(12):
        found=[]
        for t in items:
            if isinstance(t,(pcb.PAD,pcb.PCB_VIA)) or id(t) in removed or t.IsLocked() or t.GetParentGroup() or t.GetNetname() in POWER_NETS:continue
            if not connected(t,t.GetStart()) or not connected(t,t.GetEnd()):found.append(t)
        if not found:break
        for t in found:
            records.append({"uuid":t.m_Uuid.AsString(),"net":t.GetNetname(),"sweep":sweep+1});removed.add(id(t));board.Remove(t);owners.append(t)
    board.BuildConnectivity();filler=pcb.ZONE_FILLER(board);filler.Fill(board.Zones());pcb.SaveBoard(str(path),board)
    out=ROOT/'results'/(path.stem+'.json');result=json.loads(out.read_text(encoding='utf-8'))
    result.setdefault('cycles',{}).setdefault(str(cycle['cycle']),{})['fragment_cleanup']={'input_sha256':before,'output_sha256':sha(path),'removed':records,'max_sweeps':12}
    write(out,result);print('Pruned',len(records),'unlocked fragments; protected copper retained.',flush=True)
    return board,filler,owners,shapes

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('board',type=Path);args=ap.parse_args();owners=main(args.board.resolve())
