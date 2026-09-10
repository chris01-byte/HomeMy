"""Prepare the lower-power copper, without loading, filling or saving a board.

Call once on the freshly placed board, before signal autorouting.  Outer layers
are specified as 70 um copper.  Nominal corridor widths are NOT a measured
thermal rating: inspect the filled copper and run native DRC after integration.
The caller must keep foreign stitching vias outside the returned reservations.
"""
import math
import pcbnew as pcb


def _mm(v):
    return pcb.FromMM(float(v))


def _point(x, y):
    return pcb.VECTOR2I(_mm(x), _mm(y))


def _xy(p):
    return (pcb.ToMM(p.x), pcb.ToMM(p.y))


def prepare_lower_power(board):
    """Add real locked copper/transfer vias; return a reviewable route manifest.

    Does not move footprints, edit net assignments, fill zones or save files.
    Main SYS/BATT planes belong to the caller.  The SYS entry overlaps the main
    plane at (110,84).  Only F.Cu crosses the y109..133 star band; its B.Cu plane
    and insulated reinforcement remain continuous.  Return branches meet their
    own NT pads.  No LED power return is connected to LOGIC_GND or NT9 here.
    """
    if any(z.GetZoneName().startswith('LOWER_POWER/') for z in board.Zones()):
        raise RuntimeError('Lower-power preparation already exists on this board')
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    zone_groups = {}
    zone_clearances = {}
    manifest = {
        'rev_a_engineering_prototype': True, 'rev_b_production': False,
        'current_envelope_A': {'SYS_combined': 4.0, 'PC_input': 2.5,
                               'logic_buck_input': 1.5, 'V5V_total': 5.0},
        'outer_copper_um': 70, 'via_drill_mm': .4, 'via_diameter_mm': .8,
        'minimum_hole_plating_um': 25, 'routes': [], 'reservations': [],
        'tracks': 0, 'vias': 0, 'zones': 0, 'pad_clearance_candidates': [],
        'limitations': [
            'Nominal width requires filled-copper/neck inspection and native DRC.',
            'Temperature rise and connector/contact resistance require bench measurement.',
            'SYS crossing requires insulated star-bar underside; solder mask alone is not credited.',
            'External 5 V converter remains subject to its separate validation gate.'],
    }

    def pad(ref, number, net):
        candidates = [p for p in fps[ref].Pads() if p.GetNumber() == str(number)]
        if len(candidates) != 1 or candidates[0].GetNetname() != net:
            raise RuntimeError(f'Unexpected pad/net: {ref}.{number}, expected {net}')
        return candidates[0]

    def pos(ref, number, net):
        return _xy(pad(ref, number, net).GetPosition())

    # Gross channels below are placement-specific; fail rather than silently
    # retaining a stale corridor if a connector/IC is moved in another revision.
    expected = {'U3': (40,176), 'U4': (90,176), 'J9': (11,160),
                'J10': (11,188), 'J11': (11,216), 'J18': (110,285),
                'C246': (132,270), 'NT5': (35,122), 'NT6': (65,122),
                'NT8': (95,122), 'U12': (288,242)}
    for ref, target in expected.items():
        if ref not in fps or math.dist(_xy(fps[ref].GetPosition()), target) > .01:
            raise RuntimeError(f'Lower-power placement changed: {ref}; review its corridors')

    def net(name):
        n = board.FindNet(name)
        if n is None or n.GetNetCode() <= 0:
            raise RuntimeError('Missing net '+name)
        return n

    def track(name, points, width, layer):
        for a, b in zip(points, points[1:]):
            if a == b:
                continue
            t = pcb.PCB_TRACK(board)
            t.SetStart(_point(*a)); t.SetEnd(_point(*b))
            t.SetWidth(_mm(width)); t.SetLayer(layer); t.SetNet(net(name))
            t.SetLocked(True); board.Add(t)
            manifest['tracks'] += 1
        manifest['reservations'].append({'net':name,'layer':board.GetLayerName(layer),
                                         'points_mm':points,'width_mm':width,
                                         'foreign_copper_clearance_mm':.5})

    def zone(name, corners, layer, clearance=.3):
        key=(name,layer)
        if key not in zone_groups:
            z = pcb.ZONE(board); z.SetLayer(layer); z.SetNet(net(name))
            z.SetZoneName('LOWER_POWER/'+name)
            z.SetAssignedPriority(20)
            z.SetLocalClearance(_mm(clearance)); z.SetMinThickness(_mm(.2))
            z.SetPadConnection(pcb.ZONE_CONNECTION_FULL)
            z.SetIslandRemovalMode(pcb.ISLAND_REMOVAL_MODE_ALWAYS)
            z.SetLocked(True); zone_groups[key]=z; zone_clearances[key]=clearance
            board.Add(z); manifest['zones'] += 1
        else:
            z=zone_groups[key]
            zone_clearances[key]=min(zone_clearances[key],clearance)
            z.SetLocalClearance(_mm(zone_clearances[key]))
        # One unioned zone per net/layer. Overlapping same-net rectangles left as
        # distinct equal-priority zones trigger real native zones_intersect DRC.
        polygon=pcb.SHAPE_POLY_SET(); polygon.NewOutline()
        for x,y in corners:
            polygon.Append(_mm(x),_mm(y))
        z.Outline().BooleanAdd(polygon)

    def rect(name, x1,y1,x2,y2,layer,clearance=.3):
        zone(name,[(x1,y1),(x2,y1),(x2,y2),(x1,y2)],layer,clearance)

    def corridor(name, points, width, layer, purpose):
        track(name,points,width,layer)
        # Slightly wider poured shoulders, solid connections, no thermal spokes.
        half=width/2+.2
        for a,b in zip(points,points[1:]):
            dx,dy=b[0]-a[0],b[1]-a[1]; length=math.hypot(dx,dy)
            if not length:
                continue
            ux,uy=dx/length,dy/length; nx,ny=-uy*half,ux*half
            aa=(a[0]-ux*half,a[1]-uy*half); bb=(b[0]+ux*half,b[1]+uy*half)
            zone(name,[(aa[0]+nx,aa[1]+ny),(bb[0]+nx,bb[1]+ny),
                       (bb[0]-nx,bb[1]-ny),(aa[0]-nx,aa[1]-ny)],layer)
        manifest['routes'].append({'net':name,'purpose':purpose,
                                  'layer':board.GetLayerName(layer),
                                  'width_mm':width,'points_mm':points})

    def vias(name, points):
        for x,y in points:
            v=pcb.PCB_VIA(board); v.SetViaType(pcb.VIATYPE_THROUGH)
            v.SetLayerPair(pcb.F_Cu,pcb.B_Cu); v.SetPosition(_point(x,y))
            v.SetWidth(_mm(.8)); v.SetDrill(_mm(.4)); v.SetNet(net(name))
            v.SetLocked(True); board.Add(v); manifest['vias'] += 1

    def transfer(name, center, columns=3, rows=3):
        x,y=center
        points=[(x+(i-(columns-1)/2)*1.1,y+(j-(rows-1)/2)*1.1)
                for i in range(columns) for j in range(rows)]
        vias(name,points)
        hx=(columns-1)*.55+.65; hy=(rows-1)*.55+.65
        for layer in (pcb.F_Cu,pcb.B_Cu):
            rect(name,x-hx,y-hy,x+hx,y+hy,layer)
            # Explicit spines make every via a two-layer connection even before
            # pouring; no current-sharing claim depends on a floating island.
            for j in range(rows):
                yy=y+(j-(rows-1)/2)*1.1
                track(name,[(points[0][0],yy),(points[-1][0],yy)],.8,layer)
            track(name,[(x,points[0][1]),(x,points[-1][1])],.8,layer)

    # Main switched battery feed; four amps combined at the chosen eFuse limits.
    corridor('SYS_BUS_P',[(110,84),(110,155),(38,155)],4,pcb.F_Cu,
             'Main SYS plane to the two independent converter eFuses')
    corridor('SYS_BUS_P',[(38,155),(38,165.5)],4,pcb.F_Cu,'PC eFuse approach')
    corridor('SYS_BUS_P',[(87.3,155),(87.3,165.5)],4,pcb.F_Cu,'Logic eFuse approach')
    track('SYS_BUS_P',[(38,165.5),(38,171.8),(36.8,173)],1.25,pcb.F_Cu)
    track('SYS_BUS_P',[(87.3,165.5),(87.3,172),(86.8,173)],.8,pcb.F_Cu)

    # Short manufacturer-pitch pin fanouts. Input
    # pin 5 is also IN; pins 3/4 are genuinely NC and are never shorted together.
    for ref,offset,outnet,cap in [('U3',0,'PC_BUCK_IN_P','C22'),
                                ('U4',50,'LOGIC_BUCK_IN_P','C27')]:
        x=36.8+offset
        for pin in ('1','2','5'):
            a=pos(ref,pin,'SYS_BUS_P')
            track('SYS_BUS_P',[a,(x,a[1])],.25,pcb.F_Cu)
        rect('SYS_BUS_P',x-.5,173,x+.6,177.05,pcb.F_Cu,.25)
        track('SYS_BUS_P',[(x,173),(x,176.75)],.8,pcb.F_Cu)
        outx=43.2+offset
        for pin in ('17','18'):
            a=pos(ref,pin,outnet)
            track(outnet,[a,(outx,a[1])],.25,pcb.F_Cu)
        rect(outnet,outx-.6,172.2,outx+1.8,175.4,pcb.F_Cu,.25)
        rect(outnet,outx-.7,172.1,outx+1.8,175.5,pcb.B_Cu)
        vias(outnet,[(outx,y) for y in (172.8,173.8,174.8)]+[(outx+1.1,174.8)])
        for layer in (pcb.F_Cu,pcb.B_Cu):
            track(outnet,[(outx,172.8),(outx,174.8),(outx+1.1,174.8)],.8,layer)
        a=pos(cap,'1',outnet)
        track(outnet,[a,(outx,a[1])],.6,pcb.F_Cu)

    corridor('PC_BUCK_IN_P',[(43.2,174.8),(43.2,160),pos('J9','1','PC_BUCK_IN_P')],
             4,pcb.B_Cu,'2.5 A protected PC-converter feed')
    corridor('LOGIC_BUCK_IN_P',[(93.2,174.8),(93.2,188),pos('J10','1','LOGIC_BUCK_IN_P')],
             4,pcb.B_Cu,'1.5 A protected 5 V converter input')
    corridor('PC_N',[pos('NT5','1','PC_N'),(22,137),(22,165.08),pos('J9','2','PC_N')],
             4,pcb.F_Cu,'PC return directly to NT5')
    corridor('LOGIC_BUCK_N',[pos('NT6','1','LOGIC_BUCK_N'),(60,143)],
             4,pcb.F_Cu,'Logic-buck return leaves star on F.Cu')
    transfer('LOGIC_BUCK_N',(60,143),3,2)
    corridor('LOGIC_BUCK_N',[(60,143),(60,163)],4,pcb.B_Cu,'Cross below SYS branch')
    transfer('LOGIC_BUCK_N',(60,163),3,2)
    corridor('LOGIC_BUCK_N',[(60,163),(60,193.08),pos('J10','2','LOGIC_BUCK_N')],
             4,pcb.F_Cu,'Logic-buck return connector')

    # 5 V power return is its own copper network. The strip/capacitor loop closes
    # to J11.2 locally, not through NT9 or the quiet LOGIC_GND plane.
    corridor('LOGIC_5V_N',[pos('NT8','1','LOGIC_5V_N'),(90,139)],6,pcb.F_Cu,
             '5 V return star connection via NT8 only')
    transfer('LOGIC_5V_N',(90,139))
    corridor('LOGIC_5V_N',[(90,139),(120,139),(120,221.08)],6,pcb.B_Cu,
             '5 V return stem')
    corridor('LOGIC_5V_N',[pos('J11','2','LOGIC_5V_N'),(145,221.08),(145,289),
                           (120.16,289),pos('J18','3','LOGIC_5V_N')],6,pcb.B_Cu,
             '5 A LED return directly to the converter-return connector')
    corridor('LOGIC_5V_N',[pos('C246','2','LOGIC_5V_N'),(145,270)],4,pcb.B_Cu,
             'Local LED bulk-capacitor return')

    # Move to B.Cu below the return trunk, avoiding a same-layer crossing at J11.
    # The 15.7 mm entry neck passes between J11.2 and R201; it is 2 mm,
    # 70 um copper (about 1.94 mOhm / 49 mW at 5 A and 20 C by bulk rho).
    corridor('V5V',[pos('J11','1','V5V'),(14.2,216),(14.2,228.5)],2,pcb.F_Cu,
             'Short 5 A input neck between J11 return and AON feed resistor')
    transfer('V5V',(14.2,228.5))
    corridor('V5V',[(14.2,228.5),(24,238.3),(24,260),(110,260),pos('J18','1','V5V')],6,pcb.B_Cu,
             '5 A LED supply trunk')
    corridor('V5V',[(110,270),pos('C246','1','V5V')],4,pcb.B_Cu,
             'Local LED bulk-capacitor supply')
    # Dedicated 1 A logic feeder; no thin signal route is credited for U12 load.
    corridor('V5V',[(110,260),(110,254),(138,254)],2,pcb.B_Cu,
             'Logic branch before LED return crossing')
    transfer('V5V',(138,254),3,2)
    corridor('V5V',[(138,254),(152,254)],2,pcb.F_Cu,
             'Logic feed crosses the uninterrupted LED return on F.Cu')
    transfer('V5V',(152,254),3,2)
    corridor('V5V',[(152,254),(279,254),(283.5,247)],2,pcb.B_Cu,
             'At most 1 A 3.3 V regulator input branch')
    transfer('V5V',(283.5,247),2,3)
    track('V5V',[(283.5,247),(284.85,247),pos('U12','3','V5V')],1,pcb.F_Cu)
    track('V5V',[pos('C207','1','V5V'),pos('U12','3','V5V')],1,pcb.F_Cu)

    for z in zone_groups.values():
        union=z.Outline().CloneDropTriangulation()
        # Separate disjoint regions after Boolean union. Each resulting zone
        # has one connected outline, rather than encoding unrelated islands
        # inside a single ZONE object; their geometry and net remain unchanged.
        for i in range(union.OutlineCount()):
            target=z if i==0 else pcb.Cast_to_ZONE(z.Duplicate(False))
            if i:
                board.Add(target); manifest['zones'] += 1
            target.Outline().RemoveAllContours()
            target.Outline().AddOutline(union.COutline(i))
            for j in range(union.HoleCount(i)):
                target.Outline().AddHole(union.CHole(i,j),0)
            target.CacheBoundingBox(); target.SetNeedRefill(True)
    board.BuildConnectivity()
    return manifest
