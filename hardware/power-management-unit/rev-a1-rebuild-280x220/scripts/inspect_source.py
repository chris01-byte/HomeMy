"""Read-only native extraction of the verified Rev-A footprint geometries."""
import json,sys
from pathlib import Path
import pcbnew as pcb

ROOT=Path(__file__).resolve().parents[1]
BASE=ROOT.parent/'rev-a'
def xy(v):return [pcb.ToMM(v.x),pcb.ToMM(v.y)]
def main():
    current=len(sys.argv)>1 and sys.argv[1]=='current'
    path=ROOT/'kicad/HomeMy_PMU_RevA1_Rebuild_280x220.kicad_pcb' if current else BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'
    b=pcb.LoadBoard(str(path))
    rows={}
    for f in b.GetFootprints():
        f.BuildCourtyardCaches();c=f.GetCourtyard(pcb.F_Cu);box=c.BBox()
        rows[f.GetReference()]={'xy':xy(f.GetPosition()),'angle':f.GetOrientationDegrees(),
            'value':f.GetValue(),'footprint':f.GetFPIDAsString(),
            'box':[pcb.ToMM(v) for v in [box.GetX(),box.GetY(),box.GetRight(),box.GetBottom()]],
            'pads':[{'number':p.GetNumber(),'net':p.GetNetname(),'xy':xy(p.GetPosition())} for p in f.Pads()]}
    (ROOT/'reports'/('current-footprints.json' if current else 'source-footprints.json')).write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
    print('Extracted original footprint identities:',len(rows),flush=True)
    return b
if __name__=='__main__': owner=main()
