import pcbnew
B='<SITZUNG>/agents/mech/proj/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(B)
mm=pcbnew.ToMM
for fp in b.GetFootprints():
    r=fp.GetReference()
    if r in ('J1','J2','J3','J4','J5','J6'):
        print('==',r,fp.GetValue(),'pos',mm(fp.GetPosition().x),mm(fp.GetPosition().y),'rot',fp.GetOrientationDegrees())
        for g in fp.GraphicalItems():
            cls=g.GetClass()
            if cls in('PCB_TEXT','PCB_TEXTBOX'):
                p=g.GetPosition()
                print('   TEXT',b.GetLayerName(g.GetLayer()),repr(g.GetText()),'at',mm(p.x),mm(p.y))
print('board-level drawings:')
for g in b.GetDrawings():
    cls=g.GetClass()
    if cls in('PCB_TEXT','PCB_TEXTBOX'):
        p=g.GetPosition()
        print('   TEXT',b.GetLayerName(g.GetLayer()),repr(g.GetText()),'at',mm(p.x),mm(p.y))
    else:
        print('  ',cls,b.GetLayerName(g.GetLayer()))
# all footprint texts containing direction-ish words
import re
for fp in b.GetFootprints():
    for g in fp.GraphicalItems():
        if g.GetClass() in('PCB_TEXT','PCB_TEXTBOX'):
            t=g.GetText()
            if re.search(r'FACE|NORTH|SOUTH|EAST|WEST|NORD|SUED|SÜD|OST|WEST|-Y|\+Y|-X|\+X|AXIS|LUG',t,re.I):
                p=g.GetPosition(); print('  FPTEXT',fp.GetReference(),b.GetLayerName(g.GetLayer()),repr(t),mm(p.x),mm(p.y))
