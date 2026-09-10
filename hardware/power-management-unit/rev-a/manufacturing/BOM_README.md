# Revision A BOM

State: `rev_a_prototype_procurement_data`.
`rev_a_engineering_prototype = true`; `rev_b_production = false`.

The versioned `HomeMy_PMU_RevA-P1_2026-09-10` package and `release.json`
authorize bare or populated Rev-A prototype procurement only.
**Engineering prototype – not production qualified.**

Run `python scripts/build_bom.py` from the Revision A directory after
regenerating the assembled CAD record. The builder uses only Python's standard
library. It does not change schematic, PCB, source parts, stock or orders.

`REV_A_BOM.csv` is grouped by exact manufacturer part number, footprint and
DNP status. `REV_A_BOM.json` adds individual reference records, source evidence,
qualification details and excluded PCB features. Quantities describe one PCB
assembly. `quantity_positions` counts schematic positions;
`quantity_required` is zero for DNP rows. Placement waste, spares and minimum
order quantities are not included. The four default DNP positions are retained.

`REV_A_EXTERNAL_BOM.csv` and its JSON companion contain the resistor bank,
external thermistors, cable-side connectors and assembly materials. Selected
parts have exact manufacturer order codes. Unselected lugs, wire grades,
tools, cover materials and external system parts have empty MPNs deliberately.
Custom copper parts also have no manufacturer MPN: their identities and geometry
are controlled by the mechanical drawings, rather than a catalogue order code.
The BOM includes seven individual BB busbars, eight NB star bridges, 23 contact
shims and eight separate branch backing washers. Bare BC1–BC15 contacts are PCB
features and are excluded from purchases. Neither connectors nor copper may
bridge a shunt, FET bank or protected bus.

`MECHANICAL_CATALOG_BOM.json` supplies the exact clamp purchases: 31 screws,
31 nuts, 46 heavy washers, 93 disc springs and one polyimide sheet. The combined
external BOM retains the Goodfellow ordering code and assembly acceptance notes.
The builder verifies these quantities against `busbar-pcb-interface.json` and
includes both source hashes. Extra coupon material and assembly spares are
additional to the stated one-board quantities. Mechanical first-article and
coupon acceptance remain separate from part-identity checks.

`REV_A_BOM_MANIFEST.json` records inputs and output SHA-256 hashes and the
source/CAD reconciliation. A nonzero builder exit means an identity, reference,
population or source/CAD mismatch remains. The review files still record those
errors rather than hiding a component. Successful validation establishes
these data checks; the versioned package supplies the complete procurement
scope. No electrical performance or physical qualification follows from a BOM
validation pass.

The nine unselected external rows have explicit `required_before`,
`fixed_interface` and `closure_evidence` fields. None requires selection before
PCB ordering; all nine must be closed before their powered use. Their selection
must fit the frozen PCB interfaces without changing footprints. See
`HomeMy_PMU_RevA-P1_2026-09-10/integration/OPEN_ORDER_ITEMS.md`.
Supplier acceptance of the specified stackup and press-fit process is a separate
PCB order condition.

Bare test pads, copper net ties, mounting holes and ERC power flags are PCB
features rather than purchased parts. Manufacturer lifecycle observations
and exact/family-level identity evidence are distinguished in each row.
Supplier stock remains unverified for this order. Packaging aliases are
labelled same-source, and the alternate MOSFET requires engineering review.
No replacement is approved solely because it shares a voltage rating or
similar package name.
