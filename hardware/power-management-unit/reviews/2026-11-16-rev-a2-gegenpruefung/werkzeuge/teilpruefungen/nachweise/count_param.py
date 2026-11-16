import os,sys,json
from power_native_reader_param import main,pcb
b,polys,paths,zones,tap_ids,digest=main()
print(os.environ.get('LABEL'),'| pcb',digest[:12],'| pairs',len(paths),'passed',sum(r['same_continuous_copper_outline'] for r in paths),'| failing:',[(r['net'],r['layer'],r['from_pad'],r['to_pad']) for r in paths if not r['same_continuous_copper_outline']][:10],'| unconnected',b.GetConnectivity().GetUnconnectedCount(False))
