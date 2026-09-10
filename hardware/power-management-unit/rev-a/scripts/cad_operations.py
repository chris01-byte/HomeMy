"""Native KiCad board checks, zone preparation, and routing interchange."""
from pathlib import Path
import argparse
import json
import math
import traceback
import pcbnew as pcb
from build_board import force_exit, mm, point, drawing, label
from build_schematic import ROOT, CAD, PROJECT


def zone(board, name, corners, layer, priority=1, clearance=.5):
    z=pcb.ZONE(board)
    z.SetLayer(layer)
    z.SetNet(board.FindNet(name))
    z.SetLocalClearance(mm(clearance))
    z.SetMinThickness(mm(.25))
    z.SetPadConnection(pcb.ZONE_CONNECTION_FULL)
    z.SetAssignedPriority(priority)
    z.SetIslandRemovalMode(pcb.ISLAND_REMOVAL_MODE_ALWAYS)
    outline=z.Outline()
    outline.NewOutline()
    for x,y in corners:
        outline.Append(mm(x),mm(y))
    board.Add(z)
    return z


def rect(x1,y1,x2,y2):
    return [(x1,y1),(x2,y1),(x2,y2),(x1,y2)]


def corridor(board,net,points,width,layer,priority=3):
    """Overlapping copper polygons; foreign pads retain zone clearance."""
    for (x1,y1),(x2,y2) in zip(points,points[1:]):
        length=math.hypot(x2-x1,y2-y1)
        nx,ny=-(y2-y1)*width/2/length,(x2-x1)*width/2/length
        zone(board,net,[(x1+nx,y1+ny),(x2+nx,y2+ny),
                        (x2-nx,y2-ny),(x1-nx,y1-ny)],layer,priority)
    for x,y in points[1:-1]:
        zone(board,net,rect(x-width/2,y-width/2,x+width/2,y+width/2),layer,priority)


def merge_zones(board):
    groups={}
    for z in list(board.Zones()):
        if not z.GetIsRuleArea() and not z.GetZoneName().startswith('LOWER_POWER/'):
            groups.setdefault((z.GetNetname(),z.GetLayer(),z.GetAssignedPriority()),[]).append(z)
    for key,zones in groups.items():
        if len(zones)<2:
            continue
        combined=zones[0].Outline()
        for z in zones[1:]:
            combined.BooleanAdd(z.Outline())
        combined.Simplify()
        for z in zones[1:]:
            board.Remove(z)


def foreign_pad_near(pads,net,x,y,d=.9):
    for p in pads:
        if p.GetNetname()==net:
            continue
        b=p.GetBoundingBox()
        if pcb.ToMM(b.GetX())-d < x < pcb.ToMM(b.GetRight())+d and pcb.ToMM(b.GetY())-d < y < pcb.ToMM(b.GetBottom())+d:
            return True
    return False


def upper_branches(board):
    # Short broad arm returns terminate at their individual star junctions.
    for net,poly in [
        ('ARM_L_N',[(195,105),(225,105),(225,120),(205,132),(195,132)]),
        ('ARM_R_N',[(225.5,105),(255.5,105),(255.5,120),(235,132),(225.5,132)])]:
        for layer in (pcb.F_Cu,pcb.B_Cu):
            zone(board,net,poly,layer,3)
    # Motion feeds to drive, lift and brake resistor. The connector breakouts are
    # 3 mm; a six-millimetre spine exists on both 70 um outer layers.
    for layer in (pcb.F_Cu,pcb.B_Cu):
        corridor(board,'MOTION_BUS_P',[(329,20),(356,20),(356,91)],6,layer,2)
        for y in (35,63,91):
            corridor(board,'MOTION_BUS_P',[(349,y),(356,y)],3,layer,2)
    corridor(board,'DRIVE_N',[(349,57.92),(332,57.92),(332,108),(280,108),(280,122)],8,pcb.F_Cu)
    # Two 35 um inner layers keep the lift return separate from the chopper
    # pulse return and drive return. It joins BATT_N only through NT4.
    for layer in (pcb.In1_Cu,pcb.In2_Cu):
        corridor(board,'LIFT_N',[(349,85.92),(341.5,85.92)],3,layer)
        corridor(board,'LIFT_N',[(341.5,85.92),(341.5,112),(310,112),(310,122)],8,layer)
    # Q40 source is the western pad bank; local analogue reference NT10 does
    # not carry the resistor pulse current.
    zone(board,'CHOPPER_N',rect(294.5,31.7,299.5,46),pcb.F_Cu,4)
    for x in (299,316):
        corridor(board,'CHOPPER_N',[(x,17),(x,23)],3,pcb.B_Cu,4)
    corridor(board,'CHOPPER_N',[(299,23),(316,23)],8,pcb.B_Cu,4)
    corridor(board,'CHOPPER_N',[(299,23),(295,23),(295,44),(298,44),(303,53),(342,53),(342,114),(340,122)],8,pcb.B_Cu,4)
    zone(board,'CHOP_DRAIN',rect(300,29.7,340,46.5),pcb.F_Cu,3)
    corridor(board,'CHOP_DRAIN',[(338,32),(342,29.92),(349,29.92)],3,pcb.F_Cu,3)
    # Native pad-to-plane connections plus dedicated local transfer vias.
    pads=[p for f in board.GetFootprints() for p in f.Pads()]
    for x in (295,296.5,298):
        for y in (40.5,42,43.5,45):
            if foreign_pad_near(pads,'CHOPPER_N',x,y):
                continue
            v=pcb.PCB_VIA(board)
            v.SetViaType(pcb.VIATYPE_THROUGH)
            v.SetLayerPair(pcb.F_Cu,pcb.B_Cu)
            v.SetPosition(point(x,y)); v.SetWidth(mm(.8)); v.SetDrill(mm(.4))
            v.SetNet(board.FindNet('CHOPPER_N'));board.Add(v)


