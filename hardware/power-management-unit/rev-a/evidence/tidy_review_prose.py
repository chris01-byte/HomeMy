from pathlib import Path
p=Path(__file__).with_name('REVIEWED_DEFAULT_ERC_DRC.md')
s=p.read_text(encoding='utf-8')
replacements={
'on2026':'on 2026','KiCad10':'KiCad 10','under`erc`':'under `erc`','serializes`rule_severities`':'serializes `rule_severities`',
'andU30':'and U30','mixedSMD/PTH':'mixed SMD/PTH','explicit0.15-mm':'explicit 0.15 mm','contains47':'contains 47','is0.15':'is 0.15','uses0.20-mm':'uses 0.20 mm','and0.20-mm':'and 0.20 mm','contains“':'contains “','allU references':'all U references','separate47-package':'separate review of 47 packages','from0.15-mm':'from 0.15 mm','sole0.20-mm':'sole 0.20 mm',
'time2026':'time, 2026','|19:':'| 19:','|18:':'| 18:','|0 violations':'| 0 violations','|631errors,58warnings;499unconnected':'| 631 errors, 58 warnings; 499 unconnected','|499errors':'| 499 errors',';0other':'; 0 other','identifyKiCad':'identify KiCad',
'shaped2-mm':'shaped 2 mm','bars,15BC':'bars, 15 BC','eightNB':'eight NB',';160vias':'; 160 vias','reads116/104/189/148/117/215':'read 116 / 104 / 189 / 148 / 117 / 215','and759BATT_N':'and 759 BATT_N','establish160':'establish 160','PCB-005:7461103':'PCB-005: 7461103','right-angleM5':'right-angle M5','is14':'is 14','abovePCB':'above PCB','specifyingTg170':'specifying Tg 170','and1.60':'and 1.60','**including**0.02':'**including** 0.02','leaving1.58':'leaving 1.58','toTg125..135,0.15/1.09/0.15-mm':'to Tg 125–135, 0.15 / 1.09 / 0.15 mm','excludingmask':'excluding masks','corners27.65':'corners 27.65','Current226-kΩ':'The current 226 kΩ','gives29.3112':'gives 29.3112','and27.891':'and 27.891',
}
for a,b in replacements.items():s=s.replace(a,b)
s=s.replace('including coarse-pitch parts; that title alone is not evidence of a separate review of 47 packages manufacturer review.','including coarse-pitch parts; that title alone is not evidence that the manufacturer documentation for all 47 packages was separately reviewed.')
p.write_text(s,encoding='utf-8')
q=Path(__file__).with_name('review_filled_power.py')
s=q.read_text(encoding='utf-8')
replacements={
 'globalminimum':'global minimum','currentcapacity':'current capacity','outsideleadbank':'outside lead bank','Armpositive':'Arm positive','Rightpositive':'Right positive','atjunction':'at junction','StarcrossedbySYSfeed':'Star crossed by SYS feed','Starunderleftarmterminal':'Star under left arm terminal','Starunderrightarmterminal':'Star under right arm terminal','Leftarmreturn approachingNT1':'Left arm return approaching NT1','Rightarmreturn approachingNT2':'Right arm return approaching NT2','Q40source belowbank':'Q40 source below bank','Capnegative trunknearC312positive':'Cap negative trunk near C312 positive','Chopperreturn':'Chopper return','Q40drain':'Q40 drain','Chopperdrain connectorneck':'Chopper drain connector neck','Drive returnvertical':'Drive return vertical','Liftreturninner1':'Lift return inner 1','Liftreturninner2':'Lift return inner 2','LEDpositive':'LED positive','LEDreturn':'LED return','Fixed0.02mm':'Fixed 0.02 mm',
 'Nativeconnectedpad lists include physicalnettie bridges asappropriate; noexternalbarsaddedtonativecoppermodel.':'Native per-layer pad connection flags are local adjacency checks; they do not prove connection to the complete net. No external bars are added to the native copper model.',
 'Perfieldviaresistanceassumesallcountedvia barrels sharecurrentuniformly; viafieldtotalisnotlocalarrayproof.':'Per-field via resistance assumes that all counted barrels share current uniformly; a field total does not establish a local transfer rating.',
 'Noresistance,temperature,SOAorpressfitmeasurementperformed.':'No resistance, temperature, SOA or pressfit measurement was performed.',
 'R=rho(T)*L/(N*pi*d*t),d=.4mm,t=.025mm,L=1.6mm; rho20=1.724e-8ohmm,alpha=.00393/K':'R = rho(T) * L / (N * pi * d * t); d = 0.4 mm, t = 0.025 mm, L = 1.6 mm; rho20 = 1.724e-8 ohm m, alpha = 0.00393/K'
}
for a,b in replacements.items():s=s.replace(a,b)
q.write_text(s,encoding='utf-8')
