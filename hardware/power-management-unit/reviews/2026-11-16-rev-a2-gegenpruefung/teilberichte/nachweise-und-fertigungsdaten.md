# Evidence / fab-package / documentation audit — PMU Rev A2 280×260 @ d37c7f70

Path shorthands (absolute):
- `PMU` = `<SITZUNG>/pmu/hardware/power-management-unit`
- `A2` = `PMU/rev-a2-layout-280x260`
- `ROOT` = `<SITZUNG>/pmu`
- `SCR` = `<SITZUNG>/agents/evidence` (all my scripts and outputs; nothing under the worktree or /home/user/HomeMy was modified)

All runs used KiCad 10.0.8 on Linux; the project's evidence was produced with 10.0.6 on macOS.

## Bottom line
- The committed numbers are real and reproducible: all five embedded checkers re-ran with the same results.
- "247/247" and "46/46" are **connectivity statements only**. They carry no width, ampacity or thermal criterion.
- The A2 package is internally consistent (PCB ↔ netlist ↔ BOM ↔ Gerber/drill/pos ↔ manifests).
- The governing documents around A2 are stale and contradictory, and the only "orderable" artifact in the tree is the old 360×300 Rev A-P1 package.

## Task 1 — what 247/247 and 46/46 verify

**Method source and reproducibility**
- The checker source is not present as files. It is embedded as strings in `A2/reports/retest-methods.json` (10 scripts; all 10 embedded SHA-256 values match). Extracted copies are in `SCR/methods/`.
- The scripts hard-code macOS absolute paths and `import wx`, and depend on `PMU/rev-a/scripts/*` and `PMU/rev-a/evidence/high-current-tap-capture.json`.
- After rewriting paths and stripping wx, results were:

| Checker | Result | Match to committed |
|---|---|---|
| power | 247/247, exit 0 | report byte-identical, SHA 200261ee… as in `verification-processes.json` |
| mechanics/connectivity | pass | report byte-identical, SHA 746b7933… |
| critical | 46/46 | identical except timestamp, path and one float ULP |
| artifact audit | pass | — |
| parity | 0 errors | content identical |

- The parity run additionally needed the absolute paths inside `A2/reports/electrical-parity.json` (`adapter.changes`) rewritten.
- "Reconstructed" means the original checkers lived in /tmp and were lost (`retest-methods.json` `purpose`). The embedded power reader is `PMU/rev-a/evidence/review_filled_power.py` lines 1–124 plus path/wx changes and a tap-set union.
- The reconstruction is not identical to the lost original: the original excluded 494 tap objects (`power-and-critical.json` at 0ca837e), the reconstruction 492. Path results are identical to the previous commit.
- Saved zone fills are current: a fresh refill changes total filled area by 0.011 mm² of 195,582 mm², and the refilled copy still scores 247/247.

**What a power pair is**
- A pair is (net, layer, from_pad, to_pad). It passes if a sample point in each pad lies in the same outline of that net's copper on that one layer.
- The copper model is zone fill + pads + tracks, minus the net's own drills, minus 447 "tap" objects (three named groups, 0.2–1.25 mm).
- There is no width criterion. Each row itself says "no minimum width or current rating implied" (`review_filled_power.py:124`).
- The overall `passed` also requires 0 unconnected and that 18 region scans equal previously recorded values.

**How the 247 are chosen** (`review_filled_power.py:86-123`)
- 18 explicit pairs plus 229 generated ones (every pad of J1–J6, Q1–Q10, BC1–15, NT1–8, RSH1/2 on 10 anchor nets → one anchor pad).
- 18 are self-pairs (pad vs itself, e.g. `BC1.1→BC1.1`), which pass by construction. 3 are duplicates. That leaves 226 distinct non-trivial pairs.
- They collapse to 88 component-terminal groups, and to 24 (net, layer) copper islands.
- Not in the list: J7.1, J8.1, J12.1, C312.1/C313.1 (motion-bus + feed to drive, lift, chopper), and all of PC_BUCK_IN_P, LOGIC_BUCK_IN_P, PC_N, LOGIC_BUCK_N, V5V.

**Discriminating power**
- The same checker gives 247/247 on rev-a, and **246/247 on the A1 WIP board, which has 806 open connections**.

**46/46** (`PMU/rev-a/scripts/review_critical_routing.py:28-56, 170, 185`)
- For 46 named pin pairs (Kelvin, filter, gate, boost), a path of explicit track centrelines, vias and pad interiors exists, and the 125 locked analog items have no pairwise collision.
- There is no length, matching or width criterion. Lengths are identical to rev-a (e.g. motion_gate_8 is 123.6 mm for a 22.5 mm direct distance).

