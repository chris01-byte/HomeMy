# HomeMy PMU Revision A engineering work

rev_a_engineering_prototype: true  
rev_b_production: false

This directory contains the developing engineering implementation of the PMU
requirements at repository baseline `1a70bec1de092db8a2d101e67e9e882622992003`.
The authoritative requirements and staged verification plan remain in the parent
directory. Component calculations are design evidence, not measurements.

Completion and release are tracked in `release.json`. A missing or failed CAD
check must never be interpreted as a pass. Fabrication exports are review
artifacts; ordering requires the project owner's review. No physical hardware
has been energized or ordered by this work.

`design/` records circuit decisions and machine-readable component connections.
`evidence/` records manufacturer sources and retrieved datasheets.
`scripts/` contains reproducible generation and validation tools.

The local checkout is on `codex/pmu-rev-a`. Revert its individual commits to roll
back the engineering artifacts; this work does not change robot runtime or
customer-mode defaults.
