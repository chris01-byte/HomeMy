# HomeMy Agent Instructions

1. Read AGENTS.md and CURRENT_STATE.md before changing code.
2. Select one matching area from context/index.json and load only its listed files.
3. Use python tools/context/brief.py --area <area> when a local checkout is available.
4. Do not load all docs, transfer records, or archives by default.
5. Never enable actuators, commit secrets or real home data, or treat simulation as real-hardware approval.
6. For a transfer from roboter_ws, update the transfer manifest before porting code.
7. Record a durable decision in docs/decisions/ and current facts in CURRENT_STATE.md.
8. Keep every change small, testable, and reversible.
