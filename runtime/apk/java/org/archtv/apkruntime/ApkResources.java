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
    private final ApkAssets[] apkAssets;
    private final AssetManager manager;
    private final Resources resources;
    private boolean closed;

    public ApkResources(Path apk) throws Exception { this(apk, null); }

    public ApkResources(Path apk, Path systemResources) throws Exception {
        checkTable(apk);
        if (systemResources != null) checkTable(systemResources);
        ApkAssets loaded = null;
        ApkAssets system = null;
        AssetManager created = null;
        try {
            if (systemResources != null)
                system = ApkAssets.loadFromPath(systemResources.toString(), ApkAssets.PROPERTY_SYSTEM);
            loaded = ApkAssets.loadFromPath(apk.toString());
            // Explicit bootstrap asset set; the original internal constructor is also
            // used by AOSP Builder. Global Android overlays remain outside this host.
            Constructor<AssetManager> constructor = AssetManager.class.getDeclaredConstructor(boolean.class);
            constructor.setAccessible(true);
            created = constructor.newInstance(false);
            Field object = AssetManager.class.getDeclaredField("mObject");
            object.setAccessible(true);
            Method install = AssetManager.class.getDeclaredMethod("nativeSetApkAssets", long.class, ApkAssets[].class, boolean.class);
            install.setAccessible(true);
            ApkAssets[] assets = system == null ? new ApkAssets[]{loaded} : new ApkAssets[]{system, loaded};
            install.invoke(null, object.getLong(created), assets, false);
            Field inventory = AssetManager.class.getDeclaredField("mApkAssets");
            inventory.setAccessible(true);
            inventory.set(created, assets);
            DisplayMetrics metrics = new DisplayMetrics();
            metrics.setToDefaults();
            int width = Integer.parseInt(System.getProperty("archtv.display.width", "1280"));
            int height = Integer.parseInt(System.getProperty("archtv.display.height", "720"));
            checkSize(width, height);
            metrics.widthPixels = metrics.noncompatWidthPixels = width;
            metrics.heightPixels = metrics.noncompatHeightPixels = height;
            Configuration configuration = new Configuration();
            configuration.setToDefaults();
            setDimensions(configuration, metrics);
            resources = new Resources(created, metrics, configuration);
            apkAssets = assets;
            manager = created;
        } catch (Exception | Error error) {
            if (created != null) try { created.close(); } catch (Throwable close) { error.addSuppressed(close); }
            if (loaded != null) try { loaded.close(); } catch (Throwable close) { error.addSuppressed(close); }
            if (system != null) try { system.close(); } catch (Throwable close) { error.addSuppressed(close); }
            if (error instanceof Error) throw (Error)error;
            throw bad("AOSP asset initialization", error);
        }
        System.err.println("APK_RESOURCES_AOSP_READY");
        System.err.println("APK_PUBLIC_RESOURCES_AOSP_READY");
    }
    private static void checkTable(Path apk) throws Exception {
        // Keep the laboratory input budget without interpreting resource tables.
        try (ZipFile archive = new ZipFile(apk.toFile())) {
            ZipEntry table = archive.getEntry("resources.arsc");
            if (table == null || table.getSize() < 0 || table.getSize() > 16*1024*1024)
                throw bad("Missing or oversized resources.arsc", null);
        }
    }
    private static IllegalArgumentException bad(String message, Throwable cause) {
        return new IllegalArgumentException("Unsupported or invalid APK resources: "+message, cause);
    }
    public Resources platformResources() { return resources; }
    public AssetManager platformAssets() { return manager; }
    public synchronized String getString(int resourceId) {
        if (closed) throw new IllegalStateException("APK resources closed");
        return resources.getString(resourceId);
    }

    private static void checkSize(int width, int height) {
        if (width < 1 || width > 3840 || height < 1 || height > 2160)
            throw new IllegalArgumentException("Display dimensions exceed budget");
    }
    private static void setDimensions(Configuration configuration, DisplayMetrics metrics) {
        configuration.orientation = metrics.widthPixels >= metrics.heightPixels
            ? Configuration.ORIENTATION_LANDSCAPE : Configuration.ORIENTATION_PORTRAIT;
        configuration.screenWidthDp = (int)(metrics.widthPixels / metrics.density);
        configuration.screenHeightDp = (int)(metrics.heightPixels / metrics.density);
        configuration.smallestScreenWidthDp = Math.min(configuration.screenWidthDp, configuration.screenHeightDp);
    }
    public synchronized void configure(int width, int height) {
        if (closed) throw new IllegalStateException("APK resources closed");
        checkSize(width, height);
        DisplayMetrics metrics = new DisplayMetrics();
        metrics.setTo(resources.getDisplayMetrics());
        metrics.widthPixels = metrics.noncompatWidthPixels = width;
        metrics.heightPixels = metrics.noncompatHeightPixels = height;
        Configuration configuration = new Configuration(resources.getConfiguration());
        setDimensions(configuration, metrics);
        resources.updateConfiguration(configuration, metrics);
    }
    public synchronized String displayJson() {
        DisplayMetrics metrics = resources.getDisplayMetrics();
        return "["+metrics.widthPixels+","+metrics.heightPixels+"]";
    }
    @Override public synchronized void close() {
        if (closed) return;
        closed = true;
        try { manager.close(); }
        finally {
            Throwable failure = null;
            for (int i=apkAssets.length-1; i>=0; i--) {
                try { apkAssets[i].close(); }
                catch (RuntimeException | Error error) {
                    if (failure == null) failure=error; else failure.addSuppressed(error);
                }
            }
            if (failure instanceof Error) throw (Error)failure;
            if (failure != null) throw (RuntimeException)failure;
        }
    }
}
