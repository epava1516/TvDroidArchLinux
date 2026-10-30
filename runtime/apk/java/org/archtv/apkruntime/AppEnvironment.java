package org.archtv.apkruntime;

import android.content.SharedPreferences;
import android.view.View;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;

public final class AppEnvironment {
    private static AppEnvironment instance;
    public final ApkResources resources;
    public View focus;
    private final Path dataDirectory;
    private final Map<String, SharedPreferences> preferences = new HashMap<String, SharedPreferences>();
    private AppEnvironment(Path apk, Path data) throws Exception {
        resources = new ApkResources(apk);
        dataDirectory = data;
    }
    public static void initialize(Path apk, Path data) throws Exception {
        if (instance != null) throw new IllegalStateException("One APK per process");
        instance = new AppEnvironment(apk, data);
    }
    public static AppEnvironment current() {
        if (instance == null) throw new IllegalStateException("App environment not initialized");
        return instance;
    }
    public synchronized SharedPreferences preferences(String name) {
        if (!name.matches("[A-Za-z0-9_.-]{1,100}") || name.equals(".") || name.equals(".."))
            throw new IllegalArgumentException("Unsupported preference name");
        SharedPreferences value = preferences.get(name);
        if (value == null) {
            value = new IntPreferences(dataDirectory.resolve(name+".properties"));
            preferences.put(name, value);
        }
        return value;
    }
}
