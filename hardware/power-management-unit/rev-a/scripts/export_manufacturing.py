"""Export the current native board as a NON-RELEASED engineering preview.

Run with the KiCad-bundled Python through run_tool.py. This script never saves,
fills, routes or otherwise edits the input board. Successful coverage validation
only establishes that the files correspond to the board/BOM snapshot; it does
not establish electrical safety, DRC acceptance or permission to order.
"""
import argparse
import csv
import ctypes
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sys
import traceback

import pcbnew as pcb


ROOT = Path(__file__).resolve().parents[1]
STATE = 'engineering_review_not_order_release'
REQUIRED_LAYERS = [
    ('F.Cu', pcb.F_Cu), ('In1.Cu', pcb.In1_Cu), ('In2.Cu', pcb.In2_Cu),
    ('B.Cu', pcb.B_Cu), ('F.Mask', pcb.F_Mask), ('B.Mask', pcb.B_Mask),
    ('F.SilkS', pcb.F_SilkS), ('B.SilkS', pcb.B_SilkS),
    ('F.Paste', pcb.F_Paste), ('B.Paste', pcb.B_Paste), ('Edge.Cuts', pcb.Edge_Cuts),
]


def force_exit(code):
    """Avoid the known local wx/DLL shutdown hang after all outputs are closed."""
    sys.stdout.flush()
    sys.stderr.flush()
    if os.name == 'nt':
        kernel = ctypes.windll.kernel32
        kernel.GetCurrentProcess.restype = ctypes.c_void_p
        kernel.TerminateProcess.argtypes = [ctypes.c_void_p, ctypes.c_uint]
        kernel.TerminateProcess(kernel.GetCurrentProcess(), code)
    raise SystemExit(code)


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def natural(value):
    return [int(x) if x.isdigit() else x for x in re.split(r'(\d+)', value)]


def relative(path, base=ROOT):
    try:
        return Path(path).resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return Path(path).resolve().as_posix()


def json_write(path, data):
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def csv_write(path, rows, fields):
    with path.open('w', encoding='utf-8-sig', newline='') as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)
    with path.open(encoding='utf-8-sig', newline='') as handle:
        saved = list(csv.DictReader(handle))
    if len(saved) != len(rows):
        raise RuntimeError(f'CSV readback count differs: {path.name}')


def plot(board, directory, suffix, layer_ids, fmt, assembly=False):
    controller = pcb.PLOT_CONTROLLER(board)
    options = controller.GetPlotOptions()
    options.SetOutputDirectory(directory.as_posix())
    options.SetFormat(fmt)
    options.SetScale(1.0)
    options.SetAutoScale(False)
    options.SetMirror(False)
    options.SetNegative(False)
    options.SetUseAuxOrigin(False)
    options.SetPlotFrameRef(False)
    options.SetPlotValue(False)
    options.SetPlotReference(True)
    options.SetPlotFPText(True)
    options.SetDrillMarksType(pcb.DRILL_MARKS_NO_DRILL_SHAPE)
    options.SetSubtractMaskFromSilk(True)
    options.SetUseGerberX2format(True)
    options.SetIncludeGerberNetlistInfo(True)
    options.SetUseGerberProtelExtensions(False)
    options.SetGerberPrecision(6)
    options.SetCreateGerberJobFile(False)
    options.SetPlotOnAllLayersSequence(pcb.LSEQ())
    if assembly:
        # Native SVG page-size mode: 0 drawing sheet, 1 page, 2 board area.
        options.SetSvgFitPageToBoard(2)
        options.SetSvgPrecision(6)
        options.SetBlackAndWhite(True)
        options.SetSketchPadsOnFabLayers(True)
        options.SetHideDNPFPsOnFabLayers(False)
        options.SetCrossoutDNPFPsOnFabLayers(True)
    controller.SetLayer(layer_ids[0])
    if not controller.OpenPlotfile(suffix, fmt, 'REV A ENGINEERING PREVIEW / NOT ORDER RELEASE'):
        raise RuntimeError(f'Cannot open native plot: {suffix}')
    filename = Path(controller.GetPlotFileName())
    try:
        if len(layer_ids) == 1:
            success = controller.PlotLayer()
        else:
            sequence = pcb.LSEQ()
            for layer in layer_ids:
                sequence.push_back(layer)
            success = controller.PlotLayers(sequence)
        if not success:
            raise RuntimeError(f'Native plot failed: {suffix}')
    finally:
        controller.ClosePlot()
    if assembly and fmt==pcb.PLOT_FORMAT_SVG:
        # PLOT_CONTROLLER in this portable build retains the sheet viewport
        # despite page-size mode 2. Fit only the SVG viewport; native geometry,
        # coordinates, scale, strokes and layer primitives remain untouched.
        bounds=board.GetBoardEdgesBoundingBox()
        x=pcb.ToMM(bounds.GetX())-1;y=pcb.ToMM(bounds.GetY())-1
        w=pcb.ToMM(bounds.GetWidth())+2;h=pcb.ToMM(bounds.GetHeight())+2
        data=filename.read_text(encoding='utf-8')
        fitted,count=re.subn(r'width="[^"]+" height="[^"]+" viewBox="[^"]+"',
            f'width="{w:.6f}mm" height="{h:.6f}mm" viewBox="{x:.6f} {y:.6f} {w:.6f} {h:.6f}"',data,count=1)
        if count!=1:
            raise RuntimeError('Native SVG viewport was not recognized: '+str(filename))
        filename.write_text(fitted,encoding='utf-8')
    return filename


