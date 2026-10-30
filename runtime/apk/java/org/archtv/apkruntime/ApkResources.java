package org.archtv.apkruntime;

import android.content.res.ApkAssets;
import android.content.res.AssetManager;
import android.content.res.Resources;
import android.content.res.Configuration;
import android.util.DisplayMetrics;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.nio.file.Path;
import java.util.zip.ZipEntry;
import java.util.zip.ZipFile;

/** Host initialization adapter; all resource parsing and value resolution use original AOSP. */
public final class ApkResources implements AutoCloseable {
    private final ApkAssets apkAssets;
    private final AssetManager manager;
    private final Resources resources;
    private boolean closed;

    public ApkResources(Path apk) throws Exception {
        // Retain the laboratory input budget without interpreting the resource table.
        try (ZipFile archive = new ZipFile(apk.toFile())) {
            ZipEntry table = archive.getEntry("resources.arsc");
            if (table == null || table.getSize() < 0 || table.getSize() > 16*1024*1024)
                throw bad("Missing or oversized resources.arsc", null);
        }
        ApkAssets loaded = null;
        AssetManager created = null;
        try {
            loaded = ApkAssets.loadFromPath(apk.toString());
            // Host initialization has no framework-res.apk/overlays yet. This is the
            // original internal constructor used by AOSP Builder, not an API replacement.
            Constructor<AssetManager> constructor = AssetManager.class.getDeclaredConstructor(boolean.class);
            constructor.setAccessible(true);
            created = constructor.newInstance(false);
            Field object = AssetManager.class.getDeclaredField("mObject");
            object.setAccessible(true);
            Method install = AssetManager.class.getDeclaredMethod("nativeSetApkAssets", long.class, ApkAssets[].class, boolean.class);
            install.setAccessible(true);
            ApkAssets[] assets = {loaded};
            install.invoke(null, object.getLong(created), assets, false);
            Field inventory = AssetManager.class.getDeclaredField("mApkAssets");
            inventory.setAccessible(true);
            inventory.set(created, assets);
            DisplayMetrics metrics = new DisplayMetrics();
            metrics.setToDefaults();
            metrics.widthPixels = metrics.noncompatWidthPixels = 1280;
            metrics.heightPixels = metrics.noncompatHeightPixels = 720;
            Configuration configuration = new Configuration();
            configuration.setToDefaults();
            resources = new Resources(created, metrics, configuration);
            apkAssets = loaded;
            manager = created;
        } catch (Exception error) {
            try { if (created != null) created.close(); }
            finally { if (loaded != null) loaded.close(); }
            throw bad("AOSP asset initialization", error);
        }
        System.err.println("APK_RESOURCES_AOSP_READY");
        System.err.println("APK_PUBLIC_RESOURCES_AOSP_READY");
    }
    private static IllegalArgumentException bad(String message, Throwable cause) {
        return new IllegalArgumentException("Unsupported or invalid APK resources: "+message, cause);
    }
    public synchronized String getString(int resourceId) {
        if (closed) throw new IllegalStateException("APK resources closed");
        return resources.getString(resourceId);
    }

    @Override public synchronized void close() {
        if (closed) return;
        closed = true;
        try { manager.close(); }
        finally { apkAssets.close(); }
    }
}
