package org.archtv.apkruntime;

import android.content.SharedPreferences;
import android.view.View;
import java.nio.file.Path;
import java.util.HashMap;
import java.util.Map;

public final class AppEnvironment {
    private static AppEnvironment instance;
    public final ApkResources resources;
    public final Integer virtualDisplayId;
    public final android.app.Application applicationContext;
    public View focus;
    private final Path dataDirectory;
    private final Path apkPath;
    private android.content.pm.ApplicationInfo applicationInfo;
    private final Map<String, SharedPreferences> preferences = new HashMap<String, SharedPreferences>();
    private AppEnvironment(Path apk, Path data, Path systemResources, Integer displayId) throws Exception {
        if (displayId != null && displayId != 0) throw new IllegalArgumentException("Only virtual display 0 is supported");
        virtualDisplayId = displayId;
        LinuxContext base = new LinuxContext();
        resources = new ApkResources(apk, systemResources);
        try {
            applicationContext = new android.app.Application();
            java.lang.reflect.Method attach = android.content.ContextWrapper.class.getDeclaredMethod(
                "attachBaseContext", android.content.Context.class);
            attach.setAccessible(true);
            attach.invoke(applicationContext, base);
        } catch (Exception | Error problem) {
            resources.close();
            throw problem;
        }
        dataDirectory = data;
        apkPath = apk;
    }
    public static void initialize(Path apk, Path data) throws Exception { initialize(apk, data, null); }
    public static void initialize(Path apk, Path data, Path systemResources) throws Exception { initialize(apk, data, systemResources, null); }
    public static void initialize(Path apk, Path data, Path systemResources, Integer displayId) throws Exception {
        if (instance != null) throw new IllegalStateException("One APK per process");
        instance = new AppEnvironment(apk, data, systemResources, displayId);
    }
    public static AppEnvironment current() {
        if (instance == null) throw new IllegalStateException("App environment not initialized");
        return instance;
    }
    public synchronized android.content.pm.ApplicationInfo applicationInfo() {
        if(applicationInfo==null)applicationInfo=ApkMetadata.read(apkPath,dataDirectory);
        return new android.content.pm.ApplicationInfo(applicationInfo);
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
