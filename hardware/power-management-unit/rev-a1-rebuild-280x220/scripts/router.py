"""Bounded fresh-DSN/one-SES signal routing with immutable native seed checks."""
from rebuild import *
import sys,os
from collections import Counter
sys.path.insert(0,str(BASE.parent/'rev-a1/scripts'))
import bounded_interchange as inter
from bounded_seed import LOWER,CRITICAL
from review_critical_routing import NETS
from configure_power_rules import POWER_NETS
from sync_nc_nets import sync_nc_nets
import pcbnew as pcb

# Explicit routing scope; frozen net classes and all original local copper stay.
EXCLUDED=set(POWER_NETS)|set(LOWER)|set(NETS)|set('''
 MAIN_ILIM MAIN_ILIM_TAIL MAIN_OV MAIN_TMR MAIN_UVLO
 MOTION_IWRN MOTION_TEMP_DIODE MOTION_TMR MOTION_UVLO
 MOTION_IMON_RAW MOTION_IMON_INPUT MOTION_LATCH_UV_SENSE MOTION_UV_REF
 INA_VBUS AON_FB STARTUP_DIV STARTUP_RSET MAIN_CAPTURE_RC WAKE_ONT WAKE_PDT
 SYS_DIV_MID SYS_BUS_DIV SYS_BUS_ADC MOT_DIV_MID MOTION_BUS_DIV MOTION_BUS_ADC MOTION_IMON_ADC
 TEMP_MAIN_ADC TEMP_MOTION_ADC CHOP_TEMP_ADC LIFT_24V_SAMPLE LIFT_24V_N
 LOGIC_GND CHOP_GND AON_FEED_MID AON_LDO_IN AON_3V3 CAN_H CAN_L CAN_TERM_MID CHASSIS
'''.split())|{f'{p}_{s}' for p in ['PC','LOGIC'] for s in ['DVDT','ILIM','OVP','PGTH','SHDN','UVLO']}

def exclusions(b):
    names={p.GetNetname() for f in b.GetFootprints() for p in f.Pads()}
    excluded=EXCLUDED|({n for n in names if n.startswith('CHOP_')}-{'CHOP_ACTIVE_N','CHOP_FAULT_N'})
    assert excluded<=names and len(excluded)==127
    return excluded|{n for n in names if n.startswith('unconnected-(')}

def physical_extra(b):
    layers=[pcb.F_Cu,pcb.In1_Cu,pcb.In2_Cu,pcb.B_Cu];rows=[]
    for f in b.GetFootprints():
        pads=[]
        for p in f.Pads():
            copper=[]
            for l in layers:
                if p.IsOnLayer(l):
                    q=pcb.SHAPE_POLY_SET();p.TransformShapeToPolygon(q,l,0,pcb.FromMM(.001),pcb.ERROR_INSIDE);copper.append((l,str(q.Format())))
            pads.append((p.m_Uuid.AsString(),p.GetNumber(),p.GetOrientationDegrees(),p.GetAttribute(),p.GetDrillShape(),tuple(copper)))
        keepouts=[(z.GetLayerSet().FmtHex(),str(z.Outline().Format()),z.GetDoNotAllowTracks(),z.GetDoNotAllowVias(),z.GetDoNotAllowPads(),z.GetDoNotAllowZoneFills(),z.GetDoNotAllowFootprints()) for z in f.Zones() if z.GetIsRuleArea()]
        rows.append((f.GetReference(),f.GetValue(),f.GetFPIDAsString(),f.GetAttributes(),f.GetLayer(),sorted(pads),keepouts))
    edges=sorted((d.m_Uuid.AsString(),int(d.GetShape()),d.GetStart().x,d.GetStart().y,d.GetEnd().x,d.GetEnd().y,d.GetWidth()) for d in b.GetDrawings() if d.GetLayer()==pcb.Edge_Cuts)
    return sorted(rows),edges,b.GetCopperLayerCount(),b.GetDesignSettings().GetBoardThickness()

def export(label):
    r=guard();assert r['router_calls']<4 and not r['cycles'][-1]['completed']
    gate=json.loads((OUT/'cycle-06-prerouter-geometry.json').read_text(encoding='utf-8'))
    assert gate['pcb_sha256']==sha(BOARD),'Stale routing power/placement gate'
    assert gate['force']['passed_pairs']==247 and gate['critical']['passed']==46 and gate['placement']['passed']
    folder=SCRATCH/label;assert not folder.exists();folder.mkdir()
    b=pcb.LoadBoard(str(BOARD));before=sha(BOARD);dsn=folder/'native-seed.dsn'
    assert pcb.ExportSpecctraDSN(b,str(dsn))
    native_dsn_sha=sha(dsn);inter.EXCLUDED=exclusions(b)
    partition,ignored=inter.partition_dsn(dsn.read_text(encoding='utf-8'));dsn.write_text(partition,encoding='utf-8')
    realnets={t.GetNetname() for f in b.GetFootprints() for t in f.Pads()}
    entry={'input_pcb_sha256':before,'native_dsn_sha256':native_dsn_sha,'partitioned_dsn_sha256':sha(dsn),'ignored_classes':ignored,
      'excluded_nets':sorted(inter.EXCLUDED&realnets),'selected_session':'latest.ses','max_passes':250,'engine_seconds':500,'hard_total_seconds':600,'imported':False}
    write(OUT/(label+'-routing.json'),entry)
    assert before==sha(BOARD);print('Exported',label,'ignored',','.join(ignored),flush=True)
    return b