**"18 regions … bestanden"** (`A2/FINAL_REPORT.md:29`)
- There is no acceptance threshold. "Pass" means unchanged against an earlier recording of the same PCB.
- Two windows contain no copper: `MOTION_F_chopper_positive` (1999/1999 sections zero) and `LOGIC5V_In2_lower` (1910/2899).

**What these numbers do not show**
- Current capacity, neck widths, via transfer, inter-layer sharing, busbar contact, thermal behaviour.
- Running each check twice shows determinism, not independent confirmation.

**Rev-a's fuller high-current audit was not carried over**
- `PMU/rev-a/scripts/audit_high_current.py` (frozen tap geometry, 85 cross-sections, via-field counts) was not run for A2. Its criteria applied to A2 give 350 errors: 303 changed taps, 45 missing taps, 1 membership change, 1 stale geometry review.
- `PMU/rev-a/design/HIGH_CURRENT_RULES.md:78-80` requires a new bottleneck review after any routing or zone change.

**My own sensitivity test** (morphological opening of the checker's copper model, per layer, ±0.1 mm; not an ampacity proof)
- No pair depends on a neck under 2.4 mm.
- ARM_R_N return is a 6.00 mm strip (x 250–256, y ≈ 89–120) on F.Cu and B.Cu, confirmed by direct scan. Rev-a recorded 12.5 mm. ARM_L_N is 12 mm.
- BATT_N on B.Cu from NT1.2/NT2.2 to BC15.1 has a neck of about 2.6 mm near (207, 144); rev-a had 4.4 mm.
- The uncovered feeds J7.1/J8.1/J12.1 → BC11.1 have about 3.9 mm per outer layer.
- BATT_N power vias: 723 in rev-a (`PMU/rev-a/design/via-field-counts.json`) → 130 in A2.
- None of the new A2 zones for ARM_L/R, BATT_N, CHOP_DRAIN or MOTION_BUS_P B.Cu is among the 18 sampled windows.

**Negative control** (scratch copy)
- A 0.2 mm MOTION track, a 0.6/0.3 via and a 4 mm ARM track are all flagged by the custom rules. DRC = 0 therefore does mean no undersized non-tap power tracks or vias.

## Task 2 — counts
All recounted with pcbnew, netlist, BOM, drill and pos files; **no mismatch**.

| Item | Value |
|---|---|
| Footprints / pads / vias / segments / arcs | 425 / 1377 / 1807 / 3711 / 0 |
| Nets | 257 (+ net 0) |
| PTH / NPTH | 1950 / 4 |
| Press-fit 1.475 mm | 48 (J1–J6 × 8) |
| 3.2 mm PTH | 31 (15 BC + 16 NT) |
| SMD positions | 327, all top |
| BOM positions / populated / DNP | 356 / 352 / 4 |
| Grouped lines / external lines | 124 / 31 |
| Copper objects | 5595 (5518 + 77 zones) |

- BOM vs netlist (421 components): every BOM ref appears exactly once; 0 MPN, footprint, value or DNP mismatches.
- DNP = {C244, J13, R243, R244} in netlist, PCB and BOM.
- 65 symbols carry exclude_from_bom: TP1–40, BC1–15, NT1–10. This is reasonable; the clamp hardware is in the external BOM and its quantities (31 screws, 23 shims, 8 bridges) match the PCB.
- H1–H4 are board-only.
- CSV equals JSON. BOM manifest input and builder hashes match.
- External-BOM busbar hole coordinates match the A2 pads, not rev-a's.
- The stated "494 tap UUIDs / 47 removed" (`A2/FINAL_REPORT.md:51`, `filled-copper-review.json`, `retest-2026-11-16.json`) contradicts 492 / 45 (`power-and-critical.json`, the rev-a capture, and my recount: 447 present, all a subset of the 492).

## Task 3 — fab draft vs PCB
- Regenerated Gerbers (11 + job), PTH/NPTH drill, drill report and pos with the manifest's options into `SCR/fab/`.
- The committed files differ only in KiCad version string and timestamp lines. The pos file is byte-identical. The draft corresponds to this exact PCB, and all 16 manifest hashes are valid.
- Drill table:

| Tool | Size | Count |
|---|---|---|
| T1 | 0.200 | 18 (thermal vias in U10 / U30 pads) |
| T2 | 0.300 | 683 |
| T3 | 0.400 | 1124 |
| T4 | 1.000 | 15 |
| T5 | 1.100 | 6 |
| T6 | 1.200 | 4 |
| T7 | 1.400 | 21 |
| T8 | 1.475 | 48 |
| T9 | 3.200 | 31 |
| NPTH | 3.200 | 4 |

- No slots, no overlaps, no hole web under 0.35 mm, minimum hole-to-edge 0.75 mm.
- T8 is a distinct tool but is tagged only `ComponentDrill`. The pads have no press-fit property; setting it in a scratch copy yields `ComponentDrill,PressFit`.
- Draft marking is adequate at directory, README, manifest, BOM `state` column and silkscreen level (`PMU A.2 280x260  DRAFT - NOT RELEASED`).
- Gerber and drill filenames are `HomeMy_PMU_RevA-*`, with neither "DRAFT" nor "A2", and the same stem and gbrjob GUID as the released rev-a package.
- Separation from the released 360×300 board is weak; see finding M3.

## Task 4 — electrical identity
- 69/69 non-PCB files are byte-identical between rev-a, A2 and A1.
- PCB vs PCB: 425 refs with the same UUIDs, FPIDs, values, DNP flags, attributes and fields; all 1377 pads have the same UUID, number, net and local geometry. 0 differences.
- A fresh A2 netlist equals `PMU/rev-a/evidence/netlist-after-schematic-readability.xml` (421 components, 257 nets, identical node sets).
- All 1297 netted PCB pads match the netlist.
- Copper provenance checked independently: 4379 imported (all UUIDs exist in rev-a, geometry = rev-a + stated translation except 4 documented edits) plus 1216 new = 5595, none unmanifested.

## Task 5 — stale or contradictory statements
`ROOT/tools/context/brief.py --check` exits 0 and all indexed files exist, but it validates only existence and size. No A1 or A2 commit touched anything outside its own directory.

| Location | Statement | Reality |
|---|---|---|
| `ROOT/CURRENT_STATE.md:5` | only active target is 300×280 under `rev-a2-300x280`; "assembly … authorization remain false" | directory does not exist; `rev-a/release.json:28` says true |
| `ROOT/CURRENT_STATE.md:60` | next step: create the 300×280 PCB | A2 280×260 is complete |
| `ROOT/context/index.json:121-126` | "canonical 300 x 280 mm" | no entry points to A2 |
| `PMU/README.md:7, 18, 28-32` | "ausschließlich 300 × 280 mm", target `rev-a2-300x280/` | — |
| `PMU/AGENTS.md:20, 24` | same target | — |
| `PMU/AGENTS.md:31` | no router temp files or duplicates | tree contains both |
| `PMU/AGENTS.md:32` | release flags stay false | `rev-a/release.json:27-28` true |
| `PMU/ASTRA_300X280_LAYOUT.md:1, 5, 7, 30, 42, 84` | 300×280 brief | — |
| `PMU/ASTRA_300X280_LAYOUT.md:59-64` | max 10 loops, max 1 autorouter run | A2 history: 28 + 7 + 7 cycles, limit self-raised 20→28, 2 autorouter calls |
| `PMU/rev-a/README.md:9, 27-32, 91` | 360×300 "order package" + ZIP | no "superseded" note |
| `PMU/REQUIREMENTS_TRACEABILITY.md:80, 82` | BATT_N via counts; 360×300, H3 at (292, 292) | stale for A2 |
| `PMU/REV_A_ASSUMPTIONS.md:24` | 360×300, H1–H4 coordinates, BB7 348 mm | stale for A2 |
| `PMU/rev-a/manufacturing/PCB_STACKUP_PRESSFIT.md:7` | outline 360×300 | `A2/manufacturing/DRAFT_NOT_RELEASED.md:15` declares this spec applicable "unchanged" |
| `PMU/rev-a/manufacturing/PCB_STACKUP_PRESSFIT.md:25-31` | three drill classes, vias 0.40 mm | files hold 683 × 0.30 and 18 × 0.20 |
| `PMU/rev-a/design/CHOPPER_MECHANICS.md:99` | PCB is 360×300 | — |
| `A2/FINAL_REPORT.md:41` | 280×260 justified by a "later explicit user instruction" | not in the repo |

- Most misleading for a newcomer: `PMU/README.md` and `PMU/AGENTS.md` (mandatory reading), `ROOT/CURRENT_STATE.md` and the index. Following them, one would restart a 300×280 layout and never learn that A2 exists.

## Task 6 — hygiene
- Tracked size: 146.4 MB total. rev-a 115.4 MB, A2 24.1 MB, A1 6.6 MB.
- Account names in paths: about 200 `/Users/<name>` hits (A2: `retest-2026-11-16.json` 167, `retest-methods.json` 13, others; A1 11) and 95 `C:\Users\<name>` hits in about 35 rev-a files. `ROOT/CURRENT_STATE.md:50` states the repo is public.
- No credentials, keys, tokens or home data found. The only e-mail addresses are vendor contacts inside datasheet text.
- Router temp files: `PMU/rev-a/reports/routing-run-001/` and `-002/`, 24 files, 7.76 MB, including best == latest duplicates and four 0-byte logs.
- Duplicates by hash: 169 redundant files, 8.97 MB. Of these, 138 are the two extra copies of the 69 KiCad sources (4.57 MB).
- `PMU/rev-a/manufacturing/HomeMy_PMU_RevA-P1_2026-09-10.zip` (1.23 MB) is a 74/74 file-identical duplicate of the unpacked directory.
- `PMU/rev-a/manufacturing/engineering-preview/` (5.8 MB) holds Gerbers from an older PCB (SHA 70bb8eb5…; F.Cu and B.Cu differ from P1) under the same filenames, and is still referenced by `PMU/rev-a/release.json:24`.
- Other bulk: 32 vendor PDFs (38.6 MB); `PMU/rev-a/evidence/filled-power-polygons.json` (9.6 MB); `A2/reports/copper-provenance.json` (3.0 MB).
- A2 itself added no router temp files.

## Task 7 — traceability
55 IDs in `requirements.yaml`, 55 rows, statuses equal. The file is dated 2026-09-10 and describes rev-a only.

| Requirement | Verdict | Detail |
|---|---|---|
| MAIN-003 | confirmed not implemented as specified | UV is native fast (R25/R26 523k/10.1k + 1 nF; no 0.5 s delay). OV is 44.52 V nominal, 43.17–46.98 V calculated, so not within 44–45. Recovery 31.67 V vs 32.0. The row says "Documented deviations" (`REQUIREMENTS_TRACEABILITY.md:36`, `REV_A_ASSUMPTIONS.md:14-15`), so it is not claimed met. No recorded owner acceptance; `requirements.yaml` unchanged. |
| PCB-005 | confirmed substitution | Würth 7461103 instead of the Mega-Fit candidate; the "higher-current connector" alternative permits this. The required Rev-A evidence (wire-gauge and ambient derating, exact lug) is deferred to B06, and the lugs are unselected in the external BOM. |
| PCB-006 | confirmed substitution | Phoenix 1776508 (12 A) instead of Micro-Fit; reasonable. Design pulse about 9.3 A vs 8.6 A in the requirement. |
| MON-002 | refuted as weak | 150 A × 3 s = 33.75 J against the datasheet's 5× rated power for 5 s (250 J), with an honest caveat. |
| TOP-004 | design complies (no precharge) | The required inrush test is open (B01). |

## Findings

**BLOCKER** — none for the status actually claimed (CAD-complete draft, not released). M1–M3 block any fabrication release.

**MAJOR**

M1. Power-path evidence is connectivity-only and misses real geometry regressions.
- What: 247/247 includes 18 self-pairs and 3 duplicates and covers 24 copper islands. A board with 806 opens scores 246. The "18 regions passed" have no threshold and two are empty. Rev-a's bottleneck audit was not regenerated.
- Concrete misses: ARM_R_N return halved to 6.0 mm on F+B (unsampled, unreported); BATT_N vias 723 → 130.
- Why it matters: a reader of `A2/FINAL_REPORT.md:25-29` and `A2/release-status.json` will take these as power-integrity passes on a 50 A board.
- Confidence: high.
- Re-verify: `cd SCR/repro/tmp-power && PMU_BOARD=<pcb> /usr/bin/python3 -B count_param.py` (rev-a, A2 and A1 boards); `xsec.py` for the 6.00 mm strip; pair statistics from `A2/reports/power-and-critical.json`.

M2. Mandatory agent context contradicts the result.
- What: see the Task 5 table. There is no committed brief or authorization for 280×260, and the budgets cannot be checked against any committed document.
- Why it matters: the root `AGENTS.md` makes these files the entry point, so the next agent or person is steered to a non-existent 300×280 target.
- Confidence: high.
- Re-verify: `grep -rn "300 × 280\|rev-a2-300x280" ROOT --include=*.md --include=*.json`.

M3. The only "orderable" package is the old 360×300 Rev A-P1.
- What: `fabrication_release` and `assembly_release` are true (`PMU/rev-a/release.json:27-28`, P1 `README.md:5`, and the ZIP). The flags were set in a Codex-authored commit (26c7b05). No D0–D7 owner disposition is recorded, although `PMU/REQUIREMENTS_TRACEABILITY.md:96` requires one before any order.
- Contradictions: `PMU/README.md:22` (not the target geometry), `ROOT/CURRENT_STATE.md:5`, `PMU/AGENTS.md:32`.
- Why it matters: same file stems as the A2 draft plus a stale preview Gerber set make ordering the wrong board plausible. The schematic is byte-identical, so every schematic-level finding of this review applies to that released package as well.
- Confidence: high.

**MINOR**

m1. Checker provenance.
- Originals lost; code exists only inside JSON with absolute macOS paths and wx.
- The reconstruction differs from the original (494 vs 492), so the 494 / 47 figures in the final report are not reproducible.

m2. Vacuous check in the rev-a evidence.
- `PMU/rev-a/scripts/audit_high_current.py:52-56` looks for `net_name`, which the KiCad 10 format does not have. `PMU/rev-a/evidence/high-current-audit.json` therefore has `power_zones: []`, and the 1.2 mm sliver-filter check never ran.
- The property itself holds: pcbnew shows all 25 rev-a and 42 A2 power-class zones at 1.2 mm.

m3. Stale metadata inside A2.
- PCB title block says "WIP / NOT RELEASED", dated 2026-09-13 (`A2/kicad/HomeMy_PMU_RevA.kicad_pcb:11-17`).
- `A2/reports/mechanical-interface.json` status is `WIP_NOT_RELEASED`.
- `A2/reports/copper-provenance.json` carries `pcb_sha256` d0885912…, not the final hash.
- `A2/reports/cycle-and-stop-record.json` still has `full_cad_acceptance: false`.
- `A2/reports/electrical-parity.json` contains `"fabrication_release":true` (an embedded copy of rev-a's release).

m4. Draft fab set against its own spec.
- Press-fit holes are not machine-tagged and there is no `PRESSFIT_HOLES.csv`, although `PCB_STACKUP_PRESSFIT.md:37` requires separate marking.
- T7 (1.400) and T8 (1.475) are adjacent tools.
- The spec omits the 0.3 mm and 0.2 mm drill classes and states the wrong outline.
- No THT/manual placement file, no fab notes. Filenames are unmarked.

m5. Hygiene: account names in paths in a public repo; router temp files, duplicates, ZIP and stale preview set in the tree (Task 6).

m6. Traceability describes rev-a only. MAIN-003 is a deviation without recorded acceptance. PCB-005 derating evidence is deferred.

m7. GUI acceptance (`A2/FINAL_REPORT.md:33`) has no committed artifact. `final_process_check_exit_code: 1` is ambiguous.

**INFO**
- Reproduced: native-graph numbers (6815 items, 257 components), antenna keep-out free of copper on 4 layers, nominal 2D mechanics screen, drill quantisation 0.0005 mm, profile exactly 280×260, all cross-file hashes.
- `mechanics.py` writes `nominal_mechanics=True` as a constant; the real indicator is `passed`.
- The silkscreen carries the draft text, so any release needs a PCB edit, a new hash, and a re-run of all hash-bound evidence.
- PMU mandatory context is about 133 kB against the 36 kB context budget.
- A1 used 11 cycles against the brief's maximum of 10.

## Not verified
- The macOS / KiCad 10.0.6 runs themselves, the GUI open/close, and the screenshots.
- The lost original checkers and the origin of "494".
- The user instruction for 280×260 and the cycle and autorouter budgets.
- The A2 autorouter runs (SelectiveRouter class, DSN/SES not committed).
- Raw ERC/DRC report hashes and the committed netlist hash (path- and date-dependent; file not committed).
- "973 pad anchors".
- MPN lifecycle and stock.
- Any ampacity or thermal property. My corridor widths are single-layer geometric estimates, not ratings.

## Scratch artifacts
- `<SITZUNG>/agents/evidence/methods/`
- `<SITZUNG>/agents/evidence/repro/tmp-power/`
- `<SITZUNG>/agents/evidence/neck_bisect.json`
- `<SITZUNG>/agents/evidence/neck_bisect_reva.json`
- `<SITZUNG>/agents/evidence/fab/`
- `<SITZUNG>/agents/evidence/a2neg/drc_neg.json`