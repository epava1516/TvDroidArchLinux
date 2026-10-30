package org.archtv.apkruntime;

import android.os.Looper;
import android.os.MessageQueue;
import android.view.View;
import java.nio.file.Files;
import java.nio.file.Paths;

/** Actual constructor call, never Unsafe allocation or skipped field initialization. */
public final class ViewConstructorProbe {
    public static void main(String[] args) throws Exception {
        System.load(args[0]);
        System.load(args[1]);
        HostProfile.initialize();
        Files.createDirectories(Paths.get(args[3]));
        AppEnvironment.initialize(Paths.get(args[2]),Paths.get(args[3]));
        Looper.prepareMainLooper();
        try {
            if (Looper.myLooper() != Looper.getMainLooper()) throw new AssertionError("Main Looper");
            android.content.Context context = AppEnvironment.current().applicationContext;
            int counter = context.getResources().getIdentifier("counter","string","org.archtv.probe");
            if (!"Contador:".equals(context.getString(counter))) throw new AssertionError("APK resource identity");
            System.out.println("VIEW_CONSTRUCTOR_BEGIN resources="+
                AppEnvironment.current().applicationContext.getResources().getDisplayMetrics());
            try {
                View view = new View(AppEnvironment.current().applicationContext);
                if (view.getContext() != AppEnvironment.current().applicationContext)
                    throw new AssertionError("View context identity");
                System.out.println("VIEW_CONSTRUCTOR_OK "+view.getClass().getName());
            } catch (LinkageError | UnsupportedOperationException | android.content.res.Resources.NotFoundException failure) {
                System.out.println("VIEW_CONSTRUCTOR_BLOCKED "+failure);
                failure.printStackTrace(System.err);
            }
        } finally {
            java.lang.reflect.Method dispose = MessageQueue.class.getDeclaredMethod("dispose");
            dispose.setAccessible(true);
            dispose.invoke(Looper.getMainLooper().getQueue());
            AppEnvironment.current().resources.close();
        }
        System.out.println("VIEW_CONSTRUCTOR_DIAGNOSTIC_DONE");
    }
}
