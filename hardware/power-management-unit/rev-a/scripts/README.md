# Revision A CAD and evidence workflow

rev_a_engineering_prototype: true  
rev_b_production: false

Run from the repository root. Ordinary scripts use Python 3. The native board
scripts use the Python shipped with KiCad 10.0.6, which provides `pcbnew`.
`run_tool.py --kicad-root PATH` supplies workspace-local KiCad settings and
libraries. No scripts install software, submit orders, or energize hardware.

The four `design/*-parts.json` files are the captured electrical source.
`design/assembled-parts.json` is their normalized union, including intentional
no-connect pins and DNP attributes. The final native KiCad files are directly
editable; regenerating them is a deliberate replacement operation. In
particular, **`build_board.py` overwrites the routed PCB with fresh placement**.
Preserve a commit before using it on an edited board.

## Capture and initial board generation

1. Recalculate the independent evidence with `design/power_calculations.py`,
   `design/calculate_chopper.py`, and the wake/IO evidence scripts after changing
   their respective inputs. Manufacturer-limit citations remain necessary;
   arithmetic does not establish pulse SOA, temperature, or protection timing.
2. Generate mechanical drawings and contact definitions with
   `manufacturing/build_mechanical.py`; then run `scripts/build_integration.py`.
3. Run `scripts/build_schematic.py`. The root sheet and fifteen child sheets
   embed their symbols and retain stable hierarchy/component UUIDs.
4. Export a native KiCad XML netlist and compare it with the captured source.
   The checked export is `evidence/netlist-after-schematic-readability.xml`.
   The electrical parity audit must be regenerated if the schematic changes.
5. Run `scripts/build_footprints.py --library-root PATH_TO_KICAD_FOOTPRINTS`.
   This vendors the required library files and generates explicitly dimensioned
   custom lands. Inspect `design/footprint-pin-audit.json`; no generic fallback is
   accepted for an unknown part.
6. Through `run_tool.py`, run KiCad Python on `scripts/build_board.py`.
   Run ordinary Python on `scripts/configure_fabrication.py` to apply the
   physical stack and reviewed fine-pitch pad rules.
7. Through `run_tool.py`, run KiCad Python on `scripts/cad_operations.py prepare`.
   This fills the high-current and converter/LED copper, creates transfer vias,
   and preserves individual gate and lower-power routes as locked copper.
   It is intended for a newly placed board, not a board already containing
   these zones. Inspect the real filled shapes and run native DRC before routing.

Example invocation, with the project-local path adjusted to the installed tool:

```text
python hardware/power-management-unit/rev-a/scripts/run_tool.py --kicad-root PATH_TO_KICAD --timeout 60 python hardware/power-management-unit/rev-a/scripts/cad_operations.py prepare
```

## Signal routing

`cad_operations.py dsn` writes the native KiCad Specctra export. The bounded
router workflow is in `routing/README.md`; its tested versions are Freerouting
2.1.0, Java 21, and Eclipse ECJ 3.38.0. It records runtime/input hashes, periodically
saves recoverable sessions, and does not alter the native PCB.

Import a selected session using `cad_operations.py import --session PATH.ses`,
which synchronizes the 63 intentional singleton no-connect net names, refills
native zones and saves the PCB. Router metrics do not substitute
for native KiCad DRC. Continue routing from a **fresh native KiCad DSN export**:
reloading a Freerouting-written DSN can lose its imported clearance-class name.
Keep each routing attempt in a distinct run directory. Compiled helper classes
and frequent recovery snapshots are local working files; retained runs include
their best/latest candidates, logs, metrics, and hashes.

The committed design also includes explicit review corrections. They are
placement-specific overlays, not a claim that any future autoroute is accepted:

- `repair_postroute.py` protects the RSH2 force connection and lift return,
  closes the local chopper-reference/logic-return connections, and clears
  diagnosed foreign signal nets for rerouting.
