"""One native export / predetermined SES import per bounded cycle.

DSN class partitioning only selects routable nets. It preserves original class
rules and every physical obstacle; no native rule or width is relaxed.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
import re
import sys
from bounded_checks import ROOT, LEDGER, sha, write, minutes
from bounded_seed import CRITICAL, LOWER
BASE=ROOT.parent/'rev-a';sys.path.insert(0,str(BASE/'scripts'))
import pcbnew as pcb
from configure_power_rules import POWER_NETS
from sync_nc_nets import sync_nc_nets
EXCLUDED=set(POWER_NETS)|LOWER|CRITICAL
SCRATCH=ROOT.parents[3]/'tools-local/bounded-shrink-native'

def copper(board):
    values=Counter()
    for t in board.GetTracks():
        if isinstance(t,pcb.PCB_VIA):key=('via',t.GetNetname(),t.GetPosition().x,t.GetPosition().y,t.GetWidth(pcb.F_Cu),t.GetDrillValue(),tuple(t.IsOnLayer(l) for l in [pcb.F_Cu,pcb.In1_Cu,pcb.In2_Cu,pcb.B_Cu]))
        else:key=('track',t.GetNetname(),t.GetLayer(),t.GetWidth(),tuple(sorted(((t.GetStart().x,t.GetStart().y),(t.GetEnd().x,t.GetEnd().y)))))
        values[key]+=1
    return values

def physical(board):
    # Serialize physical footprint data, excluding only authoritative NC net ids
    # (which native SES can omit and sync_nc_nets restores before comparison).
    rows=[]
    for f in board.GetFootprints():
        rows.append((f.GetReference(),f.m_Uuid.AsString(),f.GetFPID().GetLibItemName(),f.GetPosition().x,f.GetPosition().y,f.GetOrientationDegrees(),tuple(sorted((p.GetNumber(),p.GetNetname(),p.GetPosition().x,p.GetPosition().y,p.GetSize().x,p.GetSize().y,p.GetDrillSize().x,p.GetDrillSize().y,p.GetShape(),p.GetLayerSet().FmtHex()) for p in f.Pads()))))
    zones=[]
    for z in board.Zones():
        zones.append((z.m_Uuid.AsString(),z.GetNetname(),z.GetLayerSet().FmtHex(),z.GetAssignedPriority(),z.GetMinThickness(),z.GetLocalClearance(),z.GetIsRuleArea(),str(z.Outline().Format())))
    groups=sorted((g.GetName(),g.m_Uuid.AsString(),tuple(sorted(t.m_Uuid.AsString() for t in g.GetItems()))) for g in board.Groups())
    identities=sorted((t.m_Uuid.AsString(),t.IsLocked(),t.GetParentGroup().GetName() if t.GetParentGroup() else '') for t in board.GetTracks() if t.IsLocked() or t.GetParentGroup())
    return sorted(rows),sorted(zones),groups,identities

def partition_dsn(text):
    # Keep token spellings, including quoted strings. Rewrite class containers
    # only; child rule/circuit subtrees remain exact original text.
    tokens=list(re.finditer(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+',text))
    stack=[];classes=[]
    for i,t in enumerate(tokens):
        if t.group()=='(':stack.append(i)
        elif t.group()==')':
            start=stack.pop()
            if tokens[start+1].group()=='class':classes.append((start,i))
    edits=[];ignored=[]
    def name(t):return t[1:-1] if t.startswith('"') and t.endswith('"') else t
    for start,end in classes:
        k=start+3
        while k<end and tokens[k].group()!='(':k+=1
        members=tokens[start+3:k];selected=[t for t in members if name(t.group()) in EXCLUDED]
        if not selected:continue
        classname=name(tokens[start+2].group())
        if len(selected)==len(members):ignored.append(classname);continue
        assert classname=='kicad_default', 'Unexpected mixed nondefault protected class: '+classname
        newname='BOUNDED_KEEP_LOWER_CRITICAL';ignored.append(newname)
        keep=' '.join(t.group() for t in members if name(t.group()) not in EXCLUDED)
        rules=text[tokens[k].start():tokens[end].start()]
        replacement='(class '+tokens[start+2].group()+' '+keep+'\n'+rules+')\n(class '+newname+' '+' '.join(t.group() for t in selected)+'\n'+rules+')'
        edits.append((tokens[start].start(),tokens[end].end(),replacement))
    for a,b,replacement in sorted(edits,reverse=True):text=text[:a]+replacement+text[b:]
    assert ignored, 'No protected DSN classes found'
    return text,sorted(set(ignored))

def main(path,action):
    ledger=json.loads(LEDGER.read_text(encoding='utf-8'));cycle=ledger['cycles'][-1]
    assert cycle['status']=='in_progress' and minutes(ledger)<140 and not ledger.get('stop_required')
    out=ROOT/'results'/(path.stem+'.json');result=json.loads(out.read_text(encoding='utf-8'));details=result['cycles'][str(cycle['cycle'])]
    board=pcb.LoadBoard(str(path));before=sha(path)
    folder=SCRATCH/(cycle['size']+'-router-cycle-'+str(cycle['cycle']));dsn=SCRATCH/(cycle['size']+'-input-cycle-'+str(cycle['cycle'])+'.dsn')
    if action=='export':
        assert not cycle.get('global_router_export') and not dsn.exists()
        assert not any(c is not cycle and c['size']==cycle['size'] and c.get('global_router_export') for c in ledger['cycles']), 'No repeated global run for this size'
        cycle['global_router_export']=1;write(LEDGER,ledger)
        assert pcb.ExportSpecctraDSN(board,str(dsn)), 'Native DSN export failed'
        raw=dsn.read_text(encoding='utf-8');text,ignored=partition_dsn(raw);dsn.write_text(text,encoding='utf-8')
        assert sha(path)==before
        details['global_router']={'seed_pcb_sha256':before,'dsn_sha256':sha(dsn),'ignored_classes':ignored,'excluded_nets':sorted(EXCLUDED),'max_passes':200,'max_seconds':480,'selected_session':'latest.ses','candidate_count':1}
        write(out,result);print('DSN',dsn,'IGNORED',','.join(ignored),flush=True)
    else:
        assert cycle.get('global_router_export') and not cycle.get('global_router_import')
        cycle['global_router_import']=1;write(LEDGER,ledger)
        entry=details['global_router'];assert entry['seed_pcb_sha256']==before
        session=folder/'latest.ses';run=json.loads((folder/'run-result.json').read_text(encoding='utf-8'))
        manifest=json.loads((folder/'run-manifest.json').read_text(encoding='utf-8'))
        assert run['worker_stopped'] and not run['uncaught_exception'] and not manifest['external_timeout_kill'], 'Router did not stop cleanly'
        assert run['input_sha256']==entry['dsn_sha256']==manifest['immutable_input_snapshot']['sha256']
        assert sha(dsn)==entry['dsn_sha256'] and run['max_passes']==entry['max_passes']
        assert run['actual_stop_pass_no']==entry['max_passes']
        assert manifest['command'][ -2 ] == str(entry['max_seconds'])
        assert next(x['sha256'] for x in manifest['outputs'] if x['path']=='latest.ses')==sha(session)
        entry['router_result']=run;entry['router_manifest_sha256']=sha(folder/'run-manifest.json');entry['session_sha256']=sha(session)
        protected=copper(board);mechanical=physical(board)
        assert pcb.ImportSpecctraSES(board,str(session)), 'Native SES import failed'
        nc=sync_nc_nets(board);missing=protected-copper(board);new=copper(board)-protected
        bad=[(k,n) for k,n in new.items() if k[1] in EXCLUDED]
        if missing or bad or mechanical!=physical(board):
            entry.update(import_saved=False,preservation_failure={'missing_seed_items':sum(missing.values()),'new_excluded_items':len(bad),'mechanical_changed':mechanical!=physical(board)})
            write(out,result);print('Rejected SES without saving changed geometry',entry['preservation_failure'],flush=True);return board
        board.BuildConnectivity();filler=pcb.ZONE_FILLER(board);filler.Fill(board.Zones());board.GetConnectivity().RecalculateRatsnest();count=board.GetConnectivity().GetUnconnectedCount(False)
        pcb.SaveBoard(str(path),board)
        entry.update(import_saved=True,preserved_seed_items=sum(protected.values()),new_signal_items=sum(new.values()),native_ratsnest_connections=count,output_pcb_sha256=sha(path),nc_assignments=nc['pads_requiring_assignment'])
        write(out,result);print('Imported one SES; preserved',sum(protected.values()),'new',sum(new.values()),'native opens',count,flush=True);return board,filler

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('board',type=Path);ap.add_argument('action',choices=['export','import']);a=ap.parse_args();owners=main(a.board.resolve(),a.action)
