import sys
sys.path.insert(0,'<SITZUNG>/agents/footprints')
import sx, pickle, os
PCB='<SITZUNG>/pmu/hardware/power-management-unit/rev-a2-layout-280x260/kicad/HomeMy_PMU_RevA.kicad_pcb'
LIB='<SITZUNG>/pmu/hardware/power-management-unit/rev-a2-layout-280x260/kicad/libraries'
CACHE='<SITZUNG>/agents/footprints/board.pkl'
def board():
    if os.path.exists(CACHE):
        return pickle.load(open(CACHE,'rb'))
    root,fps=sx.board_footprints(PCB)
    pickle.dump((root,fps),open(CACHE,'wb'))
    return root,fps
if __name__=='__main__':
    root,fps=board()
    for ref in sys.argv[1:]:
        if ref.endswith('.kicad_mod') or '/' in ref:
            path=ref if os.path.exists(ref) else os.path.join(LIB,ref)
            f=sx.load_mod(path)
            print('=== LIB',path.split('libraries/')[-1])
            for pd in sx.pads_of(f): print('  ',sx.fmt_pad(pd))
            continue
        f=fps[ref]
        x,y,rot=sx.fp_at(f)
        print(f"=== BOARD {ref} fpid {sx.S(f[1])} at ({x},{y}) rot {rot} layer {sx.fp_layer(f)}")
        for pd in sx.pads_of(f): print('  ',sx.fmt_pad(pd,rot))
