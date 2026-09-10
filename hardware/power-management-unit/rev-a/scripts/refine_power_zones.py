"""Remove sub-millimetre power-pour slivers and refill with native KiCad.

No tracks, footprints, net identities, Kelvin zones, or pad settings are edited.
Run only as a reviewed CAD operation, followed by ERC/DRC and copper review.
"""
import hashlib
import json
import traceback
import pcbnew as pcb
from configure_power_rules import CAD, ROOT, PROJECT, POWER_NETS
from build_board import force_exit, mm


def main():
    path = CAD / (PROJECT + '.kicad_pcb')
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    board = pcb.LoadBoard(str(path))
    changed = []
    for zone in board.Zones():
        if not zone.GetIsRuleArea() and zone.GetNetname() in POWER_NETS:
            changed.append({'net': zone.GetNetname(), 'layer': board.GetLayerName(zone.GetLayer()),
                            'previous_min_thickness_mm': pcb.ToMM(zone.GetMinThickness())})
            zone.SetMinThickness(mm(1.2))
            zone.SetIslandRemovalMode(pcb.ISLAND_REMOVAL_MODE_ALWAYS)
            if zone.GetNetname() == 'BATT_N':
                # NT1/NT2 branch-pad clearances cut the old y=133 return into
                # islands when narrow slivers are removed. Add a real lower
                # return corridor, retaining the separate branch nets.
                extra = pcb.SHAPE_POLY_SET()
                extra.NewOutline()
                for x, y in [(6, 131), (355, 131), (355, 137), (6, 137)]:
                    extra.Append(mm(x), mm(y))
                zone.Outline().BooleanAdd(extra)
                zone.Outline().Simplify()
    board.BuildConnectivity()
    filler = pcb.ZONE_FILLER(board)
    filler.Fill(board.Zones())
    pcb.SaveBoard(str(path), board)
    report = {'rev_a_engineering_prototype': True, 'rev_b_production': False,
              'input_board_sha256': before, 'output_board_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
              'new_zone_min_thickness_mm': 1.2, 'zones': changed,
              'batt_n_lower_edge_mm': 137,
              'meaning': 'Pour sliver filtering only; width and current capacity of complete paths require separate checks.'}
    (ROOT / 'reports/power-zone-refinement.json').write_text(json.dumps(report, indent=2) + '\n')
    print('Refined and refilled', len(changed), 'power zones', flush=True)
    return board, filler


if __name__ == '__main__':
    try:
        native_owners = main()
    except BaseException:
        traceback.print_exc()
        force_exit(1)
    force_exit(0)
