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

    private static Object start(Object manager, Class<?> managerType, String name) throws Exception {
        return call(managerType, manager, "startService", new Class<?>[]{Class.class}, Class.forName(name));
    }
    private static void local(String name, String implementation) throws Exception {
        call(Class.forName("com.android.server.LocalServices"), null, "addService",
            new Class<?>[]{Class.class,Object.class}, Class.forName(name), Class.forName(implementation).getConstructor().newInstance());
    }
    public static void main(String[] args) {
        boolean packages = args.length==1 && args[0].equals("--packages");
        Object platformCompat=null, activityManager=null;

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
            if(packages) {
                // Original SystemServer creates this pool before bootstrap services.
                Class<?> pool=Class.forName("com.android.server.SystemServerInitThreadPool");
                java.lang.reflect.Method startPool=pool.getDeclaredMethod("start");
                startPool.setAccessible(true);
                startPool.invoke(null);
                Class<?> artManager=Class.forName("android.os.ArtModuleServiceManager");
                call(Class.forName("com.android.server.art.ArtModuleServiceInitializer"),null,
                    "setArtModuleServiceManager",new Class<?>[]{artManager},artManager.getConstructor().newInstance());
                System.err.println("PACKAGES_ORIGINAL_ART_MODULE_INITIALIZED NOT_ARTD_AVAILABILITY");
            }
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
            if(packages) {
                Class<?> compat=Class.forName("com.android.server.compat.PlatformCompat");
                platformCompat=compat.getConstructor(contextType).newInstance(context);
                Class<?> serviceManager=Class.forName("android.os.ServiceManager");
                Class<?> binder=Class.forName("android.os.IBinder");
                call(serviceManager,null,"addService",new Class<?>[]{String.class,binder},"platform_compat",platformCompat);
                Object compatNative=Class.forName("com.android.server.compat.PlatformCompatNative").getConstructor(compat).newInstance(platformCompat);
                call(serviceManager,null,"addService",new Class<?>[]{String.class,binder},"platform_compat_native",compatNative);
                call(Class.forName("android.app.AppCompatCallbacks"),null,"install",new Class<?>[]{long[].class,long[].class,boolean.class},new long[0],new long[0],false);
                start(manager,managerType,"com.android.server.flags.FeatureFlagsService");
                start(manager,managerType,"com.android.server.uri.UriGrantsManagerService$Lifecycle");
                local("com.android.server.pm.permission.PermissionMigrationHelper","com.android.server.pm.permission.PermissionMigrationHelperImpl");
                local("com.android.server.appop.AppOpMigrationHelper","com.android.server.appop.AppOpMigrationHelperImpl");
                start(manager,managerType,"com.android.server.permission.access.AccessCheckingService");
                System.err.println("PACKAGES_ORIGINAL_ACCESS_CHECKING_STARTED NOT_PERMISSION_ACCEPTANCE");
                Object atmLifecycle=start(manager,managerType,"com.android.server.wm.ActivityTaskManagerService$Lifecycle");
                Object atm=call(atmLifecycle.getClass(),atmLifecycle,"getService",new Class<?>[0]);
                activityManager=call(Class.forName("com.android.server.am.ActivityManagerService$Lifecycle"),null,"startService",
                    new Class<?>[]{managerType,Class.forName("com.android.server.wm.ActivityTaskManagerService")},manager,atm);
                call(activityManager.getClass(),activityManager,"setSystemServiceManager",new Class<?>[]{managerType},manager);
                call(activityManager.getClass(),activityManager,"setInstaller",new Class<?>[]{installerType},installer);
                System.err.println("PACKAGES_ORIGINAL_AMS_ATMS_STARTED NOT_APP_LAUNCH");
            }
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
            if(packages) {
                Class<?> configType=Class.forName("com.android.server.SystemConfig");
                Object config=call(configType,null,"getInstance",new Class<?>[0]);
                Class<?> domainType=Class.forName("com.android.server.pm.verify.domain.DomainVerificationService");
                Object domain=domainType.getConstructor(contextType,configType,Class.forName("com.android.server.compat.PlatformCompat")).newInstance(context,config,platformCompat);
                call(managerType,manager,"startService",new Class<?>[]{Class.forName("com.android.server.SystemService")},domain);
                call(Class.forName("com.android.server.pm.PackageManagerService"),null,"main",new Class<?>[]{contextType,installerType,domainType,boolean.class},context,installer,domain,false);
                System.err.println("PACKAGES_ORIGINAL_PMS_RETURNED REQUIRES_INSTALL_LAUNCH_VERIFICATION");
            }
            call(looper, null, "loop", new Class<?>[0]);
            throw new IllegalStateException("Original main looper returned unexpectedly");
        } catch (Throwable failure) {
            failure.printStackTrace(System.err);
            System.exit(1);
        }
    }
}
