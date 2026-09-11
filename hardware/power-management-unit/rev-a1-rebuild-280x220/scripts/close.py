"""Stop CAD changes, restore the validated best and document the actual outcome."""
from rebuild import *
from collections import Counter,defaultdict
import re

def freeze():
    r=read();assert not r['closed'] and all(c['completed'] for c in r['cycles'])
    assert len(r['cycles'])>=6 or r.get('stop_required') or (now()-START).total_seconds()>=160*60
    best=SCRATCH/'best.kicad_pcb';selected=next(c for c in r['cycles'] if c['pcb_sha256']==sha(best) and c['accepted'])
    previous=sha(BOARD)
    if previous!=sha(best):shutil.copyfile(best,BOARD)
    r.update(closed=True,stop_required='Six full cycles exhausted' if len(r['cycles'])>=6 else r.get('stop_required') or 'Editing deadline reached',
      closed_at=now().isoformat(),restored_from_sha256=previous,final_pcb_sha256=sha(BOARD),selected_cycle=selected['number'])
    write(LEDGER,r)
    write(ROOT/'release.json',{'cad_complete':False,'orderable':False,'fabrication_release':False,'assembly_release':False,'production_release':False,'wip':True,'state':'bounded_rebuild_closed_not_orderable','pcb_sha256':sha(BOARD),'selected_cycle':selected['number']})
    print('Frozen best cycle',selected['number'],sha(BOARD),flush=True)

