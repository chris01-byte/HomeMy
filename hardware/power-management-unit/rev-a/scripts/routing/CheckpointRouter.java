// Project helper against the unmodified Freerouting 2.1.0 public Java API.
// It writes only a private DSN/SES run directory. Native KiCad DRC is still required.
import app.freerouting.Freerouting;
import app.freerouting.autoroute.BatchAutorouter;
import app.freerouting.board.ItemIdentificationNumberGenerator;
import app.freerouting.board.RoutingBoard;
import app.freerouting.core.RoutingJob;
import app.freerouting.core.RoutingJobState;
import app.freerouting.core.StoppableThread;
import app.freerouting.core.scoring.BoardStatistics;
import app.freerouting.designforms.specctra.DsnFile;
import app.freerouting.interactive.HeadlessBoardManager;
import app.freerouting.management.analytics.FRAnalytics;
import app.freerouting.management.gson.GsonProvider;
import app.freerouting.settings.GlobalSettings;
import app.freerouting.settings.RouterSettings;
import java.io.ByteArrayOutputStream;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.StandardCopyOption;
import java.security.MessageDigest;
import java.time.Instant;
import java.util.HexFormat;
import java.util.LinkedHashMap;
import java.util.Locale;
import java.util.Map;
import java.util.UUID;

public class CheckpointRouter {
    static Path output;
    static RoutingJob job;
    static long lastCheckpoint;
    static int bestIncomplete = Integer.MAX_VALUE;
    static volatile Throwable failure;
    static volatile boolean deadlineReached;
    static int checkpoints;

    static void write(Path target, byte[] bytes) throws Exception {
        Path temporary = target.resolveSibling(target.getFileName().toString() + ".tmp");
        Files.write(temporary, bytes);
        Files.move(temporary, target, StandardCopyOption.REPLACE_EXISTING);
    }

    static void checkpoint(RoutingBoard board, String reason, boolean force) throws Exception {
        long now = System.nanoTime();
        if (!force && now-lastCheckpoint < 10_000_000_000L) return;
        BoardStatistics stats = new BoardStatistics(board);
        HeadlessBoardManager manager = new HeadlessBoardManager(Locale.ENGLISH, job);
        manager.replaceRoutingBoard(board);
        byte[] ses;
        byte[] dsn;
        try (ByteArrayOutputStream bytes = new ByteArrayOutputStream()) {
            if (!manager.saveAsSpecctraSessionSes(bytes, job.name)) throw new IllegalStateException("SES export failed");
            ses = bytes.toByteArray();
        }
        try (ByteArrayOutputStream bytes = new ByteArrayOutputStream()) {
            if (!DsnFile.write(manager, bytes, job.name, false)) throw new IllegalStateException("DSN export failed");
            dsn = bytes.toByteArray();
        }
        write(output.resolve("latest.ses"), ses);
        write(output.resolve("latest.dsn"), dsn);
        write(output.resolve("latest-statistics.json"), GsonProvider.GSON.toJson(stats).getBytes(java.nio.charset.StandardCharsets.UTF_8));
        if (stats.connections.incompleteCount < bestIncomplete) {
            bestIncomplete = stats.connections.incompleteCount;
            write(output.resolve("best-incomplete-count.ses"), ses);
            write(output.resolve("best-incomplete-count.dsn"), dsn);
            write(output.resolve("best-incomplete-count-statistics.json"), GsonProvider.GSON.toJson(stats).getBytes(java.nio.charset.StandardCharsets.UTF_8));
        }
        checkpoints++;
        lastCheckpoint = now;
        System.out.println(Instant.now()+" CHECKPOINT "+reason+" pass="+job.routerSettings.get_start_pass_no()
            +" incomplete="+stats.connections.incompleteCount+" router_clearance_violations="+stats.clearanceViolations.totalCount
            +" bytes="+ses.length);
        System.out.flush();
    }

