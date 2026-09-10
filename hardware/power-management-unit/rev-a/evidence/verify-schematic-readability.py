import json,pathlib,xml.etree.ElementTree as ET,importlib.util,hashlib
root=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('sch',root/'scripts/build_schematic.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
parts=mod.load_components();by={c['ref']:c for c in parts}
tree=ET.parse(root/'evidence/netlist-after-schematic-readability.xml').getroot()
actual={}
for n in tree.findall('./nets/net'):
 for node in n.findall('node'):actual[(node.get('ref'),node.get('pin'))]=(n.get('name'),node.get('pintype'))
errors=[];pins=0
for c in parts:
 if c['ref'].startswith('#'):continue
 for p,n in c['pins'].items():
  if n is None:continue
  pins+=1;got=actual.get((c['ref'],p))
  if got is None or got[0]!=n:errors.append({'ref':c['ref'],'pin':p,'expected':n,'actual':got})
  expectedtype=c.get('pin_types',{}).get(p,'passive')
  if got and got[1].split('+')[0]!=expectedtype:errors.append({'ref':c['ref'],'pin':p,'type_expected':expectedtype,'type_actual':got[1]})
comps={c.get('ref'):c for c in tree.findall('./components/comp')}
uuid_errors=[r for r,c in comps.items() if c.findtext('tstamps')!=mod.uid('component:'+r)]
dnp={r for r,c in comps.items() if c.find("property[@name='dnp']") is not None}
erc=json.loads((root/'evidence/erc-after-schematic-readability.json').read_text())
violations=[v for s in erc['sheets'] for v in s.get('violations',[])]
artifacts=sorted((root/'assembly/schematic').glob('*.svg'))
artifacts+=sorted((root/'evidence/schematic-before').glob('*.png'))
artifacts+=sorted((root/'evidence/schematic-after').glob('*.png'))
data={'metadata':{'rev_a_engineering_prototype':True,'rev_b_production':False},
 'source_generator_sha256':hashlib.sha256((root/'scripts/build_schematic.py').read_bytes()).hexdigest(),
 'native_export_components':len(comps),'connected_source_pins_checked':pins,'pin_net_or_type_mismatches':errors,
 'component_uuid_mismatches':uuid_errors,'native_DNP_refs':sorted(dnp),'expected_DNP_refs':['C244','J13','R243','R244'],
 'ERC_report_violations':len(violations),'native_process_exit_code':1,'native_process_diagnostic':'HKCU Software/kicad-cli registry create/open denied;complete parseable SVG/XML/ERC artifacts generated;do not describe process exit as clean.',
 'visual_review':{'rasterizer':'Bundled Node.js Sharp;6720x4752 native SVG raster','reviewed_pages':['06c_esp32_p1','06a_aon_wake_p2','04_brake_chopper_p1'],
 'observed':['Left net labels extend away from symbols and pin names','ESP32/TMUX/chopper IC pin labels readable','Long connector pin names fit widened bodies','Two-pin R/C symbols use standard graphics without duplicate internal pin names','Displayed title and revision fit native title block'],'remaining_limit':'Functional pin-level hierarchy remains;this is not a fully manually drawn application schematic or PCB review.'},
 'retained_visual_artifacts':[{'path':str(p.relative_to(root)).replace('\\','/'),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in artifacts],
 'visual_consolidation':{'native_svg_count':len([p for p in artifacts if p.suffix=='.svg']),'png_crop_count':len([p for p in artifacts if p.suffix=='.png']),'native_svg_destination':'assembly/schematic','duplicate_svg_copy_sha256_verified_before_removal':True}}
(root/'evidence/schematic-readability-review.json').write_text(json.dumps(data,indent=2)+'\n')
print(json.dumps({k:v for k,v in data.items() if k not in ('visual_review','source_generator_sha256','retained_visual_artifacts')}))