def run(label):
    r=guard();assert r['router_calls']<4
    entry=json.loads((OUT/(label+'-routing.json')).read_text(encoding='utf-8'));assert 'run_started' not in entry
    r['router_calls']+=1;write(LEDGER,r);entry['run_started']=now().isoformat();write(OUT/(label+'-routing.json'),entry)
    local=SCRATCH.parent
    cmd=[sys.executable,'-B',str(ROOT/'scripts/router_engine.py'),'--java',str(local/'java21/jdk-21.0.12.1+1-jre/bin/java.exe'),
      '--router-jar',str(local/'freerouting-2.1.0.jar'),'--compiler-jar',str(local/'ecj-3.38.0.jar'),
      '--input',str(SCRATCH/label/'native-seed.dsn'),'--output',str(SCRATCH/label/'engine'),
      '--passes','250','--seconds','500','--ignore-net-classes',','.join(entry['ignored_classes'])]
    t=now();p=subprocess.run(cmd,timeout=610,creationflags=subprocess.CREATE_NO_WINDOW)
    entry['launcher_exit']=p.returncode;entry['launcher_seconds']=(now()-t).total_seconds()
    write(OUT/(label+'-routing.json'),entry);return p.returncode

def import_one(label):
    guard();out=OUT/(label+'-routing.json');entry=json.loads(out.read_text(encoding='utf-8'));assert not entry['imported']
    assert sha(BOARD)==entry['input_pcb_sha256'],'Native seed changed during engine run'
    folder=SCRATCH/label/'engine';manifest=json.loads((folder/'run-manifest.json').read_text(encoding='utf-8'));run=json.loads((folder/'run-result.json').read_text(encoding='utf-8'))
    assert run['worker_stopped'] and not run['uncaught_exception'] and not manifest['external_timeout_kill']
    assert manifest['total_seconds']<=600 and run['max_passes']==run['actual_stop_pass_no']==250
    assert run['input_sha256']==entry['partitioned_dsn_sha256']==manifest['immutable_input_snapshot']['sha256']
    assert not manifest['changed_inputs']
    session=folder/entry['selected_session'];assert next(v['sha256'] for v in manifest['outputs'] if v['path']==session.name)==sha(session)
    b=pcb.LoadBoard(str(BOARD));seed=inter.copper(b);physical=inter.physical(b);extra=physical_extra(b);excluded=exclusions(b)
    assert pcb.ImportSpecctraSES(b,str(session))
    nc=sync_nc_nets(b);missing=seed-inter.copper(b);added=inter.copper(b)-seed
    wrong=[{'item':list(k),'count':v} for k,v in added.items() if k[1] in excluded]
    entry.update(run=run,manifest_sha256=sha(folder/'run-manifest.json'),session_sha256=sha(session),
      caught_engine_exceptions=manifest['engine_exception_log_occurrences'],missing_seed_items=sum(missing.values()),new_protected_items=wrong,physical_unchanged=physical==inter.physical(b) and extra==physical_extra(b))
    if missing or wrong or not entry['physical_unchanged']:
        entry['rejected']='SES changed immutable seed or routed protected net';write(out,entry);print(entry['rejected'],flush=True);return b
    b.BuildConnectivity();f=pcb.ZONE_FILLER(b);f.Fill(b.Zones());b.GetConnectivity().RecalculateRatsnest()
    from power_audit import force
    from bounded_geometry import critical
    paths,crit=force(b),critical(b)
    entry['refilled_force_pairs']=paths['passed_pairs'];entry['refilled_critical_paths']=crit['passed']
    if paths['passed_pairs']!=247 or crit['passed']!=46:
        entry['rejected']='Refilled signal candidate lost required power or critical paths';write(out,entry)
        print(entry['rejected'],paths['passed_pairs'],crit['passed'],flush=True);return b,f
    pcb.SaveBoard(str(BOARD),b);guard()
    entry.update(imported=True,pcb_sha256=sha(BOARD),new_signal_items=sum(added.values()),native_open_connections=b.GetConnectivity().GetUnconnectedCount(False),nc_assignments=nc['pads_requiring_assignment'])
    write(out,entry);print('Imported',label,'native opens',entry['native_open_connections'],'new items',entry['new_signal_items'],flush=True)
    return b,f

if __name__=='__main__':
    operation,label=sys.argv[1:3]
    if operation=='export':owners=export(label)
    elif operation=='run':run(label)
    elif operation=='import':owners=import_one(label)
