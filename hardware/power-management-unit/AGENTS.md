# PMU agent instructions

Diese Regeln gelten für `hardware/power-management-unit/`.

## Pflichtkontext

Vor PMU-Arbeiten vollständig lesen:

- `README.md`
- `requirements.yaml`
- `ASTRA_PCB_HANDOFF.md`
- `interfaces-and-layout.md`
- `rev-a/README.md`
- `rev-a/design/HIGH_CURRENT_RULES.md`
- `rev-a/design/POWER_STAGE.md`
- `rev-a/design/WAKE_IO.md`
- `rev-a/manufacturing/PCB_STACKUP_PRESSFIT.md`
- `verification-plan.md`

Für das neue Layout zusätzlich `ASTRA_300X280_LAYOUT.md`.

## Arbeitsregeln

- Der einzige aktive Zielaufbau ist 300 × 280 mm unter `rev-a2-300x280/`.
- Keine verworfenen Verkleinerungsstände wiederherstellen oder fortsetzen.
- Nur ein Agent schreibt KiCad-Dateien; weitere Agenten dürfen parallel ausschließlich lesend prüfen.
- Topologie, Netze, Bauteile, Footprints und Schutzfunktionen nicht stillschweigend ändern.
- ERC-/DRC-Regeln nicht abschwächen, unterdrücken oder pauschal ausnehmen.
- Keine unbeschränkten Routing-, Reparatur- oder Optimierungsschleifen.
- Fehlende, abgebrochene oder zeitüberschrittene Prüfungen gelten nicht als bestanden.
- Keine temporären Routerdateien, Caches, Binärduplikate oder Zwischenberichte committen.
- Fertigungs-, Bestückungs-, Bestromungs- und Produktionsfreigaben bleiben false, solange der Nutzer sie nicht ausdrücklich erteilt.
- Bei einem notwendigen Sicherheits- oder Topologiekompromiss stoppen, Blocker präzise dokumentieren und den Nutzer entscheiden lassen.
