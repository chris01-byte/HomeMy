"""Finite source-preserving force-return recipes, including listed signal jumps.

No force vias are deleted. Local battery-return vias retain UUID and geometry
when shifted aside for the two converter return corridors.
"""
from finish_280_routes import *
from cad_operations import corridor

def split_jump(c,net,x,y0=146.5,y1=156.):
    board=c.board;removed=[];parts=[];cuts=[]
    for t in list(board.GetTracks()):
        if isinstance(t,pcb.PCB_VIA) or t.GetLayer()!=pcb.In1_Cu or t.GetNetname()!=net:continue
        a,b=xy(t.GetStart()),xy(t.GetEnd())
        if min(a[0],b[0])<x-.001 or max(a[0],b[0])>x+1.1 or max(a[1],b[1])<=y0 or min(a[1],b[1])>=y1:continue
        if abs(b[1]-a[1])<1e-9:
            lo,hi=0.,1.
        else:
            q0=(y0-a[1])/(b[1]-a[1]);q1=(y1-a[1])/(b[1]-a[1]);lo=max(0.,min(q0,q1));hi=min(1.,max(q0,q1))
        if hi<=lo:continue
        p=lambda u:[round(a[i]+u*(b[i]-a[i]),6) for i in [0,1]]
        A,B=p(lo),p(hi);w=pcb.ToMM(t.GetWidth())
        if lo>1e-9:parts.append(([a,A],w,pcb.In1_Cu))
        parts.append(([A,B],w,pcb.In2_Cu))
        if hi<1-1e-9:parts.append(([B,b],w,pcb.In1_Cu))
        cuts.extend([p(u) for u in [lo,hi] if abs(p(u)[1]-y0)<1e-5 or abs(p(u)[1]-y1)<1e-5])
        assert not t.GetParentGroup(), 'No grouped copper may be split'
        removed.append(t)
    cuts=list({tuple(p):p for p in cuts}.values());assert len(cuts)==2,(net,cuts)
    for t in removed:board.Remove(t);c.owners.append(t)
    c.screen=Screen(board)
    assert c.route('In1 lift crossing layer jump '+net,net,parts,[(p,.6,.3) for p in cuts]), 'Explicit signal jump obstructed: '+net
    c.records[-1]['removed_original_uuids']=[t.m_Uuid.AsString() for t in removed]

def relocate_return_vias(c,columns,ys):
    board=c.board;old=[];new=[]
    for t in list(board.GetTracks()):
        if not isinstance(t,pcb.PCB_VIA) or t.GetNetname()!='BATT_N':continue
        x,y=xy(t.GetPosition())
        if x not in columns or all(abs(y-v)>1e-6 for v in ys):continue
        assert not t.GetParentGroup();n=t.Duplicate().Cast();n.SetUuid(pcb.KIID(t.m_Uuid.AsString()));n.SetPosition(point(columns[x],y+.9))
        old.append(t);new.append(n);board.Remove(t);c.owners.extend([t,n])
    assert len(old)==len(columns)*len(ys)
    c.screen=Screen(board)
    for n in new:
        assert not c.screen.reason(n),c.obstacles(n)
        board.Add(n);c.screen.index(n)
    c.records.append({'label':'Relocate local BATT_N vias without count/diameter reduction','adopted':True,
                      'moves':[{'uuid':a.m_Uuid.AsString(),'from_mm':xy(a.GetPosition()),'to_mm':xy(b.GetPosition()),'diameter_mm':pcb.ToMM(b.GetWidth(pcb.F_Cu)),'drill_mm':pcb.ToMM(b.GetDrillValue())} for a,b in zip(old,new)]})

