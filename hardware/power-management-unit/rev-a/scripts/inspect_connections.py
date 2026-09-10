"""Read-only geometry diagnostics for the native routing review."""
import json
import traceback
import pcbnew as pcb
from build_schematic import CAD, PROJECT, ROOT
from build_board import force_exit


def xy(p):
    return [pcb.ToMM(p.x),pcb.ToMM(p.y)]


def main():
    board=pcb.LoadBoard(str(CAD/(PROJECT+'.kicad_pcb')))
    result={}
    nets=['MAIN_CS_P','LOGIC_GND','CHOPPER_N','MOTION_SENSED_P','LIFT_N']
    for name in nets:
        tracks=[]
        for t in board.GetTracks():
            if t.GetNetname()!=name:
                continue
            if name=='LOGIC_GND' and not (290<pcb.ToMM(t.GetPosition().x)<315 and 230<pcb.ToMM(t.GetPosition().y)<255):
                continue
            tracks.append({'uuid':str(t.m_Uuid.AsString()),'type':type(t).__name__,
                           'start':xy(t.GetStart()),'end':xy(t.GetEnd()),
                           'layer':board.GetLayerName(t.GetLayer()),
                           'width':pcb.ToMM(t.GetWidth(t.GetLayer()) if isinstance(t,pcb.PCB_VIA) else t.GetWidth())})
        zones=[]
        for z in board.Zones():
            if z.GetNetname()!=name or z.GetIsRuleArea():
                continue
            poly=z.GetFilledPolysList(z.GetLayer())
            outlines=[]
            for i in range(poly.OutlineCount()):
                contour=poly.COutline(i)
                box=contour.BBox()
                outlines.append({'index':i,'min':xy(box.GetOrigin()),'max':xy(box.GetEnd()),'vertices':contour.PointCount()})
            zones.append({'layer':board.GetLayerName(z.GetLayer()),'uuid':z.m_Uuid.AsString(),'outlines':outlines})
        result[name]={'tracks':tracks,'zones':zones}
    (ROOT/'reports/connection-diagnostics.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2),flush=True)


if __name__=='__main__':
    try:
        main()
    except BaseException:
        traceback.print_exc();force_exit(1)
    force_exit(0)
