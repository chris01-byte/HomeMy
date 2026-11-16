import pcbnew, json, sys
B='<SITZUNG>/agents/mech/proj/HomeMy_PMU_RevA.kicad_pcb'
b=pcbnew.LoadBoard(B)
print(pcbnew.GetBuildVersion())
bb=b.GetBoardEdgesBoundingBox()
print('edges bbox', pcbnew.ToMM(bb.GetX()),pcbnew.ToMM(bb.GetY()),pcbnew.ToMM(bb.GetWidth()),pcbnew.ToMM(bb.GetHeight()))
ds=b.GetDesignSettings()
print('board thickness', pcbnew.ToMM(ds.GetBoardThickness()))
for a in ['m_SolderMaskExpansion','m_SolderMaskMinWidth','m_SolderMaskToCopperClearance','m_TentViasFront','m_TentViasBack']:
    try:
        print(a, getattr(ds,a))
    except Exception as e:
        print(a,'ERR',e)
fps=list(b.GetFootprints())
print('footprints',len(fps))
tr=list(b.GetTracks())
print('tracks',len(tr))
import collections
c=collections.Counter(t.GetClass() for t in tr)
print(c)
print('zones',len(list(b.Zones())))
