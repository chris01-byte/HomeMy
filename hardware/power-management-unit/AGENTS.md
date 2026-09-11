# PMU agent instructions

Diese Anweisungen gelten für alle Dateien unter hardware/power-management-unit/.

## Pflichtkontext für den Rev-A.1-Abschluss auf 280 × 220 mm

Vor jeder Analyse oder Änderung an der kompakten PMU Rev A.1 vollständig lesen und befolgen:

- ASTRA_280X220_FINISH.md
- rev-a/README.md
- rev-a/design/HIGH_CURRENT_RULES.md
- rev-a/manufacturing/PCB_STACKUP_PRESSFIT.md
- DESIGN_REVIEW_AND_BRINGUP.md
- REV_A_ASSUMPTIONS.md

Die eingefrorene Versuchsevidenz liegt auf Branch codex/pmu-rev-a1-250x200-wip bei Commit 014632dd9d8c65689d6f62036c11b4d191d49fb4. Dieser Branch darf nicht verändert werden.

## Verbindliche Arbeitsregeln

- Nur auf dem ausdrücklich genannten Arbeitsbranch schreiben.
- Topologie, Bauteile, Footprints, Schutzfunktionen, Hochstromregeln, Kelvin-/Gate-Konzept, Press-fit- und Busbar-Schnittstellen nicht stillschweigend ändern.
- Bestehende ERC-/DRC-Regeln nicht abschwächen, unterdrücken oder pauschal ausnehmen.
- Ein Agent besitzt die KiCad-Schreibverantwortung. Weitere Agenten prüfen nur lesend.
- Keine unbeschränkten Routing- oder Reparaturschleifen.
- Die feste Größe sowie die Zeit-, Zyklen-, Prüf- und Abbruchgrenzen aus ASTRA_280X220_FINISH.md sind harte Grenzen.
- Fehlende oder abgebrochene native Prüfungen gelten niemals als bestanden.
- Fertigungs-, Bestückungs- und Produktionsfreigaben bleiben false, solange der Nutzer keinen separaten Freigabeauftrag erteilt.
- Keine temporären Routerdateien, Caches, kompilierten Hilfsdateien oder redundanten Zwischenstände committen.
- Keine reale Bestromung, Batterie-, Motor- oder Aktorprüfung durch diesen Layoutauftrag.

Bei Widersprüchen zwischen historischen Zwischenständen und den geprüften Rev-A-Anforderungen gelten die Rev-A-Anforderungen. Bei einem notwendigen Topologie- oder Sicherheitskompromiss Arbeit stoppen, den Blocker dokumentieren und den Nutzer entscheiden lassen.