def report():
    r=read();assert r['closed'] and r['final_pcb_sha256']==sha(BOARD)
    g=json.loads((OUT/'final-geometry.json').read_text(encoding='utf-8'));n=json.loads((OUT/'final-native.json').read_text(encoding='utf-8'))
    inv=json.loads((OUT/'final-invariants.json').read_text(encoding='utf-8'));drc=json.loads((OUT/'final-drc.json').read_text(encoding='utf-8'))
    assert g['pcb_sha256']==inv['pcb_sha256']==sha(BOARD)
    for rel,digest in n['inputs'].items():assert sha(ROOT.parent/rel)==digest
    assert sha(OUT/'final-erc.json')==n['checks']['erc']['sha256'] and sha(OUT/'final-drc.json')==n['checks']['drc']['sha256']
    assert n['checks']['erc']['exit'] in (0,5) and n['checks']['drc']['exit'] in (0,5),'No normal native completion'
    open_rows=defaultdict(list)
    for row in drc['unconnected_items']:
        names=[re.search(r'\[(.*?)\]',i['description']) for i in row['items']]
        names=[m.group(1) for m in names if m];assert names and len(set(names))==1
        open_rows[names[0]].append(row)
    assert sum(map(len,open_rows.values()))==g['open_connections'],'Report open-count cap or stale inputs'
    power={'BATT_FUSED_P','BATT_SENSED_P','MAIN_COMMON','SYS_BUS_P','MOTION_SENSED_P','MOTION_COMMON','MOTION_BUS_P','ARM_L_N','ARM_R_N','DRIVE_N','LIFT_N','CHOPPER_N','CHOP_DRAIN','PC_BUCK_IN_P','LOGIC_BUCK_IN_P','V5V','V3V3','AON_3V3','AON_FEED_MID','AON_LDO_IN','CHOP_10V'}
    ground={'BATT_N','LOGIC_GND','CHOP_GND','CHASSIS','PC_N','LOGIC_BUCK_N','LOGIC_5V_N','LIFT_24V_N'}
    def category(net):
        if net in ground:return 'Masse / Rueckleiter'
        if net in power:return 'Leistung / Versorgung'
        if any(w in net for w in ['KELVIN','SENSE','REF','ADC','IMON','NTC','_DIV','OVP','UVLO','PGTH','ILIM','_OV','_FB','_HYS','TEMP_MAIN','TEMP_MOTION']):return 'Messung / analoge Schwellen'
        return 'Steuerung / Kommunikation'
    nets=[{'net':net,'category':category(net),'connections':len(rows),'items':rows} for net,rows in sorted(open_rows.items(),key=lambda p:(category(p[0]),p[0]))]
    write(OUT/'final-open-nets.json',{'pcb_sha256':sha(BOARD),'open_connections':g['open_connections'],'distinct_open_nets':len(nets),'classification':'Functional grouping; BATT_N remains a high-current return despite the ground label. Active-low signals are not classified as ground by suffix.','nets':nets})
    lines=['# PMU Rev A.1 — 280 × 220 mm rebuild: Abschluss','',
      '**WIP — nicht bestellbar. Engineering prototype – not production qualified.**','',
      f"Branch: `{r['branch']}`. Nach {len(r['cycles'])} vollständigen Zyklen wurde die harte Zyklusgrenze erreicht. Bester übernommener Stand: Zyklus {r['selected_cycle']}. Weitere CAD-Änderungen sind gesperrt.",
      '',f"**{g['open_connections']} offene Verbindungen in {len(nets)} Netzen.** Native ERC: Exit {n['checks']['erc']['exit']}; DRC: Exit {n['checks']['drc']['exit']}. Schaltplanparität: {n['checks']['drc']['parity']} Befunde. Die Prozesse endeten regulär, ohne Timeout.",
      '',f"Platzierungsprüfung: {g['placement']['passed']}; {g['force']['passed_pairs']}/247 ursprüngliche Leistungspfad-Paare und {g['critical']['passed']}/46 kritische Pfade. Eingefrorene Regeln und Tap-Provenienz: {inv['passed']} ({inv['adopted']} übernommen, {inv['retired']} verworfen, zusammen 492).",'',
      '## Native DRC-Befunde','', '| Befund | Anzahl |','| --- | ---: |']
    lines += [f'| {k} | {v} |' for k,v in sorted(n['checks']['drc']['counts'].items())]
    lines += ['', '**Zusätzlicher offener Befund:** Derselbe Eingabesatz meldete in Zyklus 6 eine BATT_N-Verbindungsbreite von 0,2012 mm am Via (184; 106,4 mm), im abschließenden Nur-Lese-Lauf dagegen keinen Breitenfehler. Dieser Unterschied ist nicht geklärt. Der Befund bleibt offen; keine Ausnahme und kein Wiederholen bis zu einem sauberen Ergebnis. [Vergleich und exakte UUIDs](reports/final-native-consistency.json).']
    lines += ['', 'Die DRC-Offenliste ist vollständig und stimmt mit der nach dem Speichern neu geladenen KiCad-Konnektivität überein. Ein bestandener Teilnachweis ersetzt keine vollständige DRC- oder Fertigungsfreigabe.','',
      '## Versuchsgrenzen und Verlauf','', '| Zyklus | Übernommen | Offen | Leistung | Kritisch | Notiz |','| --- | --- | ---: | ---: | ---: | --- |']
    lines += [f"| {c['number']} | {c['accepted']} | {c['opens']} | {c['force']}/247 | {c['critical']}/46 | {c['note']} |" for c in r['cycles']]
    lines += ['',f"Autorouter-Aufrufe: {r['router_calls']} von maximal 4. Pro Lauf maximal 250 Durchgänge und 600 Sekunden insgesamt, Optimierer aus. Zeitfenster: {r['started_at']} bis spätestens 19:27 UTC; CAD-Stopp spätestens 19:07 UTC. Tatsächlicher Abschluss: {r['closed_at']}.",'',
      '## Bekannte Grenzen und ausgeführte Korrekturen','',
      '- Vollständig neue Platzierung aus dem ursprünglichen 360×300-mm-Rev-A-Entwurf. Kein kompaktes WIP-Kupfer als Quelle. 280 × 220 mm entsprechen 61.600 mm² und 42,96 % weniger Fläche.',
      '- Alle 425 Footprints, 40 Testpunkte, 48 Press-fit-Bohrungen, vier Befestigungen und der vollständige ESP32-Keepout bleiben geprüft. Kabelzugang und Montage werden geometrisch in 2D geprüft; ein gemessener 3D-Kabel-/Presswerkzeugaufbau fehlt.',
      '- Neue breite Leistungsflächen, kürzere Busbar-Kontaktabstände je dokumentierter Teilstrecke, lokale MOSFET-/Shunt-Bereiche und gezielte Kelvin-/Gate-Bäume. Die einzelnen Busbar-Abstände können auch größer geworden sein; der Geometriebericht enthält Alt/Neu je Kontaktpaar.',
      '- Zu dichte neue BATT_N-Viafelder blockierten die SYS-Zuleitung. Ein begrenzter Innenlagenkorridor wurde freigestellt; nur neue redundante Vias wurden entfernt. Originale Tap-Elemente bleiben geometrisch eingefroren.',
      '- Die eFuse-Ausgangsflächen erreichten die feinen Pins zunächst nicht. Reguläre lokale Fanouts schließen die Ausgangspins; J10 erhält einen separaten Innenlagenübergang ohne Auftrennen seiner äußeren Rückleitung.',
      '- Chopper-H-Gate-Escape, Feedback-/Entladungszweige und CHOP_SENSE wurden gezielt geführt. Der längere CHOP_GATE-Abgriff zu R305 und Q42 benötigt eine dynamische Kopplungsprüfung.',
      '- Ein erster AON-Flächenvorschlag unterbrach NT8→BC15 und wurde nur im Speicher verworfen. Der übernommene Vorschlag spart vorhandene Batterierückwege um 0,6 mm erweitert aus.',
      '- Der neue CHOP_10V-Baum auf B.Cu unterbrach sechs BATT_N-Pfade: nach frischem Fill nur 241/247. Der gesamte neue 10-V-Teilbaum wurde zurückgenommen und seine 22 entfernten Rückleiter-Vias exakt wiederhergestellt. Die neue CHOP_REF2V5-Führung auf In2 bleibt. Eine bloße Verringerung offener Verbindungen rechtfertigt keinen unterbrochenen Hochstromrückweg.',
      '- Neue Logikversorgungen und CAN-Bäume wurden explizit angelegt. Restliche Versorgung, analoge Schwellen, Schutzsignale, Warnungen und Verbindungen stehen in den folgenden Listen; ihre Vollständigkeit wird nicht aus den 247/46-Pfadprüfungen abgeleitet.',
      '- Der einzige digitale Autorouterlauf wurde nach mehr als 30 aufeinanderfolgenden Durchgängen ohne weitere Verbesserung vorzeitig beendet. Kein SES wurde importiert. Die letzten lokalen Korrekturen wurden anschließend nativ geprüft; die interne Router-Offenzahl ist keine native KiCad-Offenzahl.',
      '- Zusätzliche mechanische Prüfung: H4 hat nur 0,405 mm Courtyard-Abstand zu C245. Zwei J1-Pressfit-Lochabstände zum flachen Testpad TP1 unterschreiten konservativ 3 mm. Die Behandlung von TP1 durch das Presswerkzeug bleibt offen; keine stillschweigende Ausnahme. Siehe [mechanical-review.md](reports/mechanical-review.md).',
      '- Die dokumentierten Querschnitte sind Messstellen im tatsächlichen gefüllten Kupfer. Sie ersetzen weder eine globale Engstellenprüfung noch Stromaufteilungs-, Erwärmungs-, Schutztransienten- oder EMV-Messungen.',
      '- Keine Gerber, Bohr- oder Bestückungsfreigabedaten für diesen unvollständigen Stand erzeugt. Alte Rev-A-Fertigungsdaten passen nicht zu diesem Umriss. Keine Bestellung oder Bestromung erfolgt.',
      '', '## Offene Netze','', '| Gruppe | Netz | Offene Verbindungen |','| --- | --- | ---: |']
    lines += [f"| {v['category']} | `{v['net']}` | {v['connections']} |" for v in nets]
    lines += ['', 'Exakte Endpunkte und UUIDs: [final-open-nets.json](reports/final-open-nets.json).','', '## Dateien und Nachweise','',
      f'- [KiCad-Projekt](kicad/{NAME}.kicad_pro) und [Platine](kicad/{NAME}.kicad_pcb).',
      '- [Native Prozesscodes und alle Eingabehashes](reports/final-native.json).',
      '- [Geometrie: Zugriff, Press-fit, Antenne, Querschnitte, Flächen, Busbars und Pfade](reports/final-geometry.json).',
      '- Native Kupfervorschauen: [Oberseite](reports/WIP-top.svg), [Unterseite](reports/WIP-bottom.svg); [Platzierungsübersicht](reports/placement-review.png). Nur Sichtprüfung, keine Fertigungsdaten.',
      '- [Ergänzte ursprüngliche lokale Pfadlängen](reports/source-path-length-addendum.json); historische Nullwerte werden erklärt, nicht als Messung ausgegeben.',
      '- [Regel-/Quellen-/Tap-Prüfung](reports/final-invariants.json), [Ausführungsledger](ledger.json) und [Freigabestatus](release.json).','',
      '| Datei | SHA-256 |','| --- | --- |',f'| PCB | `{sha(BOARD)}` |',f"| Ursprüngliche Rev-A-PCB | `{r['baseline_pcb_sha256']}` |"]
    lines += [f'| {name} | `{sha(OUT/name)}` |' for name in ['final-erc.json','final-drc.json','final-native.json','final-geometry.json','final-invariants.json','final-open-nets.json']]
    lines += ['', 'Der ursprüngliche Rev-A-Stand und die früheren Versuchszweige werden nicht überschrieben. Rückfallweg: ursprünglicher Rev-A-P1-CAD-Stand unter `../rev-a/`. Der neue Stand bleibt ausschließlich auf dem separaten Rebuild-Branch.','']
    (ROOT/'FINAL_REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    (ROOT/'README.md').write_text(f"# PMU Rev A.1 — 280 × 220 mm rebuild\n\n**WIP — NICHT BESTELLBAR. Engineering prototype – not production qualified.**\n\nNeuer Layoutversuch auf `{r['branch']}` aus dem ursprünglichen Rev-A-CAD, geschlossen nach sechs vollständigen Prüfzyklen. {g['open_connections']} offene Verbindungen in {len(nets)} Netzen. Alle Freigabeflags bleiben false.\n\n[Abschlussbericht mit Grenzen, offenen Netzen und Hashes](FINAL_REPORT.md).\n\n[KiCad-Projekt öffnen](kicad/{NAME}.kicad_pro). Die Originalbibliotheken werden über relative Verweise aus `../rev-a/kicad` verwendet; das gesamte Repository gemeinsam behalten.\n\nCAD-Bearbeitung nach diesem Checkpoint gesperrt. Die Skripte dokumentieren den begrenzten Versuch; sie sind keine selbstlaufende, bestellfähige Leiterplattengenerierung.\n",encoding='utf-8')
    print('Report:',len(nets),'nets',g['open_connections'],'connections',flush=True)

if __name__=='__main__':
    if sys.argv[1]=='freeze':freeze()
    elif sys.argv[1]=='report':report()
