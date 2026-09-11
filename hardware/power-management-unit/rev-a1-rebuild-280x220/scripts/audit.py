"""Read-only new-layout physical audit, retaining original path identities."""
import sys,json,math
from pathlib import Path
from rebuild import *
sys.path.insert(0,str(BASE.parent/'rev-a1/scripts'))
from bounded_geometry import placement,critical,xy
from power_audit import force
import pcbnew as pcb
def main(label):
    (read_only_guard if label=='final' else guard)();before=sha(BOARD);b=pcb.LoadBoard(str(BOARD));old=pcb.LoadBoard(str(BASE/'kicad/HomeMy_PMU_RevA.kicad_pcb'))
    b.BuildConnectivity();b.GetConnectivity().RecalculateRatsnest()
    place=placement(b,old)
    # The old screen hardcodes connector directions. Recompute this one field
    # from the new placement's explicit physical assembly axes.
    from review_placement_access import outlines,bounds,boxes_intersect,intersection_area,rectangle
    pc=json.loads((OUT/'placement-construction.json').read_text(encoding='utf-8'))
    courts={}
    for f in b.GetFootprints():f.BuildCourtyardCaches();courts[f.GetReference()]=f.GetCourtyard(pcb.F_Cu).CloneDropTriangulation()
    ports=[]
    for ref,c in pc['ports'].items():ports.append({'ref':ref,'corridor_mm':c,'blocked_by':[r for r,q in courts.items() if r!=ref and intersection_area(q,rectangle(c))>1e-6]})
    place['ports']=ports
    place['passed']=not place['identity_errors'] and not place['courtyard_overlaps'] and len(place['probes'])==40 and all(p['3mm_probe_gap_mm']>=-1e-6 for p in place['probes']) and not any(p['blocked_by'] for p in ports) and bool(place['antenna']) and all(a['prohibitions'] and len(a['layers'])==4 and a['edge_reached'] and not a['copper_intersections'] and not a['foreign_courtyards'] for a in place['antenna']) and all(p['geometry_unchanged'] for p in place['pressfit'])
    pts=[xy(p) for d in b.GetDrawings() if d.GetLayer()==pcb.Edge_Cuts for p in [d.GetStart(),d.GetEnd()]]
    report={'pcb_sha256':before,'native_reload':True,'outline_mm':[round(max(p[i] for p in pts)-min(p[i] for p in pts),6) for i in [0,1]],'placement':place,'open_connections':b.GetConnectivity().GetUnconnectedCount(False),'force':force(b),'critical':critical(b)}
    assert sha(BOARD)==before;write(OUT/(label+'-geometry.json'),report)
    print(label,'placement',place['passed'],'opens',report['open_connections'],'force',report['force']['passed_pairs'],'critical',report['critical']['passed'],flush=True)
    return b,old
if __name__=='__main__':owners=main(sys.argv[1])
