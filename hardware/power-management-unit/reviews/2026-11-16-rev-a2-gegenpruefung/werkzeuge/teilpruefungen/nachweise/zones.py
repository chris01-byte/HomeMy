import pcbnew as pcb, json, collections, sys
S=sys.argv[1]
POWER=['BATT_FUSED_P','BATT_SENSED_P','MAIN_COMMON','BATT_N','SYS_BUS_P','MOTION_SENSED_P','MOTION_COMMON','MOTION_BUS_P','ARM_L_N','ARM_R_N']
SEL=POWER+['DRIVE_N','LIFT_N','CHOPPER_N','CHOP_DRAIN','PC_BUCK_IN_P','LOGIC_BUCK_IN_P','PC_N','LOGIC_BUCK_N','LOGIC_5V_N','V5V']
for name,path in [('rev-a',S+'/reva/kicad/HomeMy_PMU_RevA.kicad_pcb'),('A2',S+'/a2/kicad/HomeMy_PMU_RevA.kicad_pcb')]:
    b=pcb.LoadBoard(path)
    print('=====',name,'zones total',len(list(b.Zones())))
    c=collections.Counter(); rows=[]
    for z in b.Zones():
        if z.GetIsRuleArea(): c['rule_area']+=1; continue
        n=z.GetNetname()
        mt=pcb.ToMM(z.GetMinThickness())
        ls=[b.GetLayerName(l) for l in z.GetLayerSet().Seq()]
        rows.append((n,ls,mt,z.GetZoneName(),pcb.ToMM(z.GetLocalClearance().value()) if hasattr(z.GetLocalClearance(),'value') and z.GetLocalClearance().has_value() else None,z.GetPadConnection(),z.GetIslandRemovalMode(),z.GetAssignedPriority()))
    print('rule areas',c['rule_area'],'copper zones',len(rows))
    pw=[r for r in rows if r[0] in POWER]; sel=[r for r in rows if r[0] in SEL]
    print('zones on PWR-class nets',len(pw),'min_thickness dist',dict(collections.Counter(r[2] for r in pw)))
    print('zones on 20 selected nets',len(sel),'min_thickness dist',dict(collections.Counter(r[2] for r in sel)))
    print('all copper zones min_thickness dist',dict(collections.Counter(r[2] for r in rows)))
    bad=[r for r in pw if r[2]<1.2]
    print('PWR-class zones with min_thickness<1.2:',len(bad))
    for r in bad[:40]: print('   ',r)
    print('pad connection modes (PWR-class)',dict(collections.Counter(r[5] for r in pw)),'island removal',dict(collections.Counter(r[6] for r in pw)))
