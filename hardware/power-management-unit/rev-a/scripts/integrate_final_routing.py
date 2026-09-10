"""Import the exact reviewed routing candidate and apply its local repairs.

This explicit replacement operation saves the project PCB only after protected
copper preservation and zero native ratsnest count are established. Native DRC
and schematic parity remain independent required checks after this operation.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import traceback
import pcbnew as pcb
from build_board import force_exit
from final_routing_repairs import apply_final_routing_repairs
from sync_nc_nets import sync_nc_nets

ROOT=Path(__file__).resolve().parents[1]
EXPECTED_BOARD='bc006b41f415a20aa9412b334fb4027861b08900985e67b9a2d2db8188b97be6'
EXPECTED_SESSION='30ff3126f797f816506923bb6c97da340ea58be75bee15d42c2b8535435c311a'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()


def protected_geometry(board):
    result=Counter()
    for t in board.GetTracks():
        if not t.IsLocked():continue
        if isinstance(t,pcb.PCB_VIA):
            signature=('via',t.GetNetname(),t.GetPosition().x,t.GetPosition().y,
                       t.GetWidth(pcb.F_Cu),t.GetDrillValue(),
                       tuple(t.IsOnLayer(layer) for layer in [pcb.F_Cu,pcb.In1_Cu,pcb.In2_Cu,pcb.B_Cu]))
        else:
            signature=('track',t.GetNetname(),t.GetLayer(),t.GetWidth(),
                       tuple(sorted(((t.GetStart().x,t.GetStart().y),(t.GetEnd().x,t.GetEnd().y)))))
        result[signature]+=1
    return result


def main():
    filename=ROOT/'kicad/HomeMy_PMU_RevA.kicad_pcb'
    session=ROOT/'reports/routing-final-selected.ses'
    before=digest(filename)
    if before!=EXPECTED_BOARD or digest(session)!=EXPECTED_SESSION:
        raise ValueError('Input differs from the reviewed board/session snapshot; do not replay this overlay blindly')
    board=pcb.LoadBoard(str(filename));protected=protected_geometry(board)
    if not pcb.ImportSpecctraSES(board,str(session)):
        raise RuntimeError('Native SES import failed')
    nc=sync_nc_nets(board)
    missing=protected-protected_geometry(board)
    if missing:raise AssertionError(f'Import lost or changed {sum(missing.values())} locked copper items')
    repair=apply_final_routing_repairs(board)
    board.BuildConnectivity();filler=pcb.ZONE_FILLER(board);filler.Fill(board.Zones())
    board.GetConnectivity().RecalculateRatsnest()
    unconnected=board.GetConnectivity().GetUnconnectedCount(False)
    if unconnected:raise AssertionError(f'Native board still has {unconnected} unconnected ratsnest edges; source not saved')
    if before!=digest(filename):raise AssertionError('Source changed during integration')
    pcb.SaveBoard(str(filename),board)
    result=dict(rev_a_engineering_prototype=True,rev_b_production=False,
                state='routed_board_requires_separate_final_native_checks',
                input_board_sha256=before,output_board_sha256=digest(filename),
                session_path='reports/routing-final-selected.ses',session_sha256=digest(session),
                preserved_locked_copper_items=sum(protected.values()),
                native_unconnected_ratsnest_edges=unconnected,nc_synchronization=nc,repairs=repair,
                note='Candidate router metrics differ from filled native connectivity. No process, DRC, thermal or hardware pass is inferred here.')
    (ROOT/'reports/final-routing-integration.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in result.items() if k not in ['repairs','nc_synchronization']}),flush=True)
    return board,filler


if __name__=='__main__':
    try:native_owners=main()
    except BaseException:traceback.print_exc();force_exit(1)
    force_exit(0)
