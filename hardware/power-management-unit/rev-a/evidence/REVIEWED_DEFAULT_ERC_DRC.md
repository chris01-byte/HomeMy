# Reviewed ERC/DRC configuration — Rev A

Configuration review on 2026-09-10, begun during lower-power integration and refreshed against the final routed board. The latest matching native ERC and DRC reports contain zero findings and both processes ended normally with **exit code 0**. DRC explicitly included full schematic parity. `reviewed-rule-configuration.json` records exact project/board/rule/report hashes and settings; `audit_rule_configuration.py` refreshes that read-only snapshot. Earlier timeout results remain historical evidence. The release applies only to the Rev-A engineering prototype; no production or physical qualification is asserted.

## Defaults, explicit rules and added checks

The five originally ignored DRC checks match the KiCad 10.0 implementation defaults; the four originally ignored ERC checks also match implementation defaults. They were not bespoke PMU exclusions. The project has no DRC exclusion entries and no custom ERC pin-conflict matrix. After this review the root enabled two DRC warnings and one ERC warning. Sources: [KiCad board defaults](https://raw.githubusercontent.com/KiCad/kicad/10.0/pcbnew/board_design_settings.cpp), [KiCad ERC defaults and settings schema](https://raw.githubusercontent.com/KiCad/kicad/10.0/eeschema/erc/erc_settings.cpp).

| Check | Original default/report | Reviewed project setting and reason |
|---|---|---|
| DRC `missing_courtyard` | ignore | **warning enabled**: custom pressfit, clamp and star footprints need mechanical envelopes. |
| DRC `footprint_type_mismatch` | ignore | **warning enabled**: PTH/SMD attributes affect assembly exports and can expose custom-footprint mistakes. |
| DRC `footprint_filters_mismatch` | ignore | Remains ignore: generated symbols currently contain no `ki_fp_filters`; exact footprint/pin mapping is checked by the source/parity audit. Add filters/check together if the symbol scheme changes. |
| DRC `track_not_centered_on_via` | ignore | Remains ignore: no precision length tuning is claimed. Wide-current joins and via fields require geometry review irrespective of this check. |
| DRC `tuning_profile_track_geometries` | ignore | Remains ignore: no tuning profiles are configured. |
| ERC `single_global_label` | ignore | **warning enabled**: generated per-pin global labels make a one-ended typo worth reviewing. Correct actual mistakes; document only intentional one-ended external/test nets. |
| ERC `four_way_junction` | ignore | Remains ignore: current drawing generator uses short pin-label wires, not ambiguous cross-junction networks. Reconsider if hand-drawn shared wiring is introduced. |
| ERC `simulation_model_issue` | ignore | Remains ignore: these symbols do not deliver a SPICE simulation. No simulation pass is inferred. |
| ERC `footprint_filter` | ignore | Remains ignore for the same absent-filter reason as DRC. |

The correct override path is top-level `erc.rule_severities.single_global_label="warning"`; upstream `ERC_SETTINGS` is nested under `erc` and serializes `rule_severities`. Previously the project omitted this block and used defaults. This is distinct from editing symbol pin types or suppressing individual violations.

The read-only native-footprint presence screen finds no missing courtyards. U10 and U30 have mixed SMD/PTH pad types: their exposed-ground patterns contain thermal-through-hole pads. These intentional thermal patterns retain their SMD assembly attributes. The final native DRC reports no footprint-type violation with the warning enabled; no individual violation is excluded. The screen itself only checks attributes/presence; native DRC remains authoritative for shape validity. [KiCad footprint attributes](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html).

## Scope of the explicit 0.15 mm rules

The snapshot contains 47 same-package clearance rules, generated for each present `U*` component by `configure_fabrication.py`, plus the new scoped power rules. Each clearance condition requires **both objects to be pads in the same explicitly named footprint**; its minimum copper clearance is 0.15 mm. These are numerical pad-spacing rules, not ignored checks. They do not relax inter-footprint, track-to-pad or route-to-route clearance. The Default netclass uses 0.20 mm clearance and 0.20 mm track width; board minimum clearance is 0.15 mm. Other active checks include shorts, unconnected items, courtyard overlap, keepouts, annular rings, hole clearance, outline, mask bridges and thermal-starvation checks.

The generated rule title contains “Reviewed fine-pitch”, but generation currently applies to all U references, including coarse-pitch parts; that title alone is not evidence that the manufacturer documentation for all 47 packages was separately reviewed. This review confirms the **rule scope**. Retain the existing package-source/pin-map evidence, and restrict future relaxation to the documented land pattern rather than extending it to routing. No creepage, voltage-withstand or whole-assembly thermal certification follows from 0.15 mm manufacturability.

Four dedicated power classes now enforce 4 mm battery/SYS/motion tracks and 6 mm arm-return tracks, with minimum 0.8/0.4 mm via pad/drill geometry. `connection_width` is an **error**; scoped power rules set a 1.0 mm neck screen. This is a sliver screen, not proof that a 1 mm neck carries the full current. All 25 power zones use 1.2 mm minimum fill thickness. Exact captured control/measurement taps retain their small geometry, while Kelvin nets stay outside the power classes. The [high-current rule and constriction review](../design/HIGH_CURRENT_RULES.md) documents these exceptions and physical bottlenecks. Native filled-copper analysis checks 247 power-pad paths without crediting the 492 captured tap copper items. No item-level DRC exclusion is used. [KiCad connection-width rules](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html#design-rule-checking).

## Actual report snapshots

| Report | Embedded time, 2026-09-10 | Recorded result |
|---|---|---|
| `evidence/erc-after-schematic-readability.json` | 18:47:39 | 0 violations; same old ignored defaults. |
| `reports/drc-initial.json` | 18:29:01 | 631 errors, 58 warnings; 499 unconnected entries included. Historical placement/fabrication baseline. |
| `reports/drc-placement.json` | 18:40:25 | 499 errors, all unconnected; 0 other recorded violations. |
| `reports/drc-upper-power.json` | 18:56:24 | 499 errors, all unconnected; 0 other recorded violations. Still incomplete routing. |

These historical snapshots identify KiCad 10.0.6. The DRC reports above used the original five ignored defaults and do not establish results for the later routed board. The old timeout-producing final reports are retained in `reports/archive-before-prototype-release/`; high-current development snapshots are in `reports/high-current-development/`. Current final reports are replaced only by an actual new check and matched to current input hashes. A valid JSON report after an abnormal CLI shutdown remains distinct from a clean command exit.

<!-- LATEST_NATIVE_REPORT_SNAPSHOT -->
## Latest native report snapshot

This section is generated from the current files by `audit_rule_configuration.py` and `update_rule_review_snapshot.py`. The historical table above remains a record of the earlier configuration. Current PCB SHA-256: `13fcae0f58c9a6ac5f85eb721c24b44169a65f628baad6586bcd6002f4c17cfe`.

| Check | Embedded report time | Total listed findings | Checks still ignored |
|---|---|---:|---|
| ERC | 2026-09-10T23:09:56 | 0 | four_way_junction, simulation_model_issue, footprint_filter |
| DRC | 2026-09-10T23:10:04 | 0 | track_not_centered_on_via, tuning_profile_track_geometries, footprint_filters_mismatch |

- `reports/erc-final.json` SHA-256: `38a01195bd9bfedae926026ad02f03b66581b02f8acda143ae8389dbc3256a1c`; findings by type: `{}`.
- Matching `native-checks-both.json` records process exit `0`, process passed `True`, report complete `True`. Its board hash matches this configuration snapshot: `True`. The command explicitly requests schematic parity: `not applicable to ERC`.
- `reports/drc-final.json` SHA-256: `41209f2f29faef8b89e8dab513edf4540d547d1aa666cb81b91bd1e35df13c75`; findings by type: `{}`.
- Matching `native-checks-both.json` records process exit `0`, process passed `True`, report complete `True`. Its board hash matches this configuration snapshot: `True`. The command explicitly requests schematic parity: `True`.

The added courtyard, footprint-type and singleton-label warnings remain enabled in the project. A complete JSON report with zero findings is distinct from a clean CLI exit. Registry errors, timeout or abnormal shutdown are retained in the process logs; this review does not convert such an exit into a passed process. Thermal, pressfit, contact-force and system tests remain separate from CAD checks.
<!-- END_LATEST_NATIVE_REPORT_SNAPSHOT -->



## Traceability and source findings

- Corrected `REQUIREMENTS_TRACEABILITY.md` PCB-001/002/004 to the actual four-layer fabrication requirement, seven shaped 2 mm bars, 15 BC contacts, eight NB star bridges, defined film/shims/clamps and dimensional drawing. `design/via-field-counts.json` is now authoritative; 160 vias remains a conditional calculation rather than an achieved count.
- The final count file reads 116 / 104 / 189 / 148 / 117 / 215 for the six positive/common fields and 723 BATT_N vias. The earlier BATT_N count was 759. These totals can decrease after new obstacles; they do not establish 160 usable vias at each **local** transfer. The filled-copper review calculates ideal resistance and loss using the actual field counts, with local sharing limits retained.
- Corrected PCB-005: 7461103 is a right-angle M5 threaded terminal with horizontal access, not a vertical stud. Its body is 14 mm above PCB.
- The initial `configure_fabrication.py` specified Tg 170 and 1.60 mm **including** 0.02 mm masks, leaving 1.58 mm between outer copper faces. The CAD owner corrected the generator. Final read-only native inspection confirms Tg 125–135, 0.15 / 1.09 / 0.15 mm dielectrics, 0.070 / 0.035 / 0.035 / 0.070 mm copper and 1.60 mm between outer copper faces, with two additional 0.01 mm masks. ENIG is selected. This verifies CAD settings, not finished-lot thickness or laminate qualification.
- The obsolete U5 corners in `REV_A_ASSUMPTIONS.md` A03 have been corrected: the 226 kΩ source/calculation gives 29.3112 V nominal and 27.891–30.734 V modeled corners. A12/A13 now describe the actual mechanical proposal and via-field authority. No conflicting MPN/capacitance/LED-resistor values were found in the sampled traceability-to-component comparison.

CAD-owner action: use the latest matching native reports to resolve any remaining findings, preserve source hashes and process diagnostics, and repeat the filled-copper and assembly-marker review after changes. Report completion, clean tool exit, mechanical coupon acceptance and high-current qualification are separate results.
