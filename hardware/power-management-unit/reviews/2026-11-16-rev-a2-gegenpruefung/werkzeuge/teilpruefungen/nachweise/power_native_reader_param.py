"""Read-only native filled-copper analysis; never fills or saves the PCB."""
from pathlib import Path
import sys,json,math,hashlib,collections,traceback
ROOT=Path('<SITZUNG>/agents/evidence/repro/hardware/power-management-unit/rev-a')
sys.path.insert(0,str(ROOT/'scripts'))
import pcbnew as pcb
from build_board import force_exit,point,mm

def main():
    import os
    filename=Path(os.environ['PMU_BOARD'])
    digest=hashlib.sha256(filename.read_bytes()).hexdigest()
    board=pcb.LoadBoard(str(filename));board.BuildConnectivity();cn=board.GetConnectivity()
    fps={f.GetReference():f for f in board.GetFootprints()}
    tap_receipt=json.loads((ROOT/'evidence/high-current-tap-capture.json').read_text())
    source_tap_ids={row['uuid'] for rows in tap_receipt['groups'].values() for row in rows}
    tap_ids=source_tap_ids|{item.m_Uuid.AsString() for group in board.Groups() if group.GetName() in ['PWR_TAP_CONTROL','PWR_SYS_BRANCH_SPINE','PWR_SYS_BRANCH_FANOUT'] for item in group.GetItems()}
    layers=[pcb.F_Cu,pcb.In1_Cu,pcb.In2_Cu,pcb.B_Cu]
    selected=['BATT_FUSED_P','BATT_SENSED_P','MAIN_COMMON','SYS_BUS_P','MOTION_SENSED_P','MOTION_COMMON','MOTION_BUS_P','BATT_N','ARM_L_N','ARM_R_N','DRIVE_N','LIFT_N','CHOPPER_N','CHOP_DRAIN','PC_BUCK_IN_P','LOGIC_BUCK_IN_P','PC_N','LOGIC_BUCK_N','LOGIC_5V_N','V5V']
    polys={};zones=[]
    for z in board.Zones():
        name=z.GetNetname();layer=z.GetLayer()
        if z.GetIsRuleArea() or name not in selected:continue
        shape=z.GetFilledPolysList(layer)
        key=(name,layer)
        if key not in polys:polys[key]=pcb.SHAPE_POLY_SET()
        polys[key].BooleanAdd(shape)
        zones.append({'net':name,'layer':board.GetLayerName(layer),'name':z.GetZoneName(),'filled_outlines':shape.OutlineCount(),'filled_area_mm2':shape.Area()/1e12})
    print('Loaded filled polygons',len(zones),flush=True)
    # Add real same-net pad/track copper, then subtract own mechanical drills.
    for f in fps.values():
        for p in f.Pads():
            name=p.GetNetname()
            if name not in selected:continue
            for layer in layers:
                if not p.IsOnLayer(layer):continue
                key=(name,layer)
                if key not in polys:polys[key]=pcb.SHAPE_POLY_SET()
                q=pcb.SHAPE_POLY_SET();p.TransformShapeToPolygon(q,layer,0,mm(.005),pcb.ERROR_INSIDE)
                polys[key].BooleanAdd(q)
    for t in board.GetTracks():
        if t.m_Uuid.AsString() in tap_ids:continue
        name=t.GetNetname()
        if name not in selected:continue
        for layer in layers:
            if not t.IsOnLayer(layer):continue
            key=(name,layer)
            if key not in polys:polys[key]=pcb.SHAPE_POLY_SET()
            q=pcb.SHAPE_POLY_SET();t.TransformShapeToPolygon(q,layer,0,mm(.005),pcb.ERROR_INSIDE)
            polys[key].BooleanAdd(q)
    print('Added actual copper pads/tracks',flush=True)
    # Drill interiors are void in each plane. Circular holes only in these power paths.
    holes={}
    for item in [p for f in fps.values() for p in f.Pads()]+list(board.GetTracks()):
        if isinstance(item,pcb.PCB_VIA): d=pcb.ToMM(item.GetDrillValue())
        elif isinstance(item,pcb.PAD):d=pcb.ToMM(item.GetDrillSize().x)
        else:continue
        if d<=0 or item.GetNetname() not in selected:continue
        x,y=pcb.ToMM(item.GetPosition().x),pcb.ToMM(item.GetPosition().y)
        for layer in layers:
            if not item.IsOnLayer(layer):continue
            key=(item.GetNetname(),layer)
            if key not in holes:holes[key]=pcb.SHAPE_POLY_SET()
            h=pcb.SHAPE_POLY_SET();h.NewOutline()
            for k in range(40):h.Append(mm(x+d/2*math.cos(2*math.pi*k/40)),mm(y+d/2*math.sin(2*math.pi*k/40)))
            holes[key].Append(h)
    for key,h in holes.items():
        h.Simplify();polys[key].BooleanSubtract(h)
    for q in polys.values():q.Simplify();q.BuildBBoxCaches()
    print('Removed drill interiors',flush=True)

    # Geometric end-to-end checks on one layer, using points inside real pad
    # copper and outside the drill. These do not traverse component internals.
    def pad_samples(ref,number):
        p=next(p for p in fps[ref].Pads() if p.GetNumber()==str(number))
        x,y=pcb.ToMM(p.GetPosition().x),pcb.ToMM(p.GetPosition().y)
        if p.GetDrillSize().x==0:return [[x,y]]
        d=pcb.ToMM(p.GetDrillSize().x)/2+.10
        return [[x+d,y],[x-d,y],[x,y+d],[x,y-d]]
    def outline_ids(net,layer,points):
        q=polys.get((net,layer));ids=set()
        if q is None:return ids
        for x,y in points:
            for i in range(q.OutlineCount()):
                if q.Contains(point(x,y),i,0,True):ids.add(i)
        return ids
    path_checks=[]
    required_paths=[
      ('BATT_FUSED_P',pcb.F_Cu,('J1',1),('RSH1',1)),
      ('BATT_SENSED_P',pcb.F_Cu,('RSH1',4),('Q1',13)),
      ('MAIN_COMMON',pcb.F_Cu,('Q1',2),('Q4',2)),
      ('SYS_BUS_P',pcb.F_Cu,('Q4',13),('RSH2',1)),
      ('MOTION_SENSED_P',pcb.F_Cu,('RSH2',4),('Q7',13)),
      ('MOTION_COMMON',pcb.F_Cu,('Q7',2),('Q9',2)),
      ('MOTION_BUS_P',pcb.F_Cu,('Q9',13),('J3',1)),
      ('MOTION_BUS_P',pcb.F_Cu,('J3',1),('J5',1)),
      ('ARM_L_N',pcb.F_Cu,('J4',1),('NT1',1)),
      ('ARM_R_N',pcb.F_Cu,('J6',1),('NT2',1)),
      ('DRIVE_N',pcb.F_Cu,('J7',2),('NT3',1)),
      ('LIFT_N',pcb.In1_Cu,('J8',2),('NT4',1)),
      ('LIFT_N',pcb.In2_Cu,('J8',2),('NT4',1)),
      ('CHOP_DRAIN',pcb.F_Cu,('Q40',3),('J12',2)),
      ('CHOPPER_N',pcb.B_Cu,('C312',2),('NT7',1)),
      ('CHOPPER_N',pcb.B_Cu,('C313',2),('NT7',1)),
      ('BATT_N',pcb.B_Cu,('J2',1),('NT7',2)),
      ('LOGIC_5V_N',pcb.B_Cu,('J18',3),('J11',2)),
    ]
    anchors={'BATT_FUSED_P':('RSH1',1),'BATT_SENSED_P':('BC1',1),
             'MAIN_COMMON':('BC3',1),'SYS_BUS_P':('BC5',1),
             'MOTION_SENSED_P':('BC7',1),'MOTION_COMMON':('BC9',1),
             'MOTION_BUS_P':('BC11',1),'BATT_N':('BC15',1),
             'ARM_L_N':('NT1',1),'ARM_R_N':('NT2',1)}
    critical_refs={f'J{i}' for i in range(1,7)}|{f'Q{i}' for i in range(1,11)}|{f'BC{i}' for i in range(1,16)}|{f'NT{i}' for i in range(1,9)}|{'RSH1','RSH2'}
    for ref in sorted(critical_refs):
        for p in fps[ref].Pads():
            net=p.GetNetname()
            if net not in anchors:continue
            layers_to_check=[pcb.B_Cu] if net=='BATT_N' else [pcb.F_Cu]
            if ref.startswith('BC') or net in ['ARM_L_N','ARM_R_N']:
                layers_to_check=[pcb.F_Cu,pcb.B_Cu] if net!='BATT_N' else [pcb.B_Cu]
            for layer in layers_to_check:
                required_paths.append((net,layer,(ref,p.GetNumber()),anchors[net]))
    for net,layer,a,b in required_paths:
        pa,pb=pad_samples(*a),pad_samples(*b)
        ia,ib=outline_ids(net,layer,pa),outline_ids(net,layer,pb)
        path_checks.append({'net':net,'layer':board.GetLayerName(layer),'from_pad':f'{a[0]}.{a[1]}','to_pad':f'{b[0]}.{b[1]}','from_samples_mm':pa,'to_samples_mm':pb,'from_outline_ids':sorted(ia),'to_outline_ids':sorted(ib),'same_continuous_copper_outline':bool(ia&ib),'limitation':'Same-layer geometric continuity only; no minimum width or current rating implied.'})

    return board,polys,path_checks,zones,tap_ids,digest
