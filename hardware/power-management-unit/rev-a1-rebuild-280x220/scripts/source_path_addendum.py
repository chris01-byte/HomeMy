"""Read-only correction of historical source-length reporting, no CAD changes."""
from rebuild import *
import sys
sys.path.insert(0,str(BASE/'scripts'))
from review_critical_routing import graph_for,shortest
import pcbnew as pcb

def main():
    read_only_guard();before=sha(BOARD);path=BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'
    b=pcb.LoadBoard(str(path));tracks=list(b.GetTracks());pads={f.GetReference()+'.'+p.GetNumber():p for f in b.GetFootprints() for p in f.Pads()}
    receipt=OUT/'cycle-03-critical-local.json';data=json.loads(receipt.read_text(encoding='utf-8'));rows=[]
    for r in data['paths']:
        p=shortest(graph_for(r['net'],tracks,pads),r['from'],r['to'])
        assert p['path_found']
        rows.append({'from':r['from'],'to':r['to'],'net':r['net'],'source_centerline_with_pad_leads_mm':p['centerline_with_pad_leads_mm']})
    assert before==sha(BOARD)
    write(OUT/'source-path-length-addendum.json',{'source_pcb_sha256':sha(path),'historical_receipt_sha256':sha(receipt),
      'reason':'The cycle3 recipe queried the wrong source length key and recorded null. This read-only addendum supplies the original measured values; historical receipt and CAD remain unchanged. Final layout lengths are in final-geometry.json.', 'paths':rows})
    print('Source path length addendum:',len(rows),'paths; CAD unchanged',flush=True)
    return b

if __name__=='__main__':owner=main()