def main():
    global STATE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--board', type=Path, default=ROOT/'kicad/HomeMy_PMU_RevA.kicad_pcb')
    parser.add_argument('--bom', type=Path, default=ROOT/'manufacturing/REV_A_BOM.json')
    parser.add_argument('--output', type=Path, default=ROOT/'manufacturing/engineering-preview')
    parser.add_argument('--prototype-version', help='Explicit PCB-only engineering prototype package version; requires scoped release.json')
    args = parser.parse_args()
    if args.prototype_version:
        STATE = 'rev_a_pcb_prototype_order_release'
    board_path, bom_path, output = args.board.resolve(), args.bom.resolve(), args.output.resolve()
    if board_path == output or board_path in output.parents:
        raise ValueError('Output must be a directory distinct from the source board')
    for subdir in ('gerbers', 'drill', 'assembly', 'bom'):
        (output/subdir).mkdir(parents=True, exist_ok=True)
    inputs, errors, warnings, products = {}, [], [], []

    def snapshot(path):
        path = path.resolve()
        inputs[path] = digest(path)
        return path

    def product(path, kind, **extra):
        if not path.is_file() or path.stat().st_size == 0:
            errors.append(f'Missing/empty {kind}: {relative(path, output)}')
        products.append(dict(path=relative(path, output), kind=kind, **extra))

    snapshot(board_path)
    snapshot(bom_path)
    bom = json.loads(bom_path.read_text(encoding='utf-8'))
    bom_metadata = bom.get('metadata', {})
    if bom_metadata.get('rev_a_engineering_prototype') is not True or bom_metadata.get('rev_b_production') is not False:
        errors.append('BOM lacks the required Rev A true / Rev B false metadata')
    if bom_metadata.get('state') not in ('engineering_review_not_order_release','rev_a_prototype_procurement_data'):
        errors.append('Unrecognized BOM data state')
    if not bom_metadata.get('validation_passed'):
        errors.append('BOM validation has not passed; regenerate final source/assembled data and BOM')
        errors.extend('BOM: ' + e for e in bom_metadata.get('errors', []))
    bom_manifest_path = bom_path.parent/'REV_A_BOM_MANIFEST.json'
    bom_manifest = json.loads(snapshot(bom_manifest_path).read_text(encoding='utf-8'))
    for item in bom_manifest['inputs']:
        path = ROOT/Path(item['path'].replace('\\', '/'))
        snapshot(path)
        if inputs[path.resolve()] != item['sha256']:
            errors.append(f'Stale BOM input hash: {item["path"]}')
    for item in bom_manifest['outputs']:
        path = bom_path.parent/item['path']
        snapshot(path)
        if inputs[path.resolve()] != item['sha256']:
            errors.append(f'BOM output hash differs from BOM manifest: {item["path"]}')
        destination = output/'bom'/path.name
        shutil.copyfile(path, destination)
        product(destination, 'bom')
    shutil.copyfile(bom_manifest_path, output/'bom'/bom_manifest_path.name)
    product(output/'bom'/bom_manifest_path.name, 'bom_manifest')
    release_path = ROOT/'release.json'
    release = json.loads(snapshot(release_path).read_text(encoding='utf-8')) if release_path.exists() else {}
    if release.get('rev_a_engineering_prototype') is not True or release.get('rev_b_production') is not False:
        errors.append('Source release.json lacks required Rev A true / Rev B false flags')
    if args.prototype_version:
        if not release.get('fabrication_release') or not release.get('assembly_release') or release.get('prototype_package_version')!=args.prototype_version:
            raise ValueError('Prototype version does not have a scoped PCB fabrication/assembly release')
        native=json.loads(snapshot(ROOT/'reports/native-checks-both.json').read_text())
        if not native['all_processes_passed'] or not native['reports_have_zero_findings']:
            raise ValueError('Native checks must finish normally and have zero findings')
        for name,expected in native['input_hashes_sha256'].items():
            path=snapshot(ROOT/Path(name.replace('\\','/')))
            if digest(path)!=expected:raise ValueError('Stale native check: '+name)
        for row in native['checks'].values():
            path=snapshot(ROOT/row['report_path'])
            if row['process_exit_code']!=0 or digest(path)!=row['report_sha256']:
                raise ValueError('Native report/process evidence mismatch')
    board = pcb.LoadBoard(board_path.as_posix())
    if not board:
        raise RuntimeError('KiCad could not load board')
    if board.GetCopperLayerCount() != 4:
        errors.append(f'Expected four copper layers; board has {board.GetCopperLayerCount()}')
    # X2 layer metadata is emitted by KiCad from the loaded board.
    job = pcb.GERBER_JOBFILE_WRITER(board)
    for name, layer in REQUIRED_LAYERS:
        if not board.IsLayerEnabled(layer):
            errors.append(f'Required board layer is disabled: {name}')
        path = plot(board, output/'gerbers', name.replace('.', '_'), [layer], pcb.PLOT_FORMAT_GERBER)
        gerber_text = path.read_text(encoding='utf-8', errors='replace')
        if '%TF.FileFunction,' not in gerber_text or 'M02*' not in gerber_text:
            errors.append(f'Invalid/incomplete X2 Gerber: {path.name}')
        product(path, 'gerber', layer=name)
        job.AddGbrFile(layer, path.name)
    job_path = output/'gerbers'/(board_path.stem+'.gbrjob')
    if not job.CreateJobFile(job_path.as_posix()):
        errors.append('Native Gerber job creation failed')
    product(job_path, 'gerber_job')
    if job_path.exists():
        job_data = json.loads(job_path.read_text(encoding='utf-8'))
        job_files = {x['Path'] for x in job_data.get('FilesAttributes', [])}
        required_gerber_files = {Path(x['path']).name for x in products if x['kind']=='gerber'}
        if job_files != required_gerber_files:
            errors.append('Gerber job file list does not exactly cover the required Gerbers')
    drill = pcb.EXCELLON_WRITER(board)
    drill.SetFormat(True, pcb.GENDRILL_WRITER_BASE.DECIMAL_FORMAT)
    drill.SetOptions(False, False, pcb.VECTOR2I(0, 0), False)
    drill.SetRouteModeForOvalHoles(False)
    drill.SetMapFileFormat(pcb.PLOT_FORMAT_SVG)
    if not drill.CreateDrillandMapFilesSet((output/'drill').as_posix(), True, True):
        errors.append('Native Excellon/drill map generation failed')
    drill_report = output/'drill'/(board_path.stem+'-drill-report.txt')
    if not drill.GenDrillReportFile(drill_report.as_posix()):
        errors.append('Native drill report generation failed')
    product(drill_report, 'drill_report')
    for plating in ('PTH', 'NPTH'):
        drill_path = output/'drill'/f'{board_path.stem}-{plating}.drl'
        product(drill_path, 'drill', plating=plating)
        if drill_path.exists():
            text = drill_path.read_text(encoding='utf-8', errors='replace')
            expected = 'NonPlated' if plating == 'NPTH' else 'Plated'
            if not text.startswith('M48') or 'M30' not in text or f'TF.FileFunction,{expected}' not in text:
                errors.append(f'Missing header/end/plating declaration: {drill_path.name}')
        map_path = output/'drill'/f'{board_path.stem}-{plating}-drl_map.svg'
        product(map_path, 'drill_map', plating=plating)
    for side, layer in [('front', pcb.F_Fab), ('back', pcb.B_Fab)]:
        path = plot(board, output/'assembly', 'assembly-'+side,
                    [layer, pcb.Edge_Cuts], pcb.PLOT_FORMAT_SVG, assembly=True)
        if '<svg' not in path.read_text(encoding='utf-8', errors='replace'):
            errors.append(f'Invalid assembly SVG: {path.name}')
        product(path, 'assembly_svg', view='top_view_unmirrored', side=side)
    footprints = {}
    for fp in board.GetFootprints():
        ref = fp.GetReference()
        if ref in footprints:
            errors.append(f'Duplicate board reference: {ref}')
        footprints[ref] = fp
    components = {c['ref']: c for c in bom['components']}
    if len(components) != len(bom['components']):
        errors.append('Duplicate BOM reference')
    populated, dnp, excluded = [], [], []
    for ref, fp in sorted(footprints.items(), key=lambda x: natural(x[0])):
        record = components.get(ref)
        if not record:
            allowed = fp.IsExcludedFromBOM() or bool(re.match(r'^(TP|NT|H)\d+$', ref))
            excluded.append(dict(reference=ref, value=fp.GetValue(), footprint=fp.GetFPIDAsString(),
                                 reason='PCB feature / mechanical hole' if allowed else 'UNRESOLVED no BOM record'))
            if not allowed:
                errors.append(f'Board component absent from purchased BOM: {ref}')
            continue
        if fp.GetFPIDAsString() != record['footprint']:
            errors.append(f'{ref}: board footprint differs from BOM')
        if fp.GetValue() != record['description']:
            errors.append(f'{ref}: board value {fp.GetValue()!r} differs from BOM {record["description"]!r}')
        if bool(fp.IsDNP()) != bool(record['dnp']):
            errors.append(f'{ref}: board DNP differs from BOM')
        if fp.IsExcludedFromBOM():
            errors.append(f'{ref}: purchased BOM part excluded from board BOM')
        pos, attr = fp.GetPosition(), fp.GetAttributes()
        # Footprint anchor, not a computed body centroid. Vendor/machine rotation
        # and bottom-side mirroring must be mapped explicitly by the assembler.
        mount = 'through_hole_manual' if attr & pcb.FP_THROUGH_HOLE else ('smd' if attr & pcb.FP_SMD else 'other_manual')
        row = dict(reference=ref, value=fp.GetValue(), mpn=record['mpn'], manufacturer=record['manufacturer'],
                   footprint=fp.GetFPIDAsString(), x_mm=f'{pcb.ToMM(pos.x):.6f}', y_mm=f'{pcb.ToMM(pos.y):.6f}',
                   kicad_rotation_deg=f'{fp.GetOrientationDegrees():.6f}', side='bottom' if fp.IsFlipped() else 'top',
                   mounting=mount, dnp=bool(record['dnp']), state=STATE,
                   x_right_y_down_board_origin=True, footprint_anchor_not_centroid=True,
                   board_excluded_from_position=bool(fp.IsExcludedFromPosFiles()))
        (dnp if record['dnp'] else populated).append(row)
    missing = set(components)-set(footprints)
    errors.extend(f'Purchased BOM component missing from board: {ref}' for ref in sorted(missing, key=natural))
    if len(populated) != bom_metadata.get('populated_pcb_quantity'):
        errors.append('Populated placement count differs from BOM')
    if len(dnp) != bom_metadata.get('dnp_pcb_positions'):
        errors.append('DNP placement count differs from BOM')
    fields = ['reference', 'value', 'mpn', 'manufacturer', 'footprint', 'x_mm', 'y_mm',
              'kicad_rotation_deg', 'side', 'mounting', 'dnp', 'state',
              'x_right_y_down_board_origin', 'footprint_anchor_not_centroid', 'board_excluded_from_position']
    for filename, rows in [
        ('REV_A_positions_all_populated.csv', populated),
        ('REV_A_positions_smd_populated.csv', [x for x in populated if x['mounting']=='smd']),
        ('REV_A_positions_manual_populated.csv', [x for x in populated if x['mounting']!='smd']),
        ('REV_A_positions_dnp_review.csv', dnp),
    ]:
        path = output/'assembly'/filename
        csv_write(path, rows, fields)
        product(path, 'placement_csv', rows=len(rows))
    excluded_path = output/'assembly/REV_A_excluded_pcb_features.json'
    json_write(excluded_path, dict(metadata=dict(rev_a_engineering_prototype=True, rev_b_production=False, state=STATE),
                                   features=excluded))
    product(excluded_path, 'excluded_features')
    board.BuildConnectivity()
    board.GetConnectivity().RecalculateRatsnest()
    unconnected = board.GetConnectivity().GetUnconnectedCount(False)
    tracks = list(board.GetTracks())
    zones = list(board.Zones())
    pth_pads = npth_pads = 0
    for fp in footprints.values():
        for pad in fp.Pads():
            if pad.GetDrillSize().x > 0:
                pth_pads += pad.GetAttribute() == pcb.PAD_ATTRIB_PTH
                npth_pads += pad.GetAttribute() == pcb.PAD_ATTRIB_NPTH
    through_vias = [x for x in tracks if isinstance(x, pcb.PCB_VIA) and x.GetViaType()==pcb.VIATYPE_THROUGH]
    other_vias = [x for x in tracks if isinstance(x, pcb.PCB_VIA) and x.GetViaType()!=pcb.VIATYPE_THROUGH]
    if other_vias:
        errors.append('Board has blind/buried/microvias; extend drill span coverage validation before exporting this stack')
    if drill_report.exists():
        report_text = drill_report.read_text(encoding='utf-8', errors='replace')
        for label, expected in [('plated', pth_pads+len(through_vias)), ('unplated', npth_pads)]:
            match = re.search(r'Total '+label+r' holes count\s+(\d+)', report_text)
            if not match or int(match[1]) != expected:
                errors.append(f'Drill report {label} count differs from native board pads/vias: expected {expected}')
    if unconnected:
        (errors if args.prototype_version else warnings).append(f'Actual board has {unconnected} unconnected ratsnest edges')
    warnings.append('DRC/ERC, trace current capacity, vendor press-fit holes, stencil apertures and machine placement conventions require separate review')
    warnings.append('Native assembly SVGs are unmirrored top-coordinate views; DNP footprints are crossed out where supported by KiCad')
    # Every native file is closed before checksumming. A changing source produces
    # an invalid preview instead of silently combining different revisions.
    for path, original in inputs.items():
        if not path.exists() or digest(path) != original:
            errors.append(f'Input changed during export: {relative(path)}; regenerate after edits finish')
    readme = output/('EXPORT_README.md' if args.prototype_version else 'README.md')
    readme.write_text(
        ('# '+args.prototype_version+' native PCB export\n\nEngineering prototype – not production qualified.\n\n' if args.prototype_version else '# Rev A engineering preview — not an order release\n\n')+
        'These files are native KiCad exports of the board identified by SHA-256 in EXPORT_MANIFEST.json. '
        'They do not certify that the board is routed, DRC-clean, thermally qualified or safe to energize. '
        '`rev_a_engineering_prototype: true`; `rev_b_production: false`.\n\n'
        'Gerbers contain the four actual copper layers, both masks, both silkscreens, both paste layers and Edge.Cuts. '
        'Excellon holes are metric, decimal, unmirrored, absolute board origin (0,0), with PTH/NPTH in separate files. '
        'KiCad converts its screen-coordinate Y direction in its native Gerber/Excellon writer. No holes, copper, '
        'zones, apertures or drill tolerances are invented by this exporter. The Gerber job describes the loaded board stack.\n\n'
        'Placement CSVs use the KiCad footprint anchor, millimetres, absolute board origin, X right and Y down. '
        'Rotation is GetOrientationDegrees() from the loaded footprint; bottom placements remain in the same '
        'unmirrored board coordinates. The assembler must translate origin, rotation-zero, handedness and '
        'body centroid for its own equipment before use. SMD/manual subsets partition all populated purchased '
        'BOM references; DNP positions and PCB features are separate review lists. Press-fit terminals are '
        'manual through-hole operations, not reflow placements.\n\n'
        'All required layer files are present even when a layer intentionally has no image primitives. '
        'Coverage validation means files/BOM/board identities reconcile; it is independent of manufacturing '
        'release. Review errors and board_state in EXPORT_MANIFEST.json. The copied BOM includes external '
        'parts and unselected hardware; stock is unverified. Only the output paths listed in the manifest '
        'belong to this export. Re-run build_bom.py after final source/CAD generation, then run this script '
        'with KiCad Python through scripts/run_tool.py. The exporter never saves the source board.\n', encoding='utf-8')
    product(readme, 'readme')
    for entry in products:
        path = output/entry['path']
        if path.exists():
            entry.update(sha256=digest(path), bytes=path.stat().st_size)
    manifest = dict(
        metadata=dict(rev_a_engineering_prototype=True, rev_b_production=False, state=STATE,
                      fabrication_release=bool(args.prototype_version) and not errors,
                      assembly_release=bool(args.prototype_version) and not errors,
                      release_scope='Bare PCB and populated PCB engineering prototype only' if args.prototype_version else 'Unreleased intermediate export',
                      prototype_package_version=args.prototype_version,
                      exported_at_utc=datetime.now(timezone.utc).isoformat(),
                      coverage_validation_passed=not errors, errors=errors, warnings=warnings),
        exporter=dict(path=relative(Path(__file__)), sha256=digest(Path(__file__)), kicad_version=pcb.GetBuildVersion()),
        inputs=[dict(path=relative(path), sha256=sha) for path, sha in sorted(inputs.items(), key=lambda x:str(x[0]))],
        board_state=dict(footprints=len(footprints), copper_layers=board.GetCopperLayerCount(),
                         track_and_via_items=len(tracks), zones=len(zones),
                         unconnected_ratsnest_edges=unconnected, pth_drilled_pads=pth_pads, npth_drilled_pads=npth_pads,
                         through_vias=len(through_vias), other_vias=len(other_vias),
                         populated_purchased_positions=len(populated), dnp_purchased_positions=len(dnp),
                         excluded_pcb_features=len(excluded), source_release=release),
        required_layers=[name for name, _ in REQUIRED_LAYERS],
        placement_convention=dict(units='mm', origin='absolute KiCad board origin (0,0)',
                                  x='right', y='down', position='footprint anchor, not body centroid',
                                  rotation='native KiCad GetOrientationDegrees; no vendor remapping',
                                  bottom_side='unmirrored board coordinates'),
        outputs=products)
    json_write(output/'EXPORT_MANIFEST.json', manifest)
    print(f'{len(REQUIRED_LAYERS)} Gerbers; separate PTH/NPTH drills; {len(populated)} populated placements; '
          f'{len(dnp)} DNP; {len(errors)} coverage errors; {unconnected} unconnected edges.')
    for error in errors:
        print('ERROR:', error)
    print('PCB prototype scope' if args.prototype_version else 'Engineering preview only', 'Source board unchanged:', digest(board_path) == inputs[board_path])
    return 2 if errors else 0


if __name__ == '__main__':
    try:
        code = main()
    except BaseException:
        traceback.print_exc()
        force_exit(1)
    force_exit(code)
