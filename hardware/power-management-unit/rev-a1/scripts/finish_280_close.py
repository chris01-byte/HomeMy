"""Documentation-only close of a stopped fixed-size task; no PCB writes."""
from collections import Counter
import json
import re
import shutil
from finish_280 import ROOT,OUT,BOARD,SOURCE,LEDGER,read,sha,write,now,elapsed,input_hashes

def main():
    r=read();assert r.get('stop_required')
    best=r['best']['label'];n=json.loads((OUT/(best+'-native.json')).read_text(encoding='utf-8'))
    g=json.loads((OUT/(best+'-geometry.json')).read_text(encoding='utf-8'))
    assert sha(BOARD)==g['pcb_sha256']==r['best']['metrics']['pcb_sha256']
    assert input_hashes(BOARD)==n['input_hashes_sha256']
    supplemental=json.loads((OUT/'final-reference-stitches.json').read_text(encoding='utf-8'))
    assert supplemental['pcb_sha256']==sha(BOARD)
    g['reference_stitches']=supplemental['reference_stitches']
    g['reference_note']='Final read-only reloaded audit covers the two specifically required U11 stitches. The compact source did not retain the full 153-stitch roster; early cycle helper read an empty roster and did not prove their attachment.'
    write(OUT/'final-geometry.json',g)
    write(OUT/'final-required-paths.json',{'pcb_sha256':sha(BOARD),'passed':g['force']['passed_pairs'],'total':g['force']['total_pairs'],'paths':g['force']['original_pair_checks']})
    write(OUT/'final-critical-paths.json',{'pcb_sha256':sha(BOARD),**g['critical']})
    write(OUT/'final-input-sha256.json',n['input_hashes_sha256'])
    for kind in ['erc','drc']:
        shutil.copyfile(OUT/(best+'-'+kind+'.json'),OUT/('final-'+kind+'.json'))
    raw=json.loads((OUT/'final-drc.json').read_text(encoding='utf-8'));nets=Counter()
    for v in raw['unconnected_items']:
        names={re.search(r'\[([^]]+)\]',i['description']).group(1) for i in v['items']};assert len(names)==1; nets.update(names)
    inventory={'open_connections':len(raw['unconnected_items']),'affected_nets':len(nets),'net_counts':dict(sorted(nets.items())),'full_native_report':'final-drc.json'}
    write(OUT/'final-open-networks.json',inventory)
    final={'state':'stopped_wip','cad_complete':False,'orderable':False,'fabrication_release':False,'assembly_release':False,'production_release':False,
           'best_cycle':best,'restored_best_pcb_sha256':sha(BOARD),'input_set_matches_validated_best':True,'all_70_native_inputs_identical':True,
           'native_report_provenance':'Byte-identical copies of the validated cycle-02 native reports; restored CAD bytes and all native inputs match. No extra routing/check cycle follows the stopping boundary.',
           'native_results':n['results'],'open_connections':len(raw['unconnected_items']),'affected_nets':len(nets),
           'force_passed':g['force']['passed_pairs'],'force_total':247,'critical_passed':g['critical']['passed'],'critical_total':46,
           'native_erc_calls':sum(x['kind']=='erc' for x in r['native_calls']),'native_drc_calls':sum(x['kind']=='drc' for x in r['native_calls']),
           'native_setup_invalid_calls':2,'cycles':len(r['cycles']),'autorouter_calls':len(r['router_calls']),
           'mechanical_screen_passed':g['placement']['passed'],'u11_reference_stitches':g['reference_stitches'],
           'final_erc_sha256':sha(OUT/'final-erc.json'),'final_drc_sha256':sha(OUT/'final-drc.json')}
    write(OUT/'final-state.json',final)
    release=json.loads((ROOT/'release.json').read_text(encoding='utf-8'))
    release.update(revision='A.1 fixed 280x220 WIP',target_size='280x220',selected_size=None,state='fixed_280x220_stopped_after_two_unsafe_cycles',cad_release=False,cad_complete=False,wip=True,orderable=False,fabrication_release=False,assembly_release=False,production_release=False)
    release['results']['280x220']={'pcb_sha256':sha(BOARD),'final_state_sha256':sha(OUT/'final-state.json'),'report':'FINAL_280x220_REPORT.md','final_state':'finish-280x220/final-state.json'}
    write(ROOT/'release.json',release)
    r['closed']=True;r['documentation_closed_utc']=now();r['elapsed_minutes_through_documentation']=round(elapsed(r),3)
    r['final_state']='Restored cycle-02; no further automatic routing or repair permitted';write(LEDGER,r)
    rows=[]
    for c in r['cycles']:
        m=c['metrics'];counts=m['counts'];rows.append(f"| {c['number']} | {m['opens']} | {counts.get('connection_width',0)} | {counts.get('zones_intersect',0)} | {counts.get('track_dangling',0)} / {counts.get('via_dangling',0)} | {m['force']}/247 | {m['critical']}/46 | {'bestätigt' if c['progress'] else 'verworfen'} |")
    report=f'''# PMU Rev A.1 – Abschluss 280 × 220 mm

**Nicht fertiggestellt, nicht bestellbar. Der Auftrag ist wegen zwei aufeinanderfolgenden Zyklen ohne zulässigen Fortschritt beendet.**

Engineering prototype – not production qualified. `cad_complete`, `fabrication_release`, `assembly_release`, `production_release` und `orderable` sind `false`.

Branch: `codex/pmu-rev-a1-280x220-finish`. Ausgangscommit: `05e1a9ea9912712718387f560061f0f4fdd2d42e`, enthält `fc9d8e3c430a53018270b0b3bed357042d69690f`. Einzige geometrische Grundlage war die unveränderte 275×210-Platine, SHA-256 `{sha(SOURCE)}`.

Beginn: `{r['started_utc']}`. Routing-/Reparaturstopp: `2026-09-11T15:27:35+00:00`. Dokumentabschluss: `{r['documentation_closed_utc']}`; bis dahin **{r['elapsed_minutes_through_documentation']:.2f} Minuten** einschließlich Vorbereitung und Dokumentation. Commit/Push folgen dieser Zeitmarke; die Abschlussantwort nennt die Gesamtzeit. **4/6 vollständige Zyklen, 0/4 Autorouter-Aufrufe.** Phase A zählt als Zyklus 1. Fünf native ERC- und fünf DRC-Aufrufe einschließlich eines ungültigen Prüfpaars in Zyklus 4; dessen Konfiguration wurde identisch wiederhergestellt und die Verifikation wiederholt. Kein nativer Timeout oder Prozessabsturz. Die 180-Minuten-Grenze wurde nicht erreicht.

## Maßgeblicher Endstand

Wiederhergestellt wurde ausschließlich der validierte **Zyklus 2**. Alle 70 geprüften Eingaben stimmen bytegenau mit dessen Prüfmanifest überein. Die vollständigen finalen ERC-/DRC-Dateien sind bytegleiche Kopien dieser gültigen Berichte. Die darin geprüfte Platine war nach Zonenfüllung gespeichert und für die Geometrieprüfung neu geladen worden; nach Wiederherstellung wurde ihre Identität erneut geprüft.

- PCB: [HomeMy_PMU_RevA_280x220.kicad_pcb](kicad/HomeMy_PMU_RevA_280x220.kicad_pcb), SHA-256 `{sha(BOARD)}`.
- Abmessung: **280,000 × 220,000 mm**, gemessen an den Edge.Cuts-Mittellinien. Die KiCad-Anzeigebox enthält zusätzlich 0,05 mm Strichbreite.
- ERC: **0 Befunde, regulärer Exit 0**. DRC: **5 `connection_width`-Fehler, 8 `track_dangling`- und 9 `via_dangling`-Warnungen, regulärer Exit 5**. Dazu **126 offene Verbindungen auf 28 Netzen**. Kein bestandener DRC.
- Vollständige Schaltplanparität: **0 Abweichungen**; `--schematic-parity`, `--all-track-errors` und alle Schweregrade waren aktiviert.
- Pflichtpfade: **244/247**; kritische explizite Pfade: **46/46**.
- 425 unveränderte Bauteil-/Footprint-/Padidentitäten, vier Montagebohrungen, 40 Testpunkte, 48 unveränderte Press-fit-Löcher, vier Kupferlagen und ursprüngliche Regeln/Netzklassen/Stackup. Platzierungs-, Probe-, 2D-Anschluss- und Antennen-Keepout-Prüfung bestanden.
- Die beiden U11-LOGIC_GND-Stitches bleiben im Endstand nur an F.Cu angebunden. In Zyklus 3/4 korrigierte Rückleiter und Stitches wurden zusammen mit den verworfenen Versuchen zurückgenommen.

## Erhaltener Fortschritt

Die Außenkontur wurde nach rechts um 5 mm und nach unten um 10 mm erweitert. Kein Footprint, Anschluss oder Montagepunkt wurde verschoben. Der bestehende ESP32-Keepout auf allen vier Kupferlagen reicht bis Y=224,15 mm und bleibt vollständig kupfer- und bauteilfrei bis über den neuen Rand.

40 kontrolliert festgelegte 0,20-mm-Signalabschnitte und 15 Durchkontaktierungen mit 0,60/0,30 mm stellen die drei MAIN_KELVIN_P-Pfade, den zugehörigen Testpunkt und die sechs MAIN_HGATE-/MAIN_DGATE-Verbindungen her. Alle vorhandenen Leiterbahnen und Leistungsvias bleiben im maßgeblichen Endstand erhalten. Dadurch sinkt die offene Verbindungsliste von 136 auf 126; die kritischen Pfade steigen von 37 auf 46.

Die positive Kelvin-Führung folgt der vorhandenen negativen Führung auf In2.Cu; der INA-Abzweig verläuft getrennt auf In1.Cu. Die Gate-Verteilung nutzt getrennte kontrollierte Lagen. Die Haupt-Gatewege bleiben wegen der übernommenen Platzierung relativ lang: HGATE etwa 36–86 mm, DGATE etwa 83–133 mm. Die vollständigen Leitungslängen und Lagen stehen in der Pfadliste; eine EM-/Stromteilungs- oder Hardwarequalifikation ist damit nicht verbunden.

## Zyklen und Abbruch

| Zyklus | Offen | Breitenfehler | Zonenüberschneidungen | Dangling Tracks / Vias | Pflichtpfade | Kritische Pfade | Disposition |
|---|---:|---:|---:|---:|---:|---:|---|
{chr(10).join(rows)}

1. Unveränderte 275-Geometrie auf feste 280×220-Kontur übernommen, gefüllt und nativ geprüft.
2. Die neun fehlenden kritischen Pfade einschließlich separater Kelvin-Abzweige ergänzt; als bester validierter Stand gesichert.
3. Zwei DC/DC-Rückleiter, DRIVE auf F.Cu, LIFT auf In1.Cu und LOGIC_5V_N auf B.Cu ergänzt; 20 BATT_N-Vias lokal bei unveränderter Anzahl und Geometrie versetzt. Elf kreuzende Signale erhielten gezielte Lagenübergänge. Zwei U11-Stitches sowie mehrere Engstellen wurden bearbeitet. Der Versuch erzeugte 27 Überschneidungsbefunde zwischen neuen gleichnamigen Flächen und verlor den vorher bestandenen LIFT-Pfad auf In2.Cu. Nicht als Beststand akzeptiert.
4. Neue gleichnamige Flächen zu geometrisch gleichen Vereinigungen zusammengeführt; V3V3-Übergang auf B.Cu an ein vorhandenes Via zurückgeführt; CHOP_DRIVE_H-Via weiter vom Engpass versetzt. Die Prüfung mit unveränderten Originalregeln zeigt 3 Breitenfehler und 122 offene Verbindungen. Der LIFT-In2-Pfad bleibt jedoch unterbrochen. Die neue MOTION_GATE_EN-Durchkontaktierung bei (175,1488; 156,0) schneidet den verbleibenden oberen Kupferdurchgang ab. Die nachträglich lesend vorgeschlagene weitere Korrektur wurde wegen der Abbruchgrenze **nicht ausgeführt**.

Ein höherer Gesamtzähler von 246/247 genügt nicht: Zyklus 3/4 gewinnen die drei vorher fehlenden Pfade, verlieren aber einen vorher bestandenen Pflichtpfad. Das verletzt ausdrücklich die Fortschrittsbedingung. Zwei solche Zyklen lösen den Stopp aus; Zyklus 2 wurde wiederhergestellt.

In Zyklus 4 verursachte das Laden einer Scratch-PCB ohne benachbarte Projektdatei eine automatische Speicherung von KiCad-Standardeinstellungen in die aktive `.kicad_pro`. Der erste ERC-/DRC-Satz dieses Zyklus ist deshalb **ungültige Abnahme-Evidenz** und bleibt gekennzeichnet erhalten. Die exakt ursprüngliche Projektdatei wurde anhand SHA-256 wiederhergestellt; nach erneutem Füllen erfolgte die gültige Verifikation `cycle-04-verified`. Es wurden keine geänderten Regeln zur Freigabe oder Fortschrittsbewertung verwendet. Die Check-Hilfe prüft seither den gebundenen Projekt-Hash vor jedem nativen Aufruf.

## Offene Pflichtpfade und Blockaden des Endstands

- `DRIVE_N`: J7.2 → NT3.1 auf **F.Cu** fehlt. Der vorhandene B.Cu-Rückleiter ersetzt diese Prüfung nicht.
- `LIFT_N`: J8.2 → NT4.1 auf **In1.Cu** fehlt; sein ursprünglicher In2-Pfad bleibt im wiederhergestellten Endstand erhalten.
- `LOGIC_5V_N`: J18.3 → J11.2 auf **B.Cu** fehlt.
- U11.1/U11.2: lokale LOGIC_GND-Vias (23,9; 22,0) und (22,9; 21,5) nur an F.Cu.
- Weitere Leistungs-/Referenzabzweige, eFuse-Zuleitungen/-Ausgänge und Rückleiter sowie Steuerleitungen bleiben offen. Via-Felder und dicht geführte Signale begrenzen die verfügbaren Leistungskorridore. Die vollständige Endliste enthält 126 Verbindungen auf den folgenden 28 Netzen.

| Netz | Offene Verbindungen |
|---|---:|
{chr(10).join('| `'+net+'` | '+str(count)+' |' for net,count in sorted(nets.items()))}

Die 17 Dangling-Warnungen werden **nicht akzeptiert oder ausgeblendet**. Jede steht mit UUID, Position, Netz und Schweregrad im vollständigen DRC-Bericht. Die fünf End-Breitenbefunde sind ebenfalls dort einzeln dokumentiert. Weitere nur lesend entworfene SYS-/eFuse-Routen wurden nicht angewendet und besitzen keine native Freigabe.

## Nachweise und Grenzen

- [Vollständiger nativer ERC](finish-280x220/final-erc.json): SHA-256 `{sha(OUT/'final-erc.json')}`.
- [Vollständiger nativer DRC](finish-280x220/final-drc.json): SHA-256 `{sha(OUT/'final-drc.json')}`.
- [Alle 247 Pflichtpfade](finish-280x220/final-required-paths.json), [alle 46 kritischen Pfade](finish-280x220/final-critical-paths.json).
- [Alle 70 geprüften Eingabehashes](finish-280x220/final-input-sha256.json), [Geometrie, Via-Zahlen, Kupferfenster und mechanische Prüfungen](finish-280x220/final-geometry.json), [Endstatus](finish-280x220/final-state.json), [vollständiges Zyklusjournal](finish-280x220/ledger.json).
- Die frühen Geometrieausgaben lasen für die Referenzstitches versehentlich eine nicht mehr im kompakten Quellbericht enthaltene Langliste und meldeten ausdrücklich 0 geprüfte Stitches. Das war kein Anbindungsnachweis. Die separate abschließende Prüfung der beiden geforderten U11-Stitches ist jetzt im Endbericht enthalten.
- Querschnitte sind lokale Abtastungen, Busbar-Kontaktabstände sind keine fertigen Busbar-Zeichnungen. Die 2D-Prüfung ersetzt keine räumliche Gehäuse-/Werkzeug-/Kabelprüfung. Keine thermische Qualifikation, Fertigung, Bestellung, Bestückung, Bestromung oder Aktorprüfung.

Keine Gerber-, Bohr-, BOM- oder Positionsdateien für diesen unfertigen CAD-Stand erzeugt. Die ursprünglichen Varianten und ihre historischen Berichte bleiben unverändert. Parallel im lokalen Rev-A-Schaltplanverzeichnis entstandene Fremdänderungen und deren Restore-Backup gehören nicht zu diesem Auftrag; sie wurden weder zurückgesetzt noch in diesen Commit aufgenommen.
'''
    (ROOT/'FINAL_280x220_REPORT.md').write_text(report,encoding='utf-8')
    print('Documentation closed',r['elapsed_minutes_through_documentation'],'minutes; CAD bytes unchanged',sha(BOARD))

if __name__=='__main__':main()
