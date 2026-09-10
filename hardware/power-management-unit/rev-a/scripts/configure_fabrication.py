"""Explicit physical fabrication settings, without suppressed DRC checks."""
import json
from build_schematic import ROOT, CAD, PROJECT
from sexpr import parse, dump, child


def main():
    filename=CAD/(PROJECT+'.kicad_pcb')
    ast=parse(filename.read_text(encoding='utf-8'))
    child(ast,'paper')[1]='"A2"'
    setup=child(ast,'setup')
    previous=child(setup,'stackup')
    if previous:
        setup.remove(previous)
    setup.append(parse('''(stackup
      (layer "F.SilkS" (type "Top Silk Screen"))
      (layer "F.Paste" (type "Top Solder Paste"))
      (layer "F.Mask" (type "Top Solder Mask") (thickness 0.01))
      (layer "F.Cu" (type "copper") (thickness 0.07))
      (layer "dielectric 1" (type "prepreg") (thickness 0.15) (material "FR4 Tg125-135") (epsilon_r 4.3) (loss_tangent 0.02))
      (layer "In1.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 2" (type "core") (thickness 1.09) (material "FR4 Tg125-135") (epsilon_r 4.3) (loss_tangent 0.02))
      (layer "In2.Cu" (type "copper") (thickness 0.035))
      (layer "dielectric 3" (type "prepreg") (thickness 0.15) (material "FR4 Tg125-135") (epsilon_r 4.3) (loss_tangent 0.02))
      (layer "B.Cu" (type "copper") (thickness 0.07))
      (layer "B.Mask" (type "Bottom Solder Mask") (thickness 0.01))
      (layer "B.Paste" (type "Bottom Solder Paste"))
      (layer "B.SilkS" (type "Bottom Silk Screen"))
      (copper_finish "ENIG") (dielectric_constraints no))'''))
    filename.write_text(dump(ast)+'\n',encoding='utf-8')
    parts=json.loads((ROOT/'design'/'assembled-parts.json').read_text())['components']
    rules=['(version 1)', '# Only intrinsic same-package pad spacing uses 0.15 mm; routes retain the 0.20 mm netclass clearance.']
    for c in parts:
        ref=c['ref']
        if not ref.startswith('U'):
            continue
        rules.append(f'''(rule "Reviewed fine-pitch land pattern {ref}"
  (condition "A.Type == 'Pad' && B.Type == 'Pad' && A.memberOfFootprint('{ref}') && B.memberOfFootprint('{ref}')")
  (constraint clearance (min 0.15mm)))''')
    (CAD/(PROJECT+'.kicad_dru')).write_text('\n'.join(rules)+'\n')
    print('Configured 2/1/1/2 oz, 1.60 mm excluding masks, Tg125-135, ENIG; explicit same-package pad constraints.')


if __name__=='__main__':
    main()
