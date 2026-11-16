# PMU agent instructions

Diese Regeln gelten für `hardware/power-management-unit/`.

## Pflichtkontext

Vor PMU-Arbeiten lesen:

- `README.md`
- `requirements.yaml`
- `ASTRA_PCB_HANDOFF.md`
- `interfaces-and-layout.md`
- `rev-a2-layout-280x260/README.md`
- `reviews/2026-11-16-rev-a2-gegenpruefung/README.md`

Je nach Aufgabe zusätzlich: `rev-a/design/POWER_STAGE.md`, `rev-a/design/WAKE_IO.md`, `rev-a/design/CHOPPER_MECHANICS.md`, `rev-a/design/HIGH_CURRENT_RULES.md`, `rev-a/manufacturing/PCB_STACKUP_PRESSFIT.md`, `verification-plan.md`, sowie `BEFUNDE.md` und `BERECHNUNGEN.md` der Gegenprüfung.

## Arbeitsregeln

- Die einzige aktuelle Leiterplatte ist Revision A2, 280 × 260 mm, unter `rev-a2-layout-280x260/`. Keine anderen Platinengrößen anlegen und keine entfernten Stände wiederherstellen, außer der Nutzer verlangt es ausdrücklich.
- Die Befunde GP-01 bis GP-25 sind offen, bis sie in `reviews/2026-11-16-rev-a2-gegenpruefung/findings.json` mit Beleg geschlossen sind.
- Nur ein Agent schreibt KiCad-Dateien; weitere Agenten dürfen parallel ausschließlich lesend prüfen.
- Topologie, Netze, Bauteile, Footprints und Schutzfunktionen nicht stillschweigend ändern.
- ERC-/DRC-Regeln nicht abschwächen, unterdrücken oder pauschal ausnehmen. Neue Mitglieder der Ausnahmegruppen (`PWR_TAP_CONTROL` usw.) einzeln begründen; Schutzdioden und Masseverbindungen gehören nicht hinein.
- Keine unbeschränkten Routing-, Reparatur- oder Optimierungsschleifen.
- Fehlende, abgebrochene oder zeitüberschrittene Prüfungen gelten nicht als bestanden. Verbindungszähler (z. B. „247/247") sind kein Nachweis der Stromtragfähigkeit.
- Keine temporären Routerdateien, Caches, Binärduplikate, lokalen Einstellungsdateien oder absoluten Benutzerpfade committen.
- Berichte unter `rev-a2-layout-280x260/reports/` sind Momentaufnahmen und werden nicht nachträglich bearbeitet. Nach einer PCB-Änderung entstehen neue Berichte mit neuem Hash.
- Fertigungs-, Bestückungs-, Bestromungs- und Produktionsfreigaben bleiben `false`, solange der Nutzer sie nicht ausdrücklich erteilt.
- Bei einem notwendigen Sicherheits- oder Topologiekompromiss stoppen, Blocker präzise dokumentieren und den Nutzer entscheiden lassen.
