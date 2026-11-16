# PMU Revision A2 (280 × 260 mm) is the only current board

Status: accepted.

## Context

The repository held three PMU boards: the original 360 × 300 mm Revision A (with an order package marked fabrication- and assembly-released), an unfinished 300 × 280 mm A1 layout, and the completed 280 × 260 mm A2 layout. The mandatory context files still named 300 × 280 mm as the only target. The instruction to build 280 × 260 mm had not been recorded in the repository.

## Decision

The project owner decided on 2026-11-16: Revision A2, 280 × 260 mm, under `hardware/power-management-unit/rev-a2-layout-280x260/`, is the only current PMU board. All other boards and their packages are deleted.

Removed: `rev-a1-layout-300x280/`, `ASTRA_300X280_LAYOUT.md`, the 360 × 300 mm PCB and duplicate KiCad sources under `rev-a/kicad/`, the Rev A-P1 order package with ZIP and preview Gerbers, `rev-a/release.json`, board-specific reports, renders, placement and routing data, and the autorouter tooling.

Kept under `rev-a/`: circuit design records, calculations, datasheets, the rule review, checker sources and process documents. They apply unchanged to A2 because A2 uses the identical schematic.

Not selected: restoring or continuing any other board size.

## Evidence

- The A2 KiCad sources other than the PCB were byte-identical to `rev-a/kicad/` (69 of 69 files) and all 1377 pads carry the same nets; see `hardware/power-management-unit/reviews/2026-11-16-rev-a2-gegenpruefung/teilberichte/nachweise-und-fertigungsdaten.md`.
- Native ERC, DRC and schematic parity of A2 reproduce with zero findings (KiCad 10.0.8).
- The old board shared the weaknesses GP-01 and GP-02 of the cross-review and was marked released without a recorded owner decision (GP-23).

## Impact

- No electrical, CAD or release-flag change. A2 remains a draft that is not orderable; the cross-review lists 25 open findings.
- Reports under `rev-a2-layout-280x260/reports/` are snapshots of commit `d37c7f7`; comparison files they name were removed.
- Rollback: every removed file is available at commit `d37c7f70536507b69d8bcac9a166c7d541a8984e` (`git checkout d37c7f7 -- <path>`).
