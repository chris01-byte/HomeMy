import pcbnew as pcb, sys
p=sys.argv[1]
b=pcb.LoadBoard(p)
def net(n): return b.FindNet(n)
# locate a point well inside MOTION_BUS_P copper: use pad BC11.1 centre region and J3 pad
fp=b.FindFootprintByReference('BC11'); pos=fp.GetPosition()
t=pcb.PCB_TRACK(b); t.SetStart(pcb.VECTOR2I(pos.x+pcb.FromMM(6),pos.y)); t.SetEnd(pcb.VECTOR2I(pos.x+pcb.FromMM(12),pos.y)); t.SetWidth(pcb.FromMM(0.2)); t.SetLayer(pcb.F_Cu); t.SetNet(net('MOTION_BUS_P')); b.Add(t)
v=pcb.PCB_VIA(b); v.SetPosition(pcb.VECTOR2I(pos.x+pcb.FromMM(9),pos.y+pcb.FromMM(3))); v.SetWidth(pcb.F_Cu,pcb.FromMM(0.6)); v.SetDrill(pcb.FromMM(0.3)); v.SetNet(net('MOTION_BUS_P')); v.SetViaType(pcb.VIATYPE_THROUGH); b.Add(v)
# arm net 4mm track (rule says min 6 mm)
fp2=b.FindFootprintByReference('NT2'); p2=[pd for pd in fp2.Pads() if pd.GetNumber()=='1'][0].GetPosition()
t2=pcb.PCB_TRACK(b); t2.SetStart(pcb.VECTOR2I(p2.x,p2.y-pcb.FromMM(8))); t2.SetEnd(pcb.VECTOR2I(p2.x,p2.y-pcb.FromMM(14))); t2.SetWidth(pcb.FromMM(4.0)); t2.SetLayer(pcb.F_Cu); t2.SetNet(net('ARM_R_N')); b.Add(t2)
print('added: 0.2mm MOTION_BUS_P track, 0.6/0.3 MOTION_BUS_P via near BC11 (%.1f,%.1f); 4.0mm ARM_R_N track near NT2.1'%(pcb.ToMM(pos.x),pcb.ToMM(pos.y)))
pcb.SaveBoard(p,b)
