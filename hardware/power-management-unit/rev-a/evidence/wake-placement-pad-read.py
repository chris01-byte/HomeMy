import pcbnew,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
parts=json.loads((root/'design/wake-io-parts.json').read_text())['components']
lib=pathlib.Path('C:/Users/chrba/Documents/ChatGPT/HomeMy/tools-local/kicad/share/kicad/footprints')
out={}
for c in parts:
 if not c['ref'].startswith('U'): continue
 fpname=c['footprint']
 if fpname.startswith('PMU:'):
  out[c['ref']]={'pads':{str(p['number']):[p['x'],p['y']] for p in c['pad_geometry_mm']['pads']}}
  continue
 a,b=fpname.split(':')
 f=pcbnew.FootprintLoad(str(lib/(a+'.pretty')),b)
 if f is None: raise RuntimeError(fpname)
 out[c['ref']]={'pads':{p.GetNumber():[pcbnew.ToMM(p.GetPosition().x),pcbnew.ToMM(p.GetPosition().y)] for p in f.Pads()}}
print(json.dumps(out))
