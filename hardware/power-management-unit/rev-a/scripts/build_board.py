"""Build the four-layer engineering board from reviewed components/placements.

Run with KiCad's bundled Python (pcbnew). Routing is a separate, explicit step.
Unplaced components or geometry collisions are reported, never silently omitted.
"""
from collections import defaultdict
from pathlib import Path
import ctypes
import json
import math
import os
import sys
import traceback
import pcbnew as pcb
from sync_nc_nets import sync_nc_nets
from build_schematic import uid, ROOT, CAD, PROJECT, natural


def mm(v):
    return pcb.FromMM(float(v))


def point(x, y):
    return pcb.VECTOR2I(mm(x), mm(y))


def force_exit(code):
    """Avoid the portable Windows pcbnew DLL shutdown deadlock, after flush."""
    sys.stdout.flush()
    sys.stderr.flush()
    if os.name == 'nt':
        kernel = ctypes.windll.kernel32
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        kernel.TerminateProcess(kernel.GetCurrentProcess(), code)
    raise SystemExit(code)


def drawing(board, start, end, layer, width=.2):
    line = pcb.PCB_SHAPE()
    line.SetShape(pcb.SHAPE_T_SEGMENT)
    line.SetStart(point(*start))
    line.SetEnd(point(*end))
    line.SetLayer(layer)
    line.SetWidth(mm(width))
    board.Add(line)


def label(board, text, x, y, size=1.3, layer=pcb.F_SilkS):
    item = pcb.PCB_TEXT(board)
    item.SetText(text)
    item.SetPosition(point(x, y))
    item.SetLayer(layer)
    item.SetTextSize(point(size, size))
    item.SetTextThickness(mm(.18))
    board.Add(item)


def pad_bounds(fp):
    bounds = []
    for pad in fp.Pads():
        box = pad.GetBoundingBox()
        bounds.append((pcb.ToMM(box.GetX()), pcb.ToMM(box.GetY()),
                       pcb.ToMM(box.GetRight()), pcb.ToMM(box.GetBottom())))
    for shape in fp.GraphicalItems():
        if shape.GetLayer() == pcb.F_CrtYd:
            box = shape.GetBoundingBox()
            bounds.append((pcb.ToMM(box.GetX()), pcb.ToMM(box.GetY()),
                           pcb.ToMM(box.GetRight()), pcb.ToMM(box.GetBottom())))
    return (min(v[0] for v in bounds), min(v[1] for v in bounds),
            max(v[2] for v in bounds), max(v[3] for v in bounds))


def overlap(a, b, gap=.25):
    return not (a[2]+gap <= b[0] or b[2]+gap <= a[0] or a[3]+gap <= b[1] or b[3]+gap <= a[1])


def readable_references(board):
    """Place horizontal references in visible free space, retaining F.Fab detail."""
    def bounds(item):
        b = item.GetBoundingBox()
        return tuple(pcb.ToMM(v) for v in (b.GetX(), b.GetY(), b.GetRight(), b.GetBottom()))
    footprints = list(board.GetFootprints())
    pads = [bounds(p) for f in footprints for p in f.Pads() if p.GetLayerSet().Contains(pcb.F_Cu)]
    outlines = [bounds(s) for f in footprints for s in f.GraphicalItems() if s.GetLayer() == pcb.F_SilkS]
    occupied = []
    offsets=sorted((dx*dx+dy*dy,dx,dy) for dy in range(-50,51) for dx in range(-50,51))
    for f in sorted(footprints, key=lambda f: (not f.GetReference().startswith(('J','Q','U')), natural(f.GetReference()))):
        field = f.Reference()
        field.SetVisible(True)
        field.SetLayer(pcb.F_SilkS)
        field.SetTextAngle(pcb.EDA_ANGLE(0, pcb.DEGREES_T))
        field.SetTextSize(point(1,1))
        field.SetTextThickness(mm(.15))
        x, y = pcb.ToMM(f.GetPosition().x), pcb.ToMM(f.GetPosition().y)
        body = pad_bounds(f)
        chosen=None
        for _,dx,dy in offsets:
            px, py = x+dx*.5, y+dy*.5
            field.SetPosition(point(px,py))
            box = bounds(field)
            if box[0]<1 or box[1]<1 or box[2]>359 or box[3]>299:
                continue
            if overlap(box,body,.1) or any(overlap(box,b,.2) for b in pads+outlines+occupied):
                continue
            chosen=(px,py,box)
            break
        if chosen is None:
            raise RuntimeError('No visible reference position for '+f.GetReference())
        px,py,box=chosen
        field.SetPosition(point(px,py))
        occupied.append(box)


