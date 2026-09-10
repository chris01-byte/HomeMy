"""Read-only native filled-copper analysis; never fills or saves the PCB."""
from pathlib import Path
import sys,json,math,hashlib,collections,traceback
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import pcbnew as pcb
from build_board import force_exit,point,mm

def main():
    filename=ROOT/'kicad'/'HomeMy_PMU_RevA.kicad_pcb'
    digest=hashlib.sha256(filename.read_bytes()).hexdigest()
    board=pcb.LoadBoard(str(filename));board.BuildConnectivity();cn=board.GetConnectivity()
    fps={f.GetReference():f for f in board.GetFootprints()}
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
    for net,layer,a,b in [
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
    ]:
        pa,pb=pad_samples(*a),pad_samples(*b)
        ia,ib=outline_ids(net,layer,pa),outline_ids(net,layer,pb)
        path_checks.append({'net':net,'layer':board.GetLayerName(layer),'from_pad':f'{a[0]}.{a[1]}','to_pad':f'{b[0]}.{b[1]}','from_samples_mm':pa,'to_samples_mm':pb,'from_outline_ids':sorted(ia),'to_outline_ids':sorted(ib),'same_continuous_copper_outline':bool(ia&ib),'limitation':'Same-layer geometric continuity only; no minimum width or current rating implied.'})

    def scan(net,layer,a,b,label):
        q=polys.get((net,layer));length=math.dist(a,b);step=.02;n=max(1,math.ceil(length/step));actual=length/n
        intervals=[];begin=None
        for i in range(n+1):
            x=a[0]+(b[0]-a[0])*i/n;y=a[1]+(b[1]-a[1])*i/n
            hit=q is not None and q.Contains(point(x,y),-1,0,True)
            if hit and begin is None:begin=i
            if begin is not None and (not hit or i==n):
                end=i if not hit else i+1
                intervals.append([round(begin*actual,4),round(min(length,end*actual),4)])
                begin=None
        widths=[round(z-y,4) for y,z in intervals]
        return {'label':label,'net':net,'layer':board.GetLayerName(layer),'line_from_mm':a,'line_to_mm':b,'step_mm':actual,'filled_intervals_distance_mm':intervals,'continuous_widths_mm':widths,'total_copper_width_mm':round(sum(widths),4),'note':'Fixed cross-section, not global minimum or thermal/current capacity proof.'}
    scans=[]
    cases=[
      ('BATT_FUSED_P',(22,42.9),(22,49),'RSH1 input approach'),
      ('BATT_SENSED_P',(35.5,42.9),(35.5,49),'RSH1 output approach'),
      ('SYS_BUS_P',(112,42.9),(112,49),'RSH2 input approach'),
      ('MOTION_SENSED_P',(126,42.9),(126,49),'RSH2 output approach'),
      ('MAIN_COMMON',(63,19.4),(63,28.6),'Q1 source outside lead bank'),
      ('MAIN_COMMON',(77,21.4),(77,30.6),'Q4 source outside lead bank'),
      ('MOTION_COMMON',(158,24.4),(158,33.6),'Q7 source outside lead bank'),
      ('MOTION_COMMON',(172,26.4),(172,35.6),'Q9 source outside lead bank'),
      ('MOTION_BUS_P',(260,10),(260,34),'Arm positive top rail'),
      ('MOTION_BUS_P',(330,17),(330,23),'Right positive rail at junction'),
      ('BATT_N',(110,108),(110,134),'Star crossed by SYS feed'),
      ('BATT_N',(220,104),(220,136),'Star under left arm terminal'),
      ('BATT_N',(250,104),(250,136),'Star under right arm terminal'),
      ('ARM_L_N',(207,109),(207,132),'Left arm return approaching NT1'),
      ('ARM_R_N',(237,109),(237,132),'Right arm return approaching NT2'),
      ('CHOPPER_N',(290,40),(302,40),'Q40 source below bank'),
      ('CHOPPER_N',(300,20),(300,27),'Cap negative trunk near C312 positive'),
      ('CHOPPER_N',(338,80),(346,80),'Chopper return spine'),
      ('CHOP_DRAIN',(311,29),(311,41),'Q40 drain exit'),
      ('CHOP_DRAIN',(345,27),(345,33),'Chopper drain connector neck'),
    ]
    for name,a,b,label in cases:
        for layer in [pcb.F_Cu,pcb.B_Cu]:scans.append(scan(name,layer,a,b,label))
    # Sample every power FET bank, including both source and drain exits.
    for number in range(1,11):
        f=fps[f'Q{number}']; cx=pcb.ToMM(f.GetPosition().x);cy=pcb.ToMM(f.GetPosition().y)
        pp={p.GetNumber():p for p in f.Pads()}
        source_right=pcb.ToMM(pp['2'].GetPosition().x)>cx
        sx=cx+(8 if source_right else -8)
        sy0=cy+(-5.6 if source_right else -3.6)
        dx=cx+(-8 if source_right else 8)
        for layer in [pcb.F_Cu,pcb.B_Cu]:
            scans.append(scan(pp['2'].GetNetname(),layer,(sx,sy0),(sx,sy0+9.2),f'Q{number} source bank exit'))
            scans.append(scan(pp['7'].GetNetname(),layer,(dx,cy-5.6),(dx,cy+5.6),f'Q{number} drain bank exit'))
    for name,layer,a,b,label in [
      ('DRIVE_N',pcb.F_Cu,(328,80),(336,80),'Drive return vertical'),
      ('LIFT_N',pcb.In1_Cu,(340,100),(348,100),'Lift return inner 1'),
      ('LIFT_N',pcb.In2_Cu,(340,100),(348,100),'Lift return inner 2'),
      ('V5V',pcb.B_Cu,(45,256),(45,264),'LED positive trunk'),
      ('LOGIC_5V_N',pcb.B_Cu,(141,255),(149,255),'LED return trunk')]:
        scans.append(scan(name,layer,a,b,label))

    checks=[]
    for ref in ['J'+str(i) for i in range(1,13)]+['Q'+str(i) for i in range(1,11)]+['Q40','RSH1','RSH2','C312','C313']+['NT'+str(i) for i in range(1,9)]+['BC'+str(i) for i in range(1,16)]:
        f=fps[ref]
        for p in f.Pads():
            if p.GetNetname() not in selected:continue
            cp=cn.GetConnectedPads(p)
            containing=[]
            if p.GetDrillSize().x==0:
                for layer in layers:
                    if not p.IsOnLayer(layer):continue
                    shape=polys.get((p.GetNetname(),layer))
                    if shape is None:continue
                    for i in range(shape.OutlineCount()):
                        if not shape.Contains(p.GetPosition(),i,0,True):continue
                        pts=[shape.COutline(i).CPoint(k) for k in range(shape.COutline(i).PointCount())]
                        def area(chain):
                            v=[chain.CPoint(k) for k in range(chain.PointCount())]
                            return abs(sum(a.x*b.y-b.x*a.y for a,b in zip(v,v[1:]+v[:1])))/2e12
                        connected_area=area(shape.COutline(i))-sum(area(shape.CHole(i,h)) for h in range(shape.HoleCount(i)))
                        containing.append({'layer':board.GetLayerName(layer),'outline':i,'area_mm2_excluding_holes':connected_area,'bbox_mm':[pcb.ToMM(min(v.x for v in pts)),pcb.ToMM(min(v.y for v in pts)),pcb.ToMM(max(v.x for v in pts)),pcb.ToMM(max(v.y for v in pts))]})
            checks.append({'ref':ref,'pad':p.GetNumber(),'net':p.GetNetname(),
                           'pad_center_mm':[pcb.ToMM(p.GetPosition().x),pcb.ToMM(p.GetPosition().y)],
                           'layers_connected':[board.GetLayerName(l) for l in layers if p.IsOnLayer(l) and cn.IsConnectedOnLayer(p,l)],
                           'containing_copper_outlines':containing,
                           'connected_pad_labels':sorted(set(f'{a.GetParentFootprint().GetReference()}.{a.GetNumber()}' for a in cp))})
    vias=[]
    for t in board.GetTracks():
        if isinstance(t,pcb.PCB_VIA) and t.GetNetname() in selected:
            vias.append({'net':t.GetNetname(),'x':pcb.ToMM(t.GetPosition().x),'y':pcb.ToMM(t.GetPosition().y),'drill_mm':pcb.ToMM(t.GetDrillValue()),'layers_connected':[board.GetLayerName(l) for l in layers if t.IsOnLayer(l) and cn.IsConnectedOnLayer(t,l)]})
    field=json.loads((ROOT/'design'/'via-field-counts.json').read_text())
    via_calcs=[]
    for name,count in field['counts'].items():
        for temp in [20,100]:
            rho=1.724e-8*(1+.00393*(temp-20));area=math.pi*.4*.025
            R=rho*1.6/(area*count)*1000
            via_calcs.append({'net':name,'count':count,'temperature_C':temp,'resistance_ohm':R,'loss50A_W':2500*R,'loss60A_W':3600*R})
    out={'metadata':{'rev_a_engineering_prototype':True,'rev_b_production':False},'board_sha256':digest,'board_unchanged_during_review':hashlib.sha256(filename.read_bytes()).hexdigest()==digest,
         'review_status':'Engineering snapshot; final release is not established by this geometry analysis.',
         'method':'Native saved filled polygons plus effective pad/track copper, own drill interiors subtracted. No refilling or saving. Fixed 0.02 mm cross-sections.',
         'limitations':['Cross-sections are local samples, not global minimum cuts.','Native per-layer pad connection flags are local adjacency checks; they do not prove connection to the complete net. No external bars are added to the native copper model.','Per-field via resistance assumes that all counted barrels share current uniformly; a field total does not establish a local transfer rating.','No resistance, temperature, SOA or pressfit measurement was performed.'],
         'zones':zones,'cross_sections':scans,'same_layer_path_checks':path_checks,'power_pad_connectivity':checks,'vias':vias,
         'via_field_source':field,'via_field_ideal_calculations':via_calcs,
         'via_formula':'R = rho(T) * L / (N * pi * d * t); d = 0.4 mm, t = 0.025 mm, L = 1.6 mm; rho20 = 1.724e-8 ohm m, alpha = 0.00393/K'}
    (ROOT/'evidence'/'filled-power-copper-review.json').write_text(json.dumps(out,indent=2)+'\n',encoding='utf-8')
    (ROOT/'evidence'/'filled-power-polygons.json').write_text(json.dumps([
        {'net':n,'layer':board.GetLayerName(l),'outlines':[
            {'outer':[[pcb.ToMM(q.COutline(i).CPoint(k).x),pcb.ToMM(q.COutline(i).CPoint(k).y)] for k in range(q.COutline(i).PointCount())],
             'holes':[[[pcb.ToMM(q.CHole(i,j).CPoint(k).x),pcb.ToMM(q.CHole(i,j).CPoint(k).y)] for k in range(q.CHole(i,j).PointCount())] for j in range(q.HoleCount(i))]} for i in range(q.OutlineCount())]} for(n,l),q in polys.items()]),encoding='utf-8')
    print(json.dumps({'board_sha256':digest,'unchanged':out['board_unchanged_during_review'],'padchecks':len(checks),'vias':len(vias),'crosssections':len(scans)},indent=2),flush=True)

if __name__=='__main__':
    try:main()
    except BaseException:
        traceback.print_exc();force_exit(1)
    force_exit(0)
