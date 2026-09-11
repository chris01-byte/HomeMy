"""Close an exhausted failed bounded search; condense evidence, never edit CAD."""
from collections import Counter,defaultdict
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
from bounded_checks import ROOT,LEDGER,sha,write,minutes

def digest(value):return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':')).encode()).hexdigest()

def main():
    ledger=json.loads(LEDGER.read_text(encoding='utf-8'))
    assert ledger['cycles'] and all(c['status']=='completed' for c in ledger['cycles'])
    assert ledger['cycles'][-1]['size']=='300x220' and not ledger['cycles'][-1]['progress_permits_next_cycle']
    assert all(c['result']=='failed' for c in ledger['cycles'])
    finals=[]
    for size in ['250x200','275x210','300x220']:
        board=ROOT/'kicad'/('HomeMy_PMU_RevA_'+size+'.kicad_pcb');p=ROOT/'results'/(board.stem+'.json');r=json.loads(p.read_text(encoding='utf-8'))
        assert not r.get('compact_final_report'), 'Already closed'
        number=str(max(map(int,r['cycle_summaries'])));s=r['cycle_summaries'][number]
        finalphase='cycle-'+number;g=r['geometry'].get('supplementary-final-read-only',r['geometry'][finalphase])
        assert sha(board)==s['pcb_sha256']==g['pcb_sha256']==r['invariants']['pcb_sha256']
        assert r['invariants']['passed'], 'Scope or source identity audit failed'
        s['critical_paths']=g['critical'];s['native_ratsnest_connections']=g['native_ratsnest_connections']
        s['counts_may_be_capped']=any(x['count']>=199 for x in s['drc_counts'])
        s['open_network_inventory_may_be_capped']=s['open_connections']>=499
        if size=='275x210':
            s['progress']['before_open_is_lower_bound']=True;s['progress']['decrease_is_lower_bound']=True
            for c in ledger['cycles']:
                if c['size']==size:c['progress']=s['progress']
        native=[];manifests={}
        for phase,kinds in r['checks'].items():
            for kind,v in kinds.items():
                inputs=v['input_hashes_sha256'];key=digest(inputs);manifests[key]=inputs
                raw=v.get('native_report',{});row={k:v[k] for k in ['process_exit_code','process_normal','passed','report_complete','report_sha256','wall_seconds','counts','open_connections','parity_findings'] if k in v}
                row.update(phase=phase,kind=kind,input_set_sha256=key,kicad_version=raw.get('kicad_version'),counts_may_be_capped=any(x['count']>=199 for x in v['counts']) or v['open_connections']>=499)
                if kind=='drc' and phase==finalphase:
                    examples=defaultdict(list)
                    for finding in raw['violations']:
                        if len(examples[finding['type']])<5:examples[finding['type']].append(finding)
                    row['finding_examples_by_type']=dict(examples)
                native.append(row)
        # Original explicit adoption records remain reproducible; omit duplicate
        # native dumps and transient per-route geometry from the compact report.
        actions={}
        for n,c in r['cycles'].items():
            action={'input_sha256':c['input_sha256'],'copper_preparation_sha256':c['copper_preparation_sha256'],
                'removed_unapproved_power_copper_count':len(c.get('removed_unapproved_power_copper',[])),
                'original_tap_inheritance':c['original_tap_inheritance']}
            for name in ['single_local_pass','explicit_power_stage','global_router']:
                if name in c:action[name]=c[name]
            if 'fragment_cleanup' in c:
                cleanup=c['fragment_cleanup'];action['fragment_cleanup']={k:v for k,v in cleanup.items() if k!='removed'};action['fragment_cleanup']['removed_count']=len(cleanup['removed'])
            if 'critical_reference_seed' in c:
                seed=c['critical_reference_seed'];action['critical_reference_seed']={k:v for k,v in seed.items() if k not in ('critical','local','reference_stitches','native_ratsnest_connections')}
                action['critical_reference_seed'].update(critical_nets=[{k:v for k,v in x.items() if k!='uuids'} for x in seed['critical']['adopted']],critical_rejected=seed['critical']['rejected'],local_net_count=len(seed['local']['adopted']),reference_stitch_count=len(seed['reference_stitches']),
                    in_memory_before_save_ratsnest_advisory=seed['native_ratsnest_connections'],advisory_note='Pre-save in-memory counter; only fresh loaded final-board geometry and native DRC determine final opens.')
            if 'global_router' in action and 'native_ratsnest_connections' in action['global_router']:
                action['global_router']['in_memory_before_save_ratsnest_advisory']=action['global_router'].pop('native_ratsnest_connections')
            actions[n]=action
        force=g['force'];force.pop('original_pair_checks',None)
        areas=defaultdict(float)
        for z in force.pop('zones'):areas[z['net']+' / '+z['layer']]+=z['area_mm2']
        force['filled_zone_areas_mm2']={k:round(v,4) for k,v in sorted(areas.items())}
        source=r.get('source',{'commit':ledger['wip_commit'],'path':'reports/routing-round-003/HomeMy_PMU_RevA.kicad_pcb','sha256':'6ed645fb3d2c6d22e68b48f5c53482f9391e65429ced608e0dd31965875e9267'})
        output={'compact_final_report':True,'board':r['board'],'source':source,'final':s,'native_runs':native,'native_input_sets_sha256':manifests,'initial_native_ratsnest_connections':r['geometry'].get('initial',{}).get('native_ratsnest_connections'),'geometry':g,'invariants':r['invariants'],'cycle_actions':actions,
            'evidence_note':'All native type/severity totals and report hashes retained. Full timestamped native JSON/logs remain in the local scratch directory; this compact report includes up to five examples per final DRC type. Counts at KiCad caps are lower bounds. Saved-source hashes and final reloaded-board counts are authoritative.'}
        if 'derivation' in r:
            d=r['derivation'];groups=defaultdict(list)
            for ref,delta in d['rigid_footprint_translations_mm'].items():groups[tuple(delta)].append(ref)
            output['derivation']={k:v for k,v in d.items() if k!='rigid_footprint_translations_mm'}
            output['derivation']['translation_groups']=[{'delta_mm':list(delta),'refs':sorted(refs)} for delta,refs in sorted(groups.items())]
        write(p,output);finals.append((size,output,p))
    ledger.update(status='completed_without_qualified_size',stop_required='Allowed size ladder exhausted without a pass; no further engineering or optimization',engineering_finished_utc=datetime.now(timezone.utc).isoformat(),elapsed_minutes_to_close=round(minutes(ledger),2))
    write(LEDGER,ledger)
    release={'revision':'A.1 bounded WIP','selected_size':None,'cad_release':False,'fabrication_release':False,'assembly_release':False,'production_release':False,'orderable':False,'state':'bounded_search_failed','engineering_prototype_notice':'Engineering prototype – not production qualified',
             'baseline_commit':ledger['baseline_commit'],'frozen_wip_commit':ledger['wip_commit'],'results':{size:{'pcb_sha256':r['final']['pcb_sha256'],'report_sha256':sha(p)} for size,r,p in finals},'thermal_hardware_validation_performed':False}
    write(ROOT/'release.json',release)
    lines=['# PMU Rev A.1 – Ergebnis der begrenzten Verkleinerung','',
        '**Abbruch: Im erlaubten Suchraum wurde keine freigabefähige Verkleinerung erreicht. Kein Stand ist bestellbar.**','',
        'Engineering prototype – not production qualified. Fertigungs-, Bestückungs- und Produktionsfreigabe bleiben `false`. Rev A und der eingefrorene WIP-Branch wurden nicht verändert. Dies ist das Ergebnis dieses begrenzten Versuchs, kein allgemeiner Unmöglichkeitsnachweis für diese Abmessungen.','',
        'Arbeitsbranch: `codex/pmu-rev-a1-bounded-shrink`. Basis: `'+ledger['baseline_commit']+'`. WIP-Quelle: `'+ledger['wip_commit']+'`.','',
        f"Arbeitszeit bis zum dokumentierten Abschluss: {ledger['elapsed_minutes_to_close']:.2f} Minuten, einschließlich Branch-/Kontextvorbereitung ab {ledger['started_utc']}. {len(ledger['cycles'])}/5 Bearbeitungszyklen und {ledger['native_drc_calls']}/8 native DRC-Aufrufe. Grenzen: 150 Minuten insgesamt, ab Minute 140 nur Sicherung/Dokumentation; keine Registry-Änderung. Kein nativer ERC-/DRC-Absturz oder Timeout in diesem Auftrag.",'',
        '| Größe | Fläche | Zyklen genutzt/erlaubt | Offene Verbindungen / betroffene Netze | DRC-Fehler | Dangling Tracks / Vias | ERC-Fehler | Parität | ERC-/DRC-Exit |','|---|---:|---:|---:|---:|---:|---:|---:|---|']
    for size,r,p in finals:
        s=r['final'];w,h=map(int,size.split('x'));c=Counter({x['type']:x['count'] for x in s['drc_counts']});used=sum(x['size']==size for x in ledger['cycles']);prefix='≥' if s['counts_may_be_capped'] else ''
        lines.append(f"| {size.replace('x',' × ')} mm | {w*h:,} mm² | {used}/{ledger['limits']['cycles'][size]} | {s['open_connections']} / {s['affected_nets']} | {prefix}{s['drc_errors']} | {c['track_dangling']} / {c['via_dangling']} | 0 | {s['schematic_parity']} | {s['erc_exit_code']} / {s['drc_exit_code']} |")
    lines += ['', 'Alle finalen ERC-Prüfungen endeten regulär mit Exit 0; alle finalen DRC-Prüfungen regulär mit Exit 5 wegen Befunden. Vollständige Schaltplanparität und `--all-track-errors` waren aktiviert. Keine bestandene DRC-Prüfung und keine CAD-Freigabe.','',
        '## Ausgangsdaten, Fortschritt und genaue Nachweise','']
    for size,r,p in finals:
        s=r['final'];pr=s['progress'];initial=r['native_runs'][0];g=r['geometry'];force=g['force']
        lines += [f"### {size.replace('x',' × ')} mm",'',f"Quelle: `{r['source']['path']}`, SHA-256 `{r['source']['sha256']}`.",f"Finale PCB-SHA-256: `{s['pcb_sha256']}`. Kompakter [Ergebnisbericht](results/{p.name}) einschließlich Quellhashes, Netzliste, DRC-Typen, Prüfhashes und Geometrie.",'',
            f"Fortschritt: {'mindestens ' if pr.get('before_open_is_lower_bound') else ''}{pr['before_open']} → {pr['after_open']} offene Verbindungen; DRC-Fehler {pr['before_drc_errors']} → {'mindestens ' if s['counts_may_be_capped'] else ''}{pr['after_drc_errors']}. Fortschrittskriterium: **nicht erfüllt**. Kein weiterer Zyklus dieser Größe.",
            f"Geometrie: {g['placement']['footprints']} Footprints, {g['placement']['testpoints']} Testpunkte; Platzierung, 2D-Anschluss-/Probezugang, Press-fit-Geometrie und vierlagiger Antennen-Keepout bestanden. {force['passed_pairs']}/{force['total_pairs']} ursprüngliche lagenbezogene Leistungspaarprüfungen bestanden; zusätzlicher DRIVE-Rückleiter auf B.Cu: {force['compact_drive_return']['passed']}. {g['critical']['passed']}/{g['critical']['total']} explizite kritische Leiterpfade gefunden.",'',
            'Endgültige DRC-Typen: '+', '.join(f"`{x['type']}` ({x['severity']}): {x['count']}" for x in s['drc_counts'])+'. Kurzschluss-, Clearance-, Leiterbahnbreiten-, Via-/Bohrungs- und Paritätsbefunde: 0, soweit nicht ausdrücklich oben aufgeführt.','',
            'Offene Netze (Verbindungszahl): '+', '.join(f'`{net}` {n}' for net,n in s['open_networks'].items())+'.','',
            'Finale native Berichthashes:']
        for n in r['native_runs']:
            if n['phase']=='cycle-1' and n['kind']=='drc' or n['kind']=='erc' and (n['phase']=='cycle-1-library-path' or size!='250x200' and n['phase']=='cycle-1'):
                lines.append(f"- {n['kind'].upper()}: `{n['report_sha256']}` (Exit {n['process_exit_code']}).")
        lines.append('')
    lines += ['## Technische Blockaden und Grenzen','',
        '- 250 mm: unzulässig übernommene dünne Leistungskupferstücke entfernt; nur original nachgewiesene Abgriffgeometrie zugelassen. Der einzelne lokale Routingpass schloss keine zusätzliche Verbindung. Das regelkonforme Entfernen dieser Stücke vergrößerte die offene Verbindungsliste; mindestens 199 Kupferengstellen bleiben.',
        '- 275 mm: ein globaler Routingkandidat, anschließend native Prüfung. Fünf neue Engstellen sowie unterbrochene LIFT-/5-V-Rückleiter verhindern einen zweiten Zyklus. Das ursprüngliche DRIVE-F.Cu-Paar bleibt separat als fehlend erfasst; der neue B.Cu-Rückleiter ersetzt diesen historischen Lagenvergleich nicht stillschweigend.',
        '- 300 mm: R40 und R56 einmalig versetzt; dadurch alle zwölf originalen eFuse-Eingangsfächer/-spinen übernommen. Geschützte breite DRIVE-/LIFT-Rückleiter, zwei DC/DC-Ausgangsnetze und LED-Verteilung ergänzt. Ein globaler Routingkandidat; keine Wiederholung mit geringfügig geänderten Einstellungen.',
        '- Die geplante 4-mm-SYS-Zuleitung bei X=110 kreuzt 45 vorhandene BATT_N-Leistungsvias. Die geplanten PC-/Logic-Rückleiter treffen weitere Via-Felder; der Logic-Rückleiter überlappt zusätzlich einen originalen SYS-Abgriff um etwa 0,125 mm. Diese Vorschläge wurden verworfen; die Via-Felder wurden dafür nicht ausgedünnt.',
        '- Beim 300-mm-Stand waren 162/492 ursprüngliche Abgriffstücke übernehmbar. 301 Stücke über mehrere unterschiedlich verschobene Bauteile besitzen keine gemeinsame starre Abbildung; 29 weitere kollidieren mit Testpunkten, Logikpads oder Arm-Sternkontakten. Kein neuer dünner Leiter wurde deshalb als Ausnahme deklariert.',
        '- Geometrieberichte enthalten feste Kupferquerschnitte, Via-Anzahlen, 40-mm-FET-Kupferfenster und Busbar-Kontaktabstände. Diese sind keine globale Minimum-Cut-, Stromteilungs- oder Ampazitätsqualifikation. Kontaktabstände sind keine freigegebenen Busbar-Zeichnungen. Räumlicher Kabelbaum, Presswerkzeug, Gehäuse und Wärmeabfuhr bleiben physisch zu validieren.',
        '- Keine thermische Hardwarevalidierung, Bestromung, Batterie-, Motor- oder Aktorprüfung. Keine Fertigungsdaten oder Bestellpakete erzeugt. Alle 425 Bauteil-/Footprintidentitäten, 40 Testpunkte, Schaltung, Netzklassen, Regeln, Stackup und Press-fit-Abmessungen bleiben erhalten.',
        '', '## Evidenz und Reproduzierbarkeit','',
        'KiCad 10.0.6 wurde nativ ausgeführt. Der Router lief je größerer Größe einmal, mit einem Worker, höchstens 200 internen Pässen und 480 Sekunden. Seine internen Fehler/Verbindungszahlen wurden nicht als KiCad-Ergebnis ausgegeben. Nur `latest.ses` wurde je Lauf einmal importiert, nach Prüfung der Quellhashes; Seed-Kupfer, geschützte UUIDs/Gruppen, Pads, Platzierung und Flächen mussten erhalten bleiben.',
        '', 'KiCad begrenzt lange Befundlisten (hier 199 je Fehlertyp beziehungsweise 499 offene Einträge). Solche Zahlen sind als Untergrenzen gekennzeichnet; beim 300-mm-Ausgangsstand lieferte der frisch geladene native Ratsnest-Zähler 809 Verbindungen. Endzahlen offener Verbindungen stammen aus frisch geladenen finalen PCBs und stimmen mit den nicht begrenzten Verbindungslisten der nativen Endberichte überein. Der erste 250-mm-ERC-Lauf meldete wegen eines falschen lokalen Symbolbibliothekspfads Warnungen; nach dessen Korrektur wurde ERC regulär mit Exit 0 wiederholt.',
        '', 'Die Rohberichte und Routerlaufdateien bleiben lokal unter `tools-local/bounded-shrink-native`; im Repository verbleiben je Größe eine aktive PCB-Datei und ein kompakter Ergebnisbericht. Keine DSN-/SES-Dateien, .class-Dateien, Python-Caches, .kicad_prl-Dateien oder Routerlogs werden übernommen. `bounded-ledger.json` beendet weitere automatische Bearbeitung.']
    (ROOT/'BOUNDED_SHRINK_RESULT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    (ROOT/'README.md').write_text('# PMU Rev A.1 – begrenzter WIP-Versuch\n\n**Nicht bestellbar. Keine Größe hat bestanden.**\n\nEngineering prototype – not production qualified.\n\nMaßgeblich sind [Abschlussbericht](BOUNDED_SHRINK_RESULT.md), [Freigabestatus](release.json) und [Zyklen-/Prüfledger](bounded-ledger.json).\n\nDie drei KiCad-Projekte in `kicad/` sind eingefrorene Versuchsergebnisse für 250 × 200, 275 × 210 und 300 × 220 mm. Die 15 gemeinsamen Schaltplanblätter stammen unverändert aus Rev A; Bibliotheken werden relativ aus `../rev-a/kicad/` eingebunden. Pro Größe liegt ein kompakter Bericht unter `results/`.\n\nDer bisherige Rev-A-Ausgangsstand bleibt separat unter `../rev-a/`. Dieser Versuch ersetzt dessen PCB oder Prototyp-Fertigungspaket nicht. Weitere Bearbeitung benötigt einen neuen ausdrücklichen Auftrag; die automatische Größenleiter ist beendet.\n',encoding='utf-8')
    print('Closed failed bounded search at',ledger['elapsed_minutes_to_close'],'minutes;',len(ledger['cycles']),'cycles;',ledger['native_drc_calls'],'native DRC calls',flush=True)

if __name__=='__main__':main()
