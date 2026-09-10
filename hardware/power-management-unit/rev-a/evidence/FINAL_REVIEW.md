# PMU Revision A — final engineering artifact review

`rev_a_engineering_prototype: true`  
`rev_b_production: false`  
Review date: 2026-09-10. Board SHA-256:
`70bb8eb588f2fc7200f718df0e11659aad3c40c7e9d5652228eb7a58d232065f`.

The repository deliverables requested by `ASTRA_START_PROMPT.md` are implemented:
native hierarchical KiCad capture, routed four-layer PCB, exact prototype BOM
and footprints, primary-source records, calculations, requirement disposition,
mechanical reinforcement, connector/cable and button timing documentation,
native check reports, and Revision-A manufacturing outputs. Open the
[KiCad project](../kicad/HomeMy_PMU_RevA.kicad_pro) or start with the
[project index](../README.md). No hardware was ordered, assembled or energized;
no firmware or production qualification is claimed.

## Final checks

| Check | Result and evidence |
| --- | --- |
| Native KiCad 10.0.6 ERC | Complete report; **0 findings**. [JSON](../reports/erc-final.json). |
| Native DRC, all severities and track errors | **0 findings, 0 unconnected items, 0 schematic-parity differences**. [JSON](../reports/drc-final.json). |
| Native command execution | Both processes saved complete fresh reports, then failed to terminate normally while closing denied Windows registry settings. Each timed out with **124**. Neither process is recorded as passed. [Commands, hashes, status](../reports/native-checks-both.json). |
| Rule review | No item-level DRC exclusions. Default-ignored checks and 47 narrowly scoped same-package 0.15 mm pad-clearance rules are explicitly reviewed; routed clearance remains 0.20 mm. [Rule disposition](REVIEWED_DEFAULT_ERC_DRC.md). |
| Source, schematic, PCB and BOM identity | **0 errors**, with exact identities for 63 intentional no-connect pins. 430 captured symbols, 421 physical schematic parts, 425 PCB footprints including four mounting holes, 1,373 physical pad instances, and all 55 numbered requirements reconciled. [Strict parity](../reports/electrical-parity-audit.json). |
| Critical explicit routes | **46/46 paths found**; 125 protected analog copper items have no pairwise foreign-net collisions. Actual lengths, layers and via transitions are recorded. [Routing review](../design/CRITICAL_ROUTING_REVIEW.md). |
| Filled power copper | **18/18 sampled endpoint paths continuous**; Q40 connected F.Cu drain area **689.22 mm²**, above the 600 mm² geometric target. These checks do not establish current capacity or thermal resistance. [Native geometry review](filled-power-copper-review.md). |
| Placement and assembly access | 40 test points, no actual front-courtyard intersections, no copper in the four-layer antenna keepout. A centered 3 mm probe has a smallest modeled body-clearance reserve of 0.366 mm. Connector access is a limited 2D projection check. [Placement review](placement-access-review.md). |
| Assembly orientation | Gate/source/drain, Kelvin force/sense, floating U1 EP and six M5 screw-face directions are annotated. Copper, pads, positions and existing UUIDs were preserved. [Annotation application](../reports/assembly-annotation-application.json), [orientation drawing](../manufacturing/ASSEMBLY_ORIENTATION.md). |
| BOM and manufacturing coverage | **0 errors**; 356 purchased PCB positions, 352 populated, four DNP, 124 grouped rows and 31 external rows. Eleven native Gerber layers, separate PTH/NPTH Excellon files/maps, placement subsets, BOM copies and both assembly views are present. [Export manifest](../manufacturing/engineering-preview/EXPORT_MANIFEST.json). |
| Current artifact identities | The [final package audit](FINAL_REVIEW.json) checks the recorded source/output hashes and binds the native, electrical, manufacturing, geometry and visual records to this same PCB. It preserves failed native-process status separately. |
| Generator/metadata review | Seven generators reproduce fourteen outputs byte-for-byte; all 48 footprint libraries reproduce semantically and all 421 pin audits pass. Native and consumer-constrained formats inherit revision flags without schema changes. [Reproduction](generator-reproducibility-review.md), [metadata scope](release-metadata-scope.json). |

