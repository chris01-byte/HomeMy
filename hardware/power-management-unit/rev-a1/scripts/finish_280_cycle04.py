"""Second, final targeted correction of the cycle-03 force proposal.

The cycle-02 validated best remains in scratch. A rejected working candidate
is reopened explicitly; it does not replace the best unless full checks pass.
"""
from finish_280_routes import *
from finish_280 import SCRATCH
from finish_280_necks import move_via

def main():
    guard(read());assert read()['cycles'][-1]['number']==4
    source=SCRATCH/'rejected-cycle-03.kicad_pcb'
    assert sha(source)=='5a395e051ded0caf7cb3bb973a2647e8ecf0f9aa965727157910085bbdc09c6b'
    # Load the staged PCB beside its authoritative .pro/.dru. Loading the
    # scratch filename without those files can serialize KiCad defaults into
    # the destination project during SaveBoard (observed and rejected in c4).
    import shutil
    assert sha(BOARD.with_suffix('.kicad_pro'))==read()['project_sha256']
    shutil.copyfile(source,BOARD)
    board=pcb.LoadBoard(str(BOARD));c=Controlled(board)
    # Merge only the new overlapping same-net pieces, preserving the exact
    # union of their contours and all clearances, fill minima and priorities.
    groups={};removed=[]
    for z in board.Zones():
        if z.GetZoneName()=='LOWER_POWER/280_FINISH':groups.setdefault((z.GetNetname(),z.GetLayer()),[]).append(z)
    for key,zones in groups.items():
        q=zones[0].Outline()
        for z in zones[1:]:q.BooleanAdd(z.Outline())
        q.Simplify()
        for z in zones[1:]:board.Remove(z);c.owners.append(z);removed.append(z.m_Uuid.AsString())
    c.records.append({'label':'Union overlapping same-net return contours','adopted':True,'nets':[k[0] for k in groups],
                      'removed_redundant_zone_uuids':removed,'no_priority_or_rule_change':True})
    attempt('LIFT_N In1.Cu','275 missing required In1.Cu path')
    removed=[]
    for t in list(board.GetTracks()):
        if t.GetNetname()!='V3V3':continue
        if isinstance(t,pcb.PCB_VIA):
            matched=xy(t.GetPosition())==[178.7122,156.0]
        else:
            a,b=xy(t.GetStart()),xy(t.GetEnd())
            matched=t.GetLayer() in [pcb.In1_Cu,pcb.In2_Cu] and min(a[0],b[0])>=178.71219 and max(a[0],b[0])<=180.87971 and min(a[1],b[1])>=146.49999 and max(a[1],b[1])<=158.30071
        if matched:
            assert not t.GetParentGroup();removed.append(t.m_Uuid.AsString());board.Remove(t);c.owners.append(t)
    assert len(removed)==4,removed
    c.screen=Screen(board)
    assert c.route('V3V3 jump preserves lift In2 bypass','V3V3',[
        ([(178.7122,146.5),(178.7122,156.1332),(180.8797,158.3007)],.2,pcb.B_Cu)])
    c.records[-1]['removed_original_or_cycle03_uuids']=removed
    move_via(c,'d868163d',(229.5,93.8937),'ARM_L_N neck at CHOP_DRIVE_H via')
    filler=c.finish('cycle-04-corrections')
    return board,c,filler

if __name__=='__main__':owners=main()
