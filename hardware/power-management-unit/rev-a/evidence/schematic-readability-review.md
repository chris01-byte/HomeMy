# Schematic readability review

`rev_a_engineering_prototype: true`  
`rev_b_production: false`  
Date:2026-09-10. Display changes were confined to `scripts/build_schematic.py`; no PCB changes.

Left-side global labels now extend outward instead of crossing pin numbers/names. Two-pin resistors and capacitors use conventional graphics; duplicate internal passive pin names are hidden while pin numbers remain visible. Connector bodies expand to fit long names, with full widths quantized to2.54mm so both edges stay on the1.27mm connection grid. Displayed titles and the revision field fit the native title block; filenames and sheet assignments are unchanged.

Native KiCad10.0.6 SVGs were rasterized with bundled Node.js/Sharp at6720×4752pixels. I inspected the ESP32/TMUX/permission page, analog-chopper page, wake-passive page and title-block crops. The original label overlap is visible in [before](schematic-before/HomeMy_PMU_RevA-06c_esp32_p1-detail.png); the corrected dense page is [after](schematic-after/HomeMy_PMU_RevA-06c_esp32_p1-detail.png). The [passive detail](schematic-after/HomeMy_PMU_RevA-06a_aon_wake_p2-detail.png) completes the three retained comparison crops. The inspected chopper ICs and title block were also readable; the complete final native pages are retained once in [assembly/schematic](../assembly/schematic), including [chopper](../assembly/schematic/HomeMy_PMU_RevA-04_brake_chopper_p1.svg) and [ESP32/title](../assembly/schematic/HomeMy_PMU_RevA-06c_esp32_p1.svg).

[Native XML comparison](schematic-readability-review.json) verified 1,214 connected source pins across 421 non-flag components with **zero net/type mismatches**, preserved component UUIDs and exactly four DNP references:C244/J13/R243/R244. This refreshed export includes BC1–BC15 added by the integration owner: 430 schematic components including nine power flags. The [latest native ERC report](erc-after-schematic-readability.json) contains **zero violations**. An intermediate width calculation generated24 off-grid warnings; quantization corrected them without exclusions.

The portable KiCad processes returned exit1 after Windows registry-access errors despite generating complete, parseable SVG/XML/ERC artifacts. The report result and process status are recorded separately; a clean process exit is not claimed. Sharp emitted font-cache warnings, but KiCad's vector stroke lettering rendered correctly in the inspected images.

This remains a functional pin-level hierarchical schematic. The review improves legibility and checks electrical preservation; it does not claim a manually composed application-circuit drawing, routed-board correctness or hardware validation. Final SVGs have been consolidated into assembly/schematic with SHA-256 copy verification; duplicate SVGs and full-page raster galleries were removed. The review JSON records all retained artifact hashes. Any PDF export still needs to use the updated generator.
