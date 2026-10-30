package org.archtv.apkruntime;

import android.content.Context;
import android.content.ContextWrapper;
import android.os.Looper;
import android.os.MessageQueue;
import java.nio.file.Files;
import java.nio.file.Paths;

public final class ContextProbe {
    private static void check(boolean value, String message) {
        if (!value) throw new AssertionError(message);
    }
    private static final class Attached extends ContextWrapper {
        Attached() { super(null); }
        void attach(Context context) { attachBaseContext(context); }
    }
    public static void main(String[] args) throws Exception {
        System.load(args[0]);
        System.load(args[1]);
        HostProfile.initialize();
        Files.createDirectories(Paths.get(args[3]));
        try { AppEnvironment.initialize(Paths.get(args[2]),Paths.get(args[3]),null,1);throw new AssertionError("Unknown virtual display accepted"); }
        catch (IllegalArgumentException expected) { }
        AppEnvironment.initialize(Paths.get(args[2]), Paths.get(args[3]));
        Looper.prepareMainLooper();
        try {
            Context base = AppEnvironment.current().applicationContext;
            check(base instanceof android.app.Application, "Real original Application object");
            ContextWrapper wrapper = new ContextWrapper(base);
            check(wrapper.getBaseContext() == base, "Original wrapper base");
            check(wrapper.getResources() == base.getResources(), "Original Resources identity");
            check(wrapper.getAssets() == base.getAssets(), "Original AssetManager identity");
            check(wrapper.getApplicationContext() == base, "Process application context");
            check(wrapper.getMainLooper() == Looper.getMainLooper(), "Real main Looper");
            try { wrapper.getDisplayId();throw new AssertionError("Headless context invented a visual display"); }
            catch (UnsupportedOperationException expected) { check(expected.getMessage().contains("No visual display"),"Explicit missing display"); }
            check(wrapper.getClassLoader().loadClass("org.archtv.probe.MainActivity").getClassLoader()
                    == wrapper.getClassLoader(), "Actual APK classloader");
            int id = base.getResources().getIdentifier("counter", "string", "org.archtv.probe");
            check("Contador:".equals(wrapper.getString(id)), "Original Context.getString");
            check("Contador:".contentEquals(wrapper.getText(id)), "Original Context.getText");
            check(wrapper.getSharedPreferences("context", Context.MODE_PRIVATE).edit().putInt("value",7).commit(), "Preference commit");
            check(base.getSharedPreferences("context",0).getInt("value",-1) == 7, "Shared preference identity");
            Attached attached = new Attached();
            attached.attach(base);
            check("Contador:".equals(attached.getString(id)), "Attached original wrapper");
            try { attached.attach(base); throw new AssertionError("Duplicate base accepted"); }
            catch (IllegalStateException expected) { }
            try { wrapper.getSystemService(Context.WINDOW_SERVICE); throw new AssertionError("Unsupported service accepted"); }
            catch (UnsupportedOperationException expected) {
                check(expected.getMessage().contains("getSystemService"), "Explicit Linux service failure");
            }
            final int[] callbacks = {0,0,0};
            android.content.ComponentCallbacks2 callback = new android.content.ComponentCallbacks2() {
                public void onConfigurationChanged(android.content.res.Configuration value) { callbacks[0]++; }
                public void onLowMemory() { callbacks[1]++; }
                public void onTrimMemory(int level) { if (level == TRIM_MEMORY_UI_HIDDEN) callbacks[2]++; }
            };
            android.app.Application application = (android.app.Application)base;
            application.registerComponentCallbacks(callback);
            application.onConfigurationChanged(new android.content.res.Configuration(base.getResources().getConfiguration()));
            application.onLowMemory();
            application.onTrimMemory(android.content.ComponentCallbacks2.TRIM_MEMORY_UI_HIDDEN);
            application.unregisterComponentCallbacks(callback);
            application.onLowMemory();
            check(callbacks[0] == 1 && callbacks[1] == 1 && callbacks[2] == 1, "Original component callbacks and unregister");
            System.out.println("AOSP_CONTEXT_OK");
        } finally {
            java.lang.reflect.Method dispose = MessageQueue.class.getDeclaredMethod("dispose");
            dispose.setAccessible(true);
            dispose.invoke(Looper.getMainLooper().getQueue());
            AppEnvironment.current().resources.close();
        }
    }
}
