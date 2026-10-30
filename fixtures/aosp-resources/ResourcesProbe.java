package org.archtv.aospprobe;

import android.content.res.ApkAssets;
import android.content.res.AssetManager;
import java.lang.reflect.Constructor;
import java.lang.reflect.Field;
import java.lang.reflect.Method;
import java.lang.reflect.InvocationTargetException;
import java.util.HashSet;
import java.util.Set;

/** Isolated native linkage probe. Does not claim public system-resource initialization. */
public final class ResourcesProbe {
    private static Field field(Class<?> type, String name) throws Exception {
        Field value = type.getDeclaredField(name); value.setAccessible(true); return value;
    }
    private static Method method(Class<?> type, String name, Class<?>... parameters) throws Exception {
        Method value = type.getDeclaredMethod(name, parameters); value.setAccessible(true); return value;
    }
    private static void check(boolean condition, String message) {
        if (!condition) throw new AssertionError(message);
    }
    public static void main(String[] args) throws Exception {
        System.load(args[0]);
        ApkAssets apk = ApkAssets.loadFromPath(args[1]);
        try {
            Constructor<AssetManager> constructor = AssetManager.class.getDeclaredConstructor(boolean.class);
            constructor.setAccessible(true);
            // Same sentinel constructor used by AOSP Builder. No fake framework-res.apk or overlays.
            try (AssetManager manager = constructor.newInstance(false)) {
                long handle = field(AssetManager.class, "mObject").getLong(manager);
                ApkAssets[] input = {apk};
                method(AssetManager.class, "nativeSetApkAssets", long.class, ApkAssets[].class, boolean.class)
                    .invoke(null, handle, input, false);
                field(AssetManager.class, "mApkAssets").set(manager, input);
                Method identifier = method(AssetManager.class, "getResourceIdentifier", String.class, String.class, String.class);
                Set<Integer> ids = new HashSet<>();
                Method resourceText = method(AssetManager.class, "getResourceText", int.class);
                String[] expectedTexts = {"Arch TV · APK probe", args.length > 2 ? args[2] : "Contador:", "Incrementar"};
                int position = 0;
                for (String name : new String[]{"app_name", "counter", "increment"}) {
                    int id = (Integer)identifier.invoke(manager, name, "string", "org.archtv.probe");
                    check(expectedTexts[position++].contentEquals((CharSequence)resourceText.invoke(manager, id)), "Resource text by ID");
                    check((id >>> 24) == 0x7f && ids.add(id), "Resource identifier "+name);
                    check(id == (Integer)identifier.invoke(manager, "org.archtv.probe:string/"+name, null, null), "Qualified identifier");
                }
                check((Integer)identifier.invoke(manager, "absent", "string", "org.archtv.probe") == 0, "Missing resource");
                Object block = field(ApkAssets.class, "mStringBlock").get(apk);
                long pool = field(block.getClass(), "mNative").getLong(block);
                int count = (Integer)method(block.getClass(), "nativeGetSize", long.class).invoke(null, pool);
                Method get = method(ApkAssets.class, "getStringFromPool", int.class);
                Set<String> strings = new HashSet<>();
                for (int i = 0; i < count; ++i) {
                    CharSequence text = (CharSequence)get.invoke(apk, i);
                    check(text != null, "Null string");
                    check(text == get.invoke(apk, i), "Original Java cache");
                    strings.add(text.toString());
                }
                check(strings.contains("Arch TV · APK probe"), "UTF-16 JNI text");
                check(strings.contains(args.length > 2 ? args[2] : "Contador:"), "Counter text");
                check(strings.contains("Incrementar"), "Button text");
                manager.close();
                try {
                    identifier.invoke(manager, "counter", "string", "org.archtv.probe");
                    throw new AssertionError("Closed manager accepted");
                } catch (InvocationTargetException expected) {
                    check(expected.getCause() instanceof RuntimeException, "Closed manager failure");
                }
            }
        }
        finally { apk.close(); }
        System.out.println("AOSP_RESOURCES_JNI_OK");
    }
}