def pour_for(c,record):
    # The actual short 3-mm branch necks are below the generic 4-mm track-only
    # force audit filter. Add real, solid copper of the same width; do not alter
    # the required pair definitions or credit an omitted track as a pass.
    for part in record['parts']:
        existing={z.m_Uuid.AsString() for z in c.board.Zones()}
        corridor(c.board,record['net'],part['points_mm'],part['width_mm'],c.board.GetLayerID(part['layer']),20)
        for z in c.board.Zones():
            if z.m_Uuid.AsString() not in existing:z.SetMinThickness(pcb.FromMM(1.2));z.SetLocalClearance(pcb.FromMM(.5));z.SetZoneName('LOWER_POWER/280_FINISH')

def main():
    guard(read());before=sha(BOARD);board=pcb.LoadBoard(str(BOARD));c=Controlled(board)
    # Phase B4: converter returns preserve all existing battery-return vias.
    attempt('PC_N return','275 missing return')
    relocate_return_vias(c,{21.4:18.7,23.2:25.9},[140.2,142.,143.8,145.6])
    assert c.route('PC 3A return','PC_N',[(['NT5.1',(22,137),(22,153),(17,158),(17,170.08),'J9.2'],3,pcb.B_Cu)])
    pour_for(c,c.records[-1])
    attempt('LOGIC_BUCK_N return','275 missing return')
    relocate_return_vias(c,{44.8:42.1,46.6:49.3},[140.2,142.,143.8,145.6,147.4,149.2])
    assert c.route('Logic converter 2A return','LOGIC_BUCK_N',[(['NT6.1',(46,152.5),(17,152.5),(17,197.08),'J10.2'],3,pcb.F_Cu)])
    pour_for(c,c.records[-1])
    # Phase B5: retain the existing B.Cu drive and In2 lift paths, add the
    # originally required layers with explicitly protected copper.
    attempt('DRIVE_N F.Cu','275 missing required F.Cu path')
    assert c.route('Drive F.Cu parallel to retained 8mm B.Cu','DRIVE_N',[(['NT3.1',(135,153),(260,153),'J7.2'],4,pcb.F_Cu)])
    attempt('LIFT_N In1.Cu','275 missing required In1.Cu path')
    for net,x in [('MOTION_GATE_EN',175.1488),('V3V3',178.7122),('MOTION_IMON_INPUT',198.3061),('MOTION_FLT_N',204.0479),('MOTION_TEMP_FLT_N',204.8556),('TEMP_MOTION_ADC',213.8401),('LOGIC_GND',219.9535),('CHOP_ACTIVE_N',222.0964),('INA_ALERT_N',223.6985),('CHOP_FAULT_N',225.4121),('CHOP_TEMP_ADC',252.6508)]:
        split_jump(c,net,x)
    assert c.route('Lift required In1.Cu corridor','LIFT_N',[(['NT4.1',(159,150),(257,150),(257,159)],4,pcb.In1_Cu)])
    attempt('LOGIC_5V_N B.Cu','275 missing J11-J18 B.Cu')
    assert c.route('5V return 6mm spine and short 3mm pickups','LOGIC_5V_N',[
        (['J11.2',(48.08,207)],3,pcb.B_Cu), ([(48.08,207),(137,207)],6,pcb.B_Cu),
        (['J18.3',(120.16,207)],3,pcb.B_Cu), (['C246.2',(137,197),(137,207)],3,pcb.B_Cu)])
    pour_for(c,c.records[-1])
    # Phase B6: actual copper attachment to the existing connected reference.
    attempt('U11 LOGIC_GND stitches','two only-F.Cu vias')
    assert c.route('U11 local ground stitches','LOGIC_GND',[
        ([(22.9,21.5),(23.9,22),(25.6504,22.1019)],.2,pcb.In2_Cu)])
    pcb.SaveBoard(str(BOARD),board)
    action('cycle-03-force',{'input_sha256':before,'output_sha256':sha(BOARD),'recipes':c.records,'refill_and_native_pending':True})
    write(OUT/'cycle-03-force-recipes.json',{'input_sha256':before,'output_sha256':sha(BOARD),'recipes':c.records})
    return board,c

if __name__=='__main__':owners=main()