The board is 360 × 300 mm with 70/35/35/70 µm copper, 48 zones and 2,232 through
vias. Fabrication specifies 1.60–1.70 mm between outer copper faces, excluding
masks, with the press-fit hole process separately controlled. Seven 2 mm copper
bars, fifteen BC contacts and eight top star bridges reinforce the current paths.
The final mechanical regeneration changed only its geometry provenance hash;
bar/contact dimensions and purchase quantities remained unchanged.

## Visual inspection and routing provenance

The retained native SVGs were rasterized and inspected: the main schematic,
both assembly sides, all four copper layers, both drill maps, the 1:1 busbar
drawing and the supplemental orientation drawing. The views retain the board
outline, separate layer content, antenna clearance, mounting pattern and drill
legends; assembly details and DNP markings remain visible in the source SVGs.
The busbar drawing states its top-view coordinates and includes a 100 mm print
calibration bar. The native back assembly view uses unmirrored board coordinates.
[Rendered source/image hashes](../reports/rendered-review-manifest.json) identify
the inspected artifacts. Visual inspection is not an automated proof of every
feature, stencil aperture, physical cable bend or manufacturing process.

Routing used native KiCad zones and protected current/sense paths, followed by
bounded Freerouting candidates and explicit local corrections. The final import
preserved all 1,959 existing locked copper items. The reviewed completion plan
removed 31 identified unlocked segments and added 38 locked items. Run 002's
partial router result remains recorded honestly; the final acceptance evidence
comes from native KiCad and the geometry reviews after correction. The selected
session, exact plan and [integration record](../reports/final-routing-integration.json)
are retained. No end-to-end bit-identical autorouting reproduction is claimed.

## Selected design and calculation limits

LM74930QRGERQ1 drives a three-plus-three bank of PSMN1R0-100ASFJ 100 V MOSFETs;
TPS48110AQDGXRQ1 drives the two-plus-two motion bank. Each path uses a
CSS4J-4026R-L500F 0.5 mΩ four-terminal shunt. INA228AIDGSR monitors the main
shunt through independent Kelvin filtering. Two TPS26631RGER branches protect
the PC and external 5 V converter inputs. The analog motor-side chopper uses
IPT015N10N5, LM339BIPWR and UCC27511DBVR with two external RH100 10 Ω resistors.
LT3014/LTC2954/LTC6993 provide always-on wake and startup timing; the switched
ESP32-S3-WROOM-1-N8, hardware watchdog/latches and TCAN1042 complete supervision.
Motion defaults OFF and requires explicit rearming after a fault.

The linked calculations cover FET conduction and conditional SOA/inrush,
four-terminal shunt dissipation, eFuse limits, timer leakage/tolerances, startup
and forced-off timing, protection/selectivity corners, chopper hysteresis and
single-pulse energy, copper/via/bar/contact resistance and provisional thermal
limits. They explicitly retain the minimum-main-gate-drive resistance gap,
940 µF motion inrush uncertainty, fast native UV behavior, wider OV corners and
absence of guaranteed 60/65 A protection selectivity. Q40's measured geometric
area does not inherit the manufacturer's fixture thermal resistance. A cold
500 J resistor-bank test does not establish repetitive braking duty.

## Remaining owner review and physical gates

The [design review and bring-up sequence](../../DESIGN_REVIEW_AND_BRINGUP.md)
remains authoritative. Before any order, the owner reviews the concrete CAD/BOM,
manufacturer/footprint mapping, shared-shunt fault independence, gate/SOA and
transient dispositions, press-fit process, contact stack, insulation/support and
real assembly access. Exact external converter identities and the supplied fuse
must be checked against the actual installation; BOM stock was not reserved.

Initial main-path bring-up uses a current-limited motorless fixture at no more
than 1 A, motion OFF and no more than 100 µF directly on SYS. The installed
940 µF motion/chopper bank uses the separately defined controlled charging and
test arrangement. Before battery connection, close BAT-004 for the actual
external 60 A fuse, complete the staged motorless tests, and provide the required
reachable service disconnect before any separately authorized actuator test.

[Revision-B validation](../../REV_B_VALIDATION.md) retains measured hot FET/SOA
and current sharing, shunt drift and fault response, inrush without precharge,
regeneration/chopper energy and repetitive temperature, converter behavior, arm
and cable heating, fuse/BMS coordination, EMI/CAN integrity, final mechanics and
system stop behavior. No physical gate is converted into a measured pass by
this CAD review. Ordering, assembly and commissioning remain with the owner.
