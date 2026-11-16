import pcbnew as pcb, json, collections, sys
S=sys.argv[1]
tap=json.load(open(S+'/repro/hardware/power-management-unit/rev-a/evidence/high-current-tap-capture.json'))
print('tap capture keys',list(tap.keys()))
print({k:len(v) for k,v in tap['groups'].items()})
src={row['uuid'] for rows in tap['groups'].values() for row in rows}
print('source tap uuids',len(src))
for name,path in [('rev-a',S+'/reva/kicad/HomeMy_PMU_RevA.kicad_pcb'),('A2',S+'/a2/kicad/HomeMy_PMU_RevA.kicad_pcb')]:
    b=pcb.LoadBoard(path)
    print('=====',name)
    allids={t.m_Uuid.AsString():t for t in b.GetTracks()}
    gm=set()
    for g in b.Groups():
        items=list(g.GetItems())
        ids={i.m_Uuid.AsString() for i in items}
        kinds=collections.Counter(type(i).__name__ for i in items)
        print('group',repr(g.GetName()),'items',len(items),dict(kinds),'in source inventory',len(ids&src),'not in source',len(ids-src), 'locked',g.IsLocked())
        if g.GetName() in ['PWR_TAP_CONTROL','PWR_SYS_BRANCH_SPINE','PWR_SYS_BRANCH_FANOUT']: gm|=ids
    print('named tap group members',len(gm),'union with source',len(gm|src),'source present on board',len(src&set(allids)),'members not in source',len(gm-src))
    extra=gm-src
    for u in list(extra)[:10]:
        t=allids.get(u); print('   extra member',u,type(t).__name__ if t else None, t.GetNetname() if t else None)
    # width distribution of non-tap tracks on selected nets
    selected=['BATT_FUSED_P','BATT_SENSED_P','MAIN_COMMON','SYS_BUS_P','MOTION_SENSED_P','MOTION_COMMON','MOTION_BUS_P','BATT_N','ARM_L_N','ARM_R_N','DRIVE_N','LIFT_N','CHOPPER_N','CHOP_DRAIN','PC_BUCK_IN_P','LOGIC_BUCK_IN_P','PC_N','LOGIC_BUCK_N','LOGIC_5V_N','V5V']
    tapset=gm|src
    rows=collections.defaultdict(lambda: collections.Counter())
    for t in b.GetTracks():
        n=t.GetNetname()
        if n not in selected: continue
        istap=t.m_Uuid.AsString() in tapset
        if isinstance(t,pcb.PCB_VIA):
            rows[(n,'via','tap' if istap else 'pwr')][(pcb.ToMM(t.GetWidth(pcb.F_Cu)),pcb.ToMM(t.GetDrillValue()))]+=1
        else:
            rows[(n,'trk','tap' if istap else 'pwr')][pcb.ToMM(t.GetWidth())]+=1
    for k in sorted(rows):
        print('  ',k,dict(sorted(rows[k].items())))
    nc=b.GetDesignSettings().m_NetSettings
    try:
        for n in selected:
            ni=b.FindNet(n); print('   netclass',n,ni.GetNetClassName())
    except Exception as e: print('netclass err',e)
