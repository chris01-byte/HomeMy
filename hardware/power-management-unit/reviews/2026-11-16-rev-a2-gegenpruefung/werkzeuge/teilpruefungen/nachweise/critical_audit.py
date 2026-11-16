from pathlib import Path
import sys,runpy
source=Path('<SITZUNG>/agents/evidence/repro/hardware/power-management-unit/rev-a/scripts/review_critical_routing.py')
sys.path.insert(0,str(source.parent))
sys.argv=[str(source),'--board','<SITZUNG>/agents/evidence/repro/hardware/power-management-unit/rev-a2-layout-280x260/kicad/HomeMy_PMU_RevA.kicad_pcb','--output',sys.argv[1]]
runpy.run_path(str(source),run_name='__main__')
