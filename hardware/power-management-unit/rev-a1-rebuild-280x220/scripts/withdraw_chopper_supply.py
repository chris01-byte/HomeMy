"""Withdraw the rejected 10V tree and restore exact newly-created return vias."""
from rebuild import *
import pcbnew as pcb

def main():
    r=guard();before=sha(BOARD)
    recipe=json.loads((OUT/'cycle-06-chopper-recipes.json').read_text(encoding='utf-8'))
    assert before==recipe['pcb_sha256']
    best=SCRATCH/'best.kicad_pcb'
    assert sha(best)==next(c['pcb_sha256'] for c in r['cycles'] if c['number']==5)
    folder=SCRATCH/'return-restoration-source';folder.mkdir(exist_ok=True)
    sourcepath=folder/BOARD.name;shutil.copyfile(best,sourcepath)
    for ext in ['.kicad_pro','.kicad_dru']:
        shutil.copyfile(BOARD.with_suffix(ext),sourcepath.with_suffix(ext))
    # Only native via geometry is read; no libraries or footprint update is used.
    source=pcb.LoadBoard(str(sourcepath));b=pcb.LoadBoard(str(BOARD))
    selected=next(v for v in recipe['recipes'] if v['net']=='CHOP_10V')
    remove=set(selected['added_uuids']);items={t.m_Uuid.AsString():t for t in b.GetTracks()}
    assert remove<=items.keys()
    held=[]
    for uid in remove:
        t=items[uid];assert t.GetNetname()=='CHOP_10V';b.Remove(t);held.append(t)
    sourceitems={t.m_Uuid.AsString():t for t in source.GetTracks()}
    restore=recipe['retired_only_new_BATT_N_vias'];assert len(restore)==22
    for row in restore:
        uid=row['uuid'];assert uid not in items
        v=sourceitems[uid];assert isinstance(v,pcb.PCB_VIA) and v.GetNetname()=='BATT_N' and not v.GetParentGroup()
        new=v.Duplicate();new.SetUuid(pcb.KIID(uid));new.SetNet(b.FindNet('BATT_N'));b.Add(new)
    b.BuildConnectivity();f=pcb.ZONE_FILLER(b);f.Fill(b.Zones());pcb.SaveBoard(str(BOARD),b);guard()
    write(OUT/'cycle-06-chopper-withdrawal.json',{'input_pcb_sha256':before,'pcb_sha256':sha(BOARD),
      'withdrawn_after_return_review':True,'removed_10V_items':sorted(remove),'restored_exact_vias':restore,
      'source_cycle5_sha256':sha(best),'reference_tree_retained':True,
      'reason':'10V B.Cu trunk split primary BATT_N return at x204/y84.2..210.5. Fresh fill had241/247 force pairs,46/46 critical; six BATT_N B.Cu pairs failed. Complete10V tree withdrawn rather than accepting a narrow/long detour.',
      'failed_pairs':['J2.1->NT7.2','NT1.2->BC15.1','NT2.2->BC15.1','NT3.2->BC15.1','NT4.2->BC15.1','NT7.2->BC15.1']})
    print('Withdrawn10V items',len(remove),'restored22 return vias; REF retained',flush=True)
    return b,source,f,held

if __name__=='__main__':owners=main()
