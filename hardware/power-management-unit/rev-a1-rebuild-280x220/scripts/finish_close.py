"""Close this one Phase-0-blocked run without loading or changing CAD."""
from collections import Counter, defaultdict
from pathlib import Path
import json, re
from finish_run import ROOT, CAD, BOARD, OUT, LEDGER, EXPECTED, sha, write, read, now, inputs, guard


def close():
    r = guard()
    assert not r['closed'] and not r['cycles'] and r['router_calls'] == 0
    assert sha(BOARD) == EXPECTED
    names = ['basis-refill-drc', 'basis-refill-configured-drc',
             'basis-refill-direct-drc', 'basis-erc']
    receipts = {n: json.loads((OUT/(n+'-receipt.json')).read_text(encoding='utf-8')) for n in names}
    current = inputs()
    historical = json.loads((ROOT/'reports/final-native.json').read_text(encoding='utf-8'))
    assert current == historical['inputs'], 'Historical evidence inputs differ'
    for n, receipt in receipts.items():
        assert receipt['inputs_before'] == receipt['inputs_after'] == current
        assert receipt['process']['timed_out'] and receipt['process']['exit'] is None
        assert sha(OUT/(n+'.json')) == receipt['report_sha256']
    direct = receipts['basis-refill-direct-drc']['process']
    assert direct['poll_at_timeout'] is None, 'Native process was already stopped'
    assert direct['output_transport'].startswith('workspace files')

    runs = [{'name': n, 'kind': 'erc' if n.endswith('-erc') else 'drc',
             'exit': v['process']['exit'], 'timed_out': v['process']['timed_out'],
             'seconds': v['process']['seconds'], 'counts': v['counts'],
             'opens': v['opens'], 'parity': v['parity'],
             'report_sha256': v['report_sha256'],
             'receipt_sha256': sha(OUT/(n+'-receipt.json')),
             'process_sha256': sha(OUT/(n+'-process.json'))} for n, v in receipts.items()]
    last = json.loads((OUT/'basis-refill-direct-drc.json').read_text(encoding='utf-8'))
    prior = json.loads((ROOT/'reports/final-open-nets.json').read_text(encoding='utf-8'))
    categories = {v['net']: v['category'] for v in prior['nets']}
    groups = defaultdict(list)
    for connection in last['unconnected_items']:
        endpoint_nets = {re.search(r'\[([^]]+)\]', i['description']).group(1) for i in connection['items']}
        assert len(endpoint_nets) == 1
        groups[endpoint_nets.pop()].append(connection)
    nets = [{'net': n, 'category': categories[n], 'connections': len(v), 'items': v}
            for n, v in sorted(groups.items())]
    assert sum(v['connections'] for v in nets) == 293 and len(nets) == 112
    assert {v['net']: v['connections'] for v in nets} == {v['net']: v['connections'] for v in prior['nets']}
    write(OUT/'finish-open-nets.json', {
        'pcb_sha256': EXPECTED, 'open_connections': 293, 'distinct_open_nets': 112,
        'source_report': 'basis-refill-direct-drc.json',
        'source_sha256': sha(OUT/'basis-refill-direct-drc.json'),
        'native_process_completed': False,
        'classification': prior['classification'], 'nets': nets})
    width_reports = {n: [v for v in json.loads((OUT/(n+'.json')).read_text(encoding='utf-8'))['violations']
                        if v['type'] == 'connection_width'] for n in names if n.endswith('-drc')}
    write(OUT/'finish-width-findings.json', {
        'pcb_sha256': EXPECTED, 'reports': width_reports,
        'disposition': 'All reported findings remain unresolved. Report positions are item coordinates, not exact neck markers. No exclusion or rule change.'})
    preserved = {n: sha(ROOT/'reports'/n) for n in
                 ['final-native.json', 'final-geometry.json', 'final-invariants.json',
                  'final-open-nets.json', 'final-native-consistency.json', 'mechanical-review.md']}
    summary = {'pcb_sha256': EXPECTED, 'cad_inputs': current,
               'all_input_hashes_equal_historical_final': True,
               'all_before_after_input_hashes_identical': True, 'runs': runs,
               'phase0_passed': False, 'regular_native_completion': False,
               'direct_log_probe_process_alive_at_timeout': True,
               'fresh_force_and_critical_path_audit': 'not performed: Phase 0 native execution blocked',
               'historical_unchanged_board_evidence': {'force_pairs': '247/247', 'critical_paths': '46/46',
                    'frozen_rules_and_tap_provenance_passed': True, 'report_hashes': preserved},
               'open_connections': 293, 'open_nets': 112,
               'cad_changed': False, 'editing_cycles': 0, 'router_calls': 0}
    write(OUT/'finish-native-summary.json', summary)
    stopped = now().isoformat()
    r.update(closed=True, closed_at=stopped, phase='0',
             stop_reason='Native ERC/DRC produced reports but did not terminate normally. Final direct-file-output probe confirms the native DRC process remained alive at timeout. No verified Phase-0 baseline; stop without CAD edits.',
             native_restarts={'drc': 2, 'erc': 0}, native_attempts={'drc': 3, 'erc': 1},
             corrections=[{'cause': 'Fontconfig font directory/cache resolution', 'attempts': 1,
                           'result': 'Fontconfig diagnostics resolved; native completion still fails'},
                          {'cause': 'Distinguish pipe EOF wait from native process hang', 'attempts': 1,
                           'result': 'Direct file logs and Popen.wait confirm native process alive at 90-second deadline'}],
             selected_pcb_sha256=EXPECTED, selected_cad_source_commit=r['authorized_source_commit'],
             retained_without_geometry_edits=True, phase0_passed=False)
    write(LEDGER, r)
    release = json.loads((ROOT/'release.json').read_text(encoding='utf-8'))
    for flag in ['cad_complete', 'orderable', 'fabrication_release', 'assembly_release', 'production_release']:
        release[flag] = False
    release.update(wip=True, state='finish_blocked_native_checks_not_orderable',
                   pcb_sha256=EXPECTED, finish_report='FINISH_REPORT.md',
                   finish_ledger='finish-ledger.json', finish_cad_edits=0)
    write(ROOT/'release.json', release)

    lines = [
        '# PMU 280 × 220 mm — Abschluss des begrenzten Fertigstellungslaufs', '',
        '**WIP – NICHT BESTELLBAR. Engineering prototype – not production qualified.**', '',
        'Der neue Auftrag wurde in Phase 0 angehalten. ERC und DRC schreiben vollständige Berichte, '
        'beenden sich in dieser Agent-Umgebung aber nicht regulär. Der letzte DRC-Versuch mit direkter '
        'Dateiausgabe bestätigt einen bei Ablauf der 90 Sekunden noch laufenden nativen Prozess. '
        'Das ist kein bloßes Warten auf das Ende einer Ausgabepipe. Eine bestandene native Basis fehlt.', '',
        f"Branch: `{r['branch']}`. Auftragsstand: `0fdfd91ffdc3e5fd28f4c1715114b23c0d4dbe31`. "
        f"Unveränderte CAD-Ausgangsbasis: `{r['authorized_source_commit']}`.", '',
        f'PCB-SHA-256: `{EXPECTED}`.', '',
        '**Keine Routing-, Platzierungs- oder Kupferänderung.** Drei native Phase-0-Fill/Save-Aufrufe '
        'haben exakt dieselben PCB-Bytes hinterlassen. Projekt, Regeln, Schaltpläne und eingebundene '
        'Bibliotheken stimmen vollständig mit dem historischen finalen Eingabehashsatz überein. '
        'Es gibt keinen neuen CAD-Kandidaten; der vorhandene WIP-Checkpoint bleibt erhalten.', '',
        f"Laufbeginn: `{r['started_at']}`; CAD-Stopp/Abschlussledger: `{stopped}`. "
        '0 von 8 Editierzyklen, 0 von 1 Autorouter-Aufrufen. DRC: drei Versuche inklusive zweier '
        'Neustarts; ERC: ein Versuch. Die Schranken werden nicht ausgeschöpft, wenn die notwendige '
        'native Prüfung nicht ausführbar ist. Weitere CAD-Änderungen sind nach diesem Abschluss gesperrt.', '',
        '## Prüfergebnis', '',
        '| Prüfung | Ergebnis dieses Laufs |', '| --- | --- |',
        '| CAD-Identität | Start-, Vorher-/Nachher- und finaler PCB-Hash identisch; sämtliche erfassten CAD-Eingaben unverändert |',
        '| ERC | JSON: 0 Befunde; Prozess nach 90 s beendet, kein regulärer Exit-Code — **nicht bestanden** |',
        '| DRC | Alle drei Prozesse nach 90 s beendet; kein regulärer Exit-Code — **nicht bestanden** |',
        '| Schaltplanparität | Alle drei DRC-JSONs: 0 Befunde; wegen Prozessabbruch kein vollständiger Pass |',
        '| Offen | 293 Verbindungen in 112 Netzen in allen drei DRC-JSONs |',
        '| Dangling | 23 Leiterbahnen und 35 Vias in allen drei DRC-JSONs |',
        '| Silkscreen | 119 silk_over_copper + 76 silk_overlap in allen drei DRC-JSONs |',
        '| BATT_N / connection_width | Schwankende Befunde; alle bleiben offen, siehe vollständige Liste unten |',
        '| 247 Leistungspaare / 46 kritische Pfade | Historisch 247/247 und 46/46 auf byteidentischer PCB; **keine frisch abgeschlossene Pfadprüfung** |',
        '| Regeln, Tap-Provenienz, 280 × 220 mm, vier Lagen, 425 Footprints, 40 TPs, 48 Press-fit-Bohrungen, vier Befestigungen, Antennen-Keepout | Unveränderte CAD-Bytes erhalten den früheren Nachweis; keine neue vollständige native Prüfung |',
        '| Mechanik | H4/C245 und J1/TP1 bleiben offen; keine neue mechanische Freigabe |',
        '| Fertigung / Bestückung / Produktion | Alle Flags false; kein DRAFT-Prüfsatz erzeugt, da cad_complete nicht erreicht |', '',
        '## Native Versuche und Hashes', '',
        'Die folgenden JSONs sind Diagnoseevidenz. `exit: null` und `timed_out: true` bedeuten '
        'ausdrücklich keinen nativen Exit 0 oder Exit 5. Ein eventueller Exit 0 des Python-Protokollierers '
        'ist kein KiCad-Prüfergebnis. Befehle, Beginn, Dauer, stdout/stderr und vollständige '
        'Vorher-/Nachher-Hashes stehen in den zugehörigen `-process.json` und `-receipt.json`.', '',
        '| Bericht | Fehler connection_width | Zeit, s | SHA-256 |', '| --- | ---: | ---: | --- |']
    lines += [f"| [{v['name']}.json](reports/finish/{v['name']}.json) | {v['counts'].get('error:connection_width', 0) if v['kind']=='drc' else 'ERC: 0 Befunde'} | {v['seconds']:.3f} | `{v['report_sha256']}` |" for v in runs]
    lines += ['',
        'Alle DRC-Aufrufe verwenden `--schematic-parity --all-track-errors --severity-all '
        '--exit-code-violations --refill-zones --save-board` und die korrekten benachbarten '
        '.kicad_pro/.kicad_dru-Dateien. Zwischen Versuch 1 und 2 änderte sich die Fontconfig-Umgebung; '
        'zwischen Versuch 2 und 3 ausschließlich der Ausgabetransport und der Berichtsname. '
        'Diese Diagnoseschritte ersetzen nicht den verlangten reproduzierbaren, regulär beendeten Doppelcheck.', '',
        '## Fehlgeschlagene Ursachenklärung', '',
        '1. **Fontconfig:** Die Standardkonfiguration konnte Benutzerverzeichnisse und Cache nicht '
        'auflösen. Eine einzige lokale Konfigurationskorrektur verwendet dieselben Windows-Schriftverzeichnisse '
        'und einen beschreibbaren Workspace-Cache. Die Fontconfig-Fehler verschwinden; der native Timeout bleibt. '
        '[Konfigurationsnachweis](reports/finish/fontconfig-environment.json). Keine CAD- oder Regeländerung.',
        '2. **Prozessabschluss:** Ein einmaliger Wechsel von Pipes auf direkte Workspace-Logdateien '
        'und `Popen.wait()` bestätigt den noch laufenden nativen DRC-Prozess am Timeout. Nur dieser eigene '
        'Kindprozess wurde danach beendet. Kein erzwungener Erfolgs-Exit, keine Dialog-/Prüfunterdrückung.',
        '3. **Registry:** KiCad meldet verweigerten Zugriff auf `HKCU\\Software\\kicad-cli`. '
        'Das ist eine Beobachtung, keine bewiesene Ursache: der separat ausgeführte Versionsaufruf '
        'beendete sich trotz derselben Meldung regulär (10.0.6, Exit 0).',
        '4. **Native Aufräumphase:** KiCad 10.0.6 wartet nach CLI-Arbeiten auf den Threadpool '
        'und räumt Kifaces/Einstellungen/gemeinsame Ressourcen auf. Eine Blockade in diesem nach '
        'CAD-Laden erweiterten Pfad ist plausibel, wurde jedoch nicht durch eine Stackaufnahme lokalisiert. '
        '[CLI-Quellcode](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/kicad/kicad_cli.cpp#L557).', '',
        '## Offene Breitenprüfung', '',
        'Der bekannte F.Cu-Befund nennt BATT_N-Via `3f25db10-a5fc-4042-be5f-f7b44be8e08f` '
        'bei (184; 106,4) mm und CHOP_SENSE-Pad R304.1 `e250d50b-0ffb-40d1-abb0-3ea6750e749b` '
        'bei (182; 104,9125) mm beziehungsweise dessen Leiterbahn '
        '`73040b97-7918-47e3-bdc0-d79745ef74e4`. Gemeldet: 0,2012 mm gegenüber 1,0000 mm.', '',
        'Versuch 1 nennt zusätzlich 0,9180 mm auf B.Cu an LOGIC_GND-Via '
        '`83bd7ad9-613d-4faf-81a6-f2947d5b2cc0` und BATT_N-Zone '
        '`e90d672b-8c09-4079-ab7a-916c59c7d788`, sowie 0,2071 und 0,2000 mm auf F.Cu '
        'mit PC_DVDT-Leiterbahn `94b162b0-e155-49eb-b181-223818e67e7c` und U3.8 '
        '`cab1b7a3-2f47-4878-9002-8b91b183f7ec`. '
        '[Sämtliche Befunde je Versuch mit exakten Objekt-UUIDs](reports/finish/finish-width-findings.json).', '',
        'Eine Quellcodeprüfung findet bei der Engstellenzuordnung eine ungeordnete Sammlung naher '
        'Kupferobjekte ohne Netzfilter und eine Regelauswertung anhand der ersten beiden Treffer. '
        'Das ist eine mögliche Erklärung der schwankenden Zuordnung, **kein bewiesener Fehlalarm an '
        'dieser Platine**. JSON enthält nur zwei zugeordnete Objekte und deren Positionen, '
        'nicht beide tatsächlichen Halsendpunkte. Zur Klärung sind Markerposition, geprüfte Polygon-Netz-ID, '
        'Halsenden und vollständige geordnete Treffer-/Regelpaarliste nötig. '
        '[Breitenprüfer](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/pcbnew/drc/drc_test_provider_connection_width.cpp#L359), '
        '[RTree-Ergebnismenge](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/pcbnew/drc/drc_rtree.h#L428), '
        '[JSON-Serialisierung](https://github.com/KiCad/kicad-source-mirror/blob/10.0.6/common/rc_item.cpp#L175).', '',
        'Keine Breitenregel abgeschwächt, kein Befund ausgenommen, kein Via entfernt, um eine Meldung '
        'zum Verschwinden zu bringen. Auch zusätzliche Meldungen bleiben unaufgelöst.', '',
        '## Lokale Routing- und Mechanikpunkte', '',
        '- **U2.2/BATT_N:** Pad `e7d6e7d1-12be-470d-9006-5679037f532f` bei (153,8; 76,25) mm '
        'hat keinen angeschlossenen Fanout. Eine neue Verbindung nach allgemeinen Hochstrom-Mindestmaßen '
        'passt nicht direkt an das 1,45 × 0,30-mm-Pad bei 0,5-mm-Pitch. Der ursprünglich erfasste '
        '0,2-mm-Tap `ad7b84ed-b805-401d-a6ce-68225593656f` ist derzeit als retired dokumentiert. '
        'Seine exakte Wiederübernahme mit ursprünglicher Gruppe und transformierter Geometrie '
        '(153,8; 76,25) → (152,0751; 76,25) mm ist ein lokaler Reparaturkandidat ohne neue Regelausnahme. '
        'Capture bleibt unverändert; Disposition und Padanker wären nachzuführen. Das einzelne Segment '
        'schließt noch keinen vollständigen Rückweg. Keine Umsetzung oder native Validierung in diesem Lauf.',
        '- **Versorgungen:** Lesende lokale Prüfungen finden kurze Kandidaten in AON_3V3, V5V, '
        'CHOP_10V und CHOP_GND. Sie sind keine geprüften Routingfortschritte. AON-LDO-/Feed-Escapes '
        'und längere Chopper-Verbindungen kollidieren mit bestehenden Rückleitern, Feedback- oder '
        'Gate-Kupfer. Der historische CHOP_10V-B.Cu-Baum, der sechs BATT_N-Leistungspaare trennte, '
        'wurde nicht wiederholt. Die 247/46-Nachweise allein belegen nicht die Versorgung jedes Controllerpins.',
        '- **Mechanik:** H4/C245: 0,405 mm Courtyard-Abstand; Schrauben-/Scheiben-/Werkzeugkontur fehlt. '
        'J1-Pad 1/2 zu TP1: 1,96164 / 2,77096 mm gegenüber konservativ 3 mm. TP1 ist ein flaches '
        'unbestücktes Testpad, aber seine Behandlung im Presswerkzeug ist nicht freigegeben. '
        'Montage, Kabelbiegeradien, Busbar-Isolation und Pressauflage benötigen weiter den tatsächlichen '
        'mechanischen Aufbau. [Unveränderte mechanische Evidenz](reports/mechanical-review.md).', '',
        '**Die geometrische Unlösbarkeit von 280 × 220 mm oder die Notwendigkeit einer größeren '
        'Platine ist durch diesen Lauf nicht nachgewiesen.** Der unmittelbare Blocker ist die nicht '
        'regulär ausführbare native Phase 0. Mehr Routingzeit allein behebt ihn nicht.', '',
        '## Konkreter nächster Ingenieurschritt', '',
        'Den unveränderten vollständigen Eingabesatz mit KiCad 10.0.6 in einer normalen Windows-Sitzung '
        'prüfen; stdout/stderr direkt in Dateien schreiben und den tatsächlichen Prozessstatus separat '
        'erfassen. Falls der Prozess nach der Berichtsausgabe weiterläuft, eine Thread-Wait-Chain oder '
        'Stackaufnahme des eigenen Prüfprozesses sichern. Erst daraus eine gezielte Umgebungs- oder '
        'Herstellerkorrektur ableiten. Registry-Zugriff als Ursache nicht voraussetzen.', '',
        'Danach zwei frisch geladene, identische native Eingabesätze mit regulärem Prozessabschluss '
        'vergleichen und die Breitenmarker mit Halsgeometrie/Regelzuordnung auflösen. Erst mit belastbarer '
        'Basis ist ein weiterer ausdrücklich begrenzter Routingauftrag sinnvoll. U2.2 samt '
        'nachgewiesenem Originaltap ist dann ein konkreter erster lokaler Kandidat; Regeln bleiben unverändert.', '',
        '## Vollständige Restnetzliste', '',
        'Alle 293 offenen Verbindungen mit beiden Beschreibungen, Koordinaten und UUIDs stehen in '
        '[finish-open-nets.json](reports/finish/finish-open-nets.json), direkt aus dem letzten nativen '
        'DRC-Bericht dieses Laufs. Funktionale Gruppierung wird aus dem früheren Bericht übernommen '
        'und gegen jede Netzanzahl geprüft. BATT_N bleibt auch in der Massegruppe ein Hochstromrückleiter.', '',
        '| Gruppe | Netz | Offen |', '| --- | --- | ---: |']
    lines += [f"| {v['category']} | `{v['net']}` | {v['connections']} |" for v in nets]
    lines += ['', '## Nachweise und Rückfallweg', '',
        '- [Kompakter Prüf-/Hashvergleich](reports/finish/finish-native-summary.json).',
        '- [Abschlussledger](finish-ledger.json) und [Freigabestatus](release.json).',
        '- [Historischer Rebuild-Abschluss](FINAL_REPORT.md) bleibt unverändert und ist keine frische Prüfung.',
        '- `FINISH_SHA256SUMS` ist das neue vollständige Manifest dieses Verzeichnisses. Das ältere '
        '`SHA256SUMS` bleibt historische Evidenz des früheren Rebuild-Commits.',
        '- Ursprüngliches Rev-A-CAD, RevA-P1-Paket und frühere Varianten bleiben unverändert. '
        'Dieser Lauf bleibt auf dem bestehenden separaten Rebuild-Branch. Keine Bestellung, '
        'Bestückung oder Bestromung.', '']
    (ROOT/'FINISH_REPORT.md').write_text('\n'.join(lines), encoding='utf-8', newline='\n')
    (ROOT/'README.md').write_text(
        '# PMU Rev A.1 — 280 × 220 mm rebuild\n\n'
        '**WIP – NICHT BESTELLBAR. Engineering prototype – not production qualified.**\n\n'
        'Der neue begrenzte Fertigstellungslauf vom 2026-09-13 ist in Phase 0 geschlossen: '
        'native ERC-/DRC-Prozesse schreiben Berichte, enden aber nicht regulär. '
        'Keine CAD-Änderung; weiterhin 293 offene Verbindungen in 112 Netzen. Alle Freigabeflags false.\n\n'
        '[Aktueller Abschlussbericht](FINISH_REPORT.md), [Prüfevidenz](reports/finish/finish-native-summary.json) '
        'und [historischer Rebuild-Abschluss](FINAL_REPORT.md).\n\n'
        '[KiCad-Projekt öffnen](kicad/HomeMy_PMU_RevA1_Rebuild_280x220.kicad_pro). '
        'Originalbibliotheken werden relativ aus `../rev-a/kicad` eingebunden; das Repository gemeinsam behalten.\n\n'
        'CAD-Bearbeitung nach diesem Checkpoint gesperrt. `FINISH_SHA256SUMS` bezeichnet den aktuellen '
        'Nachweissatz; `SHA256SUMS` den historischen Rebuild. Die Skripte dokumentieren den begrenzten Lauf.\n',
        encoding='utf-8', newline='\n')
    state = ROOT.parents[2]/'CURRENT_STATE.md'
    text = state.read_bytes().decode('utf-8')
    anchor = '- No capability from roboter_ws has been copied into HomeMy code.'
    line = ('- The separately authorized 2026-09-13 completion run for the existing 280 × 220-mm rebuild '
            'is closed in Phase 0 without CAD edits (0 edit cycles, 0 router calls). Three DRC attempts '
            'and one ERC attempt wrote reports but timed out; direct file logging confirms the final '
            'native DRC process was still running at the deadline. Fontconfig correction did not resolve '
            'native shutdown. PCB and all CAD inputs remain byte-identical to the previous rebuild; '
            '293 opens / 112 nets, variable width findings and the two mechanical issues remain. '
            'Earlier 247/247 and 46/46 evidence is preserved, not a new completed audit. All releases '
            'remain false. See [completion-run report](hardware/power-management-unit/rev-a1-rebuild-280x220/FINISH_REPORT.md).\r\n')
    assert anchor in text and '2026-09-13 completion run' not in text
    state.write_bytes(text.replace(anchor, line+anchor).encode('utf-8'))
    assert inputs() == current and sha(BOARD) == EXPECTED
    print('Closed Phase 0: unchanged PCB, 293 opens / 112 nets, native completion blocked.', flush=True)


if __name__ == '__main__':
    close()