- `analog_routing_corrections.py` defines the fifteen placement changes and
  locked local filters/paired Kelvin trunks. `integrate_analog.py` applies it,
  preserves the force-current transfer fields, and clears foreign nets named
  in the captured diagnostic DRC. Recompute those diagnostics if the input
  placement/routing differs from the reviewed snapshot.
- `finalize_power_geometry.py` records the corrected motion CS-via position
  and enlarged chopper drain area. Measure the actual connected filled area
  after routing; the polygon outline alone is insufficient.
- `annotate_assembly.py` adds matching library/embedded F.Fab orientation
  graphics and per-connector screw-face notes. Its protected-data audit checks
  that copper, pads, positions and existing UUIDs remain unchanged.
- `integrate_final_routing.py` verifies the specific pre-import PCB and selected
  SES hashes, preserves all 1,959 existing locked copper items and applies
  `final_routing_repairs.py` with `design/FINAL_ROUTING_REPAIRS.json`. The plan
  removes 31 specifically identified unlocked segments and adds 38 locked
  completion items. The final native board has zero open connections; the
  independent native check report remains required. This overlay intentionally
  refuses a different starting board and must not be replayed on the final PCB.

After each electrical overlay, refill zones, resolve native geometric findings,
export a new DSN and complete the remaining routes. The committed final PCB and
its final check hashes are authoritative. Source/calculation generator
reproducibility is documented separately from end-to-end routing reproduction in
`../evidence/generator-reproducibility-review.md`.

## Native checks and exports

`run_native_checks.py --kicad-root PATH` captures ERC and DRC JSON, complete
process logs, input hashes, and elapsed time. DRC includes all severities, all
track errors, and native schematic parity. Report findings, unconnected items,
and parity differences are separate counts. This portable Windows installation
can write a complete report and then fail while closing its denied registry
settings. The script explicitly records that process failure and returns a
failure code; a zero-finding report is not a successful process exit.

Review the enabled/default-ignored checks in
`../evidence/REVIEWED_DEFAULT_ERC_DRC.md`. No item-level DRC exclusions are used.
The same-package 0.15 mm pad constraints do not lower routed-track clearance.
Neither ordinary DRC nor the bulk-copper calculations establish a current or
temperature rating; inspect the actual filled paths and retain the bring-up
gates in the parent directory.

After final native checks and source/PCB parity:

1. Run `build_bom.py` with ordinary Python. Exact PCB and external purchase
   records, DNP positions, and input hashes must reconcile.
2. Set `../release.json` to the actual verified state. Record remaining owner
   review and physical measurements separately from CAD completion.
3. Run `export_manufacturing.py` using KiCad Python through `run_tool.py`.
   The exporter writes eleven Gerber layers, separate PTH/NPTH Excellon files,
   drill maps, assembly views, placement subsets, BOM copies, and a manifest.
   It checks file coverage and source hashes and never saves the source PCB.
   The native assembly SVG viewport is fitted to the board outline without
   changing plotted geometry or physical scale.
4. Render and inspect both assembly views, all four copper layers, drill maps,
   and the mechanical contact drawing. A file-coverage pass alone is not a
   geometry or assembly review.
5. Re-run the electrical, rule-configuration, and placement review audits after
   any affected source changes; record final report/input hashes in the release
   evidence. Commit the reviewable artifacts on the feature branch.

`render_review.cjs PATH_TO_SHARP` reproduces the retained PNG views from the
native SVGs; visual inspection remains a separate review action.
`audit_final_package.py` verifies the recorded input/output hashes, current PCB
identity and final findings across the native, electrical, BOM, manufacturing,
critical-routing, filled-power and placement reports. Its artifact-consistency
result does not reinterpret the native processes' failed shutdown as success.

The Gerber/placement package retains an engineering-review status. Actual
fabrication, assembly, press-fit qualification, and battery energization are
separate owner actions. No physical tests are claimed by the scripts.
