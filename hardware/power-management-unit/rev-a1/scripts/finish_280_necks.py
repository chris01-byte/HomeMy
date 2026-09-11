"""Localized signal transfers away from evidenced power-copper necks."""
from finish_280_routes import *

def remove(c,prefixes):
    found=[]
    for t in list(c.board.GetTracks()):
        if any(t.m_Uuid.AsString().startswith(s) for s in prefixes):
            assert not isinstance(t,pcb.PCB_VIA) and not t.GetParentGroup()
            found.append(t);c.board.Remove(t);c.owners.append(t)
    assert len(found)==len(prefixes),(prefixes,len(found))
    c.screen=Screen(c.board)
    return [t.m_Uuid.AsString() for t in found]

def move_via(c,prefix,target,label):
    board=c.board;v=next(t for t in board.GetTracks() if t.m_Uuid.AsString().startswith(prefix));net=v.GetNetname();at=xy(v.GetPosition())
    assert isinstance(v,pcb.PCB_VIA) and not v.GetParentGroup()
    attempt(label,str(at));replacement=v.Duplicate().Cast();replacement.SetUuid(pcb.KIID(v.m_Uuid.AsString()));replacement.SetPosition(point(*target))
    old=[v];new=[replacement]
    for t in board.GetTracks():
        if isinstance(t,pcb.PCB_VIA) or t.GetNetname()!=net:continue
        a,b=xy(t.GetStart()),xy(t.GetEnd())
        if a!=at and b!=at:continue
        assert not t.GetParentGroup();n=t.Duplicate().Cast();n.SetUuid(pcb.KIID(t.m_Uuid.AsString()))
        if a==at:n.SetStart(point(*target))
        if b==at:n.SetEnd(point(*target))
        old.append(t);new.append(n)
    assert len(old)==3, (label,len(old))
    for t in old:board.Remove(t)
    c.owners.extend(old+new);c.screen=Screen(board)
    for n in new:
        assert not c.screen.reason(n),c.obstacles(n)
        board.Add(n);c.screen.index(n)
    c.records.append({'label':label,'adopted':True,'net':net,'via_uuid':v.m_Uuid.AsString(),'from_mm':at,'to_mm':target,'preserved_track_uuids':[t.m_Uuid.AsString() for t in old[1:]]})

def main():
    guard(read());before=sha(BOARD);board=pcb.LoadBoard(str(BOARD));c=Controlled(board)
    move_via(c,'d868163d',(231.3,93.8937),'ARM_L_N neck at CHOP_DRIVE_H via')
    move_via(c,'dd278165',(144.9,84.2),'SYS_BUS_P C8 neck at MOTION_ISCP via')
    attempt('MAIN_COMMON neck V3V3','three original F.Cu snake segments')
    removed=remove(c,['90cd6fa2','c636fe24','de37dec7'])
    assert c.route('V3V3 measurement supply off main force array','V3V3',[
        (['R260.1',(67.7,52.9)],.2,pcb.F_Cu),
        ([(67.7,52.9),(66.7892,52.7017),(65.1535,52.7017),(64.1597,51.7079)],.2,pcb.In2_Cu)], [((67.7,52.9),.6,.3)])
    c.records[-1]['removed_original_uuids']=removed
    attempt('C300 MOTION_BUS_P neck CHOP_FB','old front detour beside C300.1')
    removed=remove(c,['88dd3a13','d78bec86','98953e4d','9796ddb1','3860104b'])
    assert c.route('CHOP_FB transfer clear of C300 force pickup','CHOP_FB',[
        ([(188.2973,92.4712),(188.2973,92.8),(188,92.8)],.2,pcb.F_Cu),
        ([(188,92.8),(192.9093,96.0446)],.2,pcb.In2_Cu)],[((188,92.8),.6,.3)])
    c.records[-1]['removed_original_uuids']=removed
    attempt('BATT_N neck CHOP_ACTIVE_N','original six-segment U35.4-TP30 front snake')
    removed=remove(c,['3dbb3960','66b94d4e','80b89755','a92f24c0','e40613ca','ec13b002'])
    assert c.route('CHOP_ACTIVE_N off battery via field','CHOP_ACTIVE_N',[
        (['U35.4',(223,113.865)],.2,pcb.F_Cu),(['TP30.1',(230.3,119)],.2,pcb.F_Cu),
        ([(223,113.865),(223.5,114.365),(223.5,120.8),(230.3,120.8),(230.3,119)],.2,pcb.In2_Cu)],
        [((223,113.865),.6,.3),((230.3,119),.6,.3)])
    c.records[-1]['removed_original_uuids']=removed
    owners=c.finish('cycle-03-necks')
    return board,c,owners

def temp_only():
    guard(read());board=pcb.LoadBoard(str(BOARD));c=Controlled(board)
    attempt('MOTION_COMMON neck TEMP_MOTION_ADC','six original TH21-R261 F.Cu segments')
    removed=remove(c,['a6bed821','11524797','c75181ea','7bee2f84','be3823c8','e171614d'])
    assert c.route('TEMP_MOTION_ADC off motion force array','TEMP_MOTION_ADC',[
        ([(164,65.825),(163,65.825)],.2,pcb.F_Cu),
        ([(163,65.825),(163,70.4),(162.6,70.8),(162.6,71.6),(163,72),(163,77.3367),(163.9119,78.2486)],.2,pcb.In1_Cu)],
        [((163,65.825),.6,.3)])
    c.records[-1]['removed_original_uuids']=removed
    owners=c.finish('cycle-03-temp-neck');return board,c,owners

if __name__=='__main__':
    import sys
    owners=temp_only() if '--temp-only' in sys.argv else main()
