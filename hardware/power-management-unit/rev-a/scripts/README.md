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

## High-current rules and geometry

`configure_power_rules.py` maintains four power classes and actual custom-rule
minima: 4 mm battery/SYS/motion tracks, 6 mm arm returns, 0.8/0.4 mm power vias
and a scoped 1 mm neck screen. `configure_fabrication.py` includes these rules.
Exact low-current tap UUIDs and canonical geometry hashes are captured in
`evidence/high-current-tap-capture.json`; initial capture refuses an unknown
board. Do not recapture new thin tracks as exceptions. Kelvin nets retain their
signal class. See `design/HIGH_CURRENT_RULES.md` for all exceptions and necks.

`refine_power_zones.py` applies the 1.2 mm minimum fill and BATT_N extent change.
Changing copper requires a new refill, physical-geometry review and native
ERC/DRC; do not reuse release checks after edits. `audit_high_current.py` checks
classes, minima, exact tap geometry and power-path evidence. The negative-control
script uses a separate temporary board and must never alter the release PCB.

## Native checks and prototype exports

`run_native_checks.py --kicad-root PATH` calls the actual `kicad-cli` directly and
records native exit codes, complete JSON reports/logs, input hashes and elapsed
time. DRC includes all severities, all track errors and full schematic parity.
A zero-finding report with timeout 124 is a failed process. Historical examples
are archived in `reports/archive-before-prototype-release/`.

The final recorded ERC and DRC both exited **0** using installed KiCad 10.0.6
outside the agent's restricted Windows registry environment. To repeat there,
run the prepared `RUN_NATIVE_CHECKS.cmd` file, or invoke its path with PowerShell's
`&` call operator. Do not paste the batch file's contents into PowerShell.
No administrator privileges are needed. An installation path can also be passed
to the Python runner directly; the native checks do not use `run_tool.py`.

For a changed design, work in this dependency order:

1. Finish CAD, refill zones and review critical routes, placement and orientation.
   Refresh `review_filled_power.py`, `review_critical_routing.py`,
   `review_placement_access.py` and `manufacturing/review_assembly_orientation.py`
   against the actual final PCB. Native scripts use KiCad Python as documented.
2. Run `build_bom.py` and then the native checks. Both CLI processes must exit 0,
   with zero findings/open connections/parity differences and matching inputs.
3. Refresh `evidence/write_power_review.py`, then `audit_high_current.py`.
   `prepare_prototype_release.py` verifies these records and sets only the
   engineering-prototype fabrication/assembly scope; it never grants production.
4. Refresh `audit_electrical_parity.py` after updating `release.json` and BOM.
5. Run KiCad Python on `export_manufacturing.py --prototype-version RevA-P1
   --output hardware/power-management-unit/rev-a/manufacturing/HomeMy_PMU_RevA-P1_2026-09-10`.
   It creates Gerbers, drills/maps, placements, BOM copies and assembly views.
   A changed delivery requires a new version/date in the release scripts; do not
   silently replace an already ordered package under the same identity.
6. Run ordinary Python on `build_prototype_package.py` to add press-fit rows,
   mechanical and polarity drawings, integration gates, evidence, manifest and ZIP.
7. Refresh native copper plots and run `render_review.cjs PATH_TO_SHARP`.
   Inspect changed drawings; rendering is separate from visual acceptance.
8. Run `evidence/audit_rule_configuration.py`,
   `evidence/update_rule_review_snapshot.py`, `audit_final_package.py`, and
   `audit_release_metadata.py --output
   hardware/power-management-unit/rev-a/evidence/release-metadata-scope.json`.
   Resolve all consistency findings before committing the delivery.

The final audit verifies current CAD/report hashes, normal native success,
BOM/export coverage, exact delivery and ZIP bytes, high-current evidence and
rendered artifacts. No item-level DRC exclusions are accepted. Rule details are
in `evidence/REVIEWED_DEFAULT_ERC_DRC.md`.

The versioned package is orderable only as a bare/populated engineering
prototype, subject to supplier acceptance of its stackup and press-fit process.
Physical assembly, coupon acceptance, staged energization and production
qualification remain separate; no physical test is claimed by these scripts.
