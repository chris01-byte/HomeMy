# PMU 280 × 220 mm — new layout

User-authorized on 2026-09-11: rebuild the complete layout within 280 × 220 mm
on a separate branch, retaining the first passing Rev-A circuit and rules.
This replaces the closed task's requirement to start from the 275-mm WIP.

- Branch: `codex/pmu-rev-a1-280x220-rebuild`.
- Isolated worktree: `pmu-280x220-rebuild`; unrelated schematic edits in the old
  worktree are neither sources nor changes for this task.
- Electrical source: original Rev A-P1, PCB SHA-256
  `13fcae0f58c9a6ac5f85eb721c24b44169a65f628baad6586bcd6002f4c17cfe`.
- All 425 footprint/pad identities, circuit values, DNP choices, net names,
  four-layer stackup, protection topology and numerical design rules remain.
- Placement and copper are newly planned. Only exact, pad-anchored rigid copies
  of reviewed local copper are eligible for reuse, with an explicit provenance
  receipt. No 250/275/280/300-mm WIP geometry is a layout source.
- Existing rule/tap capture is immutable. New thin power copper cannot be
  declared an exception; any migrated exception must prove its original geometry,
  group, layer, dimensions, net and pad anchors by inverse rigid transform.
- Exactly one lead CAD writer. Other agents provide read-only analysis.

## Bounded execution

Start: 2026-09-11T16:27:00Z. Hard deadline: 2026-09-11T19:27:00Z.
At 19:07 UTC stop editing and reserve time for reports, commit and push.
At most six edit/native-check cycles and four autorouter calls; each router call
at most 600 seconds and 250 passes. No automatic optimizer is enabled.
At most two corrective attempts for an unchanged root cause, two consecutive
cycles without admissible measurable progress, and two restarts of a crashed
identical native process. A technical conflict requiring weaker safety rules
also stops the work. Time and counters are checked before each operation.

The initial mechanical placement is a distinct gate; then power and critical
routes must be established before general signal routing. Local read-only
screens may reject a proposed coordinate before it changes the candidate.
Each full cycle records its specific objective, native outcomes and input hashes.
Progress means a passed placement gate, an added required/critical path, at least
five closed connections, a five-percent open-count reduction, or fewer native
errors/dangling items, without losing previously accepted critical/required paths
or introducing shorts/clearance violations. Initial incomplete CAD is explicitly
unreleased; individual failed gates are never inferred to pass from totals.

At a stop boundary restore the best validated candidate, document remaining
blockers, mark WIP, commit/push this branch and finish. All original branches,
Rev-A sources, and earlier WIP variants remain unchanged.

## Acceptance

Exact dimensions; complete source/PCB parity; native ERC/DRC exit 0 with no
findings, opens or dangling copper; all 247 original power-pad pairs and 46
critical paths; independent actual-copper, preserved-rule, local neck/via,
mechanical access/press-fit/mount/antenna and assembly checks. Refill, save and
reload before final checks. Record hashes and unresolved physical qualification.
Only a complete CAD result may produce new fabrication outputs. All fabrication,
assembly and production release flags remain false pending a separate release.
No fabrication order, energization, battery or actuator activity is included.
