package org.archtv.apkruntime;

import android.app.Activity;
import android.os.Handler;
import android.os.Looper;
import android.os.MessageQueue;
import android.view.View;
import android.view.ViewGroup;
import android.widget.LinearLayout;
import android.widget.TextView;
import java.io.InputStreamReader;
import java.io.RandomAccessFile;
import java.nio.channels.FileLock;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.nio.file.attribute.PosixFilePermissions;
import java.util.concurrent.Semaphore;

/** Single-APK host. Commands activate/dump/quit drive real app callbacks. */
public final class Main {
    /** Host-only process shutdown; applications cannot quit Android's main Looper. */
    private static final class UiShutdown extends Error {
        UiShutdown() { super(null, null, false, false); }
    }
    private static String quote(String value) {
        StringBuilder result = new StringBuilder("\"");
        for (int index = 0; index < value.length(); index++) {
            char character = value.charAt(index);
            if (character == '"' || character == '\\') result.append('\\').append(character);
            else if (character < 32) result.append(String.format("\\u%04x", (int)character));
            else result.append(character);
        }
        return result.append('"').toString();
    }
    private static void view(StringBuilder json, View node, int depth) {
        if (node == null || depth > 64) throw new IllegalStateException("Missing or deep View tree");
        json.append("{\"class\":").append(quote(node.getClass().getName()));
        json.append(",\"focused\":").append(AppEnvironment.current().focus == node);
        int[] padding = node.hostPadding();
        json.append(",\"padding\":[").append(padding[0]).append(',').append(padding[1])
            .append(',').append(padding[2]).append(',').append(padding[3]).append(']');
        if (node instanceof TextView) {
            TextView text = (TextView)node;
            json.append(",\"text\":").append(quote(text.hostText()));
            json.append(",\"text_size\":").append(text.hostTextSize());
        }
        if (node instanceof LinearLayout)
            json.append(",\"orientation\":").append(((LinearLayout)node).hostOrientation());
        if (node instanceof ViewGroup) {
            json.append(",\"children\":[");
            boolean first = true;
            for (View child : ((ViewGroup)node).hostChildren()) {
                if (!first) json.append(',');
                first = false;
                view(json, child, depth+1);
            }
            json.append(']');
        }
        json.append('}');
    }
    private static void snapshot(Activity activity, String event) {
        StringBuilder json = new StringBuilder("{\"event\":").append(quote(event)).append(",\"root\":");
        view(json, activity.hostContentView(), 0);
        System.out.println(json.append('}').toString());
        System.out.flush();
    }
    private static boolean contains(View node, View target) {
        if (node == target) return true;
        if (node instanceof ViewGroup)
            for (View child : ((ViewGroup)node).hostChildren()) if (contains(child, target)) return true;
        return false;
    }
    private static String command(InputStreamReader reader) throws Exception {
        StringBuilder line = new StringBuilder();
        int value;
        while ((value = reader.read()) != -1) {
            if (value == '\n') return line.toString();
            if (line.length() >= 4096) throw new IllegalArgumentException("Command too long");
            line.append((char)value);
        }
        if (line.length() != 0) throw new IllegalArgumentException("Incomplete command");
        return null;
    }
    private static void uiThread(Looper owner, String event) {
        if (Looper.myLooper() != owner || Looper.getMainLooper() != owner || Thread.currentThread() != owner.getThread())
            throw new IllegalStateException("Callback outside UI Looper");
        System.err.println("APK_UI_DISPATCH "+event+" thread="+Thread.currentThread().getName());
    }
    private static void runUi(String activityClass) throws Exception {
        Looper.prepareMainLooper();
        Looper owner = Looper.myLooper();
        Handler ui = new Handler(owner);
        Activity[] activity = new Activity[1];
        boolean[] created = new boolean[1], closed = new boolean[1];
        Semaphore pending = new Semaphore(16);
        Throwable failure = null;
        try {
            ui.post(new Runnable() {
                public void run() {
                    uiThread(owner, "create");
                    try {
                        activity[0] = Class.forName(activityClass).asSubclass(Activity.class).getDeclaredConstructor().newInstance();
                    } catch (Exception problem) { throw new IllegalStateException("Cannot construct Activity", problem); }
                    created[0] = true;
                    activity[0].hostCreate();
                    snapshot(activity[0], "ready");
                    Thread reader = new Thread(new Runnable() {
                        public void run() {
                            try {
                                InputStreamReader input = new InputStreamReader(System.in, StandardCharsets.UTF_8);
                                while (true) {
                                    String line = command(input);
                                    final String action = line == null ? "quit" : line;
                                    pending.acquire();
                                    if (!ui.post(new Runnable() {
                                        public void run() {
                                            try {
                                                uiThread(owner, action);
                                                if (action.equals("quit")) {
                                                    created[0] = false;
                                                    try { activity[0].hostDestroy(); }
                                                    finally { AppEnvironment.current().focus = null; }
                                                    closed[0] = true;
                                                    throw new UiShutdown();
                                                } else {
                                                    if (action.equals("activate")) {
                                                        View focus = AppEnvironment.current().focus;
                                                        if (focus == null || !contains(activity[0].hostContentView(), focus) || !focus.performClick())
                                                            throw new IllegalStateException("No clickable focus in content tree");
                                                    } else if (!action.equals("dump"))
                                                        throw new IllegalArgumentException("Unknown command: "+action);
                                                    snapshot(activity[0], "updated");
                                                }
                                            } finally { pending.release(); }
                                        }
                                    })) {
                                        pending.release();
                                        throw new IllegalStateException("UI queue stopped accepting commands");
                                    }
                                    if (action.equals("quit")) return;
                                }
                            } catch (Exception problem) {
                                ui.post(new Runnable() {
                                    public void run() { throw new IllegalStateException("Command reader failed", problem); }
                                });
                            }
                        }
                    }, "archtv-apk-input");
                    reader.setDaemon(true);
                    reader.start();
                }
            });
            try { Looper.loop(); }
            catch (UiShutdown shutdown) { if (!closed[0]) throw shutdown; }
            if (!closed[0]) throw new IllegalStateException("UI loop exited without closing Activity");
        } catch (Exception | Error problem) {
            failure = problem;
            throw problem;
        } finally {
            try {
                if (created[0]) {
                    created[0] = false;
                    uiThread(owner, "destroy-after-failure");
                    try { activity[0].hostDestroy(); }
                    finally { AppEnvironment.current().focus = null; }
                }
            } catch (Exception | Error cleanup) {
                if (failure != null) failure.addSuppressed(cleanup); else throw cleanup;
            } finally {
                // Host shutdown/error unwinds the non-quittable main Looper.
                // Reuse the original, idempotent disposal method from the pinned framework.
                java.lang.reflect.Method dispose = MessageQueue.class.getDeclaredMethod("dispose");
                dispose.setAccessible(true);
                dispose.invoke(owner.getQueue());
            }
        }
        System.out.println("{\"event\":\"closed\"}");
    }
    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("APK ACTIVITY DATA_DIRECTORY required");
        String library = System.getProperty("archtv.linux.library");
        if (library == null) throw new IllegalArgumentException("archtv.linux.library is required");
        System.load(Paths.get(library).toRealPath().toString());
        Path apk = Paths.get(args[0]).toRealPath();
        Path data = Paths.get(args[2]).toAbsolutePath();
        if (Files.isSymbolicLink(data)) throw new IllegalArgumentException("Symlink data directory");
        Files.createDirectories(data);
        Files.setPosixFilePermissions(data, PosixFilePermissions.fromString("rwx------"));
        try (RandomAccessFile lockFile = new RandomAccessFile(data.resolve(".lock").toFile(), "rw");
             FileLock lock = lockFile.getChannel().tryLock()) {
            if (lock == null) throw new IllegalStateException("App data already in use");
            AppEnvironment.initialize(apk, data);
            runUi(args[1]);
        }
    }
}