def read_placements():
    result = {}
    for path in sorted((ROOT/'design').glob('placement-*.json')):
        if path.name == 'placement-audit.json':
            continue
        data = json.loads(path.read_text(encoding='utf-8'))
        entries = data.get('placements', data)
        for ref, entry in entries.items():
            if ref == 'metadata':
                continue
            if isinstance(entry, dict):
                result[ref] = (entry['x'], entry['y'], entry.get('rotation', entry.get('angle', 0)))
            else:
                result[ref] = tuple(entry[:3])
    return result


def main():
    data = json.loads((ROOT/'design'/'assembled-parts.json').read_text(encoding='utf-8'))
    parts = [c for c in data['components'] if c.get('on_board', True)]
    board = pcb.BOARD()
    board.SetCopperLayerCount(4)
    settings = board.GetDesignSettings()
    settings.m_MinClearance = mm(.15)
    settings.m_MinThroughDrill = mm(.2)
    settings.m_TrackMinWidth = mm(.2)
    settings.SetBoardThickness(mm(1.6))
    settings.m_CopperEdgeClearance = mm(.5)
    settings.m_HoleClearance = mm(.25)
    tb = board.GetTitleBlock()
    tb.SetTitle('HomeMy PMU - REVISION A ENGINEERING PROTOTYPE')
    tb.SetRevision('A')
    tb.SetDate('2026-09-10')
    tb.SetCompany('HomeMy')
    tb.SetComment(0, 'rev_a_engineering_prototype: true')
    tb.SetComment(1, 'rev_b_production: false')
    tb.SetComment(2, '360 x 300mm provisional laboratory mechanics. See release.json.')
    net_names = sorted({n for c in parts for n in c['pins'].values() if n})
    nets = {}
    for i, name in enumerate(net_names, 1):
        net = pcb.NETINFO_ITEM(board, name, i)
        board.Add(net)
        nets[name] = net
    placements = read_placements()
    fixed = {
        'J1': (15,45,0), 'J2': (15,115,0),
        'J3': (220,20,0), 'J4': (220,115,0), 'J5': (250,20,0), 'J6': (250,115,0),
        'RSH1': (30,45,0), 'RSH2': (120,45,0),
        'Q1': (55,25,90), 'Q2': (55,50,90), 'Q3': (55,75,90),
        'Q4': (85,25,270), 'Q5': (85,50,270), 'Q6': (85,75,270),
        'Q7': (150,30,90), 'Q8': (150,65,90), 'Q9': (180,30,270), 'Q10': (180,65,270),
        'U1': (70,96,0), 'U2': (165,96,0),
        'C3': (42,142,0), 'C10': (165,142,0),
        'U3': (42,176,0), 'U4': (90,176,0),
        'U11': (25,75,0), 'U10': (325,280,180),
        'NT1': (205,127,0), 'NT2': (235,127,0), 'NT3': (285,122,0),
        'NT4': (315,122,0), 'NT5': (35,122,0), 'NT6': (65,122,0),
        'NT7': (345,122,0), 'NT8': (95,122,0), 'NT9': (120,128,0), 'NT10': (299,44,0),
    }
    fixed.update(placements)
    fps, comps, occupancy = {}, {}, {}
    for c in parts:
        ref = c['ref']
        lib, name = c['footprint'].split(':')
        fp = pcb.FootprintLoad(str(CAD/'libraries'/(lib+'.pretty')), name)
        if not fp:
            raise RuntimeError(f'{ref}: cannot load {c["footprint"]}')
        board.Add(fp)
        fp.SetReference(ref)
        fp.SetValue(c['value'])
        fp.SetFPIDAsString(c['footprint'])
        fp.SetFields({'MPN':c.get('mpn',''),'Manufacturer':c.get('manufacturer',''),
                      'Datasheet':c.get('source_url',''),
                      'rev_a_engineering_prototype':'true','rev_b_production':'false'})
        for field in fp.GetFields():
            if field.GetName() not in ['Reference','Value']:
                field.SetVisible(False)
                field.SetLayer(pcb.F_Fab)
        fp.Value().SetVisible(False)
        fp.SetDNP(bool(c.get('dnp', False)))
        if not c.get('in_bom', True):
            fp.SetAttributes(fp.GetAttributes() | pcb.FP_EXCLUDE_FROM_BOM | pcb.FP_EXCLUDE_FROM_POS_FILES)
        path = pcb.KIID_PATH()
        for token in [uid('root'), uid('sheet:'+c['effective_sheet']), uid('component:'+ref)]:
            path.push_back(pcb.KIID(token))
        fp.SetPath(path)
        for pad in fp.Pads():
            net_name = c['pins'].get(pad.GetNumber())
            if net_name:
                pad.SetNet(nets[net_name])
            else:
                pad.SetNetCode(0)
        fps[ref], comps[ref] = fp, c
        if ref in fixed:
            x, y, angle = fixed[ref]
            fp.SetPosition(point(x, y))
            fp.SetOrientationDegrees(angle)
            occupancy[ref] = pad_bounds(fp)
    # Only references omitted from the reviewed placement records are packed by
    # this fallback. They are recorded for a subsequent physical placement review.
    areas = {
        '02': (12,92,110,155), '03': (125,92,215,155),
        '04': (230,20,347,152), '05': (15,160,120,198),
        '06a': (15,205,145,255), '06b': (150,160,245,245),
        '06c': (260,230,345,290), '07': (260,165,345,220),
        '08': (15,260,140,287), '09': (5,155,25,287),
    }
    fallback = []
    for c in sorted(parts, key=lambda c: (-len(c['pins']), natural(c['ref']))):
        ref = c['ref']
        if ref in occupancy:
            continue
        fp = fps[ref]
        sheet = c['sheet'].split('_')[0]
        area = areas.get(sheet, areas.get(sheet[:2], (150,250,290,288)))
        if ref.startswith('TP'):
            net = c['pins']['1']
            nearby = [fps[r].GetPosition() for r, co in comps.items() if r in occupancy and net in co['pins'].values()]
            if nearby:
                tx = sum(pcb.ToMM(p.x) for p in nearby)/len(nearby)
                ty = sum(pcb.ToMM(p.y) for p in nearby)/len(nearby)
                area = (max(8,tx-15), max(8,ty-15), min(352,tx+15), min(292,ty+15))
        choices = []
        for y in range(math.ceil(area[1]), math.floor(area[3]), 2):
            for x in range(math.ceil(area[0]), math.floor(area[2]), 2):
                fp.SetPosition(point(x,y))
                bb = pad_bounds(fp)
                if any(overlap(bb, b) for b in occupancy.values()):
                    continue
                if ref.startswith('TP') and any(overlap(bb,b) for b in
                    [(8,110,355,131),(40,15,50,85),(64,15,76,85),(96,15,108,85),
                     (132,20,144,78),(160,20,172,78),(195,15,207,85)]):
                    continue
                if bb[0] < 4 or bb[1] < 4 or bb[2] > 356 or bb[3] > 295:
                    continue
                choices.append(((x-(area[0]+area[2])/2)**2+(y-(area[1]+area[3])/2)**2, x, y, bb))
        if not choices:
            raise RuntimeError(f'No collision-free placement available for {ref} in {area}')
        _, x, y, bb = min(choices)
        fp.SetPosition(point(x,y))
        occupancy[ref] = bb
        fallback.append(ref)
    for i, (x,y) in enumerate([(8,8),(352,8),(292,292),(8,292)],1):
        fp = pcb.FootprintLoad(str(CAD/'libraries'/'MountingHole.pretty'),'MountingHole_3.2mm_M3')
        if fp:
            fp.SetReference(f'H{i}')
            fp.SetAttributes(fp.GetAttributes() | pcb.FP_BOARD_ONLY | pcb.FP_EXCLUDE_FROM_BOM | pcb.FP_EXCLUDE_FROM_POS_FILES)
            fp.SetPosition(point(x,y))
            board.Add(fp)
    for start, end in [((0,0),(360,0)),((360,0),(360,300)),((360,300),(0,300)),((0,300),(0,0))]:
        drawing(board,start,end,pcb.Edge_Cuts,.05)
    label(board,'HOMEMY PMU - REV A ENGINEERING PROTOTYPE',180,5,2)
    label(board,'MOTION DEFAULT OFF / PRODUCTION RELEASE FALSE',180,296,1.5)
    readable_references(board)
    # Block copper beneath and around the module antenna. The official module
    # footprint also contains the manufacturer's all-layer antenna keep-out.
    collisions=[]
    names=list(occupancy)
    for i,a in enumerate(names):
        for b in names[i+1:]:
            if overlap(occupancy[a],occupancy[b],0):
                collisions.append([a,b])
    outfile=CAD/(PROJECT+'.kicad_pcb')
    nc_sync=sync_nc_nets(board,parts)
    print(f'Assigned {nc_sync["singleton_nc_net_count"]} authoritative singleton NC net names.',flush=True)
    board.BuildConnectivity()
    pcb.SaveBoard(str(outfile),board)
    actual={r:{'x':pcb.ToMM(f.GetPosition().x),'y':pcb.ToMM(f.GetPosition().y),'rotation':f.GetOrientationDegrees(),
               'bounds_mm':occupancy[r]} for r,f in fps.items()}
    (ROOT/'design'/'placement-audit.json').write_text(json.dumps({
        'rev_a_engineering_prototype':True,'rev_b_production':False,
        'outline_mm':[360,300],'unreviewed_fallback_placements':fallback,
        'courtyard_or_pad_overlaps':collisions,'placements':actual},indent=2),encoding='utf-8')
    print(f'Created {outfile.name}: {len(parts)} footprints, {len(collisions)} placement overlaps, {len(fallback)} fallback placements; NOT routed.',flush=True)


if __name__ == '__main__':
    try:
        main()
    except BaseException:
        traceback.print_exc()
        force_exit(1)
    force_exit(0)
