"""Apply two explicit post-review geometry corrections, preserving net identity."""
import hashlib
import json
import traceback
import pcbnew as pcb
from build_board import force_exit,point
from build_schematic import ROOT,CAD,PROJECT


def main():
    filename=CAD/(PROJECT+'.kicad_pcb')
    board=pcb.LoadBoard(str(filename))
    before=hashlib.sha256(filename.read_bytes()).hexdigest()
    old=point(169,91.5);new=point(170,91.5)
    moved=[]
    for t in board.GetTracks():
        if t.GetNetname()!='MOTION_CS_P':
            continue
        if isinstance(t,pcb.PCB_VIA):
            if t.GetPosition()==old:
                t.SetPosition(new);moved.append(t.m_Uuid.AsString())
        else:
            if t.GetStart()==old:
                t.SetStart(new);moved.append(t.m_Uuid.AsString())
            if t.GetEnd()==old:
                t.SetEnd(new);moved.append(t.m_Uuid.AsString())
            for getter,setter in [(t.GetStart,t.SetStart),(t.GetEnd,t.SetEnd)]:
                if getter()==point(169.3,91.8):
                    setter(point(170.3,91.8))
    drain=next(z for z in board.Zones() if not z.GetIsRuleArea() and z.GetNetname()=='CHOP_DRAIN' and z.GetLayer()==pcb.F_Cu)
    extension=pcb.SHAPE_POLY_SET();extension.NewOutline()
    for x,y in [(300,40),(340,40),(340,46.5),(300,46.5)]:
        extension.Append(point(x,y))
    drain.Outline().BooleanAdd(extension);drain.Outline().Simplify()
    board.BuildConnectivity();filler=pcb.ZONE_FILLER(board);filler.Fill(board.Zones())
    pcb.SaveBoard(str(filename),board)
    report={'rev_a_engineering_prototype':True,'rev_b_production':False,
            'board_sha256_before':before,'board_sha256_after':hashlib.sha256(filename.read_bytes()).hexdigest(),
            'motion_cs_via_mm':[170,91.5],'adjusted_track_via_uuids':moved,
            'chop_drain_zone_extension_mm':[[300,40],[340,46.5]],
            'remaining_check':'Native DRC and actual filled drain area after rerouting; target at least600mm2, no thermal rating inferred.'}
    (ROOT/'reports/final-power-geometry-corrections.json').write_text(json.dumps(report,indent=2))
    print('Shifted CS via/track items:',len(moved),'; enlarged drain zone to y46.5.',flush=True)
    return board,filler


if __name__=='__main__':
    try:
        native_owners=main()
    except BaseException:
        traceback.print_exc();force_exit(1)
    force_exit(0)
