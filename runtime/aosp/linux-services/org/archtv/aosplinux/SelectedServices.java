package org.archtv.aosplinux;

import java.lang.reflect.InvocationTargetException;

/** Linux orchestration only. All contexts, resources, services and IPC are AOSP. */
public final class SelectedServices {
    private static Object call(Class<?> type, Object receiver, String name,
                               Class<?>[] parameters, Object... arguments) throws Exception {
        try {
            return type.getMethod(name, parameters).invoke(receiver, arguments);
        } catch (InvocationTargetException failure) {
            Throwable cause = failure.getCause();
            if (cause instanceof Exception) throw (Exception) cause;
            if (cause instanceof Error) throw (Error) cause;
            throw failure;
        }
    }

    public static void main(String[] args) {
        Thread mainThread = Thread.currentThread();
        Thread diagnostic = new Thread(() -> {
            try { Thread.sleep(6000); } catch (InterruptedException stopped) { return; }
            StringBuilder stack = new StringBuilder("SELECTED_MAIN_WAIT_STACK\n");
            for (StackTraceElement frame : mainThread.getStackTrace()) stack.append("    at ").append(frame).append('\n');
            System.err.println(stack.toString());
            for (java.util.Map.Entry<Thread, StackTraceElement[]> entry : Thread.getAllStackTraces().entrySet()) {
                if (!entry.getKey().getName().equals("android.display")) continue;
                stack = new StringBuilder("SELECTED_DISPLAY_WAIT_STACK\n");
                for (StackTraceElement frame : entry.getValue()) stack.append("    at ").append(frame).append('\n');
                System.err.println(stack.toString());
            }
        }, "selected-wait-diagnostic");
        diagnostic.setDaemon(true);
        diagnostic.start();
        try {
            // Common original system-server IPC/scheduling setup. These calls
            // affect this trusted process, not the Linux host or tenant APKs.
            Class<?> binderInternal = Class.forName("com.android.internal.os.BinderInternal");
            call(binderInternal, null, "disableBackgroundScheduling", new Class<?>[]{boolean.class}, true);
            call(binderInternal, null, "setMaxThreads", new Class<?>[]{int.class}, 31);
            Class<?> process = Class.forName("android.os.Process");
            int priority = process.getField("THREAD_PRIORITY_FOREGROUND").getInt(null);
            call(process, null, "setThreadPriority", new Class<?>[]{int.class}, priority);
            Class<?> looper = Class.forName("android.os.Looper");
            call(looper, null, "prepareMainLooper", new Class<?>[0]);
            System.loadLibrary("android_servers");
            Class<?> activityThread = Class.forName("android.app.ActivityThread");
            Object thread = call(activityThread, null, "systemMain", new Class<?>[0]);
            Object context = call(activityThread, thread, "getSystemContext", new Class<?>[0]);
            Class<?> contextType = Class.forName("android.content.Context");
            int theme = Class.forName("com.android.internal.R$style")
                    .getField("Theme_DeviceDefault_System").getInt(null);
            call(contextType, context, "setTheme", new Class<?>[]{int.class}, theme);
            Object uiContext = call(activityThread, thread, "getSystemUiContext", new Class<?>[0]);
            call(contextType, uiContext, "setTheme", new Class<?>[]{int.class}, theme);
            call(activityThread, null, "initializeMainlineModules", new Class<?>[0]);
            Class<?> managerType = Class.forName("com.android.server.SystemServiceManager");
            Object manager = managerType.getConstructor(contextType).newInstance(context);
            call(Class.forName("com.android.server.LocalServices"), null, "addService",
                    new Class<?>[]{Class.class, Object.class}, managerType, manager);
            // Original common region, required by PropertyInvalidatedCache
            // before starting services. No cache values/nonces are synthesized.
            Class<?> sharedType = Class.forName("com.android.internal.os.ApplicationSharedMemory");
            Object shared = call(sharedType, null, "create", new Class<?>[0]);
            call(sharedType, null, "setInstance", new Class<?>[]{sharedType}, shared);
            Class<?> installerType = Class.forName("com.android.server.pm.Installer");
            Object installer = call(managerType, manager, "startService", new Class<?>[]{Class.class}, installerType);
            // Real original Binder operation; default Installer is not isolated.
            // Its connection latch/remote exceptions remain intact.
            call(installerType, installer, "invalidateMounts", new Class<?>[0]);
            System.err.println("SELECTED_ORIGINAL_INSTALLER_INVALIDATE_RETURNED NOT_APK_INSTALLATION");
            // Original bootstrap order: power is required by LogicalDisplayMapper.
            call(managerType, manager, "startService", new Class<?>[]{Class.class},
                    Class.forName("com.android.server.power.PowerManagerService"));
            // Original PowerManager client also requires IThermalService.
            // Preserve SystemServer's Power -> Thermal -> Display order.
            call(managerType, manager, "startService", new Class<?>[]{Class.class},
                    Class.forName("com.android.server.power.thermal.ThermalManagerService"));
            // Original LightsManager is consumed by LocalDisplayAdapter.
            call(managerType, manager, "startService", new Class<?>[]{Class.class},
                    Class.forName("com.android.server.lights.LightsService"));
            call(managerType, manager, "startService", new Class<?>[]{Class.class},
                    Class.forName("com.android.server.display.DisplayManagerService"));
            Class<?> traceType = Class.forName("com.android.server.utils.TimingsTraceAndSlog");
            Object trace = traceType.getConstructor().newInstance();
            int phase = Class.forName("com.android.server.SystemService")
                    .getField("PHASE_WAIT_FOR_DEFAULT_DISPLAY").getInt(null);
            call(managerType, manager, "startBootPhase", new Class<?>[]{traceType, int.class},
                    trace, phase);
            System.err.println("SELECTED_ORIGINAL_DISPLAY_PHASE_RETURNED requires_original_IPC_verification");
            call(looper, null, "loop", new Class<?>[0]);
            throw new IllegalStateException("Original main looper returned unexpectedly");
        } catch (Throwable failure) {
            failure.printStackTrace(System.err);
            System.exit(1);
        }
    }
}
