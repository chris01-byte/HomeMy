import pcbnew
B='<SITZUNG>/agents/mech/proj/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(B)
mm=pcbnew.ToMM
for fp in b.GetFootprints():
    r=fp.GetReference()
    if r in ('J1','J2','J3','J4','J5','J6','BC1','NT1','NT5','H1','C3','C10','C312','D63','RSH1','Q1'):
        print('==',r,fp.GetValue(),'pos',mm(fp.GetPosition().x),mm(fp.GetPosition().y),'rot',fp.GetOrientationDegrees())
        for g in fp.GraphicalItems():
            cls=g.GetClass()
            if cls in('PCB_TEXT','PCB_TEXTBOX'):
                p=g.GetPosition()
                print('   TEXT',b.GetLayerName(g.GetLayer()),repr(g.GetText()),'at',mm(p.x),mm(p.y))
            elif cls=='PCB_SHAPE':
                s=g.GetStart(); e=g.GetEnd()
                print('   SHAPE',b.GetLayerName(g.GetLayer()),g.ShowShape(),(mm(s.x),mm(s.y)),(mm(e.x),mm(e.y)),'w',mm(g.GetWidth()))
        for f in fp.GetFields():
            if f.GetText():
                print('   FIELD',f.GetName(),'=',repr(f.GetText())[:150], b.GetLayerName(f.GetLayer()), 'visible' if f.IsVisible() else 'hidden')
        ms=fp.Models()
        for m in ms:
            print('   3D',m.m_Filename, m.m_Rotation.x,m.m_Rotation.y,m.m_Rotation.z, m.m_Offset.x,m.m_Offset.y,m.m_Offset.z)