def prepare(board):
    # Broad outer-layer pours are reinforced by removable copper strips. These
    # polygons are not, by themselves, a claim of 60 A continuous PCB capability.
    power=[
        ('BATT_FUSED_P',rect(7,34,28,56)),
        ('BATT_SENSED_P',rect(33,14,58.9,87)),
        ('MAIN_COMMON',rect(59.2,14,80.8,87)),
        ('SYS_BUS_P',rect(81.1,14,118,87)),
        ('MOTION_SENSED_P',rect(122,19,153.9,79)),
        ('MOTION_COMMON',rect(154.2,19,175.8,79)),
        ('MOTION_BUS_P',[(176.1,12),(331,12),(331,25),(214,25),(214,87),(176.1,87)]),
        ('BATT_N',rect(6,109,355,133)),
    ]
    for name,corners in power:
        for layer in (pcb.F_Cu,pcb.B_Cu):
            zone(board,name,corners,layer)
    zone(board,'LOGIC_GND',rect(5,151,355,295),pcb.In1_Cu,0,.3)
    zone(board,'LOGIC_GND',rect(17,67,35,86),pcb.In1_Cu,0,.3)
    zone(board,'CHOP_GND',rect(231,28,345,108),pcb.In1_Cu,0,.3)
    upper_branches(board)
    try:
        from route_lower_power import prepare_lower_power
    except ImportError:
        print('WARNING: lower power routing module not yet available',flush=True)
    else:
        lower_manifest=prepare_lower_power(board)
        (ROOT/'design'/'lower-power-routing.json').write_text(json.dumps(lower_manifest,indent=2))
    # Reinforced transfer columns stay outside the FET mounting-base solder lands.
    columns=[('BATT_SENSED_P',40,48,16,84),('MAIN_COMMON',66,74,16,84),
             ('SYS_BUS_P',96,108,16,84),('MOTION_SENSED_P',132,142,20,78),
             ('MOTION_COMMON',160,170,20,78),('MOTION_BUS_P',195,207,16,84),
             ('BATT_N',20,352,114,128)]
    pads=[p for f in board.GetFootprints() for p in f.Pads()]
    counts={}
    for name,x1,x2,y1,y2 in columns:
        counts[name]=0
        for x in range(x1,x2+1,2):
            for y in range(y1,y2+1,2):
                obstructed=False
                if any(z.GetNetname()!=name and not z.GetIsRuleArea() and z.GetAssignedPriority()>1
                       and any(z.Outline().Contains(point(x+dx,y+dy)) for dx,dy in [(0,0),(.9,0),(-.9,0),(0,.9),(0,-.9)])
                       for z in board.Zones()):
                    continue
                for p in pads:
                    b=p.GetBoundingBox()
                    d=.9 if p.GetNetname()!=name else .5
                    if (pcb.ToMM(b.GetX())-d < x < pcb.ToMM(b.GetRight())+d and
                        pcb.ToMM(b.GetY())-d < y < pcb.ToMM(b.GetBottom())+d):
                        obstructed=True
                        break
                if obstructed:
                    continue
                v=pcb.PCB_VIA(board)
                v.SetViaType(pcb.VIATYPE_THROUGH)
                v.SetLayerPair(pcb.F_Cu,pcb.B_Cu)
                v.SetPosition(point(x,y))
                v.SetWidth(mm(.8))
                v.SetDrill(mm(.4))
                v.SetNet(board.FindNet(name))
                board.Add(v)
                counts[name]+=1
    # Individual gate resistor links are deliberately short and remain locked
    # during signal routing. Global controller gate nets route subsequently.
    bynet={}
    for p in pads:
        bynet.setdefault(p.GetNetname(),[]).append(p)
    for number in range(1,11):
        name=f'Q{number}_G'
        items=bynet[name]
        gate=next(p for p in items if p.GetParentFootprint().GetReference()==f'Q{number}')
        resistor=next(p for p in items if p.GetParentFootprint().GetReference()==f'R{number}')
        gx,gy=pcb.ToMM(gate.GetPosition().x),pcb.ToMM(gate.GetPosition().y)
        rx,ry=pcb.ToMM(resistor.GetPosition().x),pcb.ToMM(resistor.GetPosition().y)
        # Escape beyond the row of source terminals before turning along it.
        escape=gx+(2.25 if rx>gx else -2.25)
        route=[(gx,gy),(escape,gy),(escape,ry),(rx,ry)]
        for start,end in zip(route,route[1:]):
            t=pcb.PCB_TRACK(board)
            t.SetStart(point(*start));t.SetEnd(point(*end))
            t.SetWidth(mm(.3));t.SetLayer(pcb.F_Cu)
            t.SetNet(gate.GetNet());t.SetLocked(True);board.Add(t)
    (ROOT/'design'/'via-field-counts.json').write_text(json.dumps({
        'rev_a_engineering_prototype':True,'rev_b_production':False,
        'via_drill_mm':.4,'via_pad_mm':.8,'minimum_hole_plating_um':25,
        'counts':counts,'note':'Counts alone do not establish current sharing or local thermal rating.'},indent=2))
    board.BuildConnectivity()
    merge_zones(board)
    print('Prepared high-current zones and transfer vias:',counts,flush=True)


