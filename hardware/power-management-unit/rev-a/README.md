# HomeMy PMU Revision A

rev_a_engineering_prototype: true  
rev_b_production: false

This directory contains the engineering implementation of the PMU requirements
at repository baseline `1a70bec1de092db8a2d101e67e9e882622992003`. Open
[`kicad/HomeMy_PMU_RevA.kicad_pro`](kicad/HomeMy_PMU_RevA.kicad_pro) in KiCad 10.
The root schematic has fifteen hierarchical child sheets. The 360 × 300 mm
laboratory PCB contains four copper layers, 425 footprints including four
mounting holes, 40 test points, and an all-layer ESP32 antenna keepout.

The authoritative requirements and staged verification plan remain in the
parent directory. Component calculations are design evidence, not measurements.

The [final review](evidence/FINAL_REVIEW.md) records zero native ERC findings,
zero DRC findings, zero open connections and zero schematic-parity differences.
Strict source/PCB/BOM reconciliation and final manufacturing file coverage also
pass. Those results are bound to the final PCB and output hashes.

Completion and release are tracked in [`release.json`](release.json). A missing
or failed CAD check must never be interpreted as a pass. Native check summaries
record report findings and command exit status separately. This portable
Windows KiCad installation can produce complete reports and then fail while
closing its registry settings; those process failures remain visible.

Fabrication exports are engineering review artifacts; ordering requires the
project owner's review. No physical hardware has been energized or ordered by
this work. The external 60 A fuse remains the only melting fuse, and motion is
hardware-disabled after power-on or a fault until explicit rearming.

## Review entry points

| Artifact | Content |
| --- | --- |
| [Final review](evidence/FINAL_REVIEW.md) | Final findings, file identities, visual inspection and unresolved physical gates |
| [Requirements traceability](../REQUIREMENTS_TRACEABILITY.md) | All 55 numbered requirements, implementation and verification disposition |
| [Revision A assumptions](../REV_A_ASSUMPTIONS.md) | Provisional thresholds, component tolerances, test points and initial settings |
| [Design review and bring-up](../DESIGN_REVIEW_AND_BRINGUP.md) | Ordered motorless tests and mandatory energization gates |
| [Revision B validation](../REV_B_VALIDATION.md) | Measurements that control later production decisions |
| [Power-stage record](design/POWER_STAGE.md) | Main/motion FET banks, shunts, eFuses, timer and protection calculations |
| [BOM](manufacturing/REV_A_BOM.csv) | 356 purchased PCB positions; 352 populated and four DNP |
| [External BOM](manufacturing/REV_A_EXTERNAL_BOM.csv) | Harness/mating parts, braking resistors and specified mechanical hardware |
| [Mechanical build](manufacturing/MECHANICAL_BUILD.md) | Seven underside copper bars, eight star bridges, clamp/insulation details |
| [Stackup and press-fit](manufacturing/PCB_STACKUP_PRESSFIT.md) | Minimum finished 70/35/35/70 µm copper, 1.60–1.70 mm between outer copper faces excluding masks, and controlled finished holes |
| [Connector assembly](manufacturing/CONNECTOR_ASSEMBLY.md) | Pin assignments, cable sizes, mating parts and assembly process |
| [Reviewed ERC/DRC rules](evidence/REVIEWED_DEFAULT_ERC_DRC.md) | Enabled checks, applicable defaults and narrowly scoped pad rules |
| [Manufacturing preview](manufacturing/engineering-preview/README.md) | Gerbers, drills, placements, BOM copies, assembly views and hash manifest |
| [Reproduction workflow](scripts/README.md) | Source capture, native CAD generation, routing, checks and exports |

## Selected architecture

LM74930QRGERQ1 controls three-plus-three PSMN1R0-100ASFJ main MOSFETs.
TPS48110AQDGXRQ1 controls the two-plus-two motion bank. Both current paths use
CSS4J-4026R-L500F four-terminal 0.5 mΩ shunts; INA228AIDGSR monitors the main
shunt through separate Kelvin filters. Two TPS26631RGER devices protect the PC
and external 5 V converter inputs. The analog motor-side chopper uses
IPT015N10N5ATMA1, LM339BIPWR and UCC27511DBVR with two external RH100 10 Ω resistors.

The always-on LT3014B/LTC2954/LTC6993 hardware implements wake, startup grant,
self-hold and forced-off behavior. The ESP32-S3-WROOM-1-N8, TCAN1042HGVDRQ1,
hardware watchdog/fault latches and power-off signal isolation complete the
supervision and communication interface. No firmware or real-motion permission
is implied by the hardware artifacts.

## Evidence limits

The calculations expose the main-controller minimum gate-drive resistance gap,
timer leakage/temperature limits, motion inrush/SOA envelope, chopper threshold
corners, single-pulse resistor energy, and uncertain fuse/BMS selectivity.
Measured contact resistance, temperature, transient peaks, repetitive braking,
converter behavior and system stop behavior remain physical validation work.
ERC/DRC cannot close those measurements.

`design/` records circuit decisions and machine-readable component connections;
`evidence/` stores manufacturer sources and review records; `reports/` stores
native CAD results and routing candidates. Historical reports retain their
original findings and are superseded only by the contemporaneous final manifest.

The local checkout is on `codex/pmu-rev-a`. Revert its individual commits to roll
back the engineering artifacts; this work does not change robot runtime or
customer-mode defaults.
