import pcbnew, json, sys
B='<SITZUNG>/agents/mech/proj/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(B)
mm=pcbnew.ToMM
out={'footprints':[],'vias':[],'tracks':[],'zones':[]}
for fp in b.GetFootprints():
    p=fp.GetPosition()
    bbx=fp.GetBoundingBox(False)
    try:
        cy=fp.GetCourtyard(pcbnew.F_CrtYd if fp.GetLayer()==pcbnew.F_Cu else pcbnew.B_CrtYd).BBox()
        cyb=[mm(cy.GetLeft()),mm(cy.GetTop()),mm(cy.GetRight()),mm(cy.GetBottom())]
    except Exception as e:
        cyb=None
    f={'ref':fp.GetReference(),'value':fp.GetValue(),'fpid':fp.GetFPID().GetUniStringLibItemName() if hasattr(fp.GetFPID(),'GetUniStringLibItemName') else str(fp.GetFPID().GetLibItemName()),
       'x':mm(p.x),'y':mm(p.y),'rot':fp.GetOrientationDegrees(),'layer':b.GetLayerName(fp.GetLayer()),
       'bbox':[mm(bbx.GetLeft()),mm(bbx.GetTop()),mm(bbx.GetRight()),mm(bbx.GetBottom())],'courtyard':cyb,
       'dnp':fp.IsDNP() if hasattr(fp,'IsDNP') else None,'pads':[]}
    for pad in fp.Pads():
        pp=pad.GetPosition()
        sz=pad.GetSize(pcbnew.F_Cu) if pad.IsOnLayer(pcbnew.F_Cu) else pad.GetSize(pcbnew.B_Cu)
        dr=pad.GetDrillSize()
        ls=[b.GetLayerName(l) for l in pad.GetLayerSet().Seq()]
        try:
            shape=pad.ShowPadShape(pcbnew.F_Cu if pad.IsOnLayer(pcbnew.F_Cu) else pcbnew.B_Cu)
        except Exception as e:
            shape='?'
        try:
            attr=pad.ShowPadAttr()
        except Exception:
            attr=str(pad.GetAttribute())
        f['pads'].append({'num':pad.GetNumber(),'x':mm(pp.x),'y':mm(pp.y),'sx':mm(sz.x),'sy':mm(sz.y),'rot':pad.GetOrientationDegrees(),
                          'drill':[mm(dr.x),mm(dr.y)],'net':pad.GetNetname(),'layers':ls,'shape':shape,'attr':attr})
    out['footprints'].append(f)
for t in b.GetTracks():
    if t.GetClass()=='PCB_VIA':
        p=t.GetPosition()
        v={'x':mm(p.x),'y':mm(p.y),'net':t.GetNetname(),'drill':mm(t.GetDrillValue()),
           'w_F':mm(t.GetWidth(pcbnew.F_Cu)),'w_B':mm(t.GetWidth(pcbnew.B_Cu)),
           'top':b.GetLayerName(t.TopLayer()),'bot':b.GetLayerName(t.BottomLayer()),'type':t.GetViaType()}
        for nm in ['GetFrontTentingMode','GetBackTentingMode']:
            if hasattr(t,nm):
                try: v[nm]=int(getattr(t,nm)())
                except Exception as e: v[nm]=str(e)
        for nm in ['IsTented']:
            if hasattr(t,nm):
                try: v['tentedF']=bool(t.IsTented(pcbnew.F_Mask)); v['tentedB']=bool(t.IsTented(pcbnew.B_Mask))
                except Exception as e: v['tented']=str(e)
        out['vias'].append(v)
    else:
        s=t.GetStart(); e=t.GetEnd()
        d={'x1':mm(s.x),'y1':mm(s.y),'x2':mm(e.x),'y2':mm(e.y),'w':mm(t.GetWidth()),'layer':b.GetLayerName(t.GetLayer()),'net':t.GetNetname(),'cls':t.GetClass()}
        out['tracks'].append(d)
for z in b.Zones():
    bbx=z.GetBoundingBox()
    out['zones'].append({'net':z.GetNetname(),'name':z.GetZoneName(),'layers':[b.GetLayerName(l) for l in z.GetLayerSet().Seq()],
                         'bbox':[mm(bbx.GetLeft()),mm(bbx.GetTop()),mm(bbx.GetRight()),mm(bbx.GetBottom())],
                         'keepout':z.GetIsRuleArea(),'filled':z.IsFilled(),'prio':z.GetAssignedPriority() if hasattr(z,'GetAssignedPriority') else None,
                         'clearance':mm(z.GetLocalClearance().value()) if hasattr(z.GetLocalClearance(),'value') and z.GetLocalClearance().has_value() else None,
                         'minthick':mm(z.GetMinThickness()),
                         'padconn':int(z.GetPadConnection())})
json.dump(out,open('<SITZUNG>/agents/mech/board.json','w'))
print(len(out['footprints']),len(out['vias']),len(out['tracks']),len(out['zones']))