    public static void main(String[] args) throws Exception {
        if (args.length < 4 || args.length > 5) {
            System.err.println("CheckpointRouter INPUT.dsn OUTPUT_DIRECTORY MAX_PASSES MAX_SECONDS [IGNORED_NET_CLASSES_CSV]");
            System.exit(64);
        }
        Path input = Path.of(args[0]).toAbsolutePath();
        output = Path.of(args[1]).toAbsolutePath();
        Files.createDirectories(output);
        int passes = Integer.parseInt(args[2]);
        long seconds = Long.parseLong(args[3]);
        if (passes<1 || seconds<1) throw new IllegalArgumentException("Positive bounds required");
        String inputHash = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(input)));
        GlobalSettings.setUserDataPath(output);
        Freerouting.globalSettings = new GlobalSettings();
        Freerouting.globalSettings.guiSettings.isEnabled = false;
        Freerouting.globalSettings.usageAndDiagnosticData.disableAnalytics = true;
        FRAnalytics.setEnabled(false);
        job = new RoutingJob(UUID.randomUUID());
        job.setInput(input.toString());
        HeadlessBoardManager manager = new HeadlessBoardManager(Locale.ENGLISH, job);
        if (manager.loadFromSpecctraDsn(job.input.getData(), null, new ItemIdentificationNumberGenerator()) != DsnFile.ReadResult.OK)
            throw new IllegalArgumentException("Cannot parse input DSN");
        job.board = manager.get_routing_board();
        job.routerSettings = new RouterSettings(job.board);
        job.routerSettings.set_start_pass_no(1);
        job.routerSettings.set_stop_pass_no(passes); // actual loop bound; CLI -mp misses this in v2.1.0
        job.routerSettings.maxPasses = passes;
        job.routerSettings.maxThreads = 1;
        job.routerSettings.setRunOptimizer(false);
        job.routerSettings.setRunFanout(false);
        job.routerSettings.ignoreNetClasses = args.length == 5 && !args[4].isBlank() ? args[4].split(",") : new String[0];
        job.state = RoutingJobState.RUNNING;
        StoppableThread worker = new StoppableThread() {
            protected void thread_action() {
                try {
                    checkpoint(job.board, "input", true);
                    BatchAutorouter router = new BatchAutorouter(job);
                    router.addBoardUpdatedEventListener(event -> {
                        try { checkpoint(event.getBoard(), "route_step", false); }
                        catch (Exception ex) { failure=ex; requestStop(); }
                    });
                    router.addTaskStateChangedEventListener(event -> {
                        System.out.println(Instant.now()+" STATE "+event.getTaskState()+" pass="+event.getPassNumber());
                        System.out.flush();
                    });
                    router.runBatchLoop();
                    checkpoint(job.board, "routing_loop_returned", true);
                } catch (Throwable ex) {
                    failure=ex;
                    ex.printStackTrace();
                }
            }
        };
        job.thread = worker;
        long started = System.nanoTime();
        worker.start();
        worker.join(seconds*1000);
        if (worker.isAlive()) {
            deadlineReached = true;
            worker.requestStop();
            System.out.println(Instant.now()+" STOP requested at explicit time bound; waiting 45 seconds for current route to stop.");
            System.out.flush();
            worker.join(45_000);
        }
        // Never serialize the live mutable board from the supervisor thread.
        // If a routing step ignores cancellation, retain the last same-thread checkpoint.
        Map<String,Object> result = new LinkedHashMap<>();
        result.put("rev_a_engineering_prototype", true);
        result.put("rev_b_production", false);
        result.put("state", "engineering_routing_candidate_not_order_release");
        result.put("input", input.toString());
        result.put("input_sha256", inputHash);
        result.put("max_passes", passes);
        result.put("actual_stop_pass_no", job.routerSettings.get_stop_pass_no());
        result.put("elapsed_seconds", (System.nanoTime()-started)/1e9);
        result.put("deadline_reached", deadlineReached);
        result.put("worker_stopped", !worker.isAlive());
        result.put("checkpoints", checkpoints);
        result.put("best_router_incomplete_count", bestIncomplete);
        result.put("uncaught_exception", failure==null ? null : failure.toString());
        result.put("native_kicad_drc_performed", false);
        result.put("warning", "Router internal errors remain in console log. SES/DSN checkpoints are candidates; native KiCad import and DRC are mandatory.");
        write(output.resolve("run-result.json"), GsonProvider.GSON.toJson(result).getBytes(java.nio.charset.StandardCharsets.UTF_8));
        System.out.println(GsonProvider.GSON.toJson(result));
        System.out.flush();
        // The upstream library can leave background executors alive; all checkpoint
        // streams above are closed. Explicit process exit does not claim completeness.
        System.exit(worker.isAlive() || failure!=null ? 3 : bestIncomplete==0 ? 0 : 2);
    }
}
