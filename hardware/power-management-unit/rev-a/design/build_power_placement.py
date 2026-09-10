"""Power-stage placement intent, in mm; does not modify CAD or imply routing."""
from pathlib import Path
import json

HERE=Path(__file__).resolve().parent
parts=json.loads((HERE/'power-parts.json').read_text())['components']
p={}
def put(ref,x,y,rotation=0,reason='Controller support; short local connection'):
    p[ref]=dict(x=x,y=y,rotation=rotation,reason=reason)

for i,(x,y,rot) in enumerate([(55,25,90),(55,50,90),(55,75,90),
                            (85,25,270),(85,50,270),(85,75,270),
                            (150,30,90),(150,65,90),(180,30,270),(180,65,270)],1):
    put('Q'+str(i),x,y,rot,'Source terminals face common-source strip; drain base faces its own bus')
    left=rot==90
    # KiCad positive-angle transform: x'=x*cos+y*sin, y'=-x*sin+y*cos.
    gx=x+(5.65 if left else -5.65)
    gy=y+(5 if left else -5)
    put('R'+str(i),gx+(1 if left else -1),gy+(3.5 if left else -3.5),90,
        'Individual 10-ohm gate resistor within ~4mm of physical gate pad; route pad2 directly to gate')
    put('R'+str(10+i),gx+(4.5 if left else -4.5),gy+(3.5 if left else -3.5),90,
        'Individual gate-source bleed; separate from common gate trace')

put('RSH1',30,45,0,'Force current left-to-right; sense pads face top for independent Kelvin pairs')
put('RSH2',120,45,0,'Force current left-to-right; sense pads face top for independent Kelvin pair')
put('D1',30,65,90,'Input TVS local heavy return to power star; preserve short input loop')
put('D2',103,80,90,'System TVS close to main output bus; heavy return separate from Kelvin')
put('U1',65,98,0,'Main controller below MOSFET banks; Kelvin routes kept together')
for ref,x,y,rot in [
 ('C1',72,92,90),('C2',67,90,0),('C3',52,141,0),
 ('R21',73,101,90),('C4',70,105,0),('R23',76,101,90),('C5',76,105,0),
 ('R22',57,104,0),('R64',52,104,0),('R24',63,105,0),
 ('R25',54,91,90),('R26',58,92,90),('C6',59,97,90),
 ('R27',48,91,90),('R28',52,97,90),('C7',55,97,90),('R29',60,101,90)]:
    put(ref,x,y,rot)

put('U2',164,94,0,'Motion controller below banks; differential sensing and charge pump stay local')
for ref,x,y,rot in [
 ('C8',169,87,0),('C9',174,97,0),('C29',174,101,0),('C10',164,141,0),
 ('R30',173,88,0),('C11',173,91,0),('R32',179,88,0),('C12',179,91,0),
 ('R31',157,98,90),('R33',157,103,0),('R34',172,105,0),
 ('R35',150,87,90),('R36',156,87,90),('R39',156,92,90),
 ('C13',161,103,90),('Q11',170,71,0),
 ('R59',150,99,90),('R60',147,99,90),('R61',144,99,90),('C28',141,99,90),
 ('U5',192,94,0),('R62',198,91,90),('R63',198,96,90),
 ('C30',192,88,0),('C31',187,95,90)]:
    put(ref,x,y,rot)
p['Q11']['reason']='Thermal coupling beside motion common-source copper; keep collector/base trace clear of force copper'
p['C3']['reason']='31.5x13mm film body and27.5mm lead pitch; retain24mm enclosure height clearance'
p['C10']['reason']=p['C3']['reason']

for idx,base_x in [(3,40),(4,90)]:
    rb=40+(idx-3)*10;cb=20+(idx-3)*5
    put('U'+str(idx),base_x,176,0,'eFuse local input/output decouplers; bottomEP uses thermal ground vias')
    coords=[(-4,7,90),(-13,-5,90),(-9,-1,90),(-17,-5,90),(-13,2,90),
            (-16,9,90),(-12,9,90),(10,-5,90),(10,0,90)]
    for off,(dx,dy,rot) in enumerate(coords): put('R'+str(rb+off),base_x+dx,176+dy,rot)
    for off,(dx,dy,rot) in enumerate([(-6,3,90),(-5,-7,0),(6,-5,90)]):
        put('C'+str(cb+off),base_x+dx,176+dy,rot)

expected={c['ref'] for c in parts}
assert set(p)==expected, (sorted(expected-set(p)),sorted(set(p)-expected))
data=dict(metadata=dict(rev_a_engineering_prototype=True,rev_b_production=False,
    units='mm',angles='KiCad degrees; positive90 maps local bottom source row toward board right',
    board_size_mm=[360,300],status='Placement intent; CAD courtyard and routing verification remains authoritative',
    reserved_power_star_y_mm=[110,125],
    external_anchor_notes={'J1':[15,45],'J2':[15,115],'TH20':[68,50],'TH21':[164,65]},
    constraints=['No controller/support bodies inside y110..125 power star strip.',
        'Route Kelvin pairs before power pours; prevent sense-to-force shorts at shunt ends.',
        'U5 uses logic star ground; no high-current return through its reference.',
        'Film timer traces cross star strip only as insulated signal layers; guard from high-dVdt copper.',
        'Gate resistors have device-specific pads; no common resistor may replace individual parts.',
        'Part center proposals are not a completed high-current routing or assembly clearance proof.']),
    placements=p)
(HERE/'placement-power.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf-8')
print('Placed',len(p),'power components')
