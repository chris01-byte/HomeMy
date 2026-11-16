# PMU Schaltungsauslegung Rev A

rev_a_engineering_prototype: true  
rev_b_production: false

Dieses Verzeichnis enthält die elektrische Auslegung der PMU: Schaltungsbeschreibungen, Bauteilwahl, Berechnungen, Datenblätter und Prozessunterlagen. Sie gilt unverändert für die aktuelle Leiterplatte **Rev A2, 280 × 260 mm** unter [`../rev-a2-layout-280x260/`](../rev-a2-layout-280x260/README.md), weil A2 denselben Schaltplan verwendet.

**Hier liegt keine Leiterplatte mehr.** Die ursprüngliche 360 × 300-mm-Platine, ihr Bestellpaket Rev A-P1 und alle platinenbezogenen Berichte wurden am 2026-11-16 entfernt (Git-Historie bis Commit `d37c7f7`). Aussagen in den Unterlagen zu Koordinaten, Via-Zahlen, Querschnittsmessungen oder dem Bestellpaket der 360 × 300-Platine sind historisch; für A2 gelten die Dateien unter `../rev-a2-layout-280x260/` und die Befunde der [Gegenprüfung](../reviews/2026-11-16-rev-a2-gegenpruefung/README.md).

Berechnungen sind Auslegungsnachweise, keine Messungen.

## Inhalt

| Pfad | Inhalt |
|---|---|
| [design/POWER_STAGE.md](design/POWER_STAGE.md) | Haupt- und Motion-Schalter, Shunts, eFuses, Zeitglieder, Schutzschwellen |
| [design/WAKE_IO.md](design/WAKE_IO.md) | Always-on-Domäne, Taster, Selbsthaltung, Latches, ESP32, CAN, LED |
| [design/CHOPPER_MECHANICS.md](design/CHOPPER_MECHANICS.md) | Bremschopper, Steckverbinder, Leiter |
| [design/HIGH_CURRENT_RULES.md](design/HIGH_CURRENT_RULES.md) | Hochstromregeln und Ausnahmegruppen der Design-Regeln |
| [design/CIRCUIT_CROSS_REVIEW.md](design/CIRCUIT_CROSS_REVIEW.md), [design/CRITICAL_ROUTING_REVIEW.md](design/CRITICAL_ROUTING_REVIEW.md) | frühere Schaltungs- und Routingprüfung |
| [design/CRITICAL_ALTERNATIVES.md](design/CRITICAL_ALTERNATIVES.md), [design/CHOPPER_PROCUREMENT.md](design/CHOPPER_PROCUREMENT.md) | Alternativen und Beschaffung kritischer Teile |
| `design/*-parts.json`, `design/*.py` | maschinenlesbare Bauteilanschlüsse und Rechenskripte |
| `evidence/power/`, `evidence/chopper/`, `evidence/*.pdf` | Datenblätter, Quellenlisten, berechnete Werte |
| [evidence/REVIEWED_DEFAULT_ERC_DRC.md](evidence/REVIEWED_DEFAULT_ERC_DRC.md) | geprüfte ERC-/DRC-Regelkonfiguration |
| `evidence/high-current-tap-capture.json`, `evidence/review_filled_power.py` | Grundlage der Leistungspfadprüfung (auch für A2 verwendet) |
| [manufacturing/PCB_STACKUP_PRESSFIT.md](manufacturing/PCB_STACKUP_PRESSFIT.md) | Lagenaufbau, Bohrklassen, Einpressprozess |
| [manufacturing/MECHANICAL_BUILD.md](manufacturing/MECHANICAL_BUILD.md), [manufacturing/CONNECTOR_ASSEMBLY.md](manufacturing/CONNECTOR_ASSEMBLY.md) | Schienen-/Klemmkonzept und Anschlussmontage |
| `manufacturing/MECHANICAL_CATALOG_BOM.json`, `busbar-calculations.json`, `build_mechanical.py`, `BOM_README.md` | Mechanik-Stückliste und Rechenwerte |
| `scripts/` | Generatoren und Prüfer des ursprünglichen Ablaufs. Pfadgebunden an die damalige Arbeitsumgebung; nur als Quelle der Prüfmethoden aufbewahrt |

## Gewählte Architektur

LM74930QRGERQ1 steuert drei plus drei PSMN1R0-100ASFJ als Hauptschalter. TPS48110AQDGXRQ1 steuert zwei plus zwei als Motion-Gate. Beide Strompfade nutzen CSS4J-4026R-L500F (0,5 mΩ, vierpolig); INA228AIDGSR misst am Hauptshunt. Zwei TPS26631RGER schützen die Eingänge von PC- und 5-V-Wandler. Der analoge Bremschopper verwendet IPT015N10N5ATMA1, LM339BIPWR und UCC27511DBVR mit zwei externen 10-Ω-Widerständen.

LT3014B, LTC2954 und LTC6993 bilden Wecken, Startfenster, Selbsthaltung und Zwangsabschaltung. ESP32-S3-WROOM-1-N8, TCAN1042HGVDRQ1, Hardware-Watchdog, Fehler-Latches und Analogschalter ergänzen Überwachung und Kommunikation. Die Hardware-Unterlagen enthalten keine Firmware und keine Bewegungsfreigabe.

## Grenzen der Nachweise

Die Rechnungen benennen offen: Gate-Spannung des Hauptschalters, Leckströme und Temperaturgrenzen der Zeitglieder, Einschaltstrom und SOA des Motion-Gates, Chopper-Schwellen, Einzelimpulsenergie der Widerstände und die unsichere Selektivität von Sicherung und BMS. Kontaktwiderstände, Temperaturen, Transienten, wiederholtes Bremsen, Wandlerverhalten und das Stoppverhalten des Gesamtsystems sind physische Validierung. Die Gegenprüfung vom 2026-11-16 ergänzt weitere Punkte (GP-01 bis GP-25).
