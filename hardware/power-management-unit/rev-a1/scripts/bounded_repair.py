"""One explicit copper-preparation stage, never a repeated repair loop.

Reject inherited width-based exemption expansion. Only original Rev-A copper
elements that admit a pad-anchored rigid transform and clear native obstacles
can regain their original exception membership. No new thin power routes.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT.parent / "rev-a"
sys.path.insert(0, str(BASE / "scripts"))
import pcbnew as pcb
from configure_power_rules import POWER_NETS
from bounded_checks import write, sha, minutes, LEDGER

LAYERS = [pcb.F_Cu, pcb.In1_Cu, pcb.In2_Cu, pcb.B_Cu]
def xy(p): return (pcb.ToMM(p.x), pcb.ToMM(p.y))
def point(x, y): return pcb.VECTOR2I(pcb.FromMM(x), pcb.FromMM(y))


def inherit_taps(board, baseline):
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    oldfps = {f.GetReference(): f for f in baseline.GetFootprints()}
    capture = json.loads((BASE / "evidence/high-current-tap-capture.json").read_text(encoding="utf-8"))
    memberships = {r["uuid"]: name for name, rows in capture["groups"].items() for r in rows}
    old_items = [t for t in baseline.GetTracks() if t.m_Uuid.AsString() in memberships]
    pads = [p for f in oldfps.values() for p in f.Pads() if p.GetNetname() in POWER_NETS]
    shapes = {(id(t), l): t.GetEffectiveShape(l) for t in old_items+pads for l in LAYERS if t.IsOnLayer(l)}
    def touch(a, b):
        return a.GetNetname() == b.GetNetname() and a.GetBoundingBox().Intersects(b.GetBoundingBox()) and any(
            a.IsOnLayer(l) and b.IsOnLayer(l) and shapes[id(a), l].Collide(shapes[id(b), l], 1) for l in LAYERS)
    parent = list(range(len(old_items)))
    def root(i):
        while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
        return i
    for i, t in enumerate(old_items):
        for j in range(i):
            if touch(t, old_items[j]): parent[root(i)] = root(j)
    components = defaultdict(list)
    for i, t in enumerate(old_items): components[root(i)].append(t)
    def transform(ref):
        src, dst = oldfps[ref], fps[ref]
        a = (dst.GetOrientationDegrees()-src.GetOrientationDegrees()) % 360
        c, s = math.cos(math.radians(a)), math.sin(math.radians(a))
        x, y = xy(src.GetPosition()); X, Y = xy(dst.GetPosition())
        return (round(a, 6), round(X-c*x-s*y, 6), round(Y+s*x-c*y, 6))
    proposals = []
    skipped = []
    for members in components.values():
        refs = {p.GetParentFootprint().GetReference() for t in members for p in pads if touch(t, p)}
        transforms = {transform(r) for r in refs}
        # SYS branch exceptions are handled separately with explicit IC ownership.
        members = [t for t in members if memberships[t.m_Uuid.AsString()] == "PWR_TAP_CONTROL"]
        if not members: continue
        if len(transforms) != 1:
            skipped.append({"net": members[0].GetNetname(), "items": len(members), "anchors": sorted(refs), "reason": "No unique rigid transform of all pad anchors"})
        else: proposals.append((members, next(iter(transforms)), sorted(refs)))
    for ref in ("U3", "U4"):
        members = []
        for t in old_items:
            if memberships[t.m_Uuid.AsString()] == "PWR_TAP_CONTROL": continue
            pos = xy(t.GetPosition())
            owner = min(("U3", "U4"), key=lambda r: math.dist(pos, xy(oldfps[r].GetPosition())))
            if owner == ref: members.append(t)
        assert len(members) == 6, "Original eFuse exception roster changed"
        proposals.append((members, transform(ref), [ref]))
    obstacles = [p for f in fps.values() for p in f.Pads()] + list(board.GetTracks())
    spatial = defaultdict(list); obstacle_shapes = {}
    def index(t):
        box = t.GetBoundingBox()
        for l in LAYERS:
            if not t.IsOnLayer(l): continue
            obstacle_shapes[id(t), l] = t.GetEffectiveShape(l)
            for i in range(math.floor(pcb.ToMM(box.GetX())/3), math.floor(pcb.ToMM(box.GetRight())/3)+1):
                for j in range(math.floor(pcb.ToMM(box.GetY())/3), math.floor(pcb.ToMM(box.GetBottom())/3)+1): spatial[i,j,l].append(t)
    for t in obstacles: index(t)
    rule_areas = [z for f in fps.values() for z in f.Zones() if z.GetIsRuleArea()] + [z for z in board.Zones() if z.GetIsRuleArea()]
    groups = {}; adopted = []; rejected = []; owners = []
    board_box = board.GetBoardEdgesBoundingBox()
    def clear(t):
        box = t.GetBoundingBox(); box.Inflate(pcb.FromMM(.2))
        if not board_box.Contains(box): return "outside board"
        for l in LAYERS:
            if not t.IsOnLayer(l): continue
            shape = t.GetEffectiveShape(l)
            for z in rule_areas:
                if z.GetLayerSet().Contains(l) and (z.GetDoNotAllowVias() if isinstance(t, pcb.PCB_VIA) else z.GetDoNotAllowTracks()) and z.Outline().Collide(shape, 0): return "rule area"
            seen = set()
            for i in range(math.floor(pcb.ToMM(box.GetX())/3), math.floor(pcb.ToMM(box.GetRight())/3)+1):
                for j in range(math.floor(pcb.ToMM(box.GetY())/3), math.floor(pcb.ToMM(box.GetBottom())/3)+1):
                    for other in spatial[i,j,l]:
                        if id(other) in seen: continue
                        seen.add(id(other))
                        if other.GetNetname() != t.GetNetname() and shape.Collide(obstacle_shapes[id(other),l], pcb.FromMM(.2)-10): return "foreign copper " + other.m_Uuid.AsString()
                        if isinstance(t, pcb.PCB_VIA) and (isinstance(other, pcb.PCB_VIA) or isinstance(other, pcb.PAD) and other.GetDrillSize().x):
                            d = pcb.ToMM(other.GetDrillValue() if isinstance(other, pcb.PCB_VIA) else other.GetDrillSize().x)
                            if math.dist(xy(t.GetPosition()), xy(other.GetPosition())) < (pcb.ToMM(t.GetDrillValue())+d)/2+.25-1e-6: return "drill clearance"
        return None
    for members, trans, refs in proposals:
        new = []
        for t in members:
            clone = t.Duplicate().Cast(); clone.SetParentGroup(None)
            clone.SetUuid(pcb.KIID(t.m_Uuid.AsString()))
            clone.Rotate(point(0, 0), pcb.EDA_ANGLE(trans[0], pcb.DEGREES_T)); clone.Move(point(trans[1], trans[2]))
            clone.SetNet(board.FindNet(t.GetNetname())); new.append(clone)
        blockers = [(t.m_Uuid.AsString(), clear(t)) for t in new]
        blockers = [(uid, reason) for uid, reason in blockers if reason]
        if blockers:
            rejected.append({"anchors": refs, "items": len(members), "transform_deg_xy_mm": trans, "blockers": blockers})
            owners.extend(new); continue
        for t in new:
            uid = t.m_Uuid.AsString(); name = memberships[uid]
            if name not in groups:
                g = pcb.PCB_GROUP(board); g.SetName(name); board.Add(g); groups[name] = g
            t.SetLocked(True); board.Add(t); groups[name].AddItem(t); index(t); owners.append(t)
            adopted.append({"baseline_uuid": uid, "candidate_uuid": uid, "group": name, "anchors": refs, "transform_deg_xy_mm": trans})
    return {"baseline_capture_sha256": sha(BASE / "evidence/high-current-tap-capture.json"), "adopted": adopted,
            "rejected": rejected, "unmappable": skipped,
            "method": "Original UUID, net, dimensions and layer; one rigid pad-anchored transform; exact native foreign-copper/keepout/drill checks. No generated thin-track classification."}, owners


def main(path, size, resume=False):
    ledger = json.loads(LEDGER.read_text(encoding="utf-8"))
    limit = ledger["limits"]["cycles"][size]
    done = [c for c in ledger["cycles"] if c["size"] == size]
    assert minutes(ledger) < 140 and not ledger.get("stop_required")
    if resume:
        assert done and done[-1]["status"] == "in_progress" and done[-1]["input_sha256"] == sha(path)
        cycle = done[-1]
        assert not cycle.get("preparation_binding_retry")
        cycle["preparation_binding_retry"] = "One restart after fixing read-only m_Uuid assignment to documented SetUuid; no PCB had been saved."
    else:
        assert len(done) < limit and len(ledger["cycles"]) < 5
        if done: assert done[-1].get("progress_permits_next_cycle"), "Progress gate did not authorize another cycle"
        cycle = {"size": size, "cycle": len(done)+1, "started_utc": datetime.now(timezone.utc).isoformat(), "input_sha256": sha(path), "status": "in_progress"}
        ledger["cycles"].append(cycle)
    write(LEDGER, ledger)
    board = pcb.LoadBoard(str(path)); baseline = pcb.LoadBoard(str(BASE / "kicad/HomeMy_PMU_RevA.kicad_pcb"))
    removed = []; owners = []
    for g in list(board.Groups()):
        if not g.GetName().startswith("PWR_"): continue
        for t in list(g.GetItems()): g.RemoveItem(t)
        board.Remove(g); owners.append(g)
    for t in list(board.GetTracks()):
        if t.GetNetname() not in POWER_NETS: continue
        minimum = 6 if t.GetNetname() in ("ARM_L_N", "ARM_R_N") else 4
        bad = pcb.ToMM(t.GetWidth(pcb.F_Cu)) < .8-1e-6 or pcb.ToMM(t.GetDrillValue()) < .4-1e-6 if isinstance(t, pcb.PCB_VIA) else pcb.ToMM(t.GetWidth()) < minimum-1e-6
        if bad:
            removed.append({"uuid": t.m_Uuid.AsString(), "net": t.GetNetname(), "reason": "No valid original exception mapping; unapproved power-net copper"})
            board.Remove(t); owners.append(t)
    strengthened = []
    for z in board.Zones():
        if not z.GetIsRuleArea() and z.GetNetname() in POWER_NETS and z.GetMinThickness() < pcb.FromMM(1.2):
            strengthened.append({"uuid": z.m_Uuid.AsString(), "net": z.GetNetname(), "old_min_mm": pcb.ToMM(z.GetMinThickness())})
            z.SetMinThickness(pcb.FromMM(1.2))
    inherited, held = inherit_taps(board, baseline); owners.extend(held)
    board.BuildConnectivity(); filler = pcb.ZONE_FILLER(board); filler.Fill(board.Zones())
    pcb.SaveBoard(str(path), board)
    out = ROOT / "results" / (path.stem+".json")
    result = json.loads(out.read_text(encoding="utf-8"))
    result.setdefault("cycles", {})[str(cycle["cycle"])] = {"input_sha256": cycle["input_sha256"], "copper_preparation_sha256": sha(path),
        "removed_unapproved_power_copper": removed, "restored_power_fill_minima": strengthened, "original_tap_inheritance": inherited}
    write(out, result)
    print("Prepared", size, "cycle", cycle["cycle"], "removed", len(removed), "inherited", len(inherited["adopted"]), "rejected components", len(inherited["rejected"]), flush=True)
    return board, baseline, filler, owners


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("board", type=Path); ap.add_argument("size"); ap.add_argument("--resume-preparation", action="store_true"); args = ap.parse_args()
    owners = main(args.board.resolve(), args.size, args.resume_preparation)
