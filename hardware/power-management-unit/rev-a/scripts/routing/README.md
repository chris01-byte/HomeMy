# Headless routing diagnostics and checkpoint helper

This helper uses the unmodified public Freerouting 2.1.0 Java API on the local Java 21 runtime. It takes DSN input and writes routing candidates to a private directory. It never loads or saves the native KiCad board. Output is engineering review material, with `rev_a_engineering_prototype: true`, `rev_b_production: false`; it is not a routing, DRC or fabrication release.

The existing Java 25 runtime encountered an access denial while initializing its security configuration in this execution environment. No security settings, filesystem permissions or sandbox restrictions were changed. Java 21 already runs the older compatible router.

## Diagnosed CLI behavior

The tagged 2.1.0 source assigns `-mp` to `RouterSettings.maxPasses`, but `BatchAutorouter.runBatchLoop()` compares its counter to `get_stop_pass_no()`. The latter defaults to 999 and the CLI does not set it. Thus `-mp 20` alone does not bound this headless routing loop. The supported general settings parser can set `--router.stop_pass_no=1`; an isolated test with that option actually ended after one pass and wrote a 382,125-byte SES. The test reduced the router's incomplete count to 189, with zero router-reported clearance violations. Those are router metrics, not KiCad DRC results.

The CLI writes the output file only for the `COMPLETED` state. The scheduler timeout can produce `TIMED_OUT`, which the CLI's waiting condition does not accept as a terminal state. An external kill can therefore lose otherwise useful progress. Version 1.9.0 has a headless board-handling base class, but its command entry point still constructs a graphical board window; it does not provide the desired complete headless CLI fallback.

Primary source references:

- [2.1 command argument assignment](https://github.com/freerouting/freerouting/blob/v2.1.0/src/main/java/app/freerouting/settings/GlobalSettings.java)
- [2.1 actual stop-pass field and setter](https://github.com/freerouting/freerouting/blob/v2.1.0/src/main/java/app/freerouting/settings/RouterSettings.java)
- [2.1 routing loop and same-thread update callbacks](https://github.com/freerouting/freerouting/blob/v2.1.0/src/main/java/app/freerouting/autoroute/BatchAutorouter.java)
- [2.1 CLI completion/output conditions](https://github.com/freerouting/freerouting/blob/v2.1.0/src/main/java/app/freerouting/Freerouting.java)
- [2.1 scheduler timeout handling](https://github.com/freerouting/freerouting/blob/v2.1.0/src/main/java/app/freerouting/management/RoutingJobSchedulerActionThread.java)
- [1.9 graphical command entry point](https://github.com/freerouting/freerouting/blob/v1.9.0/src/main/java/app/freerouting/gui/MainApplication.java)

## Checkpoint workflow

`CheckpointRouter.java` uses the public `set_stop_pass_no()` setter, explicitly disables optimization, and uses one routing worker. It obtains geometry-aware layer costs from `new RouterSettings(board)`. It saves SES, resumable DSN and router statistics every ten seconds at a completed route-step callback. Serialization happens synchronously on the routing thread, avoiding a snapshot of a concurrently mutating board. It also preserves the checkpoint with the lowest router-incomplete count. That selection criterion is recorded by its filename and does not certify electrical quality or native clearances.

At the explicit time bound it requests cooperative stop, waits 45 seconds, and retains the last safe checkpoint if the routing step does not stop. The supervisor never exports the live mutable board. The Python launcher has a separate outer timeout, checks source/input hashes, captures caught engine exceptions, and writes a run manifest. Each run must use a new output directory. Logs preserve internally caught NPEs/shove errors; the helper does not suppress them or reinterpret them as success.

The launcher compiles the helper using Eclipse ECJ 3.38.0 from the [official Maven Central artifact](https://repo.maven.apache.org/maven2/org/eclipse/jdt/ecj/3.38.0/ecj-3.38.0.jar), avoiding a second JDK installation. Both the compiler jar and router jar remain outside the project under `tools-local`; hashes are captured in each run manifest. The source excerpts used for diagnosis retain the upstream GPL license in `upstream-source/`.

Example from the worktree root, with the bundled Python executable:

```powershell
python hardware/power-management-unit/rev-a/scripts/routing/run_checkpoint_router.py `
  --java ../tools-local/java21/jdk-21.0.12.1+1-jre/bin/java.exe `
  --router-jar ../tools-local/freerouting-2.1.0.jar `
  --compiler-jar ../tools-local/ecj-3.38.0.jar `
  --input hardware/power-management-unit/rev-a/reports/HomeMy_PMU_RevA.dsn `
  --output hardware/power-management-unit/rev-a/reports/routing-run-001 `
  --passes 200 --seconds 1200
```

The bounded resume test stopped cooperatively after 20.36 s and preserved a 131-incomplete candidate, but the Freerouting-written DSN reload emitted `clearance class not found at kicad_default` and normalized 146 incompletes to 147 before routing. **Use SES import into native KiCad, native zone fill/DRC and a fresh KiCad DSN export for continued engineering work.** Direct DSN checkpoint resume is diagnostic only until its rule/net/geometry round trip is verified. A continuous long run from a fresh native DSN avoids that round-trip issue. Always use a new output directory. Routing order is randomized upstream, so candidate geometry is not bit-reproducible; hashes capture provenance. The command can optionally skip specified net classes through `--ignore-net-classes`; doing so deliberately leaves them for separate engineering routing and must be reflected in final connectivity review.

Before integrating a candidate, verify its footprint/net identities against the actual board snapshot, import SES into the intended KiCad board, fill native zones, run native KiCad DRC with all unconnected nets reported, and inspect Kelvin, gate, switching-current, high-current and thermal paths. Router clearance=0 and incomplete=0 are insufficient release evidence. Do not classify returned PCB connectivity as adequate until those native checks pass.

## Final retained candidate

Run 002 stopped cooperatively at its 1,200 s time bound with 15 router-incomplete
connections in its best checkpoint. The selected earlier frozen session is
retained separately as `../../reports/routing-final-selected.ses`, SHA-256
`30ff3126f797f816506923bb6c97da340ea58be75bee15d42c2b8535435c311a`.
After native import and fill it had six open connections and eleven duplicated
dangling branches. The explicit local repair plan in
`../../design/FINAL_ROUTING_REPAIRS.json` completed those connections, removed
the diagnosed stubs and adjusted two local pin escapes. The final native ERC and
DRC reports have zero findings, zero open connections and zero parity issues;
their separate process-exit limitation is recorded in
`../../reports/native-checks-both.json`. The router's own partial result is kept
unchanged and is not presented as an automatic routing pass.
