package org.archtv.aospprobe;

import android.content.res.ApkAssets;
import android.content.res.AssetManager;
import android.content.res.Resources;
import android.content.res.Configuration;
import android.util.DisplayMetrics;
import android.os.SystemProperties;
import android.os.Trace;
import android.os.Build;
import java.util.Locale;
import java.lang.ref.Reference;
import java.lang.ref.WeakReference;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;

/** Uses original public Resources constructor with the current host AssetManager initialization. */
public final class PublicResourcesProbe {
    public static void main(String[] args) throws Exception {
        Method refersTo = Reference.class.getMethod("refersTo", Object.class);
        Object object = new Object();
        WeakReference<Object> weak = new WeakReference<>(object);
        if (!(Boolean)refersTo.invoke(weak, object) || (Boolean)refersTo.invoke(weak, new Object()))
            throw new AssertionError("ART Reference.refersTo semantics");
        System.err.println("PUBLIC_RESOURCES_STAGE reference");
        if (args.length == 0) { System.out.println("ART_REFERENCE_OK"); return; }
        System.load(args[0]);
        System.load(args[1]);
        if (!"Televisión 📺".equals(SystemProperties.get("archtv.public.unicode")))
            throw new AssertionError("UTF-16 host property");
        if (!"fallback".equals(SystemProperties.get("archtv.public.absent", "fallback"))
                || !"".equals(SystemProperties.get("archtv.public.absent", null)))
            throw new AssertionError("Missing property default");
        if (!SystemProperties.getBoolean("archtv.public.true", false)
                || SystemProperties.getBoolean("archtv.public.false", true)
                || SystemProperties.getBoolean("archtv.public.invalid", false)
                || !SystemProperties.getBoolean("archtv.public.invalid", true))
            throw new AssertionError("Boolean property spellings/defaults");
        if (Trace.isTagEnabled(Trace.TRACE_TAG_RESOURCES))
            throw new AssertionError("Host tracing must be disabled");
        ApkAssets apk = ApkAssets.loadFromPath(args[2]);
        try {
            Constructor<AssetManager> ctor = AssetManager.class.getDeclaredConstructor(boolean.class);
            ctor.setAccessible(true);
            try (AssetManager assets = ctor.newInstance(false)) {
                Field objectField = AssetManager.class.getDeclaredField("mObject");
                objectField.setAccessible(true);
                Method set = AssetManager.class.getDeclaredMethod("nativeSetApkAssets", long.class, ApkAssets[].class, boolean.class);
                set.setAccessible(true);
                ApkAssets[] input = {apk};
                set.invoke(null, objectField.getLong(assets), input, false);
                Field inventory = AssetManager.class.getDeclaredField("mApkAssets");
                inventory.setAccessible(true); inventory.set(assets, input);
                System.err.println("PUBLIC_RESOURCES_STAGE assets");
                DisplayMetrics metrics = new DisplayMetrics();
                metrics.setToDefaults();
                metrics.widthPixels = metrics.noncompatWidthPixels = 1280;
                metrics.heightPixels = metrics.noncompatHeightPixels = 720;
                Configuration configuration = new Configuration();
                configuration.setToDefaults();
                System.err.println("PUBLIC_RESOURCES_STAGE configuration");
                Resources resources = new Resources(assets, metrics, configuration);
                System.err.println("PUBLIC_RESOURCES_STAGE constructed");
                int id = resources.getIdentifier("counter", "string", "org.archtv.probe");
                if (!"Contador:".equals(resources.getString(id))) throw new AssertionError("Original Resources.getString");
                if (resources.getDisplayMetrics().widthPixels != 1280
                        || resources.getDisplayMetrics().heightPixels != 720
                        || Build.VERSION.RESOURCES_SDK_INT != 33)
                    throw new AssertionError("Metrics/framework profile");
                configuration.setLocale(new Locale("ar"));
                configuration.densityDpi = 240;
                configuration.fontScale = 1.25f;
                resources.updateConfiguration(configuration, metrics);
                if (resources.getConfiguration().getLayoutDirection() != 1
                        || resources.getDisplayMetrics().densityDpi != 240
                        || resources.getDisplayMetrics().scaledDensity != 1.875f
                        || !"Contador:".equals(resources.getString(id)))
                    throw new AssertionError("Configuration update and default resource fallback");
                try {
                    resources.getString(0x7f01ffff);
                    throw new AssertionError("Missing resource accepted");
                } catch (Resources.NotFoundException expected) { }
                Method createTheme = AssetManager.class.getDeclaredMethod("nativeThemeCreate", long.class);
                createTheme.setAccessible(true);
                long theme = (Long)createTheme.invoke(null, objectField.getLong(assets));
                if (theme == 0) throw new AssertionError("Native theme allocation");
                Method freeFunction = AssetManager.class.getDeclaredMethod("nativeGetThemeFreeFunction");
                freeFunction.setAccessible(true);
                long callback = (Long)freeFunction.invoke(null);
                Method applyFree = Class.forName("libcore.util.NativeAllocationRegistry")
                    .getDeclaredMethod("applyFreeFunction", long.class, long.class);
                applyFree.setAccessible(true);
                applyFree.invoke(null, callback, theme);
                System.err.println("PUBLIC_RESOURCES_STAGE theme-release");
                System.out.println("AOSP_PUBLIC_RESOURCES_OK");
            }
        } finally { apk.close(); }
    }
}