def main():
    p=argparse.ArgumentParser()
    p.add_argument('operation',choices=['prepare','fill','dsn','import','drc','geometry','plot'])
    p.add_argument('--session',type=Path)
    args=p.parse_args()
    filename=CAD/(PROJECT+'.kicad_pcb')
    board=pcb.LoadBoard(str(filename))
    reports=ROOT/'reports'
    reports.mkdir(exist_ok=True)
    if args.operation=='plot':
        from export_manufacturing import plot
        for name,layer in [('top-copper',pcb.F_Cu),('inner1-copper',pcb.In1_Cu),
                           ('inner2-copper',pcb.In2_Cu),('bottom-copper',pcb.B_Cu)]:
            output=plot(board,reports,name,[layer,pcb.Edge_Cuts],pcb.PLOT_FORMAT_SVG,True)
            print(output,flush=True)
    if args.operation=='prepare':
        prepare(board)
    if args.operation in ['prepare','fill','import']:
        if args.operation=='import':
            if not args.session or not pcb.ImportSpecctraSES(board,str(args.session.resolve())):
                raise RuntimeError('Routing session import failed')
            from sync_nc_nets import sync_nc_nets
            nc_result=sync_nc_nets(board)
            (reports/'nc-net-synchronization.json').write_text(json.dumps(nc_result,indent=2))
        board.BuildConnectivity()
        filler=pcb.ZONE_FILLER(board)
        filler.Fill(board.Zones())
        pcb.SaveBoard(str(filename),board)
        print('Zones filled; native PCB saved.',flush=True)
    if args.operation=='dsn':
        output=reports/(PROJECT+'.dsn')
        if not pcb.ExportSpecctraDSN(board,str(output)):
            raise RuntimeError('Specctra export failed')
        print('Exported',output,flush=True)
    if args.operation=='drc':
        result=pcb.WriteDRCReport(board,str(reports/'drc-native.txt'),pcb.EDA_UNITS_MM,True)
        print('Native DRC report generated:',result,flush=True)
        if not result:
            raise RuntimeError('DRC report generation failed')
    if args.operation=='geometry':
        result=[]
        for f in board.GetFootprints():
            result.append({'ref':f.GetReference(),'x':pcb.ToMM(f.GetPosition().x),'y':pcb.ToMM(f.GetPosition().y),
                           'rotation':f.GetOrientationDegrees(),
                           'pads':[{'number':pad.GetNumber(),'net':pad.GetNetname(),
                                    'x':pcb.ToMM(pad.GetPosition().x),'y':pcb.ToMM(pad.GetPosition().y),
                                    'width':pcb.ToMM(pad.GetSize().x),'height':pcb.ToMM(pad.GetSize().y)} for pad in f.Pads()]})
        (reports/'board-pad-geometry.json').write_text(json.dumps(result,indent=2))


if __name__=='__main__':
    try:
        main()
    except BaseException:
        traceback.print_exc()
        force_exit(1)
    force_exit(0)
