# Rebuild scope

Before any analysis or modification in this directory, read in full and follow,
in this order:

1. ASTRA_FINISH_REBUILD_280X220.md
2. RUN_PLAN.md
3. FINAL_REPORT.md
4. the parent AGENTS.md files and their required Rev-A context

The user's 2026-09-12 follow-up authorizes exactly one fresh, bounded completion
run from the committed rebuild PCB identified in
ASTRA_FINISH_REBUILD_280X220.md. This supersedes only the old run's exhausted
counters and the CAD lock recorded in FINAL_REPORT.md. It does not authorize a
new layout, a board-size change, weaker rules, a different source board, a
topology change or a fabrication release.

All original Rev-A electrical, manufacturing and protection rules still apply.
Only the lead agent writes CAD; subagents are read-only reviewers. Do not load
or save a board without its correct sibling .kicad_pro/.kicad_dru. Do not alter
the original Rev-A sources or any earlier compact variant. Keep every release
other than a strictly evidenced cad_complete status false until a separate user
release request.
