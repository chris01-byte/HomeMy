"""Apply the reviewed analog overlay and clear diagnosed foreign signal routes.

Existing force-current transfer vias and locked routes are preserved. Refill,
native DRC and fresh DSN routing are required after this integration step.
"""
import hashlib
import json
import re
import traceback
import pcbnew as pcb
from build_board import force_exit, readable_references
from build_schematic import ROOT, CAD, PROJECT
from analog_routing_corrections import apply_analog_routing_corrections, OWNED


def main():
    path=CAD/(PROJECT+'.kicad_pcb')
    before=hashlib.sha256(path.read_bytes()).hexdigest()
    board=pcb.LoadBoard(str(path))
    # The 0.8/0.4 mm transfer fields predate the signal router. They are physical
    # current-path elements, even though the original preparation left them unlocked.
    protected=[]
    for t in board.GetTracks():
        if isinstance(t,pcb.PCB_VIA) and abs(pcb.ToMM(t.GetWidth(pcb.F_Cu))-.8)<.0001 and abs(pcb.ToMM(t.GetDrillValue())-.4)<.0001:
            t.SetLocked(True);protected.append(t.m_Uuid.AsString())
    result=apply_analog_routing_corrections(board)
    diagnostic=ROOT/'reports/analog-routing-test-drc.json'
    data=json.loads(diagnostic.read_text())
    foreign=set()
    for violation in data['violations']:
        if violation['type'] not in ['clearance','shorting_items','tracks_crossing','hole_clearance','hole_to_hole']:
            continue
        names={name for item in violation['items'] for name in re.findall(r'\[([^\]]+)\]',item['description'])}
        if names & OWNED:
            foreign.update(names-OWNED-{'<no net>'})
    detached=[];removed={}
    for t in list(board.GetTracks()):
        if t.GetNetname() in foreign and not t.IsLocked():
            removed[t.GetNetname()]=removed.get(t.GetNetname(),0)+1
            board.Remove(t);detached.append(t)
    readable_references(board)
    board.BuildConnectivity()
    filler=pcb.ZONE_FILLER(board);filler.Fill(board.Zones())
    pcb.SaveBoard(str(path),board)
    result.update(board_saved=True,board_sha256_before=before,
                  board_sha256_after=hashlib.sha256(path.read_bytes()).hexdigest(),
                  protected_transfer_vias=len(protected),foreign_signal_items_removed=removed,
                  diagnostic_sha256=hashlib.sha256(diagnostic.read_bytes()).hexdigest())
    (ROOT/'reports/analog-routing-integration.json').write_text(json.dumps(result,indent=2)+'\n')
    print('Analog overlay saved; protected transfer vias:',len(protected),'; foreign signal items removed:',removed,flush=True)
    return board,detached,filler


if __name__=='__main__':
    try:
        native_owners=main()
    except BaseException:
        traceback.print_exc();force_exit(1)
    force_exit(0)
