package org.archtv.apkruntime;

import android.app.Activity;
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

/** Single-APK host. Commands activate/dump/quit drive real app callbacks. */
public final class Main {
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
    public static void main(String[] args) throws Exception {
        if (args.length != 3) throw new IllegalArgumentException("APK ACTIVITY DATA_DIRECTORY required");
        Path apk = Paths.get(args[0]).toRealPath();
        Path data = Paths.get(args[2]).toAbsolutePath();
        if (Files.isSymbolicLink(data)) throw new IllegalArgumentException("Symlink data directory");
        Files.createDirectories(data);
        Files.setPosixFilePermissions(data, PosixFilePermissions.fromString("rwx------"));
        try (RandomAccessFile lockFile = new RandomAccessFile(data.resolve(".lock").toFile(), "rw");
             FileLock lock = lockFile.getChannel().tryLock()) {
            if (lock == null) throw new IllegalStateException("App data already in use");
            AppEnvironment.initialize(apk, data);
            Activity activity = Class.forName(args[1]).asSubclass(Activity.class).getDeclaredConstructor().newInstance();
            try {
                activity.hostCreate();
                snapshot(activity, "ready");
                InputStreamReader reader = new InputStreamReader(System.in, StandardCharsets.UTF_8);
                String input;
                while ((input = command(reader)) != null && !input.equals("quit")) {
                    if (input.equals("activate")) {
                        View focus = AppEnvironment.current().focus;
                        if (focus == null || !contains(activity.hostContentView(), focus) || !focus.performClick())
                            throw new IllegalStateException("No clickable focus in content tree");
                    } else if (!input.equals("dump")) throw new IllegalArgumentException("Unknown command: "+input);
                    snapshot(activity, "updated");
                }
            } finally {
                activity.hostDestroy();
                AppEnvironment.current().focus = null;
            }
            System.out.println("{\"event\":\"closed\"}");
        }
    }
}
